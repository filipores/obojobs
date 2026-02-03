"""
Tests for the ATS Optimizer service (cover letter analysis).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from services.ats_optimizer import ATSOptimizer, analyze_cover_letter_ats


class TestATSOptimizer:
    """Tests for ATSOptimizer class."""

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            optimizer = ATSOptimizer(api_key="test-key")
            assert optimizer.api_key == "test-key"
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_without_api_key_uses_config(self):
        """Test initialization uses config when no API key provided."""
        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            with patch("services.ats_optimizer.config") as mock_config:
                mock_config.ANTHROPIC_API_KEY = "config-key"
                mock_config.CLAUDE_MODEL = "claude-3-5-haiku-20241022"
                optimizer = ATSOptimizer()
                assert optimizer.api_key == "config-key"
                mock_anthropic.assert_called_once_with(api_key="config-key")

    def test_init_raises_without_api_key(self):
        """Test initialization raises error when no API key available."""
        with patch("services.ats_optimizer.config") as mock_config:
            mock_config.ANTHROPIC_API_KEY = None
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY nicht gesetzt"):
                ATSOptimizer(api_key=None)

    def test_analyze_empty_cover_letter_raises_error(self):
        """Test that empty cover letter raises ValueError."""
        with patch("services.ats_optimizer.Anthropic"):
            optimizer = ATSOptimizer(api_key="test-key")
            with pytest.raises(ValueError, match="Cover letter text cannot be empty"):
                optimizer.analyze_cover_letter("", "Some job description")

    def test_analyze_empty_job_raises_error(self):
        """Test that empty job description raises ValueError."""
        with patch("services.ats_optimizer.Anthropic"):
            optimizer = ATSOptimizer(api_key="test-key")
            with pytest.raises(ValueError, match="Job description cannot be empty"):
                optimizer.analyze_cover_letter("Some cover letter", "")

    def test_analyze_whitespace_only_cover_letter_raises_error(self):
        """Test that whitespace-only cover letter raises ValueError."""
        with patch("services.ats_optimizer.Anthropic"):
            optimizer = ATSOptimizer(api_key="test-key")
            with pytest.raises(ValueError, match="Cover letter text cannot be empty"):
                optimizer.analyze_cover_letter("   \n\t  ", "Some job description")

    def test_analyze_successful_response(self):
        """Test successful analysis with all fields."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": ["Docker", "Kubernetes"],
                        "keyword_suggestions": [
                            {"keyword": "Docker", "suggestion": "Mention Docker in your project experience"},
                            {"keyword": "Kubernetes", "suggestion": "Add Kubernetes deployment knowledge"},
                        ],
                        "format_issues": [],
                        "found_keywords": ["Python", "Java", "Teamwork"],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter(
                "I am an experienced Python and Java developer with strong teamwork skills.",
                "Looking for Python developer with Docker and Kubernetes experience.",
            )

            assert "ats_score" in result
            assert result["missing_keywords"] == ["Docker", "Kubernetes"]
            assert result["found_keywords"] == ["Python", "Java", "Teamwork"]
            assert len(result["keyword_suggestions"]) == 2
            assert result["format_issues"] == []

    def test_ats_score_calculation(self):
        """Test ATS score is calculated correctly."""
        mock_response = MagicMock()
        # 3 found, 2 missing = 60% keyword match
        # 0 format issues = 100% format score
        # Expected: 60 * 0.7 + 100 * 0.3 = 42 + 30 = 72
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": ["Docker", "Kubernetes"],
                        "keyword_suggestions": [],
                        "format_issues": [],
                        "found_keywords": ["Python", "Java", "Teamwork"],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] == 72

    def test_format_issues_penalty(self):
        """Test that format issues reduce the score."""
        mock_response = MagicMock()
        # 5 found, 0 missing = 100% keyword match
        # 2 format issues = -20 points = 80% format score
        # Expected: 100 * 0.7 + 80 * 0.3 = 70 + 24 = 94
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": [],
                        "keyword_suggestions": [],
                        "format_issues": ["Issue 1", "Issue 2"],
                        "found_keywords": ["A", "B", "C", "D", "E"],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] == 94

    def test_keyword_density_calculation(self):
        """Test keyword density is calculated correctly."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": ["Docker"],
                        "keyword_suggestions": [],
                        "format_issues": [],
                        "found_keywords": ["Python"],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter(
                "I love Python. Python is great. More Python!", "Need Python and Docker skills"
            )

            assert result["keyword_density"]["Python"] == 3
            assert result["keyword_density"]["Docker"] == 0

    def test_analyze_handles_invalid_json(self):
        """Test that invalid JSON returns default response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not valid JSON at all")]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] == 0
            assert result["missing_keywords"] == []
            assert "Analyse konnte nicht durchgeführt werden" in result["format_issues"]

    def test_analyze_api_failure_retries(self):
        """Test that API failures trigger retries."""
        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                MagicMock(
                    content=[
                        MagicMock(
                            text=json.dumps(
                                {
                                    "missing_keywords": [],
                                    "keyword_suggestions": [],
                                    "format_issues": [],
                                    "found_keywords": ["Python"],
                                }
                            )
                        )
                    ]
                ),
            ]
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["found_keywords"] == ["Python"]
            assert mock_client.messages.create.call_count == 3

    def test_analyze_api_failure_exhausts_retries(self):
        """Test that exhausted retries raise exception."""
        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Persistent error")
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")

            with pytest.raises(Exception, match="ATS optimization analysis failed after 3 attempts"):
                optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert mock_client.messages.create.call_count == 3

    def test_convenience_function(self):
        """Test the analyze_cover_letter_ats convenience function."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {"missing_keywords": [], "keyword_suggestions": [], "format_issues": [], "found_keywords": ["SQL"]}
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            result = analyze_cover_letter_ats("Cover letter with SQL", "Need SQL developer", api_key="test-key")

            assert "SQL" in result["found_keywords"]

    def test_missing_keywords_limited_to_ten(self):
        """Test that missing keywords are limited to 10."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": [f"Keyword{i}" for i in range(15)],
                        "keyword_suggestions": [],
                        "format_issues": [],
                        "found_keywords": [],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert len(result["missing_keywords"]) == 10

    def test_keyword_suggestions_limited_to_five(self):
        """Test that keyword suggestions are limited to 5."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": [],
                        "keyword_suggestions": [{"keyword": f"K{i}", "suggestion": f"S{i}"} for i in range(10)],
                        "format_issues": [],
                        "found_keywords": [],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert len(result["keyword_suggestions"]) == 5

    def test_score_never_below_zero(self):
        """Test that score is never below 0."""
        mock_response = MagicMock()
        # 0 found, 10 missing = 0% keyword match
        # 4 format issues = -40 but capped at -30 = 70% format
        # Expected: max(0, 0 * 0.7 + 70 * 0.3) = max(0, 21) = 21
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": [f"K{i}" for i in range(10)],
                        "keyword_suggestions": [],
                        "format_issues": ["I1", "I2", "I3", "I4"],
                        "found_keywords": [],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] >= 0
            assert result["ats_score"] == 21

    def test_score_never_above_hundred(self):
        """Test that score is never above 100."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "missing_keywords": [],
                        "keyword_suggestions": [],
                        "format_issues": [],
                        "found_keywords": ["A", "B", "C"],
                    }
                )
            )
        ]

        with patch("services.ats_optimizer.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            optimizer = ATSOptimizer(api_key="test-key")
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] <= 100
            assert result["ats_score"] == 100
