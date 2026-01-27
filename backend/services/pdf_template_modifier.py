"""
PDF Template Modifier Service

Uses PyMuPDF (fitz) to modify PDF templates by redacting placeholder text
and inserting replacement values while preserving the original layout.
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import fitz  # PyMuPDF - only for type checking

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


class VariablePosition(TypedDict):
    """Type definition for variable position data."""

    x: float
    y: float
    width: float
    height: float
    page: int
    font_size: float
    font_name: str | None


class PDFTemplateModifier:
    """
    Service class for modifying PDF templates by replacing placeholder text.

    Uses PyMuPDF (fitz) to:
    1. Redact original text at specified positions
    2. Insert replacement text with similar font/size
    3. Preserve all other PDF content (images, layout, etc.)
    """

    # Default font to use when the original font is not available
    DEFAULT_FONT = "helv"  # Helvetica in PyMuPDF
    DEFAULT_FONT_SIZE = 12.0

    # Mapping of common font names to PyMuPDF built-in fonts
    FONT_MAPPING = {
        "helvetica": "helv",
        "helvetica-bold": "hebo",
        "helvetica-oblique": "heit",
        "helvetica-boldoblique": "hebi",
        "times": "tiro",
        "times-roman": "tiro",
        "times-bold": "tibo",
        "times-italic": "tiit",
        "times-bolditalic": "tibi",
        "courier": "cour",
        "courier-bold": "cobo",
        "courier-oblique": "coit",
        "courier-boldoblique": "cobi",
        "symbol": "symb",
        "zapfdingbats": "zadb",
    }

    def __init__(self):
        """Initialize the PDF Template Modifier."""
        if fitz is None:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF template modification. "
                "Install it with: pip install PyMuPDF"
            )

    def generate_from_template(
        self,
        pdf_path: str,
        variable_positions: dict[str, VariablePosition],
        replacements: dict[str, str],
    ) -> bytes:
        """
        Generate a modified PDF by replacing placeholder text at specified positions.

        Args:
            pdf_path: Path to the PDF template file.
            variable_positions: Dictionary mapping variable names to their positions.
                Format:
                {
                    "FIRMA": {
                        "x": 100,
                        "y": 200,
                        "width": 150,
                        "height": 20,
                        "page": 0,
                        "font_size": 12,
                        "font_name": "Helvetica"  # optional
                    },
                    ...
                }
            replacements: Dictionary mapping variable names to replacement text.
                Format:
                {
                    "FIRMA": "Muster GmbH",
                    "POSITION": "Software Engineer"
                }

        Returns:
            bytes: The modified PDF as bytes.

        Raises:
            FileNotFoundError: If the PDF template file does not exist.
            ValueError: If the PDF cannot be processed.
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"Failed to open PDF file: {pdf_path}, error: {e}")
            raise FileNotFoundError(f"Could not open PDF file: {pdf_path}") from e

        try:
            # First pass: Apply redactions for all variables that have replacements
            self._apply_redactions(doc, variable_positions, replacements)

            # Second pass: Insert replacement text
            self._insert_replacements(doc, variable_positions, replacements)

            # Save to bytes
            output_buffer = io.BytesIO()
            doc.save(output_buffer, garbage=4, deflate=True)
            output_buffer.seek(0)

            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to modify PDF: {e}")
            raise ValueError(f"Failed to modify PDF: {e}") from e

        finally:
            doc.close()

    def generate_from_template_bytes(
        self,
        pdf_bytes: bytes,
        variable_positions: dict[str, VariablePosition],
        replacements: dict[str, str],
    ) -> bytes:
        """
        Generate a modified PDF from bytes input.

        Args:
            pdf_bytes: The PDF template as bytes.
            variable_positions: Dictionary mapping variable names to their positions.
            replacements: Dictionary mapping variable names to replacement text.

        Returns:
            bytes: The modified PDF as bytes.
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF from bytes: {e}")
            raise ValueError("Could not open PDF from bytes") from e

        try:
            # First pass: Apply redactions for all variables that have replacements
            self._apply_redactions(doc, variable_positions, replacements)

            # Second pass: Insert replacement text
            self._insert_replacements(doc, variable_positions, replacements)

            # Save to bytes
            output_buffer = io.BytesIO()
            doc.save(output_buffer, garbage=4, deflate=True)
            output_buffer.seek(0)

            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to modify PDF: {e}")
            raise ValueError(f"Failed to modify PDF: {e}") from e

        finally:
            doc.close()

    def _apply_redactions(
        self,
        doc: fitz.Document,
        variable_positions: dict[str, VariablePosition],
        replacements: dict[str, str],
    ) -> None:
        """
        Apply redactions to remove original text at specified positions.

        Args:
            doc: The PyMuPDF document object.
            variable_positions: Dictionary of variable positions.
            replacements: Dictionary of replacement values.
        """
        # Group positions by page for efficiency
        positions_by_page: dict[int, list[tuple[str, VariablePosition]]] = {}

        for var_name, position in variable_positions.items():
            # Only redact if we have a replacement for this variable
            if var_name not in replacements:
                logger.debug(f"Skipping redaction for '{var_name}': no replacement provided")
                continue

            page_num = position.get("page", 0)
            if page_num not in positions_by_page:
                positions_by_page[page_num] = []
            positions_by_page[page_num].append((var_name, position))

        # Apply redactions page by page
        for page_num, positions in positions_by_page.items():
            if page_num >= len(doc):
                logger.warning(f"Page {page_num} does not exist in document (total pages: {len(doc)})")
                continue

            page = doc[page_num]

            for var_name, position in positions:
                rect = self._get_rect_from_position(position)

                # Add redaction annotation (white fill to cover original text)
                page.add_redact_annot(
                    rect,
                    fill=(1, 1, 1),  # White fill
                )

            # Apply all redactions for this page
            page.apply_redactions()

    def _insert_replacements(
        self,
        doc: fitz.Document,
        variable_positions: dict[str, VariablePosition],
        replacements: dict[str, str],
    ) -> None:
        """
        Insert replacement text at the specified positions.

        Args:
            doc: The PyMuPDF document object.
            variable_positions: Dictionary of variable positions.
            replacements: Dictionary of replacement values.
        """
        for var_name, replacement_text in replacements.items():
            if var_name not in variable_positions:
                logger.warning(f"No position defined for variable '{var_name}', skipping")
                continue

            position = variable_positions[var_name]
            page_num = position.get("page", 0)

            if page_num >= len(doc):
                logger.warning(f"Page {page_num} does not exist for variable '{var_name}'")
                continue

            page = doc[page_num]

            # Get font settings
            font_size = position.get("font_size", self.DEFAULT_FONT_SIZE)
            font_name = self._resolve_font(position.get("font_name"))

            # Get position
            x = position.get("x", 0)
            y = position.get("y", 0)
            width = position.get("width", 200)
            height = position.get("height", font_size * 1.5)

            # Create text rectangle
            text_rect = fitz.Rect(x, y, x + width, y + height)

            # Insert text with automatic fitting
            self._insert_text_with_fitting(
                page=page,
                rect=text_rect,
                text=replacement_text,
                font_name=font_name,
                font_size=font_size,
            )

    def _insert_text_with_fitting(
        self,
        page: fitz.Page,
        rect: fitz.Rect,
        text: str,
        font_name: str,
        font_size: float,
    ) -> None:
        """
        Insert text into a rectangle, adjusting font size if necessary to fit.

        Args:
            page: The PyMuPDF page object.
            rect: The rectangle to insert text into.
            text: The text to insert.
            font_name: The font name to use.
            font_size: The initial font size.
        """
        # Try to insert text, reducing font size if it doesn't fit
        current_size = font_size
        min_size = max(6.0, font_size * 0.5)  # Don't go below 6pt or half original

        while current_size >= min_size:
            try:
                # Calculate text width with current font size
                text_length = fitz.get_text_length(text, fontname=font_name, fontsize=current_size)

                if text_length <= rect.width:
                    # Text fits, insert it
                    # Calculate vertical position (center text vertically in rect)
                    text_height = current_size
                    y_offset = (rect.height - text_height) / 2 if rect.height > text_height else 0
                    insert_point = fitz.Point(rect.x0, rect.y0 + text_height + y_offset)

                    page.insert_text(
                        insert_point,
                        text,
                        fontname=font_name,
                        fontsize=current_size,
                        color=(0, 0, 0),  # Black text
                    )
                    return

                # Text doesn't fit, try smaller size
                current_size -= 0.5

            except Exception as e:
                logger.warning(f"Error inserting text with font '{font_name}': {e}")
                # Try with default font
                if font_name != self.DEFAULT_FONT:
                    font_name = self.DEFAULT_FONT
                    continue
                break

        # If we couldn't fit the text, use text box which handles wrapping
        try:
            page.insert_textbox(
                rect,
                text,
                fontname=font_name,
                fontsize=min_size,
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )
        except Exception as e:
            logger.error(f"Failed to insert text '{text}': {e}")
            # Last resort: insert at point without fitting
            page.insert_text(
                fitz.Point(rect.x0, rect.y0 + font_size),
                text,
                fontname=self.DEFAULT_FONT,
                fontsize=min_size,
                color=(0, 0, 0),
            )

    def _resolve_font(self, font_name: str | None) -> str:
        """
        Resolve a font name to a PyMuPDF built-in font.

        Args:
            font_name: The requested font name, or None.

        Returns:
            str: A valid PyMuPDF font name.
        """
        if not font_name:
            return self.DEFAULT_FONT

        # Normalize font name
        normalized = font_name.lower().replace(" ", "").replace("-", "")

        # Check direct mapping
        for key, value in self.FONT_MAPPING.items():
            if key.replace("-", "") in normalized or normalized in key.replace("-", ""):
                return value

        # Check for bold/italic variants
        if "bold" in normalized and "italic" in normalized:
            return "hebi"  # Helvetica Bold Italic
        elif "bold" in normalized:
            return "hebo"  # Helvetica Bold
        elif "italic" in normalized or "oblique" in normalized:
            return "heit"  # Helvetica Italic

        # Default fallback
        logger.debug(f"Font '{font_name}' not found, using default Helvetica")
        return self.DEFAULT_FONT

    def _get_rect_from_position(self, position: VariablePosition) -> fitz.Rect:
        """
        Create a fitz.Rect from a position dictionary.

        Args:
            position: The position dictionary.

        Returns:
            fitz.Rect: The rectangle representing the position.
        """
        x = position.get("x", 0)
        y = position.get("y", 0)
        width = position.get("width", 100)
        height = position.get("height", 20)

        return fitz.Rect(x, y, x + width, y + height)

    def preview_positions(
        self,
        pdf_path: str,
        variable_positions: dict[str, VariablePosition],
    ) -> bytes:
        """
        Generate a preview PDF showing the variable positions as colored rectangles.

        Useful for debugging and verifying position data.

        Args:
            pdf_path: Path to the PDF template file.
            variable_positions: Dictionary of variable positions.

        Returns:
            bytes: The preview PDF as bytes with rectangles drawn.
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"Failed to open PDF file: {pdf_path}, error: {e}")
            raise FileNotFoundError(f"Could not open PDF file: {pdf_path}") from e

        try:
            # Define colors for different variables
            colors = [
                (1, 0, 0),  # Red
                (0, 1, 0),  # Green
                (0, 0, 1),  # Blue
                (1, 1, 0),  # Yellow
                (1, 0, 1),  # Magenta
                (0, 1, 1),  # Cyan
            ]

            for idx, (var_name, position) in enumerate(variable_positions.items()):
                page_num = position.get("page", 0)

                if page_num >= len(doc):
                    continue

                page = doc[page_num]
                rect = self._get_rect_from_position(position)
                color = colors[idx % len(colors)]

                # Draw rectangle outline
                page.draw_rect(rect, color=color, width=1.5)

                # Add label
                label_point = fitz.Point(rect.x0, rect.y0 - 2)
                page.insert_text(
                    label_point,
                    var_name,
                    fontname="helv",
                    fontsize=8,
                    color=color,
                )

            # Save to bytes
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            output_buffer.seek(0)

            return output_buffer.getvalue()

        finally:
            doc.close()

    def extract_text_at_position(
        self,
        pdf_path: str,
        position: VariablePosition,
    ) -> str:
        """
        Extract text at a specific position in the PDF.

        Useful for verifying that positions are correctly aligned.

        Args:
            pdf_path: Path to the PDF file.
            position: The position to extract text from.

        Returns:
            str: The extracted text.
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise FileNotFoundError(f"Could not open PDF file: {pdf_path}") from e

        try:
            page_num = position.get("page", 0)

            if page_num >= len(doc):
                return ""

            page = doc[page_num]
            rect = self._get_rect_from_position(position)

            # Extract text from the rectangle
            text = page.get_text("text", clip=rect)
            return text.strip()

        finally:
            doc.close()
