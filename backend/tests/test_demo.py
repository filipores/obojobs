"""Tests for demo generation routes."""

import io
from unittest.mock import MagicMock, patch


class TestDemoGeneration:
    """Test POST /api/demo/generate"""

    def test_missing_url_json(self, client):
        response = client.post(
            "/api/demo/generate",
            json={"url": ""},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_url(self, client):
        response = client.post(
            "/api/demo/generate",
            json={"url": "not-a-url"},
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("services.demo_generator.DemoGenerator")
    def test_json_flow_success(self, mock_gen_class, client):
        mock_gen = MagicMock()
        mock_gen.generate_demo.return_value = {
            "position": "Entwickler",
            "firma": "Test GmbH",
            "einleitung": "Test intro",
            "anschreiben": "Full letter",
        }
        mock_gen_class.return_value = mock_gen

        response = client.post(
            "/api/demo/generate",
            json={"url": "https://example.com/job"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["firma"] == "Test GmbH"

    @patch("routes.demo.extract_text_from_pdf")
    @patch("services.demo_generator.DemoGenerator")
    def test_multipart_flow_success(self, mock_gen_class, mock_extract, client):
        mock_extract.return_value = "Extracted CV text"
        mock_gen = MagicMock()
        mock_gen.generate_demo.return_value = {
            "position": "Entwickler",
            "firma": "Test GmbH",
        }
        mock_gen_class.return_value = mock_gen

        pdf_data = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job", "cv_file": (pdf_data, "cv.pdf")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200

    def test_multipart_missing_cv(self, client):
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_multipart_non_pdf(self, client):
        txt_data = io.BytesIO(b"not a pdf")
        response = client.post(
            "/api/demo/generate",
            data={"url": "https://example.com/job", "cv_file": (txt_data, "cv.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
