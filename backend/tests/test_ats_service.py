"""
Tests for the ATS (Applicant Tracking System) service.
"""

from unittest.mock import MagicMock, patch

import pytest

from services.ats_service import (
    CATEGORY_WEIGHTS,
    ATSService,
    analyze_cv_against_job,
)


class TestATSService:
    """Tests for ATSService class."""

    def test_init_creates_ai_client(self):
        """Test initialization creates an AIClient instance."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            service = ATSService()
            mock_ai_client_cls.assert_called_once()
            assert service.client is mock_ai_client_cls.return_value

    def test_analyze_empty_cv_raises_error(self):
        """Test that empty CV text raises ValueError."""
        with patch("services.ats_service.AIClient"):
            service = ATSService()
            with pytest.raises(ValueError, match="CV text cannot be empty"):
                service.analyze_cv_against_job("", "Some job description")

    def test_analyze_empty_job_raises_error(self):
        """Test that empty job description raises ValueError."""
        with patch("services.ats_service.AIClient"):
            service = ATSService()
            with pytest.raises(ValueError, match="Job description cannot be empty"):
                service.analyze_cv_against_job("Some CV text", "")

    def test_analyze_whitespace_only_cv_raises_error(self):
        """Test that whitespace-only CV raises ValueError."""
        with patch("services.ats_service.AIClient"):
            service = ATSService()
            with pytest.raises(ValueError, match="CV text cannot be empty"):
                service.analyze_cv_against_job("   \n\t  ", "Some job description")

    def test_analyze_whitespace_only_job_raises_error(self):
        """Test that whitespace-only job description raises ValueError."""
        with patch("services.ats_service.AIClient"):
            service = ATSService()
            with pytest.raises(ValueError, match="Job description cannot be empty"):
                service.analyze_cv_against_job("Some CV text", "   \n\t  ")

    def test_analyze_successful_response_with_categories(self):
        """Test successful analysis with categorized keywords."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {
                        "matched": ["Python", "JavaScript"],
                        "missing": ["Docker", "Kubernetes"],
                    },
                    "soft_skills": {
                        "matched": ["Teamwork"],
                        "missing": ["Leadership"],
                    },
                    "qualifications": {
                        "matched": ["Bachelor CS"],
                        "missing": ["AWS Certification"],
                    },
                    "experience": {
                        "matched": ["3 years development"],
                        "missing": ["DevOps experience"],
                    },
                },
                "suggestions": [
                    {"content": "Add Docker experience", "priority": "high"},
                    {
                        "content": "Include cloud certifications",
                        "priority": "medium",
                    },
                    {"content": "Mention leadership roles", "priority": "low"},
                ],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job(
                "Experienced Python developer with React skills",
                "Looking for Python developer with Docker and Kubernetes",
            )

            # Check categories exist
            assert "categories" in result
            assert "hard_skills" in result["categories"]
            assert "soft_skills" in result["categories"]
            assert "qualifications" in result["categories"]
            assert "experience" in result["categories"]

            # Check category data
            assert "Python" in result["categories"]["hard_skills"]["matched"]
            assert "Docker" in result["categories"]["hard_skills"]["missing"]

            # Check flattened keywords for backward compatibility
            assert "Python" in result["matched_keywords"]
            assert "Docker" in result["missing_keywords"]

            # Check suggestions with priorities
            assert len(result["suggestions"]) == 3
            assert result["suggestions"][0]["content"] == "Add Docker experience"
            assert result["suggestions"][0]["priority"] == "high"
            assert result["suggestions"][1]["priority"] == "medium"
            assert result["suggestions"][2]["priority"] == "low"

    def test_weighted_score_calculation(self):
        """Test that score is calculated using category weights."""
        # 50% match in hard_skills (weight 0.40) = 20
        # 100% match in soft_skills (weight 0.15) = 15
        # 0% match in qualifications (weight 0.25) = 0
        # 100% match in experience (weight 0.20) = 20
        # Total expected: 55
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {
                        "matched": ["Python"],
                        "missing": ["Docker"],
                    },
                    "soft_skills": {"matched": ["Teamwork"], "missing": []},
                    "qualifications": {
                        "matched": [],
                        "missing": ["AWS Cert"],
                    },
                    "experience": {
                        "matched": ["3 years"],
                        "missing": [],
                    },
                },
                "suggestions": [],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV", "Job")

            # hard_skills: 1/2 * 100 * 0.40 = 20
            # soft_skills: 1/1 * 100 * 0.15 = 15
            # qualifications: 0/1 * 100 * 0.25 = 0
            # experience: 1/1 * 100 * 0.20 = 20
            # Total: 55
            assert result["score"] == 55

    def test_weighted_score_empty_category_gives_full_weight(self):
        """Test that empty categories contribute full score."""
        # Only hard_skills has data (50% match)
        # Other categories are empty -> get 100% score for their weight
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {
                        "matched": ["Python"],
                        "missing": ["Docker"],
                    },
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": [],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV", "Job")

            # hard_skills: 1/2 * 100 * 0.40 = 20
            # soft_skills: 100 * 0.15 = 15 (empty -> full)
            # qualifications: 100 * 0.25 = 25 (empty -> full)
            # experience: 100 * 0.20 = 20 (empty -> full)
            # Total: 80
            assert result["score"] == 80

    def test_score_clamped_to_valid_range(self):
        """Test that score is always between 0 and 100."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()

            # Perfect match -> 100
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": ["A", "B"], "missing": []},
                    "soft_skills": {"matched": ["C"], "missing": []},
                    "qualifications": {"matched": ["D"], "missing": []},
                    "experience": {"matched": ["E"], "missing": []},
                },
                "suggestions": [],
            }
            result = service.analyze_cv_against_job("CV", "Job")
            assert result["score"] == 100

            # No match -> 0
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": [], "missing": ["A"]},
                    "soft_skills": {"matched": [], "missing": ["B"]},
                    "qualifications": {"matched": [], "missing": ["C"]},
                    "experience": {"matched": [], "missing": ["D"]},
                },
                "suggestions": [],
            }
            result = service.analyze_cv_against_job("CV", "Job")
            assert result["score"] == 0

    def test_analyze_handles_malformed_category_data(self):
        """Test that malformed category data is handled gracefully."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": "not a dict",
                    "soft_skills": {"matched": "not a list"},
                    "qualifications": None,
                    # experience missing entirely
                },
                "suggestions": [],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV text", "Job description")

            # All categories should be empty but valid
            for category in ["hard_skills", "soft_skills", "qualifications", "experience"]:
                assert category in result["categories"]
                assert result["categories"][category]["matched"] == []
                assert result["categories"][category]["missing"] == []

    def test_suggestion_priority_validation(self):
        """Test that invalid priorities are set to medium."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": [], "missing": []},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": [
                    {"content": "Valid high", "priority": "high"},
                    {"content": "Invalid priority", "priority": "critical"},
                    {"content": "Missing priority"},
                    {"content": "Valid low", "priority": "low"},
                ],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV", "Job")

            assert result["suggestions"][0]["priority"] == "high"
            assert result["suggestions"][1]["priority"] == "medium"  # Invalid -> medium
            assert result["suggestions"][2]["priority"] == "medium"  # Missing -> medium
            assert result["suggestions"][3]["priority"] == "low"

    def test_backward_compatibility_string_suggestions(self):
        """Test that plain string suggestions are converted to dict format."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": [], "missing": []},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": ["Plain string suggestion", "Another one"],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV", "Job")

            assert len(result["suggestions"]) == 2
            assert result["suggestions"][0]["content"] == "Plain string suggestion"
            assert result["suggestions"][0]["priority"] == "medium"

    def test_analyze_api_failure_raises_exception(self):
        """Test that API failure raises an exception."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.side_effect = Exception("Persistent error")
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()

            with pytest.raises(Exception, match="ATS analysis failed"):
                service.analyze_cv_against_job("CV text", "Job description")

    def test_convenience_function(self):
        """Test the analyze_cv_against_job convenience function."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": ["SQL"], "missing": []},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": [],
            }
            mock_ai_client_cls.return_value = mock_client

            result = analyze_cv_against_job("CV with SQL", "Need SQL developer")

            assert "SQL" in result["matched_keywords"]
            assert "categories" in result

    def test_long_inputs_are_truncated(self):
        """Test that very long inputs are handled (truncated in prompt)."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": [], "missing": []},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": [],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            long_cv = "A" * 10000
            long_job = "B" * 10000
            result = service.analyze_cv_against_job(long_cv, long_job)

            assert "categories" in result
            call_args = mock_client._call_api_json_with_retry.call_args
            prompt = call_args.kwargs["messages"][0]["content"]
            assert len(prompt) < 20000

    def test_filters_empty_keywords_in_categories(self):
        """Test that empty strings in category keywords are filtered out."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {
                        "matched": ["Python", "", None],
                        "missing": ["", "Docker"],
                    },
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": [
                    {"content": "", "priority": "high"},
                    {"content": "Valid suggestion", "priority": "low"},
                ],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV", "Job")

            # Check categories
            assert result["categories"]["hard_skills"]["matched"] == ["Python"]
            assert result["categories"]["hard_skills"]["missing"] == ["Docker"]

            # Check flattened keywords
            assert "" not in result["matched_keywords"]
            assert "" not in result["missing_keywords"]

            # Check suggestions (empty content filtered)
            assert len(result["suggestions"]) == 1
            assert result["suggestions"][0]["content"] == "Valid suggestion"

    def test_category_weights_sum_to_one(self):
        """Test that category weights sum to 1.0."""
        total = sum(CATEGORY_WEIGHTS.values())
        assert abs(total - 1.0) < 0.0001

    def test_all_valid_priorities(self):
        """Test that all valid priorities are accepted."""
        with patch("services.ats_service.AIClient") as mock_ai_client_cls:
            mock_client = MagicMock()
            mock_client._call_api_json_with_retry.return_value = {
                "categories": {
                    "hard_skills": {"matched": [], "missing": []},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
                "suggestions": [
                    {"content": "High priority", "priority": "high"},
                    {"content": "Medium priority", "priority": "medium"},
                    {"content": "Low priority", "priority": "low"},
                ],
            }
            mock_ai_client_cls.return_value = mock_client

            service = ATSService()
            result = service.analyze_cv_against_job("CV", "Job")

            assert result["suggestions"][0]["priority"] == "high"
            assert result["suggestions"][1]["priority"] == "medium"
            assert result["suggestions"][2]["priority"] == "low"
