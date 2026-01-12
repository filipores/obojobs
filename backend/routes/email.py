import os
import secrets

from flask import Blueprint, jsonify, request, session
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import db
from models.application import Application
from models.document import Document
from models.email_account import EmailAccount
from services.gmail_service import GmailService
from services.outlook_service import OutlookService

# Maximum total attachment size: 10MB
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024

email_bp = Blueprint("email", __name__)


@email_bp.route("/accounts", methods=["GET"])
@jwt_required()
def list_email_accounts():
    """
    List all connected email accounts for the current user.

    Returns:
        JSON with list of email accounts
    """
    user_id = get_jwt_identity()

    accounts = EmailAccount.query.filter_by(user_id=int(user_id)).all()

    return jsonify({
        "success": True,
        "data": [account.to_dict() for account in accounts],
    }), 200


@email_bp.route("/accounts/<int:account_id>", methods=["DELETE"])
@jwt_required()
def delete_email_account(account_id):
    """
    Disconnect an email account.

    Args:
        account_id: ID of the email account to delete

    Returns:
        JSON with success status
    """
    user_id = get_jwt_identity()

    account = EmailAccount.query.filter_by(
        id=account_id,
        user_id=int(user_id)
    ).first()

    if not account:
        return jsonify({
            "success": False,
            "error": "Email account not found",
        }), 404

    db.session.delete(account)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Email account disconnected successfully",
    }), 200


@email_bp.route("/gmail/auth-url", methods=["GET"])
@jwt_required()
def gmail_auth_url():
    """
    Generate Gmail OAuth authorization URL.

    Returns:
        JSON with authorization_url to redirect the user to
    """
    try:
        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session for verification
        user_id = get_jwt_identity()
        session[f"gmail_oauth_state_{user_id}"] = state

        authorization_url, _ = GmailService.get_authorization_url(state=state)

        return jsonify({
            "success": True,
            "authorization_url": authorization_url,
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to generate authorization URL: {str(e)}",
        }), 500


@email_bp.route("/gmail/callback", methods=["GET"])
@jwt_required()
def gmail_callback():
    """
    Handle Gmail OAuth callback.

    Query Parameters:
        code: Authorization code from Google
        state: State parameter for CSRF verification
        error: Error message if authorization failed

    Returns:
        JSON with success status and email account info
    """
    # Check for errors from Google
    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "Unknown error")
        return jsonify({
            "success": False,
            "error": f"OAuth error: {error} - {error_description}",
        }), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({
            "success": False,
            "error": "Authorization code is required",
        }), 400

    user_id = get_jwt_identity()

    # Verify state for CSRF protection
    stored_state = session.get(f"gmail_oauth_state_{user_id}")
    if stored_state and state != stored_state:
        return jsonify({
            "success": False,
            "error": "Invalid state parameter",
        }), 400

    # Clear the stored state
    session.pop(f"gmail_oauth_state_{user_id}", None)

    try:
        # Exchange code for tokens
        token_data = GmailService.exchange_code_for_tokens(code)

        # Get user's email address
        email = GmailService.get_user_email(token_data["access_token"])

        # Save tokens to database
        email_account = GmailService.save_tokens(
            user_id=int(user_id),
            email=email,
            token_data=token_data,
        )

        return jsonify({
            "success": True,
            "message": "Gmail account connected successfully",
            "data": email_account.to_dict(),
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to complete OAuth flow: {str(e)}",
        }), 500


@email_bp.route("/outlook/auth-url", methods=["GET"])
@jwt_required()
def outlook_auth_url():
    """
    Generate Outlook OAuth authorization URL.

    Returns:
        JSON with authorization_url to redirect the user to
    """
    try:
        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session for verification
        user_id = get_jwt_identity()
        session[f"outlook_oauth_state_{user_id}"] = state

        authorization_url, _ = OutlookService.get_authorization_url(state=state)

        return jsonify({
            "success": True,
            "authorization_url": authorization_url,
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to generate authorization URL: {str(e)}",
        }), 500


@email_bp.route("/outlook/callback", methods=["GET"])
@jwt_required()
def outlook_callback():
    """
    Handle Outlook OAuth callback.

    Query Parameters:
        code: Authorization code from Microsoft
        state: State parameter for CSRF verification
        error: Error message if authorization failed

    Returns:
        JSON with success status and email account info
    """
    # Check for errors from Microsoft
    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "Unknown error")
        return jsonify({
            "success": False,
            "error": f"OAuth error: {error} - {error_description}",
        }), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({
            "success": False,
            "error": "Authorization code is required",
        }), 400

    user_id = get_jwt_identity()

    # Verify state for CSRF protection
    stored_state = session.get(f"outlook_oauth_state_{user_id}")
    if stored_state and state != stored_state:
        return jsonify({
            "success": False,
            "error": "Invalid state parameter",
        }), 400

    # Clear the stored state
    session.pop(f"outlook_oauth_state_{user_id}", None)

    try:
        # Exchange code for tokens
        token_data = OutlookService.exchange_code_for_tokens(code)

        # Get user's email address
        email = OutlookService.get_user_email(token_data["access_token"])

        # Save tokens to database
        email_account = OutlookService.save_tokens(
            user_id=int(user_id),
            email=email,
            token_data=token_data,
        )

        return jsonify({
            "success": True,
            "message": "Outlook account connected successfully",
            "data": email_account.to_dict(),
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to complete OAuth flow: {str(e)}",
        }), 500


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
        return jsonify({
            "success": False,
            "error": "application_id is required",
        }), 400

    if not email_account_id:
        return jsonify({
            "success": False,
            "error": "email_account_id is required",
        }), 400

    if not subject:
        return jsonify({
            "success": False,
            "error": "subject is required",
        }), 400

    if not body:
        return jsonify({
            "success": False,
            "error": "body is required",
        }), 400

    if not to_email:
        return jsonify({
            "success": False,
            "error": "to_email is required",
        }), 400

    # Get the application
    application = Application.query.filter_by(
        id=application_id,
        user_id=int(user_id),
    ).first()

    if not application:
        return jsonify({
            "success": False,
            "error": "Application not found",
        }), 404

    # Get the email account
    email_account = EmailAccount.query.filter_by(
        id=email_account_id,
        user_id=int(user_id),
    ).first()

    if not email_account:
        return jsonify({
            "success": False,
            "error": "Email account not found",
        }), 404

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
            attachments.append({
                "path": pdf_path,
                "filename": filename,
            })

    # Add Lebenslauf if requested
    if "lebenslauf" in attachment_types:
        cv_doc = Document.query.filter_by(
            user_id=int(user_id),
            doc_type="cv_pdf",
        ).order_by(Document.uploaded_at.desc()).first()

        if cv_doc and os.path.exists(cv_doc.file_path):
            file_size = os.path.getsize(cv_doc.file_path)
            total_size += file_size
            filename = cv_doc.original_filename or "Lebenslauf.pdf"
            attachments.append({
                "path": cv_doc.file_path,
                "filename": filename,
            })

    # Check total attachment size
    if total_size > MAX_ATTACHMENT_SIZE:
        return jsonify({
            "success": False,
            "error": f"Total attachment size exceeds 10MB limit ({total_size / 1024 / 1024:.1f}MB)",
        }), 400

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
            return jsonify({
                "success": False,
                "error": f"Unknown provider: {email_account.provider}",
            }), 400

        return jsonify({
            "success": True,
            "message": "Email sent successfully",
            "data": {
                "result": result,
                "attachments_count": len(attachments),
                "provider": email_account.provider,
            },
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to send email: {str(e)}",
        }), 500
