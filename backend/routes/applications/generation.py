import logging
import os
import tempfile

from flask import jsonify, request

from middleware.api_key_required import api_key_required
from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import (
    check_subscription_limit,
    decrement_application_count,
    get_subscription_usage,
)
from models import Application, JobRequirement, Template, db
from routes.applications import applications_bp
from services.contact_extractor import ContactExtractor
from services.generator import BewerbungsGenerator
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
from services.web_scraper import WebScraper

# Display names for job portal identifiers returned by WebScraper
PORTAL_DISPLAY_NAMES = {
    "stepstone": "StepStone",
    "indeed": "Indeed",
    "xing": "XING",
}

# HTTP status codes that indicate a client-side scraping error (not a server bug)
_SCRAPER_CLIENT_ERROR_CODES = ("403", "404", "429", "400", "401", "502", "503")

# Fields to check for profile completeness warnings
_PROFILE_FIELDS = ["full_name", "phone", "address", "city", "postal_code"]


def _get_profile_warning(user):
    """Check if user profile is missing key contact fields.

    Returns a dict with 'incomplete' and 'missing_fields' if any fields
    are empty, or None if profile is complete.
    """
    missing = [f for f in _PROFILE_FIELDS if not getattr(user, f, None)]
    if missing:
        return {"incomplete": True, "missing_fields": missing}
    return None


def _is_scraper_client_error(error_message: str) -> bool:
    """Check if a scraper error message indicates a client-side HTTP error."""
    return any(code in error_message for code in _SCRAPER_CLIENT_ERROR_CODES)


def calculate_and_store_job_fit(app, job_description, user_id):
    """Calculate job-fit score after generation and store it in the application.

    This runs in the background and doesn't block the generation response.
    If it fails, the application is still created - job-fit is just unavailable.
    """
    try:
        # Analyze requirements from job description
        analyzer = RequirementAnalyzer()
        extracted_requirements = analyzer.analyze_requirements(job_description)

        if not extracted_requirements:
            return  # No requirements found, can't calculate job-fit

        # Clear any existing requirements (shouldn't exist for new app, but be safe)
        JobRequirement.query.filter_by(application_id=app.id).delete()

        # Save requirements
        for req_data in extracted_requirements:
            requirement = JobRequirement(
                application_id=app.id,
                requirement_text=req_data["requirement_text"],
                requirement_type=req_data["requirement_type"],
                skill_category=req_data.get("skill_category"),
            )
            db.session.add(requirement)
        db.session.commit()

        # Calculate job-fit score
        calculator = JobFitCalculator()
        result = calculator.calculate_job_fit(user_id, app.id)

        # Store the overall score in the application
        app.job_fit_score = result.overall_score
        db.session.commit()

    except Exception as e:
        # Log but don't fail - job-fit is optional
        logging.warning(f"Failed to calculate job-fit for app {app.id}: {e}")


@applications_bp.route("/generate", methods=["POST"])
@api_key_required  # Extension uses API key
@check_subscription_limit
def generate_application(current_user):
    """Generate a new application (FROM EXTENSION ONLY)"""
    data = request.json
    company = data.get("company")
    text = data.get("text")
    url = data.get("url", "")
    template_id = data.get("template_id")  # Optional template selection

    if not company or not text:
        return jsonify({"error": "Company and text are required"}), 400

    try:
        # If URL is provided, use it directly for link extraction
        # Otherwise create temp file with text
        if url and url.startswith(("http://", "https://")):
            # Use URL directly - generator will scrape and extract links
            stellenanzeige_source = url
        else:
            # Create temporary file for job posting text
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                if url:
                    f.write(f"URL: {url}\n\n")
                f.write(text)
                stellenanzeige_source = f.name

        # Generate application with optional template
        generator = BewerbungsGenerator(user_id=current_user.id, template_id=template_id)
        generator.prepare()
        pdf_path = generator.generate_bewerbung(stellenanzeige_source, company)

        # Get latest application
        latest = Application.query.filter_by(user_id=current_user.id).order_by(Application.datum.desc()).first()

        # Cleanup temp file (if created)
        if not (url and url.startswith(("http://", "https://"))):
            temp_path = stellenanzeige_source
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        # Get updated usage info (increment already done by @check_subscription_limit)
        usage = get_subscription_usage(current_user)

        result = {
            "success": True,
            "pdf_path": pdf_path,
            "company": company,
            "position": latest.position if latest else "",
            "email": latest.email if latest else "",
            "betreff": latest.betreff if latest else "",
            "usage": usage,
            "message": f"Bewerbung für {company} erstellt",
        }
        profile_warning = _get_profile_warning(current_user)
        if profile_warning:
            result["profile_warning"] = profile_warning

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@applications_bp.route("/quick-extract", methods=["POST"])
@jwt_required_custom
def quick_extract(current_user):
    """Quick extraction of company and title from job URL for minimal confirmation flow.

    Returns only the essential fields needed for a quick confirmation dialog:
    - company: The company name
    - title: The job position title

    This is faster than the full preview-job endpoint since it doesn't extract
    the full description and other optional fields.
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

        # Fetch structured job data (uses same scraper but we only return essential fields)
        job_data = scraper.fetch_structured_job_posting(url)

        # Extract only company and title
        company = (job_data.get("company") or "").strip()
        title = (job_data.get("title") or "").strip()

        # If both are missing, extraction failed
        if not company and not title:
            return jsonify(
                {
                    "success": False,
                    "error": "Konnte keine Stellendaten extrahieren. Bitte verwenden Sie die manuelle Eingabe.",
                    "use_manual_input": True,
                }
            ), 400

        return jsonify(
            {
                "success": True,
                "data": {
                    "company": company,
                    "title": title,
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
                "error": "Fehler beim Laden der Stellenanzeige. Bitte versuchen Sie es erneut oder verwenden Sie die manuelle Eingabe.",
            }
        ), 500


@applications_bp.route("/preview-job", methods=["POST"])
@jwt_required_custom
def preview_job(current_user):
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
        if not job_data.get("title"):
            missing_fields.append("Titel")
        if not job_data.get("company"):
            missing_fields.append("Firma")
        if not job_data.get("description") and not job_data.get("text"):
            missing_fields.append("Beschreibung")

        # If ALL required fields are missing, scraping failed completely
        has_title = bool((job_data.get("title") or "").strip())
        has_company = bool((job_data.get("company") or "").strip())
        has_description = bool((job_data.get("description") or "").strip() or (job_data.get("text") or "").strip())

        if not has_title and not has_company and not has_description:
            return jsonify(
                {
                    "success": False,
                    "error": "Konnte keine Stellenanzeige von der URL laden. Die Seite scheint keine Stellenanzeige zu enthalten oder ist nicht zugänglich. Bitte verwenden Sie die manuelle Eingabe.",
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

        logging.warning(f"preview-job server error for {url}: {error_message}")
        return jsonify(
            {
                "success": False,
                "error": "Fehler beim Laden der Stellenanzeige. Bitte versuchen Sie es erneut oder verwenden Sie die manuelle Eingabe.",
            }
        ), 500


@applications_bp.route("/analyze-manual-text", methods=["POST"])
@jwt_required_custom
def analyze_manual_text(current_user):
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
                "error": "Stellentext zu kurz. Bitte fügen Sie den vollständigen Text der Stellenanzeige ein.",
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
                if not extracted_title and 5 < len(line) < 100:
                    # First short line might be the title
                    if any(
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


@applications_bp.route("/generate-from-url", methods=["POST"])
@jwt_required_custom
@check_subscription_limit
def generate_from_url(current_user):
    """Generate a new application from URL (Web App)

    Accepts optional user-edited data from the preview step. If provided,
    uses the edited data instead of re-scraping the URL.
    """
    data = request.json
    url = data.get("url", "").strip()
    template_id = data.get("template_id")

    # Optional user-edited data from preview step
    user_company = data.get("company", "").strip()
    user_title = data.get("title", "").strip()
    user_contact_person = data.get("contact_person", "").strip()
    user_contact_email = data.get("contact_email", "").strip()
    user_location = data.get("location", "").strip()
    user_description = data.get("description", "").strip()

    if not url:
        return jsonify({"success": False, "error": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."}), 400

    try:
        scraper = WebScraper()

        # If user provided edited data from preview, use it
        # Otherwise fall back to scraping
        if user_company or user_description:
            # Use user's edited data
            company = user_company if user_company else scraper.extract_company_name_from_url(url)
            job_text = user_description
        else:
            # Scrape the job posting (legacy flow)
            job_data = scraper.fetch_job_posting(url)

            if not job_data.get("text"):
                return jsonify(
                    {"success": False, "error": "Konnte keine Stellenanzeige von der URL laden. Bitte prüfe die URL."}
                ), 400

            # Extract company name - prefer scraped, fallback to URL extraction
            company = job_data.get("company") or scraper.extract_company_name_from_url(url)
            job_text = job_data.get("text")

        # Validate template if provided
        if template_id:
            template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()
            if not template:
                return jsonify({"success": False, "error": "Template nicht gefunden"}), 404

        # Build user_details dict if user provided edited data
        user_details = None
        if user_company or user_description:
            user_details = {
                "position": user_title,
                "contact_person": user_contact_person,
                "contact_email": user_contact_email,
                "location": user_location,
                "description": user_description,
                "quelle": data.get("quelle", "").strip() or None,
            }

        # Generate application using existing generator
        generator = BewerbungsGenerator(user_id=current_user.id, template_id=template_id)
        generator.prepare()
        pdf_path = generator.generate_bewerbung(url, company, user_details=user_details)

        # Get the newly created application
        latest = Application.query.filter_by(user_id=current_user.id).order_by(Application.datum.desc()).first()

        # Calculate and store job-fit score (non-blocking)
        if latest and job_text:
            calculate_and_store_job_fit(latest, job_text, current_user.id)

        # Get updated usage info (increment already done by @check_subscription_limit)
        usage = get_subscription_usage(current_user)

        result = {
            "success": True,
            "application": latest.to_dict() if latest else None,
            "pdf_path": pdf_path,
            "usage": usage,
            "message": f"Bewerbung für {company} erstellt",
        }
        profile_warning = _get_profile_warning(current_user)
        if profile_warning:
            result["profile_warning"] = profile_warning

        return jsonify(result), 200

    except ValueError as e:
        # Missing documents error from generator -- rollback the counter
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        # Generation failed -- rollback the counter
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": f"Fehler bei der Generierung: {str(e)}"}), 500


@applications_bp.route("/generate-from-text", methods=["POST"])
@jwt_required_custom
@check_subscription_limit
def generate_from_text(current_user):
    """Generate a new application from manually pasted job posting text.

    This is a fallback when URL scraping fails. The user pastes the job
    posting text directly, and we generate the application from that.
    """
    data = request.json or {}
    job_text = data.get("job_text", "").strip()
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()
    template_id = data.get("template_id")
    description = data.get("description", "").strip()  # Structured description for interview prep

    if not job_text:
        return jsonify({"success": False, "error": "Stellentext ist erforderlich"}), 400

    if len(job_text) < 100:
        return jsonify(
            {"success": False, "error": "Stellentext zu kurz. Bitte fügen Sie den vollständigen Text ein."}
        ), 400

    if not company:
        return jsonify({"success": False, "error": "Firmenname ist erforderlich"}), 400

    try:
        # Validate template if provided
        if template_id:
            template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()
            if not template:
                return jsonify({"success": False, "error": "Template nicht gefunden"}), 404

        # Save job text to temporary file for generator
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "job_posting.txt")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(job_text)

        try:
            # Generate application using existing generator with temp file
            generator = BewerbungsGenerator(user_id=current_user.id, template_id=template_id)
            generator.prepare()
            pdf_path = generator.generate_bewerbung(temp_file, company)

            # Get the newly created application
            latest = Application.query.filter_by(user_id=current_user.id).order_by(Application.datum.desc()).first()

            # Update application with title and description if provided
            if latest:
                if title:
                    latest.position = title
                # Store the structured description in notizen for interview prep
                if description:
                    latest.notizen = description
                db.session.commit()

                # Calculate and store job-fit score (non-blocking)
                calculate_and_store_job_fit(latest, job_text, current_user.id)

            # Get updated usage info (increment already done by @check_subscription_limit)
            usage = get_subscription_usage(current_user)

            result = {
                "success": True,
                "application": latest.to_dict() if latest else None,
                "pdf_path": pdf_path,
                "usage": usage,
                "message": f"Bewerbung für {company} erstellt",
            }
            profile_warning = _get_profile_warning(current_user)
            if profile_warning:
                result["profile_warning"] = profile_warning

            return jsonify(result), 200

        finally:
            # Cleanup temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    except ValueError as e:
        # Generation failed -- rollback the counter
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        # Generation failed -- rollback the counter
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": f"Fehler bei der Generierung: {str(e)}"}), 500
