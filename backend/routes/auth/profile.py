from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from routes.auth import auth_bp
from services.auth_service import AuthService


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout user by adding current token to blacklist.

    Requires authentication. The token's JTI is added to the blacklist,
    making it invalid for future use even if it hasn't expired yet.
    """
    jwt = get_jwt()
    jti = jwt["jti"]
    token_type = jwt.get("type", "access")
    user_id = int(get_jwt_identity())

    # Get token expiration time
    exp_timestamp = jwt["exp"]
    expires_at = datetime.utcfromtimestamp(exp_timestamp)

    # Add token to blacklist
    AuthService.logout_user(jti=jti, token_type=token_type, user_id=user_id, expires_at=expires_at)

    return jsonify({"message": "Erfolgreich abgemeldet"}), 200


@auth_bp.route("/language", methods=["PUT"])
@jwt_required()
def update_language():
    """
    Update user language preference.

    Requires authentication. Allows updating language preference (de or en).
    """
    current_user_id = get_jwt_identity()
    data = request.json or {}

    language = data.get("language", "").strip().lower()

    try:
        result = AuthService.update_language(int(current_user_id), language)
        return jsonify(result), 200
    except ValueError as e:
        error_msg = str(e)
        if "nicht gefunden" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update user profile information.

    Requires authentication. Allows updating full_name and display_name.
    """
    current_user_id = get_jwt_identity()
    data = request.json or {}

    try:
        result = AuthService.update_profile(int(current_user_id), data)
        return jsonify(result), 200
    except ValueError as e:
        error_msg = str(e)
        if "nicht gefunden" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400


@auth_bp.route("/delete-account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """
    Delete user account and all associated data.

    Requires authentication. This action is irreversible and will:
    - Delete the user account
    - Delete all associated data (documents, applications, templates, etc.)
    - Blacklist the current JWT token
    - Cancel any active Stripe subscriptions

    GDPR compliance: This ensures the "right to be forgotten" is fulfilled.
    """
    current_user_id = get_jwt_identity()

    try:
        result = AuthService.delete_account(int(current_user_id))
        return jsonify(result), 200
    except ValueError:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
