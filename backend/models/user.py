from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    display_name = db.Column(db.String(100))  # Optional display name for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)

    # Password reset fields
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_sent_at = db.Column(db.DateTime, nullable=True)

    # Account lockout fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Stripe fields
    stripe_customer_id = db.Column(db.String(255), nullable=True, unique=True, index=True)

    # Language preference (de = German, en = English)
    language = db.Column(db.String(5), nullable=False, default='de')

    # Subscription usage tracking
    applications_this_month = db.Column(db.Integer, default=0, nullable=False)
    month_reset_at = db.Column(db.DateTime, nullable=True)

    # Weekly goal tracking
    weekly_goal = db.Column(db.Integer, default=5, nullable=False)

    # Relationships
    documents = db.relationship("Document", back_populates="user", cascade="all, delete-orphan")
    templates = db.relationship("Template", back_populates="user", cascade="all, delete-orphan")
    applications = db.relationship("Application", back_populates="user", cascade="all, delete-orphan")
    api_keys = db.relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    email_accounts = db.relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
    subscription = db.relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skills = db.relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    job_recommendations = db.relationship("JobRecommendation", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "stripe_customer_id": self.stripe_customer_id,
            "applications_this_month": self.applications_this_month,
            "month_reset_at": self.month_reset_at.isoformat() if self.month_reset_at else None,
            "subscription": self.subscription.to_dict() if self.subscription else None,
            "weekly_goal": self.weekly_goal,
            "language": self.language,
        }
