"""
Tests for the applications blueprint (/api/applications).

Covers:
- List applications (pagination, user isolation)
- Get single application
- Update application (status, notes)
- Delete application
- Quick-extract from URL
- Preview job from URL
- Generate from URL
- Generate from text
- Analyze manual text
- Export (CSV, PDF)
- Subscription limit enforcement
"""

from unittest.mock import MagicMock, patch

import pytest

from models import Application, db

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_application(app, test_user):
    """Create a single test application in the database."""
    with app.app_context():
        record = Application(
            user_id=test_user["id"],
            firma="Test GmbH",
            position="Entwickler",
            status="erstellt",
            email="hr@test.com",
            quelle="https://example.com/job",
        )
        db.session.add(record)
        db.session.commit()
        return {"id": record.id, "firma": "Test GmbH", "position": "Entwickler"}


@pytest.fixture
def multiple_applications(app, test_user):
    """Create several applications for pagination / list tests."""
    with app.app_context():
        ids = []
        for i in range(5):
            record = Application(
                user_id=test_user["id"],
                firma=f"Firma {i}",
                position=f"Position {i}",
                status="erstellt",
            )
            db.session.add(record)
            db.session.flush()
            ids.append(record.id)
        db.session.commit()
        return ids


@pytest.fixture
def other_user_application(app):
    """Create an application belonging to a different user."""
    from models import User

    with app.app_context():
        other = User(email="other@example.com", full_name="Other User")
        other.set_password("OtherPass123")
        db.session.add(other)
        db.session.flush()

        record = Application(
            user_id=other.id,
            firma="Andere GmbH",
            position="Manager",
            status="erstellt",
        )
        db.session.add(record)
        db.session.commit()
        return {"id": record.id, "user_id": other.id}


# ===========================================================================
# 1. List Applications
# ===========================================================================


class TestListApplications:
    """GET /api/applications"""

    def test_empty_list(self, client, auth_headers):
        response = client.get("/api/applications", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["total"] == 0
        assert data["applications"] == []

    def test_returns_applications(self, client, auth_headers, multiple_applications):
        response = client.get("/api/applications", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 5
        assert len(data["applications"]) == 5

    def test_pagination(self, client, auth_headers, multiple_applications):
        response = client.get("/api/applications?page=1&per_page=2", headers=auth_headers)
        data = response.get_json()
        assert data["total"] == 5
        assert len(data["applications"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["pages"] == 3

    def test_only_own_applications(self, client, auth_headers, test_application, other_user_application):
        response = client.get("/api/applications", headers=auth_headers)
        data = response.get_json()
        assert data["total"] == 1
        assert data["applications"][0]["firma"] == "Test GmbH"

    def test_requires_auth(self, client):
        response = client.get("/api/applications")
        assert response.status_code == 401


# ===========================================================================
# 2. Get Application
# ===========================================================================


class TestGetApplication:
    """GET /api/applications/<id>"""

    def test_get_existing(self, client, auth_headers, test_application):
        app_id = test_application["id"]
        response = client.get(f"/api/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["application"]["firma"] == "Test GmbH"
        assert data["application"]["position"] == "Entwickler"

    def test_not_found(self, client, auth_headers):
        response = client.get("/api/applications/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_other_users_application(self, client, auth_headers, other_user_application):
        app_id = other_user_application["id"]
        response = client.get(f"/api/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 404


# ===========================================================================
# 3. Update Application
# ===========================================================================


class TestUpdateApplication:
    """PUT /api/applications/<id>"""

    def test_update_status(self, client, auth_headers, test_application):
        app_id = test_application["id"]
        response = client.put(
            f"/api/applications/{app_id}",
            json={"status": "versendet"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["application"]["status"] == "versendet"
        # Status history should include the new entry
        history = data["application"]["status_history"]
        assert any(h["status"] == "versendet" for h in history)

    def test_update_notizen(self, client, auth_headers, test_application):
        app_id = test_application["id"]
        response = client.put(
            f"/api/applications/{app_id}",
            json={"notizen": "Telefonat am Montag"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["application"]["notizen"] == "Telefonat am Montag"

    def test_update_nonexistent(self, client, auth_headers):
        response = client.put(
            "/api/applications/99999",
            json={"status": "versendet"},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===========================================================================
# 4. Delete Application
# ===========================================================================


class TestDeleteApplication:
    """DELETE /api/applications/<id>"""

    def test_delete_existing(self, client, auth_headers, test_application, app):
        app_id = test_application["id"]
        response = client.delete(f"/api/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["success"] is True

        # Verify deleted
        with app.app_context():
            assert Application.query.get(app_id) is None

    def test_delete_nonexistent(self, client, auth_headers):
        response = client.delete("/api/applications/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_other_users_application(self, client, auth_headers, other_user_application):
        app_id = other_user_application["id"]
        response = client.delete(f"/api/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 404


# ===========================================================================
# 5. Quick-Extract
# ===========================================================================


class TestQuickExtract:
    """POST /api/applications/quick-extract"""

    def test_missing_url(self, client, auth_headers):
        response = client.post(
            "/api/applications/quick-extract",
            json={"url": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.get_json()["success"] is False

    def test_invalid_url(self, client, auth_headers):
        response = client.post(
            "/api/applications/quick-extract",
            json={"url": "not-a-url"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.applications.scraping.WebScraper")
    def test_success(self, mock_scraper_class, client, auth_headers):
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = {
            "company": "Test GmbH",
            "title": "Python Developer",
        }
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/quick-extract",
            json={"url": "https://www.stepstone.de/job/123"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["company"] == "Test GmbH"
        assert data["data"]["title"] == "Python Developer"
        assert data["data"]["portal"] == "StepStone"

    @patch("routes.applications.scraping.WebScraper")
    def test_empty_extraction(self, mock_scraper_class, client, auth_headers):
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = None
        mock_scraper.fetch_structured_job_posting.return_value = {
            "company": "",
            "title": "",
        }
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/quick-extract",
            json={"url": "https://example.com/not-a-job"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.get_json()["success"] is False


# ===========================================================================
# 6. Preview Job
# ===========================================================================


class TestPreviewJob:
    """POST /api/applications/preview-job"""

    def test_missing_url(self, client, auth_headers):
        response = client.post(
            "/api/applications/preview-job",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_url(self, client, auth_headers):
        response = client.post(
            "/api/applications/preview-job",
            json={"url": "ftp://bad"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.applications.scraping.WebScraper")
    def test_success(self, mock_scraper_class, client, auth_headers):
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "indeed"
        mock_scraper.fetch_structured_job_posting.return_value = {
            "title": "Backend Engineer",
            "company": "Startup AG",
            "location": "München",
            "description": "Wir suchen jemanden...",
        }
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": "https://de.indeed.com/viewjob?jk=abc123"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["company"] == "Startup AG"
        assert data["portal"] == "Indeed"

    @patch("routes.applications.scraping.WebScraper")
    def test_empty_scrape(self, mock_scraper_class, client, auth_headers):
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = None
        mock_scraper.fetch_structured_job_posting.return_value = {
            "title": "",
            "company": "",
            "description": "",
            "text": "",
        }
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": "https://example.com/nothing"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.get_json()["success"] is False


# ===========================================================================
# 7. Generate from URL
# ===========================================================================


class TestGenerateFromUrl:
    """POST /api/applications/generate-from-url"""

    def test_missing_url(self, client, auth_headers):
        response = client.post(
            "/api/applications/generate-from-url",
            json={"url": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_url(self, client, auth_headers):
        response = client.post(
            "/api/applications/generate-from-url",
            json={"url": "not-valid"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.applications.generation.calculate_and_store_job_fit")
    @patch("routes.applications.generation.get_subscription_usage")
    @patch("routes.applications.generation.BewerbungsGenerator")
    @patch("routes.applications.generation.WebScraper")
    def test_success_with_user_data(
        self,
        mock_scraper_class,
        mock_gen_class,
        mock_usage,
        mock_job_fit,
        client,
        auth_headers,
        app,
        test_user,
    ):
        """Generate using user-edited preview data (company + description provided)."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        mock_gen = MagicMock()
        mock_gen.generate_bewerbung.return_value = "/tmp/test.pdf"
        mock_gen.warnings = []
        mock_gen_class.return_value = mock_gen

        mock_usage.return_value = {
            "plan": "free",
            "limit": 3,
            "used": 1,
            "remaining": 2,
            "unlimited": False,
        }

        # Pre-create the application the generator would normally produce
        with app.app_context():
            test_app = Application(
                user_id=test_user["id"],
                firma="Test GmbH",
                position="Developer",
                status="erstellt",
            )
            db.session.add(test_app)
            db.session.commit()

        response = client.post(
            "/api/applications/generate-from-url",
            json={
                "url": "https://example.com/job",
                "company": "Test GmbH",
                "description": "A job description that is reasonably long",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["pdf_path"] == "/tmp/test.pdf"
        mock_gen.generate_bewerbung.assert_called_once()

    @patch("routes.applications.generation.calculate_and_store_job_fit")
    @patch("routes.applications.generation.get_subscription_usage")
    @patch("routes.applications.generation.BewerbungsGenerator")
    @patch("routes.applications.generation.WebScraper")
    def test_success_scrape_flow(
        self,
        mock_scraper_class,
        mock_gen_class,
        mock_usage,
        mock_job_fit,
        client,
        auth_headers,
        app,
        test_user,
    ):
        """Generate with URL scraping (no user-edited company/description)."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_job_posting.return_value = {
            "text": "Wir suchen einen Entwickler...",
            "company": "Scraped GmbH",
        }
        mock_scraper_class.return_value = mock_scraper

        mock_gen = MagicMock()
        mock_gen.generate_bewerbung.return_value = "/tmp/scraped.pdf"
        mock_gen.warnings = []
        mock_gen_class.return_value = mock_gen

        mock_usage.return_value = {
            "plan": "free",
            "limit": 3,
            "used": 0,
            "remaining": 3,
            "unlimited": False,
        }

        # Pre-create application
        with app.app_context():
            test_app = Application(
                user_id=test_user["id"],
                firma="Scraped GmbH",
                position="Entwickler",
                status="erstellt",
            )
            db.session.add(test_app)
            db.session.commit()

        response = client.post(
            "/api/applications/generate-from-url",
            json={"url": "https://example.com/job"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["success"] is True

    @patch("routes.applications.generation.WebScraper")
    def test_scrape_returns_empty(self, mock_scraper_class, client, auth_headers):
        """Should return 400 when scraper returns no text."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_job_posting.return_value = {"text": "", "company": ""}
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/generate-from-url",
            json={"url": "https://example.com/empty"},
            headers=auth_headers,
        )
        assert response.status_code == 400


# ===========================================================================
# 8. Generate from Text
# ===========================================================================


class TestGenerateFromText:
    """POST /api/applications/generate-from-text"""

    def test_missing_text(self, client, auth_headers):
        response = client.post(
            "/api/applications/generate-from-text",
            json={"job_text": "", "company": "Test GmbH"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_text_too_short(self, client, auth_headers):
        response = client.post(
            "/api/applications/generate-from-text",
            json={"job_text": "Zu kurz", "company": "Test GmbH"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_company(self, client, auth_headers):
        long_text = "A" * 150
        response = client.post(
            "/api/applications/generate-from-text",
            json={"job_text": long_text, "company": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.applications.generation.calculate_and_store_job_fit")
    @patch("routes.applications.generation.get_subscription_usage")
    @patch("routes.applications.generation.BewerbungsGenerator")
    def test_success(
        self,
        mock_gen_class,
        mock_usage,
        mock_job_fit,
        client,
        auth_headers,
        app,
        test_user,
    ):
        mock_gen = MagicMock()
        mock_gen.generate_bewerbung.return_value = "/tmp/text.pdf"
        mock_gen.warnings = []
        mock_gen_class.return_value = mock_gen

        mock_usage.return_value = {
            "plan": "free",
            "limit": 3,
            "used": 0,
            "remaining": 3,
            "unlimited": False,
        }

        # Pre-create application
        with app.app_context():
            test_app = Application(
                user_id=test_user["id"],
                firma="Manual GmbH",
                position="Tester",
                status="erstellt",
            )
            db.session.add(test_app)
            db.session.commit()

        long_text = "Wir suchen einen erfahrenen Software-Entwickler " * 10
        response = client.post(
            "/api/applications/generate-from-text",
            json={
                "job_text": long_text,
                "company": "Manual GmbH",
                "title": "Software-Entwickler",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["pdf_path"] == "/tmp/text.pdf"


# ===========================================================================
# 9. Analyze Manual Text
# ===========================================================================


class TestAnalyzeManualText:
    """POST /api/applications/analyze-manual-text"""

    def test_missing_text(self, client, auth_headers):
        response = client.post(
            "/api/applications/analyze-manual-text",
            json={"job_text": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_text_too_short(self, client, auth_headers):
        response = client.post(
            "/api/applications/analyze-manual-text",
            json={"job_text": "Kurz"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.applications.scraping.ContactExtractor")
    def test_success(self, mock_extractor_class, client, auth_headers):
        mock_extractor = MagicMock()
        mock_extractor.extract_contact_data.return_value = {
            "contact_email": "jobs@firma.de",
            "contact_person": "Herr Schmidt",
            "location": "Hamburg",
            "employment_type": "FULL_TIME",
        }
        mock_extractor_class.return_value = mock_extractor

        long_text = (
            "Software Engineer (m/w/d)\n"
            "MegaCorp GmbH\n" + "Wir suchen einen erfahrenen Entwickler für unser Team. " * 10
        )
        response = client.post(
            "/api/applications/analyze-manual-text",
            json={"job_text": long_text},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["is_manual"] is True
        assert data["data"]["portal"] == "Manuell eingegeben"
        assert data["data"]["contact_email"] == "jobs@firma.de"

    @patch("routes.applications.scraping.ContactExtractor")
    def test_with_company_and_title(self, mock_extractor_class, client, auth_headers):
        mock_extractor = MagicMock()
        mock_extractor.extract_contact_data.return_value = {}
        mock_extractor_class.return_value = mock_extractor

        long_text = "Wir suchen einen Entwickler. " * 15
        response = client.post(
            "/api/applications/analyze-manual-text",
            json={
                "job_text": long_text,
                "company": "Provided GmbH",
                "title": "Senior Dev",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["company"] == "Provided GmbH"
        assert data["title"] == "Senior Dev"


# ===========================================================================
# 10. Export
# ===========================================================================


class TestExportApplications:
    """GET /api/applications/export"""

    def test_csv_export_empty(self, client, auth_headers):
        response = client.get("/api/applications/export?format=csv", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.content_type

    def test_csv_export_with_data(self, client, auth_headers, test_application):
        response = client.get("/api/applications/export?format=csv", headers=auth_headers)
        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert "Test GmbH" in content
        assert "Entwickler" in content

    def test_pdf_export(self, client, auth_headers):
        response = client.get("/api/applications/export?format=pdf", headers=auth_headers)
        assert response.status_code == 200
        assert "application/pdf" in response.content_type

    def test_csv_export_with_search_filter(self, client, auth_headers, multiple_applications):
        response = client.get(
            "/api/applications/export?format=csv&search=Firma%201",
            headers=auth_headers,
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert "Firma 1" in content

    def test_csv_export_with_status_filter(self, client, auth_headers, test_application):
        response = client.get(
            "/api/applications/export?format=csv&status=erstellt",
            headers=auth_headers,
        )
        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert "Test GmbH" in content


# ===========================================================================
# 11. Subscription Limit
# ===========================================================================


class TestSubscriptionLimit:
    """Verify that @check_subscription_limit blocks users with no credits."""

    def test_limit_reached_generate_from_url(self, client, auth_headers, app, test_user):
        """User with 0 credits should be blocked."""
        from models import User

        with app.app_context():
            user = db.session.get(User, test_user["id"])
            user.credits_remaining = 0
            db.session.commit()

        response = client.post(
            "/api/applications/generate-from-url",
            json={"url": "https://example.com/job"},
            headers=auth_headers,
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data["error_code"] == "SUBSCRIPTION_LIMIT_REACHED"

    def test_limit_reached_generate_from_text(self, client, auth_headers, app, test_user):
        from models import User

        with app.app_context():
            user = db.session.get(User, test_user["id"])
            user.credits_remaining = 0
            db.session.commit()

        long_text = "A" * 150
        response = client.post(
            "/api/applications/generate-from-text",
            json={"job_text": long_text, "company": "X GmbH"},
            headers=auth_headers,
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data["error_code"] == "SUBSCRIPTION_LIMIT_REACHED"


# ===========================================================================
# 12. Timeline
# ===========================================================================


class TestTimeline:
    """GET /api/applications/timeline"""

    def test_empty_timeline(self, client, auth_headers):
        response = client.get("/api/applications/timeline", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["total"] == 0

    def test_timeline_with_data(self, client, auth_headers, test_application):
        response = client.get("/api/applications/timeline", headers=auth_headers)
        data = response.get_json()
        assert data["data"]["total"] == 1
        app_data = data["data"]["applications"][0]
        assert app_data["firma"] == "Test GmbH"
        # Should have fallback status_history
        assert len(app_data["status_history"]) >= 1

    def test_timeline_with_days_filter(self, client, auth_headers, test_application):
        response = client.get("/api/applications/timeline?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["filter"] == "7"


# ===========================================================================
# 13. Auth Required
# ===========================================================================


class TestAuthRequired:
    """Endpoints should return 401 without a valid token."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/api/applications"),
            ("GET", "/api/applications/1"),
            ("PUT", "/api/applications/1"),
            ("DELETE", "/api/applications/1"),
            ("POST", "/api/applications/quick-extract"),
            ("POST", "/api/applications/preview-job"),
            ("POST", "/api/applications/generate-from-url"),
            ("POST", "/api/applications/generate-from-text"),
            ("POST", "/api/applications/analyze-manual-text"),
            ("GET", "/api/applications/export"),
            ("GET", "/api/applications/timeline"),
        ],
    )
    def test_requires_auth(self, client, method, path):
        fn = getattr(client, method.lower())
        response = fn(path)
        assert response.status_code == 401
