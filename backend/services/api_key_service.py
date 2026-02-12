"""Service layer for API key management."""

from models import APIKey, db


def list_api_keys(user_id: int) -> list[APIKey]:
    """Return all API keys for the given user."""
    return APIKey.query.filter_by(user_id=user_id).all()


def create_api_key(user_id: int, name: str = "Chrome Extension") -> tuple[APIKey, str]:
    """Generate a new API key and return (api_key_obj, plaintext_key)."""
    new_key = APIKey.generate_key()
    api_key_obj = APIKey(user_id=user_id, name=name)
    api_key_obj.set_key(new_key)
    db.session.add(api_key_obj)
    db.session.commit()
    return api_key_obj, new_key


def delete_api_key(key_id: int, user_id: int) -> APIKey | None:
    """Delete an API key. Returns the key object or None if not found."""
    api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
    if not api_key:
        return None
    db.session.delete(api_key)
    db.session.commit()
    return api_key
