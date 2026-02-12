from datetime import datetime

from . import db


class UserSkill(db.Model):  # type: ignore[name-defined]
    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    skill_name = db.Column(db.String(255), nullable=False)
    skill_category = db.Column(
        db.String(50), nullable=False
    )  # technical, soft_skills, languages, tools, certifications
    experience_years = db.Column(db.Float, nullable=True)  # Jahre Erfahrung, kann null sein
    source_document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="skills")
    source_document = db.relationship("Document", backref="extracted_skills")

    # Valid categories
    VALID_CATEGORIES = ["technical", "soft_skills", "languages", "tools", "certifications"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_name": self.skill_name,
            "skill_category": self.skill_category,
            "experience_years": self.experience_years,
            "source_document_id": self.source_document_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def validate_category(cls, category: str) -> bool:
        return category in cls.VALID_CATEGORIES
