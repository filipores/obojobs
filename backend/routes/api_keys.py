from flask import Blueprint, request, jsonify

from middleware.jwt_required import jwt_required_custom
from models import db, APIKey

api_keys_bp = Blueprint('api_keys', __name__)


@api_keys_bp.route('', methods=['GET'])
@jwt_required_custom
def list_api_keys(current_user):
    """List user's API keys"""
    keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'success': True,
        'api_keys': [key.to_dict() for key in keys]
    }), 200


@api_keys_bp.route('', methods=['POST'])
@jwt_required_custom
def create_api_key(current_user):
    """Create a new API key"""
    data = request.json
    name = data.get('name', 'Chrome Extension')

    # Generate new key
    new_key = APIKey.generate_key()

    # Create API key record
    api_key_obj = APIKey(
        user_id=current_user.id,
        name=name
    )
    api_key_obj.set_key(new_key)

    db.session.add(api_key_obj)
    db.session.commit()

    # Return plaintext key ONCE
    return jsonify({
        'success': True,
        'api_key': new_key,  # Only time this is returned in plaintext
        'key_id': api_key_obj.id,
        'key_prefix': api_key_obj.key_prefix,
        'message': 'Save this key now, it will not be shown again'
    }), 201


@api_keys_bp.route('/<int:key_id>', methods=['DELETE'])
@jwt_required_custom
def delete_api_key(key_id, current_user):
    """Revoke an API key"""
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first()

    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    db.session.delete(api_key)
    db.session.commit()

    return jsonify({'success': True, 'message': 'API key revoked'}), 200
