"""Tests for services/generator.py - BewerbungsGenerator service."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from models import Application, Document, User, UserSkill, db


class TestBewerbungsGeneratorInit:
    """Tests for BewerbungsGenerator initialization."""

    @patch("services.generator.QwenAPIClient")
    def test_init_sets_user_id(self, mock_api_cls, app):
        """Test that __init__ stores user_id and creates API client."""
        from services.generator import BewerbungsGenerator

        gen = BewerbungsGenerator(user_id=42)

        assert gen.user_id == 42
        assert gen.cv_text is None
        assert gen.zeugnis_text is None
        assert gen.extracted_links is None
        assert gen.user is None
        assert gen._prepared is False
        mock_api_cls.assert_called_once()

    @patch("services.generator.QwenAPIClient")
    def test_init_creates_api_client(self, mock_api_cls, app):
        """Test that QwenAPIClient is instantiated on init."""
        from services.generator import BewerbungsGenerator

        gen = BewerbungsGenerator(user_id=1)

        assert gen.api_client is not None
        mock_api_cls.assert_called_once()


class TestPrepare:
    """Tests for BewerbungsGenerator.prepare()."""

    @patch("services.generator.QwenAPIClient")
    def test_prepare_loads_user_and_documents(self, mock_api_cls, app, test_user):
        """Test that prepare() loads user from DB and calls load_user_documents."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 test content")
                cv_path = f.name

            try:
                doc = Document(
                    user_id=test_user["id"],
                    doc_type="lebenslauf",
                    file_path=cv_path,
                    original_filename="cv.pdf",
                )
                db.session.add(doc)
                db.session.commit()

                with patch("services.generator.read_document", return_value="CV text"):
                    from services.generator import BewerbungsGenerator

                    gen = BewerbungsGenerator(user_id=test_user["id"])
                    gen.prepare()

                    assert gen._prepared is True
                    assert gen.user is not None
                    assert gen.user.email == "test@example.com"
                    assert gen.cv_text == "CV text"
            finally:
                os.unlink(cv_path)

    @patch("services.generator.QwenAPIClient")
    def test_prepare_only_runs_once(self, mock_api_cls, app, test_user):
        """Test that calling prepare() twice does not reload."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 test")
                cv_path = f.name

            try:
                doc = Document(
                    user_id=test_user["id"],
                    doc_type="lebenslauf",
                    file_path=cv_path,
                    original_filename="cv.pdf",
                )
                db.session.add(doc)
                db.session.commit()

                with patch("services.generator.read_document", return_value="CV text") as mock_read:
                    from services.generator import BewerbungsGenerator

                    gen = BewerbungsGenerator(user_id=test_user["id"])
                    gen.prepare()
                    gen.prepare()  # second call should be no-op

                    # read_document should only be called once
                    assert mock_read.call_count == 1
            finally:
                os.unlink(cv_path)


class TestLoadUserDocuments:
    """Tests for BewerbungsGenerator.load_user_documents()."""

    @patch("services.generator.QwenAPIClient")
    def test_loads_cv_only(self, mock_api_cls, app, test_user):
        """Test loading only a Lebenslauf (no Arbeitszeugnis)."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 test")
                cv_path = f.name

            try:
                doc = Document(
                    user_id=test_user["id"],
                    doc_type="lebenslauf",
                    file_path=cv_path,
                    original_filename="cv.pdf",
                )
                db.session.add(doc)
                db.session.commit()

                with patch("services.generator.read_document", return_value="CV text content"):
                    from services.generator import BewerbungsGenerator

                    gen = BewerbungsGenerator(user_id=test_user["id"])
                    gen.load_user_documents()

                    assert gen.cv_text == "CV text content"
                    assert gen.zeugnis_text is None
            finally:
                os.unlink(cv_path)

    @patch("services.generator.QwenAPIClient")
    def test_loads_cv_and_zeugnis(self, mock_api_cls, app, test_user):
        """Test loading both Lebenslauf and Arbeitszeugnis."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 cv")
                cv_path = f.name
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 zeugnis")
                zeugnis_path = f.name

            try:
                cv_doc = Document(
                    user_id=test_user["id"],
                    doc_type="lebenslauf",
                    file_path=cv_path,
                    original_filename="cv.pdf",
                )
                zeugnis_doc = Document(
                    user_id=test_user["id"],
                    doc_type="arbeitszeugnis",
                    file_path=zeugnis_path,
                    original_filename="zeugnis.pdf",
                )
                db.session.add_all([cv_doc, zeugnis_doc])
                db.session.commit()

                with patch("services.generator.read_document", side_effect=["CV text", "Zeugnis text"]):
                    from services.generator import BewerbungsGenerator

                    gen = BewerbungsGenerator(user_id=test_user["id"])
                    gen.load_user_documents()

                    assert gen.cv_text == "CV text"
                    assert gen.zeugnis_text == "Zeugnis text"
            finally:
                os.unlink(cv_path)
                os.unlink(zeugnis_path)

    @patch("services.generator.QwenAPIClient")
    def test_raises_when_no_cv(self, mock_api_cls, app, test_user):
        """Test that ValueError is raised when no Lebenslauf exists."""
        with app.app_context():
            from services.generator import BewerbungsGenerator

            gen = BewerbungsGenerator(user_id=test_user["id"])

            with pytest.raises(ValueError, match="Lebenslauf nicht gefunden"):
                gen.load_user_documents()

    @patch("services.generator.QwenAPIClient")
    def test_raises_when_cv_file_missing(self, mock_api_cls, app, test_user):
        """Test that ValueError is raised when CV file path does not exist on disk."""
        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/nonexistent/path/cv.pdf",
                original_filename="cv.pdf",
            )
            db.session.add(doc)
            db.session.commit()

            from services.generator import BewerbungsGenerator

            gen = BewerbungsGenerator(user_id=test_user["id"])

            with pytest.raises(ValueError, match="Lebenslauf nicht gefunden"):
                gen.load_user_documents()


class TestGenerateBewerbung:
    """Tests for BewerbungsGenerator.generate_bewerbung()."""

    def _make_generator(self, app, test_user, mock_api):
        """Helper to create a prepared BewerbungsGenerator with mocked internals."""
        from services.generator import BewerbungsGenerator

        gen = BewerbungsGenerator(user_id=test_user["id"])
        gen.api_client = mock_api
        gen.cv_text = "Test CV text with Python experience"
        gen.zeugnis_text = None
        gen._prepared = True
        gen.user = db.session.get(User, test_user["id"])

        # Set user details for header generation
        gen.user.full_name = "Max Mustermann"
        gen.user.address = "Teststraße 1"
        gen.user.postal_code = "80331"
        gen.user.city = "München"
        gen.user.phone = "+49 123 456789"
        gen.user.email = "test@example.com"
        gen.user.website = None
        db.session.commit()

        return gen

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_with_user_details(self, mock_api_cls, mock_pdf, app, test_user):
        """Test full generation flow with user-provided details (preview path)."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = (
                "Sehr geehrte Damen und Herren,\n\nAnschreiben body.\n\nMit freundlichen Grüßen\nMax"
            )
            mock_api.generate_betreff.return_value = "Bewerbung als Developer"
            mock_api.generate_email_text.return_value = "Email body text"

            gen = self._make_generator(app, test_user, mock_api)

            result = gen.generate_bewerbung(
                stellenanzeige_path="https://example.com/job",
                firma_name="Test GmbH",
                user_details={
                    "position": "Senior Developer",
                    "contact_person": "Frau Schmidt",
                    "contact_email": "hr@test.de",
                    "description": "A job posting about development",
                    "quelle": "LinkedIn",
                },
            )

            assert result.endswith(".pdf")
            mock_api.generate_anschreiben.assert_called_once()
            mock_pdf.assert_called_once()

            # Verify application was saved
            app_record = Application.query.filter_by(user_id=test_user["id"]).first()
            assert app_record is not None
            assert app_record.firma == "Test GmbH"
            assert app_record.position == "Senior Developer"
            assert app_record.status == "erstellt"
            assert app_record.betreff == "Bewerbung als Senior Developer - Max Mustermann"

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_with_url_extraction(self, mock_api_cls, mock_pdf, app, test_user):
        """Test generation flow that reads from URL and extracts details via API."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.extract_bewerbung_details.return_value = {
                "firma": "Test GmbH",
                "position": "Developer",
                "ansprechpartner": "Sehr geehrte Damen und Herren",
                "quelle": "Website",
                "email": "jobs@test.de",
                "stellenanzeige_kompakt": "kompakt",
            }
            mock_api.generate_anschreiben.return_value = "Sehr geehrte Damen und Herren,\n\nBody.\n\nMFG\nMax"
            mock_api.generate_betreff.return_value = "Bewerbung als Developer"
            mock_api.generate_email_text.return_value = "Email text"

            gen = self._make_generator(app, test_user, mock_api)

            with patch(
                "services.generator.read_document",
                return_value={
                    "text": "Job posting content",
                    "email_links": [{"email": "hr@test.de", "text": "HR"}],
                    "application_links": [],
                    "all_links": [],
                },
            ):
                with patch("services.generator.is_url", return_value=True):
                    result = gen.generate_bewerbung(
                        stellenanzeige_path="https://example.com/job",
                        firma_name="Test GmbH",
                    )

            assert result.endswith(".pdf")
            mock_api.extract_bewerbung_details.assert_called_once()

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_with_file_path(self, mock_api_cls, mock_pdf, app, test_user):
        """Test generation with a file path instead of URL."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.extract_bewerbung_details.return_value = {
                "firma": "Firma AG",
                "position": "Tester",
                "ansprechpartner": "Sehr geehrte Damen und Herren",
                "quelle": "Website",
                "email": "",
                "stellenanzeige_kompakt": "kompakt",
            }
            mock_api.generate_anschreiben.return_value = "Sehr geehrte Damen und Herren,\n\nBody."
            mock_api.generate_betreff.return_value = "Bewerbung als Tester"
            mock_api.generate_email_text.return_value = "Email"

            gen = self._make_generator(app, test_user, mock_api)

            with patch("services.generator.read_document", return_value="File content"):
                with patch("services.generator.is_url", return_value=False):
                    result = gen.generate_bewerbung(
                        stellenanzeige_path="/path/to/job.pdf",
                        firma_name="Firma AG",
                    )

            assert result.endswith(".pdf")
            # For file path, extracted_links should be None
            assert gen.extracted_links is None

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_auto_prepares(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that generate_bewerbung auto-calls prepare() if not prepared."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 test")
                cv_path = f.name

            try:
                doc = Document(
                    user_id=test_user["id"],
                    doc_type="lebenslauf",
                    file_path=cv_path,
                    original_filename="cv.pdf",
                )
                db.session.add(doc)

                user = db.session.get(User, test_user["id"])
                user.full_name = "Max Mustermann"
                user.city = "Berlin"
                db.session.commit()

                mock_api = MagicMock()
                mock_api.generate_anschreiben.return_value = "Sehr geehrte Damen und Herren,\n\nBody."
                mock_api.generate_betreff.return_value = "Betreff"
                mock_api.generate_email_text.return_value = "Email"

                from services.generator import BewerbungsGenerator

                gen = BewerbungsGenerator(user_id=test_user["id"])
                gen.api_client = mock_api

                with patch("services.generator.read_document") as mock_read:
                    mock_read.side_effect = [
                        "CV content",  # load_user_documents
                        {"text": "Job text", "email_links": [], "application_links": [], "all_links": []},  # URL read
                    ]
                    with patch("services.generator.is_url", return_value=True):
                        mock_api.extract_bewerbung_details.return_value = {
                            "firma": "F",
                            "position": "P",
                            "ansprechpartner": "Sehr geehrte Damen und Herren",
                            "quelle": "Web",
                            "email": "",
                            "stellenanzeige_kompakt": "k",
                        }
                        result = gen.generate_bewerbung("https://example.com", "Firma")

                assert gen._prepared is True
                assert result.endswith(".pdf")
            finally:
                os.unlink(cv_path)

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_builds_briefkopf(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that the briefkopf (header) is built correctly from user data."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Sehr geehrte Damen und Herren,\n\nBody."
            mock_api.generate_betreff.return_value = "Bewerbung als Dev"
            mock_api.generate_email_text.return_value = "Email"

            gen = self._make_generator(app, test_user, mock_api)

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Firma GmbH",
                user_details={
                    "position": "Developer",
                    "contact_person": "",
                    "description": "Job desc",
                },
            )

            # Check what was passed to create_anschreiben_pdf
            call_args = mock_pdf.call_args
            full_text = call_args[0][0]  # first positional arg

            assert "Max Mustermann" in full_text
            assert "Teststraße 1" in full_text
            assert "80331 München" in full_text
            assert "+49 123 456789" in full_text
            assert "Firma GmbH" in full_text
            assert "Bewerbung als Developer" in full_text

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_custom_output_filename(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that a custom output filename is respected."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Sehr geehrte Damen und Herren,\n\nBody."
            mock_api.generate_betreff.return_value = "Betreff"
            mock_api.generate_email_text.return_value = "Email"

            gen = self._make_generator(app, test_user, mock_api)

            result = gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Test",
                output_filename="custom_name.pdf",
                user_details={"description": "Job", "position": "Dev"},
            )

            assert result.endswith("custom_name.pdf")

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_saves_application_to_db(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that an Application record is created and committed."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Sehr geehrte Damen und Herren,\n\nBody."
            mock_api.generate_betreff.return_value = "Bewerbung als Dev"
            mock_api.generate_email_text.return_value = "Email text here"

            gen = self._make_generator(app, test_user, mock_api)

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="SaveTest GmbH",
                user_details={"description": "Job desc", "position": "Tester", "quelle": "Indeed"},
            )

            app_record = Application.query.filter_by(firma="SaveTest GmbH").first()
            assert app_record is not None
            assert app_record.user_id == test_user["id"]
            assert app_record.position == "Tester"
            assert app_record.status == "erstellt"
            assert app_record.betreff == "Bewerbung als Tester - Max Mustermann"
            assert "Bewerbungsunterlagen" in app_record.email_text

            # Check status_history was initialized
            history = app_record.get_status_history()
            assert len(history) >= 1
            assert history[0]["status"] == "erstellt"

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_passes_tonalitaet(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that tonalitaet parameter is forwarded to generate_anschreiben."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Body."
            mock_api.generate_betreff.return_value = "Betreff"
            mock_api.generate_email_text.return_value = "Email"

            gen = self._make_generator(app, test_user, mock_api)

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Test",
                user_details={"description": "Job", "position": "Dev"},
                tonalitaet="kreativ",
            )

            call_kwargs = mock_api.generate_anschreiben.call_args
            assert call_kwargs[1]["tonalitaet"] == "kreativ"

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_includes_user_skills(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that user skills are passed to generate_anschreiben."""
        with app.app_context():
            # Add skills for the test user
            skill1 = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            skill2 = UserSkill(
                user_id=test_user["id"],
                skill_name="Docker",
                skill_category="tools",
            )
            db.session.add_all([skill1, skill2])
            db.session.commit()

            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Body."
            mock_api.generate_betreff.return_value = "Betreff"
            mock_api.generate_email_text.return_value = "Email"

            gen = self._make_generator(app, test_user, mock_api)

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Test",
                user_details={"description": "Job", "position": "Dev"},
            )

            call_kwargs = mock_api.generate_anschreiben.call_args[1]
            user_skills = call_kwargs["user_skills"]
            skill_names = [s.skill_name for s in user_skills]
            assert "Python" in skill_names
            assert "Docker" in skill_names

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_normalizes_blank_lines(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that excessive blank lines in the output are normalized."""
        with app.app_context():
            mock_api = MagicMock()
            # Return text with excessive blank lines
            mock_api.generate_anschreiben.return_value = "Line1\n\n\n\n\nLine2"
            mock_api.generate_betreff.return_value = "Betreff"
            mock_api.generate_email_text.return_value = "Email"

            gen = self._make_generator(app, test_user, mock_api)

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Test",
                user_details={"description": "Job", "position": "Dev"},
            )

            # Verify the text passed to PDF doesn't have >2 consecutive newlines
            call_args = mock_pdf.call_args
            full_text = call_args[0][0]
            assert "\n\n\n" not in full_text

    @patch("services.generator.EmailFormatter")
    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_generate_builds_attachments_list(self, mock_api_cls, mock_pdf, mock_email_fmt, app, test_user):
        """Test that attachments list includes uploaded documents."""
        with app.app_context():
            # Add an Arbeitszeugnis document
            zeugnis_doc = Document(
                user_id=test_user["id"],
                doc_type="arbeitszeugnis",
                file_path="/path/to/zeugnis.pdf",
                original_filename="Arbeitszeugnis_Firma.pdf",
            )
            db.session.add(zeugnis_doc)
            db.session.commit()

            mock_email_fmt.generate_betreff.return_value = "Betreff"
            mock_email_fmt.generate_email_text.return_value = "Email"

            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Body."

            gen = self._make_generator(app, test_user, mock_api)

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Test",
                user_details={"description": "Job", "position": "Dev"},
            )

            # Check that generate_email_text received attachments with Arbeitszeugnis
            call_kwargs = mock_email_fmt.generate_email_text.call_args[1]
            attachments = call_kwargs["attachments"]
            assert "Anschreiben" in attachments
            assert "Lebenslauf" in attachments
            assert "Arbeitszeugnis_Firma.pdf" in attachments


class TestProcessFirma:
    """Tests for BewerbungsGenerator.process_firma()."""

    @patch("services.generator.QwenAPIClient")
    def test_process_firma_success(self, mock_api_cls, app, test_user):
        """Test process_firma delegates to generate_bewerbung."""
        from services.generator import BewerbungsGenerator

        with app.app_context():
            gen = BewerbungsGenerator(user_id=test_user["id"])
            gen._prepared = True

            with patch.object(gen, "generate_bewerbung", return_value="/path/to/output.pdf") as mock_gen:
                result = gen.process_firma({"name": "Test GmbH", "stellenanzeige": "https://example.com/job"})

            assert result == "/path/to/output.pdf"
            mock_gen.assert_called_once_with("https://example.com/job", "Test GmbH")

    @patch("services.generator.QwenAPIClient")
    def test_process_firma_missing_name(self, mock_api_cls, app, test_user):
        """Test process_firma returns None when name is missing."""
        from services.generator import BewerbungsGenerator

        with app.app_context():
            gen = BewerbungsGenerator(user_id=test_user["id"])
            result = gen.process_firma({"stellenanzeige": "https://example.com"})
            assert result is None

    @patch("services.generator.QwenAPIClient")
    def test_process_firma_missing_stellenanzeige(self, mock_api_cls, app, test_user):
        """Test process_firma returns None when stellenanzeige is missing."""
        from services.generator import BewerbungsGenerator

        with app.app_context():
            gen = BewerbungsGenerator(user_id=test_user["id"])
            result = gen.process_firma({"name": "Test GmbH"})
            assert result is None

    @patch("services.generator.QwenAPIClient")
    def test_process_firma_handles_error(self, mock_api_cls, app, test_user):
        """Test process_firma catches exceptions and returns None."""
        from services.generator import BewerbungsGenerator

        with app.app_context():
            gen = BewerbungsGenerator(user_id=test_user["id"])
            gen._prepared = True

            with patch.object(gen, "generate_bewerbung", side_effect=Exception("API Error")):
                result = gen.process_firma({"name": "Test GmbH", "stellenanzeige": "https://example.com"})

            assert result is None


class TestContactPersonFormatting:
    """Tests for contact person salutation formatting in generate_bewerbung."""

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_user_details_with_contact_person(self, mock_api_cls, mock_pdf, app, test_user):
        """Test that contact_person is formatted via ContactExtractor."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Body."
            mock_api.generate_betreff.return_value = "Betreff"
            mock_api.generate_email_text.return_value = "Email"

            from services.generator import BewerbungsGenerator

            gen = BewerbungsGenerator(user_id=test_user["id"])
            gen.api_client = mock_api
            gen.cv_text = "CV text"
            gen._prepared = True
            gen.user = db.session.get(User, test_user["id"])
            gen.user.full_name = "Max Mustermann"
            db.session.commit()

            with patch("services.generator.ContactExtractor") as mock_ce:
                mock_ce.return_value.format_contact_person_salutation.return_value = "Sehr geehrte Frau Schmidt"

                gen.generate_bewerbung(
                    stellenanzeige_path="https://example.com",
                    firma_name="Test GmbH",
                    user_details={
                        "description": "Job",
                        "position": "Dev",
                        "contact_person": "Frau Schmidt",
                    },
                )

            # Verify the formatted salutation was passed to generate_anschreiben
            call_kwargs = mock_api.generate_anschreiben.call_args[1]
            assert call_kwargs["ansprechpartner"] == "Sehr geehrte Frau Schmidt"

    @patch("services.generator.create_anschreiben_pdf")
    @patch("services.generator.QwenAPIClient")
    def test_user_details_without_contact_person(self, mock_api_cls, mock_pdf, app, test_user):
        """Test fallback when no contact_person is provided."""
        with app.app_context():
            mock_api = MagicMock()
            mock_api.generate_anschreiben.return_value = "Body."
            mock_api.generate_betreff.return_value = "Betreff"
            mock_api.generate_email_text.return_value = "Email"

            from services.generator import BewerbungsGenerator

            gen = BewerbungsGenerator(user_id=test_user["id"])
            gen.api_client = mock_api
            gen.cv_text = "CV text"
            gen._prepared = True
            gen.user = db.session.get(User, test_user["id"])
            gen.user.full_name = "Max Mustermann"
            db.session.commit()

            gen.generate_bewerbung(
                stellenanzeige_path="https://example.com",
                firma_name="Test GmbH",
                user_details={
                    "description": "Job",
                    "position": "Dev",
                    "contact_person": "",
                },
            )

            # When contact_person is empty, ContactExtractor should get None
            call_kwargs = mock_api.generate_anschreiben.call_args[1]
            # The ansprechpartner should be some fallback salutation
            assert call_kwargs["ansprechpartner"]  # Not empty
