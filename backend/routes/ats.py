"""
ATS (Applicant Tracking System) API Routes.

Provides endpoints for analyzing CVs against job descriptions.
"""

import json
import os
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from middleware.jwt_required import jwt_required_custom
from models import ATSAnalysis, Document, db
from services.ats_service import ATSService
from services.web_scraper import WebScraper

ats_bp = Blueprint("ats", __name__)

# Cache duration in hours
CACHE_DURATION_HOURS = 24


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
            return jsonify({"success": False, "error": "job_url oder job_text ist erforderlich"}), 400

        # Check cache first (only for job_url, within 24 hours)
        if job_url:
            cache_cutoff = datetime.utcnow() - timedelta(hours=CACHE_DURATION_HOURS)
            cached_result = (
                ATSAnalysis.query.filter(
                    ATSAnalysis.user_id == current_user.id,
                    ATSAnalysis.job_url == job_url,
                    ATSAnalysis.created_at >= cache_cutoff,
                )
                .order_by(ATSAnalysis.created_at.desc())
                .first()
            )

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
        cv_document = Document.query.filter_by(user_id=current_user.id, doc_type="lebenslauf").first()

        if not cv_document:
            return jsonify(
                {
                    "success": False,
                    "error": "Kein Lebenslauf hochgeladen. Bitte laden Sie zuerst Ihren Lebenslauf hoch.",
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
                job_text_hash = ATSAnalysis.hash_job_text(job_text)
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

            ats_analysis = ATSAnalysis(
                user_id=current_user.id,
                job_url=scraped_url,
                job_text_hash=job_text_hash,
                title=analysis_title,
                score=response_data["score"],
                result_json=json.dumps(response_data),
            )
            db.session.add(ats_analysis)
            db.session.commit()

            response_data["analysis_id"] = ats_analysis.id
            response_data["cached"] = False

            if scraped_url:
                response_data["job_url"] = scraped_url

            return jsonify({"success": True, "data": response_data}), 200

        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Analyse fehlgeschlagen: {str(e)}"}), 500

    return rate_limited_analyze()


@ats_bp.route("/history", methods=["GET"])
@jwt_required_custom
def get_history(current_user):
    """
    Get the user's ATS analysis history.

    Returns the last 20 analyses ordered by date (newest first).

    Returns:
        200: { success: true, data: { analyses: [...] } }
    """
    analyses = (
        ATSAnalysis.query.filter_by(user_id=current_user.id).order_by(ATSAnalysis.created_at.desc()).limit(20).all()
    )

    return jsonify({"success": True, "data": {"analyses": [a.to_summary_dict() for a in analyses]}}), 200


@ats_bp.route("/history/<int:analysis_id>", methods=["GET"])
@jwt_required_custom
def get_analysis(current_user, analysis_id):
    """
    Get a specific ATS analysis by ID.

    Returns:
        200: { success: true, data: { ... full analysis result ... } }
        404: Analysis not found
    """
    analysis = ATSAnalysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()

    if not analysis:
        return jsonify({"success": False, "error": "Analyse nicht gefunden"}), 404

    return jsonify({"success": True, "data": analysis.to_dict()}), 200


@ats_bp.route("/history/<int:analysis_id>", methods=["DELETE"])
@jwt_required_custom
def delete_analysis(current_user, analysis_id):
    """
    Delete a specific ATS analysis by ID.

    Returns:
        200: { success: true, message: "..." }
        404: Analysis not found
    """
    analysis = ATSAnalysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()

    if not analysis:
        return jsonify({"success": False, "error": "Analyse nicht gefunden"}), 404

    db.session.delete(analysis)
    db.session.commit()

    return jsonify({"success": True, "message": "Analyse gelöscht"}), 200
