"""Tests for branchenspezifische Prompt-Regeln."""

from unittest.mock import MagicMock, patch

import pytest

from services.industry_rules import (
    INDUSTRY_RULES,
    VALID_BRANCHES,
    VALID_SIZES,
    get_industry_prompt_block,
)
from services.prompts import build_anschreiben_system_prompt


class TestIndustryRulesData:
    """Verify INDUSTRY_RULES dict structure and completeness."""

    def test_all_branches_have_required_keys(self):
        """Each branch must have label, base_rules, and size_rules."""
        for branch_key, rules in INDUSTRY_RULES.items():
            assert "label" in rules, f"{branch_key} missing 'label'"
            assert "base_rules" in rules, f"{branch_key} missing 'base_rules'"
            assert "size_rules" in rules, f"{branch_key} missing 'size_rules'"

    def test_base_rules_have_required_keys(self):
        """Each base_rules must have tone, hook, body, avoid."""
        for branch_key, rules in INDUSTRY_RULES.items():
            base = rules["base_rules"]
            for key in ("tone", "hook", "body", "avoid"):
                assert key in base, f"{branch_key}.base_rules missing '{key}'"
                assert len(base[key]) > 10, f"{branch_key}.base_rules.{key} too short"

    def test_size_rules_have_kmu_and_konzern(self):
        """Each branch must have both kmu and konzern size rules."""
        for branch_key, rules in INDUSTRY_RULES.items():
            size = rules["size_rules"]
            assert "kmu" in size, f"{branch_key}.size_rules missing 'kmu'"
            assert "konzern" in size, f"{branch_key}.size_rules missing 'konzern'"

    def test_valid_branches_matches_dict_keys(self):
        assert VALID_BRANCHES == set(INDUSTRY_RULES.keys())

    def test_valid_sizes(self):
        assert VALID_SIZES == {"kmu", "konzern"}

    def test_five_branches_defined(self):
        assert len(INDUSTRY_RULES) == 5

    def test_gesundheit_has_mandatory_fields(self):
        assert "mandatory_fields" in INDUSTRY_RULES["gesundheit"]
        assert "Schichtbereitschaft" in INDUSTRY_RULES["gesundheit"]["mandatory_fields"]


class TestGetIndustryPromptBlock:
    """Tests for the get_industry_prompt_block() function."""

    def test_returns_empty_for_none(self):
        assert get_industry_prompt_block(None) == ""

    def test_returns_empty_for_unknown_branch(self):
        assert get_industry_prompt_block("andere") == ""
        assert get_industry_prompt_block("unbekannt") == ""
        assert get_industry_prompt_block("xyz") == ""

    def test_returns_empty_for_empty_string(self):
        assert get_industry_prompt_block("") == ""

    @pytest.mark.parametrize("branche", list(INDUSTRY_RULES.keys()))
    def test_each_branch_produces_content(self, branche):
        """Every known branch must produce a non-trivial prompt block."""
        result = get_industry_prompt_block(branche)
        assert len(result) > 100
        assert "## INDUSTRY RULES" in result
        assert INDUSTRY_RULES[branche]["label"] in result

    @pytest.mark.parametrize("branche", list(INDUSTRY_RULES.keys()))
    def test_each_branch_has_tone_and_hook(self, branche):
        result = get_industry_prompt_block(branche)
        assert "TONE:" in result
        assert "HOOK:" in result
        assert "BODY STRATEGY:" in result
        assert "AVOID:" in result

    def test_kmu_rules_injected(self):
        result = get_industry_prompt_block("it_software", "kmu")
        assert "COMPANY SIZE:" in result
        assert "Hands-on" in result

    def test_konzern_rules_injected(self):
        result = get_industry_prompt_block("it_software", "konzern")
        assert "COMPANY SIZE:" in result
        assert "Skalierbarkeit" in result

    def test_no_size_rules_for_none(self):
        result = get_industry_prompt_block("it_software", None)
        assert "COMPANY SIZE:" not in result

    def test_no_size_rules_for_unknown(self):
        result = get_industry_prompt_block("it_software", "unbekannt")
        assert "COMPANY SIZE:" not in result

    def test_gesundheit_mandatory_fields_included(self):
        result = get_industry_prompt_block("gesundheit")
        assert "MANDATORISCH" in result
        assert "Schichtbereitschaft" in result

    def test_it_no_mandatory_fields(self):
        """IT branch should NOT have mandatory fields section."""
        result = get_industry_prompt_block("it_software")
        assert "MANDATORISCH" not in result

    def test_consulting_spot_framework(self):
        result = get_industry_prompt_block("consulting")
        assert "SPOT" in result

    def test_maschinenbau_industrie_40(self):
        result = get_industry_prompt_block("maschinenbau")
        assert "Industrie 4.0" in result

    def test_marketing_storytelling(self):
        result = get_industry_prompt_block("marketing")
        assert "story" in result.lower()


class TestPromptIntegration:
    """Test that industry rules integrate correctly with the system prompt."""

    PROMPT_DEFAULTS = {
        "cv_text": "Test CV",
        "position": "Developer",
        "quelle": "LinkedIn",
        "ansprechpartner": "Sehr geehrte Damen und Herren",
    }

    def test_industry_block_in_system_prompt(self):
        result = build_anschreiben_system_prompt(
            **self.PROMPT_DEFAULTS,
            branche="it_software",
            unternehmensgroesse="kmu",
        )
        assert "## INDUSTRY RULES" in result
        assert "IT / Software-Entwicklung" in result
        assert "Hands-on" in result

    def test_no_industry_block_when_none(self):
        result = build_anschreiben_system_prompt(
            **self.PROMPT_DEFAULTS,
            branche=None,
        )
        assert "## INDUSTRY RULES" not in result

    def test_no_industry_block_for_andere(self):
        result = build_anschreiben_system_prompt(
            **self.PROMPT_DEFAULTS,
            branche="andere",
        )
        assert "## INDUSTRY RULES" not in result

    def test_industry_block_between_tone_and_context(self):
        """Industry rules must appear between ## VOICE & TONE and ## CONTEXT."""
        result = build_anschreiben_system_prompt(
            **self.PROMPT_DEFAULTS,
            branche="consulting",
        )
        tone_pos = result.index("## VOICE & TONE")
        industry_pos = result.index("## INDUSTRY RULES")
        context_pos = result.index("## CONTEXT")
        assert tone_pos < industry_pos < context_pos


MOCK_ANSCHREIBEN = "Sehr geehrte Damen und Herren,\n\nText.\n\nMit freundlichen Grüßen\nMax"


def _make_mock_ai_client(mock_openai_cls):
    """Create an AIClient with a mocked OpenAI backend returning a fixed Anschreiben."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = MOCK_ANSCHREIBEN
    mock_client.chat.completions.create.return_value = mock_response

    from services.ai_client import AIClient

    return AIClient(api_key="test-key"), mock_client


class TestIndustryRulesInGeneration:
    """Tests for industry rules integration in AIClient."""

    GENERATE_DEFAULTS = {
        "cv_text": "CV text",
        "stellenanzeige_text": "Job text",
        "firma_name": "Firma",
        "position": "Developer",
        "ansprechpartner": "Sehr geehrte Damen und Herren",
    }

    def _get_system_message(self, mock_client):
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        return messages[0]["content"]

    @patch("services.ai_client.OpenAI")
    def test_industry_rules_in_system_prompt_when_branche_set(self, mock_openai_cls, app):
        """When details contain branche, INDUSTRY RULES should appear in system prompt."""
        client, mock_backend = _make_mock_ai_client(mock_openai_cls)
        client.generate_anschreiben(
            **self.GENERATE_DEFAULTS,
            details={"branche": "it_software", "unternehmensgroesse": "kmu"},
        )

        system_msg = self._get_system_message(mock_backend)
        assert "## INDUSTRY RULES" in system_msg
        assert "IT / Software-Entwicklung" in system_msg
        assert "Hands-on" in system_msg

    @patch("services.ai_client.OpenAI")
    def test_no_industry_rules_when_branche_none(self, mock_openai_cls, app):
        """When details have no branche, no INDUSTRY RULES block should appear."""
        client, mock_backend = _make_mock_ai_client(mock_openai_cls)
        client.generate_anschreiben(
            **self.GENERATE_DEFAULTS,
            details={"branche": None, "unternehmensgroesse": None},
        )

        system_msg = self._get_system_message(mock_backend)
        assert "## INDUSTRY RULES" not in system_msg

    @patch("services.ai_client.OpenAI")
    def test_no_industry_rules_without_details(self, mock_openai_cls, app):
        """When no details dict is passed, no INDUSTRY RULES block should appear."""
        client, mock_backend = _make_mock_ai_client(mock_openai_cls)
        client.generate_anschreiben(**self.GENERATE_DEFAULTS)

        system_msg = self._get_system_message(mock_backend)
        assert "## INDUSTRY RULES" not in system_msg


class TestExtractBrancheNormalization:
    """Tests for branche/unternehmensgroesse normalization in extract_bewerbung_details."""

    @patch("services.ai_client.OpenAI")
    def test_normalize_branche_from_extraction(self, mock_openai_cls, app):
        """Extracted branche should be normalized into details dict."""
        client, _ = _make_mock_ai_client(mock_openai_cls)
        result = client._normalize_extracted_details(
            {
                "ansprechpartner": "Sehr geehrte Frau Schmidt",
                "position": "Developer",
                "quelle": "LinkedIn",
                "email": "test@test.de",
                "zusammenfassung": "IT company",
                "branche": "it_software",
                "unternehmensgroesse": "kmu",
            },
            "Test GmbH",
        )
        assert result["branche"] == "it_software"
        assert result["unternehmensgroesse"] == "kmu"

    @patch("services.ai_client.OpenAI")
    def test_normalize_andere_branche_to_none(self, mock_openai_cls, app):
        """branche='andere' should be normalized to None."""
        client, _ = _make_mock_ai_client(mock_openai_cls)
        result = client._normalize_extracted_details(
            {
                "branche": "andere",
                "unternehmensgroesse": "unbekannt",
            },
            "Test GmbH",
        )
        assert result["branche"] is None
        assert result["unternehmensgroesse"] is None

    @patch("services.ai_client.OpenAI")
    def test_normalize_missing_branche(self, mock_openai_cls, app):
        """Missing branche in API response should default to None."""
        client, _ = _make_mock_ai_client(mock_openai_cls)
        result = client._normalize_extracted_details({}, "Test GmbH")
        assert result["branche"] is None
        assert result["unternehmensgroesse"] is None
