"""
Tests for template_generator service.
"""

from models import Template, db
from services.template_generator import (
    DEFAULT_GERMAN_TEMPLATE,
    create_default_template,
    get_or_create_default_template,
)


class TestCreateDefaultTemplate:
    """Tests for create_default_template function."""

    def test_creates_template_for_user(self, app, test_user):
        """Test that create_default_template creates a template."""
        with app.app_context():
            template = create_default_template(test_user["id"])

            assert template is not None
            assert template.user_id == test_user["id"]
            assert template.name == "Standard-Vorlage (automatisch erstellt)"
            assert template.content == DEFAULT_GERMAN_TEMPLATE
            assert template.is_default is True
            assert template.is_pdf_template is False

    def test_template_persisted_to_database(self, app, test_user):
        """Test that the template is saved to the database."""
        with app.app_context():
            template = create_default_template(test_user["id"])
            template_id = template.id

            # Query again to verify persistence
            found = Template.query.get(template_id)
            assert found is not None
            assert found.name == "Standard-Vorlage (automatisch erstellt)"

    def test_template_has_required_placeholders(self, app, test_user):
        """Test that the default template has all required placeholders."""
        with app.app_context():
            template = create_default_template(test_user["id"])

            assert "{{ANSPRECHPARTNER}}" in template.content
            assert "{{POSITION}}" in template.content
            assert "{{EINLEITUNG}}" in template.content
            assert "{{FIRMA}}" in template.content
            assert "{{NAME}}" in template.content
            assert "{{ADRESSE}}" in template.content
            assert "{{PLZ_ORT}}" in template.content
            assert "{{TELEFON}}" in template.content
            assert "{{EMAIL}}" in template.content
            assert "{{DATUM}}" in template.content
            assert "{{STADT}}" in template.content


class TestGetOrCreateDefaultTemplate:
    """Tests for get_or_create_default_template function."""

    def test_returns_existing_default_template(self, app, test_user):
        """Test that existing default template is returned."""
        with app.app_context():
            # Create an existing default template
            existing = Template(
                user_id=test_user["id"],
                name="Existing Default",
                content="Test content",
                is_default=True,
            )
            db.session.add(existing)
            db.session.commit()

            # Should return existing template
            result = get_or_create_default_template(test_user["id"])
            assert result.id == existing.id
            assert result.name == "Existing Default"

    def test_returns_any_template_if_no_default(self, app, test_user):
        """Test that any existing template is returned if no default."""
        with app.app_context():
            # Create a non-default template
            existing = Template(
                user_id=test_user["id"],
                name="Non-Default Template",
                content="Test content",
                is_default=False,
            )
            db.session.add(existing)
            db.session.commit()

            # Should return existing non-default template
            result = get_or_create_default_template(test_user["id"])
            assert result.id == existing.id
            assert result.name == "Non-Default Template"

    def test_creates_default_if_none_exists(self, app, test_user):
        """Test that a default template is created if none exists."""
        with app.app_context():
            # Ensure no templates exist
            assert Template.query.filter_by(user_id=test_user["id"]).count() == 0

            # Should create a new default template
            result = get_or_create_default_template(test_user["id"])
            assert result is not None
            assert result.name == "Standard-Vorlage (automatisch erstellt)"
            assert result.is_default is True

    def test_does_not_create_duplicate(self, app, test_user):
        """Test that calling twice doesn't create duplicates."""
        with app.app_context():
            # First call creates template
            result1 = get_or_create_default_template(test_user["id"])

            # Second call should return the same template
            result2 = get_or_create_default_template(test_user["id"])

            assert result1.id == result2.id
            assert Template.query.filter_by(user_id=test_user["id"]).count() == 1


class TestDefaultTemplateContent:
    """Tests for the default template content."""

    def test_default_template_is_valid_german(self):
        """Test that the default template contains proper German text."""
        # Check for common German business letter elements
        assert "Mit freundlichen Grüßen" in DEFAULT_GERMAN_TEMPLATE
        assert "Vorstellungsgespräch" in DEFAULT_GERMAN_TEMPLATE

    def test_default_template_has_professional_structure(self):
        """Test that the template has a logical structure."""
        lines = DEFAULT_GERMAN_TEMPLATE.strip().split("\n")

        # Should start with sender name placeholder (letterhead)
        assert "{{NAME}}" in lines[0]

        # Should end with sender name (signature)
        assert "{{NAME}}" in lines[-1]

        # Should contain closing
        assert "Mit freundlichen Grüßen" in DEFAULT_GERMAN_TEMPLATE

        # Should contain date and city
        assert "{{DATUM}}" in DEFAULT_GERMAN_TEMPLATE
        assert "{{STADT}}" in DEFAULT_GERMAN_TEMPLATE
