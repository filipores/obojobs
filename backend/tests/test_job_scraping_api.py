"""
API tests for job scraping functionality with German job sites.

Tests the /api/applications/preview-job endpoint with various German job portals:
- StepStone
- Indeed.de
- XING
- Arbeitsagentur
"""

from unittest.mock import MagicMock, patch

# Sample German job site URLs
GERMAN_JOB_URLS = {
    "stepstone": "https://www.stepstone.de/stellenangebote--Software-Engineer-Berlin-TechCorp--12345.html",
    "indeed": "https://de.indeed.com/viewjob?jk=abc123def456",
    "xing": "https://www.xing.com/jobs/berlin-software-developer-123456",
    "arbeitsagentur": "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345678",
}

# Sample scraped job data for mocking
SAMPLE_JOB_DATA = {
    "title": "Software Engineer (m/w/d)",
    "company": "TechCorp GmbH",
    "location": "Berlin, Deutschland",
    "description": "Wir suchen einen erfahrenen Software Engineer...",
    "requirements": "Python, JavaScript, 3+ Jahre Erfahrung",
    "contact_email": "bewerbung@techcorp.de",
    "contact_person": "Frau Müller",
    "posted_date": "2026-01-15",
    "application_deadline": "2026-02-15",
    "employment_type": "FULL_TIME",
    "salary": "60000-80000 EUR",
    "text": "Full job posting text...",
}


class TestPreviewJobEndpoint:
    """Tests for the /api/applications/preview-job endpoint."""

    def test_preview_job_requires_auth(self, client):
        """Should return 401 when no auth token provided."""
        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
        )
        assert response.status_code == 401

    def test_preview_job_requires_url(self, client, auth_headers):
        """Should return 400 when URL is missing."""
        response = client.post(
            "/api/applications/preview-job",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "URL" in data["error"]

    def test_preview_job_rejects_invalid_url(self, client, auth_headers):
        """Should return 400 for invalid URL format."""
        response = client.post(
            "/api/applications/preview-job",
            json={"url": "not-a-valid-url"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_preview_job_rejects_url_without_protocol(self, client, auth_headers):
        """Should return 400 for URL without http:// or https://."""
        response = client.post(
            "/api/applications/preview-job",
            json={"url": "www.stepstone.de/job/12345"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "http" in data["error"].lower()


class TestStepStoneScraping:
    """Tests for scraping StepStone job postings."""

    @patch("routes.applications.WebScraper")
    def test_preview_stepstone_job(self, mock_scraper_class, client, auth_headers):
        """Should successfully scrape StepStone job posting."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = SAMPLE_JOB_DATA
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["portal"] == "StepStone"
        assert data["data"]["portal_id"] == "stepstone"
        assert data["data"]["title"] == SAMPLE_JOB_DATA["title"]
        assert data["data"]["company"] == SAMPLE_JOB_DATA["company"]

    @patch("routes.applications.WebScraper")
    def test_stepstone_returns_all_fields(self, mock_scraper_class, client, auth_headers):
        """Should return all extracted fields from StepStone."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = SAMPLE_JOB_DATA
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        data = response.get_json()["data"]
        assert data["location"] == SAMPLE_JOB_DATA["location"]
        assert data["description"] == SAMPLE_JOB_DATA["description"]
        assert data["requirements"] == SAMPLE_JOB_DATA["requirements"]
        assert data["contact_email"] == SAMPLE_JOB_DATA["contact_email"]
        assert data["contact_person"] == SAMPLE_JOB_DATA["contact_person"]
        assert data["salary"] == SAMPLE_JOB_DATA["salary"]


class TestIndeedScraping:
    """Tests for scraping Indeed.de job postings."""

    @patch("routes.applications.WebScraper")
    def test_preview_indeed_job(self, mock_scraper_class, client, auth_headers):
        """Should successfully scrape Indeed.de job posting."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "indeed"
        mock_scraper.fetch_structured_job_posting.return_value = SAMPLE_JOB_DATA
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["indeed"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["portal"] == "Indeed"
        assert data["data"]["portal_id"] == "indeed"


class TestXingScraping:
    """Tests for scraping XING job postings."""

    @patch("routes.applications.WebScraper")
    def test_preview_xing_job(self, mock_scraper_class, client, auth_headers):
        """Should successfully scrape XING job posting."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "xing"
        mock_scraper.fetch_structured_job_posting.return_value = SAMPLE_JOB_DATA
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["xing"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["portal"] == "XING"
        assert data["data"]["portal_id"] == "xing"


class TestArbeitsagenturScraping:
    """Tests for scraping Arbeitsagentur job postings."""

    @patch("routes.applications.WebScraper")
    def test_preview_arbeitsagentur_job(self, mock_scraper_class, client, auth_headers):
        """Should scrape Arbeitsagentur job posting (generic portal)."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = None  # Not a recognized portal
        mock_scraper.fetch_structured_job_posting.return_value = SAMPLE_JOB_DATA
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["arbeitsagentur"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # Arbeitsagentur is not in the recognized portals, so should be "Sonstige"
        assert data["data"]["portal"] == "Sonstige"
        assert data["data"]["portal_id"] == "generic"


class TestScrapingErrorHandling:
    """Tests for error handling during scraping."""

    @patch("routes.applications.WebScraper")
    def test_handles_empty_response(self, mock_scraper_class, client, auth_headers):
        """Should return 400 when no job data found."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = {"text": "", "title": ""}
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Stellenanzeige" in data["error"]

    @patch("routes.applications.WebScraper")
    def test_handles_403_error(self, mock_scraper_class, client, auth_headers):
        """Should return 400 for 403 Forbidden errors (blocked by site)."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.side_effect = Exception("403 Forbidden")
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        assert response.status_code == 400

    @patch("routes.applications.WebScraper")
    def test_handles_404_error(self, mock_scraper_class, client, auth_headers):
        """Should return 400 for 404 Not Found errors."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.side_effect = Exception("404 Not Found")
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        assert response.status_code == 400

    @patch("routes.applications.WebScraper")
    def test_handles_rate_limiting(self, mock_scraper_class, client, auth_headers):
        """Should return 400 for 429 Too Many Requests errors."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "indeed"
        mock_scraper.fetch_structured_job_posting.side_effect = Exception("429 Too Many Requests")
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["indeed"]},
            headers=auth_headers,
        )

        assert response.status_code == 400

    @patch("routes.applications.WebScraper")
    def test_handles_connection_error(self, mock_scraper_class, client, auth_headers):
        """Should return 500 for connection/server errors."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.side_effect = Exception("Connection refused")
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False


class TestMissingFieldsDetection:
    """Tests for detecting missing fields in scraped data."""

    @patch("routes.applications.WebScraper")
    def test_reports_missing_title(self, mock_scraper_class, client, auth_headers):
        """Should report missing title field."""
        job_data = {**SAMPLE_JOB_DATA, "title": None}
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = job_data
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        data = response.get_json()
        assert "Titel" in data["data"]["missing_fields"]

    @patch("routes.applications.WebScraper")
    def test_reports_missing_company(self, mock_scraper_class, client, auth_headers):
        """Should report missing company field."""
        job_data = {**SAMPLE_JOB_DATA, "company": None}
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = job_data
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        data = response.get_json()
        assert "Firma" in data["data"]["missing_fields"]

    @patch("routes.applications.WebScraper")
    def test_reports_missing_description(self, mock_scraper_class, client, auth_headers):
        """Should report missing description field."""
        job_data = {**SAMPLE_JOB_DATA, "description": None}
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = job_data
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        data = response.get_json()
        assert "Beschreibung" in data["data"]["missing_fields"]

    @patch("routes.applications.WebScraper")
    def test_no_missing_fields_when_complete(self, mock_scraper_class, client, auth_headers):
        """Should report empty missing_fields when all fields present."""
        mock_scraper = MagicMock()
        mock_scraper.detect_job_board.return_value = "stepstone"
        mock_scraper.fetch_structured_job_posting.return_value = SAMPLE_JOB_DATA
        mock_scraper_class.return_value = mock_scraper

        response = client.post(
            "/api/applications/preview-job",
            json={"url": GERMAN_JOB_URLS["stepstone"]},
            headers=auth_headers,
        )

        data = response.get_json()
        assert data["data"]["missing_fields"] == []
