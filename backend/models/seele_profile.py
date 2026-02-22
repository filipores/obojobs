import json
from datetime import datetime

from . import db


class SeeleProfile(db.Model):  # type: ignore[name-defined]
    __tablename__ = "seele_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    profil_json = db.Column(db.Text, nullable=False, default="{}")
    version = db.Column(db.Integer, nullable=False, default=1)
    vollstaendigkeit = db.Column(db.Integer, nullable=False, default=0)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship("User", backref=db.backref("seele_profile", uselist=False, cascade="all, delete-orphan"))

    def get_profil(self):
        """Parse and return the profile as dict."""
        try:
            return json.loads(self.profil_json) if self.profil_json else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_profil(self, data):
        """Set profile from dict, update version."""
        self.profil_json = json.dumps(data, ensure_ascii=False)
        self.version += 1
        self.aktualisiert_am = datetime.utcnow()

    def berechne_vollstaendigkeit(self):
        """Calculate profile completeness as percentage."""
        profil = self.get_profil()
        if not profil:
            self.vollstaendigkeit = 0
            return 0

        total_fields = 0
        filled_fields = 0

        for section_key, section_data in profil.items():
            if section_key == "meta":
                continue
            if not isinstance(section_data, dict):
                continue
            for field_val in section_data.values():
                total_fields += 1
                if field_val and field_val != [] and field_val != {}:
                    filled_fields += 1

        pct = round((filled_fields / total_fields * 100) if total_fields > 0 else 0)
        self.vollstaendigkeit = pct
        return pct

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "profil": self.get_profil(),
            "version": self.version,
            "vollstaendigkeit": self.vollstaendigkeit,
            "erstellt_am": self.erstellt_am.isoformat() if self.erstellt_am else None,
            "aktualisiert_am": self.aktualisiert_am.isoformat() if self.aktualisiert_am else None,
        }
