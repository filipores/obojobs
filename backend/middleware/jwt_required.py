from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models import User


def jwt_required_custom(fn: Callable) -> Callable:
    """
    Custom JWT required decorator that also loads the current user.
    Usage: @jwt_required_custom
    Access user via: current_user (injected into function kwargs)
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        verify_jwt_in_request()
        user_id = get_jwt_identity()

        # Convert string identity back to int
        user = User.query.get(int(user_id))
        if not user or not user.is_active:
            return jsonify({"error": "Ungültiger oder inaktiver Benutzer"}), 401

        # Inject current_user into kwargs
        kwargs["current_user"] = user
        return fn(*args, **kwargs)

    return wrapper
