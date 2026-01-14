from datetime import datetime

from . import db


class InterviewQuestion(db.Model):
    __tablename__ = "interview_questions"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False)  # behavioral, technical, situational, company_specific, salary_negotiation
    difficulty = db.Column(db.String(20), default="medium")  # easy, medium, hard
    sample_answer = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship("Application", back_populates="interview_questions")

    # Valid question types
    VALID_TYPES = ["behavioral", "technical", "situational", "company_specific", "salary_negotiation"]

    # Valid difficulty levels
    VALID_DIFFICULTIES = ["easy", "medium", "hard"]

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "difficulty": self.difficulty,
            "sample_answer": self.sample_answer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def validate_type(cls, question_type):
        return question_type in cls.VALID_TYPES

    @classmethod
    def validate_difficulty(cls, difficulty):
        return difficulty in cls.VALID_DIFFICULTIES
