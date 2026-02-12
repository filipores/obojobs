from datetime import datetime, timedelta

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from routes.auth import auth_bp
from services.auth_service import AuthService
from services.email_service import send_password_reset_email
from services.password_reset_service import PasswordResetService
from services.password_validator import PasswordValidator

# Rate limiting storage (in-memory for development)
# In production, this should use Redis
_password_reset_rate_limits: dict[str, list[datetime]] = {}

MAX_PASSWORD_RESET_PER_HOUR = 3


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
