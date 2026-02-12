import os

from flask import Response, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from routes.email import email_bp
from services import email_data_service


@email_bp.route("/integration-status", methods=["GET"])
@jwt_required()
def integration_status() -> tuple[Response, int]:
    """
    Check which email integrations are properly configured.

    Returns:
        JSON with configuration status for Gmail and Outlook
    """
    gmail_configured = all(
        [
            os.environ.get("GOOGLE_CLIENT_ID"),
            os.environ.get("GOOGLE_CLIENT_SECRET"),
            os.environ.get("GOOGLE_REDIRECT_URI"),
        ]
    )

    outlook_configured = all(
        [
            os.environ.get("MICROSOFT_CLIENT_ID"),
            os.environ.get("MICROSOFT_CLIENT_SECRET"),
            os.environ.get("MICROSOFT_REDIRECT_URI"),
        ]
    )

    return jsonify(
        {
            "success": True,
            "data": {
                "gmail": {"configured": gmail_configured, "provider": "gmail"},
                "outlook": {"configured": outlook_configured, "provider": "outlook"},
            },
        }
    ), 200


@email_bp.route("/accounts", methods=["GET"])
@jwt_required()
def list_email_accounts() -> tuple[Response, int]:
    """
    List all connected email accounts for the current user.

    Returns:
        JSON with list of email accounts
    """
    user_id = get_jwt_identity()

    accounts = email_data_service.get_email_accounts(user_id)

    return jsonify(
        {
            "success": True,
            "data": [account.to_dict() for account in accounts],
        }
    ), 200


@email_bp.route("/accounts/<int:account_id>", methods=["DELETE"])
@jwt_required()
def delete_email_account(account_id: int) -> tuple[Response, int]:
    """
    Disconnect an email account.

    Args:
        account_id: ID of the email account to delete

    Returns:
        JSON with success status
    """
    user_id = get_jwt_identity()

    account = email_data_service.get_email_account(account_id, user_id)

    if not account:
        return jsonify(
            {
                "success": False,
                "error": "E-Mail-Konto nicht gefunden",
            }
        ), 404

    email_data_service.delete_email_account(account)

    return jsonify(
        {
            "success": True,
            "message": "E-Mail-Konto erfolgreich getrennt",
        }
    ), 200
