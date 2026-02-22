"""Tests for seele_fragen module - FALLBACK_FRAGEN, get_naechste_fragen, generiere_fragen."""

from unittest.mock import patch

from services.seele_fragen import FALLBACK_FRAGEN, generiere_fragen, get_naechste_fragen
from services.seele_profile_builder import erstelle_leeres_profil

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


class TestFallbackFragen:
    """Tests for FALLBACK_FRAGEN structure and get_naechste_fragen."""

    def test_onboarding_fragen_exist(self):
        """Onboarding has 4 fallback questions."""
        assert len(FALLBACK_FRAGEN["onboarding"]) == 4

    def test_pre_bewerbung_fragen_exist(self):
        """Pre-bewerbung has 3 fallback questions."""
        assert len(FALLBACK_FRAGEN["pre_bewerbung"]) == 3

    def test_micro_empty(self):
        """Micro catalog is empty (AI-generated)."""
        assert FALLBACK_FRAGEN["micro"] == []

    def test_frage_structure(self):
        """Each question has required fields."""
        for _typ, fragen in FALLBACK_FRAGEN.items():
            for frage in fragen:
                assert "key" in frage
                assert "frage" in frage
                assert "typ" in frage
                assert "." in frage["key"], f"Key must be dot-separated: {frage['key']}"

    def test_get_naechste_fragen_all_open(self):
        """All questions returned when profile is empty."""
        fragen = get_naechste_fragen(FALLBACK_FRAGEN["onboarding"], {})
        assert len(fragen) == 4

    def test_get_naechste_fragen_max_limit(self):
        """Respects max_fragen limit."""
        fragen = get_naechste_fragen(FALLBACK_FRAGEN["onboarding"], {}, max_fragen=2)
        assert len(fragen) == 2

    def test_get_naechste_fragen_filters_answered(self):
        """Already-answered questions are excluded."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv auf Jobsuche"

        fragen = get_naechste_fragen(FALLBACK_FRAGEN["onboarding"], profil)
        keys = [f["key"] for f in fragen]
        assert "motivation.aktuelle_situation" not in keys

    def test_get_naechste_fragen_empty_list(self):
        """Empty question list returns empty."""
        fragen = get_naechste_fragen([], {})
        assert fragen == []


class TestGeneriereFragen:
    """Tests for AI-based question generation."""

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_calls_ai(self, mock_client_cls):
        """generiere_fragen sends CV text in prompt to AI."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_ONBOARDING_FRAGEN}

        result = generiere_fragen(
            "onboarding",
            cv_text="Erfahrener Data Scientist mit 5 Jahren Python",
            skills=["Python", "Machine Learning"],
        )

        assert len(result) == 4
        mock_instance._call_api_json_with_retry.assert_called_once()
        call_args = mock_instance._call_api_json_with_retry.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "Data Scientist" in prompt
        assert "Python" in prompt

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_includes_zeugnis(self, mock_client_cls):
        """Zeugnis text is included in prompt when provided."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_ONBOARDING_FRAGEN}

        generiere_fragen(
            "onboarding",
            cv_text="Test CV",
            zeugnis_text="Herr Mustermann hat stets zur vollen Zufriedenheit gearbeitet",
        )

        call_args = mock_instance._call_api_json_with_retry.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "ARBEITSZEUGNIS" in prompt
        assert "vollen Zufriedenheit" in prompt

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_fallback_on_error(self, mock_client_cls):
        """AI failure returns fallback questions."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.side_effect = Exception("API error")

        result = generiere_fragen("onboarding", cv_text="Test CV")

        assert len(result) == len(FALLBACK_FRAGEN["onboarding"])

    def test_generiere_fragen_no_cv_returns_fallback(self):
        """Without CV text, fallback questions are returned."""
        result = generiere_fragen("onboarding")
        assert len(result) == len(FALLBACK_FRAGEN["onboarding"])

    def test_generiere_fragen_micro_returns_empty(self):
        """Micro session type returns empty list."""
        result = generiere_fragen("micro")
        assert result == []

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_validates_keys(self, mock_client_cls):
        """Invalid keys from AI are filtered out."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {
            "fragen": [
                {"key": "invalid.key", "frage": "Test?", "typ": "chips", "optionen": ["A"], "mehrfach": False},
                {
                    "key": "motivation.aktuelle_situation",
                    "frage": "Valid?",
                    "typ": "chips",
                    "optionen": ["A", "B"],
                    "mehrfach": False,
                },
            ]
        }

        result = generiere_fragen("onboarding", cv_text="Test CV")

        assert len(result) == 1
        assert result[0]["key"] == "motivation.aktuelle_situation"

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_includes_already_answered(self, mock_client_cls):
        """Already-answered profile fields are included in prompt."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_ONBOARDING_FRAGEN}

        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv auf Jobsuche"

        generiere_fragen("onboarding", cv_text="Test CV", profil=profil)

        call_args = mock_instance._call_api_json_with_retry.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "BEREITS BEKANNT" in prompt
        assert "Aktiv auf Jobsuche" in prompt
