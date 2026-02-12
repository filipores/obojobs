import json
import logging
import os
import re
from datetime import datetime
from typing import Any

from config import config
from models import Application, Document, JobRequirement, User, UserSkill, db

from .contact_extractor import ContactExtractor
from .pdf_handler import create_anschreiben_pdf, is_url, read_document
from .qwen_client import QwenAPIClient
from .requirement_analyzer import RequirementAnalyzer

logger = logging.getLogger(__name__)


class BewerbungsGenerator:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.api_client = QwenAPIClient()
        self.cv_text = None
        self.zeugnis_text = None
        self.extracted_links = None
        self.user = None
        self._prepared = False

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
        """Load documents from database for this user"""
        logger.info("Lade Dokumente für User %s...", self.user_id)

        # Load Lebenslauf (Pflicht)
        cv_doc = Document.query.filter_by(user_id=self.user_id, doc_type="lebenslauf").first()
        if cv_doc and os.path.exists(cv_doc.file_path):
            self.cv_text = read_document(cv_doc.file_path)
            logger.info("Lebenslauf geladen")
        else:
            raise ValueError("Lebenslauf nicht gefunden. Bitte lade deinen Lebenslauf hoch.")

        # Load Arbeitszeugnis (Optional)
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
        """Generate a job application.

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
        """
        # Auto-prepare if not already done (backwards compatibility)
        if not self._prepared:
            self.prepare()

        logger.info("Generiere Bewerbung fuer: %s", firma_name)

        # Check if user provided pre-edited data with description
        use_user_data = user_details and user_details.get("description")

        if use_user_data:
            logger.info("1/5 Verwende Benutzerdaten aus Vorschau...")
            stellenanzeige_text = user_details["description"]
            self.extracted_links = None
            logger.info("Benutzerdaten geladen")
        else:
            logger.info("1/5 Lese Stellenanzeige...")

            if is_url(stellenanzeige_path):
                logger.info("Lade von URL: %s", stellenanzeige_path)
                doc_result = read_document(stellenanzeige_path, return_links=True)
                stellenanzeige_text = doc_result["text"]

                # Zeige gefundene Links
                if doc_result.get("email_links"):
                    logger.info("%d E-Mail-Link(s) gefunden", len(doc_result["email_links"]))
                if doc_result.get("application_links"):
                    logger.info("%d Bewerbungs-Link(s) gefunden", len(doc_result["application_links"]))

                # Speichere Links für spätere Verwendung
                self.extracted_links = doc_result
            else:
                stellenanzeige_text = read_document(stellenanzeige_path)
                self.extracted_links = None

            logger.info("Stellenanzeige geladen")

        # Use user-provided details or extract via Claude API
        if use_user_data:
            logger.info("2/5 Verwende bearbeitete Details...")
            contact_person = user_details.get("contact_person") or ""
            # Format raw contact name into proper salutation (e.g. "Tom Heinfling" -> "Sehr geehrte/r Tom Heinfling")
            ansprechpartner = ContactExtractor().format_contact_person_salutation(
                contact_person if contact_person else None, firma_name
            )
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
        logger.info("Position: %s", details["position"])
        logger.info("Ansprechpartner: %s", details["ansprechpartner"])
        logger.info("Quelle: %s", details["quelle"])

        logger.info("3/5 Generiere vollständiges Anschreiben...")
        bewerber_vorname = None
        bewerber_name = None
        if self.user and self.user.full_name:
            bewerber_vorname = self.user.full_name.split()[0]
            bewerber_name = self.user.full_name

        user_skills = UserSkill.query.filter_by(user_id=self.user_id).all() if self.user_id else []

        anschreiben_body = self.api_client.generate_anschreiben(
            cv_text=self.cv_text,
            stellenanzeige_text=stellenanzeige_text,
            firma_name=firma_name,
            position=details["position"],
            ansprechpartner=details["ansprechpartner"],
            quelle=details["quelle"],
            zeugnis_text=self.zeugnis_text,
            bewerber_vorname=bewerber_vorname,
            bewerber_name=bewerber_name,
            user_skills=user_skills,
            tonalitaet=tonalitaet,
        )
        logger.info("Anschreiben generiert (%d Zeichen)", len(anschreiben_body))

        # Format current date in German
        german_months = [
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
        now = datetime.now()
        datum_formatiert = f"{now.day:02d}. {german_months[now.month - 1]} {now.year}"

        # Build briefkopf (header) programmatically
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

        # Company + date
        header_parts.append("")  # blank line
        header_parts.append(firma_name)
        ort_datum = f"{self.user.city}, {datum_formatiert}" if self.user.city else datum_formatiert
        header_parts.append(ort_datum)
        header_parts.append("")  # blank line
        header_parts.append(f"Bewerbung als {details['position']}")
        header_parts.append("")  # blank line

        briefkopf = "\n".join(header_parts)

        # Combine briefkopf + AI-generated body
        anschreiben_vollstaendig = briefkopf + anschreiben_body

        # Clean up excessive blank lines
        anschreiben_vollstaendig = re.sub(r"\n{3,}", "\n\n", anschreiben_vollstaendig)
        anschreiben_vollstaendig = anschreiben_vollstaendig.strip()

        # Create PDF
        pdf_dir = os.path.join(config.UPLOAD_FOLDER, f"user_{self.user_id}", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        output_filename = output_filename or f"Anschreiben_{firma_name.replace(' ', '_')}.pdf"
        output_path = os.path.join(pdf_dir, output_filename)

        logger.info("4/5 Erstelle PDF...")
        create_anschreiben_pdf(anschreiben_vollstaendig, output_path, firma_name)

        logger.info("Bewerbung erstellt: %s", output_path)

        # Email-Daten generieren mit verbesserter Personalisierung
        betreff = self.api_client.generate_betreff(
            details["position"], firma_name, style="professional", user_name=self.user.full_name
        )
        # Build attachments list dynamically from user's uploaded documents
        attachments = ["Anschreiben", "Lebenslauf"]
        user_docs = Document.query.filter_by(user_id=self.user_id).all()
        for doc in user_docs:
            if doc.doc_type == "arbeitszeugnis":
                attachments.append(doc.original_filename or "Arbeitszeugnis")
            elif doc.doc_type not in ("lebenslauf", "anschreiben"):
                attachments.append(doc.original_filename or doc.doc_type)
        email_text = self.api_client.generate_email_text(
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

        # Collect all extracted information
        links = self.extracted_links or {}
        extracted_info = {
            "email_from_text": details.get("email", ""),
            "email_links": links.get("email_links", []),
            "application_links": links.get("application_links", []),
            "all_links": links.get("all_links", []),
        }

        # Save to database
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
        # Initialize status history with 'erstellt'
        application.add_status_change("erstellt")
        db.session.add(application)
        db.session.commit()

        # Extract and save job requirements in background
        self._extract_requirements(application.id, stellenanzeige_text)

        # Log email information
        logger.info("Email an: %s", details.get("email") or "Keine E-Mail-Adresse gefunden")
        logger.info("Betreff: %s", betreff)
        logger.debug("Email-Text: %s", email_text)

        # Log extrahierte Links
        if extracted_info["email_links"]:
            for link in extracted_info["email_links"]:
                logger.info("E-Mail-Link: %s (%s)", link["email"], link["text"])

        if extracted_info["application_links"]:
            for link in extracted_info["application_links"][:5]:
                logger.info("Bewerbungs-Link: %s: %s", link["text"], link["url"])

        return output_path

    def process_firma(self, firma_config: dict[str, str]) -> str | None:
        try:
            firma_name = firma_config.get("name")
            stellenanzeige_path = firma_config.get("stellenanzeige")

            if not firma_name or not stellenanzeige_path:
                raise ValueError("Firma-Config muss 'name' und 'stellenanzeige' enthalten")

            return self.generate_bewerbung(stellenanzeige_path, firma_name)
        except Exception as e:
            logger.error("Fehler bei %s: %s", firma_config.get("name", "unbekannt"), e)
            return None

    def _extract_requirements(self, application_id: int, job_text: str) -> None:
        """Extract job requirements from job posting text and save to database.

        This runs silently and doesn't block the main application generation.
        Errors are logged but don't cause the main flow to fail.
        """
        try:
            logger.info("Extrahiere Anforderungen aus Stellenanzeige...")
            analyzer = RequirementAnalyzer()
            requirements = analyzer.analyze_requirements(job_text)

            if not requirements:
                logger.info("Keine Anforderungen gefunden")
                return

            # Save requirements to database
            for req_data in requirements:
                requirement = JobRequirement(
                    application_id=application_id,
                    requirement_text=req_data["requirement_text"],
                    requirement_type=req_data["requirement_type"],
                    skill_category=req_data.get("skill_category"),
                )
                db.session.add(requirement)

            db.session.commit()

            must_have_count = sum(1 for r in requirements if r["requirement_type"] == "must_have")
            nice_to_have_count = len(requirements) - must_have_count
            logger.info(
                "%d Anforderungen extrahiert (%d Pflicht, %d Optional)",
                len(requirements),
                must_have_count,
                nice_to_have_count,
            )

        except Exception as e:
            logger.warning("Anforderungs-Extraktion fehlgeschlagen: %s", e)
