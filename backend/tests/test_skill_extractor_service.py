"""Tests for services/skill_extractor.py - SkillExtractor service."""

from unittest.mock import MagicMock, patch

import pytest


class TestSkillExtractorInit:
    """Tests for SkillExtractor initialization."""

    @patch("services.skill_extractor.Anthropic")
    def test_init_with_explicit_key(self, mock_anthropic, app):
        """Test initialization with an explicit API key."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key-123")

        assert extractor.api_key == "test-key-123"
        mock_anthropic.assert_called_once_with(api_key="test-key-123")

    @patch("services.skill_extractor.Anthropic")
    def test_init_uses_config_key(self, mock_anthropic, app):
        """Test that init falls back to config ANTHROPIC_API_KEY."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()

        # conftest sets ANTHROPIC_API_KEY to "test-api-key"
        assert extractor.api_key == "test-api-key"

    def test_init_raises_without_key(self, app):
        """Test that ValueError is raised when no API key is available."""
        with patch("services.skill_extractor.config") as mock_config:
            mock_config.ANTHROPIC_API_KEY = None
            mock_config.CLAUDE_MODEL = "claude-3-5-haiku-20241022"

            from services.skill_extractor import SkillExtractor

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY nicht gesetzt"):
                SkillExtractor(api_key=None)


class TestExtractSkillsFromCV:
    """Tests for SkillExtractor.extract_skills_from_cv()."""

    @patch("services.skill_extractor.Anthropic")
    def test_successful_extraction(self, mock_anthropic_cls, app):
        """Test successful skill extraction from CV text."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """[
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
            {"skill_name": "Englisch", "skill_category": "languages", "experience_years": null},
            {"skill_name": "Git", "skill_category": "tools", "experience_years": 3}
        ]"""
        mock_client.messages.create.return_value = mock_response

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        result = extractor.extract_skills_from_cv("Max Mustermann, 5 Jahre Python Erfahrung")

        assert len(result) == 3
        assert result[0]["skill_name"] == "Python"
        assert result[0]["skill_category"] == "technical"
        assert result[0]["experience_years"] == 5.0
        assert result[1]["skill_name"] == "Englisch"
        assert result[1]["experience_years"] is None
        mock_client.messages.create.assert_called_once()

    @patch("services.skill_extractor.Anthropic")
    def test_retries_on_failure(self, mock_anthropic_cls, app):
        """Test that extraction retries on API errors."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[
            0
        ].text = '[{"skill_name": "Python", "skill_category": "technical", "experience_years": null}]'

        # Fail first, succeed second
        mock_client.messages.create.side_effect = [
            Exception("API error"),
            mock_response,
        ]

        from services.skill_extractor import SkillExtractor

        with patch("services.skill_extractor.time.sleep"):
            extractor = SkillExtractor(api_key="test-key")
            result = extractor.extract_skills_from_cv("CV text", retry_count=3)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"
        assert mock_client.messages.create.call_count == 2

    @patch("services.skill_extractor.Anthropic")
    def test_returns_empty_after_all_retries_fail(self, mock_anthropic_cls, app):
        """Test that empty list is returned after all retries are exhausted."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API down")

        from services.skill_extractor import SkillExtractor

        with patch("services.skill_extractor.time.sleep"):
            extractor = SkillExtractor(api_key="test-key")
            result = extractor.extract_skills_from_cv("CV text", retry_count=2)

        assert result == []
        assert mock_client.messages.create.call_count == 2

    @patch("services.skill_extractor.Anthropic")
    def test_custom_retry_count(self, mock_anthropic_cls, app):
        """Test extraction with custom retry count."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("fail")

        from services.skill_extractor import SkillExtractor

        with patch("services.skill_extractor.time.sleep"):
            extractor = SkillExtractor(api_key="test-key")
            result = extractor.extract_skills_from_cv("CV", retry_count=5)

        assert result == []
        assert mock_client.messages.create.call_count == 5


class TestCreateExtractionPrompt:
    """Tests for SkillExtractor._create_extraction_prompt()."""

    @patch("services.skill_extractor.Anthropic")
    def test_prompt_contains_cv_text(self, mock_anthropic_cls, app):
        """Test that the prompt includes the CV text."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        prompt = extractor._create_extraction_prompt("Mein Lebenslauf mit Python und Java")

        assert "Mein Lebenslauf mit Python und Java" in prompt
        assert "LEBENSLAUF:" in prompt

    @patch("services.skill_extractor.Anthropic")
    def test_prompt_truncates_long_text(self, mock_anthropic_cls, app):
        """Test that CV text is truncated to 4000 chars."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        long_text = "A" * 5000
        prompt = extractor._create_extraction_prompt(long_text)

        # The prompt should contain at most 4000 A's from the CV text
        assert "A" * 4000 in prompt
        assert "A" * 5000 not in prompt

    @patch("services.skill_extractor.Anthropic")
    def test_prompt_contains_categories(self, mock_anthropic_cls, app):
        """Test that the prompt lists all valid categories."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        prompt = extractor._create_extraction_prompt("CV text")

        assert "technical" in prompt
        assert "soft_skills" in prompt
        assert "languages" in prompt
        assert "tools" in prompt
        assert "certifications" in prompt

    @patch("services.skill_extractor.Anthropic")
    def test_prompt_requests_json(self, mock_anthropic_cls, app):
        """Test that the prompt explicitly requests JSON output."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        prompt = extractor._create_extraction_prompt("CV text")

        assert "JSON" in prompt


class TestParseSkillsResponse:
    """Tests for SkillExtractor._parse_skills_response()."""

    @patch("services.skill_extractor.Anthropic")
    def test_parses_valid_json(self, mock_anthropic_cls, app):
        """Test parsing a valid JSON response."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "Python", "skill_category": "technical", "experience_years": 5}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"
        assert result[0]["skill_category"] == "technical"
        assert result[0]["experience_years"] == 5.0

    @patch("services.skill_extractor.Anthropic")
    def test_parses_json_with_surrounding_text(self, mock_anthropic_cls, app):
        """Test that JSON is extracted even when surrounded by text."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = 'Here are the skills:\n[{"skill_name": "Java", "skill_category": "technical", "experience_years": null}]\nDone.'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Java"

    @patch("services.skill_extractor.Anthropic")
    def test_returns_empty_for_no_json(self, mock_anthropic_cls, app):
        """Test that empty list is returned when no JSON array is found."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        result = extractor._parse_skills_response("No JSON here, just text.")

        assert result == []

    @patch("services.skill_extractor.Anthropic")
    def test_returns_empty_for_invalid_json(self, mock_anthropic_cls, app):
        """Test that empty list is returned for malformed JSON."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        result = extractor._parse_skills_response("[{invalid json}]")

        assert result == []

    @patch("services.skill_extractor.Anthropic")
    def test_skips_entries_without_skill_name(self, mock_anthropic_cls, app):
        """Test that entries without a skill_name are skipped."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "", "skill_category": "technical", "experience_years": 3}, {"skill_name": "Python", "skill_category": "technical", "experience_years": 5}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"

    @patch("services.skill_extractor.Anthropic")
    def test_skips_non_dict_entries(self, mock_anthropic_cls, app):
        """Test that non-dict entries in the array are skipped."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '["invalid", {"skill_name": "Python", "skill_category": "technical", "experience_years": null}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"

    @patch("services.skill_extractor.Anthropic")
    def test_maps_alternative_categories(self, mock_anthropic_cls, app):
        """Test that alternative category names are mapped correctly."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = """[
            {"skill_name": "Python", "skill_category": "programming", "experience_years": null},
            {"skill_name": "Deutsch", "skill_category": "sprachen", "experience_years": null},
            {"skill_name": "Teamwork", "skill_category": "soft_skill", "experience_years": null},
            {"skill_name": "Docker", "skill_category": "tool", "experience_years": null},
            {"skill_name": "AWS", "skill_category": "zertifikat", "experience_years": null},
            {"skill_name": "Scrum", "skill_category": "programmierung", "experience_years": null}
        ]"""

        result = extractor._parse_skills_response(response)

        assert len(result) == 6
        assert result[0]["skill_category"] == "technical"  # programming -> technical
        assert result[1]["skill_category"] == "languages"  # sprachen -> languages
        assert result[2]["skill_category"] == "soft_skills"  # soft_skill -> soft_skills
        assert result[3]["skill_category"] == "tools"  # tool -> tools
        assert result[4]["skill_category"] == "certifications"  # zertifikat -> certifications
        assert result[5]["skill_category"] == "technical"  # programmierung -> technical

    @patch("services.skill_extractor.Anthropic")
    def test_unknown_category_defaults_to_technical(self, mock_anthropic_cls, app):
        """Test that completely unknown categories default to 'technical'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "Something", "skill_category": "unknown_category", "experience_years": null}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_category"] == "technical"

    @patch("services.skill_extractor.Anthropic")
    def test_validates_experience_years(self, mock_anthropic_cls, app):
        """Test validation of experience_years field."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = """[
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
            {"skill_name": "Java", "skill_category": "technical", "experience_years": 2.5},
            {"skill_name": "Go", "skill_category": "technical", "experience_years": -1},
            {"skill_name": "Rust", "skill_category": "technical", "experience_years": "invalid"},
            {"skill_name": "C++", "skill_category": "technical", "experience_years": null}
        ]"""

        result = extractor._parse_skills_response(response)

        assert len(result) == 5
        assert result[0]["experience_years"] == 5.0
        assert result[1]["experience_years"] == 2.5
        assert result[2]["experience_years"] is None  # negative -> None
        assert result[3]["experience_years"] is None  # invalid string -> None
        assert result[4]["experience_years"] is None  # null stays None

    @patch("services.skill_extractor.Anthropic")
    def test_strips_whitespace_from_names(self, mock_anthropic_cls, app):
        """Test that skill names and categories are stripped of whitespace."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "  Python  ", "skill_category": "  TECHNICAL  ", "experience_years": null}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"
        assert result[0]["skill_category"] == "technical"

    @patch("services.skill_extractor.Anthropic")
    def test_handles_multiple_json_arrays(self, mock_anthropic_cls, app):
        """Test parsing when response contains text before/after JSON."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = 'Hier sind die Skills:\n```json\n[{"skill_name": "React", "skill_category": "technical", "experience_years": 3}]\n```'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_name"] == "React"

    @patch("services.skill_extractor.Anthropic")
    def test_zertifikate_category_mapping(self, mock_anthropic_cls, app):
        """Test that 'zertifikate' (plural) maps to 'certifications'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "ISTQB", "skill_category": "zertifikate", "experience_years": null}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_category"] == "certifications"

    @patch("services.skill_extractor.Anthropic")
    def test_softskills_no_underscore_mapping(self, mock_anthropic_cls, app):
        """Test that 'softskills' (no underscore) maps to 'soft_skills'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "Leadership", "skill_category": "softskills", "experience_years": null}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_category"] == "soft_skills"

    @patch("services.skill_extractor.Anthropic")
    def test_language_singular_mapping(self, mock_anthropic_cls, app):
        """Test that 'language' (singular) maps to 'languages'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = '[{"skill_name": "English", "skill_category": "language", "experience_years": null}]'

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_category"] == "languages"

    @patch("services.skill_extractor.Anthropic")
    def test_certification_singular_mapping(self, mock_anthropic_cls, app):
        """Test that 'certification' (singular) maps to 'certifications'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        response = (
            '[{"skill_name": "AWS Solutions Architect", "skill_category": "certification", "experience_years": null}]'
        )

        result = extractor._parse_skills_response(response)

        assert len(result) == 1
        assert result[0]["skill_category"] == "certifications"

    @patch("services.skill_extractor.Anthropic")
    def test_empty_json_array(self, mock_anthropic_cls, app):
        """Test parsing an empty JSON array."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        result = extractor._parse_skills_response("[]")

        assert result == []

    @patch("services.skill_extractor.Anthropic")
    def test_valid_categories_accepted_directly(self, mock_anthropic_cls, app):
        """Test that all VALID_CATEGORIES are accepted without mapping."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")

        for category in SkillExtractor.VALID_CATEGORIES:
            response = f'[{{"skill_name": "Test", "skill_category": "{category}", "experience_years": null}}]'
            result = extractor._parse_skills_response(response)
            assert len(result) == 1
            assert result[0]["skill_category"] == category


class TestEndToEndExtraction:
    """Integration-style tests for full extraction flow."""

    @patch("services.skill_extractor.Anthropic")
    def test_realistic_cv_extraction(self, mock_anthropic_cls, app):
        """Test extraction with a realistic Claude response."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """[
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
            {"skill_name": "JavaScript", "skill_category": "technical", "experience_years": 3},
            {"skill_name": "React", "skill_category": "technical", "experience_years": 2},
            {"skill_name": "Docker", "skill_category": "tools", "experience_years": 3},
            {"skill_name": "Git", "skill_category": "tools", "experience_years": 5},
            {"skill_name": "Teamführung", "skill_category": "soft_skills", "experience_years": null},
            {"skill_name": "Deutsch", "skill_category": "languages", "experience_years": null},
            {"skill_name": "Englisch", "skill_category": "languages", "experience_years": null},
            {"skill_name": "AWS Certified Developer", "skill_category": "certifications", "experience_years": null}
        ]"""
        mock_client.messages.create.return_value = mock_response

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        result = extractor.extract_skills_from_cv(
            "Max Mustermann\n5 Jahre Erfahrung als Python-Entwickler\n"
            "JavaScript, React Frontend\nDocker, Git\nTeamführer\n"
            "Sprachen: Deutsch (Muttersprache), Englisch (fließend)\n"
            "Zertifikate: AWS Certified Developer"
        )

        assert len(result) == 9
        technical = [s for s in result if s["skill_category"] == "technical"]
        tools = [s for s in result if s["skill_category"] == "tools"]
        languages = [s for s in result if s["skill_category"] == "languages"]
        soft = [s for s in result if s["skill_category"] == "soft_skills"]
        certs = [s for s in result if s["skill_category"] == "certifications"]

        assert len(technical) == 3
        assert len(tools) == 2
        assert len(languages) == 2
        assert len(soft) == 1
        assert len(certs) == 1

    @patch("services.skill_extractor.Anthropic")
    def test_api_called_with_correct_params(self, mock_anthropic_cls, app):
        """Test that the Anthropic API is called with correct parameters."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "[]"
        mock_client.messages.create.return_value = mock_response

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor(api_key="test-key")
        extractor.extract_skills_from_cv("CV text content")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["temperature"] == 0.2
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"
        assert "CV text content" in call_kwargs["messages"][0]["content"]
