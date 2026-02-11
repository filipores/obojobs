"""
Demo API Routes.

Provides anonymous demo endpoints for unauthenticated users.
Rate limited to prevent abuse.
"""

import os
import tempfile

from flask import Blueprint, current_app, jsonify, request
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

from config import config
from services.pdf_handler import extract_text_from_pdf

demo_bp = Blueprint("demo", __name__)

ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _generate_demo_logic():
    """Core demo generation logic.

    Requires multipart/form-data with cv_file and url.
    """
    try:
        # Validate URL first (cheap check before file I/O)
        url = request.form.get("url", "").strip()

        if not url:
            return jsonify({"success": False, "message": "URL ist erforderlich"}), 400

        if not url.startswith(("http://", "https://")):
            return jsonify({"success": False, "message": "Ungültige URL"}), 400

        if "cv_file" not in request.files:
            return jsonify({"success": False, "message": "CV-Datei ist erforderlich"}), 400

        cv_file = request.files["cv_file"]

        if cv_file.filename == "":
            return jsonify({"success": False, "message": "Keine Datei ausgewählt"}), 400

        if not _allowed_file(cv_file.filename):
            return jsonify({"success": False, "message": "Nur PDF-Dateien erlaubt"}), 400

        cv_file.seek(0, os.SEEK_END)
        file_size = cv_file.tell()
        cv_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"success": False, "message": "Datei zu groß. Max. 10 MB erlaubt."}), 400

        # Save to temp file, extract text, then always clean up
        filename = secure_filename(cv_file.filename)
        temp_file_path = os.path.join(tempfile.gettempdir(), f"demo_cv_{os.urandom(8).hex()}_{filename}")
        cv_file.save(temp_file_path)

        try:
            cv_text = extract_text_from_pdf(temp_file_path)
            if not cv_text.strip():
                return jsonify({"success": False, "message": "Konnte keinen Text aus dem PDF extrahieren"}), 400
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        from services.demo_generator import DemoGenerator

        generator = DemoGenerator()
        result = generator.generate_demo(url, cv_text=cv_text)
        result["cv_text"] = cv_text

        return jsonify({"success": True, "data": result}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Demo generation failed: {e}")
        return jsonify({"success": False, "message": "Generierung fehlgeschlagen. Bitte versuche es erneut."}), 500


@demo_bp.route("/generate", methods=["POST"])
def generate_demo():
    """
    Generate a demo application from a job URL and uploaded CV.

    Anonymous endpoint with strict rate limiting (1 request per hour per IP).
    Whitelisted IPs (configured via RATE_LIMIT_WHITELIST) bypass rate limiting.

    Accepts multipart/form-data:
       - url: str - URL of job posting to analyze
       - cv_file: file (PDF, required) - User's CV for personalization

    Returns:
        200: { success: true, data: { position, firma, einleitung, anschreiben, cv_text, ... } }
        400: Invalid input or missing CV file
        429: Rate limit exceeded
        500: Server error
    """
    remote_addr = get_remote_address()
    if remote_addr in config.RATE_LIMIT_WHITELIST:
        return _generate_demo_logic()

    limiter = current_app.limiter
    limit = limiter.limit("1 per hour")

    @limit
    def rate_limited_generate():
        return _generate_demo_logic()

    return rate_limited_generate()
