"""
Demo API Routes.

Provides anonymous demo endpoints for unauthenticated users.
Rate limited to prevent abuse.
"""

from flask import Blueprint, current_app, jsonify, request
from flask_limiter.util import get_remote_address

from config import config

demo_bp = Blueprint("demo", __name__)


def _generate_demo_logic():
    """Core demo generation logic, separated for reuse."""
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    # Validate URL
    if not url:
        return jsonify({"success": False, "message": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "message": "Ungültige URL"}), 400

    try:
        from services.demo_generator import DemoGenerator

        generator = DemoGenerator()
        result = generator.generate_demo(url)

        return jsonify({"success": True, "data": result}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Demo generation failed: {e}")
        return jsonify({"success": False, "message": "Generierung fehlgeschlagen. Bitte versuche es erneut."}), 500


@demo_bp.route("/generate", methods=["POST"])
def generate_demo():
    """
    Generate a demo application from a job URL.

    Anonymous endpoint with strict rate limiting (1 request per hour per IP).
    Uses pre-cached sample CV and returns ephemeral data (not saved).
    Whitelisted IPs (configured via RATE_LIMIT_WHITELIST) bypass rate limiting.

    Request JSON:
        url: str - URL of job posting to analyze

    Returns:
        200: { success: true, data: { position, firma, einleitung, anschreiben, ... } }
        400: Invalid input
        429: Rate limit exceeded
        500: Server error
    """
    # Check if IP is whitelisted - bypass rate limiting
    remote_addr = get_remote_address()
    if remote_addr in config.RATE_LIMIT_WHITELIST:
        return _generate_demo_logic()

    # Apply strict rate limit - 1 per hour for anonymous demo
    limiter = current_app.limiter
    limit = limiter.limit("1 per hour")

    @limit
    def rate_limited_generate():
        return _generate_demo_logic()

    return rate_limited_generate()
