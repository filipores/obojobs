import json
import os
import re

from flask import jsonify, request

from middleware.jwt_required import jwt_required_custom
from routes.applications import applications_bp
from services import application_service
from services.ats_optimizer import ATSOptimizer
from services.web_scraper import WebScraper


def _extract_cover_letter_text(app):
    """Try to get cover letter text from email_text or PDF."""
    if app.email_text:
        return app.email_text

    if app.pdf_path and os.path.exists(app.pdf_path):
        try:
            import fitz  # PyMuPDF

            with fitz.open(app.pdf_path) as doc:
                return "".join(page.get_text() for page in doc)
        except Exception:
            pass

    return ""


@applications_bp.route("/<int:app_id>/ats-check", methods=["POST"])
@jwt_required_custom
def check_ats_compatibility(app_id, current_user):
    """Check ATS compatibility of a generated cover letter against the job posting.

    This endpoint analyzes the GENERATED application text against the original
    job posting to ensure important keywords are included for ATS systems.

    Request body:
        - cover_letter_text: (optional) The cover letter text to analyze.
          If not provided, will try to extract from the stored PDF or email_text.
        - job_description: (optional) The job posting text.
          If not provided, will try to fetch from the application's quelle URL.

    Returns:
        - ats_score: 0-100 compatibility score
        - missing_keywords: Important keywords not found in cover letter
        - keyword_suggestions: How to naturally incorporate missing keywords
        - format_issues: Formatting problems that may affect ATS parsing
        - keyword_density: Count of each keyword in the cover letter
    """
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    cover_letter_text = data.get("cover_letter_text", "")
    job_description = data.get("job_description", "")

    # Try to get cover letter text if not provided
    if not cover_letter_text:
        cover_letter_text = _extract_cover_letter_text(app)

    if not cover_letter_text:
        return jsonify(
            {
                "success": False,
                "error": "Kein Bewerbungstext vorhanden. Bitte gib den Text an oder stelle sicher, dass eine Bewerbung generiert wurde.",
            }
        ), 400

    # Try to get job description if not provided
    if not job_description:
        # Try from notizen (might contain job description)
        if app.notizen and "[Draft - Job-Fit Analyse]" in app.notizen:
            job_description = app.notizen.replace("[Draft - Job-Fit Analyse]", "").strip()
        elif app.notizen and len(app.notizen.strip()) >= 100:
            # Manual text flow stores job description in notizen
            job_description = app.notizen.strip()
        # Try to scrape from quelle URL
        elif app.quelle and app.quelle.startswith(("http://", "https://")):
            try:
                scraper = WebScraper()
                job_data = scraper.fetch_job_posting(app.quelle)
                job_description = job_data.get("text", "")
            except Exception:
                pass

    if not job_description:
        return jsonify(
            {"success": False, "error": "Keine Stellenbeschreibung vorhanden. Bitte gib den Stellentext an."}
        ), 400

    # Ensure both are strings (not dicts from JSON fields)
    if not isinstance(cover_letter_text, str):
        cover_letter_text = str(cover_letter_text)
    if not isinstance(job_description, str):
        job_description = str(job_description)

    try:
        optimizer = ATSOptimizer()
        result = optimizer.analyze_cover_letter(cover_letter_text, job_description)

        return jsonify(
            {
                "success": True,
                "data": {
                    "ats_score": result["ats_score"],
                    "missing_keywords": result["missing_keywords"],
                    "keyword_suggestions": result["keyword_suggestions"],
                    "format_issues": result["format_issues"],
                    "keyword_density": result["keyword_density"],
                    "found_keywords": result.get("found_keywords", []),
                },
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der ATS-Analyse: {str(e)}"}), 500


@applications_bp.route("/<int:app_id>/ats-optimize", methods=["POST"])
@jwt_required_custom
def optimize_cover_letter_for_ats(app_id, current_user):
    """Optimize a cover letter for ATS compatibility using AI.

    Takes the current cover letter and missing keywords, and returns
    an optimized version that naturally incorporates the keywords.

    Request body:
        - cover_letter_text: (optional) The cover letter text to optimize.
          If not provided, will try to extract from the stored PDF or email_text.
        - job_description: (optional) The job posting text.
          If not provided, will try to fetch from the application's quelle URL.
        - missing_keywords: (optional) List of keywords to incorporate.
          If not provided, will be determined from ATS analysis.

    Returns:
        - original_text: The original cover letter text
        - optimized_text: The optimized cover letter text
        - changes_made: List of changes/keywords incorporated
    """
    from anthropic import Anthropic

    from config import config

    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    cover_letter_text = data.get("cover_letter_text", "")
    job_description = data.get("job_description", "")
    missing_keywords = data.get("missing_keywords", [])

    # Try to get cover letter text if not provided
    if not cover_letter_text:
        cover_letter_text = _extract_cover_letter_text(app)

    if not cover_letter_text:
        return jsonify({"success": False, "error": "Kein Bewerbungstext vorhanden. Bitte gib den Text an."}), 400

    # Try to get job description if not provided
    if not job_description:
        if app.notizen and "[Draft - Job-Fit Analyse]" in app.notizen:
            job_description = app.notizen.replace("[Draft - Job-Fit Analyse]", "").strip()
        elif app.quelle and app.quelle.startswith(("http://", "https://")):
            try:
                scraper = WebScraper()
                job_data = scraper.fetch_job_posting(app.quelle)
                job_description = job_data.get("text", "")
            except Exception:
                pass

    if not job_description:
        return jsonify(
            {"success": False, "error": "Keine Stellenbeschreibung vorhanden. Bitte gib den Stellentext an."}
        ), 400

    # If no missing keywords provided, perform ATS analysis first
    if not missing_keywords:
        try:
            optimizer = ATSOptimizer()
            ats_result = optimizer.analyze_cover_letter(cover_letter_text, job_description)
            missing_keywords = ats_result.get("missing_keywords", [])
        except Exception:
            pass

    if not missing_keywords:
        return jsonify(
            {
                "success": True,
                "data": {
                    "original_text": cover_letter_text,
                    "optimized_text": cover_letter_text,
                    "changes_made": [],
                    "message": "Keine fehlenden Keywords - Bewerbung ist bereits gut optimiert.",
                },
            }
        ), 200

    # Use Claude to optimize the cover letter
    try:
        api_key = config.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")

        client = Anthropic(api_key=api_key)

        prompt = f"""Du bist ein Experte für Bewerbungsoptimierung. Optimiere das folgende Anschreiben für ATS-Systeme (Applicant Tracking Systems).

WICHTIG: Der Ton und Stil des Anschreibens MÜSSEN erhalten bleiben. Die Änderungen sollen subtil und natürlich sein.

STELLENANZEIGE:
{job_description[:3000]}

AKTUELLES ANSCHREIBEN:
{cover_letter_text}

FEHLENDE KEYWORDS (diese natürlich einbauen):
{", ".join(missing_keywords[:10])}

AUFGABE:
1. Baue die fehlenden Keywords natürlich in den Text ein
2. Verändere NICHT den grundlegenden Ton und Stil
3. Halte die Länge ähnlich zum Original
4. Mache keine Stiländerungen außer dem Einbau der Keywords

Antworte im JSON-Format:
{{
  "optimized_text": "Der vollständig optimierte Bewerbungstext...",
  "changes_made": [
    "Keyword 'Python' in Absatz 2 eingebaut",
    "Keyword 'Teamarbeit' im Schlusssatz hinzugefügt"
  ]
}}

Antworte NUR mit dem JSON, keine zusätzlichen Erklärungen."""

        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text.strip()

        # Parse JSON response
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            return jsonify({"success": False, "error": "Fehler bei der KI-Optimierung: Ungültiges Antwortformat"}), 500

        result = json.loads(json_match.group())
        optimized_text = result.get("optimized_text", cover_letter_text)
        changes_made = result.get("changes_made", [])

        # Update the application's email_text with optimized version
        application_service.save_application_email_text(app, optimized_text)

        return jsonify(
            {
                "success": True,
                "data": {
                    "original_text": cover_letter_text,
                    "optimized_text": optimized_text,
                    "changes_made": changes_made,
                },
            }
        ), 200

    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Fehler bei der KI-Optimierung: JSON-Parsing fehlgeschlagen"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der KI-Optimierung: {str(e)}"}), 500
