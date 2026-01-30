"""
PDF Template Extractor Service

Uses PyMuPDF (fitz) for position-aware text extraction with OCR fallback
for scanned PDFs using pytesseract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fitz  # PyMuPDF - only for type checking

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment, misc]

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError:
    pytesseract = None  # type: ignore[assignment]
    convert_from_path = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]


@dataclass
class TextBlock:
    """Represents a text block with position and font information."""

    text: str
    x: float
    y: float
    width: float
    height: float
    font_name: str
    font_size: float
    page: int


class PDFTemplateExtractor:
    """
    Extracts text from PDFs with position and font information.

    Uses PyMuPDF for native PDF text extraction and falls back to
    pytesseract OCR for scanned PDFs.
    """

    def __init__(self, ocr_language: str = "deu"):
        """
        Initialize the extractor.

        Args:
            ocr_language: Language code for OCR (default: 'deu' for German)
        """
        if fitz is None:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF template extraction. "
                "Install it with: pip install PyMuPDF"
            )
        self.ocr_language = ocr_language

    def extract_text_with_positions(self, pdf_path: str) -> dict:
        """
        Extract text blocks with their positions and font information.

        Returns dict with 'text_blocks' list, each containing:
        - text: str
        - x: float
        - y: float
        - width: float
        - height: float
        - font_name: str
        - font_size: float
        - page: int

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with 'text_blocks' list and metadata
        """
        text_blocks = []

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                # Extract text blocks with detailed information
                blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

                for block in blocks:
                    # Skip image blocks (type 1), only process text blocks (type 0)
                    if block.get("type") != 0:
                        continue

                    # Process each line in the block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if not text:
                                continue

                            bbox = span.get("bbox", (0, 0, 0, 0))
                            text_blocks.append(
                                {
                                    "text": text,
                                    "x": bbox[0],
                                    "y": bbox[1],
                                    "width": bbox[2] - bbox[0],
                                    "height": bbox[3] - bbox[1],
                                    "font_name": span.get("font", "unknown"),
                                    "font_size": span.get("size", 0.0),
                                    "page": page_num,
                                }
                            )

            doc.close()

            # OCR fallback for scanned PDFs (no text extracted)
            if not text_blocks:
                text_blocks = self._extract_with_ocr(pdf_path)

        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}") from e

        return {
            "text_blocks": text_blocks,
            "total_blocks": len(text_blocks),
            "source": "ocr" if self._is_ocr_result(text_blocks) else "native",
        }

    def _extract_with_ocr(self, pdf_path: str) -> list[dict]:
        """
        Extract text using OCR for scanned PDFs.

        Uses pytesseract with detailed output to get position information.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of text block dictionaries
        """
        text_blocks = []

        try:
            images = convert_from_path(pdf_path)

            for page_num, image in enumerate(images):
                # Use pytesseract with detailed output for position data
                ocr_data = pytesseract.image_to_data(
                    image, lang=self.ocr_language, output_type=pytesseract.Output.DICT
                )

                n_boxes = len(ocr_data["text"])
                for i in range(n_boxes):
                    text = ocr_data["text"][i].strip()
                    confidence = int(ocr_data["conf"][i])

                    # Skip empty text or low confidence results
                    if not text or confidence < 0:
                        continue

                    text_blocks.append(
                        {
                            "text": text,
                            "x": float(ocr_data["left"][i]),
                            "y": float(ocr_data["top"][i]),
                            "width": float(ocr_data["width"][i]),
                            "height": float(ocr_data["height"][i]),
                            "font_name": "ocr_detected",
                            "font_size": 0.0,  # OCR cannot determine font size
                            "page": page_num,
                        }
                    )

        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}") from e

        return text_blocks

    def _is_ocr_result(self, text_blocks: list[dict]) -> bool:
        """Check if text blocks are from OCR extraction."""
        if not text_blocks:
            return False
        return text_blocks[0].get("font_name") == "ocr_detected"

    def get_plain_text(self, pdf_path: str) -> str:
        """
        Extract plain text from PDF without position information.

        Preserves paragraph structure by detecting line breaks based on
        vertical spacing between text blocks.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Plain text with preserved paragraphs and line breaks
        """
        result = self.extract_text_with_positions(pdf_path)
        text_blocks = result.get("text_blocks", [])

        if not text_blocks:
            return ""

        # Group blocks by page and sort by position (top to bottom, left to right)
        pages: dict[int, list[dict]] = {}
        for block in text_blocks:
            page_num = block["page"]
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(block)

        # Sort blocks within each page by y position, then x position
        for page_num in pages:
            pages[page_num].sort(key=lambda b: (b["y"], b["x"]))

        # Concatenate text from all pages, preserving line breaks
        plain_text_parts = []
        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]
            if not page_blocks:
                continue

            # Build page text with line break detection
            lines: list[str] = []
            current_line: list[str] = []
            prev_y: float | None = None
            prev_height: float = 12.0  # Default line height

            for block in page_blocks:
                curr_y = block["y"]
                curr_height = block.get("height", 12.0)

                if prev_y is not None:
                    # Calculate vertical gap between blocks
                    y_gap = curr_y - prev_y

                    # If gap is larger than 1.5x the line height, it's a new paragraph
                    if y_gap > prev_height * 1.8:
                        # Save current line and add paragraph break
                        if current_line:
                            lines.append(" ".join(current_line))
                            current_line = []
                        lines.append("")  # Empty line for paragraph break
                    # If gap is larger than line height, it's a new line
                    elif y_gap > prev_height * 0.8:
                        if current_line:
                            lines.append(" ".join(current_line))
                            current_line = []

                current_line.append(block["text"])
                prev_y = curr_y + curr_height
                prev_height = curr_height if curr_height > 0 else prev_height

            # Don't forget the last line
            if current_line:
                lines.append(" ".join(current_line))

            # Join lines and add to page parts
            page_text = "\n".join(lines)
            plain_text_parts.append(page_text)

        return "\n\n".join(plain_text_parts)

    def extract_by_region(
        self,
        pdf_path: str,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        page: int | None = None,
    ) -> list[dict]:
        """
        Extract text blocks within a specific region.

        Args:
            pdf_path: Path to the PDF file
            x_min: Minimum x coordinate
            y_min: Minimum y coordinate
            x_max: Maximum x coordinate
            y_max: Maximum y coordinate
            page: Specific page number (None for all pages)

        Returns:
            List of text blocks within the region
        """
        result = self.extract_text_with_positions(pdf_path)
        text_blocks = result.get("text_blocks", [])

        filtered_blocks = []
        for block in text_blocks:
            # Filter by page if specified
            if page is not None and block["page"] != page:
                continue

            # Check if block is within the region
            block_x = block["x"]
            block_y = block["y"]
            block_x_max = block_x + block["width"]
            block_y_max = block_y + block["height"]

            # Block is within region if it overlaps
            if block_x_max >= x_min and block_x <= x_max and block_y_max >= y_min and block_y <= y_max:
                filtered_blocks.append(block)

        return filtered_blocks

    def get_text_by_font(
        self, pdf_path: str, font_name: str | None = None, min_font_size: float | None = None
    ) -> list[dict]:
        """
        Extract text blocks filtered by font properties.

        Args:
            pdf_path: Path to the PDF file
            font_name: Filter by font name (substring match)
            min_font_size: Minimum font size filter

        Returns:
            List of text blocks matching the font criteria
        """
        result = self.extract_text_with_positions(pdf_path)
        text_blocks = result.get("text_blocks", [])

        filtered_blocks = []
        for block in text_blocks:
            # Filter by font name if specified
            if font_name is not None:
                if font_name.lower() not in block["font_name"].lower():
                    continue

            # Filter by minimum font size if specified
            if min_font_size is not None:
                if block["font_size"] < min_font_size:
                    continue

            filtered_blocks.append(block)

        return filtered_blocks

    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in the PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages
        """
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            raise RuntimeError(f"Failed to get page count: {e}") from e

    def get_page_dimensions(self, pdf_path: str, page_num: int = 0) -> dict:
        """
        Get the dimensions of a specific page.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)

        Returns:
            Dictionary with 'width' and 'height'
        """
        try:
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                doc.close()
                raise ValueError(f"Page {page_num} does not exist (total pages: {len(doc)})")

            page = doc[page_num]
            rect = page.rect
            dimensions = {"width": rect.width, "height": rect.height}
            doc.close()
            return dimensions
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to get page dimensions: {e}") from e
