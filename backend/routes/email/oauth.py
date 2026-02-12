import os
import secrets

from flask import Response, jsonify, request, session
from flask_jwt_extended import get_jwt_identity, jwt_required

from routes.email import email_bp
from services.gmail_service import GmailService
from services.outlook_service import OutlookService


@email_bp.route("/gmail/auth-url", methods=["GET"])
@jwt_required()
def gmail_auth_url() -> tuple[Response, int]:
    """
    Generate Gmail OAuth authorization URL.

    Returns:
        JSON with authorization_url to redirect the user to
    """
    try:
        # Check if Gmail integration is configured before attempting OAuth
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

        if not client_id or not client_secret or not redirect_uri:
            return jsonify(
                {
                    "success": False,
                    "error": "Gmail-Integration ist derzeit nicht konfiguriert.",
                    "config_status": {
                        "client_id": bool(client_id),
                        "client_secret": bool(client_secret),
                        "redirect_uri": bool(redirect_uri),
                    },
                }
            ), 400

        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session for verification
        user_id = get_jwt_identity()
        session[f"gmail_oauth_state_{user_id}"] = state

        authorization_url, _ = GmailService.get_authorization_url(state=state)

        return jsonify(
            {
                "success": True,
                "authorization_url": authorization_url,
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
                "error": f"Fehler beim Erstellen der Autorisierungs-URL: {str(e)}",
            }
        ), 500


@email_bp.route("/gmail/callback", methods=["GET"])
@jwt_required()
def gmail_callback() -> tuple[Response, int]:
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
        error_description = request.args.get("error_description", "Unbekannter Fehler")
        return jsonify(
            {
                "success": False,
                "error": f"OAuth-Fehler: {error} - {error_description}",
            }
        ), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify(
            {
                "success": False,
                "error": "Autorisierungscode ist erforderlich",
            }
        ), 400

    user_id = get_jwt_identity()

    # Verify state for CSRF protection
    stored_state = session.get(f"gmail_oauth_state_{user_id}")
    if stored_state and state != stored_state:
        return jsonify(
            {
                "success": False,
                "error": "Ungültiger State-Parameter",
            }
        ), 400

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

        return jsonify(
            {
                "success": True,
                "message": "Gmail-Konto erfolgreich verbunden",
                "data": email_account.to_dict(),
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
                "error": f"Fehler beim Abschluss des OAuth-Prozesses: {str(e)}",
            }
        ), 500


@email_bp.route("/outlook/auth-url", methods=["GET"])
@jwt_required()
def outlook_auth_url() -> tuple[Response, int]:
    """
    Generate Outlook OAuth authorization URL.

    Returns:
        JSON with authorization_url to redirect the user to
    """
    try:
        # Check if Outlook integration is configured before attempting OAuth
        client_id = os.environ.get("MICROSOFT_CLIENT_ID")
        client_secret = os.environ.get("MICROSOFT_CLIENT_SECRET")
        redirect_uri = os.environ.get("MICROSOFT_REDIRECT_URI")

        if not client_id or not client_secret or not redirect_uri:
            return jsonify(
                {
                    "success": False,
                    "error": "Outlook-Integration ist derzeit nicht konfiguriert.",
                    "config_status": {
                        "client_id": bool(client_id),
                        "client_secret": bool(client_secret),
                        "redirect_uri": bool(redirect_uri),
                    },
                }
            ), 400

        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session for verification
        user_id = get_jwt_identity()
        session[f"outlook_oauth_state_{user_id}"] = state

        authorization_url, _ = OutlookService.get_authorization_url(state=state)

        return jsonify(
            {
                "success": True,
                "authorization_url": authorization_url,
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
                "error": f"Fehler beim Erstellen der Autorisierungs-URL: {str(e)}",
            }
        ), 500


@email_bp.route("/outlook/callback", methods=["GET"])
@jwt_required()
def outlook_callback() -> tuple[Response, int]:
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
        error_description = request.args.get("error_description", "Unbekannter Fehler")
        return jsonify(
            {
                "success": False,
                "error": f"OAuth-Fehler: {error} - {error_description}",
            }
        ), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify(
            {
                "success": False,
                "error": "Autorisierungscode ist erforderlich",
            }
        ), 400

    user_id = get_jwt_identity()

    # Verify state for CSRF protection
    stored_state = session.get(f"outlook_oauth_state_{user_id}")
    if stored_state and state != stored_state:
        return jsonify(
            {
                "success": False,
                "error": "Ungültiger State-Parameter",
            }
        ), 400

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

        return jsonify(
            {
                "success": True,
                "message": "Outlook-Konto erfolgreich verbunden",
                "data": email_account.to_dict(),
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
                "error": f"Fehler beim Abschluss des OAuth-Prozesses: {str(e)}",
            }
        ), 500
