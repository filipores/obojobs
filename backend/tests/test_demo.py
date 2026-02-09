"""Tests for demo generation routes."""

import io
from unittest.mock import MagicMock, patch


class TestDemoGeneration:
    """Test POST /api/demo/generate"""

    def test_missing_cv_file(self, client):
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "CV-Datei" in data["message"]

    def test_empty_filename(self, client):
        pdf_data = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job", "cv_file": (pdf_data, "")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_non_pdf_file(self, client):
        txt_data = io.BytesIO(b"not a pdf")
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job", "cv_file": (txt_data, "cv.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "PDF" in data["message"]

    def test_missing_url(self, client):
        pdf_data = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/api/demo/generate",
            data={"url": "", "cv_file": (pdf_data, "cv.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "URL" in data["message"]

    def test_invalid_url(self, client):
        pdf_data = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/api/demo/generate",
            data={"url": "not-a-url", "cv_file": (pdf_data, "cv.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    @patch("routes.demo.extract_text_from_pdf")
    @patch("services.demo_generator.DemoGenerator")
    def test_success(self, mock_gen_class, mock_extract, client):
        mock_extract.return_value = "Extracted CV text"
        mock_gen = MagicMock()
        mock_gen.generate_demo.return_value = {
            "position": "Entwickler",
            "firma": "Test GmbH",
            "einleitung": "Test intro",
            "anschreiben": "Full letter",
        }
        mock_gen_class.return_value = mock_gen

        pdf_data = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job", "cv_file": (pdf_data, "cv.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["firma"] == "Test GmbH"
        assert "cv_text" in data["data"]

    @patch("routes.demo.extract_text_from_pdf")
    def test_empty_pdf_text(self, mock_extract, client):
        mock_extract.return_value = "   "
        pdf_data = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job", "cv_file": (pdf_data, "cv.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Text" in data["message"]
