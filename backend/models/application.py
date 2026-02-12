import json
from datetime import datetime

from . import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"))
    datum = db.Column(db.DateTime, default=datetime.utcnow)
    firma = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255))
    ansprechpartner = db.Column(db.Text)
    email = db.Column(db.String(255))
    quelle = db.Column(db.String(255))
    status = db.Column(db.String(50), default="erstellt")
    pdf_path = db.Column(db.String(500))
    betreff = db.Column(db.Text)
    email_text = db.Column(db.Text)
    einleitung = db.Column(db.Text)  # Generated intro paragraph for "holy shit" moment
    notizen = db.Column(db.Text)
    links_json = db.Column(db.Text)  # JSON stored as text
    sent_at = db.Column(db.DateTime, nullable=True)
    sent_via = db.Column(db.String(50), nullable=True)  # 'gmail' or 'outlook'
    status_history = db.Column(db.Text, nullable=True)  # JSON array of status changes

    # Interview Tracking
    interview_date = db.Column(db.DateTime, nullable=True)  # Geplantes Interview-Datum
    interview_feedback = db.Column(db.Text, nullable=True)  # Eigenes Feedback nach Interview
    interview_result = db.Column(db.String(50), nullable=True)  # scheduled, completed, passed, rejected, offer_received

    # Job-Fit Score (calculated after generation)
    job_fit_score = db.Column(db.Integer, nullable=True)  # 0-100

    # Relationships
    user = db.relationship("User", back_populates="applications")
    template = db.relationship("Template", back_populates="applications")
    requirements = db.relationship("JobRequirement", back_populates="application", cascade="all, delete-orphan")
    interview_questions = db.relationship(
        "InterviewQuestion", back_populates="application", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "datum": self.datum.isoformat() if self.datum else None,
            "firma": self.firma,
            "position": self.position,
            "ansprechpartner": self.ansprechpartner,
            "email": self.email,
            "quelle": self.quelle,
            "status": self.status,
            "pdf_path": self.pdf_path,
            "betreff": self.betreff,
            "email_text": self.email_text,
            "einleitung": self.einleitung,
            "notizen": self.notizen,
            "links_json": self.links_json,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_via": self.sent_via,
            "status_history": self.get_status_history(),
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "interview_feedback": self.interview_feedback,
            "interview_result": self.interview_result,
            "job_fit_score": self.job_fit_score,
        }

    def get_status_history(self) -> list[dict]:
        """Parse status_history JSON or return empty list."""
        if not self.status_history:
            return []
        try:
            return json.loads(self.status_history)
        except (json.JSONDecodeError, TypeError):
            return []

    def add_status_change(self, new_status: str, timestamp: datetime | None = None) -> None:
        """Add a status change to the history."""
        history = self.get_status_history()
        if timestamp is None:
            timestamp = datetime.utcnow()
        history.append({"status": new_status, "timestamp": timestamp.isoformat()})
        self.status_history = json.dumps(history)
