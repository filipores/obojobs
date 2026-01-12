from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required

from models import TokenBlacklist
from services.auth_service import AuthService
from services.email_verification_service import EmailVerificationService
from services.password_reset_service import PasswordResetService
from services.password_validator import PasswordValidator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.json

    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = AuthService.register_user(email, password, full_name)
        return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user"""
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        result = AuthService.login_user(email, password)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


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
        return jsonify({"error": "User not found"}), 404

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
        _verification_rate_limits[key] = [
            ts for ts in _verification_rate_limits[key] if ts > one_hour_ago
        ]
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
        return jsonify({"error": "User not found"}), 404

    # Check if already verified
    if user.email_verified:
        return jsonify({"error": "Email is already verified"}), 400

    # Check rate limit
    if not _check_verification_rate_limit(user.id):
        return jsonify({
            "error": "Too many verification requests. Please try again later.",
            "retry_after_minutes": 60
        }), 429

    # Generate and store token
    token = EmailVerificationService.create_verification_token(user)

    # Record the request for rate limiting
    _record_verification_request(user.id)

    # In development, log the token (in production, send email)
    # TODO: Integrate actual email sending service
    print(f"[DEV] Verification token for {user.email}: {token}")

    return jsonify({
        "message": "Verification email sent",
        "email": user.email
    }), 200


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """
    Verify email using the provided token.

    Public endpoint - does not require authentication.
    """
    data = request.json or {}
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token is required"}), 400

    result = EmailVerificationService.verify_token(token)

    if not result["success"]:
        return jsonify({"error": result["message"]}), 400

    user = result["user"]
    return jsonify({
        "message": "Email verified successfully",
        "user": user.to_dict()
    }), 200


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
        _password_reset_rate_limits[key] = [
            ts for ts in _password_reset_rate_limits[key] if ts > one_hour_ago
        ]
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
        return jsonify({
            "message": "If an account with this email exists, a reset link has been sent."
        }), 200

    # Check rate limit (even for non-existent emails to prevent timing attacks)
    if not _check_password_reset_rate_limit(email):
        # Still return 200 to prevent enumeration, but don't process
        return jsonify({
            "message": "If an account with this email exists, a reset link has been sent."
        }), 200

    # Record the request for rate limiting
    _record_password_reset_request(email)

    # Find user by email
    user = AuthService.get_user_by_email(email)

    if user and user.is_active:
        # Generate and store token
        token = PasswordResetService.create_reset_token(user)

        # In development, log the token (in production, send email)
        # TODO: Integrate actual email sending service
        print(f"[DEV] Password reset token for {user.email}: {token}")

    # Always return same response to prevent email enumeration
    return jsonify({
        "message": "If an account with this email exists, a reset link has been sent."
    }), 200


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
        return jsonify({"error": "Token is required"}), 400

    if not new_password:
        return jsonify({"error": "New password is required"}), 400

    # Validate password strength
    validation = PasswordValidator.validate(new_password)
    if not validation["valid"]:
        return jsonify({
            "error": "Password does not meet requirements",
            "failed_rules": validation["errors"]
        }), 400

    # Reset the password
    result = PasswordResetService.reset_password(token, new_password)

    if not result["success"]:
        return jsonify({"error": result["message"]}), 400

    return jsonify({"message": "Password reset successfully"}), 200


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
        result = AuthService.change_password(
            int(current_user_id), current_password, new_password
        )
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
    TokenBlacklist.add_token(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        expires_at=expires_at
    )

    return jsonify({"message": "Successfully logged out"}), 200
