from typing import Any

from flask import Blueprint, Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from services import api_key_service

api_keys_bp = Blueprint("api_keys", __name__)


@api_keys_bp.route("", methods=["GET"])
@jwt_required_custom
def list_api_keys(current_user: Any) -> tuple[Response, int]:
    """List user's API keys"""
    keys = api_key_service.list_api_keys(current_user.id)
    return jsonify({"success": True, "api_keys": [key.to_dict() for key in keys]}), 200


@api_keys_bp.route("", methods=["POST"])
@jwt_required_custom
def create_api_key(current_user: Any) -> tuple[Response, int]:
    """Create a new API key"""
    data = request.json
    name = data.get("name", "Chrome Extension")

    api_key_obj, new_key = api_key_service.create_api_key(current_user.id, name=name)

    # Return plaintext key ONCE
    return jsonify(
        {
            "success": True,
            "api_key": new_key,  # Only time this is returned in plaintext
            "key_id": api_key_obj.id,
            "key_prefix": api_key_obj.key_prefix,
            "message": "Speichere diesen Schlüssel jetzt, er wird nicht erneut angezeigt",
        }
    ), 201


@api_keys_bp.route("/<int:key_id>", methods=["DELETE"])
@jwt_required_custom
def delete_api_key(key_id: int, current_user: Any) -> tuple[Response, int]:
    """Revoke an API key"""
    api_key = api_key_service.delete_api_key(key_id, current_user.id)

    if not api_key:
        return jsonify({"error": "API-Schlüssel nicht gefunden"}), 404

    return jsonify({"success": True, "message": "API-Schlüssel widerrufen"}), 200
