"""
ATS (Applicant Tracking System) API Routes.

Provides endpoints for analyzing CVs against job descriptions.
"""

import os

from flask import Blueprint, current_app, jsonify, request

from middleware.jwt_required import jwt_required_custom
from models import Document
from services.ats_service import ATSService
from services.web_scraper import WebScraper

ats_bp = Blueprint("ats", __name__)


@ats_bp.route("/analyze", methods=["POST"])
@jwt_required_custom
def analyze_cv(current_user):
    """
    Analyze user's CV against a job description.

    Accepts either job_url OR job_text (at least one required).
    Uses the user's uploaded CV (doc_type='lebenslauf').

    Rate limited to 20 requests per hour.

    Request JSON:
        job_url: str (optional) - URL of job posting to scrape
        job_text: str (optional) - Direct job description text

    Returns:
        200: { success: true, data: { score, matched_keywords, missing_keywords, suggestions } }
        400: Missing input or no CV uploaded
        429: Rate limit exceeded
        500: Server error
    """
    # Apply rate limit - 20 per hour for this endpoint
    limiter = current_app.limiter
    limit = limiter.limit("20 per hour")

    @limit
    def rate_limited_analyze():
        data = request.get_json() or {}
        job_url = data.get("job_url", "").strip()
        job_text = data.get("job_text", "").strip()

        # Validate: at least one of job_url or job_text required
        if not job_url and not job_text:
            return jsonify({
                "success": False,
                "error": "job_url oder job_text ist erforderlich"
            }), 400

        # Get user's CV
        cv_document = Document.query.filter_by(
            user_id=current_user.id,
            doc_type="lebenslauf"
        ).first()

        if not cv_document:
            return jsonify({
                "success": False,
                "error": "Kein Lebenslauf hochgeladen. Bitte laden Sie zuerst Ihren Lebenslauf hoch."
            }), 400

        # Read CV text from file
        if not os.path.exists(cv_document.file_path):
            return jsonify({
                "success": False,
                "error": "Lebenslauf-Datei nicht gefunden"
            }), 400

        with open(cv_document.file_path, encoding="utf-8") as f:
            cv_text = f.read()

        if not cv_text.strip():
            return jsonify({
                "success": False,
                "error": "Lebenslauf ist leer"
            }), 400

        # Get job description text
        job_description = job_text
        scraped_url = None

        if job_url:
            try:
                scraper = WebScraper()
                scraped_data = scraper.fetch_job_posting(job_url)
                job_description = scraped_data.get("text", "")
                scraped_url = job_url

                if not job_description.strip():
                    return jsonify({
                        "success": False,
                        "error": "Konnte keinen Text von der URL extrahieren"
                    }), 400
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Fehler beim Laden der Job-URL: {str(e)}"
                }), 400

        # Perform ATS analysis
        try:
            service = ATSService()
            result = service.analyze_cv_against_job(cv_text, job_description)

            response_data = {
                "score": result.get("score", 0),
                "matched_keywords": result.get("matched_keywords", []),
                "missing_keywords": result.get("missing_keywords", []),
                "suggestions": result.get("suggestions", []),
                "categories": result.get("categories", {})
            }

            if scraped_url:
                response_data["job_url"] = scraped_url

            return jsonify({
                "success": True,
                "data": response_data
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Analyse fehlgeschlagen: {str(e)}"
            }), 500

    return rate_limited_analyze()
