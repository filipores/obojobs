"""Tests for recommendations search, save, and stats endpoints."""

import json
from unittest.mock import MagicMock, patch

from models import JobRecommendation, db


def _create_recommendation(user_id, fit_score=80, fit_category="gut", dismissed=False, applied=False, job_url=None):
    rec = JobRecommendation(
        user_id=user_id,
        job_data_json=json.dumps({"title": "Dev", "company": "Test GmbH", "url": job_url}),
        fit_score=fit_score,
        fit_category=fit_category,
        job_title="Dev",
        company_name="Test GmbH",
        job_url=job_url,
        dismissed=dismissed,
        applied=applied,
    )
    db.session.add(rec)
    return rec


class TestSaveRecommendation:
    """Tests for POST /api/recommendations/save"""

    def test_requires_auth(self, client):
        assert client.post("/api/recommendations/save", json={}).status_code == 401

    def test_missing_data(self, client, auth_headers):
        assert (
            client.post("/api/recommendations/save", headers=auth_headers, content_type="application/json").status_code
            == 400
        )

    @patch("routes.recommendations.JobRecommender")
    def test_duplicate_url(self, mock_cls, client, auth_headers):
        mock_cls.return_value.check_duplicate.return_value = True
        r = client.post("/api/recommendations/save", json={"job_url": "http://x/1"}, headers=auth_headers)
        assert r.status_code == 400 and r.get_json()["is_duplicate"] is True

    @patch("routes.recommendations.JobRecommender")
    def test_save_with_job_data(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock.check_duplicate.return_value = False
        rec = MagicMock()
        rec.to_dict.return_value = {"id": 1}
        mock.create_recommendation.return_value = rec
        r = client.post(
            "/api/recommendations/save",
            json={"job_data": {"title": "D"}, "fit_score": 80, "fit_category": "gut"},
            headers=auth_headers,
        )
        assert r.status_code == 201

    @patch("routes.recommendations.JobRecommender")
    def test_save_without_job_data_fetches(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock.check_duplicate.return_value = False
        mock.analyze_job_for_user.return_value = {"job_data": {"title": "D"}, "fit_score": 75, "fit_category": "gut"}
        rec = MagicMock()
        rec.to_dict.return_value = {"id": 1}
        mock.create_recommendation.return_value = rec
        assert (
            client.post("/api/recommendations/save", json={"job_url": "http://x/f"}, headers=auth_headers).status_code
            == 201
        )

    @patch("routes.recommendations.JobRecommender")
    def test_save_no_job_data_returns_400(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock.check_duplicate.return_value = False
        mock.analyze_job_for_user.return_value = None
        assert (
            client.post("/api/recommendations/save", json={"job_url": "http://x/b"}, headers=auth_headers).status_code
            == 400
        )

    @patch("routes.recommendations.JobRecommender")
    def test_save_default_fit_score(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock.check_duplicate.return_value = False
        rec = MagicMock()
        rec.to_dict.return_value = {"id": 1}
        mock.create_recommendation.return_value = rec
        client.post("/api/recommendations/save", json={"job_data": {"title": "D"}}, headers=auth_headers)
        assert mock.create_recommendation.call_args.kwargs["fit_score"] == 50


class TestSearchJobs:
    """Tests for POST /api/recommendations/search"""

    def test_requires_auth(self, client):
        assert client.post("/api/recommendations/search", json={}).status_code == 401

    @patch("routes.recommendations.JobRecommender")
    def test_search_success(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock_cls.MIN_FIT_SCORE = 60
        mock.search_and_score_jobs.return_value = {
            "results": [{"title": "D", "fit_score": 85, "fit_category": "sehr_gut", "url": "http://j/1"}],
            "total_found": 1,
            "page": 1,
            "has_more": False,
        }
        mock.check_duplicate.return_value = False
        mock.create_recommendation.return_value = MagicMock(id=1)
        r = client.post("/api/recommendations/search", json={"location": "Berlin"}, headers=auth_headers)
        assert r.get_json()["data"]["saved_count"] == 1

    @patch("routes.recommendations.JobRecommender")
    def test_search_low_score_not_saved(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock_cls.MIN_FIT_SCORE = 60
        mock.search_and_score_jobs.return_value = {
            "results": [{"title": "D", "fit_score": 10, "fit_category": "niedrig", "url": "http://j/2"}],
            "total_found": 1,
            "page": 1,
            "has_more": False,
        }
        r = client.post("/api/recommendations/search", json={}, headers=auth_headers)
        assert r.get_json()["data"]["saved_count"] == 0


class TestRecommendationStats:
    """Tests for GET /api/recommendations/stats"""

    def test_requires_auth(self, client):
        assert client.get("/api/recommendations/stats").status_code == 401

    def test_empty_stats(self, client, auth_headers):
        data = client.get("/api/recommendations/stats", headers=auth_headers).get_json()
        assert data["total"] == 0

    def test_stats_with_data(self, app, client, test_user, auth_headers):
        with app.app_context():
            _create_recommendation(test_user["id"], fit_score=90, fit_category="sehr_gut")
            _create_recommendation(test_user["id"], fit_score=75, fit_category="gut")
            _create_recommendation(test_user["id"], fit_category="mittel", dismissed=True)
            _create_recommendation(test_user["id"], fit_category="mittel", applied=True)
            db.session.commit()
        data = client.get("/api/recommendations/stats", headers=auth_headers).get_json()
        assert data["total"] == 4
        assert data["dismissed"] == 1
        assert data["by_score"]["sehr_gut"] == 1
