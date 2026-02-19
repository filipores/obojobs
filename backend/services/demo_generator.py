"""
Demo Generator Service.

Generates ephemeral job applications for anonymous users using their uploaded CV.
No database persistence - results are returned directly.
"""

from urllib.parse import urlparse

from .ai_client import AIClient
from .email_formatter import EmailFormatter
from .pdf_handler import read_document


class DemoGenerator:
    """Demo generator using user-uploaded CV.

    Unlike BewerbungsGenerator, this class:
    - Uses a user-provided CV (no database lookup)
    - Does not persist results to the database
    - Returns ephemeral data for display only
    """

    def __init__(self) -> None:
        self.api_client = AIClient()

    def generate_demo(self, job_url: str, cv_text: str) -> dict[str, str]:
        """Generate a demo application from a job URL.

        Args:
            job_url: URL of the job posting to analyze
            cv_text: CV text extracted from user's uploaded PDF

        Returns:
            dict with position, firma, ansprechpartner, einleitung,
            anschreiben, betreff, email_text
        """
        # Phase 1: Read job posting from URL
        doc_result = read_document(job_url, return_links=True)
        stellenanzeige_text = doc_result["text"]

        if not stellenanzeige_text.strip():
            raise ValueError("Konnte keinen Text von der URL extrahieren")

        parsed_url = urlparse(job_url)
        url_firma = parsed_url.netloc.replace("www.", "").split(".")[0].title()

        # Phase 2: Extract details (position, contact, source)
        details = self.api_client.extract_bewerbung_details(stellenanzeige_text, url_firma)

        # Use AI-extracted firma if available, fall back to URL-based
        firma_name = details.get("firma") or url_firma

        # Phase 3: Generate full cover letter body
        anschreiben_body = self.api_client.generate_anschreiben(
            cv_text=cv_text,
            stellenanzeige_text=stellenanzeige_text,
            firma_name=firma_name,
            position=details["position"],
            ansprechpartner=details["ansprechpartner"],
            quelle=details["quelle"],
            zeugnis_text=None,
            tonalitaet="modern",
        )

        # Phase 4: Generate email content (no PDF for demo)
        betreff = EmailFormatter.generate_betreff(details["position"], firma_name, style="professional")
        email_text = EmailFormatter.generate_email_text(
            position=details["position"],
            ansprechperson=details["ansprechpartner"],
            firma_name=firma_name,
            attachments=["Anschreiben", "Lebenslauf"],
        )

        return {
            "position": details["position"],
            "firma": firma_name,
            "ansprechpartner": details["ansprechpartner"],
            "quelle": details["quelle"],
            "einleitung": anschreiben_body,
            "anschreiben": anschreiben_body,
            "betreff": betreff,
            "email_text": email_text,
        }
