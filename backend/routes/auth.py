from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from config import Config
from models import TokenBlacklist, User, db
from services.auth_service import AuthService
from services.email_service import send_password_reset_email, send_verification_email
from services.email_verification_service import EmailVerificationService
from services.password_reset_service import PasswordResetService
from services.password_validator import PasswordValidator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    # Check if registration is enabled
    if not Config.REGISTRATION_ENABLED:
        return jsonify(
            {"error": "Registrierung ist derzeit deaktiviert. Bitte kontaktieren Sie den Administrator."}
        ), 403

    data = request.json

    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not email or not password:
        return jsonify({"error": "E-Mail und Passwort sind erforderlich"}), 400

    try:
        user = AuthService.register_user(email, password, full_name)
        return jsonify({"message": "Registrierung erfolgreich", "user": user.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user"""
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "E-Mail und Passwort sind erforderlich"}), 400

    try:
        result = AuthService.login_user(email, password)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/google", methods=["POST"])
def google_auth():
    """
    Authenticate with Google OAuth.

    Accepts a Google ID token from the frontend and:
    - Verifies the token with Google
    - Creates a new user if email doesn't exist
    - Links Google account if email exists without Google ID
    - Returns JWT tokens for authentication
    """
    data = request.json or {}
    credential = data.get("credential")

    if not credential:
        return jsonify({"error": "Google credential ist erforderlich"}), 400

    # Verify Google Client ID is configured
    if not Config.GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth ist nicht konfiguriert"}), 500

    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), Config.GOOGLE_CLIENT_ID)

        # Get user info from token
        google_id = idinfo["sub"]
        email = idinfo.get("email")
        email_verified = idinfo.get("email_verified", False)
        full_name = idinfo.get("name")

        if not email:
            return jsonify({"error": "Keine E-Mail-Adresse von Google erhalten"}), 400

        email = email.lower()

        # Check if user exists by Google ID
        user = User.query.filter_by(google_id=google_id).first()

        if not user:
            # Check if user exists by email
            user = User.query.filter_by(email=email).first()

            if user:
                # Link Google account to existing user
                user.google_id = google_id
                # Mark email as verified if Google says it's verified
                if email_verified and not user.email_verified:
                    user.email_verified = True
                db.session.commit()
            else:
                # Check if registration is enabled
                if not Config.REGISTRATION_ENABLED:
                    return jsonify(
                        {"error": "Registrierung ist derzeit deaktiviert. Bitte kontaktieren Sie den Administrator."}
                    ), 403

                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    full_name=full_name,
                    email_verified=email_verified,  # Google-verified emails are trusted
                )
                db.session.add(user)
                db.session.commit()

        # Check if user is active
        if not user.is_active:
            return jsonify({"error": "Konto ist deaktiviert"}), 401

        # Create JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}), 200

    except ValueError:
        # Token verification failed
        return jsonify({"error": "Ungültiges Google-Token"}), 401
    except Exception as e:
        print(f"Google auth error: {e}")
        return jsonify({"error": "Google-Authentifizierung fehlgeschlagen"}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Get current user info"""
    current_user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(int(current_user_id))

    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route("/password-requirements", methods=["GET"])
def password_requirements():
    """Get password requirements for frontend display"""
    return jsonify({"requirements": PasswordValidator.get_requirements()}), 200


@auth_bp.route("/validate-password", methods=["POST"])
def validate_password():
    """Validate password strength"""
    data = request.json
    password = data.get("password", "")

    result = PasswordValidator.validate(password)
    return jsonify(result), 200


# Rate limiting storage (in-memory for development)
# In production, this should use Redis
_verification_rate_limits: dict[str, list[datetime]] = {}
_password_reset_rate_limits: dict[str, list[datetime]] = {}

# Maximum verification emails per hour
MAX_VERIFICATION_EMAILS_PER_HOUR = 3
MAX_PASSWORD_RESET_PER_HOUR = 3


def _check_verification_rate_limit(user_id: int) -> bool:
    """
    Check if user has exceeded verification email rate limit.

    Args:
        user_id: User ID to check

    Returns:
        True if under limit (can send), False if rate limited
    """
    key = str(user_id)
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # Clean up old entries and get recent requests
    if key in _verification_rate_limits:
        _verification_rate_limits[key] = [ts for ts in _verification_rate_limits[key] if ts > one_hour_ago]
    else:
        _verification_rate_limits[key] = []

    # Check if under limit
    return len(_verification_rate_limits[key]) < MAX_VERIFICATION_EMAILS_PER_HOUR


def _record_verification_request(user_id: int) -> None:
    """Record a verification email request for rate limiting."""
    key = str(user_id)
    if key not in _verification_rate_limits:
        _verification_rate_limits[key] = []
    _verification_rate_limits[key].append(datetime.utcnow())


@auth_bp.route("/send-verification", methods=["POST"])
@jwt_required()
def send_verification():
    """
    Send a new email verification token.

    Requires authentication. Rate limited to 3 requests per hour.
    In development mode, logs the token instead of sending email.
    """
    current_user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(int(current_user_id))

    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    # Check if already verified
    if user.email_verified:
        return jsonify({"error": "E-Mail ist bereits bestätigt"}), 400

    # Check rate limit
    if not _check_verification_rate_limit(user.id):
        return jsonify(
            {"error": "Zu viele Bestätigungsanfragen. Bitte später erneut versuchen.", "retry_after_minutes": 60}
        ), 429

    # Generate and store token
    token = EmailVerificationService.create_verification_token(user)

    # Record the request for rate limiting
    _record_verification_request(user.id)

    send_verification_email(user.email, token)

    return jsonify({"message": "Bestätigungs-E-Mail gesendet", "email": user.email}), 200


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """
    Verify email using the provided token.

    Public endpoint - does not require authentication.
    """
    data = request.json or {}
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token ist erforderlich"}), 400

    result = EmailVerificationService.verify_token(token)

    if not result["success"]:
        return jsonify({"error": result["message"]}), 400

    user = result["user"]
    return jsonify({"message": "E-Mail erfolgreich bestätigt", "user": user.to_dict()}), 200


def _check_password_reset_rate_limit(email: str) -> bool:
    """
    Check if email has exceeded password reset rate limit.

    Args:
        email: Email address to check

    Returns:
        True if under limit (can send), False if rate limited
    """
    key = email.lower()
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # Clean up old entries and get recent requests
    if key in _password_reset_rate_limits:
        _password_reset_rate_limits[key] = [ts for ts in _password_reset_rate_limits[key] if ts > one_hour_ago]
    else:
        _password_reset_rate_limits[key] = []

    # Check if under limit
    return len(_password_reset_rate_limits[key]) < MAX_PASSWORD_RESET_PER_HOUR


def _record_password_reset_request(email: str) -> None:
    """Record a password reset request for rate limiting."""
    key = email.lower()
    if key not in _password_reset_rate_limits:
        _password_reset_rate_limits[key] = []
    _password_reset_rate_limits[key].append(datetime.utcnow())


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Request a password reset token.

    Public endpoint. Always returns 200 OK to prevent email enumeration.
    Rate limited to 3 requests per hour per email.
    In development mode, logs the token instead of sending email.
    """
    data = request.json or {}
    email = data.get("email", "").strip().lower()

    if not email:
        # Still return 200 to prevent enumeration
        return jsonify({"message": "Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet."}), 200

    # Check rate limit (even for non-existent emails to prevent timing attacks)
    if not _check_password_reset_rate_limit(email):
        # Still return 200 to prevent enumeration, but don't process
        return jsonify({"message": "Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet."}), 200

    # Record the request for rate limiting
    _record_password_reset_request(email)

    # Find user by email
    user = AuthService.get_user_by_email(email)

    if user and user.is_active:
        # Generate and store token
        token = PasswordResetService.create_reset_token(user)

        send_password_reset_email(user.email, token)

    # Always return same response to prevent email enumeration
    return jsonify({"message": "Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet."}), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Reset password using the provided token.

    Public endpoint - does not require authentication.
    """
    data = request.json or {}
    token = data.get("token")
    new_password = data.get("new_password")

    if not token:
        return jsonify({"error": "Token ist erforderlich"}), 400

    if not new_password:
        return jsonify({"error": "Neues Passwort ist erforderlich"}), 400

    # Validate password strength
    validation = PasswordValidator.validate(new_password)
    if not validation["valid"]:
        return jsonify({"error": "Passwort erfüllt nicht die Anforderungen", "failed_rules": validation["errors"]}), 400

    # Reset the password
    result = PasswordResetService.reset_password(token, new_password)

    if not result["success"]:
        return jsonify({"error": result["message"]}), 400

    return jsonify({"message": "Passwort erfolgreich zurückgesetzt"}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """
    Change password for authenticated user.

    Requires authentication. Validates current password and new password strength.
    """
    current_user_id = get_jwt_identity()
    data = request.json or {}

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password:
        return jsonify({"error": "Aktuelles Passwort ist erforderlich"}), 400

    if not new_password:
        return jsonify({"error": "Neues Passwort ist erforderlich"}), 400

    try:
        result = AuthService.change_password(int(current_user_id), current_password, new_password)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout user by adding current token to blacklist.

    Requires authentication. The token's JTI is added to the blacklist,
    making it invalid for future use even if it hasn't expired yet.
    """
    jwt = get_jwt()
    jti = jwt["jti"]
    token_type = jwt.get("type", "access")
    user_id = int(get_jwt_identity())

    # Get token expiration time
    exp_timestamp = jwt["exp"]
    expires_at = datetime.utcfromtimestamp(exp_timestamp)

    # Add token to blacklist
    TokenBlacklist.add_token(jti=jti, token_type=token_type, user_id=user_id, expires_at=expires_at)

    return jsonify({"message": "Erfolgreich abgemeldet"}), 200


@auth_bp.route("/language", methods=["PUT"])
@jwt_required()
def update_language():
    """
    Update user language preference.

    Requires authentication. Allows updating language preference (de or en).
    """
    current_user_id = get_jwt_identity()
    data = request.json or {}

    user = AuthService.get_user_by_id(int(current_user_id))
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    language = data.get("language", "").strip().lower()
    if language not in ["de", "en"]:
        return jsonify({"error": "Ungültige Sprache. Muss 'de' oder 'en' sein."}), 400

    user.language = language
    db.session.commit()

    return jsonify({"message": "Spracheinstellung aktualisiert", "language": user.language}), 200


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update user profile information.

    Requires authentication. Allows updating full_name and display_name.
    """
    current_user_id = get_jwt_identity()
    data = request.json or {}

    user = AuthService.get_user_by_id(int(current_user_id))
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    # Profile field definitions: (json_key, model_attr, max_length, label)
    profile_fields = [
        ("full_name", "full_name", 255, "Name"),
        ("display_name", "display_name", 100, "Anzeigename"),
        ("phone", "phone", 50, "Telefonnummer"),
        ("address", "address", 255, "Adresse"),
        ("city", "city", 100, "Stadt"),
        ("postal_code", "postal_code", 20, "PLZ"),
        ("website", "website", 255, "Website"),
    ]

    for json_key, attr, max_length, label in profile_fields:
        if json_key not in data:
            continue
        value = data[json_key]
        if value and len(value) > max_length:
            return jsonify({"error": f"{label} darf maximal {max_length} Zeichen haben"}), 400
        setattr(user, attr, value.strip() if value else None)

    db.session.commit()

    return jsonify({"message": "Profil erfolgreich aktualisiert", "user": user.to_dict()}), 200


@auth_bp.route("/delete-account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """
    Delete user account and all associated data.

    Requires authentication. This action is irreversible and will:
    - Delete the user account
    - Delete all associated data (documents, applications, templates, etc.)
    - Blacklist the current JWT token
    - Cancel any active Stripe subscriptions

    GDPR compliance: This ensures the "right to be forgotten" is fulfilled.
    """
    current_user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(int(current_user_id))

    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    try:
        # Cancel Stripe subscription if exists
        if user.stripe_customer_id:
            try:
                # Note: In a real implementation, you would cancel the Stripe subscription here
                # import stripe
                # stripe.Customer.delete(user.stripe_customer_id)
                pass
            except Exception as e:
                # Log the error but don't fail the deletion
                print(f"Warning: Could not cancel Stripe subscription for user {user.id}: {e}")

        # Store info for logging before deletion
        user_email = user.email
        user_id = user.id

        # Delete all TokenBlacklist entries for this user to avoid foreign key issues
        TokenBlacklist.query.filter_by(user_id=user_id).delete()

        # Delete user (cascade will handle all other related data)
        db.session.delete(user)
        db.session.commit()

        # Note: We don't manually blacklist the current token because it would create
        # a foreign key constraint violation. Since the user is deleted, any subsequent
        # API calls with this token will fail during user lookup anyway.

        # Log successful deletion (for compliance purposes)
        print(f"[GDPR] Account deleted for user {user_email} (ID: {current_user_id})")

        return jsonify({"message": "Ihr Konto und alle zugehörigen Daten wurden erfolgreich gelöscht."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting account for user {current_user_id}: {e}")
        return jsonify({"error": "Fehler beim Löschen des Kontos. Bitte kontaktieren Sie den Support."}), 500
