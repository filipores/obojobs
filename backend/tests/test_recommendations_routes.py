"""Tests for recommendations routes - core CRUD and analyze (routes/recommendations.py)."""

import json
from unittest.mock import MagicMock, patch

from models import JobRecommendation, db


def _create_recommendation(user_id, fit_score=80, fit_category="gut", dismissed=False, applied=False, job_url=None):
    """Helper to create a JobRecommendation."""
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


class TestGetRecommendations:
    """Tests for GET /api/recommendations"""

    def test_requires_auth(self, client):
        assert client.get("/api/recommendations").status_code == 401

    @patch("routes.recommendations.JobRecommender")
    def test_returns_recommendations(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        rec = MagicMock()
        rec.to_dict.return_value = {"id": 1, "fit_score": 80}
        mock.get_recommendations.return_value = [rec]
        assert client.get("/api/recommendations", headers=auth_headers).get_json()["total"] == 1

    @patch("routes.recommendations.JobRecommender")
    def test_respects_limit(self, mock_cls, client, auth_headers):
        mock_cls.return_value.get_recommendations.return_value = []
        client.get("/api/recommendations?limit=5", headers=auth_headers)
        assert mock_cls.return_value.get_recommendations.call_args.kwargs["limit"] == 5

    @patch("routes.recommendations.JobRecommender")
    def test_invalid_limit_uses_default(self, mock_cls, client, auth_headers):
        mock_cls.return_value.get_recommendations.return_value = []
        client.get("/api/recommendations?limit=abc", headers=auth_headers)
        assert mock_cls.return_value.get_recommendations.call_args.kwargs["limit"] == 20

    @patch("routes.recommendations.JobRecommender")
    def test_include_dismissed(self, mock_cls, client, auth_headers):
        mock_cls.return_value.get_recommendations.return_value = []
        client.get("/api/recommendations?include_dismissed=true", headers=auth_headers)
        assert mock_cls.return_value.get_recommendations.call_args.kwargs["include_dismissed"] is True


class TestAnalyzeJob:
    """Tests for POST /api/recommendations/analyze"""

    def test_requires_auth(self, client):
        assert client.post("/api/recommendations/analyze", json={"job_url": "http://x"}).status_code == 401

    def test_missing_job_url(self, client, auth_headers):
        assert client.post("/api/recommendations/analyze", json={}, headers=auth_headers).status_code == 400

    @patch("routes.recommendations.JobRecommender")
    def test_duplicate_job(self, mock_cls, app, client, test_user, auth_headers):
        with app.app_context():
            _create_recommendation(test_user["id"], job_url="http://example.com/job/1")
            db.session.commit()
        r = client.post(
            "/api/recommendations/analyze", json={"job_url": "http://example.com/job/1"}, headers=auth_headers
        )
        assert r.get_json()["is_duplicate"] is True

    @patch("routes.recommendations.JobRecommender")
    def test_analyze_success(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock.analyze_job_for_user.return_value = {
            "fit_score": 85,
            "fit_category": "sehr_gut",
            "job_data": {"title": "Dev"},
        }
        mock.create_recommendation.return_value = MagicMock(id=1)
        mock_cls.MIN_FIT_SCORE = 60
        assert (
            client.post(
                "/api/recommendations/analyze", json={"job_url": "http://x/2"}, headers=auth_headers
            ).status_code
            == 200
        )

    @patch("routes.recommendations.JobRecommender")
    def test_analyze_returns_none(self, mock_cls, client, auth_headers):
        mock_cls.return_value.analyze_job_for_user.return_value = None
        assert (
            client.post(
                "/api/recommendations/analyze", json={"job_url": "http://x/3"}, headers=auth_headers
            ).status_code
            == 400
        )

    @patch("routes.recommendations.JobRecommender")
    def test_analyze_returns_error(self, mock_cls, client, auth_headers):
        mock_cls.return_value.analyze_job_for_user.return_value = {"error": "Could not scrape"}
        assert (
            client.post(
                "/api/recommendations/analyze", json={"job_url": "http://x/4"}, headers=auth_headers
            ).status_code
            == 400
        )


class TestAnalyzeManualJob:
    """Tests for POST /api/recommendations/analyze-manual"""

    def test_requires_auth(self, client):
        assert client.post("/api/recommendations/analyze-manual", json={"job_text": "x" * 200}).status_code == 401

    def test_missing_job_text(self, client, auth_headers):
        assert client.post("/api/recommendations/analyze-manual", json={}, headers=auth_headers).status_code == 400

    def test_job_text_too_short(self, client, auth_headers):
        r = client.post("/api/recommendations/analyze-manual", json={"job_text": "Short"}, headers=auth_headers)
        assert r.status_code == 400

    @patch("routes.recommendations.JobRecommender")
    def test_success(self, mock_cls, client, auth_headers):
        mock = mock_cls.return_value
        mock.analyze_manual_job_for_user.return_value = {
            "fit_score": 75,
            "fit_category": "gut",
            "job_data": {"title": "D"},
        }
        mock.create_recommendation.return_value = MagicMock(id=1)
        mock_cls.MIN_FIT_SCORE = 60
        assert (
            client.post(
                "/api/recommendations/analyze-manual", json={"job_text": "x" * 200}, headers=auth_headers
            ).status_code
            == 200
        )

    @patch("routes.recommendations.JobRecommender")
    def test_returns_none(self, mock_cls, client, auth_headers):
        mock_cls.return_value.analyze_manual_job_for_user.return_value = None
        assert (
            client.post(
                "/api/recommendations/analyze-manual", json={"job_text": "x" * 200}, headers=auth_headers
            ).status_code
            == 400
        )

    @patch("routes.recommendations.JobRecommender")
    def test_returns_error(self, mock_cls, client, auth_headers):
        mock_cls.return_value.analyze_manual_job_for_user.return_value = {"error": "fail"}
        assert (
            client.post(
                "/api/recommendations/analyze-manual", json={"job_text": "x" * 200}, headers=auth_headers
            ).status_code
            == 400
        )


class TestGetRecommendation:
    """Tests for GET /api/recommendations/<id>"""

    def test_requires_auth(self, client):
        assert client.get("/api/recommendations/1").status_code == 401

    def test_not_found(self, client, auth_headers):
        assert client.get("/api/recommendations/9999", headers=auth_headers).status_code == 404

    def test_returns_recommendation(self, app, client, test_user, auth_headers):
        with app.app_context():
            rec = _create_recommendation(test_user["id"])
            db.session.commit()
            rid = rec.id
        assert (
            client.get(f"/api/recommendations/{rid}", headers=auth_headers).get_json()["recommendation"]["fit_score"]
            == 80
        )


class TestDismissRecommendation:
    """Tests for POST /api/recommendations/<id>/dismiss"""

    def test_requires_auth(self, client):
        assert client.post("/api/recommendations/1/dismiss").status_code == 401

    @patch("routes.recommendations.JobRecommender")
    def test_not_found(self, mock_cls, client, auth_headers):
        mock_cls.return_value.dismiss_recommendation.return_value = False
        assert client.post("/api/recommendations/9999/dismiss", headers=auth_headers).status_code == 404

    @patch("routes.recommendations.JobRecommender")
    def test_success(self, mock_cls, client, auth_headers):
        mock_cls.return_value.dismiss_recommendation.return_value = True
        assert client.post("/api/recommendations/1/dismiss", headers=auth_headers).status_code == 200


class TestMarkApplied:
    """Tests for POST /api/recommendations/<id>/apply"""

    def test_requires_auth(self, client):
        assert client.post("/api/recommendations/1/apply").status_code == 401

    @patch("routes.recommendations.JobRecommender")
    def test_not_found(self, mock_cls, client, auth_headers):
        mock_cls.return_value.mark_as_applied.return_value = False
        assert client.post("/api/recommendations/9999/apply", json={}, headers=auth_headers).status_code == 404

    @patch("routes.recommendations.JobRecommender")
    def test_success(self, mock_cls, client, auth_headers):
        mock_cls.return_value.mark_as_applied.return_value = True
        assert (
            client.post("/api/recommendations/1/apply", json={"application_id": 42}, headers=auth_headers).status_code
            == 200
        )


class TestDeleteRecommendation:
    """Tests for DELETE /api/recommendations/<id>"""

    def test_requires_auth(self, client):
        assert client.delete("/api/recommendations/1").status_code == 401

    def test_not_found(self, client, auth_headers):
        assert client.delete("/api/recommendations/9999", headers=auth_headers).status_code == 404

    def test_success(self, app, client, test_user, auth_headers):
        with app.app_context():
            rec = _create_recommendation(test_user["id"])
            db.session.commit()
            rid = rec.id
        assert client.delete(f"/api/recommendations/{rid}", headers=auth_headers).status_code == 200
