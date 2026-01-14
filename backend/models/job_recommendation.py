"""
JobRecommendation Model - Stores job recommendations based on user profile and job-fit score.
"""

import json
from datetime import datetime

from . import db


class JobRecommendation(db.Model):
    __tablename__ = "job_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_data_json = db.Column(db.Text, nullable=False)  # Stored as JSON text
    fit_score = db.Column(db.Integer, nullable=False)  # 0-100
    fit_category = db.Column(db.String(50), nullable=False)  # sehr_gut, gut, mittel
    source = db.Column(db.String(100))  # Job board source (indeed, stepstone, etc.)
    job_url = db.Column(db.String(500))
    job_title = db.Column(db.String(255))
    company_name = db.Column(db.String(255))
    location = db.Column(db.String(255))
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)
    dismissed = db.Column(db.Boolean, default=False)  # User dismissed this recommendation
    applied = db.Column(db.Boolean, default=False)  # User started an application
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="job_recommendations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_data": self.get_job_data(),
            "fit_score": self.fit_score,
            "fit_category": self.fit_category,
            "source": self.source,
            "job_url": self.job_url,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "location": self.location,
            "recommended_at": self.recommended_at.isoformat() if self.recommended_at else None,
            "dismissed": self.dismissed,
            "applied": self.applied,
            "application_id": self.application_id,
        }

    def get_job_data(self) -> dict:
        """Parse job_data JSON or return empty dict."""
        if not self.job_data_json:
            return {}
        try:
            return json.loads(self.job_data_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_job_data(self, data: dict):
        """Serialize job data to JSON."""
        self.job_data_json = json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_job_data(cls, user_id: int, job_data: dict, fit_score: int, fit_category: str):
        """Create a JobRecommendation from scraped job data."""
        recommendation = cls(
            user_id=user_id,
            fit_score=fit_score,
            fit_category=fit_category,
            source=job_data.get("source", "unknown"),
            job_url=job_data.get("url") or job_data.get("source_url"),
            job_title=job_data.get("title"),
            company_name=job_data.get("company"),
            location=job_data.get("location"),
        )
        recommendation.set_job_data(job_data)
        return recommendation
