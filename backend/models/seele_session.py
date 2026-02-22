import json
from datetime import datetime

from . import db


class SeeleSession(db.Model):  # type: ignore[name-defined]
    __tablename__ = "seele_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    session_typ = db.Column(db.String(30), nullable=False)  # onboarding, pre_bewerbung, micro
    status = db.Column(db.String(20), nullable=False, default="aktiv")  # aktiv, abgeschlossen, abgebrochen
    fragen_geplant = db.Column(db.Integer, nullable=False, default=0)
    fragen_beantwortet = db.Column(db.Integer, nullable=False, default=0)
    fragen_uebersprungen = db.Column(db.Integer, nullable=False, default=0)
    kontext_json = db.Column(db.Text, nullable=True)
    gestartet_am = db.Column(db.DateTime, default=datetime.utcnow)
    beendet_am = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship("User", backref=db.backref("seele_sessions", lazy="dynamic"))
    antworten = db.relationship("SeeleAntwort", backref="session", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_typ": self.session_typ,
            "status": self.status,
            "fragen_geplant": self.fragen_geplant,
            "fragen_beantwortet": self.fragen_beantwortet,
            "fragen_uebersprungen": self.fragen_uebersprungen,
            "kontext": json.loads(self.kontext_json) if self.kontext_json else None,
            "gestartet_am": self.gestartet_am.isoformat() if self.gestartet_am else None,
            "beendet_am": self.beendet_am.isoformat() if self.beendet_am else None,
        }
