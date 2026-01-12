"""
Tests for the ATS (Applicant Tracking System) service.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from services.ats_service import ATSService, analyze_cv_against_job


class TestATSService:
    """Tests for ATSService class."""

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        with patch("services.ats_service.Anthropic") as mock_anthropic:
            service = ATSService(api_key="test-key")
            assert service.api_key == "test-key"
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_without_api_key_uses_config(self):
        """Test initialization uses config when no API key provided."""
        with patch("services.ats_service.Anthropic") as mock_anthropic:
            with patch("services.ats_service.config") as mock_config:
                mock_config.ANTHROPIC_API_KEY = "config-key"
                mock_config.CLAUDE_MODEL = "claude-3-5-haiku-20241022"
                service = ATSService()
                assert service.api_key == "config-key"
                mock_anthropic.assert_called_once_with(api_key="config-key")

    def test_init_raises_without_api_key(self):
        """Test initialization raises error when no API key available."""
        with patch("services.ats_service.config") as mock_config:
            mock_config.ANTHROPIC_API_KEY = None
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY nicht gesetzt"):
                ATSService(api_key=None)

    def test_analyze_empty_cv_raises_error(self):
        """Test that empty CV text raises ValueError."""
        with patch("services.ats_service.Anthropic"):
            service = ATSService(api_key="test-key")
            with pytest.raises(ValueError, match="CV text cannot be empty"):
                service.analyze_cv_against_job("", "Some job description")

    def test_analyze_empty_job_raises_error(self):
        """Test that empty job description raises ValueError."""
        with patch("services.ats_service.Anthropic"):
            service = ATSService(api_key="test-key")
            with pytest.raises(ValueError, match="Job description cannot be empty"):
                service.analyze_cv_against_job("Some CV text", "")

    def test_analyze_whitespace_only_cv_raises_error(self):
        """Test that whitespace-only CV raises ValueError."""
        with patch("services.ats_service.Anthropic"):
            service = ATSService(api_key="test-key")
            with pytest.raises(ValueError, match="CV text cannot be empty"):
                service.analyze_cv_against_job("   \n\t  ", "Some job description")

    def test_analyze_whitespace_only_job_raises_error(self):
        """Test that whitespace-only job description raises ValueError."""
        with patch("services.ats_service.Anthropic"):
            service = ATSService(api_key="test-key")
            with pytest.raises(ValueError, match="Job description cannot be empty"):
                service.analyze_cv_against_job("Some CV text", "   \n\t  ")

    def test_analyze_successful_response(self):
        """Test successful analysis with valid response."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "score": 75,
                        "matched_keywords": ["Python", "JavaScript", "React"],
                        "missing_keywords": ["Docker", "Kubernetes"],
                        "suggestions": [
                            "Add Docker experience",
                            "Include cloud certifications",
                        ],
                    }
                )
            )
        ]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            result = service.analyze_cv_against_job(
                "Experienced Python developer with React skills",
                "Looking for Python developer with Docker and Kubernetes",
            )

            assert result["score"] == 75
            assert "Python" in result["matched_keywords"]
            assert "Docker" in result["missing_keywords"]
            assert len(result["suggestions"]) == 2

    def test_analyze_handles_json_in_text(self):
        """Test that JSON embedded in text is correctly extracted."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='Here is the analysis:\n{"score": 80, "matched_keywords": ["Python"], "missing_keywords": ["Go"], "suggestions": ["Learn Go"]}\nThat\'s my analysis.'
            )
        ]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            result = service.analyze_cv_against_job("CV text", "Job description")

            assert result["score"] == 80
            assert result["matched_keywords"] == ["Python"]

    def test_analyze_clamps_score_to_valid_range(self):
        """Test that score is clamped to 0-100 range."""
        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")

            # Test score > 100
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    text='{"score": 150, "matched_keywords": [], "missing_keywords": [], "suggestions": []}'
                )
            ]
            mock_client.messages.create.return_value = mock_response
            result = service.analyze_cv_against_job("CV", "Job")
            assert result["score"] == 100

            # Test score < 0
            mock_response.content = [
                MagicMock(
                    text='{"score": -10, "matched_keywords": [], "missing_keywords": [], "suggestions": []}'
                )
            ]
            result = service.analyze_cv_against_job("CV", "Job")
            assert result["score"] == 0

    def test_analyze_handles_invalid_json(self):
        """Test that invalid JSON returns default response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not valid JSON at all")]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            result = service.analyze_cv_against_job("CV text", "Job description")

            assert result["score"] == 0
            assert result["matched_keywords"] == []
            assert result["missing_keywords"] == []
            assert "Analyse konnte nicht durchgeführt werden" in result["suggestions"]

    def test_analyze_handles_malformed_json_fields(self):
        """Test that malformed fields are handled gracefully."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"score": "high", "matched_keywords": "Python", "missing_keywords": null, "suggestions": 123}'
            )
        ]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            result = service.analyze_cv_against_job("CV text", "Job description")

            assert result["score"] == 0
            assert result["matched_keywords"] == []
            assert result["missing_keywords"] == []
            assert result["suggestions"] == []

    def test_analyze_api_failure_retries(self):
        """Test that API failures trigger retries."""
        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                MagicMock(
                    content=[
                        MagicMock(
                            text='{"score": 50, "matched_keywords": [], "missing_keywords": [], "suggestions": []}'
                        )
                    ]
                ),
            ]
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            result = service.analyze_cv_against_job("CV text", "Job description")

            assert result["score"] == 50
            assert mock_client.messages.create.call_count == 3

    def test_analyze_api_failure_exhausts_retries(self):
        """Test that exhausted retries raise exception."""
        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Persistent error")
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")

            with pytest.raises(Exception, match="ATS analysis failed after 3 attempts"):
                service.analyze_cv_against_job("CV text", "Job description")

            assert mock_client.messages.create.call_count == 3

    def test_convenience_function(self):
        """Test the analyze_cv_against_job convenience function."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"score": 60, "matched_keywords": ["SQL"], "missing_keywords": [], "suggestions": []}'
            )
        ]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            result = analyze_cv_against_job(
                "CV with SQL", "Need SQL developer", api_key="test-key"
            )

            assert result["score"] == 60
            assert "SQL" in result["matched_keywords"]

    def test_long_inputs_are_truncated(self):
        """Test that very long inputs are handled (truncated in prompt)."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"score": 70, "matched_keywords": [], "missing_keywords": [], "suggestions": []}'
            )
        ]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            long_cv = "A" * 10000
            long_job = "B" * 10000
            result = service.analyze_cv_against_job(long_cv, long_job)

            assert result["score"] == 70
            call_args = mock_client.messages.create.call_args
            prompt = call_args.kwargs["messages"][0]["content"]
            assert len(prompt) < 20000

    def test_filters_empty_keywords(self):
        """Test that empty strings in keywords are filtered out."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"score": 50, "matched_keywords": ["Python", "", null, "React"], "missing_keywords": ["", "Docker"], "suggestions": ["", "Add skills"]}'
            )
        ]

        with patch("services.ats_service.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            service = ATSService(api_key="test-key")
            result = service.analyze_cv_against_job("CV", "Job")

            assert "" not in result["matched_keywords"]
            assert "" not in result["missing_keywords"]
            assert "" not in result["suggestions"]
            assert "Python" in result["matched_keywords"]
