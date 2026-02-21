"""
ATS (Applicant Tracking System) API Routes.

Provides endpoints for analyzing CVs against job descriptions.
"""

import json
import os
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from middleware.jwt_required import jwt_required_custom
from services import ats_analysis_service
from services.ats_service import ATSService
from services.web_scraper import WebScraper

ats_bp = Blueprint("ats", __name__)

# Cache duration in hours
CACHE_DURATION_HOURS = 24


@ats_bp.route("/analyze", methods=["POST"])
@jwt_required_custom
def analyze_cv(current_user: Any) -> Response | tuple[Response, int]:
    """
    Analyze user's CV against a job description.

    Accepts either job_url OR job_text (at least one required).
    Uses the user's uploaded CV (doc_type='lebenslauf').

    Rate limited to 20 requests per hour.
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
            return jsonify({"success": False, "error": "job_url oder job_text ist erforderlich"}), 400

        # Check cache first (only for job_url, within 24 hours)
        if job_url:
            cached_result = ats_analysis_service.find_cached_analysis(current_user.id, job_url, CACHE_DURATION_HOURS)

            if cached_result:
                try:
                    result_data = json.loads(cached_result.result_json)
                    result_data["job_url"] = job_url
                    result_data["cached"] = True
                    result_data["analysis_id"] = cached_result.id
                    return jsonify({"success": True, "data": result_data}), 200
                except json.JSONDecodeError:
                    pass  # Continue with fresh analysis

        # Get user's CV
        cv_document = ats_analysis_service.get_cv_document(current_user.id)

        if not cv_document:
            return jsonify(
                {
                    "success": False,
                    "error": "Kein Lebenslauf hochgeladen. Bitte lade zuerst deinen Lebenslauf hoch.",
                }
            ), 400

        # Read CV text from file
        if not os.path.exists(cv_document.file_path):
            return jsonify({"success": False, "error": "Lebenslauf-Datei nicht gefunden"}), 400

        with open(cv_document.file_path, encoding="utf-8") as f:
            cv_text = f.read()

        if not cv_text.strip():
            return jsonify({"success": False, "error": "Lebenslauf ist leer"}), 400

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
                    return jsonify({"success": False, "error": "Konnte keinen Text von der URL extrahieren"}), 400
            except Exception as e:
                return jsonify({"success": False, "error": f"Fehler beim Laden der Job-URL: {str(e)}"}), 400

        # Perform ATS analysis
        try:
            service = ATSService()
            result = service.analyze_cv_against_job(cv_text, job_description)

            response_data = {
                "score": result.get("score", 0),
                "matched_keywords": result.get("matched_keywords", []),
                "missing_keywords": result.get("missing_keywords", []),
                "suggestions": result.get("suggestions", []),
                "categories": result.get("categories", {}),
            }

            # Save analysis to database
            job_text_hash = None
            analysis_title = None

            if job_text and not job_url:
                job_text_hash = ats_analysis_service.hash_job_text(job_text)
                # Extract title from first non-empty line of job text
                lines = job_text.strip().split("\n")
                for line in lines:
                    stripped = line.strip()
                    if stripped:
                        # Truncate to 100 chars for display
                        analysis_title = stripped[:100] + ("..." if len(stripped) > 100 else "")
                        break
                if not analysis_title:
                    analysis_title = "Manuelle Analyse"
            elif scraped_url:
                # Extract hostname as title for URL analyses
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(scraped_url)
                    analysis_title = parsed.netloc.replace("www.", "")
                except Exception:
                    analysis_title = scraped_url[:100]

            ats_analysis = ats_analysis_service.create_analysis(
                user_id=current_user.id,
                job_url=scraped_url,
                job_text_hash=job_text_hash,
                title=analysis_title,
                score=response_data["score"],
                result_json=json.dumps(response_data),
            )

            response_data["analysis_id"] = ats_analysis.id
            response_data["cached"] = False

            if scraped_url:
                response_data["job_url"] = scraped_url

            return jsonify({"success": True, "data": response_data}), 200

        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            ats_analysis_service.rollback()
            return jsonify({"success": False, "error": f"Analyse fehlgeschlagen: {str(e)}"}), 500

    return rate_limited_analyze()


@ats_bp.route("/history", methods=["GET"])
@jwt_required_custom
def get_history(current_user: Any) -> tuple[Response, int]:
    """Get the user's ATS analysis history."""
    analyses = ats_analysis_service.get_history(current_user.id)

    return jsonify({"success": True, "data": {"analyses": [a.to_summary_dict() for a in analyses]}}), 200


@ats_bp.route("/history/<int:analysis_id>", methods=["GET"])
@jwt_required_custom
def get_analysis(current_user: Any, analysis_id: int) -> tuple[Response, int]:
    """Get a specific ATS analysis by ID."""
    analysis = ats_analysis_service.get_analysis(analysis_id, current_user.id)

    if not analysis:
        return jsonify({"success": False, "error": "Analyse nicht gefunden"}), 404

    return jsonify({"success": True, "data": analysis.to_dict()}), 200


@ats_bp.route("/history/<int:analysis_id>", methods=["DELETE"])
@jwt_required_custom
def delete_analysis(current_user: Any, analysis_id: int) -> tuple[Response, int]:
    """Delete a specific ATS analysis by ID."""
    analysis = ats_analysis_service.delete_analysis(analysis_id, current_user.id)

    if not analysis:
        return jsonify({"success": False, "error": "Analyse nicht gefunden"}), 404

    return jsonify({"success": True, "message": "Analyse gelöscht"}), 200
