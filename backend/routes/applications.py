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
from models import Application, InterviewQuestion, JobRequirement, Template, UserSkill, db
from services.ats_optimizer import ATSOptimizer
from services.generator import BewerbungsGenerator
from services.interview_evaluator import InterviewEvaluator
from services.interview_generator import InterviewGenerator
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
from services.star_analyzer import STARAnalyzer
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
    - learning_recommendations: Suggestions for how to learn missing skills

    Query params:
    - include_recommendations: 'true' to include learning recommendations (default: true)
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

    include_recommendations = request.args.get("include_recommendations", "true").lower() == "true"

    try:
        calculator = JobFitCalculator()
        result = calculator.calculate_job_fit(current_user.id, app_id)

        # Generate learning recommendations if there are missing/partial skills
        if include_recommendations and (result.missing_skills or result.partial_matches):
            recommendations = calculator.generate_learning_recommendations(
                result.missing_skills,
                result.partial_matches
            )
            result.learning_recommendations = recommendations

        return jsonify({
            "success": True,
            "job_fit": result.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Job-Fit Berechnung: {str(e)}"
        }), 500


@applications_bp.route("/analyze-job-fit", methods=["POST"])
@jwt_required_custom
def analyze_job_fit_preview(current_user):
    """Create a temporary application for job-fit analysis before generating.

    This endpoint:
    1. Creates a temporary (draft) application
    2. Analyzes and extracts job requirements
    3. Returns the application ID for job-fit score calculation

    The temporary application can be used for the full generation later
    or deleted if the user decides not to proceed.
    """
    data = request.json or {}
    url = data.get("url", "").strip()
    description = data.get("description", "")
    company = data.get("company", "")
    title = data.get("title", "")

    if not description:
        return jsonify({
            "success": False,
            "error": "Stellenbeschreibung ist erforderlich"
        }), 400

    try:
        # Create a temporary application for analysis
        app = Application(
            user_id=current_user.id,
            firma=company or "Unbekannt",
            position=title or "Unbekannt",
            quelle=url,
            status="erstellt",
            notizen=f"[Draft - Job-Fit Analyse]\n\n{description[:2000]}",  # Store description for reference
        )
        db.session.add(app)
        db.session.commit()

        # Analyze requirements using Claude
        analyzer = RequirementAnalyzer()
        extracted_requirements = analyzer.analyze_requirements(description)

        if extracted_requirements:
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

        return jsonify({
            "success": True,
            "application_id": app.id,
            "requirements_count": len(extracted_requirements) if extracted_requirements else 0,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Job-Fit Analyse: {str(e)}"
        }), 500


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
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    cover_letter_text = data.get("cover_letter_text", "")
    job_description = data.get("job_description", "")

    # Try to get cover letter text if not provided
    if not cover_letter_text:
        # First try email_text
        if app.email_text:
            cover_letter_text = app.email_text
        # Then try to extract from PDF
        elif app.pdf_path and os.path.exists(app.pdf_path):
            try:
                import fitz  # PyMuPDF

                with fitz.open(app.pdf_path) as doc:
                    cover_letter_text = ""
                    for page in doc:
                        cover_letter_text += page.get_text()
            except Exception:
                pass

    if not cover_letter_text:
        return jsonify({
            "success": False,
            "error": "Kein Bewerbungstext vorhanden. Bitte gib den Text an oder stelle sicher, dass eine Bewerbung generiert wurde."
        }), 400

    # Try to get job description if not provided
    if not job_description:
        # Try from notizen (might contain job description)
        if app.notizen and "[Draft - Job-Fit Analyse]" in app.notizen:
            job_description = app.notizen.replace("[Draft - Job-Fit Analyse]", "").strip()
        # Try to scrape from quelle URL
        elif app.quelle and app.quelle.startswith(("http://", "https://")):
            try:
                scraper = WebScraper()
                job_data = scraper.fetch_job_posting(app.quelle)
                job_description = job_data.get("text", "")
            except Exception:
                pass

    if not job_description:
        return jsonify({
            "success": False,
            "error": "Keine Stellenbeschreibung vorhanden. Bitte gib den Stellentext an."
        }), 400

    try:
        optimizer = ATSOptimizer()
        result = optimizer.analyze_cover_letter(cover_letter_text, job_description)

        return jsonify({
            "success": True,
            "data": {
                "ats_score": result["ats_score"],
                "missing_keywords": result["missing_keywords"],
                "keyword_suggestions": result["keyword_suggestions"],
                "format_issues": result["format_issues"],
                "keyword_density": result["keyword_density"],
                "found_keywords": result.get("found_keywords", []),
            }
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der ATS-Analyse: {str(e)}"
        }), 500


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

    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    cover_letter_text = data.get("cover_letter_text", "")
    job_description = data.get("job_description", "")
    missing_keywords = data.get("missing_keywords", [])

    # Try to get cover letter text if not provided
    if not cover_letter_text:
        if app.email_text:
            cover_letter_text = app.email_text
        elif app.pdf_path and os.path.exists(app.pdf_path):
            try:
                import fitz  # PyMuPDF

                with fitz.open(app.pdf_path) as doc:
                    cover_letter_text = ""
                    for page in doc:
                        cover_letter_text += page.get_text()
            except Exception:
                pass

    if not cover_letter_text:
        return jsonify({
            "success": False,
            "error": "Kein Bewerbungstext vorhanden. Bitte gib den Text an."
        }), 400

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
        return jsonify({
            "success": False,
            "error": "Keine Stellenbeschreibung vorhanden. Bitte gib den Stellentext an."
        }), 400

    # If no missing keywords provided, perform ATS analysis first
    if not missing_keywords:
        try:
            optimizer = ATSOptimizer()
            ats_result = optimizer.analyze_cover_letter(cover_letter_text, job_description)
            missing_keywords = ats_result.get("missing_keywords", [])
        except Exception:
            pass

    if not missing_keywords:
        return jsonify({
            "success": True,
            "data": {
                "original_text": cover_letter_text,
                "optimized_text": cover_letter_text,
                "changes_made": [],
                "message": "Keine fehlenden Keywords - Bewerbung ist bereits gut optimiert."
            }
        }), 200

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
{', '.join(missing_keywords[:10])}

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
        import json
        import re

        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            return jsonify({
                "success": False,
                "error": "Fehler bei der KI-Optimierung: Ungültiges Antwortformat"
            }), 500

        result = json.loads(json_match.group())
        optimized_text = result.get("optimized_text", cover_letter_text)
        changes_made = result.get("changes_made", [])

        # Update the application's email_text with optimized version
        app.email_text = optimized_text
        db.session.commit()

        return jsonify({
            "success": True,
            "data": {
                "original_text": cover_letter_text,
                "optimized_text": optimized_text,
                "changes_made": changes_made,
            }
        }), 200

    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "error": "Fehler bei der KI-Optimierung: JSON-Parsing fehlgeschlagen"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der KI-Optimierung: {str(e)}"
        }), 500


@applications_bp.route("/<int:app_id>/generate-questions", methods=["POST"])
@jwt_required_custom
def generate_interview_questions(app_id, current_user):
    """Generate interview questions for an application based on the job posting.

    Uses Claude API to generate personalized interview questions considering:
    - The job posting and requirements
    - The user's skills and experience
    - German interview culture

    Request body (optional):
        - question_count: Number of questions to generate (10-15, default 12)

    Returns:
        - questions: List of generated interview questions with sample answers
    """
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    question_count = data.get("question_count", 12)

    # Get job text from various sources
    job_text = ""

    # First try notizen
    if app.notizen:
        job_text = app.notizen.replace("[Draft - Job-Fit Analyse]", "").strip()

    # Then try to scrape from quelle URL
    if not job_text and app.quelle and app.quelle.startswith(("http://", "https://")):
        try:
            scraper = WebScraper()
            job_data = scraper.fetch_job_posting(app.quelle)
            job_text = job_data.get("text", "")
        except Exception:
            pass

    if not job_text:
        return jsonify({
            "success": False,
            "error": "Keine Stellenbeschreibung vorhanden. Bitte stelle sicher, dass die Bewerbung eine Stellenanzeige-URL oder Beschreibung hat."
        }), 400

    # Get user skills for personalized questions
    user_skills = UserSkill.query.filter_by(user_id=current_user.id).all()
    skills_list = [{"skill_name": s.skill_name, "category": s.skill_category} for s in user_skills]

    try:
        generator = InterviewGenerator()
        questions = generator.generate_questions(
            job_text=job_text,
            firma=app.firma or "Unbekannt",
            position=app.position or "Unbekannt",
            user_skills=skills_list,
            question_count=question_count,
        )

        if not questions:
            return jsonify({
                "success": False,
                "error": "Keine Interview-Fragen generiert. Bitte versuche es erneut."
            }), 500

        # Delete existing questions for this application
        InterviewQuestion.query.filter_by(application_id=app_id).delete()

        # Save generated questions
        for q_data in questions:
            question = InterviewQuestion(
                application_id=app_id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                difficulty=q_data.get("difficulty", "medium"),
                sample_answer=q_data.get("sample_answer"),
            )
            db.session.add(question)

        db.session.commit()

        # Get saved questions
        saved_questions = InterviewQuestion.query.filter_by(application_id=app_id).all()

        return jsonify({
            "success": True,
            "data": {
                "application_id": app_id,
                "questions": [q.to_dict() for q in saved_questions],
                "total": len(saved_questions),
            },
            "message": f"{len(saved_questions)} Interview-Fragen generiert"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Fragen-Generierung: {str(e)}"
        }), 500


@applications_bp.route("/<int:app_id>/interview-questions", methods=["GET"])
@jwt_required_custom
def get_interview_questions(app_id, current_user):
    """Get all interview questions for an application.

    Returns questions grouped by type (behavioral, technical, situational,
    company_specific, salary_negotiation).

    Query params:
        - type: Filter by question type (optional)
    """
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    question_type = request.args.get("type")

    query = InterviewQuestion.query.filter_by(application_id=app_id)
    if question_type and question_type in InterviewQuestion.VALID_TYPES:
        query = query.filter_by(question_type=question_type)

    questions = query.all()

    # Group by type
    grouped = {
        "behavioral": [],
        "technical": [],
        "situational": [],
        "company_specific": [],
        "salary_negotiation": [],
    }

    for q in questions:
        if q.question_type in grouped:
            grouped[q.question_type].append(q.to_dict())

    return jsonify({
        "success": True,
        "data": {
            "application_id": app_id,
            "questions": grouped,
            "all_questions": [q.to_dict() for q in questions],
            "total": len(questions),
        }
    }), 200


@applications_bp.route("/interview/evaluate-answer", methods=["POST"])
@jwt_required_custom
def evaluate_interview_answer(current_user):
    """Evaluate an interview answer and provide AI feedback.

    Request body:
        - question_id: ID of the interview question being answered
        - answer_text: The user's answer to evaluate
        - application_id: Optional, for context (position, company)

    Returns:
        - evaluation: Structured feedback with score, strengths, improvements
        - star_analysis: STAR method analysis (for behavioral questions only)
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    question_id = data.get("question_id")
    answer_text = data.get("answer_text", "").strip()

    if not question_id:
        return jsonify({"success": False, "error": "question_id ist erforderlich"}), 400

    if not answer_text:
        return jsonify({"success": False, "error": "answer_text ist erforderlich"}), 400

    if len(answer_text) < 10:
        return jsonify({
            "success": False,
            "error": "Die Antwort ist zu kurz. Bitte geben Sie eine ausführlichere Antwort."
        }), 400

    # Get the question
    question = InterviewQuestion.query.get(question_id)
    if not question:
        return jsonify({"success": False, "error": "Frage nicht gefunden"}), 404

    # Verify user has access to this question's application
    app = Application.query.filter_by(
        id=question.application_id,
        user_id=current_user.id
    ).first()

    if not app:
        return jsonify({"success": False, "error": "Keine Berechtigung"}), 403

    try:
        evaluator = InterviewEvaluator()
        evaluation = evaluator.evaluate_answer(
            question_text=question.question_text,
            question_type=question.question_type,
            answer_text=answer_text,
            position=app.position,
            firma=app.firma,
        )

        return jsonify({
            "success": True,
            "data": {
                "question_id": question_id,
                "question_type": question.question_type,
                "evaluation": evaluation,
            },
            "message": "Antwort erfolgreich bewertet"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Bewertung: {str(e)}"
        }), 500


@applications_bp.route("/interview/summary", methods=["POST"])
@jwt_required_custom
def get_interview_summary(current_user):
    """Generate a summary of all interview answers for a mock interview session.

    Request body:
        - application_id: The application ID
        - answers: List of answer evaluations with scores and feedback

    Returns:
        - summary: Overall assessment with category scores and recommendations
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    application_id = data.get("application_id")
    answers = data.get("answers", [])

    if not application_id:
        return jsonify({"success": False, "error": "application_id ist erforderlich"}), 400

    # Verify user has access to this application
    app = Application.query.filter_by(
        id=application_id,
        user_id=current_user.id
    ).first()

    if not app:
        return jsonify({"success": False, "error": "Bewerbung nicht gefunden"}), 404

    try:
        evaluator = InterviewEvaluator()
        summary = evaluator.generate_interview_summary(
            answers=answers,
            position=app.position,
            firma=app.firma,
        )

        return jsonify({
            "success": True,
            "data": {
                "application_id": application_id,
                "summary": summary,
            },
            "message": "Zusammenfassung erstellt"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der Zusammenfassung: {str(e)}"
        }), 500


@applications_bp.route("/interview/analyze-star", methods=["POST"])
@jwt_required_custom
def analyze_star_method(current_user):
    """Perform detailed STAR method analysis on a behavioral interview answer.

    Provides specialized feedback for behavioral questions with detailed analysis
    of each STAR component (Situation, Task, Action, Result) and improvement suggestions.

    Request body:
        - question_id: (optional) ID of the interview question
        - question_text: (required if no question_id) The question text
        - answer_text: The user's answer to analyze
        - application_id: Optional, for context (position, company)

    Returns:
        - star_analysis: Detailed analysis with:
          - overall_star_score: 0-100 compliance score
          - components: Analysis for each STAR component
          - improvement_suggestions: Specific improvement tips
          - improved_answer_example: Example of improved answer
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    question_id = data.get("question_id")
    question_text = data.get("question_text", "").strip()
    answer_text = data.get("answer_text", "").strip()
    application_id = data.get("application_id")

    # Get question text from question_id if not provided
    if not question_text and question_id:
        question = InterviewQuestion.query.get(question_id)
        if question:
            question_text = question.question_text
            if not application_id:
                application_id = question.application_id

    if not question_text:
        return jsonify({
            "success": False,
            "error": "question_text oder question_id ist erforderlich"
        }), 400

    if not answer_text:
        return jsonify({
            "success": False,
            "error": "answer_text ist erforderlich"
        }), 400

    if len(answer_text) < 20:
        return jsonify({
            "success": False,
            "error": "Die Antwort ist zu kurz für eine STAR-Analyse. Bitte geben Sie eine ausführlichere Antwort."
        }), 400

    # Get context from application if available
    position = None
    firma = None
    if application_id:
        app = Application.query.filter_by(
            id=application_id,
            user_id=current_user.id
        ).first()
        if app:
            position = app.position
            firma = app.firma

    try:
        analyzer = STARAnalyzer()
        analysis = analyzer.analyze_star(
            question_text=question_text,
            answer_text=answer_text,
            position=position,
            firma=firma,
        )

        return jsonify({
            "success": True,
            "data": {
                "question_id": question_id,
                "question_text": question_text,
                "star_analysis": analysis,
            },
            "message": "STAR-Analyse erfolgreich"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Fehler bei der STAR-Analyse: {str(e)}"
        }), 500


@applications_bp.route("/interview/star-components", methods=["GET"])
@jwt_required_custom
def get_star_components(current_user):
    """Get descriptions of STAR method components.

    Returns detailed information about each STAR component for help/reference.
    """
    analyzer = STARAnalyzer()
    return jsonify({
        "success": True,
        "data": {
            "components": analyzer.get_component_descriptions(),
        }
    }), 200


# ==================== Interview Result Tracking ====================


VALID_INTERVIEW_RESULTS = ["scheduled", "completed", "passed", "rejected", "offer_received"]


@applications_bp.route("/<int:app_id>/interview-result", methods=["PUT"])
@jwt_required_custom
def update_interview_result(app_id, current_user):
    """Update interview result and feedback for an application.

    Request body:
        - interview_date: (optional) ISO date string for scheduled interview
        - interview_result: (optional) One of: scheduled, completed, passed, rejected, offer_received
        - interview_feedback: (optional) Free text for personal notes after interview

    Returns:
        - application: Updated application with interview fields
    """
    app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}

    # Update interview_date
    if "interview_date" in data:
        date_value = data["interview_date"]
        if date_value:
            try:
                # Parse ISO format date
                if isinstance(date_value, str):
                    # Handle both datetime and date-only formats
                    if "T" in date_value:
                        app.interview_date = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                    else:
                        app.interview_date = datetime.fromisoformat(date_value)
                else:
                    app.interview_date = None
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Ungültiges Datumsformat. Bitte ISO-Format verwenden (YYYY-MM-DD oder YYYY-MM-DDTHH:MM:SS)"
                }), 400
        else:
            app.interview_date = None

    # Update interview_result
    if "interview_result" in data:
        result_value = data["interview_result"]
        if result_value:
            if result_value not in VALID_INTERVIEW_RESULTS:
                return jsonify({
                    "success": False,
                    "error": f"Ungültiges Ergebnis. Erlaubt: {', '.join(VALID_INTERVIEW_RESULTS)}"
                }), 400
            app.interview_result = result_value
        else:
            app.interview_result = None

    # Update interview_feedback
    if "interview_feedback" in data:
        app.interview_feedback = data["interview_feedback"]

    db.session.commit()

    return jsonify({
        "success": True,
        "application": app.to_dict(),
        "message": "Interview-Ergebnis aktualisiert"
    }), 200


@applications_bp.route("/interview-stats", methods=["GET"])
@jwt_required_custom
def get_interview_statistics(current_user):
    """Get interview statistics for the current user.

    Returns aggregated interview data:
        - total_interviews: Total applications with interview scheduled/completed
        - success_rate: Percentage of passed interviews out of completed
        - result_breakdown: Count per interview_result status
        - upcoming_interviews: List of scheduled interviews
        - recent_results: List of recent interview outcomes
    """
    from sqlalchemy import func

    # Base query for user's applications
    base_query = Application.query.filter_by(user_id=current_user.id)

    # Total applications with any interview result
    total_with_results = base_query.filter(Application.interview_result.isnot(None)).count()

    # Count per result status
    result_counts = (
        db.session.query(Application.interview_result, func.count(Application.id))
        .filter_by(user_id=current_user.id)
        .filter(Application.interview_result.isnot(None))
        .group_by(Application.interview_result)
        .all()
    )

    result_breakdown = dict.fromkeys(VALID_INTERVIEW_RESULTS, 0)
    for result, count in result_counts:
        if result in result_breakdown:
            result_breakdown[result] = count

    # Calculate success rate (passed + offer_received out of all completed outcomes)
    completed_outcomes = result_breakdown.get("passed", 0) + result_breakdown.get("rejected", 0) + result_breakdown.get("offer_received", 0)
    successful_outcomes = result_breakdown.get("passed", 0) + result_breakdown.get("offer_received", 0)
    success_rate = round((successful_outcomes / completed_outcomes * 100) if completed_outcomes > 0 else 0, 1)

    # Upcoming interviews (scheduled with future date)
    upcoming = (
        base_query.filter(
            Application.interview_result == "scheduled",
            Application.interview_date.isnot(None),
            Application.interview_date >= datetime.utcnow(),
        )
        .order_by(Application.interview_date.asc())
        .limit(5)
        .all()
    )

    # Recent results (last 10 completed interviews)
    recent_results = (
        base_query.filter(
            Application.interview_result.in_(["completed", "passed", "rejected", "offer_received"])
        )
        .order_by(Application.interview_date.desc().nulls_last())
        .limit(10)
        .all()
    )

    return jsonify({
        "success": True,
        "data": {
            "total_interviews": total_with_results,
            "success_rate": success_rate,
            "result_breakdown": result_breakdown,
            "upcoming_interviews": [
                {
                    "id": app.id,
                    "firma": app.firma,
                    "position": app.position,
                    "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                }
                for app in upcoming
            ],
            "recent_results": [
                {
                    "id": app.id,
                    "firma": app.firma,
                    "position": app.position,
                    "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                    "interview_result": app.interview_result,
                    "interview_feedback": app.interview_feedback,
                }
                for app in recent_results
            ],
        }
    }), 200
