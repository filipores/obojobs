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
    notizen = db.Column(db.Text)
    links_json = db.Column(db.Text)  # JSON stored as text
    sent_at = db.Column(db.DateTime, nullable=True)
    sent_via = db.Column(db.String(50), nullable=True)  # 'gmail' or 'outlook'

    # Relationships
    user = db.relationship("User", back_populates="applications")
    template = db.relationship("Template", back_populates="applications")

    def to_dict(self):
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
            "notizen": self.notizen,
            "links_json": self.links_json,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_via": self.sent_via,
        }
