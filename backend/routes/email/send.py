import os

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from routes.email import email_bp
from services import email_data_service
from services.gmail_service import GmailService
from services.outlook_service import OutlookService

# Maximum total attachment size: 10MB
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


@email_bp.route("/send", methods=["POST"])
@jwt_required()
def send_email():
    """
    Send an email with attachments via connected email account.

    Request Body:
        application_id: ID of the application to send
        email_account_id: ID of the email account to use
        subject: Email subject
        body: Email body text
        attachments: Optional list of attachment types ['anschreiben', 'lebenslauf']

    Returns:
        JSON with success status and message ID
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate required fields
    application_id = data.get("application_id")
    email_account_id = data.get("email_account_id")
    subject = data.get("subject")
    body = data.get("body")
    to_email = data.get("to_email")
    attachment_types = data.get("attachments", ["anschreiben", "lebenslauf"])

    if not application_id:
        return jsonify(
            {
                "success": False,
                "error": "Bewerbungs-ID ist erforderlich",
            }
        ), 400

    if not email_account_id:
        return jsonify(
            {
                "success": False,
                "error": "E-Mail-Konto-ID ist erforderlich",
            }
        ), 400

    if not subject:
        return jsonify(
            {
                "success": False,
                "error": "Betreff ist erforderlich",
            }
        ), 400

    if not body:
        return jsonify(
            {
                "success": False,
                "error": "Nachrichtentext ist erforderlich",
            }
        ), 400

    if not to_email:
        return jsonify(
            {
                "success": False,
                "error": "Empfänger-E-Mail ist erforderlich",
            }
        ), 400

    # Get the application
    application = email_data_service.get_application(application_id, user_id)

    if not application:
        return jsonify(
            {
                "success": False,
                "error": "Bewerbung nicht gefunden",
            }
        ), 404

    # Get the email account
    email_account = email_data_service.get_email_account(email_account_id, user_id)

    if not email_account:
        return jsonify(
            {
                "success": False,
                "error": "E-Mail-Konto nicht gefunden",
            }
        ), 404

    # Build attachments list
    attachments = []
    total_size = 0

    # Add application PDF (Anschreiben) if requested
    if "anschreiben" in attachment_types and application.pdf_path:
        pdf_path = application.pdf_path
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            total_size += file_size
            filename = f"Anschreiben_{application.firma}.pdf"
            attachments.append(
                {
                    "path": pdf_path,
                    "filename": filename,
                }
            )

    # Add Lebenslauf if requested
    if "lebenslauf" in attachment_types:
        cv_doc = email_data_service.get_cv_document(user_id)

        if cv_doc and os.path.exists(cv_doc.file_path):
            file_size = os.path.getsize(cv_doc.file_path)
            total_size += file_size
            filename = cv_doc.original_filename or "Lebenslauf.pdf"
            attachments.append(
                {
                    "path": cv_doc.file_path,
                    "filename": filename,
                }
            )

    # Check total attachment size
    if total_size > MAX_ATTACHMENT_SIZE:
        return jsonify(
            {
                "success": False,
                "error": f"Gesamtgröße der Anhänge überschreitet 10MB Limit ({total_size / 1024 / 1024:.1f}MB)",
            }
        ), 400

    try:
        # Send email based on provider
        if email_account.provider == "gmail":
            result = GmailService.send_email(
                email_account=email_account,
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachments if attachments else None,
            )
        elif email_account.provider == "outlook":
            result = OutlookService.send_email(
                email_account=email_account,
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachments if attachments else None,
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": f"Unbekannter Anbieter: {email_account.provider}",
                }
            ), 400

        # Update application: set sent_at, sent_via, and status
        email_data_service.mark_application_sent(application, email_account.provider)

        return jsonify(
            {
                "success": True,
                "message": "E-Mail erfolgreich gesendet",
                "data": {
                    "result": result,
                    "attachments_count": len(attachments),
                    "provider": email_account.provider,
                    "sent_at": application.sent_at.isoformat(),
                    "sent_via": application.sent_via,
                },
            }
        ), 200

    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 400
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": f"Fehler beim Senden der E-Mail: {str(e)}",
            }
        ), 500
