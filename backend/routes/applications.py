import csv
import io
import os
import tempfile
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, make_response, request, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from middleware.api_key_required import api_key_required
from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import (
    check_subscription_limit,
    get_subscription_usage,
    increment_application_count,
)
from models import Application, JobRequirement, Template, db
from services.generator import BewerbungsGenerator
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
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


@applications_bp.route("/timeline", methods=["GET"])
@jwt_required_custom
def get_timeline(current_user):
    """Get all applications with status history for timeline view.
    Supports filtering by time period: 7, 30, 90 days or all."""
    days_filter = request.args.get("days", "all")

    query = Application.query.filter_by(user_id=current_user.id)

    # Apply time filter
    if days_filter != "all":
        try:
            days = int(days_filter)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Application.datum >= cutoff_date)
        except ValueError:
            pass  # Invalid filter, show all

    # Order by date descending
    applications = query.order_by(Application.datum.desc()).all()

    # Build timeline data
    timeline_data = []
    for app in applications:
        app_dict = app.to_dict()
        # Ensure status_history is included (it's in to_dict now)
        # Add a timeline-specific format if no history exists
        if not app_dict.get("status_history"):
            # Create initial history from datum if none exists
            app_dict["status_history"] = [
                {"status": "erstellt", "timestamp": app_dict["datum"]}
            ]
        timeline_data.append(app_dict)

    return jsonify(
        {
            "success": True,
            "data": {
                "applications": timeline_data,
                "total": len(timeline_data),
                "filter": days_filter,
            },
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

        if not job_data.get("text") and not job_data.get("title"):
            return jsonify(
                {"success": False, "error": "Konnte keine Stellenanzeige von der URL laden. Bitte prüfe die URL."}
            ), 400

        # Map job board to display name
        portal_names = {
            "stepstone": "StepStone",
            "indeed": "Indeed",
            "xing": "XING",
        }

        # Check for missing important fields
        missing_fields = []
        if not job_data.get("title"):
            missing_fields.append("Titel")
        if not job_data.get("company"):
            missing_fields.append("Firma")
        if not job_data.get("description"):
            missing_fields.append("Beschreibung")

        return jsonify({
            "success": True,
            "data": {
                "portal": portal_names.get(job_board, "Sonstige"),
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
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler beim Laden der Stellenanzeige: {str(e)}"}), 500


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
        new_status = data["status"]
        # Only add to history if status actually changed
        if new_status != app.status:
            app.add_status_change(new_status)
        app.status = new_status
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


@applications_bp.route("/export", methods=["GET"])
@jwt_required_custom
def export_applications(current_user):
    """Export all applications as CSV or PDF.
    Query params:
    - format: 'csv' (default) or 'pdf'
    """
    export_format = request.args.get("format", "csv").lower()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Get all applications for user
    applications = (
        Application.query.filter_by(user_id=current_user.id)
        .order_by(Application.datum.desc())
        .all()
    )

    if export_format == "pdf":
        return _export_as_pdf(applications, today)
    else:
        return _export_as_csv(applications, today)


def _export_as_csv(applications, date_str):
    """Generate CSV export of applications."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)

    # Header row
    writer.writerow(["Firma", "Position", "Status", "Datum", "Ansprechpartner", "Email"])

    # Data rows
    for app in applications:
        datum_str = app.datum.strftime("%d.%m.%Y") if app.datum else ""
        writer.writerow([
            app.firma or "",
            app.position or "",
            _get_status_label(app.status),
            datum_str,
            app.ansprechpartner or "",
            app.email or "",
        ])

    # Create response with CSV
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=bewerbungen_{date_str}.csv"
    return response


def _export_as_pdf(applications, date_str):
    """Generate PDF export of applications with obojobs branding."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor("#3D5A6C"),  # AI color from design system
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#6B6B6B"),
        spaceAfter=20,
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = []

    # Header with obojobs branding
    story.append(Paragraph("obojobs", title_style))
    story.append(Paragraph(f"Bewerbungsübersicht • Exportiert am {date_str}", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))

    # Table data
    table_data = [["Firma", "Position", "Status", "Datum", "Kontakt", "Email"]]

    for app in applications:
        datum_str = app.datum.strftime("%d.%m.%Y") if app.datum else ""
        table_data.append([
            Paragraph(app.firma or "", cell_style),
            Paragraph(app.position or "", cell_style),
            _get_status_label(app.status),
            datum_str,
            Paragraph(app.ansprechpartner or "", cell_style),
            Paragraph(app.email or "", cell_style),
        ])

    # Create table with styling
    col_widths = [3 * cm, 4 * cm, 2.5 * cm, 2.2 * cm, 3 * cm, 3.5 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3D5A6C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),

        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),

        # Alternating row colors
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7F5F0"), colors.white]),

        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4C9BA")),

        # Alignment
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(table)

    # Footer info
    story.append(Spacer(1, 1 * cm))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#9B958F"),
    )
    story.append(Paragraph(f"Gesamt: {len(applications)} Bewerbungen", footer_style))

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=bewerbungen_{date_str}.pdf"
    return response


def _get_status_label(status):
    """Convert status code to readable label."""
    labels = {
        "erstellt": "Erstellt",
        "versendet": "Versendet",
        "antwort_erhalten": "Antwort",
        "absage": "Absage",
        "zusage": "Zusage",
    }
    return labels.get(status, status or "")


@applications_bp.route("/<int:app_id>/requirements", methods=["GET"])
@jwt_required_custom
def get_requirements(app_id, current_user):
    """Get job requirements for an application."""
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    # Get requirements from database
    requirements = JobRequirement.query.filter_by(application_id=app_id).all()

    # Group requirements by type
    must_have = [r.to_dict() for r in requirements if r.requirement_type == "must_have"]
    nice_to_have = [r.to_dict() for r in requirements if r.requirement_type == "nice_to_have"]

    return jsonify({
        "success": True,
        "data": {
            "application_id": app_id,
            "must_have": must_have,
            "nice_to_have": nice_to_have,
            "total": len(requirements),
        }
    }), 200


@applications_bp.route("/<int:app_id>/analyze-requirements", methods=["POST"])
@jwt_required_custom
def analyze_requirements(app_id, current_user):
    """Analyze and extract requirements from job posting for an application.

    This endpoint uses Claude API to extract requirements from the job posting text
    stored in the application's notizen field or from a provided URL.
    """
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    job_text = data.get("job_text")

    # If no job_text provided, try to get it from the application's source
    if not job_text:
        # Try to use notizen as fallback (might contain job description)
        if app.notizen:
            job_text = app.notizen
        # Or try to scrape from quelle URL if it's a valid URL
        elif app.quelle and app.quelle.startswith(("http://", "https://")):
            try:
                scraper = WebScraper()
                job_data = scraper.fetch_job_posting(app.quelle)
                job_text = job_data.get("text", "")
            except Exception:
                pass

    if not job_text:
        return jsonify({
            "success": False,
            "error": "Kein Stellentext vorhanden. Bitte gib den Stellentext an."
        }), 400

    try:
        # Analyze requirements using Claude
        analyzer = RequirementAnalyzer()
        extracted_requirements = analyzer.analyze_requirements(job_text)

        if not extracted_requirements:
            return jsonify({
                "success": False,
                "error": "Keine Anforderungen gefunden. Bitte überprüfe den Stellentext."
            }), 400

        # Delete existing requirements for this application
        JobRequirement.query.filter_by(application_id=app_id).delete()

        # Save new requirements
        for req_data in extracted_requirements:
            requirement = JobRequirement(
                application_id=app_id,
                requirement_text=req_data["requirement_text"],
                requirement_type=req_data["requirement_type"],
                skill_category=req_data.get("skill_category"),
            )
            db.session.add(requirement)

        db.session.commit()

        # Get the saved requirements
        requirements = JobRequirement.query.filter_by(application_id=app_id).all()
        must_have = [r.to_dict() for r in requirements if r.requirement_type == "must_have"]
        nice_to_have = [r.to_dict() for r in requirements if r.requirement_type == "nice_to_have"]

        return jsonify({
            "success": True,
            "data": {
                "application_id": app_id,
                "must_have": must_have,
                "nice_to_have": nice_to_have,
                "total": len(requirements),
            },
            "message": f"{len(requirements)} Anforderungen extrahiert"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Anforderungs-Analyse: {str(e)}"
        }), 500


@applications_bp.route("/<int:app_id>/job-fit", methods=["GET"])
@jwt_required_custom
def get_job_fit(app_id, current_user):
    """Calculate and return the job-fit score for an application.

    Compares user skills against job requirements and returns:
    - overall_score: 0-100 weighted score (70% must-have, 30% nice-to-have)
    - score_category: sehr_gut (80%+), gut (60-79%), mittel (40-59%), niedrig (<40%)
    - matched_skills: Requirements the user fully meets
    - partial_matches: Requirements partially met (e.g., less experience than required)
    - missing_skills: Requirements the user doesn't meet
    """
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    # Check if requirements exist
    requirements = JobRequirement.query.filter_by(application_id=app_id).all()
    if not requirements:
        return jsonify({
            "success": False,
            "error": "Keine Anforderungen für diese Bewerbung vorhanden. Bitte zuerst Anforderungen analysieren."
        }), 400

    try:
        calculator = JobFitCalculator()
        result = calculator.calculate_job_fit(current_user.id, app_id)

        return jsonify({
            "success": True,
            "data": result.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Job-Fit Berechnung: {str(e)}"
        }), 500
