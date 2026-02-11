"""
Tests for document upload/management endpoints.
"""

import io
from unittest.mock import MagicMock, patch

from models import Document, User, UserSkill, db


def create_test_pdf():
    """Create a minimal valid PDF file for testing."""
    pdf = io.BytesIO()
    pdf.write(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF"
    )
    pdf.seek(0)
    return pdf


def create_second_user(app):
    """Create a second user for isolation tests."""
    user = User(email="other@example.com", full_name="Other User")
    user.set_password("OtherPass123")
    db.session.add(user)
    db.session.commit()
    return user


class TestDocumentUpload:
    """Tests for POST /api/documents"""

    def test_upload_without_file(self, client, auth_headers):
        """Upload without file returns 400."""
        response = client.post(
            "/api/documents",
            data={"doc_type": "lebenslauf"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Keine Datei hochgeladen"

    def test_upload_with_empty_filename(self, client, auth_headers):
        """Upload with empty filename returns 400."""
        response = client.post(
            "/api/documents",
            data={
                "file": (io.BytesIO(b"data"), ""),
                "doc_type": "lebenslauf",
            },
            headers=auth_headers,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Keine Datei ausgewählt"

    def test_upload_non_pdf_file(self, client, auth_headers):
        """Upload non-PDF file returns 400."""
        response = client.post(
            "/api/documents",
            data={
                "file": (io.BytesIO(b"plain text"), "resume.txt"),
                "doc_type": "lebenslauf",
            },
            headers=auth_headers,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Nur PDF-Dateien erlaubt"

    def test_upload_with_invalid_doc_type(self, client, auth_headers):
        """Upload with invalid doc_type returns 400."""
        response = client.post(
            "/api/documents",
            data={
                "file": (create_test_pdf(), "resume.pdf"),
                "doc_type": "invalid_type",
            },
            headers=auth_headers,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Ungültiger Dokumenttyp" in data["error"]

    def test_upload_without_doc_type(self, client, auth_headers):
        """Upload without doc_type returns 400."""
        response = client.post(
            "/api/documents",
            data={
                "file": (create_test_pdf(), "resume.pdf"),
            },
            headers=auth_headers,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Ungültiger Dokumenttyp" in data["error"]

    @patch("routes.documents.extract_text_from_pdf")
    def test_upload_valid_pdf(self, mock_extract, client, auth_headers, test_user, tmp_path):
        """Upload valid PDF creates document and returns 201."""
        mock_extract.return_value = "Extracted CV text with skills and experience."

        with patch("routes.documents.config") as mock_config:
            mock_config.UPLOAD_FOLDER = str(tmp_path)

            response = client.post(
                "/api/documents",
                data={
                    "file": (create_test_pdf(), "resume.pdf"),
                    "doc_type": "arbeitszeugnis",
                },
                headers=auth_headers,
                content_type="multipart/form-data",
            )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "document" in data
        assert data["document"]["doc_type"] == "arbeitszeugnis"
        assert data["text_length"] > 0

    @patch("routes.documents.SkillExtractor")
    @patch("routes.documents.extract_text_from_pdf")
    def test_upload_cv_extracts_skills(
        self, mock_extract, mock_extractor_class, client, auth_headers, test_user, tmp_path
    ):
        """Upload CV (lebenslauf) triggers skill extraction."""
        mock_extract.return_value = "CV text with Python and Teamwork skills."

        mock_instance = MagicMock()
        mock_instance.extract_skills_from_cv.return_value = [
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5},
            {"skill_name": "Teamwork", "skill_category": "soft_skills", "experience_years": None},
        ]
        mock_extractor_class.return_value = mock_instance

        with patch("routes.documents.config") as mock_config:
            mock_config.UPLOAD_FOLDER = str(tmp_path)

            response = client.post(
                "/api/documents",
                data={
                    "file": (create_test_pdf(), "lebenslauf.pdf"),
                    "doc_type": "lebenslauf",
                },
                headers=auth_headers,
                content_type="multipart/form-data",
            )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "skills_extracted" in data
        assert data["skills_extracted"] == 2

        mock_instance.extract_skills_from_cv.assert_called_once()

    @patch("routes.documents.extract_text_from_pdf")
    def test_upload_replaces_existing_doc_of_same_type(
        self, mock_extract, client, auth_headers, test_user, app, tmp_path
    ):
        """Uploading a document of the same type replaces the existing one."""
        mock_extract.return_value = "First version of text."

        with patch("routes.documents.config") as mock_config:
            mock_config.UPLOAD_FOLDER = str(tmp_path)

            # First upload
            client.post(
                "/api/documents",
                data={
                    "file": (create_test_pdf(), "zeugnis1.pdf"),
                    "doc_type": "arbeitszeugnis",
                },
                headers=auth_headers,
                content_type="multipart/form-data",
            )

            mock_extract.return_value = "Second version of text."

            # Second upload of same type
            response = client.post(
                "/api/documents",
                data={
                    "file": (create_test_pdf(), "zeugnis2.pdf"),
                    "doc_type": "arbeitszeugnis",
                },
                headers=auth_headers,
                content_type="multipart/form-data",
            )

        assert response.status_code == 201

        # Should still have only one document of this type
        with app.app_context():
            docs = Document.query.filter_by(user_id=test_user["id"], doc_type="arbeitszeugnis").all()
            assert len(docs) == 1
            assert docs[0].original_filename == "zeugnis2.pdf"

    @patch("routes.documents.extract_text_from_pdf")
    def test_upload_empty_text_extraction(self, mock_extract, client, auth_headers, tmp_path):
        """Upload where PDF text extraction returns empty string returns 400."""
        mock_extract.return_value = "   "

        with patch("routes.documents.config") as mock_config:
            mock_config.UPLOAD_FOLDER = str(tmp_path)

            response = client.post(
                "/api/documents",
                data={
                    "file": (create_test_pdf(), "empty.pdf"),
                    "doc_type": "lebenslauf",
                },
                headers=auth_headers,
                content_type="multipart/form-data",
            )

        assert response.status_code == 400
        data = response.get_json()
        assert "keinen Text" in data["error"]


class TestDocumentList:
    """Tests for GET /api/documents"""

    def test_list_documents_empty(self, client, auth_headers):
        """List documents when none exist returns empty list."""
        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["documents"] == []

    def test_list_documents_with_documents(self, client, auth_headers, test_user, app):
        """List documents returns user's documents."""
        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/fake/path/lebenslauf.txt",
                original_filename="cv.pdf",
            )
            db.session.add(doc)
            db.session.commit()

        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["doc_type"] == "lebenslauf"

    def test_list_documents_only_returns_own_docs(self, client, auth_headers, test_user, app):
        """List documents only returns the current user's documents."""
        with app.app_context():
            # Add document for the test user
            own_doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/fake/path/own.txt",
                original_filename="own.pdf",
            )
            db.session.add(own_doc)

            # Add document for another user
            other_user = create_second_user(app)
            other_doc = Document(
                user_id=other_user.id,
                doc_type="arbeitszeugnis",
                file_path="/fake/path/other.txt",
                original_filename="other.pdf",
            )
            db.session.add(other_doc)
            db.session.commit()

        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["original_filename"] == "own.pdf"


class TestDocumentGet:
    """Tests for GET /api/documents/<id>"""

    def test_get_existing_document(self, client, auth_headers, test_user, app, tmp_path):
        """Get existing document returns the file."""
        # Create a real file on disk
        txt_file = tmp_path / "lebenslauf.txt"
        txt_file.write_text("Extracted CV text content")

        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path=str(txt_file),
                original_filename="cv.pdf",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 200
        assert b"Extracted CV text content" in response.data

    def test_get_nonexistent_document(self, client, auth_headers):
        """Get non-existent document returns 404."""
        response = client.get("/api/documents/99999", headers=auth_headers)
        assert response.status_code == 404
        assert response.get_json()["error"] == "Dokument nicht gefunden"

    def test_get_another_users_document(self, client, auth_headers, test_user, app, tmp_path):
        """Get another user's document returns 404 (filtered by user_id)."""
        txt_file = tmp_path / "other.txt"
        txt_file.write_text("Other user's document")

        with app.app_context():
            other_user = create_second_user(app)
            doc = Document(
                user_id=other_user.id,
                doc_type="arbeitszeugnis",
                file_path=str(txt_file),
                original_filename="other.pdf",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_document_file_missing_on_disk(self, client, auth_headers, test_user, app):
        """Get document where file is missing on disk returns 404."""
        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/nonexistent/path/lebenslauf.txt",
                original_filename="cv.pdf",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 404
        assert response.get_json()["error"] == "Datei nicht gefunden"


class TestDocumentDelete:
    """Tests for DELETE /api/documents/<id>"""

    def test_delete_document(self, client, auth_headers, test_user, app, tmp_path):
        """Delete document removes it from the database."""
        txt_file = tmp_path / "arbeitszeugnis.txt"
        txt_file.write_text("Test content")

        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="arbeitszeugnis",
                file_path=str(txt_file),
                original_filename="zeugnis.pdf",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "gelöscht" in data["message"]

        # Verify document is gone from DB
        with app.app_context():
            assert Document.query.get(doc_id) is None

        # Verify file is removed from disk
        assert not txt_file.exists()

    def test_delete_document_with_skills(self, client, auth_headers, test_user, app, tmp_path):
        """Delete document with delete_skills=true removes associated skills."""
        txt_file = tmp_path / "lebenslauf.txt"
        txt_file.write_text("CV content")

        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path=str(txt_file),
                original_filename="cv.pdf",
            )
            db.session.add(doc)
            db.session.commit()

            # Add skills linked to this document
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
                experience_years=5,
                source_document_id=doc.id,
            )
            db.session.add(skill)
            db.session.commit()
            doc_id = doc.id

        response = client.delete(f"/api/documents/{doc_id}?delete_skills=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["skills_deleted"] == 1
        assert "Skills" in data["message"]

        # Verify skills are gone
        with app.app_context():
            skills = UserSkill.query.filter_by(user_id=test_user["id"]).all()
            assert len(skills) == 0

    def test_delete_document_without_skills_flag(self, client, auth_headers, test_user, app, tmp_path):
        """Delete document without delete_skills flag preserves skills."""
        txt_file = tmp_path / "lebenslauf.txt"
        txt_file.write_text("CV content")

        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path=str(txt_file),
                original_filename="cv.pdf",
            )
            db.session.add(doc)
            db.session.commit()

            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
                experience_years=5,
                source_document_id=doc.id,
            )
            db.session.add(skill)
            db.session.commit()
            doc_id = doc.id

        response = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 200

        # Skills should still exist (source_document_id will be a dangling reference)
        with app.app_context():
            skills = UserSkill.query.filter_by(user_id=test_user["id"]).all()
            assert len(skills) == 1
            assert skills[0].skill_name == "Python"

    def test_delete_nonexistent_document(self, client, auth_headers):
        """Delete non-existent document returns 404."""
        response = client.delete("/api/documents/99999", headers=auth_headers)
        assert response.status_code == 404
        assert response.get_json()["error"] == "Document not found"

    def test_delete_another_users_document(self, client, auth_headers, test_user, app, tmp_path):
        """Delete another user's document returns 404."""
        txt_file = tmp_path / "other.txt"
        txt_file.write_text("Other content")

        with app.app_context():
            other_user = create_second_user(app)
            doc = Document(
                user_id=other_user.id,
                doc_type="arbeitszeugnis",
                file_path=str(txt_file),
                original_filename="other.pdf",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 404


class TestDocumentUnauthenticated:
    """Tests that all endpoints require authentication."""

    def test_list_documents_unauthenticated(self, client):
        """GET /api/documents without auth returns 401."""
        response = client.get("/api/documents")
        assert response.status_code == 401

    def test_upload_document_unauthenticated(self, client):
        """POST /api/documents without auth returns 401."""
        response = client.post(
            "/api/documents",
            data={
                "file": (create_test_pdf(), "resume.pdf"),
                "doc_type": "lebenslauf",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 401

    def test_get_document_unauthenticated(self, client):
        """GET /api/documents/<id> without auth returns 401."""
        response = client.get("/api/documents/1")
        assert response.status_code == 401

    def test_delete_document_unauthenticated(self, client):
        """DELETE /api/documents/<id> without auth returns 401."""
        response = client.delete("/api/documents/1")
        assert response.status_code == 401
