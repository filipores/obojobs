"""
Tests for the ATS Optimizer service (cover letter analysis).
"""

from unittest.mock import MagicMock, patch

import pytest

from services.ats_optimizer import ATSOptimizer, analyze_cover_letter_ats


class TestATSOptimizer:
    """Tests for ATSOptimizer class."""

    def test_init_creates_ai_client(self):
        """Test initialization creates an AIClient instance."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            optimizer = ATSOptimizer()
            mock_ai_client_cls.assert_called_once()
            assert optimizer.client is mock_ai_client_cls.return_value

    def test_analyze_empty_cover_letter_raises_error(self):
        """Test that empty cover letter raises ValueError."""
        with patch("services.ats_optimizer.AIClient"):
            optimizer = ATSOptimizer()
            with pytest.raises(ValueError, match="Cover letter text cannot be empty"):
                optimizer.analyze_cover_letter("", "Some job description")

    def test_analyze_empty_job_raises_error(self):
        """Test that empty job description raises ValueError."""
        with patch("services.ats_optimizer.AIClient"):
            optimizer = ATSOptimizer()
            with pytest.raises(ValueError, match="Job description cannot be empty"):
                optimizer.analyze_cover_letter("Some cover letter", "")

    def test_analyze_whitespace_only_cover_letter_raises_error(self):
        """Test that whitespace-only cover letter raises ValueError."""
        with patch("services.ats_optimizer.AIClient"):
            optimizer = ATSOptimizer()
            with pytest.raises(ValueError, match="Cover letter text cannot be empty"):
                optimizer.analyze_cover_letter("   \n\t  ", "Some job description")

    def test_analyze_successful_response(self):
        """Test successful analysis with all fields."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": ["Docker", "Kubernetes"],
                "keyword_suggestions": [
                    {"keyword": "Docker", "suggestion": "Mention Docker in your project experience"},
                    {"keyword": "Kubernetes", "suggestion": "Add Kubernetes deployment knowledge"},
                ],
                "format_issues": [],
                "found_keywords": ["Python", "Java", "Teamwork"],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
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
        # 3 found, 2 missing = 60% keyword match
        # 0 format issues = 100% format score
        # Expected: 60 * 0.7 + 100 * 0.3 = 42 + 30 = 72
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": ["Docker", "Kubernetes"],
                "keyword_suggestions": [],
                "format_issues": [],
                "found_keywords": ["Python", "Java", "Teamwork"],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] == 72

    def test_format_issues_penalty(self):
        """Test that format issues reduce the score."""
        # 5 found, 0 missing = 100% keyword match
        # 2 format issues = -20 points = 80% format score
        # Expected: 100 * 0.7 + 80 * 0.3 = 70 + 24 = 94
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": [],
                "keyword_suggestions": [],
                "format_issues": ["Issue 1", "Issue 2"],
                "found_keywords": ["A", "B", "C", "D", "E"],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] == 94

    def test_keyword_density_calculation(self):
        """Test keyword density is calculated correctly."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": ["Docker"],
                "keyword_suggestions": [],
                "format_issues": [],
                "found_keywords": ["Python"],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter(
                "I love Python. Python is great. More Python!", "Need Python and Docker skills"
            )

            assert result["keyword_density"]["Python"] == 3
            assert result["keyword_density"]["Docker"] == 0

    def test_analyze_api_failure_raises_exception(self):
        """Test that API failure raises an exception."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.side_effect = Exception("Persistent error")
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()

            with pytest.raises(Exception, match="ATS optimization analysis failed"):
                optimizer.analyze_cover_letter("Cover letter", "Job description")

    def test_convenience_function(self):
        """Test the analyze_cover_letter_ats convenience function."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": [],
                "keyword_suggestions": [],
                "format_issues": [],
                "found_keywords": ["SQL"],
            }
            mock_ai_client_cls.return_value = mock_client

            result = analyze_cover_letter_ats("Cover letter with SQL", "Need SQL developer")

            assert "SQL" in result["found_keywords"]

    def test_missing_keywords_limited_to_ten(self):
        """Test that missing keywords are limited to 10."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": [f"Keyword{i}" for i in range(15)],
                "keyword_suggestions": [],
                "format_issues": [],
                "found_keywords": [],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert len(result["missing_keywords"]) == 10

    def test_keyword_suggestions_limited_to_five(self):
        """Test that keyword suggestions are limited to 5."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": [],
                "keyword_suggestions": [{"keyword": f"K{i}", "suggestion": f"S{i}"} for i in range(10)],
                "format_issues": [],
                "found_keywords": [],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert len(result["keyword_suggestions"]) == 5

    def test_score_never_below_zero(self):
        """Test that score is never below 0."""
        # 0 found, 10 missing = 0% keyword match
        # 4 format issues = -40 but capped at -30 = 70% format
        # Expected: max(0, 0 * 0.7 + 70 * 0.3) = max(0, 21) = 21
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": [f"K{i}" for i in range(10)],
                "keyword_suggestions": [],
                "format_issues": ["I1", "I2", "I3", "I4"],
                "found_keywords": [],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] >= 0
            assert result["ats_score"] == 21

    def test_score_never_above_hundred(self):
        """Test that score is never above 100."""
        with patch("services.ats_optimizer.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "missing_keywords": [],
                "keyword_suggestions": [],
                "format_issues": [],
                "found_keywords": ["A", "B", "C"],
            }
            mock_ai_client_cls.return_value = mock_client

            optimizer = ATSOptimizer()
            result = optimizer.analyze_cover_letter("Cover letter", "Job description")

            assert result["ats_score"] <= 100
            assert result["ats_score"] == 100
