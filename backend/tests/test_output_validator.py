"""Tests for the output validation pipeline."""

from services.output_validator import OutputValidator


class TestOutputValidator:
    def setup_method(self):
        self.validator = OutputValidator()

    def test_valid_letter_passes(self):
        text = """Sehr geehrte Frau Schmidt,

als erfahrener Softwareentwickler mit Schwerpunkt auf Python und Flask bewerbe ich mich bei Ihnen auf die ausgeschriebene Stelle. In meiner bisherigen Position bei der Muster GmbH habe ich mehrere Webapplikationen entwickelt und betreut, darunter ein umfangreiches Kundenportal mit über 5.000 aktiven Nutzern.

Besonders meine Erfahrung mit REST APIs und Datenbankdesign passt gut zu den Anforderungen Ihrer Stelle. Bei meinem letzten Arbeitgeber habe ich ein Team von drei Entwicklern koordiniert und erfolgreich ein E-Commerce-Projekt abgeschlossen. Dabei habe ich die gesamte Backend-Architektur entworfen und die Datenbankmigrationen geplant. Die enge Zusammenarbeit mit dem Frontend-Team hat mir gezeigt, wie wichtig klare API-Dokumentation und gute Kommunikation sind.

Darüber hinaus habe ich in meiner Freizeit Open-Source-Projekte betreut und regelmäßig an Meetups in der lokalen Developer-Community teilgenommen. Diese Erfahrungen haben meinen Blick für sauberen, wartbaren Code geschärft.

Ich freue mich auf ein persönliches Gespräch, um meine Qualifikationen und meine Motivation für die Stelle näher zu erläutern. Gerne stehe ich Ihnen ab sofort zur Verfügung.

Mit freundlichen Grüßen
Max Mustermann"""
        result = self.validator.validate(text)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_too_short_letter_has_error(self):
        text = "Sehr geehrte Damen und Herren, ich bewerbe mich. Mit freundlichen Grüßen"
        result = self.validator.validate(text)
        assert not result.is_valid
        assert any("zu kurz" in e for e in result.errors)

    def test_missing_greeting_warning(self):
        text = "Ich möchte mich bewerben. " * 40 + "\nMit freundlichen Grüßen\nMax"
        result = self.validator.validate(text)
        assert any("Anrede" in w for w in result.warnings)

    def test_missing_closing_warning(self):
        text = "Sehr geehrte Damen und Herren,\n\n" + "Ich habe Erfahrung. " * 40
        result = self.validator.validate(text)
        assert any("Grußformel" in w for w in result.warnings)

    def test_ich_repetition_warning(self):
        text = "Sehr geehrte Damen und Herren,\n\n"
        text += "Ich kann das. Ich mache das. Ich bin gut. Ich habe Erfahrung. Ich freue mich. Ich bin motiviert. " * 5
        text += "\n\nMit freundlichen Grüßen\nMax"
        result = self.validator.validate(text)
        assert any("Ich" in w for w in result.warnings)

    def test_dash_warning(self):
        text = "Sehr geehrte Damen und Herren,\n\n"
        text += "Ich bin Entwickler – mit viel Erfahrung. " * 20
        text += "\n\nMit freundlichen Grüßen\nMax"
        result = self.validator.validate(text)
        assert any("Gedankenstriche" in w for w in result.warnings)

    def test_skill_hallucination_detection(self):
        text = "Sehr geehrte Damen und Herren,\n\n"
        text += "Ich habe Erfahrung mit React, Angular und Kubernetes. " * 10
        text += "\n\nMit freundlichen Grüßen\nMax"
        cv = "Python, Flask, SQL, Docker"
        result = self.validator.validate(text, cv_text=cv)
        assert any("erfundene Skills" in w for w in result.warnings)
        assert "react" in result.metrics.get("potentially_hallucinated_skills", [])

    def test_metrics_populated(self):
        text = "Sehr geehrte Damen und Herren,\n\n" + "Test Satz hier. " * 50 + "\n\nMit freundlichen Grüßen\nMax"
        result = self.validator.validate(text)
        assert "word_count" in result.metrics
        assert "paragraph_count" in result.metrics
