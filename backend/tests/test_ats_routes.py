"""
Tests for ATS (Applicant Tracking System) API routes.
"""

import json
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models import ATSAnalysis, Document, User, db


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
            "suggestions": [{"content": "Docker Erfahrung hinzufügen", "priority": "high"}],
            "categories": {
                "hard_skills": {
                    "matched": ["Python"],
                    "missing": ["Docker"],
                },
                "soft_skills": {"matched": [], "missing": []},
                "qualifications": {"matched": [], "missing": []},
                "experience": {
                    "matched": ["Entwickler"],
                    "missing": [],
                },
            },
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
        # Check categories are included in response
        assert "categories" in data["data"]
        assert "hard_skills" in data["data"]["categories"]
        assert "Python" in data["data"]["categories"]["hard_skills"]["matched"]
        # Check suggestions have priority
        assert data["data"]["suggestions"][0]["priority"] == "high"

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
            "suggestions": [{"content": "TypeScript lernen", "priority": "medium"}],
            "categories": {
                "hard_skills": {
                    "matched": ["React", "Node.js"],
                    "missing": ["TypeScript"],
                },
                "soft_skills": {"matched": [], "missing": []},
                "qualifications": {"matched": [], "missing": []},
                "experience": {"matched": [], "missing": []},
            },
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
            "categories": {
                "hard_skills": {"matched": [], "missing": []},
                "soft_skills": {"matched": [], "missing": []},
                "qualifications": {"matched": [], "missing": []},
                "experience": {"matched": [], "missing": []},
            },
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

    def test_analyze_saves_result_to_database(self, app, client, test_user, auth_headers):
        """Test that successful analysis is saved to database."""
        with app.app_context():
            user = User.query.get(test_user["id"])

            user_dir = os.path.join(app.config.get("UPLOAD_FOLDER", "/tmp"), f"user_{user.id}", "documents")
            os.makedirs(user_dir, exist_ok=True)
            cv_path = os.path.join(user_dir, "lebenslauf.txt")

            with open(cv_path, "w", encoding="utf-8") as f:
                f.write("Python Developer with 5 years experience.")

            document = Document(
                user_id=user.id,
                doc_type="lebenslauf",
                file_path=cv_path,
                original_filename="cv.pdf",
            )
            db.session.add(document)
            db.session.commit()

        mock_result = {
            "score": 85,
            "matched_keywords": ["Python"],
            "missing_keywords": [],
            "suggestions": [],
            "categories": {
                "hard_skills": {"matched": ["Python"], "missing": []},
                "soft_skills": {"matched": [], "missing": []},
                "qualifications": {"matched": [], "missing": []},
                "experience": {"matched": [], "missing": []},
            },
        }

        with patch("routes.ats.ATSService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_cv_against_job.return_value = mock_result
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/ats/analyze",
                json={"job_text": "Looking for Python developer"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "analysis_id" in data["data"]
        assert data["data"]["cached"] is False

        # Verify saved in database
        with app.app_context():
            analysis = ATSAnalysis.query.get(data["data"]["analysis_id"])
            assert analysis is not None
            assert analysis.score == 85
            assert analysis.user_id == test_user["id"]

    def test_analyze_returns_cached_result_for_same_url(self, app, client, test_user, auth_headers):
        """Test that same URL within 24h returns cached result."""
        job_url = "https://example.com/cached-job"

        # Create cached analysis
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

            cached_result = {
                "score": 70,
                "matched_keywords": ["cached"],
                "missing_keywords": [],
                "suggestions": [],
                "categories": {
                    "hard_skills": {"matched": [], "missing": []},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
            }

            analysis = ATSAnalysis(
                user_id=user.id,
                job_url=job_url,
                score=70,
                result_json=json.dumps(cached_result),
                created_at=datetime.utcnow() - timedelta(hours=1),  # 1 hour ago
            )
            db.session.add(analysis)
            db.session.commit()

        # Request should return cached result without calling ATSService
        with patch("routes.ats.ATSService") as mock_service_class:
            response = client.post(
                "/api/ats/analyze",
                json={"job_url": job_url},
                headers=auth_headers,
            )

            # ATSService should NOT be called because we have cached result
            mock_service_class.assert_not_called()

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["cached"] is True
        assert data["data"]["score"] == 70


class TestATSHistory:
    """Tests for GET /api/ats/history endpoint."""

    def test_history_requires_authentication(self, client):
        """Test that /api/ats/history requires JWT authentication."""
        response = client.get("/api/ats/history")
        assert response.status_code == 401

    def test_history_returns_empty_list(self, client, auth_headers):
        """Test that history returns empty list when no analyses exist."""
        response = client.get("/api/ats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["analyses"] == []

    def test_history_returns_user_analyses(self, app, client, test_user, auth_headers):
        """Test that history returns user's analyses."""
        with app.app_context():
            result_json = json.dumps(
                {
                    "score": 75,
                    "matched_keywords": ["Python", "Django"],
                    "missing_keywords": ["Docker"],
                    "suggestions": [],
                    "categories": {},
                }
            )

            analysis1 = ATSAnalysis(
                user_id=test_user["id"],
                job_url="https://example.com/job1",
                score=75,
                result_json=result_json,
            )
            analysis2 = ATSAnalysis(
                user_id=test_user["id"],
                job_url="https://example.com/job2",
                score=80,
                result_json=result_json,
            )
            db.session.add_all([analysis1, analysis2])
            db.session.commit()

        response = client.get("/api/ats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]["analyses"]) == 2

    def test_history_returns_max_20_analyses(self, app, client, test_user, auth_headers):
        """Test that history returns maximum 20 analyses."""
        with app.app_context():
            result_json = json.dumps({"score": 50, "matched_keywords": [], "missing_keywords": [], "suggestions": []})

            for i in range(25):
                analysis = ATSAnalysis(
                    user_id=test_user["id"],
                    job_url=f"https://example.com/job{i}",
                    score=50 + i,
                    result_json=result_json,
                )
                db.session.add(analysis)
            db.session.commit()

        response = client.get("/api/ats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]["analyses"]) == 20

    def test_history_ordered_by_date_desc(self, app, client, test_user, auth_headers):
        """Test that history is ordered by created_at descending."""
        with app.app_context():
            result_json = json.dumps({"score": 50, "matched_keywords": [], "missing_keywords": [], "suggestions": []})

            old_analysis = ATSAnalysis(
                user_id=test_user["id"],
                job_url="https://example.com/old",
                score=50,
                result_json=result_json,
                created_at=datetime.utcnow() - timedelta(days=1),
            )
            new_analysis = ATSAnalysis(
                user_id=test_user["id"],
                job_url="https://example.com/new",
                score=90,
                result_json=result_json,
                created_at=datetime.utcnow(),
            )
            db.session.add_all([old_analysis, new_analysis])
            db.session.commit()

        response = client.get("/api/ats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        analyses = data["data"]["analyses"]
        assert analyses[0]["score"] == 90  # Newest first
        assert analyses[1]["score"] == 50

    def test_history_does_not_show_other_users_analyses(self, app, client, test_user, auth_headers):
        """Test that history only shows current user's analyses."""
        with app.app_context():
            # Create another user and their analysis
            other_user = User(email="other@example.com", full_name="Other User")
            other_user.set_password("password123")
            db.session.add(other_user)
            db.session.commit()

            result_json = json.dumps({"score": 50, "matched_keywords": [], "missing_keywords": [], "suggestions": []})

            other_analysis = ATSAnalysis(
                user_id=other_user.id,
                job_url="https://example.com/other",
                score=99,
                result_json=result_json,
            )
            my_analysis = ATSAnalysis(
                user_id=test_user["id"],
                job_url="https://example.com/mine",
                score=75,
                result_json=result_json,
            )
            db.session.add_all([other_analysis, my_analysis])
            db.session.commit()

        response = client.get("/api/ats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]["analyses"]) == 1
        assert data["data"]["analyses"][0]["score"] == 75


class TestATSHistoryDetail:
    """Tests for GET /api/ats/history/<id> endpoint."""

    def test_history_detail_requires_authentication(self, client):
        """Test that /api/ats/history/<id> requires JWT authentication."""
        response = client.get("/api/ats/history/1")
        assert response.status_code == 401

    def test_history_detail_returns_404_for_nonexistent(self, client, auth_headers):
        """Test that nonexistent analysis returns 404."""
        response = client.get("/api/ats/history/99999", headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert "nicht gefunden" in data["error"]

    def test_history_detail_returns_full_analysis(self, app, client, test_user, auth_headers):
        """Test that history detail returns full analysis result."""
        with app.app_context():
            result_data = {
                "score": 85,
                "matched_keywords": ["Python", "Django"],
                "missing_keywords": ["Docker"],
                "suggestions": [{"content": "Add Docker", "priority": "high"}],
                "categories": {
                    "hard_skills": {"matched": ["Python", "Django"], "missing": ["Docker"]},
                    "soft_skills": {"matched": [], "missing": []},
                    "qualifications": {"matched": [], "missing": []},
                    "experience": {"matched": [], "missing": []},
                },
            }

            analysis = ATSAnalysis(
                user_id=test_user["id"],
                job_url="https://example.com/job",
                score=85,
                result_json=json.dumps(result_data),
            )
            db.session.add(analysis)
            db.session.commit()
            analysis_id = analysis.id

        response = client.get(f"/api/ats/history/{analysis_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["score"] == 85
        assert data["data"]["job_url"] == "https://example.com/job"
        assert "result" in data["data"]
        assert data["data"]["result"]["matched_keywords"] == ["Python", "Django"]

    def test_history_detail_returns_404_for_other_users_analysis(self, app, client, test_user, auth_headers):
        """Test that trying to access other user's analysis returns 404."""
        with app.app_context():
            other_user = User(email="other2@example.com", full_name="Other User")
            other_user.set_password("password123")
            db.session.add(other_user)
            db.session.commit()

            result_json = json.dumps({"score": 50, "matched_keywords": [], "missing_keywords": [], "suggestions": []})

            other_analysis = ATSAnalysis(
                user_id=other_user.id,
                job_url="https://example.com/secret",
                score=99,
                result_json=result_json,
            )
            db.session.add(other_analysis)
            db.session.commit()
            other_analysis_id = other_analysis.id

        response = client.get(f"/api/ats/history/{other_analysis_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
