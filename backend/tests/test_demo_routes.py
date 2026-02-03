"""
Tests for Demo API routes.
"""

from unittest.mock import MagicMock, patch


class TestDemoGenerate:
    """Tests for POST /api/demo/generate endpoint."""

    def test_generate_does_not_require_authentication(self, client):
        """Test that /api/demo/generate is accessible without authentication."""
        with patch("routes.demo.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = {
                "text": "We are looking for a Senior Python Developer...",
                "company": "Test GmbH",
            }
            mock_scraper.extract_company_name_from_url.return_value = "Test GmbH"
            mock_scraper_class.return_value = mock_scraper

            with patch("routes.demo.DemoGenerator") as mock_generator_class:
                mock_generator = MagicMock()
                mock_generator.generate_demo.return_value = {
                    "einleitung": "Sehr geehrte Damen und Herren...",
                    "position": "Senior Python Developer",
                    "company": "Test GmbH",
                    "ansprechpartner": "Sehr geehrte Damen und Herren",
                    "sample_cv_name": "Max Mustermann",
                }
                mock_generator_class.return_value = mock_generator

                response = client.post(
                    "/api/demo/generate",
                    json={"job_url": "https://example.com/job"},
                )

                # Should not return 401 (not authenticated)
                assert response.status_code != 401

    def test_generate_returns_400_without_job_url(self, client):
        """Test that missing job_url returns 400."""
        response = client.post(
            "/api/demo/generate",
            json={},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "job_url ist erforderlich" in data["error"]

    def test_generate_returns_400_with_empty_job_url(self, client):
        """Test that empty job_url returns 400."""
        response = client.post(
            "/api/demo/generate",
            json={"job_url": ""},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "job_url ist erforderlich" in data["error"]

    def test_generate_returns_400_with_invalid_url(self, client):
        """Test that invalid URL format returns 400."""
        response = client.post(
            "/api/demo/generate",
            json={"job_url": "not-a-valid-url"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Ungültige URL" in data["error"]

    def test_generate_success_with_valid_url(self, client):
        """Test successful demo generation with valid URL."""
        with patch("routes.demo.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = {
                "text": "We are looking for a Senior Python Developer with 5 years experience...",
                "company": "TechCorp GmbH",
            }
            mock_scraper.extract_company_name_from_url.return_value = "TechCorp"
            mock_scraper_class.return_value = mock_scraper

            with patch("routes.demo.DemoGenerator") as mock_generator_class:
                mock_generator = MagicMock()
                mock_generator.generate_demo.return_value = {
                    "einleitung": "Mit großem Interesse habe ich Ihre Stellenanzeige gelesen...",
                    "position": "Senior Python Developer",
                    "company": "TechCorp GmbH",
                    "ansprechpartner": "Sehr geehrte Damen und Herren",
                    "sample_cv_name": "Max Mustermann",
                }
                mock_generator_class.return_value = mock_generator

                response = client.post(
                    "/api/demo/generate",
                    json={"job_url": "https://example.com/jobs/python-developer"},
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data["success"] is True
                assert "data" in data
                assert "einleitung" in data["data"]
                assert "position" in data["data"]
                assert "company" in data["data"]
                assert "sample_cv_name" in data["data"]
                assert "demo_note" in data["data"]
                assert "Registriere dich" in data["data"]["demo_note"]

    def test_generate_returns_400_when_scraping_fails_no_text(self, client):
        """Test that empty scraped text returns 400."""
        with patch("routes.demo.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = {
                "text": "",
                "company": None,
            }
            mock_scraper_class.return_value = mock_scraper

            response = client.post(
                "/api/demo/generate",
                json={"job_url": "https://example.com/empty-page"},
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["success"] is False
            assert "Konnte keinen Text von der URL extrahieren" in data["error"]

    def test_generate_handles_scraping_exception(self, client):
        """Test that scraping exceptions are handled gracefully."""
        with patch("routes.demo.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.side_effect = Exception("Connection timeout")
            mock_scraper_class.return_value = mock_scraper

            response = client.post(
                "/api/demo/generate",
                json={"job_url": "https://example.com/timeout"},
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["success"] is False
            assert "konnte nicht geladen werden" in data["error"]

    def test_generate_handles_blocked_site_error(self, client):
        """Test that blocked site errors are handled with friendly message."""
        with patch("routes.demo.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.side_effect = Exception("403 Forbidden - blocked")
            mock_scraper_class.return_value = mock_scraper

            response = client.post(
                "/api/demo/generate",
                json={"job_url": "https://linkedin.com/jobs/123"},
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["success"] is False
            assert "blockiert" in data["error"]

    def test_generate_uses_fallback_company_name_from_url(self, client):
        """Test that company name is extracted from URL if not in scraped data."""
        with patch("routes.demo.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = {
                "text": "We are looking for a developer...",
                "company": None,  # No company in scraped data
            }
            mock_scraper.extract_company_name_from_url.return_value = "ExampleCorp"
            mock_scraper_class.return_value = mock_scraper

            with patch("routes.demo.DemoGenerator") as mock_generator_class:
                mock_generator = MagicMock()
                mock_generator.generate_demo.return_value = {
                    "einleitung": "...",
                    "position": "Developer",
                    "company": "ExampleCorp",
                    "ansprechpartner": "Sehr geehrte Damen und Herren",
                    "sample_cv_name": "Max Mustermann",
                }
                mock_generator_class.return_value = mock_generator

                response = client.post(
                    "/api/demo/generate",
                    json={"job_url": "https://examplecorp.com/careers"},
                )

                assert response.status_code == 200
                # Verify that extract_company_name_from_url was called
                mock_scraper.extract_company_name_from_url.assert_called_once()


class TestDemoGeneratorService:
    """Tests for DemoGenerator service."""

    def test_sample_cv_is_loaded(self):
        """Test that sample CV is loaded correctly."""
        from services.demo_generator import get_sample_cv

        sample_cv = get_sample_cv()
        assert sample_cv is not None
        assert "name" in sample_cv
        assert "cv_text" in sample_cv
        assert len(sample_cv["cv_text"]) > 100

    def test_sample_cv_is_cached(self):
        """Test that sample CV is cached after first load."""
        from services.demo_generator import get_sample_cv

        sample_cv1 = get_sample_cv()
        sample_cv2 = get_sample_cv()
        # Should be the exact same object (cached)
        assert sample_cv1 is sample_cv2

    def test_demo_generator_creates_result(self):
        """Test that DemoGenerator returns expected structure."""
        with patch("services.demo_generator.ClaudeAPIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.extract_bewerbung_details.return_value = {
                "firma": "Test GmbH",
                "ansprechpartner": "Sehr geehrte Damen und Herren",
                "position": "Python Developer",
                "quelle": "Website",
                "email": "",
                "stellenanzeige_kompakt": "Looking for Python dev...",
            }
            mock_client.generate_einleitung.return_value = "Mit großem Interesse..."
            mock_client_class.return_value = mock_client

            from services.demo_generator import DemoGenerator

            generator = DemoGenerator()
            result = generator.generate_demo(
                job_text="Looking for a Python Developer...",
                company_name="Test GmbH",
            )

            assert "einleitung" in result
            assert "position" in result
            assert "company" in result
            assert "sample_cv_name" in result
            assert result["einleitung"] == "Mit großem Interesse..."
            assert result["position"] == "Python Developer"
            assert result["company"] == "Test GmbH"
