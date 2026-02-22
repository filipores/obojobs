import json
from datetime import datetime

from . import db


class SeeleAntwort(db.Model):  # type: ignore[name-defined]
    __tablename__ = "seele_antworten"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("seele_sessions.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    frage_key = db.Column(db.String(100), nullable=False)  # e.g. "arbeitsstil.typ"
    frage_text = db.Column(db.String(500), nullable=False)
    antwort_typ = db.Column(db.String(20), nullable=False)  # chips, freitext, chips_freitext, slider
    antwort_json = db.Column(db.Text, nullable=True)
    uebersprungen = db.Column(db.Boolean, nullable=False, default=False)
    beantwortet_am = db.Column(db.DateTime, default=datetime.utcnow)

    def get_antwort(self):
        try:
            return json.loads(self.antwort_json) if self.antwort_json else None
        except (json.JSONDecodeError, TypeError):
            return None

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "frage_key": self.frage_key,
            "frage_text": self.frage_text,
            "antwort_typ": self.antwort_typ,
            "antwort": self.get_antwort(),
            "uebersprungen": self.uebersprungen,
            "beantwortet_am": self.beantwortet_am.isoformat() if self.beantwortet_am else None,
        }
