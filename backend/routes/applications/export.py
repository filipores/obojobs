import csv
import io
import os
import re
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from flask import Response, jsonify, make_response, request, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from middleware.jwt_required import jwt_required_custom
from routes.applications import applications_bp
from services import application_service


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename.

    Removes or replaces characters that are invalid in filenames.
    """
    if not name:
        return "Anschreiben"

    # Replace German umlauts and special characters FIRST (before any normalization)
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)

    # Remove any remaining non-ASCII characters
    name = name.encode("ascii", "ignore").decode("ascii")

    # Replace spaces and invalid filename characters with underscores
    name = re.sub(r'[<>:"/\\|?*\s]+', "_", name)

    # Remove leading/trailing underscores and dots
    name = name.strip("_.")

    # Ensure we have something left
    return name if name else "Anschreiben"


def _replace_template_vars(text: str | None, app: Any) -> str:
    """Replace template variables in text with actual application values."""
    if not text:
        return ""
    return (
        text.replace("{{FIRMA}}", app.firma or "")
        .replace("{{POSITION}}", app.position or "")
        .replace("{{ANSPRECHPARTNER}}", app.ansprechpartner or "")
        .replace("{{QUELLE}}", app.quelle or "")
    )


def _get_status_label(status: str | None) -> str:
    """Convert status code to readable label."""
    labels = {
        "erstellt": "Erstellt",
        "versendet": "Versendet",
        "antwort_erhalten": "Antwort",
        "absage": "Absage",
        "zusage": "Zusage",
    }
    return labels.get(status, status or "")


def _export_as_csv(applications: list[Any], date_str: str) -> Response:
    """Generate CSV export of applications."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)

    # Header row
    writer.writerow(["Firma", "Position", "Status", "Datum", "Ansprechpartner", "Email"])

    # Data rows
    for app in applications:
        datum_str = app.datum.strftime("%d.%m.%Y") if app.datum else ""
        writer.writerow(
            [
                app.firma or "",
                app.position or "",
                _get_status_label(app.status),
                datum_str,
                app.ansprechpartner or "",
                app.email or "",
            ]
        )

    # Create response with CSV
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=bewerbungen_{date_str}.csv"
    return response


def _export_as_pdf(applications: list[Any], date_str: str) -> Response:
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
        table_data.append(
            [
                Paragraph(app.firma or "", cell_style),
                Paragraph(app.position or "", cell_style),
                _get_status_label(app.status),
                datum_str,
                Paragraph(app.ansprechpartner or "", cell_style),
                Paragraph(app.email or "", cell_style),
            ]
        )

    # Create table with styling
    col_widths = [3 * cm, 4 * cm, 2.5 * cm, 2.2 * cm, 3 * cm, 3.5 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
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
            ]
        )
    )

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


@applications_bp.route("/<int:app_id>/pdf", methods=["GET"])
@jwt_required_custom
def download_pdf(app_id: int, current_user: Any) -> Response | tuple[Response, int]:
    """Download application PDF"""
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"error": "Application not found"}), 404

    if not app.pdf_path or not os.path.exists(app.pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    # Sanitize company name for use in filename
    safe_firma = sanitize_filename(app.firma)
    return send_file(os.path.abspath(app.pdf_path), as_attachment=True, download_name=f"Anschreiben_{safe_firma}.pdf")


@applications_bp.route("/<int:app_id>/email-draft", methods=["GET"])
@jwt_required_custom
def download_email_draft(app_id: int, current_user: Any) -> Response | tuple[Response, int]:
    """Generate and download a .eml email draft file with the Anschreiben PDF attached."""
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"error": "Application not found"}), 404

    if not app.pdf_path or not os.path.exists(app.pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    safe_firma = sanitize_filename(app.firma)

    # Build MIME message
    msg = MIMEMultipart()
    if app.email:
        msg["To"] = app.email
    msg["Subject"] = _replace_template_vars(app.betreff, app)

    # Plain text body
    body = _replace_template_vars(app.email_text, app)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach Anschreiben PDF
    with open(app.pdf_path, "rb") as f:
        pdf_part = MIMEBase("application", "pdf")
        pdf_part.set_payload(f.read())
    encoders.encode_base64(pdf_part)
    pdf_part.add_header("Content-Disposition", "attachment", filename=f"Anschreiben_{safe_firma}.pdf")
    msg.attach(pdf_part)

    # Attach CV and Arbeitszeugnis if available
    for doc_type, default_name in [("lebenslauf", "Lebenslauf.pdf"), ("arbeitszeugnis", "Arbeitszeugnis.pdf")]:
        doc = application_service.get_document(current_user.id, doc_type)
        if doc and doc.pdf_path and os.path.exists(doc.pdf_path):
            with open(doc.pdf_path, "rb") as f:
                doc_part = MIMEBase("application", "pdf")
                doc_part.set_payload(f.read())
            encoders.encode_base64(doc_part)
            attach_name = doc.original_filename or default_name
            doc_part.add_header("Content-Disposition", "attachment", filename=attach_name)
            msg.attach(doc_part)

    # Return as .eml download
    eml_bytes = msg.as_bytes()
    response = make_response(eml_bytes)
    response.headers["Content-Type"] = "message/rfc822"
    response.headers["Content-Disposition"] = f'attachment; filename="Bewerbung_{safe_firma}.eml"'
    return response


@applications_bp.route("/export", methods=["GET"])
@jwt_required_custom
def export_applications(current_user: Any) -> Response:
    """Export applications as CSV or PDF.
    Query params:
    - format: 'csv' (default) or 'pdf'
    - search: (optional) Filter by search term (firma, position)
    - status: (optional) Filter by status
    - firma: (optional) Filter by company name
    """
    export_format = request.args.get("format", "csv").lower()
    search_query = request.args.get("search", "").strip()
    filter_status = request.args.get("status", "").strip()
    filter_firma = request.args.get("firma", "").strip()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Get filtered applications
    applications = application_service.get_filtered_applications(
        current_user.id,
        search_query=search_query,
        filter_status=filter_status,
        filter_firma=filter_firma,
    )

    if export_format == "pdf":
        return _export_as_pdf(applications, today)
    return _export_as_csv(applications, today)
