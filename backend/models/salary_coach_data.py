"""
SalaryCoachData Model.

Stores salary research and negotiation strategy data for persistence.
"""

from datetime import datetime

from . import db


class SalaryCoachData(db.Model):
    """Model for storing salary coach research and strategy data."""

    __tablename__ = "salary_coach_data"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Form data
    position = db.Column(db.String(255), nullable=True)
    region = db.Column(db.String(255), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    target_salary = db.Column(db.Integer, nullable=True)
    current_salary = db.Column(db.Integer, nullable=True)
    industry = db.Column(db.String(255), nullable=True)

    # Research result (JSON)
    research_json = db.Column(db.Text, nullable=True)

    # Strategy result (JSON)
    strategy_json = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship("User", backref=db.backref("salary_coach_data", uselist=False))

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        import json

        research = None
        strategy = None

        try:
            if self.research_json:
                research = json.loads(self.research_json)
        except (json.JSONDecodeError, TypeError):
            pass

        try:
            if self.strategy_json:
                strategy = json.loads(self.strategy_json)
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "id": self.id,
            "formData": {
                "position": self.position or "",
                "region": self.region or "Deutschland",
                "experienceYears": self.experience_years or 3,
                "targetSalary": self.target_salary,
                "currentSalary": self.current_salary,
                "industry": self.industry or "",
            },
            "research": research,
            "strategy": strategy,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
