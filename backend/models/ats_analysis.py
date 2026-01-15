"""
ATSAnalysis Model.

Stores ATS analysis results for caching and history functionality.
"""

import hashlib
from datetime import datetime

from . import db


class ATSAnalysis(db.Model):
    """Model for storing ATS analysis results."""

    __tablename__ = "ats_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_url = db.Column(db.String(2048), nullable=True, index=True)
    job_text_hash = db.Column(db.String(64), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=True)
    score = db.Column(db.Integer, nullable=False)
    result_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = db.relationship("User", backref=db.backref("ats_analyses", lazy="dynamic"))

    @staticmethod
    def hash_job_text(job_text: str) -> str:
        """Create a SHA-256 hash of job text for duplicate detection."""
        return hashlib.sha256(job_text.strip().lower().encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        import json

        result = {}
        try:
            result = json.loads(self.result_json)
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_url": self.job_url,
            "title": self.title,
            "score": self.score,
            "result": result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_summary_dict(self) -> dict:
        """Convert model to summary dictionary for history list."""
        import json

        result = {}
        try:
            result = json.loads(self.result_json)
        except (json.JSONDecodeError, TypeError):
            pass

        # Extract matched/missing counts for summary
        matched_count = len(result.get("matched_keywords", []))
        missing_count = len(result.get("missing_keywords", []))

        return {
            "id": self.id,
            "job_url": self.job_url,
            "title": self.title,
            "score": self.score,
            "matched_count": matched_count,
            "missing_count": missing_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
