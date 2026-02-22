"""Tests for seele_fragen module - FALLBACK_FRAGEN, get_naechste_fragen, generiere_fragen, Lücken-Analyse."""

from unittest.mock import patch

from services.seele_fragen import (
    ALLE_PROFIL_KEYS,
    FALLBACK_FRAGEN,
    FELD_METADATA,
    _fallback_fuer_luecken,
    _finde_fragbare_luecken,
    _get_fallback_fragen,
    _ist_feld_leer,
    generiere_fragen,
    get_naechste_fragen,
)
from services.seele_profile_builder import LEERES_PROFIL, erstelle_leeres_profil

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


class TestFeldMetadata:
    """Tests for FELD_METADATA structure."""

    def test_all_profil_fields_covered(self):
        """Every non-meta field in LEERES_PROFIL has metadata."""
        for section_key, section_data in LEERES_PROFIL.items():
            if section_key == "meta":
                continue
            for field_key in section_data:
                full_key = f"{section_key}.{field_key}"
                assert full_key in FELD_METADATA, f"Missing metadata for {full_key}"

    def test_no_extra_metadata(self):
        """No metadata for keys that don't exist in LEERES_PROFIL."""
        for key in FELD_METADATA:
            section, field = key.split(".", 1)
            assert section in LEERES_PROFIL, f"Unknown section: {section}"
            assert field in LEERES_PROFIL[section], f"Unknown field: {key}"

    def test_metadata_has_required_fields(self):
        """Each metadata entry has all required fields."""
        for key, meta in FELD_METADATA.items():
            assert "beschreibung" in meta, f"{key} missing beschreibung"
            assert "auto_extract" in meta, f"{key} missing auto_extract"
            assert "prioritaet" in meta, f"{key} missing prioritaet"
            assert "typ_empfehlung" in meta, f"{key} missing typ_empfehlung"
            assert meta["prioritaet"] in ("hoch", "mittel", "niedrig")
            assert meta["typ_empfehlung"] in ("chips", "freitext", "chips_freitext", "slider")

    def test_auto_extract_fields_count(self):
        """There are 9 auto-extractable fields."""
        auto_fields = [k for k, v in FELD_METADATA.items() if v["auto_extract"]]
        assert len(auto_fields) == 9


class TestFallbackFragen:
    """Tests for FALLBACK_FRAGEN structure and get_naechste_fragen."""

    def test_profil_fallback_covers_all_non_auto_fields(self):
        """Profil fallback has questions for all non-auto-extractable fields."""
        assert len(FALLBACK_FRAGEN["profil"]) == 24

    def test_old_session_types_resolve(self):
        """Old session types (onboarding, pre_bewerbung) resolve to profil fallback."""
        onboarding = _get_fallback_fragen("onboarding")
        pre_bew = _get_fallback_fragen("pre_bewerbung")
        profil = _get_fallback_fragen("profil")
        assert len(onboarding) == len(profil)
        assert len(pre_bew) == len(profil)

    def test_micro_empty(self):
        """Micro catalog is empty (AI-generated)."""
        assert FALLBACK_FRAGEN["micro"] == []

    def test_frage_structure(self):
        """Each profil fallback question has required fields and valid keys."""
        for frage in FALLBACK_FRAGEN["profil"]:
            assert "key" in frage
            assert "frage" in frage
            assert "typ" in frage
            assert "." in frage["key"], f"Key must be dot-separated: {frage['key']}"
            assert frage["key"] in ALLE_PROFIL_KEYS, f"Key not in profil: {frage['key']}"

    def test_get_naechste_fragen_all_open(self):
        """All questions returned when profile is empty."""
        fragen = get_naechste_fragen(MOCK_PROFIL_FRAGEN, {})
        assert len(fragen) == 4

    def test_get_naechste_fragen_max_limit(self):
        """Respects max_fragen limit."""
        fragen = get_naechste_fragen(MOCK_PROFIL_FRAGEN, {}, max_fragen=2)
        assert len(fragen) == 2

    def test_get_naechste_fragen_filters_answered(self):
        """Already-answered questions are excluded via beantwortete_keys."""
        beantwortete = {"motivation.aktuelle_situation"}
        fragen = get_naechste_fragen(MOCK_PROFIL_FRAGEN, {}, beantwortete_keys=beantwortete)
        keys = [f["key"] for f in fragen]
        assert "motivation.aktuelle_situation" not in keys
        assert len(fragen) == 3

    def test_get_naechste_fragen_empty_list(self):
        """Empty question list returns empty."""
        fragen = get_naechste_fragen([], {})
        assert fragen == []


class TestLueckenAnalyse:
    """Tests for _finde_fragbare_luecken and related helpers."""

    def test_finde_luecken_leeres_profil(self):
        """Empty profile has all non-auto-extract fields as gaps."""
        profil = erstelle_leeres_profil()
        luecken = _finde_fragbare_luecken(profil)

        # All non-auto-extract fields should be gaps
        non_auto = {k for k, v in FELD_METADATA.items() if not v["auto_extract"]}
        assert set(luecken.keys()) == non_auto

    def test_finde_luecken_teilweise_ausgefuellt(self):
        """Filled non-auto fields are excluded from gaps."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv auf Jobsuche"
        profil["arbeitsstil"]["arbeitsmodell"] = "Remote"

        luecken = _finde_fragbare_luecken(profil)
        assert "motivation.aktuelle_situation" not in luecken
        assert "arbeitsstil.arbeitsmodell" not in luecken

    def test_finde_luecken_auto_extract_ignoriert(self):
        """Auto-extractable fields are never returned as gaps."""
        profil = erstelle_leeres_profil()
        luecken = _finde_fragbare_luecken(profil)

        auto_keys = {k for k, v in FELD_METADATA.items() if v["auto_extract"]}
        for key in auto_keys:
            assert key not in luecken

    def test_finde_luecken_none_profil(self):
        """None profile returns all non-auto-extract fields."""
        luecken = _finde_fragbare_luecken(None)
        non_auto = {k for k, v in FELD_METADATA.items() if not v["auto_extract"]}
        assert set(luecken.keys()) == non_auto

    def test_ist_feld_leer_none(self):
        """None value is considered empty."""
        profil = erstelle_leeres_profil()
        assert _ist_feld_leer(profil, "motivation.aktuelle_situation") is True

    def test_ist_feld_leer_leere_liste(self):
        """Empty list is considered empty."""
        profil = erstelle_leeres_profil()
        assert _ist_feld_leer(profil, "motivation.wichtig_im_job") is True

    def test_ist_feld_leer_ausgefuellt(self):
        """Filled field is not empty."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv"
        assert _ist_feld_leer(profil, "motivation.aktuelle_situation") is False

    def test_fallback_fuer_luecken_filtert(self):
        """Fallback questions are filtered to only include gap fields."""
        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv"
        profil["arbeitsstil"]["arbeitsmodell"] = "Remote"
        profil["motivation"]["wechsel_tempo"] = "Sofort"

        luecken = _finde_fragbare_luecken(profil)
        fallback = _get_fallback_fragen("profil")
        gefiltert = _fallback_fuer_luecken(luecken, fallback)

        keys = {f["key"] for f in gefiltert}
        assert "motivation.aktuelle_situation" not in keys
        assert "arbeitsstil.arbeitsmodell" not in keys
        assert "motivation.wechsel_tempo" not in keys

    def test_fallback_fuer_luecken_max_5(self):
        """Fallback returns max 5 questions."""
        luecken = _finde_fragbare_luecken(None)  # all gaps
        fallback = _get_fallback_fragen("profil")
        gefiltert = _fallback_fuer_luecken(luecken, fallback)
        assert len(gefiltert) <= 5

    def test_fallback_fuer_luecken_leer(self):
        """Empty gaps dict returns empty list."""
        gefiltert = _fallback_fuer_luecken({}, _get_fallback_fragen("profil"))
        assert gefiltert == []


class TestGeneriereFragen:
    """Tests for AI-based question generation."""

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_calls_ai(self, mock_client_cls):
        """generiere_fragen sends CV text and gaps in prompt to AI."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_PROFIL_FRAGEN}

        result = generiere_fragen(
            "profil",
            cv_text="Erfahrener Data Scientist mit 5 Jahren Python",
            skills=["Python", "Machine Learning"],
        )

        assert len(result) == 4
        mock_instance._call_api_json_with_retry.assert_called_once()
        call_args = mock_instance._call_api_json_with_retry.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "Data Scientist" in prompt
        assert "Python" in prompt
        # New: prompt should contain gap descriptions
        assert "OFFENE FELDER" in prompt

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_includes_zeugnis(self, mock_client_cls):
        """Zeugnis text is included in prompt when provided."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_PROFIL_FRAGEN}

        generiere_fragen(
            "profil",
            cv_text="Test CV",
            zeugnis_text="Herr Mustermann hat stets zur vollen Zufriedenheit gearbeitet",
        )

        call_args = mock_instance._call_api_json_with_retry.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "ARBEITSZEUGNIS" in prompt
        assert "vollen Zufriedenheit" in prompt

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_fallback_on_error(self, mock_client_cls):
        """AI failure returns filtered fallback questions."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.side_effect = Exception("API error")

        result = generiere_fragen("profil", cv_text="Test CV")

        # Should return up to 5 fallback questions filtered to gaps
        assert len(result) <= 5
        assert len(result) > 0

    def test_generiere_fragen_no_cv_returns_filtered_fallback(self):
        """Without CV text, filtered fallback questions are returned."""
        result = generiere_fragen("profil")
        # Should return up to 5 fallback questions for gaps
        assert len(result) <= 5
        assert len(result) > 0

    def test_generiere_fragen_micro_returns_empty(self):
        """Micro session type returns empty list."""
        result = generiere_fragen("micro")
        assert result == []

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_validates_keys(self, mock_client_cls):
        """Invalid keys from AI are filtered out, valid profil keys pass."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {
            "fragen": [
                {"key": "totally.invalid_key", "frage": "Test?", "typ": "chips", "optionen": ["A"], "mehrfach": False},
                {
                    "key": "motivation.aktuelle_situation",
                    "frage": "Valid?",
                    "typ": "chips",
                    "optionen": ["A", "B"],
                    "mehrfach": False,
                },
            ]
        }

        result = generiere_fragen("profil", cv_text="Test CV")

        assert len(result) == 1
        assert result[0]["key"] == "motivation.aktuelle_situation"

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_accepts_any_profil_key(self, mock_client_cls):
        """AI can use any valid profil key, not just a hardcoded subset."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {
            "fragen": [
                {
                    "key": "persoenlichkeit.selbstbeschreibung",
                    "frage": "Wie beschreibst du dich?",
                    "typ": "freitext",
                    "optionen": None,
                    "mehrfach": False,
                },
                {
                    "key": "persoenliche_daten.verfuegbar_ab",
                    "frage": "Ab wann bist du da?",
                    "typ": "chips",
                    "optionen": ["Sofort", "In 1 Monat"],
                    "mehrfach": False,
                },
            ]
        }

        result = generiere_fragen("profil", cv_text="Test CV")
        assert len(result) == 2
        keys = {f["key"] for f in result}
        assert "persoenlichkeit.selbstbeschreibung" in keys
        assert "persoenliche_daten.verfuegbar_ab" in keys

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_includes_already_answered(self, mock_client_cls):
        """Already-answered profile fields are included in prompt."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_PROFIL_FRAGEN}

        profil = erstelle_leeres_profil()
        profil["motivation"]["aktuelle_situation"] = "Aktiv auf Jobsuche"

        generiere_fragen("profil", cv_text="Test CV", profil=profil)

        call_args = mock_instance._call_api_json_with_retry.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "BEREITS BEKANNT" in prompt
        assert "Aktiv auf Jobsuche" in prompt

    def test_generiere_fragen_no_gaps_returns_empty(self):
        """Fully filled profile returns empty (no gaps)."""
        profil = erstelle_leeres_profil()
        # Fill all non-auto-extract fields
        for key, meta in FELD_METADATA.items():
            if meta["auto_extract"]:
                continue
            section, field = key.split(".", 1)
            # Use appropriate value based on default type
            default = LEERES_PROFIL[section][field]
            profil[section][field] = ["value"] if isinstance(default, list) else "value"

        result = generiere_fragen("profil", cv_text="Test CV", profil=profil)
        assert result == []

    @patch("services.seele_fragen.AIClient")
    def test_generiere_fragen_max_tokens_1200(self, mock_client_cls):
        """AI call uses 1200 max_tokens (increased from old 800)."""
        mock_instance = mock_client_cls.return_value
        mock_instance._call_api_json_with_retry.return_value = {"fragen": MOCK_PROFIL_FRAGEN}

        generiere_fragen("profil", cv_text="Test CV")

        call_args = mock_instance._call_api_json_with_retry.call_args
        assert call_args[1]["max_tokens"] == 1200

    def test_generiere_fragen_backward_compat_onboarding(self):
        """Old session type 'onboarding' still works (resolves to profil logic)."""
        result = generiere_fragen("onboarding")
        # Should return fallback questions since no CV
        assert len(result) > 0
        assert len(result) <= 5
