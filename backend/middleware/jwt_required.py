from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models import User, db


def get_current_user_id() -> int:
    """Return the current JWT identity as an integer.

    JWT spec requires the ``sub`` claim to be a string, so
    ``get_jwt_identity()`` always returns a string.  This helper
    centralises the ``int()`` conversion so callers don't have to.
    """
    return int(get_jwt_identity())


def jwt_required_custom(fn: Callable) -> Callable:
    """
    Custom JWT required decorator that also loads the current user.
    Usage: @jwt_required_custom
    Access user via: current_user (injected into function kwargs)
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        verify_jwt_in_request()
        user_id = get_current_user_id()

        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            return jsonify({"error": "Ungültiger oder inaktiver Benutzer"}), 401

        kwargs["current_user"] = user
        return fn(*args, **kwargs)

    return wrapper
