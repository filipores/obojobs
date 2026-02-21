"""Tests for services/email_formatter.py - EmailFormatter service."""

from services.email_formatter import EmailFormatter


class TestGenerateBetreff:
    """Tests for EmailFormatter.generate_betreff()."""

    def test_professional_with_firma_and_name(self):
        result = EmailFormatter.generate_betreff("Developer", "Test GmbH", "professional", "Max Mustermann")
        assert result == "Bewerbung als Developer - Max Mustermann"

    def test_professional_without_firma(self):
        result = EmailFormatter.generate_betreff("Developer", style="professional", user_name="Max")
        assert result == "Bewerbung als Developer"

    def test_professional_without_name(self):
        result = EmailFormatter.generate_betreff("Developer", "Test GmbH", "professional")
        assert result == "Bewerbung als Developer - Bewerber"

    def test_informal(self):
        result = EmailFormatter.generate_betreff("Developer", style="informal")
        assert result == "Bewerbung: Developer"

    def test_formal_with_firma(self):
        result = EmailFormatter.generate_betreff("Developer", "Test GmbH", "formal")
        assert result == "Bewerbung um die Position als Developer bei Test GmbH"

    def test_formal_without_firma(self):
        result = EmailFormatter.generate_betreff("Developer", style="formal")
        assert result == "Bewerbung um die Position als Developer"


class TestBuildSignature:
    """Tests for EmailFormatter.build_signature()."""

    def test_full_signature(self):
        result = EmailFormatter.build_signature(
            user_name="Max Mustermann",
            user_email="max@example.com",
            user_phone="+49 123 456",
            user_city="Berlin",
            user_website="https://max.dev",
        )
        lines = result.split("\n")
        assert lines[0] == "Max Mustermann"
        assert "Berlin | +49 123 456" in lines[1]
        assert "max@example.com" in result
        assert "https://max.dev" in result

    def test_minimal_signature(self):
        result = EmailFormatter.build_signature()
        assert result == "Ihr Name"

    def test_name_only(self):
        result = EmailFormatter.build_signature(user_name="Max Mustermann")
        assert result == "Max Mustermann"

    def test_name_and_email(self):
        result = EmailFormatter.build_signature(user_name="Max", user_email="max@example.com")
        assert result == "Max\nmax@example.com"

    def test_city_without_phone(self):
        result = EmailFormatter.build_signature(user_name="Max", user_city="Berlin")
        lines = result.split("\n")
        assert lines[0] == "Max"
        assert lines[1] == "Berlin"


class TestCombineEmailBodyWithSignature:
    """Tests for EmailFormatter.combine_email_body_with_signature()."""

    def test_combines_body_and_signature(self):
        ai_body = "Sehr geehrte Damen und Herren,\n\nAnbei meine Bewerbung.\n\nMit freundlichen Grüßen"
        result = EmailFormatter.combine_email_body_with_signature(
            ai_body=ai_body,
            user_name="Max Mustermann",
            user_email="max@example.com",
        )
        assert result.startswith("Sehr geehrte Damen und Herren,")
        assert "Mit freundlichen Grüßen" in result
        assert result.endswith("max@example.com")
        assert "Max Mustermann" in result

    def test_strips_trailing_whitespace_from_body(self):
        ai_body = "Body text\n\nMit freundlichen Grüßen\n\n  "
        result = EmailFormatter.combine_email_body_with_signature(
            ai_body=ai_body,
            user_name="Max",
        )
        # Should not have double blank lines between greeting and signature
        assert "Mit freundlichen Grüßen\nMax" in result

    def test_without_user_details(self):
        ai_body = "Body.\n\nMit freundlichen Grüßen"
        result = EmailFormatter.combine_email_body_with_signature(ai_body=ai_body)
        assert "Ihr Name" in result


class TestGenerateEmailText:
    """Tests for EmailFormatter.generate_email_text() (static fallback)."""

    def test_static_template_with_firma(self):
        result = EmailFormatter.generate_email_text(
            position="Developer",
            ansprechperson="Sehr geehrte Damen und Herren",
            firma_name="Test GmbH",
            user_name="Max Mustermann",
        )
        assert "Bewerbungsunterlagen" in result
        assert "Developer bei Test GmbH" in result
        assert "Max Mustermann" in result
        assert result.startswith("Sehr geehrte Damen und Herren,")

    def test_static_template_without_firma(self):
        result = EmailFormatter.generate_email_text(
            position="Developer",
            ansprechperson="Sehr geehrte Damen und Herren",
        )
        assert "die Position als Developer" in result
        assert "Ihr Name" in result

    def test_includes_contact_details(self):
        result = EmailFormatter.generate_email_text(
            position="Developer",
            ansprechperson="Sehr geehrte Damen und Herren",
            user_name="Max",
            user_email="max@example.com",
            user_phone="+49 123",
            user_city="Berlin",
        )
        assert "max@example.com" in result
        assert "Berlin" in result
        assert "+49 123" in result
