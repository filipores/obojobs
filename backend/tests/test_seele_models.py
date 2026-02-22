"""Tests for Seele models - CRUD, to_dict(), cascade delete, completeness."""

import json

import pytest

from models import SeeleAntwort, SeeleProfile, SeeleSession, User, db


class TestSeeleProfile:
    """Tests for SeeleProfile model."""

    def test_create_profile(self, app, test_user):
        """Create a profile with empty JSON."""
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json="{}",
            version=1,
            vollstaendigkeit=0,
        )
        db.session.add(profile)
        db.session.commit()

        assert profile.id is not None
        assert profile.user_id == test_user["id"]
        assert profile.version == 1
        assert profile.vollstaendigkeit == 0
        assert profile.erstellt_am is not None

    def test_unique_user_constraint(self, app, test_user):
        """Only one profile per user."""
        p1 = SeeleProfile(user_id=test_user["id"], profil_json="{}")
        db.session.add(p1)
        db.session.commit()

        p2 = SeeleProfile(user_id=test_user["id"], profil_json="{}")
        db.session.add(p2)
        with pytest.raises(Exception):  # noqa: B017
            db.session.commit()
        db.session.rollback()

    def test_get_profil_empty(self, app, test_user):
        """get_profil() returns empty dict for empty JSON."""
        profile = SeeleProfile(user_id=test_user["id"], profil_json="{}")
        db.session.add(profile)
        db.session.commit()

        assert profile.get_profil() == {}

    def test_get_profil_with_data(self, app, test_user):
        """get_profil() parses stored JSON."""
        data = {"motivation": {"aktuelle_situation": "Aktiv auf Jobsuche"}}
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json=json.dumps(data),
        )
        db.session.add(profile)
        db.session.commit()

        result = profile.get_profil()
        assert result["motivation"]["aktuelle_situation"] == "Aktiv auf Jobsuche"

    def test_get_profil_invalid_json(self, app, test_user):
        """get_profil() handles corrupt JSON gracefully."""
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json="not valid json {{{",
        )
        db.session.add(profile)
        db.session.commit()

        assert profile.get_profil() == {}

    def test_set_profil(self, app, test_user):
        """set_profil() serializes data and increments version."""
        profile = SeeleProfile(user_id=test_user["id"], profil_json="{}", version=1)
        db.session.add(profile)
        db.session.commit()

        data = {"arbeitsstil": {"typ": "Remote"}}
        profile.set_profil(data)
        db.session.commit()

        assert profile.version == 2
        assert profile.get_profil()["arbeitsstil"]["typ"] == "Remote"

    def test_berechne_vollstaendigkeit_empty(self, app, test_user):
        """Empty profile = 0% completeness."""
        profile = SeeleProfile(user_id=test_user["id"], profil_json="{}")
        db.session.add(profile)
        db.session.commit()

        assert profile.berechne_vollstaendigkeit() == 0

    def test_berechne_vollstaendigkeit_partial(self, app, test_user):
        """Partial profile returns percentage > 0."""
        from services.seele_profile_builder import erstelle_leeres_profil

        data = erstelle_leeres_profil()
        data["motivation"]["aktuelle_situation"] = "Aktiv auf Jobsuche"
        data["arbeitsstil"]["typ"] = "Remote"

        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json=json.dumps(data),
        )
        db.session.add(profile)
        db.session.commit()

        pct = profile.berechne_vollstaendigkeit()
        assert pct > 0
        assert pct < 100
        assert profile.vollstaendigkeit == pct

    def test_berechne_vollstaendigkeit_ignores_meta(self, app, test_user):
        """Meta section should not count toward completeness."""
        data = {
            "meta": {"quellen": {"cv": True}, "confidence": {"high": True}, "letzte_session": "2026-01-01"},
            "motivation": {"aktuelle_situation": None},
        }
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json=json.dumps(data),
        )
        db.session.add(profile)
        db.session.commit()

        pct = profile.berechne_vollstaendigkeit()
        assert pct == 0  # Only motivation section, one field, unfilled

    def test_to_dict(self, app, test_user):
        """to_dict() returns all expected fields."""
        data = {"motivation": {"aktuelle_situation": "Offen"}}
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json=json.dumps(data),
            version=3,
            vollstaendigkeit=25,
        )
        db.session.add(profile)
        db.session.commit()

        d = profile.to_dict()
        assert d["user_id"] == test_user["id"]
        assert d["profil"]["motivation"]["aktuelle_situation"] == "Offen"
        assert d["version"] == 3
        assert d["vollstaendigkeit"] == 25
        assert "erstellt_am" in d
        assert "aktualisiert_am" in d

    def test_cascade_delete(self, app, test_user):
        """Deleting user cascades to profile."""
        profile = SeeleProfile(user_id=test_user["id"], profil_json="{}")
        db.session.add(profile)
        db.session.commit()
        profile_id = profile.id

        user = User.query.get(test_user["id"])
        db.session.delete(user)
        db.session.commit()

        assert SeeleProfile.query.get(profile_id) is None

    def test_user_backref(self, app, test_user):
        """User.seele_profile backref returns profile (uselist=False)."""
        profile = SeeleProfile(user_id=test_user["id"], profil_json="{}")
        db.session.add(profile)
        db.session.commit()

        user = User.query.get(test_user["id"])
        assert user.seele_profile is not None
        assert user.seele_profile.id == profile.id


class TestSeeleSession:
    """Tests for SeeleSession model."""

    def test_create_session(self, app, test_user):
        """Create a session with defaults."""
        session = SeeleSession(
            user_id=test_user["id"],
            session_typ="onboarding",
        )
        db.session.add(session)
        db.session.commit()

        assert session.id is not None
        assert session.status == "aktiv"
        assert session.fragen_geplant == 0
        assert session.fragen_beantwortet == 0
        assert session.fragen_uebersprungen == 0
        assert session.gestartet_am is not None

    def test_session_types(self, app, test_user):
        """All 3 session types can be created."""
        for typ in ("onboarding", "pre_bewerbung", "micro"):
            s = SeeleSession(user_id=test_user["id"], session_typ=typ)
            db.session.add(s)
        db.session.commit()

        sessions = SeeleSession.query.filter_by(user_id=test_user["id"]).all()
        assert len(sessions) == 3

    def test_to_dict(self, app, test_user):
        """to_dict() returns all expected fields."""
        session = SeeleSession(
            user_id=test_user["id"],
            session_typ="onboarding",
            fragen_geplant=4,
            kontext_json='{"trigger": "cv_upload"}',
        )
        db.session.add(session)
        db.session.commit()

        d = session.to_dict()
        assert d["session_typ"] == "onboarding"
        assert d["status"] == "aktiv"
        assert d["fragen_geplant"] == 4
        assert d["kontext"]["trigger"] == "cv_upload"
        assert "gestartet_am" in d

    def test_to_dict_no_kontext(self, app, test_user):
        """to_dict() handles null kontext_json."""
        session = SeeleSession(
            user_id=test_user["id"],
            session_typ="onboarding",
        )
        db.session.add(session)
        db.session.commit()

        d = session.to_dict()
        assert d["kontext"] is None


class TestSeeleAntwort:
    """Tests for SeeleAntwort model."""

    def test_create_antwort(self, app, test_user):
        """Create an answer record."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        antwort = SeeleAntwort(
            session_id=session.id,
            user_id=test_user["id"],
            frage_key="motivation.aktuelle_situation",
            frage_text="Was beschreibt deine aktuelle Situation am besten?",
            antwort_typ="chips",
            antwort_json=json.dumps("Aktiv auf Jobsuche"),
        )
        db.session.add(antwort)
        db.session.commit()

        assert antwort.id is not None
        assert antwort.uebersprungen is False
        assert antwort.beantwortet_am is not None

    def test_get_antwort_string(self, app, test_user):
        """get_antwort() returns parsed string."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        antwort = SeeleAntwort(
            session_id=session.id,
            user_id=test_user["id"],
            frage_key="arbeitsstil.typ",
            frage_text="Test",
            antwort_typ="chips",
            antwort_json=json.dumps("Remote"),
        )
        db.session.add(antwort)
        db.session.commit()

        assert antwort.get_antwort() == "Remote"

    def test_get_antwort_list(self, app, test_user):
        """get_antwort() returns parsed list."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        antwort = SeeleAntwort(
            session_id=session.id,
            user_id=test_user["id"],
            frage_key="motivation.wichtig_im_job",
            frage_text="Test",
            antwort_typ="chips_freitext",
            antwort_json=json.dumps(["Work-Life-Balance", "Gehalt"]),
        )
        db.session.add(antwort)
        db.session.commit()

        result = antwort.get_antwort()
        assert isinstance(result, list)
        assert "Work-Life-Balance" in result

    def test_get_antwort_skipped(self, app, test_user):
        """get_antwort() returns None for skipped questions."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        antwort = SeeleAntwort(
            session_id=session.id,
            user_id=test_user["id"],
            frage_key="test.key",
            frage_text="Test",
            antwort_typ="chips",
            antwort_json=None,
            uebersprungen=True,
        )
        db.session.add(antwort)
        db.session.commit()

        assert antwort.get_antwort() is None
        assert antwort.uebersprungen is True

    def test_to_dict(self, app, test_user):
        """to_dict() returns all expected fields."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        antwort = SeeleAntwort(
            session_id=session.id,
            user_id=test_user["id"],
            frage_key="arbeitsstil.teamrolle",
            frage_text="Welche Rolle?",
            antwort_typ="chips",
            antwort_json=json.dumps("Umsetzer"),
        )
        db.session.add(antwort)
        db.session.commit()

        d = antwort.to_dict()
        assert d["frage_key"] == "arbeitsstil.teamrolle"
        assert d["frage_text"] == "Welche Rolle?"
        assert d["antwort_typ"] == "chips"
        assert d["antwort"] == "Umsetzer"
        assert d["uebersprungen"] is False
        assert "beantwortet_am" in d

    def test_cascade_delete_from_session(self, app, test_user):
        """Deleting session cascades to answers."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        antwort = SeeleAntwort(
            session_id=session.id,
            user_id=test_user["id"],
            frage_key="test.key",
            frage_text="Test",
            antwort_typ="chips",
        )
        db.session.add(antwort)
        db.session.commit()
        antwort_id = antwort.id

        db.session.delete(session)
        db.session.commit()

        assert SeeleAntwort.query.get(antwort_id) is None

    def test_session_antworten_relationship(self, app, test_user):
        """Session.antworten backref works."""
        session = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        db.session.add(session)
        db.session.commit()

        for i in range(3):
            a = SeeleAntwort(
                session_id=session.id,
                user_id=test_user["id"],
                frage_key=f"test.key{i}",
                frage_text=f"Frage {i}",
                antwort_typ="chips",
            )
            db.session.add(a)
        db.session.commit()

        assert session.antworten.count() == 3
