"""
Tests for PDF Template Modifier Service.

Tests cover:
- generate_from_template() with variable replacements
- generate_from_template_bytes() for byte input
- Font resolution and mapping
- Multi-page support
- Text fitting and wrapping
- Preview positions functionality
- Error handling
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPDFTemplateModifier:
    """Test suite for PDFTemplateModifier class."""

    @pytest.fixture
    def modifier(self):
        """Create modifier instance."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            return PDFTemplateModifier()

    @pytest.fixture
    def sample_positions(self):
        """Sample variable positions for testing."""
        return {
            "FIRMA": {
                "x": 100,
                "y": 200,
                "width": 150,
                "height": 20,
                "page": 0,
                "font_size": 12.0,
                "font_name": "Helvetica",
            },
            "POSITION": {
                "x": 100,
                "y": 250,
                "width": 200,
                "height": 20,
                "page": 0,
                "font_size": 14.0,
                "font_name": "Arial-Bold",
            },
        }

    @pytest.fixture
    def sample_replacements(self):
        """Sample replacement values for testing."""
        return {
            "FIRMA": "Muster GmbH",
            "POSITION": "Software Developer",
        }

    @pytest.fixture
    def mock_fitz_doc(self):
        """Create mock fitz document."""
        mock_doc = MagicMock()
        mock_page = MagicMock()

        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, i: mock_page
        mock_doc.close = MagicMock()
        mock_doc.save = MagicMock()

        mock_page.add_redact_annot = MagicMock()
        mock_page.apply_redactions = MagicMock()
        mock_page.insert_text = MagicMock()
        mock_page.insert_textbox = MagicMock()
        mock_page.draw_rect = MagicMock()

        return mock_doc, mock_page

    def test_generate_from_template_basic(self, sample_positions, sample_replacements, mock_fitz_doc):
        """Test basic PDF generation with variable replacements."""
        mock_doc, mock_page = mock_fitz_doc

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = MagicMock(return_value=50)  # Text fits

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            result = modifier.generate_from_template(
                pdf_path="/fake/template.pdf",
                variable_positions=sample_positions,
                replacements=sample_replacements,
            )

            # Verify document was opened
            mock_fitz.open.assert_called_once_with("/fake/template.pdf")

            # Verify redactions were applied
            assert mock_page.add_redact_annot.called
            assert mock_page.apply_redactions.called

            # Verify text was inserted
            assert mock_page.insert_text.called

            # Verify document was saved and closed
            assert mock_doc.save.called
            assert mock_doc.close.called

            # Result should be bytes
            assert isinstance(result, bytes)

    def test_generate_from_template_bytes(self, sample_positions, sample_replacements, mock_fitz_doc):
        """Test PDF generation from bytes input."""
        mock_doc, mock_page = mock_fitz_doc
        pdf_bytes = b"%PDF-1.4 fake content"

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = MagicMock(return_value=50)

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            result = modifier.generate_from_template_bytes(
                pdf_bytes=pdf_bytes,
                variable_positions=sample_positions,
                replacements=sample_replacements,
            )

            # Verify document was opened from bytes
            mock_fitz.open.assert_called_once_with(stream=pdf_bytes, filetype="pdf")

            assert isinstance(result, bytes)

    def test_skips_variables_without_replacement(self, mock_fitz_doc):
        """Test that variables without replacements are skipped."""
        mock_doc, mock_page = mock_fitz_doc

        positions = {
            "FIRMA": {"x": 100, "y": 200, "width": 150, "height": 20, "page": 0, "font_size": 12.0},
            "UNUSED": {"x": 100, "y": 300, "width": 150, "height": 20, "page": 0, "font_size": 12.0},
        }
        replacements = {"FIRMA": "Test GmbH"}  # No replacement for UNUSED

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = MagicMock(return_value=50)

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            modifier.generate_from_template("/fake/template.pdf", positions, replacements)

            # Only one redaction should be added (for FIRMA, not UNUSED)
            assert mock_page.add_redact_annot.call_count == 1

    def test_skips_replacement_without_position(self, mock_fitz_doc):
        """Test that replacements without positions are skipped."""
        mock_doc, mock_page = mock_fitz_doc

        positions = {"FIRMA": {"x": 100, "y": 200, "width": 150, "height": 20, "page": 0, "font_size": 12.0}}
        replacements = {"FIRMA": "Test GmbH", "EXTRA": "No Position"}  # EXTRA has no position

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = MagicMock(return_value=50)

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            modifier.generate_from_template("/fake/template.pdf", positions, replacements)

            # Should complete without error, only inserting FIRMA
            assert mock_page.insert_text.call_count >= 1

    def test_multipage_support(self, sample_replacements):
        """Test handling of multi-page PDFs."""
        mock_doc = MagicMock()
        mock_page0 = MagicMock()
        mock_page1 = MagicMock()

        mock_doc.__len__ = lambda self: 2
        mock_doc.__getitem__ = lambda self, i: mock_page0 if i == 0 else mock_page1
        mock_doc.close = MagicMock()
        mock_doc.save = MagicMock()

        positions = {
            "FIRMA": {"x": 100, "y": 200, "width": 150, "height": 20, "page": 0, "font_size": 12.0},
            "POSITION": {"x": 100, "y": 200, "width": 150, "height": 20, "page": 1, "font_size": 12.0},
        }

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = MagicMock(return_value=50)

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            modifier.generate_from_template("/fake/template.pdf", positions, sample_replacements)

            # Page 0 should have FIRMA redaction
            assert mock_page0.add_redact_annot.called
            # Page 1 should have POSITION redaction
            assert mock_page1.add_redact_annot.called

    def test_invalid_page_number_warning(self, sample_replacements, mock_fitz_doc):
        """Test handling of invalid page numbers in positions."""
        mock_doc, mock_page = mock_fitz_doc

        positions = {
            "FIRMA": {"x": 100, "y": 200, "width": 150, "height": 20, "page": 99, "font_size": 12.0}  # Invalid page
        }

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            # Should not raise, just skip the invalid page
            modifier.generate_from_template("/fake/template.pdf", positions, sample_replacements)

            # No redactions should be applied (page 99 doesn't exist)
            assert not mock_page.add_redact_annot.called

    def test_font_resolution_helvetica(self):
        """Test font name resolution for Helvetica variants."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            assert modifier._resolve_font("Helvetica") == "helv"
            assert modifier._resolve_font("helvetica-bold") == "hebo"
            assert modifier._resolve_font("Helvetica-Oblique") == "heit"

    def test_font_resolution_times(self):
        """Test font name resolution for Times variants."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            assert modifier._resolve_font("Times") == "tiro"
            assert modifier._resolve_font("times-roman") == "tiro"
            assert modifier._resolve_font("Times-Bold") == "tibo"

    def test_font_resolution_courier(self):
        """Test font name resolution for Courier variants."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            assert modifier._resolve_font("Courier") == "cour"
            assert modifier._resolve_font("courier-bold") == "cobo"

    def test_font_resolution_unknown_defaults_to_helvetica(self):
        """Test that unknown fonts default to Helvetica."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            assert modifier._resolve_font("UnknownFont") == "helv"
            assert modifier._resolve_font("Comic Sans MS") == "helv"
            assert modifier._resolve_font(None) == "helv"

    def test_font_resolution_bold_italic_detection(self):
        """Test detection of bold/italic in font names."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            # Should detect bold
            assert modifier._resolve_font("SomeFont-Bold") == "hebo"
            # Should detect italic
            assert modifier._resolve_font("SomeFont-Italic") == "heit"
            # Should detect bold italic
            assert modifier._resolve_font("SomeFont-BoldItalic") == "hebi"

    def test_text_fitting_reduces_font_size(self, mock_fitz_doc):
        """Test that font size is reduced if text doesn't fit."""
        mock_doc, mock_page = mock_fitz_doc

        positions = {"FIRMA": {"x": 100, "y": 200, "width": 50, "height": 20, "page": 0, "font_size": 12.0}}
        replacements = {"FIRMA": "Very Long Company Name That Needs Reduction"}

        call_count = [0]

        def mock_text_length(text, fontname, fontsize):
            # First calls return too long, then eventually fit
            call_count[0] += 1
            if fontsize >= 10:
                return 200  # Too wide
            return 40  # Fits

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock(width=50, height=20, x0=100, y0=200))
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = mock_text_length
            mock_fitz.TEXT_ALIGN_LEFT = 0

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            modifier.generate_from_template("/fake/template.pdf", positions, replacements)

            # Font size reduction should have been attempted
            assert call_count[0] > 1

    def test_preview_positions(self, sample_positions, mock_fitz_doc):
        """Test preview_positions draws colored rectangles."""
        mock_doc, mock_page = mock_fitz_doc

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            result = modifier.preview_positions("/fake/template.pdf", sample_positions)

            # Should draw rectangles for each variable
            assert mock_page.draw_rect.call_count == 2
            # Should add labels
            assert mock_page.insert_text.call_count == 2

            assert isinstance(result, bytes)

    def test_extract_text_at_position(self, mock_fitz_doc):
        """Test extracting text at a specific position."""
        mock_doc, mock_page = mock_fitz_doc
        mock_page.get_text.return_value = "Extracted Text"

        position = {"x": 100, "y": 200, "width": 150, "height": 20, "page": 0}

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            text = modifier.extract_text_at_position("/fake/template.pdf", position)

            assert text == "Extracted Text"
            mock_page.get_text.assert_called_once()

    def test_file_not_found_error(self):
        """Test error handling for missing PDF file."""
        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.side_effect = Exception("File not found")

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            with pytest.raises(FileNotFoundError, match="Could not open PDF"):
                modifier.generate_from_template("/nonexistent/path.pdf", {}, {})

    def test_invalid_pdf_bytes_error(self):
        """Test error handling for invalid PDF bytes."""
        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.side_effect = Exception("Invalid PDF")

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            with pytest.raises(ValueError, match="Could not open PDF from bytes"):
                modifier.generate_from_template_bytes(b"not a pdf", {}, {})

    def test_modification_error_handling(self, mock_fitz_doc):
        """Test error handling during PDF modification."""
        mock_doc, mock_page = mock_fitz_doc
        mock_page.add_redact_annot.side_effect = Exception("Redaction failed")

        positions = {"FIRMA": {"x": 100, "y": 200, "width": 150, "height": 20, "page": 0, "font_size": 12.0}}
        replacements = {"FIRMA": "Test"}

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock())

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()

            with pytest.raises(ValueError, match="Failed to modify PDF"):
                modifier.generate_from_template("/fake/template.pdf", positions, replacements)

    def test_empty_positions_and_replacements(self, mock_fitz_doc):
        """Test handling of empty positions and replacements."""
        mock_doc, mock_page = mock_fitz_doc

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            result = modifier.generate_from_template("/fake/template.pdf", {}, {})

            # Should succeed without modifications
            assert isinstance(result, bytes)
            assert not mock_page.add_redact_annot.called
            assert not mock_page.insert_text.called

    def test_rect_creation_from_position(self):
        """Test rectangle creation from position dictionary."""
        with patch("services.pdf_template_modifier.fitz"):
            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            position = {"x": 100, "y": 200, "width": 150, "height": 20}

            with patch("services.pdf_template_modifier.fitz.Rect") as mock_rect:
                modifier._get_rect_from_position(position)
                mock_rect.assert_called_once_with(100, 200, 250, 220)  # x, y, x+width, y+height

    def test_default_values_in_position(self, mock_fitz_doc):
        """Test that default values are used for missing position fields."""
        mock_doc, mock_page = mock_fitz_doc

        # Position with minimal fields
        positions = {"FIRMA": {"page": 0}}  # Missing x, y, width, height, font_size, font_name
        replacements = {"FIRMA": "Test"}

        with patch("services.pdf_template_modifier.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.Rect = MagicMock(side_effect=lambda *args: MagicMock(width=100, height=20, x0=0, y0=0))
            mock_fitz.Point = MagicMock(side_effect=lambda *args: MagicMock())
            mock_fitz.get_text_length = MagicMock(return_value=50)

            from services.pdf_template_modifier import PDFTemplateModifier

            modifier = PDFTemplateModifier()
            # Should not raise, uses default values
            modifier.generate_from_template("/fake/template.pdf", positions, replacements)

            assert mock_page.add_redact_annot.called
