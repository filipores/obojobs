import secrets
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class APIKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    key_hash = db.Column(db.String(255), nullable=False)
    key_prefix = db.Column(db.String(10), nullable=False, index=True)
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship
    user = db.relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key() -> str:
        """Generate a new API key with prefix mlr_"""
        return f"mlr_{secrets.token_urlsafe(32)}"

    def set_key(self, key: str) -> None:
        """Hash and store the API key"""
        self.key_hash = generate_password_hash(key)
        self.key_prefix = key[:8]  # Store first 8 chars for display

    def check_key(self, key: str) -> bool:
        """Verify an API key"""
        return check_password_hash(self.key_hash, key)

    def to_dict(self, include_prefix: bool = True) -> dict:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
        }
        if include_prefix:
            result["key_prefix"] = self.key_prefix
        return result
