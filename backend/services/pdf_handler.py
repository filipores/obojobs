import re

import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from .web_scraper import WebScraper

# Zen Farbpalette
SUMI = HexColor("#2C2C2C")  # Text
AI_INDIGO = HexColor("#3D5A6C")  # Akzent
SAND = HexColor("#D4C9BA")  # Dekorative Linie
STONE = HexColor("#9B958F")  # Sekundär


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # OCR-Fallback für gescannte PDFs
    if not text.strip():
        images = convert_from_path(pdf_path)
        for image in images:
            text += pytesseract.image_to_string(image, lang="deu") + "\n"

    return text.strip()


def read_text_file(file_path: str) -> str:
    with open(file_path, encoding="utf-8") as file:
        return file.read()


def is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def read_document(file_path: str, return_links: bool = False) -> str | dict:
    """
    Liest ein Dokument (PDF, TXT oder URL).

    Args:
        file_path: Pfad zur Datei oder URL
        return_links: Wenn True, gibt Dict mit text und links zurück (nur bei URLs)

    Returns:
        String mit Text oder Dict mit text und links
    """
    if is_url(file_path):
        scraper = WebScraper()
        result = scraper.fetch_job_posting(file_path)

        if return_links:
            return result
        text: str = result["text"]
        return text
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
        if return_links:
            return {"text": text, "all_links": [], "email_links": [], "application_links": []}
        return text
    text = read_text_file(file_path)
    if return_links:
        return {"text": text, "all_links": [], "email_links": [], "application_links": []}
    return text


def _is_header_line(line: str) -> bool:
    """Detect header/contact lines by structural markers (pipes, email, phone, URLs)."""
    pipe_count = line.count("|")
    has_email = "@" in line and "." in line
    has_phone = bool(re.search(r"\+?\d[\d\s\-/]{6,}", line))
    has_url = bool(re.search(r"\w+\.\w{2,}", line)) and "@" not in line.split(".")[-1]
    return pipe_count >= 2 or (has_email and (has_phone or has_url))


def _is_greeting_line(line: str) -> bool:
    """Detect salutation/greeting lines."""
    lower = line.lower().rstrip(",").strip()
    greeting_starts = (
        "sehr geehrte",
        "moin",
        "hallo",
        "liebe",
        "guten tag",
        "dear",
        "hi ",
        "hey ",
        "bewerbung als",
        "bewerbung um",
    )
    return lower.startswith(greeting_starts)


def _is_date_or_location_line(line: str) -> bool:
    """Detect date or location lines like 'Hamburg, 08. Februar 2026'."""
    return bool(re.search(r"\d{1,2}\.\s*\w+\s+\d{4}", line))


def create_anschreiben_pdf(anschreiben_text: str, output_path: str, firma_name: str) -> str:
    doc = SimpleDocTemplate(
        output_path, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm
    )

    header_style = ParagraphStyle(
        "Header", fontName="Helvetica-Bold", fontSize=12, leading=16, alignment=TA_CENTER, spaceAfter=4
    )
    greeting_style = ParagraphStyle(
        "Greeting", fontName="Helvetica-Bold", fontSize=11, leading=16, alignment=TA_LEFT, spaceAfter=8
    )
    meta_style = ParagraphStyle(
        "Meta",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=4,
        textColor=colors.HexColor("#555555"),
    )
    body_style = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=12
    )

    story = []
    header_done = False

    for para in anschreiben_text.split("\n"):
        para_stripped = para.strip()
        if not para_stripped:
            if header_done:
                story.append(Spacer(1, 0.3 * cm))
            continue

        para_escaped = para_stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if not header_done and _is_header_line(para_stripped):
            story.append(Paragraph(para_escaped, header_style))
        elif not header_done and _is_date_or_location_line(para_stripped):
            story.append(Paragraph(para_escaped, meta_style))
        elif _is_greeting_line(para_stripped):
            if not header_done:
                story.append(Spacer(1, 0.4 * cm))
            header_done = True
            story.append(Paragraph(para_escaped, greeting_style))
        else:
            header_done = True
            story.append(Paragraph(para_escaped, body_style))

    doc.build(story)
    return output_path


def create_zen_anschreiben_pdf(anschreiben_text: str, output_path: str, firma_name: str) -> str:
    """
    Erstellt ein Anschreiben-PDF mit japanischer Zen-Ästhetik.

    Design-Prinzipien:
    - Ma (間): Großzügige Ränder und Zeilenhöhe für Atemraum
    - Wabi-Sabi: Subtile, asymmetrische Elemente
    - Serif für Überschriften, Sans-Serif für Fließtext
    - Indigo als Akzentfarbe, Sand für dekorative Linien
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=A4, rightMargin=2.2 * cm, leftMargin=2.2 * cm, topMargin=2.8 * cm, bottomMargin=2.8 * cm
    )

    # Zen-Stile
    title_style = ParagraphStyle(
        "ZenTitle", fontName="Times-Bold", fontSize=18, leading=22, alignment=TA_CENTER, textColor=SUMI, spaceAfter=6
    )

    company_style = ParagraphStyle(
        "ZenCompany",
        fontName="Times-Italic",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=AI_INDIGO,
        spaceAfter=20,
    )

    contact_style = ParagraphStyle(
        "ZenContact", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_CENTER, textColor=STONE, spaceAfter=10
    )

    body_style = ParagraphStyle(
        "ZenBody",
        fontName="Helvetica",
        fontSize=10.5,
        leading=17,  # 1.6x Zeilenhöhe für bessere Lesbarkeit
        alignment=TA_JUSTIFY,
        textColor=SUMI,
        spaceAfter=14,
        firstLineIndent=0,
    )

    story = []
    line_count = 0
    in_header = True

    for para in anschreiben_text.split("\n"):
        para_stripped = para.strip()
        if para_stripped:
            line_count += 1
            para_escaped = para_stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if line_count == 1:
                # Titel
                story.append(Paragraph(para_escaped, title_style))
            elif line_count == 2:
                # Firma
                story.append(Paragraph(para_escaped, company_style))
            elif line_count == 3:
                # Kontaktinfo
                story.append(Paragraph(para_escaped, contact_style))
                # Dekorative Linie nach Header (Wabi-Sabi: asymmetrisch bei 40%)
                story.append(HRFlowable(width="40%", thickness=0.5, color=SAND, spaceAfter=20, spaceBefore=10))
                in_header = False
            else:
                # Fließtext
                story.append(Paragraph(para_escaped, body_style))
        elif not in_header:
            story.append(Spacer(1, 0.4 * cm))

    doc.build(story)
    return output_path
