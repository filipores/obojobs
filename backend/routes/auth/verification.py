from datetime import datetime, timedelta

from flask import Response, jsonify, request
from flask_jwt_extended import jwt_required

from middleware.jwt_required import get_current_user_id
from routes.auth import auth_bp
from services.auth_service import AuthService
from services.email_service import send_verification_email
from services.email_verification_service import EmailVerificationService

# Rate limiting storage (in-memory for development)
# In production, this should use Redis
_verification_rate_limits: dict[str, list[datetime]] = {}

# Maximum verification emails per hour
MAX_VERIFICATION_EMAILS_PER_HOUR = 3


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


_RESEND_VERIFICATION_RESPONSE = "Falls ein Konto mit dieser E-Mail existiert, wurde eine Bestätigungs-E-Mail gesendet."


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification() -> tuple[Response, int]:
    """
    Resend email verification for unverified users who cannot log in.

    Public endpoint - does not require authentication.
    Accepts email in the request body. Rate limited to 3 requests per hour.
    Always returns 200 to prevent email enumeration.
    """
    data = request.json or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"message": _RESEND_VERIFICATION_RESPONSE}), 200

    user = AuthService.get_user_by_email(email)

    if not user or user.email_verified:
        return jsonify({"message": _RESEND_VERIFICATION_RESPONSE}), 200

    if not _check_verification_rate_limit(user.id):
        return jsonify({"message": _RESEND_VERIFICATION_RESPONSE}), 200

    # Generate and store token
    token = EmailVerificationService.create_verification_token(user)

    # Record the request for rate limiting
    _record_verification_request(user.id)

    send_verification_email(user.email, token)

    return jsonify({"message": _RESEND_VERIFICATION_RESPONSE}), 200


@auth_bp.route("/send-verification", methods=["POST"])
@jwt_required()
def send_verification() -> tuple[Response, int]:
    """
    Send a new email verification token.

    Requires authentication. Rate limited to 3 requests per hour.
    In development mode, logs the token instead of sending email.
    """
    current_user_id = get_current_user_id()
    user = AuthService.get_user_by_id(current_user_id)

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
def verify_email() -> tuple[Response, int]:
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
