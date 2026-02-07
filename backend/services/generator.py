import json
import logging
import os
import re
from datetime import datetime

from config import config
from models import Application, Document, JobRequirement, Template, User, db

from .api_client import ClaudeAPIClient
from .pdf_handler import create_anschreiben_pdf, is_url, read_document
from .pdf_template_modifier import PDFTemplateModifier
from .requirement_analyzer import RequirementAnalyzer
from .template_generator import get_or_create_default_template

logger = logging.getLogger(__name__)


def _convert_variable_positions_to_dict(variable_positions) -> dict:
    """
    Convert variable_positions from list format to dict format.

    The PDFTemplateModifier expects a dict like:
        {"FIRMA": {"x": 100, "y": 200, "width": 150, ...}, ...}

    But the frontend may send a list like:
        [{"variable_name": "FIRMA", "x": 100, "y": 200, ...}, ...]
    """
    if variable_positions is None:
        return {}

    if isinstance(variable_positions, dict):
        return variable_positions

    if isinstance(variable_positions, list):
        result = {}
        for item in variable_positions:
            if not isinstance(item, dict):
                continue
            var_name = item.get("variable_name") or item.get("variable")
            if not var_name:
                continue
            # Extract position data, excluding the variable name key
            position_data = {
                k: v for k, v in item.items() if k not in ("variable_name", "variable", "suggested_text", "text")
            }
            result[var_name] = position_data
        return result

    return {}


class BewerbungsGenerator:
    def __init__(self, user_id: int, template_id: int | None = None):
        self.user_id = user_id
        self.template_id = template_id
        self.api_client = ClaudeAPIClient()
        self.cv_text = None
        self.anschreiben_template = None
        self.template = None  # Store template object for PDF template support
        self.zeugnis_text = None
        self.extracted_links = None
        self.user = User.query.get(user_id)
        self.load_user_documents()

    def load_user_documents(self):
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

        # Load Anschreiben-Template
        if self.template_id:
            # Specific template requested
            template = Template.query.filter_by(id=self.template_id, user_id=self.user_id).first()
            if template:
                self.template = template
                self.anschreiben_template = template.content
                logger.info("Template '%s' geladen (ID: %s)", template.name, self.template_id)
                if template.is_pdf_template:
                    logger.info("PDF-Template erkannt: %s", template.pdf_path)
            else:
                raise ValueError(f"Template mit ID {self.template_id} nicht gefunden.")
        else:
            # No specific template selected - use default template from DB
            template = get_or_create_default_template(self.user_id)
            self.template = template
            self.anschreiben_template = template.content
            if template.name == "Standard-Vorlage (automatisch erstellt)":
                logger.info("Standard-Template automatisch erstellt")
            else:
                logger.info("Template geladen")
            if template.is_pdf_template:
                logger.info("PDF-Template erkannt: %s", template.pdf_path)

        logger.info("Dokumente geladen")

    def generate_bewerbung(
        self,
        stellenanzeige_path: str,
        firma_name: str,
        output_filename: str | None = None,
        user_details: dict | None = None,
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
            details = {
                "firma": firma_name,
                "position": user_details.get("position") or "Softwareentwickler",
                "ansprechpartner": user_details.get("contact_person") or "Sehr geehrte Damen und Herren",
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

        logger.info("3/5 Generiere personalisierten Einleitungsabsatz mit Claude...")
        einleitung = self.api_client.generate_einleitung(
            cv_text=self.cv_text,
            stellenanzeige_text=stellenanzeige_text,
            firma_name=firma_name,
            zeugnis_text=self.zeugnis_text,
            details=details,
            use_extraction=config.USE_EXTRACTION,
        )
        logger.info("Einleitung generiert (%d Zeichen)", len(einleitung))
        logger.debug("Generierte Einleitung: %s", einleitung)

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

        # Build smart composite values that handle empty fields gracefully
        kontakt_zeile = " | ".join(filter(None, [self.user.phone, self.user.email]))

        ort_datum = f"{self.user.city}, {datum_formatiert}" if self.user.city else datum_formatiert

        # Prepare variable replacements
        replacements = {
            "FIRMA": firma_name,
            "ANSPRECHPARTNER": details["ansprechpartner"],
            "POSITION": details["position"],
            "QUELLE": details["quelle"],
            "EINLEITUNG": einleitung,
            "NAME": self.user.full_name or "",
            "EMAIL": self.user.email or "",
            "TELEFON": self.user.phone or "",
            "ADRESSE": self.user.address or "",
            "PLZ_ORT": f"{self.user.postal_code or ''} {self.user.city or ''}".strip(),
            "WEBSEITE": self.user.website or "",
            "DATUM": datum_formatiert,
            "STADT": self.user.city or "",
            "KONTAKT_ZEILE": kontakt_zeile,
            "ORT_DATUM": ort_datum,
        }

        # Create user-specific PDF directory
        pdf_dir = os.path.join(config.UPLOAD_FOLDER, f"user_{self.user_id}", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        output_filename = output_filename or f"Anschreiben_{firma_name.replace(' ', '_')}.pdf"
        output_path = os.path.join(pdf_dir, output_filename)

        # Check if using PDF template or text template
        if self.template and self.template.is_pdf_template:
            logger.info("4/5 PDF-Template wird verwendet...")
            logger.info("5/5 Erstelle PDF aus Template...")

            # Use PDFTemplateModifier to generate PDF from template
            modifier = PDFTemplateModifier()
            # Convert variable_positions to dict format if it's a list
            positions_dict = _convert_variable_positions_to_dict(self.template.variable_positions)
            pdf_bytes = modifier.generate_from_template(
                pdf_path=self.template.pdf_path,
                variable_positions=positions_dict,
                replacements=replacements,
            )

            # Write the PDF bytes to output file
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
        else:
            logger.info("4/5 Erstelle vollstaendiges Anschreiben...")
            anschreiben_vollstaendig = self.anschreiben_template
            for var_name, value in replacements.items():
                placeholder = f"{{{{{var_name}}}}}"
                anschreiben_vollstaendig = anschreiben_vollstaendig.replace(placeholder, value)

            # Clean up blank lines from empty variables (e.g. missing address/phone)
            anschreiben_vollstaendig = re.sub(r"\n{3,}", "\n\n", anschreiben_vollstaendig)
            anschreiben_vollstaendig = anschreiben_vollstaendig.strip()

            logger.info("5/5 Erstelle PDF...")
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
            einleitung=einleitung,
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
