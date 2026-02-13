import logging

from flask import Response, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from config import Config
from middleware.jwt_required import get_current_user_id
from routes.auth import auth_bp
from services.auth_service import AuthService
from services.password_validator import PasswordValidator

logger = logging.getLogger(__name__)


@auth_bp.route("/register", methods=["POST"])
def register() -> tuple[Response, int]:
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
def login() -> tuple[Response, int]:
    """Login user"""
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "E-Mail und Passwort sind erforderlich"}), 400

    try:
        result = AuthService.login_user(email, password)

        # Block login for users who haven't verified their email.
        # Google OAuth users are excluded (they have no email verification flow).
        # We check AFTER login_user succeeds to avoid revealing verification status
        # for invalid passwords (security: prevents email enumeration).
        user_data = result["user"]
        if not user_data["email_verified"]:
            block = AuthService.check_email_verification_for_login(email)
            if block:
                return jsonify(block), 403

        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/google", methods=["POST"])
def google_auth() -> tuple[Response, int]:
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

        result = AuthService.google_auth_login(
            google_id=google_id,
            email=email,
            email_verified=email_verified,
            full_name=full_name,
            registration_enabled=Config.REGISTRATION_ENABLED,
        )

        return jsonify(result), 200

    except ValueError as e:
        error_msg = str(e)
        if "deaktiviert" in error_msg and "Registrierung" in error_msg:
            return jsonify({"error": error_msg}), 403
        if "deaktiviert" in error_msg:
            return jsonify({"error": error_msg}), 401
        # Token verification failed
        return jsonify({"error": "Ungültiges Google-Token"}), 401
    except Exception as e:
        logger.error("Google auth error: %s", e)
        return jsonify({"error": "Google-Authentifizierung fehlgeschlagen"}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh() -> tuple[Response, int]:
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me() -> Response | tuple[Response, int]:
    """Get current user info"""
    current_user_id = get_current_user_id()
    user = AuthService.get_user_by_id(current_user_id)

    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route("/password-requirements", methods=["GET"])
def password_requirements() -> tuple[Response, int]:
    """Get password requirements for frontend display"""
    return jsonify({"requirements": PasswordValidator.get_requirements()}), 200


@auth_bp.route("/validate-password", methods=["POST"])
def validate_password() -> tuple[Response, int]:
    """Validate password strength"""
    data = request.json
    password = data.get("password", "")

    result = PasswordValidator.validate(password)
    return jsonify(result), 200
