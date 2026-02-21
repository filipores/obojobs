"""
Route handlers for application generation.

Handles generate, generate-from-url, generate-from-url-stream, and generate-from-text endpoints.
"""

import json
import logging
import os
import queue
import tempfile
import threading
from typing import Any

from flask import Response, current_app, jsonify, request

from middleware.api_key_required import api_key_required
from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import (
    check_subscription_limit,
    decrement_application_count,
    get_subscription_usage,
)
from routes.applications import applications_bp
from services import application_service
from services.generator import BewerbungsGenerator
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
from services.subscription_data_service import get_user as get_user_by_id
from services.web_scraper import WebScraper

logger = logging.getLogger(__name__)

# Fields to check for profile completeness warnings
_PROFILE_FIELDS = ["full_name", "phone", "address", "city", "postal_code"]


def _get_profile_warning(user: Any) -> dict[str, Any] | None:
    """Check if user profile is missing key contact fields.

    Returns a dict with 'incomplete' and 'missing_fields' if any fields
    are empty, or None if profile is complete.
    """
    missing = [f for f in _PROFILE_FIELDS if not getattr(user, f, None)]
    if missing:
        return {"incomplete": True, "missing_fields": missing}
    return None


def _add_generation_warnings(result: dict, generator: BewerbungsGenerator, user: Any) -> None:
    """Attach pipeline warnings and profile completeness warnings to the response."""
    if generator.warnings:
        result["warnings"] = generator.warnings
    profile_warning = _get_profile_warning(user)
    if profile_warning:
        result["profile_warning"] = profile_warning


def _resolve_job_data(
    url: str,
    user_company: str,
    user_description: str,
) -> tuple[str, str]:
    """Resolve company name and job text from user-provided data or by scraping.

    Returns (company, job_text). Raises ValueError if scraping yields no text.
    """
    scraper = WebScraper()

    if user_description:
        company = user_company or scraper.extract_company_name_from_url(url)
        return company, user_description

    # Always scrape when no description provided (even if company is known)
    job_data = scraper.fetch_job_posting(url)
    if not job_data.get("text"):
        raise ValueError("Konnte keine Stellenanzeige von der URL laden. Bitte prüfe die URL.")

    company = user_company or job_data.get("company") or scraper.extract_company_name_from_url(url)
    return company, job_data["text"]


def _build_user_details(data: dict[str, Any]) -> dict[str, Any] | None:
    """Build user_details dict from request data if user provided edited preview data.

    Returns None if no user-edited data is present.
    """
    user_company = data.get("company", "").strip()
    user_description = data.get("description", "").strip()

    if not user_company and not user_description:
        return None

    return {
        "position": data.get("title", "").strip(),
        "contact_person": data.get("contact_person", "").strip(),
        "contact_email": data.get("contact_email", "").strip(),
        "location": data.get("location", "").strip(),
        "description": user_description,
        "quelle": data.get("quelle", "").strip() or None,
    }


def _build_generation_result(
    latest: Any,
    pdf_path: str,
    usage: dict,
    generator: BewerbungsGenerator,
    user: Any,
    company: str,
) -> dict[str, Any]:
    """Build the standard generation response dict."""
    result = {
        "success": True,
        "application": latest.to_dict() if latest else None,
        "pdf_path": pdf_path,
        "usage": usage,
        "message": f"Bewerbung für {company} erstellt",
    }
    _add_generation_warnings(result, generator, user)
    return result


def calculate_and_store_job_fit(app: Any, job_description: str, user_id: int) -> None:
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

        # Save requirements (clears existing first)
        application_service.save_requirements(app.id, extracted_requirements)

        # Calculate job-fit score
        calculator = JobFitCalculator()
        result = calculator.calculate_job_fit(user_id, app.id)

        # Store the overall score in the application
        application_service.update_application_fields(app, job_fit_score=result.overall_score)

    except Exception as e:
        # Log but don't fail - job-fit is optional
        logger.warning("Failed to calculate job-fit for app %s: %s", app.id, e)


def start_job_fit_calculation(application: Any, job_description: str, user_id: int) -> None:
    """Start job-fit calculation in a background thread.

    The calculation runs asynchronously and doesn't block the response.
    """
    flask_app = current_app._get_current_object()

    def run_with_context():
        with flask_app.app_context():
            calculate_and_store_job_fit(application, job_description, user_id)

    thread = threading.Thread(target=run_with_context, daemon=True)
    thread.start()


@applications_bp.route("/generate", methods=["POST"])
@api_key_required  # Extension uses API key
@check_subscription_limit
def generate_application(current_user: Any) -> tuple[Response, int]:
    """Generate a new application (FROM EXTENSION ONLY)"""
    data = request.json
    company = data.get("company")
    text = data.get("text")
    url = data.get("url", "")
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

        # Generate application
        generator = BewerbungsGenerator(user_id=current_user.id)
        generator.prepare()
        pdf_path = generator.generate_bewerbung(stellenanzeige_source, company)

        # Get latest application
        latest = application_service.get_latest_application(current_user.id)

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
        _add_generation_warnings(result, generator, current_user)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@applications_bp.route("/generate-from-url", methods=["POST"])
@jwt_required_custom
@check_subscription_limit
def generate_from_url(current_user: Any) -> tuple[Response, int]:
    """Generate a new application from URL (Web App)

    Accepts optional user-edited data from the preview step. If provided,
    uses the edited data instead of re-scraping the URL.
    """
    data = request.json
    url = data.get("url", "").strip()
    tone = data.get("tone", "modern")
    model = data.get("model", "qwen")
    user_company = data.get("company", "").strip()
    user_description = data.get("description", "").strip()

    if not url:
        return jsonify({"success": False, "error": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."}), 400

    try:
        company, job_text = _resolve_job_data(url, user_company, user_description)
        user_details = _build_user_details(data)

        generator = BewerbungsGenerator(user_id=current_user.id, model=model)
        generator.prepare()
        pdf_path = generator.generate_bewerbung(url, company, user_details=user_details, tonalitaet=tone)

        latest = application_service.get_latest_application(current_user.id)
        if latest:
            fit_score = data.get("fit_score")
            if fit_score is not None:
                application_service.update_application_fields(latest, job_fit_score=int(fit_score))
            elif job_text:
                start_job_fit_calculation(latest, job_text, current_user.id)

        usage = get_subscription_usage(current_user)
        result = _build_generation_result(latest, pdf_path, usage, generator, current_user, company)

        return jsonify(result), 200

    except ValueError as e:
        # Missing documents error from generator -- rollback the counter
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        # Generation failed -- rollback the counter
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": f"Fehler bei der Generierung: {str(e)}"}), 500


@applications_bp.route("/generate-from-url-stream", methods=["POST"])
@jwt_required_custom
@check_subscription_limit
def generate_from_url_stream(current_user: Any) -> Response:
    """Generate a new application from URL with SSE progress streaming.

    Streams progress events as Server-Sent Events (SSE) while the generation
    pipeline runs in a background thread. Falls back gracefully -- the original
    generate-from-url endpoint remains available as a non-streaming alternative.
    """
    data = request.json
    url = data.get("url", "").strip()
    tone = data.get("tone", "modern")
    model = data.get("model", "qwen")

    if not url:
        return jsonify({"success": False, "error": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."}), 400

    # Capture Flask app and user_id for the background thread (avoids detached instances)
    flask_app = current_app._get_current_object()
    user_id = current_user.id
    user_company = data.get("company", "").strip()
    user_description = data.get("description", "").strip()
    user_details = _build_user_details(data)
    fit_score = data.get("fit_score")

    progress_queue = queue.Queue()
    result_holder = {"result": None, "error": None}

    def thinking_cb(text):
        progress_queue.put({"type": "thinking", "text": text})

    def content_cb(text):
        progress_queue.put({"type": "content", "text": text})

    def run_generation():
        with flask_app.app_context():
            user = get_user_by_id(user_id)
            try:
                company, job_text = _resolve_job_data(url, user_company, user_description)

                generator = BewerbungsGenerator(
                    user_id=user_id,
                    progress_callback=progress_queue.put,
                    model=model,
                    thinking_callback=thinking_cb if model == "kimi" else None,
                    content_callback=content_cb if model == "kimi" else None,
                )
                generator.prepare()
                pdf_path = generator.generate_bewerbung(
                    url,
                    company,
                    user_details=user_details,
                    tonalitaet=tone,
                )

                if model == "kimi":
                    progress_queue.put({"type": "thinking_done"})

                latest = application_service.get_latest_application(user_id)
                if latest:
                    if fit_score is not None:
                        application_service.update_application_fields(latest, job_fit_score=int(fit_score))
                    elif job_text:
                        calculate_and_store_job_fit(latest, job_text, user_id)

                usage = get_subscription_usage(user)
                result_holder["result"] = _build_generation_result(
                    latest,
                    pdf_path,
                    usage,
                    generator,
                    user,
                    company,
                )

            except ValueError as e:
                decrement_application_count(user)
                result_holder["error"] = str(e)
            except Exception as e:
                decrement_application_count(user)
                logger.exception("SSE generation failed for user %s", user_id)
                result_holder["error"] = f"Fehler bei der Generierung: {str(e)}"
            finally:
                progress_queue.put(None)  # Signal: generation complete

    def generate_events():
        gen_thread = threading.Thread(target=run_generation, daemon=True)
        gen_thread.start()

        while True:
            try:
                event = progress_queue.get(timeout=120)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

        gen_thread.join(timeout=5)

        if result_holder["error"]:
            yield f"data: {json.dumps({'type': 'error', 'error': result_holder['error']})}\n\n"
        elif result_holder["result"]:
            yield f"data: {json.dumps({'type': 'complete', **result_holder['result']})}\n\n"

    return Response(
        generate_events(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@applications_bp.route("/generate-from-text", methods=["POST"])
@jwt_required_custom
@check_subscription_limit
def generate_from_text(current_user: Any) -> tuple[Response, int]:
    """Generate a new application from manually pasted job posting text.

    This is a fallback when URL scraping fails. The user pastes the job
    posting text directly, and we generate the application from that.
    """
    data = request.json or {}
    job_text = data.get("job_text", "").strip()
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()
    tone = data.get("tone", "modern")
    model = data.get("model", "qwen")
    description = data.get("description", "").strip()  # Structured description for interview prep

    if not job_text:
        return jsonify({"success": False, "error": "Stellentext ist erforderlich"}), 400

    if len(job_text) < 100:
        return jsonify({"success": False, "error": "Stellentext zu kurz. Bitte füge den vollständigen Text ein."}), 400

    if not company:
        return jsonify({"success": False, "error": "Firmenname ist erforderlich"}), 400

    # Write job text to a temp file for the generator pipeline
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(job_text)
        temp_file = f.name

    try:
        generator = BewerbungsGenerator(user_id=current_user.id, model=model)
        generator.prepare()
        pdf_path = generator.generate_bewerbung(temp_file, company, tonalitaet=tone)

        latest = application_service.get_latest_application(current_user.id)

        if latest:
            updates = {}
            if title:
                updates["position"] = title
            if description:
                updates["notizen"] = description
            if updates:
                application_service.update_application_fields(latest, **updates)

            start_job_fit_calculation(latest, job_text, current_user.id)

        usage = get_subscription_usage(current_user)
        result = _build_generation_result(latest, pdf_path, usage, generator, current_user, company)

        return jsonify(result), 200

    except ValueError as e:
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        decrement_application_count(current_user)
        return jsonify({"success": False, "error": f"Fehler bei der Generierung: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
