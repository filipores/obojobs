from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(db.Model):  # type: ignore[name-defined]
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    full_name = db.Column(db.String(255))
    display_name = db.Column(db.String(100))  # Optional display name for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

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

    # OAuth fields
    google_id = db.Column(db.String(255), nullable=True, unique=True, index=True)

    # Language preference (de = German, en = English)
    language = db.Column(db.String(5), nullable=False, default="de")

    # Subscription usage tracking
    applications_this_month = db.Column(db.Integer, default=0, nullable=False)
    month_reset_at = db.Column(db.DateTime, nullable=True)

    # Credit-based system: one-time purchases add credits, each generation costs 1
    credits_remaining = db.Column(db.Integer, default=10, nullable=False)

    # Weekly goal tracking
    weekly_goal = db.Column(db.Integer, default=5, nullable=False)

    # Job search preferences (used by auto-recommendation scheduler)
    preferred_location = db.Column(db.String(255), nullable=True)  # e.g. "Berlin", "München"
    preferred_working_time = db.Column(
        db.String(10), nullable=True
    )  # 'vz' (Vollzeit), 'tz' (Teilzeit), 'ho' (Homeoffice)

    # Personal contact details (for templates/PDFs)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(255), nullable=True)

    # Relationships
    documents = db.relationship("Document", back_populates="user", cascade="all, delete-orphan")
    templates = db.relationship("Template", back_populates="user", cascade="all, delete-orphan")
    applications = db.relationship("Application", back_populates="user", cascade="all, delete-orphan")
    api_keys = db.relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    email_accounts = db.relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
    subscription = db.relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skills = db.relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    job_recommendations = db.relationship("JobRecommendation", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False  # OAuth-only users cannot login with password
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "email_verified": self.email_verified,
            "stripe_customer_id": self.stripe_customer_id,
            "applications_this_month": self.applications_this_month,
            "month_reset_at": self.month_reset_at.isoformat() if self.month_reset_at else None,
            "credits_remaining": self.credits_remaining,
            "subscription": self.subscription.to_dict() if self.subscription else None,
            "weekly_goal": self.weekly_goal,
            "language": self.language,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "website": self.website,
            "preferred_location": self.preferred_location,
            "preferred_working_time": self.preferred_working_time,
        }
