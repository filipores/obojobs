from typing import Dict

import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from .web_scraper import WebScraper


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # OCR-Fallback für gescannte PDFs
    if not text.strip():
        images = convert_from_path(pdf_path)
        for image in images:
            text += pytesseract.image_to_string(image, lang='deu') + "\n"

    return text.strip()


def read_text_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def is_url(path: str) -> bool:
    return path.startswith('http://') or path.startswith('https://')


def read_document(file_path: str, return_links: bool = False) -> str | Dict:
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
        else:
            return result['text']
    elif file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
        if return_links:
            return {'text': text, 'all_links': [], 'email_links': [], 'application_links': []}
        return text
    else:
        text = read_text_file(file_path)
        if return_links:
            return {'text': text, 'all_links': [], 'email_links': [], 'application_links': []}
        return text


def create_anschreiben_pdf(anschreiben_text: str, output_path: str, firma_name: str) -> str:
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=16,
                                 leading=20, alignment=TA_CENTER, spaceAfter=8)
    h2_style = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=14,
                             leading=18, alignment=TA_CENTER, spaceAfter=8)
    contact_style = ParagraphStyle('Contact', fontName='Helvetica', fontSize=10,
                                  leading=14, alignment=TA_CENTER, spaceAfter=20)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=11,
                               leading=16, alignment=TA_JUSTIFY, spaceAfter=12)

    story = []
    line_count = 0
    in_header = True

    for para in anschreiben_text.split('\n'):
        para_stripped = para.strip()
        if para_stripped:
            line_count += 1
            para_escaped = para_stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            if line_count == 1:
                story.append(Paragraph(para_escaped, title_style))
            elif line_count == 2:
                story.append(Paragraph(para_escaped, h2_style))
            elif line_count == 3:
                story.append(Paragraph(para_escaped, contact_style))
                in_header = False
            else:
                story.append(Paragraph(para_escaped, body_style))
        elif not in_header:
            story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    return output_path
