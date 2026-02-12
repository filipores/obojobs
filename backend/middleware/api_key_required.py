from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

from flask import jsonify, request

from models import APIKey, User, db


def api_key_required(fn: Callable) -> Callable:
    """
    API Key authentication decorator for extension requests.
    Usage: @api_key_required
    Access user via: current_user (injected into function kwargs)
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return jsonify({"error": "API-Schlüssel erforderlich"}), 401

        # Find API key by prefix (first 8 chars)
        key_prefix = api_key[:8]
        api_key_obj = APIKey.query.filter_by(key_prefix=key_prefix, is_active=True).first()

        if not api_key_obj:
            return jsonify({"error": "Ungültiger API-Schlüssel"}), 401

        # Verify the full key
        if not api_key_obj.check_key(api_key):
            return jsonify({"error": "Ungültiger API-Schlüssel"}), 401

        # Get user
        user = User.query.get(api_key_obj.user_id)
        if not user or not user.is_active:
            return jsonify({"error": "Ungültiger oder inaktiver Benutzer"}), 401

        # Update last_used_at
        api_key_obj.last_used_at = datetime.utcnow()
        db.session.commit()

        # Inject current_user into kwargs
        kwargs["current_user"] = user
        return fn(*args, **kwargs)

    return wrapper
