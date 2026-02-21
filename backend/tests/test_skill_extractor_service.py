"""Tests for services/skill_extractor.py - SkillExtractor service."""

from unittest.mock import MagicMock, patch


class TestSkillExtractorInit:
    """Tests for SkillExtractor initialization."""

    @patch("services.skill_extractor.AIClient")
    def test_init_creates_ai_client(self, mock_ai_client_cls, app):
        """Test initialization creates an AIClient instance."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()

        mock_ai_client_cls.assert_called_once()
        assert extractor.client is mock_ai_client_cls.return_value


class TestExtractSkillsFromCV:
    """Tests for SkillExtractor.extract_skills_from_cv()."""

    @patch("services.skill_extractor.AIClient")
    def test_successful_extraction(self, mock_ai_client_cls, app):
        """Test successful skill extraction from CV text."""
        mock_client = MagicMock()
        mock_ai_client_cls.return_value = mock_client

        mock_client._call_api_json_with_retry.return_value = {
            "skills": [
                {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
                {"skill_name": "Englisch", "skill_category": "languages", "experience_years": None},
                {"skill_name": "Git", "skill_category": "tools", "experience_years": 3},
            ]
        }

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        result = extractor.extract_skills_from_cv("Max Mustermann, 5 Jahre Python Erfahrung")

        assert len(result) == 3
        assert result[0]["skill_name"] == "Python"
        assert result[0]["skill_category"] == "technical"
        assert result[0]["experience_years"] == 5.0
        assert result[1]["skill_name"] == "Englisch"
        assert result[1]["experience_years"] is None
        mock_client._call_api_json_with_retry.assert_called_once()

    @patch("services.skill_extractor.AIClient")
    def test_returns_empty_on_api_failure(self, mock_ai_client_cls, app):
        """Test that empty list is returned when API call fails."""
        mock_client = MagicMock()
        mock_ai_client_cls.return_value = mock_client
        mock_client._call_api_json_with_retry.side_effect = Exception("API down")

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        result = extractor.extract_skills_from_cv("CV text")

        assert result == []

    @patch("services.skill_extractor.AIClient")
    def test_returns_empty_when_no_skills_key(self, mock_ai_client_cls, app):
        """Test that empty list is returned when API returns no 'skills' key."""
        mock_client = MagicMock()
        mock_ai_client_cls.return_value = mock_client
        mock_client._call_api_json_with_retry.return_value = {"data": "no skills key"}

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        result = extractor.extract_skills_from_cv("CV text")

        assert result == []


class TestCreateExtractionPrompt:
    """Tests for SkillExtractor._create_extraction_prompt()."""

    @patch("services.skill_extractor.AIClient")
    def test_prompt_contains_cv_text(self, mock_ai_client_cls, app):
        """Test that the prompt includes the CV text."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        prompt = extractor._create_extraction_prompt("Mein Lebenslauf mit Python und Java")

        assert "Mein Lebenslauf mit Python und Java" in prompt
        assert "LEBENSLAUF:" in prompt

    @patch("services.skill_extractor.AIClient")
    def test_prompt_truncates_long_text(self, mock_ai_client_cls, app):
        """Test that CV text is truncated to 4000 chars."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        long_text = "A" * 5000
        prompt = extractor._create_extraction_prompt(long_text)

        # The prompt should contain at most 4000 A's from the CV text
        assert "A" * 4000 in prompt
        assert "A" * 5000 not in prompt

    @patch("services.skill_extractor.AIClient")
    def test_prompt_contains_categories(self, mock_ai_client_cls, app):
        """Test that the prompt lists all valid categories."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        prompt = extractor._create_extraction_prompt("CV text")

        assert "technical" in prompt
        assert "soft_skills" in prompt
        assert "languages" in prompt
        assert "tools" in prompt
        assert "certifications" in prompt

    @patch("services.skill_extractor.AIClient")
    def test_prompt_requests_json(self, mock_ai_client_cls, app):
        """Test that the prompt explicitly requests JSON output."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        prompt = extractor._create_extraction_prompt("CV text")

        assert "JSON" in prompt


class TestValidateSkills:
    """Tests for SkillExtractor._validate_skills()."""

    @patch("services.skill_extractor.AIClient")
    def test_validates_valid_skills(self, mock_ai_client_cls, app):
        """Test validating a valid skills list."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [{"skill_name": "Python", "skill_category": "technical", "experience_years": 5}]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"
        assert result[0]["skill_category"] == "technical"
        assert result[0]["experience_years"] == 5.0

    @patch("services.skill_extractor.AIClient")
    def test_skips_entries_without_skill_name(self, mock_ai_client_cls, app):
        """Test that entries without a skill_name are skipped."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [
            {"skill_name": "", "skill_category": "technical", "experience_years": 3},
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
        ]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"

    @patch("services.skill_extractor.AIClient")
    def test_skips_non_dict_entries(self, mock_ai_client_cls, app):
        """Test that non-dict entries in the array are skipped."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [
            "invalid",
            {"skill_name": "Python", "skill_category": "technical", "experience_years": None},
        ]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"

    @patch("services.skill_extractor.AIClient")
    def test_maps_alternative_categories(self, mock_ai_client_cls, app):
        """Test that alternative category names are mapped correctly."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [
            {"skill_name": "Python", "skill_category": "programming", "experience_years": None},
            {"skill_name": "Deutsch", "skill_category": "sprachen", "experience_years": None},
            {"skill_name": "Teamwork", "skill_category": "soft_skill", "experience_years": None},
            {"skill_name": "Docker", "skill_category": "tool", "experience_years": None},
            {"skill_name": "AWS", "skill_category": "zertifikat", "experience_years": None},
            {"skill_name": "Scrum", "skill_category": "programmierung", "experience_years": None},
        ]

        result = extractor._validate_skills(skills)

        assert len(result) == 6
        assert result[0]["skill_category"] == "technical"  # programming -> technical
        assert result[1]["skill_category"] == "languages"  # sprachen -> languages
        assert result[2]["skill_category"] == "soft_skills"  # soft_skill -> soft_skills
        assert result[3]["skill_category"] == "tools"  # tool -> tools
        assert result[4]["skill_category"] == "certifications"  # zertifikat -> certifications
        assert result[5]["skill_category"] == "technical"  # programmierung -> technical

    @patch("services.skill_extractor.AIClient")
    def test_unknown_category_defaults_to_technical(self, mock_ai_client_cls, app):
        """Test that completely unknown categories default to 'technical'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [{"skill_name": "Something", "skill_category": "unknown_category", "experience_years": None}]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_category"] == "technical"

    @patch("services.skill_extractor.AIClient")
    def test_validates_experience_years(self, mock_ai_client_cls, app):
        """Test validation of experience_years field."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
            {"skill_name": "Java", "skill_category": "technical", "experience_years": 2.5},
            {"skill_name": "Go", "skill_category": "technical", "experience_years": -1},
            {"skill_name": "Rust", "skill_category": "technical", "experience_years": "invalid"},
            {"skill_name": "C++", "skill_category": "technical", "experience_years": None},
        ]

        result = extractor._validate_skills(skills)

        assert len(result) == 5
        assert result[0]["experience_years"] == 5.0
        assert result[1]["experience_years"] == 2.5
        assert result[2]["experience_years"] is None  # negative -> None
        assert result[3]["experience_years"] is None  # invalid string -> None
        assert result[4]["experience_years"] is None  # null stays None

    @patch("services.skill_extractor.AIClient")
    def test_strips_whitespace_from_names(self, mock_ai_client_cls, app):
        """Test that skill names and categories are stripped of whitespace."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [{"skill_name": "  Python  ", "skill_category": "  TECHNICAL  ", "experience_years": None}]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"
        assert result[0]["skill_category"] == "technical"

    @patch("services.skill_extractor.AIClient")
    def test_zertifikate_category_mapping(self, mock_ai_client_cls, app):
        """Test that 'zertifikate' (plural) maps to 'certifications'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [{"skill_name": "ISTQB", "skill_category": "zertifikate", "experience_years": None}]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_category"] == "certifications"

    @patch("services.skill_extractor.AIClient")
    def test_softskills_no_underscore_mapping(self, mock_ai_client_cls, app):
        """Test that 'softskills' (no underscore) maps to 'soft_skills'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [{"skill_name": "Leadership", "skill_category": "softskills", "experience_years": None}]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_category"] == "soft_skills"

    @patch("services.skill_extractor.AIClient")
    def test_language_singular_mapping(self, mock_ai_client_cls, app):
        """Test that 'language' (singular) maps to 'languages'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [{"skill_name": "English", "skill_category": "language", "experience_years": None}]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_category"] == "languages"

    @patch("services.skill_extractor.AIClient")
    def test_certification_singular_mapping(self, mock_ai_client_cls, app):
        """Test that 'certification' (singular) maps to 'certifications'."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        skills = [
            {"skill_name": "AWS Solutions Architect", "skill_category": "certification", "experience_years": None}
        ]

        result = extractor._validate_skills(skills)

        assert len(result) == 1
        assert result[0]["skill_category"] == "certifications"

    @patch("services.skill_extractor.AIClient")
    def test_empty_skills_list(self, mock_ai_client_cls, app):
        """Test validating an empty skills list."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        result = extractor._validate_skills([])

        assert result == []

    @patch("services.skill_extractor.AIClient")
    def test_valid_categories_accepted_directly(self, mock_ai_client_cls, app):
        """Test that all VALID_CATEGORIES are accepted without mapping."""
        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()

        for category in SkillExtractor.VALID_CATEGORIES:
            skills = [{"skill_name": "Test", "skill_category": category, "experience_years": None}]
            result = extractor._validate_skills(skills)
            assert len(result) == 1
            assert result[0]["skill_category"] == category


class TestEndToEndExtraction:
    """Integration-style tests for full extraction flow."""

    @patch("services.skill_extractor.AIClient")
    def test_realistic_cv_extraction(self, mock_ai_client_cls, app):
        """Test extraction with a realistic API response."""
        mock_client = MagicMock()
        mock_ai_client_cls.return_value = mock_client

        mock_client._call_api_json_with_retry.return_value = {
            "skills": [
                {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
                {"skill_name": "JavaScript", "skill_category": "technical", "experience_years": 3},
                {"skill_name": "React", "skill_category": "technical", "experience_years": 2},
                {"skill_name": "Docker", "skill_category": "tools", "experience_years": 3},
                {"skill_name": "Git", "skill_category": "tools", "experience_years": 5},
                {"skill_name": "Teamfuehrung", "skill_category": "soft_skills", "experience_years": None},
                {"skill_name": "Deutsch", "skill_category": "languages", "experience_years": None},
                {"skill_name": "Englisch", "skill_category": "languages", "experience_years": None},
                {"skill_name": "AWS Certified Developer", "skill_category": "certifications", "experience_years": None},
            ]
        }

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        result = extractor.extract_skills_from_cv(
            "Max Mustermann\n5 Jahre Erfahrung als Python-Entwickler\n"
            "JavaScript, React Frontend\nDocker, Git\nTeamfuehrer\n"
            "Sprachen: Deutsch (Muttersprache), Englisch (fliessend)\n"
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

    @patch("services.skill_extractor.AIClient")
    def test_api_called_with_correct_params(self, mock_ai_client_cls, app):
        """Test that the AIClient API is called with correct parameters."""
        mock_client = MagicMock()
        mock_ai_client_cls.return_value = mock_client

        mock_client._call_api_json_with_retry.return_value = {"skills": []}
        mock_client.model = "test-model"

        from services.skill_extractor import SkillExtractor

        extractor = SkillExtractor()
        extractor.extract_skills_from_cv("CV text content")

        call_kwargs = mock_client._call_api_json_with_retry.call_args[1]
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["temperature"] == 0.2
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"
        assert "CV text content" in call_kwargs["messages"][0]["content"]
