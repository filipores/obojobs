from datetime import datetime

from . import db


class JobRequirement(db.Model):
    __tablename__ = "job_requirements"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False, index=True)
    requirement_text = db.Column(db.Text, nullable=False)
    requirement_type = db.Column(db.String(20), nullable=False)  # must_have, nice_to_have
    skill_category = db.Column(db.String(50), nullable=True)  # technical, soft_skills, languages, tools, certifications
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship("Application", back_populates="requirements")

    # Valid requirement types
    VALID_TYPES = ["must_have", "nice_to_have"]

    # Valid skill categories (same as UserSkill)
    VALID_CATEGORIES = ["technical", "soft_skills", "languages", "tools", "certifications"]

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "requirement_text": self.requirement_text,
            "requirement_type": self.requirement_type,
            "skill_category": self.skill_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def validate_type(cls, requirement_type):
        return requirement_type in cls.VALID_TYPES

    @classmethod
    def validate_category(cls, category):
        return category is None or category in cls.VALID_CATEGORIES
