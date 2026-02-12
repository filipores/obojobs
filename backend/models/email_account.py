import os
from datetime import datetime

from cryptography.fernet import Fernet

from . import db


def get_fernet() -> Fernet:
    """Get Fernet instance using EMAIL_ENCRYPTION_KEY from environment."""
    key = os.environ.get("EMAIL_ENCRYPTION_KEY")
    if not key:
        raise ValueError("EMAIL_ENCRYPTION_KEY environment variable is not set")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token: str | None) -> str | None:
    """Encrypt a token string using Fernet encryption."""
    if token is None:
        return None
    fernet = get_fernet()
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str | None) -> str | None:
    """Decrypt an encrypted token string using Fernet encryption."""
    if encrypted_token is None:
        return None
    fernet = get_fernet()
    return fernet.decrypt(encrypted_token.encode()).decode()


class EmailAccount(db.Model):
    __tablename__ = "email_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    provider = db.Column(db.String(50), nullable=False)  # 'gmail' or 'outlook'
    email = db.Column(db.String(255), nullable=False)
    access_token_encrypted = db.Column(db.Text, nullable=True)
    refresh_token_encrypted = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship("User", back_populates="email_accounts")

    def set_access_token(self, token: str | None) -> None:
        """Encrypt and store the access token."""
        self.access_token_encrypted = encrypt_token(token)

    def get_access_token(self) -> str | None:
        """Decrypt and return the access token."""
        return decrypt_token(self.access_token_encrypted)

    def set_refresh_token(self, token: str | None) -> None:
        """Encrypt and store the refresh token."""
        self.refresh_token_encrypted = encrypt_token(token)

    def get_refresh_token(self) -> str | None:
        """Decrypt and return the refresh token."""
        return decrypt_token(self.refresh_token_encrypted)

    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.token_expires_at is None:
            return True
        return datetime.utcnow() >= self.token_expires_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "email": self.email,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
