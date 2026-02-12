from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify

from middleware.jwt_required import jwt_required_custom


def admin_required(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        current_user = kwargs.get("current_user")
        if not current_user.is_admin:
            return jsonify({"error": "Admin-Rechte erforderlich"}), 403
        return fn(*args, **kwargs)

    return jwt_required_custom(wrapper)
