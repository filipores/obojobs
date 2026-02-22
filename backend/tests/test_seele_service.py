"""Tests for Seele service layer - session lifecycle, answer merging, profile generation."""

import json
from unittest.mock import patch

import pytest

from models import SeeleAntwort, SeeleProfile, SeeleSession, db
from services import seele_cv_extraktor, seele_service
from services.seele_profile_builder import (
    berechne_vollstaendigkeit,
    erstelle_leeres_profil,
    merge_antwort,
    profil_fuer_prompt,
)

# Mock-Fragen fuer Tests (simulieren AI-generierte Fragen)
MOCK_PROFIL_FRAGEN = [
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


class TestProfileBuilder:
    """Tests for seele_profile_builder module."""

    def test_erstelle_leeres_profil(self):
        """Empty profile has all 8 sections."""
        profil = erstelle_leeres_profil()
        expected_sections = [
            "persoenliche_daten",
            "berufserfahrung",
            "qualifikationen",
            "arbeitsstil",
            "motivation",
            "gehaltsvorstellung",
            "persoenlichkeit",
            "meta",
        ]
        for section in expected_sections:
            assert section in profil

    def test_erstelle_leeres_profil_deep_copy(self):
        """Each call returns an independent copy."""
        p1 = erstelle_leeres_profil()
        p2 = erstelle_leeres_profil()
        p1["motivation"]["aktuelle_situation"] = "test"
        assert p2["motivation"]["aktuelle_situation"] is None

    def test_merge_antwort_string(self):
        """Merge string answer into dot-path location."""
        profil = erstelle_leeres_profil()
        result = merge_antwort(profil, "motivation.aktuelle_situation", "Aktiv auf Jobsuche")
        assert result["motivation"]["aktuelle_situation"] == "Aktiv auf Jobsuche"

    def test_merge_antwort_list(self):
        """Merge list answer."""
        profil = erstelle_leeres_profil()
        result = merge_antwort(profil, "motivation.wichtig_im_job", ["Gehalt", "Teamkultur"])
        assert result["motivation"]["wichtig_im_job"] == ["Gehalt", "Teamkultur"]

    def test_merge_antwort_number(self):
        """Merge numeric answer (slider)."""
        profil = erstelle_leeres_profil()
        result = merge_antwort(profil, "gehaltsvorstellung.wunsch", 65000)
        assert result["gehaltsvorstellung"]["wunsch"] == 65000

    def test_merge_antwort_none_profil(self):
        """Merging into None creates new profile."""
        result = merge_antwort(None, "arbeitsstil.typ", "Remote")
        assert result["arbeitsstil"]["typ"] == "Remote"

    def test_merge_antwort_invalid_key(self):
        """Invalid key (no dot) leaves profile unchanged."""
        profil = erstelle_leeres_profil()
        result = merge_antwort(profil, "invalidkey", "value")
        assert result == profil

    def test_merge_antwort_new_section(self):
        """Merge into non-existing section creates it."""
        profil = {"motivation": {"aktuelle_situation": None}}
        result = merge_antwort(profil, "neue_sektion.feld", "wert")
        assert result["neue_sektion"]["feld"] == "wert"

    def test_berechne_vollstaendigkeit_empty(self):
        """Empty profile = 0%."""
        assert berechne_vollstaendigkeit(erstelle_leeres_profil()) == 0

    def test_berechne_vollstaendigkeit_none(self):
        """None profile = 0%."""
        assert berechne_vollstaendigkeit(None) == 0

    def test_berechne_vollstaendigkeit_partial(self):
        """Partial profile returns value between 0 and 100."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv"
        profil["arbeitsstil"]["typ"] = "Remote"
        pct = berechne_vollstaendigkeit(profil)
        assert 0 < pct < 100

    def test_berechne_vollstaendigkeit_ignores_meta(self):
        """Meta section not counted."""
        profil = {
            "meta": {"quellen": {"cv": True}},
            "motivation": {"feld1": None},
        }
        assert berechne_vollstaendigkeit(profil) == 0

    def test_profil_fuer_prompt_none(self):
        """None profile returns None."""
        assert profil_fuer_prompt(None) is None

    def test_profil_fuer_prompt_empty(self):
        """Empty profile returns None (below 10% threshold)."""
        assert profil_fuer_prompt(erstelle_leeres_profil()) is None

    def test_profil_fuer_prompt_with_data(self):
        """Profile with data returns formatted text."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv auf Jobsuche"
        profil["motivation"]["wichtig_im_job"] = ["Gehalt", "Teamkultur"]
        profil["arbeitsstil"]["arbeitsmodell"] = ["Remote", "Hybrid"]
        profil["arbeitsstil"]["staerken"] = ["Analytisches Denken"]
        profil["arbeitsstil"]["teamrolle"] = "Umsetzer"

        result = profil_fuer_prompt(profil)
        assert result is not None
        assert "Aktiv auf Jobsuche" in result
        assert "Gehalt" in result
        assert "Remote" in result
        assert "Umsetzer" in result

    def test_profil_fuer_prompt_salary(self):
        """Salary is included in prompt text."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv"
        profil["arbeitsstil"]["typ"] = "x"
        profil["arbeitsstil"]["arbeitsmodell"] = "Remote"
        profil["gehaltsvorstellung"]["wunsch"] = 65000

        result = profil_fuer_prompt(profil)
        assert result is not None
        assert "65000" in result


class TestSeeleService:
    """Tests for seele_service module (orchestration)."""

    def test_get_or_create_profil_creates(self, app, test_user):
        """Creates profile if none exists."""
        result = seele_service.get_or_create_profil(test_user["id"])
        assert result["user_id"] == test_user["id"]
        assert "profil" in result
        assert result["vollstaendigkeit"] == 0

    def test_get_or_create_profil_returns_existing(self, app, test_user):
        """Returns existing profile without creating duplicate."""
        r1 = seele_service.get_or_create_profil(test_user["id"])
        r2 = seele_service.get_or_create_profil(test_user["id"])
        assert r1["id"] == r2["id"]

    def test_update_profil(self, app, test_user):
        """Manual profile update merges sections."""
        seele_service.get_or_create_profil(test_user["id"])
        result = seele_service.update_profil(
            test_user["id"],
            {"motivation": {"aktuelle_situation": "Karrierewechsel"}},
        )
        assert result["profil"]["motivation"]["aktuelle_situation"] == "Karrierewechsel"

    def test_update_profil_ignores_meta(self, app, test_user):
        """Meta section cannot be updated via manual update."""
        seele_service.get_or_create_profil(test_user["id"])
        seele_service.update_profil(
            test_user["id"],
            {"meta": {"quellen": {"hacked": True}}},
        )
        profile = SeeleProfile.query.filter_by(user_id=test_user["id"]).first()
        profil = profile.get_profil()
        assert profil.get("meta", {}).get("quellen", {}).get("hacked") is None

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_starte_session_profil(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Start profil session returns questions."""
        result = seele_service.starte_session(test_user["id"], "profil")
        assert result["session"]["session_typ"] == "profil"
        assert result["session"]["status"] == "aktiv"
        assert len(result["fragen"]) > 0
        assert result["session"]["fragen_geplant"] == len(result["fragen"])

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_starte_session_caches_fragen(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Started session caches generated questions in kontext_json."""
        result = seele_service.starte_session(test_user["id"], "profil")
        session = SeeleSession.query.get(result["session"]["id"])
        kontext = json.loads(session.kontext_json)
        assert "generierte_fragen" in kontext
        assert len(kontext["generierte_fragen"]) == len(MOCK_PROFIL_FRAGEN)

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_starte_session_duplicate_blocked(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Cannot start session while one is active."""
        seele_service.starte_session(test_user["id"], "profil")
        with pytest.raises(ValueError, match="aktive Session"):
            seele_service.starte_session(test_user["id"], "profil")

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_beantworte_frage(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Answer a question, profile gets updated."""
        result = seele_service.starte_session(test_user["id"], "profil")
        session_id = result["session"]["id"]
        frage_key = result["fragen"][0]["key"]

        answer_result = seele_service.beantworte_frage(test_user["id"], session_id, frage_key, "Aktiv auf Jobsuche")
        assert answer_result["session"]["fragen_beantwortet"] == 1
        assert answer_result["profil"] is not None

        # Verify answer saved
        antwort = SeeleAntwort.query.filter_by(session_id=session_id, frage_key=frage_key).first()
        assert antwort is not None
        assert antwort.uebersprungen is False

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_beantworte_frage_invalid_session(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Answering for non-existent session raises ValueError."""
        with pytest.raises(ValueError, match="nicht gefunden"):
            seele_service.beantworte_frage(test_user["id"], 9999, "key", "val")

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_ueberspringe_frage(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Skip a question, counter increments."""
        result = seele_service.starte_session(test_user["id"], "profil")
        session_id = result["session"]["id"]
        frage_key = result["fragen"][0]["key"]

        skip_result = seele_service.ueberspringe_frage(test_user["id"], session_id, frage_key)
        assert skip_result["session"]["fragen_uebersprungen"] == 1

        # Verify skip record saved
        antwort = SeeleAntwort.query.filter_by(session_id=session_id, frage_key=frage_key).first()
        assert antwort is not None
        assert antwort.uebersprungen is True

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_beende_session(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """End session early sets status to abgebrochen."""
        result = seele_service.starte_session(test_user["id"], "profil")
        session_id = result["session"]["id"]

        ended = seele_service.beende_session(test_user["id"], session_id)
        assert ended["status"] == "abgebrochen"
        assert ended["beendet_am"] is not None

    def test_beende_session_invalid(self, app, test_user):
        """Ending non-existent session raises ValueError."""
        with pytest.raises(ValueError, match="nicht gefunden"):
            seele_service.beende_session(test_user["id"], 9999)

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_get_aktuelle_session(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Get active session with questions from cache."""
        seele_service.starte_session(test_user["id"], "profil")
        result = seele_service.get_aktuelle_session(test_user["id"])
        assert result is not None
        assert result["session"]["status"] == "aktiv"
        assert len(result["fragen"]) > 0

    def test_get_aktuelle_session_none(self, app, test_user):
        """No active session returns None."""
        result = seele_service.get_aktuelle_session(test_user["id"])
        assert result is None

    def test_get_profil_fuer_generation_none(self, app, test_user):
        """No profile returns None."""
        result = seele_service.get_profil_fuer_generation(test_user["id"])
        assert result is None

    def test_get_profil_fuer_generation_with_data(self, app, test_user):
        """Profile with sufficient data returns text."""
        seele_service.get_or_create_profil(test_user["id"])
        seele_service.update_profil(
            test_user["id"],
            {
                "motivation": {
                    "aktuelle_situation": "Aktiv auf Jobsuche",
                    "wichtig_im_job": ["Gehalt", "Teamkultur"],
                },
                "arbeitsstil": {
                    "arbeitsmodell": "Remote",
                    "staerken": ["Analytisches Denken"],
                    "teamrolle": "Umsetzer",
                },
            },
        )

        result = seele_service.get_profil_fuer_generation(test_user["id"])
        assert result is not None
        assert "Aktiv auf Jobsuche" in result

    def test_soll_session_starten_no_profile(self, app, test_user):
        """No profile -> recommend profil session."""
        result = seele_service.soll_session_starten(test_user["id"], "dashboard")
        assert result["soll_starten"] is True
        assert result["session_typ"] == "profil"

    def test_soll_session_starten_low_completeness(self, app, test_user):
        """Low completeness on dashboard -> recommend profil session."""
        seele_service.get_or_create_profil(test_user["id"])
        result = seele_service.soll_session_starten(test_user["id"], "dashboard")
        assert result["soll_starten"] is True
        assert result["session_typ"] == "profil"

    def test_soll_session_starten_sufficient(self, app, test_user):
        """Sufficient completeness -> no session recommended."""
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json="{}",
            vollstaendigkeit=80,
        )
        db.session.add(profile)
        db.session.commit()

        result = seele_service.soll_session_starten(test_user["id"], "dashboard")
        assert result["soll_starten"] is False

    def test_soll_session_starten_pre_bewerbung_threshold(self, app, test_user):
        """Pre_bewerbung trigger with 55% completeness -> recommend session."""
        profile = SeeleProfile(
            user_id=test_user["id"],
            profil_json="{}",
            vollstaendigkeit=55,
        )
        db.session.add(profile)
        db.session.commit()

        result = seele_service.soll_session_starten(test_user["id"], "pre_bewerbung")
        assert result["soll_starten"] is True
        assert result["session_typ"] == "profil"

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_soll_session_starten_active_session(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Active session exists -> returns that session."""
        seele_service.starte_session(test_user["id"], "profil")
        result = seele_service.soll_session_starten(test_user["id"], "dashboard")
        assert result["soll_starten"] is True
        assert result["session_id"] is not None

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_full_session_lifecycle(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """Full lifecycle: start -> answer all -> auto-close."""
        result = seele_service.starte_session(test_user["id"], "profil")
        session_id = result["session"]["id"]
        fragen = result["fragen"]

        for frage in fragen:
            seele_service.beantworte_frage(
                test_user["id"],
                session_id,
                frage["key"],
                frage["optionen"][0] if frage.get("optionen") else "test",
            )

        session = SeeleSession.query.get(session_id)
        assert session.status == "abgeschlossen"
        assert session.beendet_am is not None

        profile = SeeleProfile.query.filter_by(user_id=test_user["id"]).first()
        assert profile is not None
        assert profile.vollstaendigkeit > 0

    @patch("services.seele_service.auto_extrahiere_cv_felder", side_effect=lambda uid, cv, p, pr: (p, pr))
    @patch("services.seele_service.generiere_micro_frage", return_value=None)
    @patch("services.seele_service.generiere_fragen", return_value=MOCK_PROFIL_FRAGEN)
    def test_get_aktuelle_session_reads_from_cache(self, mock_gen, mock_micro, mock_auto, app, test_user):
        """get_aktuelle_session reads questions from cache, not regenerating."""
        seele_service.starte_session(test_user["id"], "profil")
        mock_gen.reset_mock()

        result = seele_service.get_aktuelle_session(test_user["id"])
        assert result is not None
        assert len(result["fragen"]) > 0
        mock_gen.assert_not_called()


class TestAutoExtraktion:
    """Tests for CV auto-extraction feature."""

    @patch("services.seele_cv_extraktor.AIClient")
    def test_auto_extraktion_fills_empty_fields(self, mock_client_cls, app, test_user):
        """Auto-extraction fills empty auto-extractable fields."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {
            "persoenliche_daten.name": "Max Mustermann",
            "berufserfahrung.aktuelle_position": "Software Engineer",
            "berufserfahrung.branche": "IT",
        }

        seele_service.get_or_create_profil(test_user["id"])
        profile = SeeleProfile.query.filter_by(user_id=test_user["id"]).first()
        profil_data = profile.get_profil()

        updated_profil, updated_profile = seele_cv_extraktor.auto_extrahiere_cv_felder(
            test_user["id"], "Max Mustermann, Software Engineer bei TechCorp", profil_data, profile
        )

        assert updated_profil["persoenliche_daten"]["name"] == "Max Mustermann"
        assert updated_profil["berufserfahrung"]["aktuelle_position"] == "Software Engineer"
        assert updated_profil["berufserfahrung"]["branche"] == "IT"

    @patch("services.seele_cv_extraktor.AIClient")
    def test_auto_extraktion_skips_filled_fields(self, mock_client_cls, app, test_user):
        """Auto-extraction does not overwrite existing values."""
        seele_service.get_or_create_profil(test_user["id"])
        seele_service.update_profil(
            test_user["id"],
            {"persoenliche_daten": {"name": "Existing Name"}},
        )

        profile = SeeleProfile.query.filter_by(user_id=test_user["id"]).first()
        profil_data = profile.get_profil()

        # The AI call won't include persoenliche_daten.name since it's already filled
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {
            "berufserfahrung.aktuelle_position": "Developer",
        }

        updated_profil, _ = seele_cv_extraktor.auto_extrahiere_cv_felder(
            test_user["id"], "Test CV", profil_data, profile
        )

        # Existing value preserved
        assert updated_profil["persoenliche_daten"]["name"] == "Existing Name"

    @patch("services.seele_cv_extraktor.AIClient")
    def test_auto_extraktion_handles_error(self, mock_client_cls, app, test_user):
        """Auto-extraction failure returns original data unchanged."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.side_effect = Exception("API error")

        seele_service.get_or_create_profil(test_user["id"])
        profile = SeeleProfile.query.filter_by(user_id=test_user["id"]).first()
        profil_data = profile.get_profil()

        updated_profil, updated_profile = seele_cv_extraktor.auto_extrahiere_cv_felder(
            test_user["id"], "Test CV", profil_data, profile
        )

        # Should return original data unchanged
        assert updated_profil == profil_data
