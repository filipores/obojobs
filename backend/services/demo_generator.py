"""
Demo Generator Service.

Generates ephemeral job applications for anonymous users using their uploaded CV.
No database persistence - results are returned directly.
"""

import os
from urllib.parse import urlparse

from config import config

from .pdf_handler import read_document
from .qwen_client import QwenAPIClient


class DemoGenerator:
    """Demo generator using user-uploaded CV.

    Unlike BewerbungsGenerator, this class:
    - Uses a user-provided CV (no database lookup)
    - Does not persist results to the database
    - Returns ephemeral data for display only
    """

    SAMPLE_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "anschreiben_template.txt")

    def __init__(self):
        self.api_client = QwenAPIClient()
        self.anschreiben_template = self._load_sample_template()

    def _load_sample_template(self) -> str:
        """Load the sample Anschreiben template."""
        template_path = os.path.normpath(self.SAMPLE_TEMPLATE_PATH)
        if not os.path.exists(template_path):
            raise ValueError(f"Sample template not found at {template_path}")

        with open(template_path, encoding="utf-8") as f:
            return f.read()

    def generate_demo(self, job_url: str, cv_text: str) -> dict:
        """Generate a demo application from a job URL.

        Uses the same 5-phase generation process as real applications,
        but returns ephemeral data without database persistence.

        Args:
            job_url: URL of the job posting to analyze
            cv_text: CV text extracted from user's uploaded PDF

        Returns:
            dict with:
                - position: Extracted job position
                - firma: Company name
                - ansprechpartner: Contact greeting
                - einleitung: Generated personalized intro
                - anschreiben: Full cover letter text
                - betreff: Email subject line
                - email_text: Email body text
        """
        # Phase 1: Read job posting from URL
        doc_result = read_document(job_url, return_links=True)
        stellenanzeige_text = doc_result["text"]

        if not stellenanzeige_text.strip():
            raise ValueError("Konnte keinen Text von der URL extrahieren")

        parsed_url = urlparse(job_url)
        firma_name = parsed_url.netloc.replace("www.", "").split(".")[0].title()

        # Phase 2: Extract details (position, contact, source)
        details = self.api_client.extract_bewerbung_details(stellenanzeige_text, firma_name)

        # Phase 3: Generate personalized introduction
        einleitung = self.api_client.generate_einleitung(
            cv_text=cv_text,
            stellenanzeige_text=stellenanzeige_text,
            firma_name=firma_name,
            zeugnis_text=None,  # Demo doesn't use certificate
            details=details,
            use_extraction=config.USE_EXTRACTION,
        )

        # Phase 4: Create full cover letter by replacing template variables
        anschreiben = self.anschreiben_template
        replacements = {
            "FIRMA": firma_name,
            "ANSPRECHPARTNER": details["ansprechpartner"],
            "POSITION": details["position"],
            "QUELLE": details["quelle"],
            "EINLEITUNG": einleitung,
        }
        for var_name, value in replacements.items():
            placeholder = f"{{{{{var_name}}}}}"
            anschreiben = anschreiben.replace(placeholder, value)

        # Phase 5: Generate email content (no PDF for demo)
        betreff = self.api_client.generate_betreff(details["position"], firma_name, style="professional")
        email_text = self.api_client.generate_email_text(
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
            "einleitung": einleitung,
            "anschreiben": anschreiben,
            "betreff": betreff,
            "email_text": email_text,
        }
