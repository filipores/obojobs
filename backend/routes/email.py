import secrets

from flask import Blueprint, jsonify, request, session
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.gmail_service import GmailService

email_bp = Blueprint("email", __name__)


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
