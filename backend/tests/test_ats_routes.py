"""
Tests for ATS (Applicant Tracking System) API routes.
"""

import os
from unittest.mock import MagicMock, patch

from models import Document, User, db


class TestATSAnalyze:
    """Tests for POST /api/ats/analyze endpoint."""

    def test_analyze_requires_authentication(self, client):
        """Test that /api/ats/analyze requires JWT authentication."""
        response = client.post(
            "/api/ats/analyze",
            json={"job_text": "Looking for a Python developer"},
        )

        assert response.status_code == 401

    def test_analyze_returns_400_without_job_input(self, client, auth_headers):
        """Test that missing job_url and job_text returns 400."""
        response = client.post(
            "/api/ats/analyze",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "job_url oder job_text ist erforderlich" in data["error"]

    def test_analyze_returns_400_with_empty_job_inputs(self, client, auth_headers):
        """Test that empty job_url and job_text returns 400."""
        response = client.post(
            "/api/ats/analyze",
            json={"job_url": "", "job_text": "   "},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "job_url oder job_text ist erforderlich" in data["error"]

    def test_analyze_returns_400_without_cv(self, client, auth_headers):
        """Test that missing CV returns 400."""
        response = client.post(
            "/api/ats/analyze",
            json={"job_text": "Looking for a Python developer"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Kein Lebenslauf hochgeladen" in data["error"]

    def test_analyze_with_job_text_success(self, app, client, test_user, auth_headers):
        """Test successful analysis with job_text."""
        # Create CV document for user
        with app.app_context():
            user = User.query.get(test_user["id"])

            # Create temp directory and CV file
            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("Erfahrener Python Entwickler mit 5 Jahren Erfahrung.")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        mock_result = {
            "score": 75,
            "matched_keywords": ["Python", "Entwickler"],
            "missing_keywords": ["Docker"],
            "suggestions": ["Docker Erfahrung hinzufügen"],
        }

        with patch("routes.ats.ATSService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_cv_against_job.return_value = mock_result
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/ats/analyze",
                json={"job_text": "Wir suchen Python Entwickler mit Docker Kenntnissen"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["score"] == 75
        assert "Python" in data["data"]["matched_keywords"]
        assert "Docker" in data["data"]["missing_keywords"]

    def test_analyze_with_job_url_success(self, app, client, test_user, auth_headers):
        """Test successful analysis with job_url."""
        # Create CV document for user
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("Senior Developer mit React und Node.js Erfahrung.")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="resume.pdf",
            )
            db.session.add(document)
            db.session.commit()

        mock_scraped = {
            "text": "Fullstack Developer gesucht. React, Node.js, TypeScript erforderlich.",
            "all_links": [],
            "email_links": [],
            "application_links": [],
            "source_url": "https://example.com/job",
        }

        mock_result = {
            "score": 80,
            "matched_keywords": ["React", "Node.js"],
            "missing_keywords": ["TypeScript"],
            "suggestions": ["TypeScript lernen"],
        }

        with patch("routes.ats.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = mock_scraped
            mock_scraper_class.return_value = mock_scraper

            with patch("routes.ats.ATSService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.analyze_cv_against_job.return_value = mock_result
                mock_service_class.return_value = mock_service

                response = client.post(
                    "/api/ats/analyze",
                    json={"job_url": "https://example.com/job"},
                    headers=auth_headers,
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["score"] == 80
        assert data["data"]["job_url"] == "https://example.com/job"

    def test_analyze_with_job_url_scrape_error(self, app, client, test_user, auth_headers):
        """Test that scraping error returns 400."""
        # Create CV document
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("CV content")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        with patch("routes.ats.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.side_effect = Exception("Network error")
            mock_scraper_class.return_value = mock_scraper

            response = client.post(
                "/api/ats/analyze",
                json={"job_url": "https://invalid-url.com/job"},
                headers=auth_headers,
            )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Fehler beim Laden der Job-URL" in data["error"]

    def test_analyze_with_empty_scraped_text(self, app, client, test_user, auth_headers):
        """Test that empty scraped text returns 400."""
        # Create CV document
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("CV content")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        mock_scraped = {
            "text": "",  # Empty text
            "all_links": [],
            "email_links": [],
            "application_links": [],
            "source_url": "https://example.com/job",
        }

        with patch("routes.ats.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = mock_scraped
            mock_scraper_class.return_value = mock_scraper

            response = client.post(
                "/api/ats/analyze",
                json={"job_url": "https://example.com/job"},
                headers=auth_headers,
            )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Konnte keinen Text von der URL extrahieren" in data["error"]

    def test_analyze_cv_file_not_found(self, app, client, test_user, auth_headers):
        """Test that missing CV file returns 400."""
        with app.app_context():
            user = User.query.get(test_user["id"])

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path="/nonexistent/path/cv.txt",
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        response = client.post(
            "/api/ats/analyze",
            json={"job_text": "Job description"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Lebenslauf-Datei nicht gefunden" in data["error"]

    def test_analyze_empty_cv_file(self, app, client, test_user, auth_headers):
        """Test that empty CV file returns 400."""
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            # Create empty CV file
            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("   ")  # Only whitespace

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        response = client.post(
            "/api/ats/analyze",
            json={"job_text": "Job description"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Lebenslauf ist leer" in data["error"]

    def test_analyze_service_error(self, app, client, test_user, auth_headers):
        """Test that ATS service error returns 500."""
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("CV content")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        with patch("routes.ats.ATSService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_cv_against_job.side_effect = Exception("API error")
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/ats/analyze",
                json={"job_text": "Job description"},
                headers=auth_headers,
            )

        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "Analyse fehlgeschlagen" in data["error"]

    def test_analyze_service_value_error(self, app, client, test_user, auth_headers):
        """Test that ATS service ValueError returns 400."""
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("CV content")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        with patch("routes.ats.ATSService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_cv_against_job.side_effect = ValueError("Invalid input")
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/ats/analyze",
                json={"job_text": "Job description"},
                headers=auth_headers,
            )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Invalid input" in data["error"]

    def test_analyze_prefers_job_url_over_job_text(self, app, client, test_user, auth_headers):
        """Test that job_url is used when both job_url and job_text provided."""
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("CV content")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        mock_scraped = {
            "text": "Scraped job description from URL",
            "all_links": [],
            "email_links": [],
            "application_links": [],
            "source_url": "https://example.com/job",
        }

        mock_result = {
            "score": 60,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": [],
        }

        with patch("routes.ats.WebScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.fetch_job_posting.return_value = mock_scraped
            mock_scraper_class.return_value = mock_scraper

            with patch("routes.ats.ATSService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.analyze_cv_against_job.return_value = mock_result
                mock_service_class.return_value = mock_service

                response = client.post(
                    "/api/ats/analyze",
                    json={
                        "job_url": "https://example.com/job",
                        "job_text": "This text should be ignored",
                    },
                    headers=auth_headers,
                )

                # Verify the scraped text was used, not job_text
                call_args = mock_service.analyze_cv_against_job.call_args
                assert "Scraped job description from URL" in call_args[0][1]

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["job_url"] == "https://example.com/job"
