from datetime import datetime

from . import db


class TokenBlacklist(db.Model):
    """
    Model for storing invalidated JWT tokens.
    Used for implementing logout functionality.
    Tokens are stored with their JTI (JWT ID) for efficient lookup.
    """

    __tablename__ = "token_blacklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Relationship
    user = db.relationship("User", backref=db.backref("blacklisted_tokens", lazy="dynamic"))

    @classmethod
    def is_token_blacklisted(cls, jti: str) -> bool:
        """Check if a token JTI is in the blacklist."""
        return cls.query.filter_by(jti=jti).first() is not None

    @classmethod
    def add_token(cls, jti: str, token_type: str, user_id: int, expires_at: datetime) -> "TokenBlacklist":
        """Add a token to the blacklist."""
        blacklisted = cls(jti=jti, token_type=token_type, user_id=user_id, expires_at=expires_at)
        db.session.add(blacklisted)
        db.session.commit()
        return blacklisted

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired tokens from blacklist. Returns count of removed tokens."""
        now = datetime.utcnow()
        result = cls.query.filter(cls.expires_at < now).delete()
        db.session.commit()
        return result
