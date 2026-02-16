import json
import logging
import os
import re
from datetime import datetime
from typing import Any

from config import config
from models import Application, Document, User, UserSkill, db

from .contact_extractor import ContactExtractor
from .email_formatter import EmailFormatter
from .output_validator import OutputValidator
from .pdf_handler import create_anschreiben_pdf, is_url, read_document
from .qwen_client import QwenAPIClient

logger = logging.getLogger(__name__)

_GERMAN_MONTHS = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]


class BewerbungsGenerator:
    def __init__(self, user_id: int, progress_callback=None):
        self.user_id = user_id
        self.api_client = QwenAPIClient()
        self.validator = OutputValidator()
        self.cv_text = None
        self.zeugnis_text = None
        self.extracted_links = None
        self.user = None
        self._prepared = False
        self.warnings = []
        self.progress_callback = progress_callback

    def _emit_progress(self, step, total_steps, message):
        """Emit progress event if callback is set."""
        if self.progress_callback:
            self.progress_callback(
                {
                    "step": step,
                    "total_steps": total_steps,
                    "message": message,
                    "progress": round(step / total_steps * 100),
                }
            )

    def prepare(self) -> None:
        """Load user data and documents from database.

        Performs all I/O operations: DB queries and file reads.
        Must be called before generate_bewerbung(). If not called explicitly,
        generate_bewerbung() will call it automatically for backwards compatibility.
        """
        if self._prepared:
            return
        self.user = User.query.get(self.user_id)
        self.load_user_documents()
        self._prepared = True

    def load_user_documents(self) -> None:
        """Load documents from database for this user."""
        logger.info("Lade Dokumente für User %s...", self.user_id)

        cv_doc = Document.query.filter_by(user_id=self.user_id, doc_type="lebenslauf").first()
        if not cv_doc or not os.path.exists(cv_doc.file_path):
            raise ValueError("Lebenslauf nicht gefunden. Bitte lade deinen Lebenslauf hoch.")
        self.cv_text = read_document(cv_doc.file_path)
        logger.info("Lebenslauf geladen")

        zeugnis_doc = Document.query.filter_by(user_id=self.user_id, doc_type="arbeitszeugnis").first()
        if zeugnis_doc and os.path.exists(zeugnis_doc.file_path):
            self.zeugnis_text = read_document(zeugnis_doc.file_path)
            logger.info("Arbeitszeugnis geladen")
        else:
            self.zeugnis_text = None
            logger.info("Arbeitszeugnis nicht vorhanden (optional)")

        logger.info("Dokumente geladen")

    def generate_bewerbung(
        self,
        stellenanzeige_path: str,
        firma_name: str,
        output_filename: str | None = None,
        user_details: dict[str, Any] | None = None,
        tonalitaet: str = "modern",
    ) -> str:
        """Generate a job application -- orchestrates the pipeline.

        Args:
            stellenanzeige_path: URL or file path to job posting
            firma_name: Company name
            output_filename: Optional custom output filename
            user_details: Optional dict with user-edited data from preview step:
                - position: Job title
                - contact_person: Contact person for salutation
                - contact_email: Contact email
                - location: Job location
                - description: Job description text (used instead of re-scraping)
                - quelle: Source/portal name
            tonalitaet: Tone of the cover letter (default: "modern")
        """
        # Auto-prepare if not already done (backwards compatibility)
        if not self._prepared:
            self.prepare()

        logger.info("Generiere Bewerbung fuer: %s", firma_name)

        # Step 1: Load job posting
        self._emit_progress(1, 7, "Stellenanzeige wird geladen...")
        stellenanzeige_text = self._load_job_posting(stellenanzeige_path, user_details)

        # Step 2: Extract details
        self._emit_progress(2, 7, "Details werden extrahiert...")
        details = self._extract_details(stellenanzeige_text, firma_name, user_details)

        # Step 3: Generate cover letter body
        self._emit_progress(3, 7, "Anschreiben wird generiert...")
        anschreiben_body = self._generate_letter_body(stellenanzeige_text, firma_name, details, tonalitaet)

        # Step 4: Build complete letter with header
        self._emit_progress(4, 7, "Anschreiben wird formatiert...")
        anschreiben_vollstaendig = self._build_complete_letter(firma_name, details, anschreiben_body)

        # Step 5: Create PDF
        self._emit_progress(5, 7, "PDF wird erstellt...")
        output_path = self._create_pdf(firma_name, anschreiben_vollstaendig, output_filename)

        # Step 6: Generate email data
        self._emit_progress(6, 7, "E-Mail-Daten werden vorbereitet...")
        betreff, email_text = self._generate_email_data(firma_name, details)

        # Step 7: Save to database
        self._emit_progress(7, 7, "Bewerbung wird gespeichert...")
        self._save_application(
            firma_name, details, output_path, betreff, email_text, anschreiben_body, stellenanzeige_text
        )

        return output_path

    def _load_job_posting(self, stellenanzeige_path: str, user_details: dict[str, Any] | None) -> str:
        """Load job posting text from user-provided data, URL, or file path."""
        if user_details and user_details.get("description"):
            logger.info("1/5 Verwende Benutzerdaten aus Vorschau...")
            self.extracted_links = None
            return user_details["description"]

        logger.info("1/5 Lese Stellenanzeige...")

        if is_url(stellenanzeige_path):
            logger.info("Lade von URL: %s", stellenanzeige_path)
            doc_result = read_document(stellenanzeige_path, return_links=True)
            stellenanzeige_text = doc_result["text"]

            if doc_result.get("email_links"):
                logger.info("%d E-Mail-Link(s) gefunden", len(doc_result["email_links"]))
            if doc_result.get("application_links"):
                logger.info("%d Bewerbungs-Link(s) gefunden", len(doc_result["application_links"]))

            self.extracted_links = doc_result
        else:
            stellenanzeige_text = read_document(stellenanzeige_path)
            self.extracted_links = None

        logger.info("Stellenanzeige geladen")
        return stellenanzeige_text

    def _extract_details(
        self,
        stellenanzeige_text: str,
        firma_name: str,
        user_details: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Extract job details via AI, or use pre-provided data from the preview step."""
        if user_details and user_details.get("description"):
            logger.info("2/5 Verwende bearbeitete Details...")
            contact_person = user_details.get("contact_person") or None
            ansprechpartner = ContactExtractor().format_contact_person_salutation(contact_person, firma_name)
            details = {
                "firma": firma_name,
                "position": user_details.get("position") or "Softwareentwickler",
                "ansprechpartner": ansprechpartner,
                "quelle": user_details.get("quelle") or "eure Website",
                "email": user_details.get("contact_email") or "",
                "stellenanzeige_kompakt": stellenanzeige_text[:500] if stellenanzeige_text else "",
            }
            logger.info("Details aus Vorschau verwendet")
        else:
            logger.info("2/5 Extrahiere Details (Position, Ansprechpartner, Quelle)...")
            details = self.api_client.extract_bewerbung_details(stellenanzeige_text, firma_name)
            logger.info("Details extrahiert")

        self.warnings.extend(details.pop("warnings", []))

        logger.info("Position: %s", details["position"])
        logger.info("Ansprechpartner: %s", details["ansprechpartner"])
        logger.info("Quelle: %s", details["quelle"])
        return details

    def _extract_user_inputs(self) -> tuple[str | None, str | None, list]:
        """Extract user data for cover letter generation.

        Returns:
            Tuple of (full_name, first_name, user_skills)
        """
        if not self.user:
            return None, None, []

        full_name = self.user.full_name
        first_name = full_name.split()[0] if full_name else None
        user_skills = UserSkill.query.filter_by(user_id=self.user_id).all()

        return full_name, first_name, user_skills or []

    def _generate_letter_body(
        self,
        stellenanzeige_text: str,
        firma_name: str,
        details: dict[str, str],
        tonalitaet: str,
    ) -> str:
        """Generate the AI-written cover letter body via Qwen."""
        logger.info("3/5 Generiere vollständiges Anschreiben...")

        # Prepare user inputs
        full_name, bewerber_vorname, user_skills = self._extract_user_inputs()

        # Generate body via API
        anschreiben_body = self.api_client.generate_anschreiben(
            cv_text=self.cv_text,
            stellenanzeige_text=stellenanzeige_text,
            firma_name=firma_name,
            position=details["position"],
            ansprechpartner=details["ansprechpartner"],
            quelle=details["quelle"],
            zeugnis_text=self.zeugnis_text,
            bewerber_vorname=bewerber_vorname,
            bewerber_name=full_name,
            user_skills=user_skills,
            tonalitaet=tonalitaet,
            details=details,
        )
        logger.info("Anschreiben generiert (%d Zeichen)", len(anschreiben_body))

        # Fix gray-zone skill claims before validation
        anschreiben_body = self.validator.fix_gray_zone_claims(
            text=anschreiben_body,
            cv_text=self.cv_text,
            user_skills=user_skills,
        )

        # Validate generated output
        validation = self.validator.validate(
            text=anschreiben_body,
            cv_text=self.cv_text,
            user_skills=user_skills,
        )

        # Collect validation feedback
        if validation.warnings:
            self.warnings.extend(validation.warnings)
            logger.info("Validierung: %d Warnings", len(validation.warnings))

        if validation.errors:
            self.warnings.extend(validation.errors)
            logger.warning("Validierung: %d Errors", len(validation.errors))

        logger.info("Validierung Metriken: %s", validation.metrics)

        return anschreiben_body

    def _build_complete_letter(
        self,
        firma_name: str,
        details: dict[str, str],
        anschreiben_body: str,
    ) -> str:
        """Build the complete letter with briefkopf (header) and cleanup."""
        now = datetime.now()
        datum_formatiert = f"{now.day:02d}. {_GERMAN_MONTHS[now.month - 1]} {now.year}"

        header_parts = []
        if self.user.full_name:
            header_parts.append(self.user.full_name)
        if self.user.address:
            header_parts.append(self.user.address)
        if self.user.postal_code or self.user.city:
            header_parts.append(f"{self.user.postal_code or ''} {self.user.city or ''}".strip())

        contact_parts = []
        if self.user.phone:
            contact_parts.append(self.user.phone)
        if self.user.email:
            contact_parts.append(self.user.email)
        if self.user.website:
            contact_parts.append(self.user.website)
        if contact_parts:
            header_parts.append(" | ".join(contact_parts))

        header_parts.append("")
        header_parts.append(firma_name)
        ort_datum = f"{self.user.city}, {datum_formatiert}" if self.user.city else datum_formatiert
        header_parts.append(ort_datum)
        header_parts.append("")
        header_parts.append(f"Bewerbung als {details['position']}")
        header_parts.append("")

        briefkopf = "\n".join(header_parts)
        anschreiben_vollstaendig = briefkopf + anschreiben_body
        anschreiben_vollstaendig = re.sub(r"\n{3,}", "\n\n", anschreiben_vollstaendig)
        return anschreiben_vollstaendig.strip()

    def _create_pdf(
        self,
        firma_name: str,
        anschreiben_vollstaendig: str,
        output_filename: str | None,
    ) -> str:
        """Create the PDF file and return its path."""
        pdf_dir = os.path.join(config.UPLOAD_FOLDER, f"user_{self.user_id}", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        output_filename = output_filename or f"Anschreiben_{firma_name.replace(' ', '_')}.pdf"
        output_path = os.path.join(pdf_dir, output_filename)

        logger.info("4/5 Erstelle PDF...")
        create_anschreiben_pdf(anschreiben_vollstaendig, output_path, firma_name)
        logger.info("Bewerbung erstellt: %s", output_path)
        return output_path

    def _generate_email_data(self, firma_name: str, details: dict[str, str]) -> tuple[str, str]:
        """Generate email subject and body text."""
        betreff = EmailFormatter.generate_betreff(
            details["position"], firma_name, style="professional", user_name=self.user.full_name
        )
        # Build attachments list dynamically from user's uploaded documents
        attachments = ["Anschreiben", "Lebenslauf"]
        user_docs = Document.query.filter_by(user_id=self.user_id).all()
        for doc in user_docs:
            if doc.doc_type == "arbeitszeugnis":
                attachments.append(doc.original_filename or "Arbeitszeugnis")
            elif doc.doc_type != "lebenslauf":
                attachments.append(doc.original_filename or doc.doc_type)
        email_text = EmailFormatter.generate_email_text(
            position=details["position"],
            ansprechperson=details["ansprechpartner"],
            firma_name=firma_name,
            attachments=attachments,
            user_name=self.user.full_name,
            user_email=self.user.email,
            user_phone=self.user.phone,
            user_city=self.user.city,
            user_website=self.user.website,
        )
        return betreff, email_text

    def _save_application(
        self,
        firma_name: str,
        details: dict[str, str],
        output_path: str,
        betreff: str,
        email_text: str,
        anschreiben_body: str,
        stellenanzeige_text: str,
    ) -> None:
        """Save application record to database and log results."""
        links = self.extracted_links or {}
        extracted_info = {
            "email_from_text": details.get("email", ""),
            "email_links": links.get("email_links", []),
            "application_links": links.get("application_links", []),
            "all_links": links.get("all_links", []),
        }

        application = Application(
            user_id=self.user_id,
            firma=firma_name,
            position=details["position"],
            ansprechpartner=details["ansprechpartner"],
            email=details.get("email", ""),
            quelle=details["quelle"],
            status="erstellt",
            pdf_path=output_path,
            betreff=betreff,
            email_text=email_text,
            einleitung=anschreiben_body,
            links_json=json.dumps(extracted_info),
        )
        application.add_status_change("erstellt")
        db.session.add(application)
        db.session.commit()

        logger.info("Email an: %s", details.get("email") or "Keine E-Mail-Adresse gefunden")
        logger.info("Betreff: %s", betreff)
        logger.debug("Email-Text: %s", email_text)

        if extracted_info["email_links"]:
            for link in extracted_info["email_links"]:
                logger.info("E-Mail-Link: %s (%s)", link["email"], link["text"])

        if extracted_info["application_links"]:
            for link in extracted_info["application_links"][:5]:
                logger.info("Bewerbungs-Link: %s: %s", link["text"], link["url"])

    def process_firma(self, firma_config: dict[str, str]) -> str | None:
        """Process a single company config dict and generate an application.

        Returns the output PDF path on success, or None on failure.
        """
        try:
            firma_name = firma_config.get("name")
            stellenanzeige_path = firma_config.get("stellenanzeige")

            if not firma_name or not stellenanzeige_path:
                raise ValueError("Firma-Config muss 'name' und 'stellenanzeige' enthalten")

            return self.generate_bewerbung(stellenanzeige_path, firma_name)
        except Exception as e:
            logger.error("Fehler bei %s: %s", firma_config.get("name", "unbekannt"), e)
            return None
