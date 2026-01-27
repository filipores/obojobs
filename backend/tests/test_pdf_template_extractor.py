"""
Tests for PDF Template Extractor Service.

Tests cover:
- extract_text_with_positions() with native PDF text
- get_plain_text() text concatenation
- OCR fallback for scanned PDFs
- Region-based extraction
- Font-based filtering
- Error handling
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPDFTemplateExtractor:
    """Test suite for PDFTemplateExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance with mocked dependencies."""
        with patch("services.pdf_template_extractor.fitz"):
            from services.pdf_template_extractor import PDFTemplateExtractor

            return PDFTemplateExtractor(ocr_language="deu")

    @pytest.fixture
    def mock_fitz_doc(self):
        """Create mock fitz document with text blocks."""
        mock_doc = MagicMock()
        mock_page = MagicMock()

        # Mock text extraction result
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,  # Text block
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Firma GmbH",
                                    "bbox": (100, 50, 200, 70),
                                    "font": "Helvetica",
                                    "size": 12.0,
                                }
                            ]
                        }
                    ],
                },
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Software Developer",
                                    "bbox": (100, 100, 250, 120),
                                    "font": "Arial-Bold",
                                    "size": 14.0,
                                }
                            ]
                        }
                    ],
                },
                {
                    "type": 1,  # Image block - should be skipped
                    "image": "some_image_data",
                },
            ]
        }

        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.__len__ = lambda self: 1
        mock_doc.close = MagicMock()

        return mock_doc

    def test_extract_text_with_positions_native(self, mock_fitz_doc):
        """Test native PDF text extraction with position data."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            result = extractor.extract_text_with_positions("/fake/path.pdf")

            assert result["source"] == "native"
            assert result["total_blocks"] == 2
            assert len(result["text_blocks"]) == 2

            # Check first block
            block1 = result["text_blocks"][0]
            assert block1["text"] == "Firma GmbH"
            assert block1["x"] == 100
            assert block1["y"] == 50
            assert block1["width"] == 100  # 200 - 100
            assert block1["height"] == 20  # 70 - 50
            assert block1["font_name"] == "Helvetica"
            assert block1["font_size"] == 12.0
            assert block1["page"] == 0

            # Check second block
            block2 = result["text_blocks"][1]
            assert block2["text"] == "Software Developer"
            assert block2["font_name"] == "Arial-Bold"
            assert block2["font_size"] == 14.0

    def test_extract_text_with_positions_skips_images(self, mock_fitz_doc):
        """Test that image blocks are skipped during extraction."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            result = extractor.extract_text_with_positions("/fake/path.pdf")

            # Should only have 2 text blocks, not 3 (image block skipped)
            assert result["total_blocks"] == 2

    def test_extract_text_with_positions_skips_empty_text(self):
        """Test that empty text spans are skipped."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {"text": "  ", "bbox": (0, 0, 10, 10), "font": "Arial", "size": 12},
                                {"text": "Valid", "bbox": (20, 0, 50, 10), "font": "Arial", "size": 12},
                            ]
                        }
                    ],
                }
            ]
        }
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.close = MagicMock()

        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            result = extractor.extract_text_with_positions("/fake/path.pdf")

            # Only "Valid" should be extracted, empty text skipped
            assert result["total_blocks"] == 1
            assert result["text_blocks"][0]["text"] == "Valid"

    def test_ocr_fallback_when_no_native_text(self):
        """Test OCR fallback is triggered for scanned PDFs."""
        # Mock empty native extraction
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {"blocks": []}
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.close = MagicMock()

        # Mock OCR results
        mock_ocr_data = {
            "text": ["Hello", "World", ""],
            "conf": [90, 85, -1],  # -1 means no detection
            "left": [10, 10, 0],
            "top": [20, 40, 0],
            "width": [50, 60, 0],
            "height": [15, 15, 0],
        }

        with (
            patch("services.pdf_template_extractor.fitz") as mock_fitz,
            patch("services.pdf_template_extractor.convert_from_path") as mock_convert,
            patch("services.pdf_template_extractor.pytesseract") as mock_tesseract,
        ):
            mock_fitz.open.return_value = mock_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1
            mock_convert.return_value = [MagicMock()]  # One page image
            mock_tesseract.image_to_data.return_value = mock_ocr_data
            mock_tesseract.Output.DICT = "dict"

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor(ocr_language="deu")
            result = extractor.extract_text_with_positions("/fake/scanned.pdf")

            assert result["source"] == "ocr"
            assert result["total_blocks"] == 2  # Only 2 valid blocks (empty and low conf skipped)

            block1 = result["text_blocks"][0]
            assert block1["text"] == "Hello"
            assert block1["font_name"] == "ocr_detected"
            assert block1["font_size"] == 0.0  # OCR cannot determine font size

    def test_get_plain_text_concatenation(self, mock_fitz_doc):
        """Test plain text extraction concatenates blocks correctly."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            text = extractor.get_plain_text("/fake/path.pdf")

            assert "Firma GmbH" in text
            assert "Software Developer" in text

    def test_get_plain_text_sorts_by_position(self):
        """Test that plain text is sorted by position (top to bottom, left to right)."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {"spans": [{"text": "Bottom", "bbox": (10, 100, 50, 110), "font": "Arial", "size": 12}]}
                    ],
                },
                {
                    "type": 0,
                    "lines": [{"spans": [{"text": "Top", "bbox": (10, 10, 50, 20), "font": "Arial", "size": 12}]}],
                },
            ]
        }
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.close = MagicMock()

        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            text = extractor.get_plain_text("/fake/path.pdf")

            # "Top" should come before "Bottom" in sorted output
            assert text.index("Top") < text.index("Bottom")

    def test_get_plain_text_empty_pdf(self):
        """Test plain text extraction returns empty string for empty PDF."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {"blocks": []}
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.close = MagicMock()

        with (
            patch("services.pdf_template_extractor.fitz") as mock_fitz,
            patch("services.pdf_template_extractor.convert_from_path") as mock_convert,
            patch("services.pdf_template_extractor.pytesseract") as mock_tesseract,
        ):
            mock_fitz.open.return_value = mock_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1
            mock_convert.return_value = []  # No pages
            mock_tesseract.Output.DICT = "dict"

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            text = extractor.get_plain_text("/fake/empty.pdf")

            assert text == ""

    def test_extract_by_region(self, mock_fitz_doc):
        """Test region-based text extraction."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            # Extract from region that only contains first block
            blocks = extractor.extract_by_region("/fake/path.pdf", 90, 40, 210, 80)

            assert len(blocks) == 1
            assert blocks[0]["text"] == "Firma GmbH"

    def test_extract_by_region_with_page_filter(self, mock_fitz_doc):
        """Test region extraction with page filter."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            # Extract from page 0
            blocks = extractor.extract_by_region("/fake/path.pdf", 0, 0, 500, 500, page=0)
            assert len(blocks) == 2

            # Extract from non-existent page 1
            blocks = extractor.extract_by_region("/fake/path.pdf", 0, 0, 500, 500, page=1)
            assert len(blocks) == 0

    def test_get_text_by_font_name_filter(self, mock_fitz_doc):
        """Test font name filtering."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            # Filter by Arial font
            blocks = extractor.get_text_by_font("/fake/path.pdf", font_name="Arial")

            assert len(blocks) == 1
            assert blocks[0]["text"] == "Software Developer"

    def test_get_text_by_font_size_filter(self, mock_fitz_doc):
        """Test minimum font size filtering."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_fitz_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            # Filter by min font size 13
            blocks = extractor.get_text_by_font("/fake/path.pdf", min_font_size=13.0)

            assert len(blocks) == 1
            assert blocks[0]["text"] == "Software Developer"
            assert blocks[0]["font_size"] == 14.0

    def test_get_page_count(self):
        """Test page count retrieval."""
        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 5
        mock_doc.close = MagicMock()

        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            count = extractor.get_page_count("/fake/path.pdf")

            assert count == 5

    def test_get_page_dimensions(self):
        """Test page dimensions retrieval."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect = MagicMock()
        mock_page.rect.width = 612.0  # Letter size width in points
        mock_page.rect.height = 792.0  # Letter size height in points
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, i: mock_page
        mock_doc.close = MagicMock()

        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            dims = extractor.get_page_dimensions("/fake/path.pdf", page_num=0)

            assert dims["width"] == 612.0
            assert dims["height"] == 792.0

    def test_get_page_dimensions_invalid_page(self):
        """Test error handling for invalid page number."""
        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 1
        mock_doc.close = MagicMock()

        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            with pytest.raises(ValueError, match="Page 5 does not exist"):
                extractor.get_page_dimensions("/fake/path.pdf", page_num=5)

    def test_extract_text_error_handling(self):
        """Test error handling for failed PDF opening."""
        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.side_effect = Exception("File not found")

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            with pytest.raises(RuntimeError, match="Failed to extract text"):
                extractor.extract_text_with_positions("/nonexistent/path.pdf")

    def test_ocr_error_handling(self):
        """Test error handling for OCR failures."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {"blocks": []}  # No native text
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.close = MagicMock()

        with (
            patch("services.pdf_template_extractor.fitz") as mock_fitz,
            patch("services.pdf_template_extractor.convert_from_path") as mock_convert,
        ):
            mock_fitz.open.return_value = mock_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1
            mock_convert.side_effect = Exception("PDF conversion failed")

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()

            with pytest.raises(RuntimeError, match="OCR extraction failed"):
                extractor.extract_text_with_positions("/fake/scanned.pdf")

    def test_multipage_extraction(self):
        """Test extraction from multi-page PDF."""
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()

        mock_page1.get_text.return_value = {
            "blocks": [
                {"type": 0, "lines": [{"spans": [{"text": "Page 1", "bbox": (0, 0, 50, 10), "font": "Arial", "size": 12}]}]}
            ]
        }
        mock_page2.get_text.return_value = {
            "blocks": [
                {"type": 0, "lines": [{"spans": [{"text": "Page 2", "bbox": (0, 0, 50, 10), "font": "Arial", "size": 12}]}]}
            ]
        }

        mock_doc.__iter__ = lambda self: iter([mock_page1, mock_page2])
        mock_doc.close = MagicMock()

        with patch("services.pdf_template_extractor.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            mock_fitz.TEXT_PRESERVE_WHITESPACE = 1

            from services.pdf_template_extractor import PDFTemplateExtractor

            extractor = PDFTemplateExtractor()
            result = extractor.extract_text_with_positions("/fake/multipage.pdf")

            assert result["total_blocks"] == 2
            assert result["text_blocks"][0]["page"] == 0
            assert result["text_blocks"][0]["text"] == "Page 1"
            assert result["text_blocks"][1]["page"] == 1
            assert result["text_blocks"][1]["text"] == "Page 2"
