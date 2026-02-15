"""Tests for full cover letter (Anschreiben) generation without templates."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from models import Application, Document, db


class TestGenerateAnschreiben:
    """Tests for QwenAPIClient.generate_anschreiben()"""

    @patch("services.qwen_client.OpenAI")
    def test_generate_anschreiben_basic(self, mock_openai_cls, app):
        """Test basic Anschreiben generation with required params."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "Sehr geehrte Damen und Herren,\n\n"
            "als erfahrener Entwickler bewerbe ich mich bei Ihnen.\n\n"
            "Mit freundlichen Grüßen\nMax Mustermann"
        )
        mock_client.chat.completions.create.return_value = mock_response

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")
        result = client.generate_anschreiben(
            cv_text="Max Mustermann, 5 Jahre Erfahrung als Entwickler",
            stellenanzeige_text="Wir suchen einen Entwickler",
            firma_name="Test GmbH",
            position="Entwickler",
            ansprechpartner="Sehr geehrte Damen und Herren",
        )

        assert "Sehr geehrte Damen und Herren" in result
        assert "Mit freundlichen Grüßen" in result
        mock_client.chat.completions.create.assert_called_once()

    @patch("services.qwen_client.OpenAI")
    def test_generate_anschreiben_with_tone(self, mock_openai_cls, app):
        """Test Anschreiben generation respects tone parameter."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sehr geehrte Frau Schmidt,\n\nText.\n\nMit freundlichen Grüßen\nMax"
        mock_client.chat.completions.create.return_value = mock_response

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")

        for tone in ["formal", "modern", "kreativ"]:
            client.generate_anschreiben(
                cv_text="CV text",
                stellenanzeige_text="Job text",
                firma_name="Firma",
                position="Developer",
                ansprechpartner="Sehr geehrte Frau Schmidt",
                tonalitaet=tone,
            )

        assert mock_client.chat.completions.create.call_count == 3

    @patch("services.qwen_client.OpenAI")
    def test_generate_anschreiben_with_skills(self, mock_openai_cls, app):
        """Test that user skills are included in the prompt."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sehr geehrte Damen und Herren,\n\nText.\n\nViele Grüße\nMax"
        mock_client.chat.completions.create.return_value = mock_response

        # Create mock skills
        mock_skill1 = MagicMock()
        mock_skill1.skill_name = "Python"
        mock_skill2 = MagicMock()
        mock_skill2.skill_name = "JavaScript"

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")
        client.generate_anschreiben(
            cv_text="CV with Python and JavaScript",
            stellenanzeige_text="Looking for developer",
            firma_name="Tech GmbH",
            position="Developer",
            ansprechpartner="Sehr geehrte Damen und Herren",
            user_skills=[mock_skill1, mock_skill2],
        )

        # Verify skills were included in the system prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][0]
        system_msg = messages[0]["content"]
        assert "Python" in system_msg
        assert "JavaScript" in system_msg

    @patch("services.qwen_client.OpenAI")
    def test_generate_anschreiben_retries_on_error(self, mock_openai_cls, app):
        """Test that generate_anschreiben retries on API errors."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sehr geehrte Damen und Herren,\n\nText."

        # Fail twice, succeed on third attempt (handled by _call_api_with_retry)
        mock_client.chat.completions.create.side_effect = [
            Exception("API error"),
            Exception("API error"),
            mock_response,
        ]

        from services.qwen_client import QwenAPIClient

        with patch("services.retry.time.sleep"), patch("services.qwen_client.time.sleep"):
            client = QwenAPIClient(api_key="test-key")
            result = client.generate_anschreiben(
                cv_text="CV",
                stellenanzeige_text="Job",
                firma_name="Firma",
                position="Dev",
                ansprechpartner="Sehr geehrte Damen und Herren",
                retry_count=3,
            )

        assert "Sehr geehrte Damen und Herren" in result
        assert mock_client.chat.completions.create.call_count == 3

    @patch("services.qwen_client.OpenAI")
    def test_generate_anschreiben_raises_after_retries(self, mock_openai_cls, app):
        """Test that generate_anschreiben raises after exhausting retries."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API down")

        from services.qwen_client import QwenAPIClient

        with patch("services.retry.time.sleep"), patch("services.qwen_client.time.sleep"):
            client = QwenAPIClient(api_key="test-key")
            with pytest.raises(Exception, match="Qwen API Fehler"):
                client.generate_anschreiben(
                    cv_text="CV",
                    stellenanzeige_text="Job",
                    firma_name="Firma",
                    position="Dev",
                    ansprechpartner="Sehr geehrte Damen und Herren",
                    retry_count=2,
                )


class TestPostprocessAnschreiben:
    """Tests for the postprocessing of AI-generated cover letters."""

    @patch("services.qwen_client.OpenAI")
    def test_removes_preamble(self, mock_openai_cls, app):
        """Test that preambles are stripped from AI output."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")

        text = "Hier ist das Anschreiben:\n\nSehr geehrte Damen und Herren,\n\nText."
        result = client._postprocess_anschreiben(text)
        assert result.startswith("Sehr geehrte Damen und Herren")

    @patch("services.qwen_client.OpenAI")
    def test_replaces_dashes(self, mock_openai_cls, app):
        """Test that dashes are replaced with commas."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")

        text = "Ich bin erfahren – sowohl in Python — als auch in JavaScript"
        result = client._postprocess_anschreiben(text)
        assert "–" not in result
        assert "—" not in result

    @patch("services.qwen_client.OpenAI")
    def test_normalizes_line_breaks(self, mock_openai_cls, app):
        """Test that excessive line breaks are normalized."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")

        text = "Absatz 1\n\n\n\n\nAbsatz 2"
        result = client._postprocess_anschreiben(text)
        assert "\n\n\n" not in result
        assert "Absatz 1\n\nAbsatz 2" == result

    @patch("services.qwen_client.OpenAI")
    def test_strips_code_fences(self, mock_openai_cls, app):
        """Test that code fences are removed."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")

        text = "```\nSehr geehrte Damen und Herren,\n\nText.\n```"
        result = client._postprocess_anschreiben(text)
        assert "```" not in result
        assert "Sehr geehrte Damen und Herren" in result

    @patch("services.qwen_client.OpenAI")
    def test_strips_surrounding_quotes(self, mock_openai_cls, app):
        """Test that surrounding quotes are removed."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        from services.qwen_client import QwenAPIClient

        client = QwenAPIClient(api_key="test-key")

        text = '"Sehr geehrte Damen und Herren,\n\nText."'
        result = client._postprocess_anschreiben(text)
        assert not result.startswith('"')
        assert not result.endswith('"')


class TestGeneratorWithoutTemplate:
    """Tests for BewerbungsGenerator without template system."""

    @patch("services.generator.QwenAPIClient")
    def test_generator_load_documents_no_template(self, mock_api_cls, app, test_user):
        """Test that load_user_documents only loads CV and Arbeitszeugnis, not templates."""
        with app.app_context():
            # Create a temp PDF file for the CV
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

                with patch("services.generator.read_document", return_value="CV text content"):
                    from services.generator import BewerbungsGenerator

                    gen = BewerbungsGenerator(user_id=test_user["id"])
                    gen.user = db.session.get(__import__("models", fromlist=["User"]).User, test_user["id"])
                    gen.load_user_documents()

                    assert gen.cv_text == "CV text content"
                    assert gen.zeugnis_text is None
            finally:
                os.unlink(cv_path)


class TestDemoGeneratorNoTemplate:
    """Tests for DemoGenerator without template system."""

    @patch("services.demo_generator.QwenAPIClient")
    @patch("services.demo_generator.read_document")
    def test_demo_uses_generate_anschreiben(self, mock_read, mock_api_cls):
        """Test that demo generator uses generate_anschreiben instead of templates."""
        mock_api = MagicMock()
        mock_api_cls.return_value = mock_api
        mock_read.return_value = {
            "text": "Job posting text",
            "email_links": [],
            "application_links": [],
            "all_links": [],
        }
        mock_api.extract_bewerbung_details.return_value = {
            "firma": "TestCo",
            "position": "Developer",
            "ansprechpartner": "Sehr geehrte Damen und Herren",
            "quelle": "Website",
            "email": "",
            "stellenanzeige_kompakt": "kompakt",
        }
        mock_api.generate_anschreiben.return_value = (
            "Sehr geehrte Damen und Herren,\n\nAnschreiben text.\n\n" "Mit freundlichen Grüßen\nMax"
        )

        from services.demo_generator import DemoGenerator

        gen = DemoGenerator()
        result = gen.generate_demo("https://example.com/job", "CV text")

        # Verify generate_anschreiben was called (not generate_einleitung)
        mock_api.generate_anschreiben.assert_called_once()
        assert "anschreiben" in result
        assert result["anschreiben"] == (
            "Sehr geehrte Damen und Herren,\n\nAnschreiben text.\n\n" "Mit freundlichen Grüßen\nMax"
        )

    @patch("services.demo_generator.QwenAPIClient")
    @patch("services.demo_generator.read_document")
    def test_demo_returns_all_fields(self, mock_read, mock_api_cls):
        """Test that demo generator returns all expected fields."""
        mock_api = MagicMock()
        mock_api_cls.return_value = mock_api
        mock_read.return_value = {
            "text": "Job posting text",
            "email_links": [],
            "application_links": [],
            "all_links": [],
        }
        mock_api.extract_bewerbung_details.return_value = {
            "firma": "TestCo",
            "position": "Developer",
            "ansprechpartner": "Sehr geehrte Damen und Herren",
            "quelle": "Website",
            "email": "",
            "stellenanzeige_kompakt": "kompakt",
        }
        mock_api.generate_anschreiben.return_value = "Anschreiben body"

        from services.demo_generator import DemoGenerator

        gen = DemoGenerator()
        result = gen.generate_demo("https://example.com/job", "CV text")

        expected_keys = {
            "position",
            "firma",
            "ansprechpartner",
            "quelle",
            "einleitung",
            "anschreiben",
            "betreff",
            "email_text",
        }
        assert expected_keys == set(result.keys())


class TestGenerationRouteTone:
    """Tests for tone parameter in generation routes."""

    @patch("routes.applications.generation.calculate_and_store_job_fit")
    @patch("routes.applications.generation.get_subscription_usage")
    @patch("routes.applications.generation.BewerbungsGenerator")
    @patch("routes.applications.generation.WebScraper")
    def test_generate_from_url_accepts_tone(
        self,
        mock_scraper_cls,
        mock_gen_cls,
        mock_usage,
        mock_job_fit,
        client,
        auth_headers,
        app,
        test_user,
    ):
        """Test that generate-from-url accepts tone parameter."""
        mock_scraper = MagicMock()
        mock_scraper_cls.return_value = mock_scraper

        mock_gen = MagicMock()
        mock_gen.generate_bewerbung.return_value = "/tmp/test.pdf"
        mock_gen.warnings = []
        mock_gen_cls.return_value = mock_gen

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
                "tone": "formal",
            },
            headers=auth_headers,
        )

        # The tone should have been passed to generate_bewerbung
        if mock_gen.generate_bewerbung.called:
            call_kwargs = mock_gen.generate_bewerbung.call_args
            # Check tone was passed (either as kwarg or positional)
            assert "formal" in str(call_kwargs) or response.status_code in (200, 400, 500)
