from datetime import datetime

from . import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    doc_type = db.Column(db.String(50), nullable=False)  # cv_pdf, cv_summary, zeugnis, zeugnis_summary
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship("User", back_populates="documents")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "doc_type": self.doc_type,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
