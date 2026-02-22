"""Integration tests for Seele - end-to-end session flow and prompt injection."""

import json
from unittest.mock import patch

from models import SeeleAntwort, SeeleProfile, SeeleSession, db
from services import seele_service

MOCK_ONBOARDING_FRAGEN = [
    {
        "key": "motivation.aktuelle_situation",
        "frage": "Was beschreibt deine aktuelle Situation am besten?",
        "typ": "chips",
        "optionen": ["Aktiv auf Jobsuche", "Offen für Neues", "Karrierewechsel"],
        "mehrfach": False,
    },
    {
        "key": "arbeitsstil.arbeitsmodell",
        "frage": "Welches Arbeitsmodell passt zu dir?",
        "typ": "chips",
        "optionen": ["Remote", "Hybrid", "Vor Ort"],
        "mehrfach": True,
    },
    {
        "key": "motivation.wichtig_im_job",
        "frage": "Was ist dir im nächsten Job wichtig?",
        "typ": "chips_freitext",
        "optionen": ["Work-Life-Balance", "Gehalt", "Teamkultur"],
        "mehrfach": True,
        "max_auswahl": 5,
    },
    {
        "key": "motivation.wechsel_tempo",
        "frage": "Wie schnell möchtest du wechseln?",
        "typ": "chips",
        "optionen": ["Sofort verfügbar", "In 1-3 Monaten", "Schaue mich nur um"],
        "mehrfach": False,
    },
]


class TestEndToEndSessionFlow:
    """End-to-end: Start session -> Answer questions -> Profile in prompt."""

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_full_flow_via_api(self, mock_gen, mock_micro, client, auth_headers, test_user):
        """Complete flow through API endpoints."""
        # 1. Check: should recommend session
        check = client.get("/api/seele/check?trigger=dashboard", headers=auth_headers)
        assert check.get_json()["soll_starten"] is True

        # 2. Start session
        start = client.post(
            "/api/seele/sessions",
            headers=auth_headers,
            json={"session_typ": "onboarding"},
        )
        assert start.status_code == 201
        session_id = start.get_json()["session"]["id"]
        fragen = start.get_json()["fragen"]
        assert len(fragen) > 0

        # 3. Answer first question
        first_key = fragen[0]["key"]
        answer1 = client.post(
            "/api/seele/antworten",
            headers=auth_headers,
            json={
                "session_id": session_id,
                "frage_key": first_key,
                "antwort": "Aktiv auf Jobsuche",
            },
        )
        assert answer1.status_code == 200
        assert answer1.get_json()["session"]["fragen_beantwortet"] == 1

        # 4. Skip second question
        second_key = fragen[1]["key"]
        skip = client.post(
            "/api/seele/antworten/ueberspringen",
            headers=auth_headers,
            json={
                "session_id": session_id,
                "frage_key": second_key,
            },
        )
        assert skip.status_code == 200
        assert skip.get_json()["session"]["fragen_uebersprungen"] == 1

        # 5. Answer remaining questions
        remaining = skip.get_json()["naechste_fragen"]
        for frage in remaining:
            if frage.get("optionen"):
                antwort_val = frage["optionen"][0]
            else:
                antwort_val = "test_value"
            client.post(
                "/api/seele/antworten",
                headers=auth_headers,
                json={
                    "session_id": session_id,
                    "frage_key": frage["key"],
                    "antwort": antwort_val,
                },
            )

        # 6. Verify session closed
        aktuell = client.get("/api/seele/sessions/aktuell", headers=auth_headers)
        assert aktuell.get_json()["session"] is None

        # 7. Verify profile has data
        profil = client.get("/api/seele/profil", headers=auth_headers)
        assert profil.status_code == 200
        profil_data = profil.get_json()["profil"]
        assert profil_data["vollstaendigkeit"] > 0

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_profile_in_prompt_after_session(self, mock_gen, mock_micro, app, test_user):
        """After answering questions, profile text is available for prompt injection."""
        # Start and complete a session
        result = seele_service.starte_session(test_user["id"], "onboarding")
        session_id = result["session"]["id"]

        for frage in result["fragen"]:
            if frage.get("optionen"):
                antwort_val = frage["optionen"][0]
            else:
                antwort_val = "test"
            seele_service.beantworte_frage(test_user["id"], session_id, frage["key"], antwort_val)

        # Check prompt text
        prompt_text = seele_service.get_profil_fuer_generation(test_user["id"])
        assert prompt_text is not None
        assert "Aktiv auf Jobsuche" in prompt_text

    def test_profile_update_preserves_existing(self, app, test_user):
        """Updating one section doesn't erase others."""
        seele_service.get_or_create_profil(test_user["id"])

        # Set motivation
        seele_service.update_profil(
            test_user["id"],
            {"motivation": {"aktuelle_situation": "Karrierewechsel"}},
        )

        # Set arbeitsstil (should not erase motivation)
        seele_service.update_profil(
            test_user["id"],
            {"arbeitsstil": {"typ": "Remote"}},
        )

        profile = SeeleProfile.query.filter_by(user_id=test_user["id"]).first()
        profil = profile.get_profil()
        assert profil["motivation"]["aktuelle_situation"] == "Karrierewechsel"
        assert profil["arbeitsstil"]["typ"] == "Remote"

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_session_abort_and_restart(self, mock_gen, mock_micro, app, test_user):
        """Abort session, then start new one."""
        # Start and abort
        result = seele_service.starte_session(test_user["id"], "onboarding")
        session_id = result["session"]["id"]
        seele_service.beende_session(test_user["id"], session_id)

        # Verify aborted
        session = SeeleSession.query.get(session_id)
        assert session.status == "abgebrochen"

        # Start new session (should work since old one is not active)
        result2 = seele_service.starte_session(test_user["id"], "onboarding")
        assert result2["session"]["id"] != session_id
        assert result2["session"]["status"] == "aktiv"

    def test_no_profile_returns_none_for_generation(self, app, test_user):
        """Without any profile, generation gets None (backward compatible)."""
        result = seele_service.get_profil_fuer_generation(test_user["id"])
        assert result is None

    def test_sparse_profile_returns_none_for_generation(self, app, test_user):
        """Very sparse profile (< 10%) returns None."""
        seele_service.get_or_create_profil(test_user["id"])
        result = seele_service.get_profil_fuer_generation(test_user["id"])
        assert result is None


class TestPromptIntegration:
    """Test that Seele profile integrates into Anschreiben prompts."""

    def test_prompt_includes_seele_section(self):
        """build_anschreiben_system_prompt includes Seele section when provided."""
        from services.prompts import build_anschreiben_system_prompt

        seele_text = "- Aktuelle Situation: Aktiv auf Jobsuche\n- Arbeitsmodell: Remote"

        prompt = build_anschreiben_system_prompt(
            cv_text="Test CV",
            position="Software Engineer",
            quelle="LinkedIn",
            ansprechpartner="Herr Müller",
            seele_profil_text=seele_text,
        )

        assert "SEELE-PROFIL" in prompt
        assert "Aktiv auf Jobsuche" in prompt
        assert "Arbeitsmodell: Remote" in prompt

    def test_prompt_without_seele(self):
        """build_anschreiben_system_prompt works without Seele (backward compatible)."""
        from services.prompts import build_anschreiben_system_prompt

        prompt = build_anschreiben_system_prompt(
            cv_text="Test CV",
            position="Software Engineer",
            quelle="LinkedIn",
            ansprechpartner="Herr Müller",
        )

        assert "SEELE-PROFIL" not in prompt
        # Prompt should still work normally
        assert "Software Engineer" in prompt

    def test_prompt_with_none_seele(self):
        """Explicit None for seele_profil_text does not include section."""
        from services.prompts import build_anschreiben_system_prompt

        prompt = build_anschreiben_system_prompt(
            cv_text="Test CV",
            position="Developer",
            quelle="Manual",
            ansprechpartner="",
            seele_profil_text=None,
        )

        assert "SEELE-PROFIL" not in prompt


class TestDatabaseIntegrity:
    """Test database relationships and constraints."""

    def test_multiple_sessions_per_user(self, app, test_user):
        """User can have multiple sessions (but only one active)."""
        s1 = SeeleSession(
            user_id=test_user["id"],
            session_typ="onboarding",
            status="abgeschlossen",
        )
        s2 = SeeleSession(
            user_id=test_user["id"],
            session_typ="pre_bewerbung",
            status="aktiv",
        )
        db.session.add_all([s1, s2])
        db.session.commit()

        sessions = SeeleSession.query.filter_by(user_id=test_user["id"]).all()
        assert len(sessions) == 2

    def test_answers_linked_to_correct_session(self, app, test_user):
        """Answers are correctly linked to their session."""
        s1 = SeeleSession(user_id=test_user["id"], session_typ="onboarding")
        s2 = SeeleSession(user_id=test_user["id"], session_typ="pre_bewerbung")
        db.session.add_all([s1, s2])
        db.session.commit()

        a1 = SeeleAntwort(
            session_id=s1.id,
            user_id=test_user["id"],
            frage_key="test.key1",
            frage_text="Q1",
            antwort_typ="chips",
        )
        a2 = SeeleAntwort(
            session_id=s2.id,
            user_id=test_user["id"],
            frage_key="test.key2",
            frage_text="Q2",
            antwort_typ="chips",
        )
        db.session.add_all([a1, a2])
        db.session.commit()

        assert s1.antworten.count() == 1
        assert s2.antworten.count() == 1
        assert s1.antworten.first().frage_key == "test.key1"

    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_ONBOARDING_FRAGEN)
    def test_cached_fragen_survive_reload(self, mock_gen, mock_micro, app, test_user):
        """Questions cached in kontext_json persist across session lookups."""
        result = seele_service.starte_session(test_user["id"], "onboarding")
        session_id = result["session"]["id"]

        # Simulate page reload - get session again
        session = SeeleSession.query.get(session_id)
        kontext = json.loads(session.kontext_json)
        assert "generierte_fragen" in kontext
        assert len(kontext["generierte_fragen"]) == len(MOCK_ONBOARDING_FRAGEN)
