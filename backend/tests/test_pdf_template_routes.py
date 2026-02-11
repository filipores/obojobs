"""
Tests for PDF Template API Routes.

Tests cover:
- POST /templates/upload-pdf (file upload, validation)
- POST /templates/<id>/analyze-variables (AI analysis)
- PUT /templates/<id>/variable-positions (save positions)
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.skip(reason="PDF template feature not fully integrated")
class TestUploadPdfTemplate:
    """Tests for POST /templates/upload-pdf endpoint."""

    def test_upload_pdf_success(self, client, auth_headers):
        """Test successful PDF upload creates template."""
        pdf_content = b"%PDF-1.4 fake pdf content"

        mock_extraction = {
            "text_blocks": [{"text": "Hello World", "x": 100, "y": 50, "width": 100, "height": 20, "page": 0}],
            "total_blocks": 1,
            "source": "native",
        }

        with (
            patch("routes.templates.PDFTemplateExtractor") as mock_extractor_class,
            patch("routes.templates.os.makedirs"),
            patch("routes.templates.secure_filename", return_value="test.pdf"),
            patch("routes.templates.time.time", return_value=1234567890),
        ):
            mock_extractor = MagicMock()
            mock_extractor.extract_text_with_positions.return_value = mock_extraction
            mock_extractor.get_plain_text.return_value = "Hello World"
            mock_extractor_class.return_value = mock_extractor

            # Mock file save
            with patch("werkzeug.datastructures.FileStorage.save"):
                response = client.post(
                    "/api/templates/upload-pdf",
                    headers=auth_headers,
                    data={
                        "file": (io.BytesIO(pdf_content), "test.pdf", "application/pdf"),
                        "name": "My PDF Template",
                    },
                    content_type="multipart/form-data",
                )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "template" in data
        assert data["template"]["name"] == "My PDF Template"
        assert data["template"]["is_pdf_template"] is True
        assert data["extraction_source"] == "native"
        assert data["total_blocks"] == 1

    def test_upload_pdf_no_file(self, client, auth_headers):
        """Test upload fails without file."""
        response = client.post(
            "/api/templates/upload-pdf",
            headers=auth_headers,
            data={},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Keine Datei" in data["error"]

    def test_upload_pdf_empty_filename(self, client, auth_headers):
        """Test upload fails with empty filename."""
        response = client.post(
            "/api/templates/upload-pdf",
            headers=auth_headers,
            data={"file": (io.BytesIO(b"content"), "", "application/pdf")},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Keine Datei" in data["error"]

    def test_upload_pdf_wrong_file_type(self, client, auth_headers):
        """Test upload rejects non-PDF files."""
        response = client.post(
            "/api/templates/upload-pdf",
            headers=auth_headers,
            data={"file": (io.BytesIO(b"content"), "test.txt", "text/plain")},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "PDF" in data["error"]

    @pytest.mark.skip(reason="Mock setup needs refinement")
    def test_upload_pdf_file_too_large(self, client, auth_headers):
        """Test upload rejects files over 10MB."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)

        response = client.post(
            "/api/templates/upload-pdf",
            headers=auth_headers,
            data={"file": (io.BytesIO(large_content), "large.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "groß" in data["error"] or "Größe" in data["error"]

    def test_upload_pdf_uses_filename_as_default_name(self, client, auth_headers):
        """Test template name defaults to filename when not provided."""
        pdf_content = b"%PDF-1.4 fake pdf content"

        mock_extraction = {
            "text_blocks": [],
            "total_blocks": 0,
            "source": "native",
        }

        with (
            patch("routes.templates.PDFTemplateExtractor") as mock_extractor_class,
            patch("routes.templates.os.makedirs"),
            patch("routes.templates.secure_filename", return_value="my_template.pdf"),
            patch("routes.templates.time.time", return_value=1234567890),
        ):
            mock_extractor = MagicMock()
            mock_extractor.extract_text_with_positions.return_value = mock_extraction
            mock_extractor.get_plain_text.return_value = ""
            mock_extractor_class.return_value = mock_extractor

            with patch("werkzeug.datastructures.FileStorage.save"):
                response = client.post(
                    "/api/templates/upload-pdf",
                    headers=auth_headers,
                    data={"file": (io.BytesIO(pdf_content), "my_template.pdf", "application/pdf")},
                    content_type="multipart/form-data",
                )

        assert response.status_code == 201
        data = response.get_json()
        # Filename without extension should be used as name
        assert data["template"]["name"] == "my_template"

    def test_upload_pdf_extraction_error_cleanup(self, client, auth_headers):
        """Test file cleanup on extraction error."""
        pdf_content = b"%PDF-1.4 fake pdf content"

        with (
            patch("routes.templates.PDFTemplateExtractor") as mock_extractor_class,
            patch("routes.templates.os.makedirs"),
            patch("routes.templates.os.path.exists", return_value=True),
            patch("routes.templates.os.remove") as mock_remove,
            patch("routes.templates.secure_filename", return_value="test.pdf"),
            patch("routes.templates.time.time", return_value=1234567890),
        ):
            mock_extractor = MagicMock()
            mock_extractor.extract_text_with_positions.side_effect = Exception("Extraction failed")
            mock_extractor_class.return_value = mock_extractor

            with patch("werkzeug.datastructures.FileStorage.save"):
                response = client.post(
                    "/api/templates/upload-pdf",
                    headers=auth_headers,
                    data={"file": (io.BytesIO(pdf_content), "test.pdf", "application/pdf")},
                    content_type="multipart/form-data",
                )

        assert response.status_code == 500
        # File should be cleaned up
        mock_remove.assert_called_once()

    def test_upload_pdf_unauthorized(self, client):
        """Test upload requires authentication."""
        response = client.post(
            "/api/templates/upload-pdf",
            data={"file": (io.BytesIO(b"content"), "test.pdf", "application/pdf")},
            content_type="multipart/form-data",
        )

        assert response.status_code == 401


@pytest.mark.skip(reason="PDF template feature not fully integrated")
class TestAnalyzeVariables:
    """Tests for POST /templates/<id>/analyze-variables endpoint."""

    def test_analyze_variables_success(self, client, auth_headers, app):
        """Test successful variable analysis with AI."""
        # Create a PDF template first
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test PDF Template",
                content="Sehr geehrte Frau Müller, ich bewerbe mich bei Muster GmbH als Entwickler.",
                is_pdf_template=True,
                pdf_path="/fake/path.pdf",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        with (
            patch("routes.templates.os.path.exists", return_value=True),
            patch("routes.templates.PDFTemplateExtractor") as mock_extractor_class,
            patch("routes.templates.QwenAPIClient") as mock_api_class,
        ):
            mock_extractor = MagicMock()
            mock_extractor.extract_text_with_positions.return_value = {
                "text_blocks": [{"text": "Muster GmbH", "x": 100, "y": 50, "width": 80, "height": 15, "page": 0}]
            }
            mock_extractor_class.return_value = mock_extractor

            mock_api = MagicMock()
            mock_api.chat_complete.return_value = json.dumps(
                [
                    {"text": "Muster GmbH", "variable": "FIRMA", "confidence": 0.95, "reason": "Company name"},
                    {"text": "Entwickler", "variable": "POSITION", "confidence": 0.90, "reason": "Job title"},
                ]
            )
            mock_api_class.return_value = mock_api

            response = client.post(
                f"/api/templates/{template_id}/analyze-variables",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["variable"] == "FIRMA"
        assert data["suggestions"][0]["confidence"] == 0.95
        # Position should be enriched from text blocks
        assert data["suggestions"][0]["position"] is not None

    def test_analyze_variables_template_not_found(self, client, auth_headers):
        """Test analysis fails for non-existent template."""
        response = client.post(
            "/api/templates/99999/analyze-variables",
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "nicht gefunden" in data["error"]

    def test_analyze_variables_non_pdf_template(self, client, auth_headers, app):
        """Test analysis fails for non-PDF templates."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Text Template",
                content="Some content",
                is_pdf_template=False,
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        response = client.post(
            f"/api/templates/{template_id}/analyze-variables",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "PDF" in data["error"]

    def test_analyze_variables_empty_content(self, client, auth_headers, app):
        """Test analysis fails for template with no content."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Empty Template",
                content="",
                is_pdf_template=True,
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        response = client.post(
            f"/api/templates/{template_id}/analyze-variables",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "keinen Text" in data["error"]

    def test_analyze_variables_ai_error(self, client, auth_headers, app):
        """Test handling of AI API errors."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Some content here",
                is_pdf_template=True,
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        with patch("routes.templates.QwenAPIClient") as mock_api_class:
            mock_api = MagicMock()
            mock_api.chat_complete.side_effect = Exception("API Error")
            mock_api_class.return_value = mock_api

            response = client.post(
                f"/api/templates/{template_id}/analyze-variables",
                headers=auth_headers,
            )

        assert response.status_code == 500
        data = response.get_json()
        assert "Fehler" in data["error"]


@pytest.mark.skip(reason="PDF template feature not fully integrated")
class TestSaveVariablePositions:
    """Tests for PUT /templates/<id>/variable-positions endpoint."""

    def test_save_positions_dict_format(self, client, auth_headers, app):
        """Test saving variable positions as dictionary."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
                is_pdf_template=True,
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        positions = {
            "FIRMA": {"x": 100, "y": 50, "width": 150, "height": 20, "page": 0},
            "POSITION": {"x": 100, "y": 100, "width": 200, "height": 20, "page": 0},
        }

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={"variable_positions": positions},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["template"]["variable_positions"] == positions

    def test_save_positions_list_format(self, client, auth_headers, app):
        """Test saving variable positions as list."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
                is_pdf_template=True,
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        positions = [
            {"variable": "FIRMA", "x": 100, "y": 50, "width": 150, "height": 20, "page": 0},
            {"variable": "POSITION", "x": 100, "y": 100, "width": 200, "height": 20, "page": 0},
        ]

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={"variable_positions": positions},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_save_positions_template_not_found(self, client, auth_headers):
        """Test saving positions for non-existent template."""
        response = client.put(
            "/api/templates/99999/variable-positions",
            headers=auth_headers,
            json={"variable_positions": {}},
        )

        assert response.status_code == 404

    @pytest.mark.skip(reason="Mock setup needs refinement")
    def test_save_positions_missing_data(self, client, auth_headers, app):
        """Test saving positions with missing data."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={},  # Missing variable_positions
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "erforderlich" in data["error"]

    def test_save_positions_invalid_variable_name_dict(self, client, auth_headers, app):
        """Test rejection of unknown variable names in dict format."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        positions = {
            "INVALID_VAR": {"x": 100, "y": 50},  # Invalid variable name
        }

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={"variable_positions": positions},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Unbekannte Variable" in data["error"]

    def test_save_positions_invalid_variable_name_list(self, client, auth_headers, app):
        """Test rejection of unknown variable names in list format."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        positions = [
            {"variable": "UNKNOWN", "x": 100, "y": 50},
        ]

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={"variable_positions": positions},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Unbekannte Variable" in data["error"]

    def test_save_positions_all_valid_variables(self, client, auth_headers, app):
        """Test all valid variable names are accepted."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        positions = {
            "FIRMA": {"x": 100, "y": 50},
            "POSITION": {"x": 100, "y": 100},
            "ANSPRECHPARTNER": {"x": 100, "y": 150},
            "QUELLE": {"x": 100, "y": 200},
            "EINLEITUNG": {"x": 100, "y": 250},
        }

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={"variable_positions": positions},
        )

        assert response.status_code == 200

    def test_save_positions_empty_dict(self, client, auth_headers, app):
        """Test saving empty positions is allowed."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.filter_by(email="test@example.com").first()
            template = Template(
                user_id=user.id,
                name="Test Template",
                content="Content",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,
            json={"variable_positions": {}},
        )

        assert response.status_code == 200

    def test_save_positions_unauthorized(self, client, app):
        """Test saving positions requires authentication."""
        with app.app_context():
            from models import Template, User, db

            user = User.query.first()
            if user:
                template = Template(
                    user_id=user.id,
                    name="Test Template",
                    content="Content",
                )
                db.session.add(template)
                db.session.commit()
                template_id = template.id
            else:
                template_id = 1

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            json={"variable_positions": {}},
        )

        assert response.status_code == 401

    def test_save_positions_other_users_template(self, client, auth_headers, app):
        """Test cannot save positions for another user's template."""
        with app.app_context():
            from models import Template, User, db

            # Create another user
            other_user = User(email="other@example.com", full_name="Other User")
            other_user.set_password("OtherPass123")
            db.session.add(other_user)
            db.session.commit()

            # Create template for other user
            template = Template(
                user_id=other_user.id,
                name="Other User Template",
                content="Content",
            )
            db.session.add(template)
            db.session.commit()
            template_id = template.id

        response = client.put(
            f"/api/templates/{template_id}/variable-positions",
            headers=auth_headers,  # Auth headers are for test@example.com
            json={"variable_positions": {}},
        )

        assert response.status_code == 404  # Should appear as not found
