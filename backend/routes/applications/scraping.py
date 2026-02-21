"""
Route handlers for job posting scraping and text analysis.

Handles quick-extract, preview-job, and analyze-manual-text endpoints.
"""

import logging
from typing import Any

from flask import Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from routes.applications import applications_bp
from services.contact_extractor import ContactExtractor
from services.web_scraper import WebScraper

logger = logging.getLogger(__name__)

# Display names for job portal identifiers returned by WebScraper
PORTAL_DISPLAY_NAMES = {
    "stepstone": "StepStone",
    "indeed": "Indeed",
    "xing": "XING",
}

# Patterns that indicate a scraper error we should pass through to the user (not a server bug)
_SCRAPER_ERROR_PATTERNS = (
    "403",
    "404",
    "429",
    "400",
    "401",
    "502",
    "503",
    "blockiert",
    "nicht gefunden",
    "nicht zugänglich",
    "konnte nicht geladen",
    "Zu viele Anfragen",
    "manuell",
    "manuelle Eingabe",
)


def _is_scraper_client_error(error_message: str) -> bool:
    """Check if a scraper error is user-facing (not an internal server bug)."""
    return any(pattern in error_message for pattern in _SCRAPER_ERROR_PATTERNS)


@applications_bp.route("/quick-extract", methods=["POST"])
@jwt_required_custom
def quick_extract(current_user: Any) -> tuple[Response, int]:
    """Quick extraction of job data from URL for minimal confirmation flow.

    Returns the essential fields (company, title, description) needed for
    a quick confirmation dialog, without extracting optional fields like
    location, contact person, or salary.
    """
    data = request.json
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"success": False, "error": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."}), 400

    try:
        scraper = WebScraper()

        # Detect job board for display
        job_board = scraper.detect_job_board(url)

        # Fetch structured job data (includes description to avoid re-scraping later)
        job_data = scraper.fetch_structured_job_posting(url)

        # Extract fields
        company = (job_data.get("company") or "").strip()
        title = (job_data.get("title") or "").strip()
        description = (job_data.get("description") or job_data.get("text") or "").strip()

        # If both are missing, extraction failed
        if not company and not title:
            return jsonify(
                {
                    "success": False,
                    "error": "Konnte keine Stellendaten extrahieren. Bitte verwende die manuelle Eingabe.",
                    "use_manual_input": True,
                }
            ), 400

        return jsonify(
            {
                "success": True,
                "data": {
                    "company": company,
                    "title": title,
                    "description": description,
                    "portal": PORTAL_DISPLAY_NAMES.get(job_board, "Sonstige"),
                    "portal_id": job_board or "generic",
                    "url": url,
                },
            }
        ), 200

    except Exception as e:
        error_message = str(e)

        if _is_scraper_client_error(error_message):
            return jsonify({"success": False, "error": error_message}), 400

        return jsonify(
            {
                "success": False,
                "error": "Fehler beim Laden der Stellenanzeige. Bitte versuche es erneut oder verwende die manuelle Eingabe.",
            }
        ), 500


@applications_bp.route("/preview-job", methods=["POST"])
@jwt_required_custom
def preview_job(current_user: Any) -> tuple[Response, int]:
    """Preview job posting data from URL before generating application.

    Returns structured job data including detected portal and all extracted fields.
    This allows the user to review and edit data before generating.
    """
    data = request.json
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"success": False, "error": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."}), 400

    try:
        scraper = WebScraper()

        # Detect job board
        job_board = scraper.detect_job_board(url)

        # Fetch structured job data
        job_data = scraper.fetch_structured_job_posting(url)

        # Check for missing important fields
        missing_fields = []
        if not (job_data.get("title") or "").strip():
            missing_fields.append("Titel")
        if not (job_data.get("company") or "").strip():
            missing_fields.append("Firma")
        if not ((job_data.get("description") or "").strip() or (job_data.get("text") or "").strip()):
            missing_fields.append("Beschreibung")

        # If ALL required fields are missing, scraping failed completely
        if len(missing_fields) == 3:
            return jsonify(
                {
                    "success": False,
                    "error": "Konnte keine Stellenanzeige von der URL laden. Die Seite scheint keine Stellenanzeige zu enthalten oder ist nicht zugänglich. Bitte verwende die manuelle Eingabe.",
                    "use_manual_input": True,
                }
            ), 400

        return jsonify(
            {
                "success": True,
                "data": {
                    "portal": PORTAL_DISPLAY_NAMES.get(job_board, "Sonstige"),
                    "portal_id": job_board or "generic",
                    "url": url,
                    "title": job_data.get("title"),
                    "company": job_data.get("company"),
                    "location": job_data.get("location"),
                    "description": job_data.get("description"),
                    "requirements": job_data.get("requirements"),
                    "contact_email": job_data.get("contact_email"),
                    "contact_person": job_data.get("contact_person"),
                    "posted_date": job_data.get("posted_date"),
                    "application_deadline": job_data.get("application_deadline"),
                    "employment_type": job_data.get("employment_type"),
                    "salary": job_data.get("salary"),
                    "company_profile_url": job_data.get("company_profile_url"),
                    "missing_fields": missing_fields,
                },
            }
        ), 200

    except Exception as e:
        error_message = str(e)

        if _is_scraper_client_error(error_message):
            return jsonify({"success": False, "error": error_message}), 400

        logger.warning("preview-job server error for %s: %s", url, error_message)
        return jsonify(
            {
                "success": False,
                "error": "Fehler beim Laden der Stellenanzeige. Bitte versuche es erneut oder verwende die manuelle Eingabe.",
            }
        ), 500


@applications_bp.route("/analyze-manual-text", methods=["POST"])
@jwt_required_custom
def analyze_manual_text(current_user: Any) -> tuple[Response, int]:
    """Analyze manually pasted job posting text as fallback when scraping fails.

    This endpoint allows users to paste job posting text directly when
    URL scraping fails (403, timeout, blocked by job portal, etc.)

    UX-004: Enhanced with NLP-based extraction of contact data, email, and location.
    """
    data = request.json or {}
    job_text = data.get("job_text", "").strip()
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()

    if not job_text:
        return jsonify({"success": False, "error": "Stellentext ist erforderlich"}), 400

    if len(job_text) < 100:
        return jsonify(
            {
                "success": False,
                "error": "Stellentext zu kurz. Bitte füge den vollständigen Text der Stellenanzeige ein.",
            }
        ), 400

    try:
        # Use ContactExtractor for NLP-based extraction (UX-004)
        extractor = ContactExtractor()
        contact_data = extractor.extract_contact_data(job_text)

        # Try to extract company and title from text if not provided
        extracted_company = company
        extracted_title = title

        if not extracted_company or not extracted_title:
            # Simple extraction from beginning of text
            lines = job_text.split("\n")[:10]
            for line in lines:
                line = line.strip()
                if (
                    not extracted_title
                    and 5 < len(line) < 100
                    and any(
                        keyword in line.lower()
                        for keyword in [
                            "entwickler",
                            "engineer",
                            "manager",
                            "consultant",
                            "analyst",
                            "designer",
                            "spezialist",
                            "berater",
                            "leiter",
                            "m/w/d",
                            "(m/w/d)",
                        ]
                    )
                ):
                    extracted_title = line
                if not extracted_company and ("gmbh" in line.lower() or "ag" in line.lower() or "se" in line.lower()):
                    extracted_company = line

        # Check for missing important fields
        missing_fields = []
        if not extracted_title:
            missing_fields.append("Titel")
        if not extracted_company:
            missing_fields.append("Firma")

        return jsonify(
            {
                "success": True,
                "data": {
                    "portal": "Manuell eingegeben",
                    "portal_id": "manual",
                    "url": None,
                    "title": extracted_title,
                    "company": extracted_company,
                    "location": contact_data.get("location"),
                    "description": job_text,
                    "requirements": None,
                    "contact_email": contact_data.get("contact_email"),
                    "contact_person": contact_data.get("contact_person"),
                    "posted_date": None,
                    "application_deadline": None,
                    "employment_type": contact_data.get("employment_type"),
                    "salary": None,
                    "company_profile_url": None,
                    "missing_fields": missing_fields,
                    "is_manual": True,
                },
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Textanalyse: {str(e)}"}), 500
