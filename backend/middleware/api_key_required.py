from datetime import datetime
from functools import wraps

from flask import request, jsonify

from models import db, APIKey, User


def api_key_required(fn):
    """
    API Key authentication decorator for extension requests.
    Usage: @api_key_required
    Access user via: current_user (injected into function kwargs)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        # Find API key by prefix (first 8 chars)
        key_prefix = api_key[:8]
        api_key_obj = APIKey.query.filter_by(key_prefix=key_prefix, is_active=True).first()

        if not api_key_obj:
            return jsonify({'error': 'Invalid API key'}), 401

        # Verify the full key
        if not api_key_obj.check_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401

        # Get user
        user = User.query.get(api_key_obj.user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid or inactive user'}), 401

        # Update last_used_at
        api_key_obj.last_used_at = datetime.utcnow()
        db.session.commit()

        # Inject current_user into kwargs
        kwargs['current_user'] = user
        return fn(*args, **kwargs)

    return wrapper
