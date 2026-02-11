from functools import wraps

from flask import jsonify

from middleware.jwt_required import jwt_required_custom


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")
        if not current_user.is_admin:
            return jsonify({"error": "Admin-Rechte erforderlich"}), 403
        return fn(*args, **kwargs)

    return jwt_required_custom(wrapper)
