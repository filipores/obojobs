from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    credits_remaining = db.Column(db.Integer, default=5)  # Changed from 50 to 5
    credits_max = db.Column(db.Integer, default=50)  # Kept for backward compatibility
    total_credits_purchased = db.Column(db.Integer, default=0)  # NEW: Track lifetime purchases
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    documents = db.relationship("Document", back_populates="user", cascade="all, delete-orphan")
    templates = db.relationship("Template", back_populates="user", cascade="all, delete-orphan")
    applications = db.relationship("Application", back_populates="user", cascade="all, delete-orphan")
    api_keys = db.relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    purchases = db.relationship("Purchase", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "credits_remaining": self.credits_remaining,
            "credits_max": self.credits_max,
            "total_credits_purchased": self.total_credits_purchased,
            "is_active": self.is_active,
        }
