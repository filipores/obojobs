import os
import tempfile

from flask import Blueprint, jsonify, request, send_file

from middleware.api_key_required import api_key_required
from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import (
    check_subscription_limit,
    get_subscription_usage,
    increment_application_count,
)
from models import Application, Template, db
from services.generator import BewerbungsGenerator
from services.web_scraper import WebScraper

applications_bp = Blueprint("applications", __name__)


@applications_bp.route("", methods=["GET"])
@jwt_required_custom
def list_applications(current_user):
    """List user's applications"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = (
        Application.query.filter_by(user_id=current_user.id)
        .order_by(Application.datum.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "success": True,
            "applications": [app.to_dict() for app in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    ), 200


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
        pdf_path = generator.generate_bewerbung(stellenanzeige_source, company)

        # Get latest application
        latest = Application.query.filter_by(user_id=current_user.id).order_by(Application.datum.desc()).first()

        # Cleanup temp file (if created)
        if not (url and url.startswith(("http://", "https://"))):
            temp_path = stellenanzeige_source
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        # Increment subscription usage counter
        increment_application_count(current_user)

        # Get updated usage info
        usage = get_subscription_usage(current_user)

        return jsonify(
            {
                "success": True,
                "pdf_path": pdf_path,
                "company": company,
                "position": latest.position if latest else "",
                "email": latest.email if latest else "",
                "betreff": latest.betreff if latest else "",
                "usage": usage,
                "message": f"Bewerbung für {company} erstellt",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@applications_bp.route("/generate-from-url", methods=["POST"])
@jwt_required_custom
@check_subscription_limit
def generate_from_url(current_user):
    """Generate a new application from URL (Web App)"""
    data = request.json
    url = data.get("url", "").strip()
    template_id = data.get("template_id")

    if not url:
        return jsonify({"success": False, "error": "URL ist erforderlich"}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"success": False, "error": "Ungültige URL. Bitte mit http:// oder https:// beginnen."}), 400

    try:
        # Scrape the job posting
        scraper = WebScraper()
        job_data = scraper.fetch_job_posting(url)

        if not job_data.get("text"):
            return jsonify(
                {"success": False, "error": "Konnte keine Stellenanzeige von der URL laden. Bitte prüfe die URL."}
            ), 400

        # Extract company name from URL
        company = scraper.extract_company_name_from_url(url)

        # Validate template if provided
        if template_id:
            template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()
            if not template:
                return jsonify({"success": False, "error": "Template nicht gefunden"}), 404

        # Generate application using existing generator
        generator = BewerbungsGenerator(user_id=current_user.id, template_id=template_id)
        pdf_path = generator.generate_bewerbung(url, company)

        # Get the newly created application
        latest = Application.query.filter_by(user_id=current_user.id).order_by(Application.datum.desc()).first()

        # Increment subscription usage counter
        increment_application_count(current_user)

        # Get updated usage info
        usage = get_subscription_usage(current_user)

        return jsonify(
            {
                "success": True,
                "application": latest.to_dict() if latest else None,
                "pdf_path": pdf_path,
                "usage": usage,
                "message": f"Bewerbung für {company} erstellt",
            }
        ), 200

    except ValueError as e:
        # Missing documents error from generator
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Generierung: {str(e)}"}), 500


@applications_bp.route("/<int:app_id>", methods=["GET"])
@jwt_required_custom
def get_application(app_id, current_user):
    """Get application details"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    return jsonify({"success": True, "application": app.to_dict()}), 200


@applications_bp.route("/<int:app_id>", methods=["PUT"])
@jwt_required_custom
def update_application(app_id, current_user):
    """Update application (status, notes)"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    data = request.json

    if "status" in data:
        app.status = data["status"]
    if "notizen" in data:
        app.notizen = data["notizen"]

    db.session.commit()

    return jsonify({"success": True, "application": app.to_dict()}), 200


@applications_bp.route("/<int:app_id>", methods=["DELETE"])
@jwt_required_custom
def delete_application(app_id, current_user):
    """Delete application"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    # Delete PDF file
    if app.pdf_path and os.path.exists(app.pdf_path):
        os.remove(app.pdf_path)

    db.session.delete(app)
    db.session.commit()

    return jsonify({"success": True, "message": "Application deleted"}), 200


@applications_bp.route("/<int:app_id>/pdf", methods=["GET"])
@jwt_required_custom
def download_pdf(app_id, current_user):
    """Download application PDF"""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"error": "Application not found"}), 404

    if not app.pdf_path or not os.path.exists(app.pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    return send_file(app.pdf_path, as_attachment=True, download_name=f"Anschreiben_{app.firma}.pdf")
