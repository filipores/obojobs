import json
import os

from config import config
from models import Application, Document, JobRequirement, Template, db

from .api_client import ClaudeAPIClient
from .pdf_handler import create_anschreiben_pdf, is_url, read_document
from .pdf_template_modifier import PDFTemplateModifier
from .requirement_analyzer import RequirementAnalyzer
from .template_generator import get_or_create_default_template


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
        self.load_user_documents()

    def load_user_documents(self):
        """Load documents from database for this user"""
        print(f"Lade Dokumente für User {self.user_id}...")

        # Load Lebenslauf (Pflicht)
        cv_doc = Document.query.filter_by(user_id=self.user_id, doc_type="lebenslauf").first()
        if cv_doc and os.path.exists(cv_doc.file_path):
            self.cv_text = read_document(cv_doc.file_path)
            print("✓ Lebenslauf geladen")
        else:
            raise ValueError("Lebenslauf nicht gefunden. Bitte lade deinen Lebenslauf hoch.")

        # Load Arbeitszeugnis (Optional)
        zeugnis_doc = Document.query.filter_by(user_id=self.user_id, doc_type="arbeitszeugnis").first()
        if zeugnis_doc and os.path.exists(zeugnis_doc.file_path):
            self.zeugnis_text = read_document(zeugnis_doc.file_path)
            print("✓ Arbeitszeugnis geladen")
        else:
            self.zeugnis_text = None
            print("ℹ Arbeitszeugnis nicht vorhanden (optional)")

        # Load Anschreiben-Template
        if self.template_id:
            # Specific template requested
            template = Template.query.filter_by(id=self.template_id, user_id=self.user_id).first()
            if template:
                self.template = template
                self.anschreiben_template = template.content
                print(f"✓ Template '{template.name}' geladen (ID: {self.template_id})")
                if template.is_pdf_template:
                    print(f"  → PDF-Template erkannt: {template.pdf_path}")
            else:
                raise ValueError(f"Template mit ID {self.template_id} nicht gefunden.")
        else:
            # Load Anschreiben-Template (falls hochgeladen)
            anschreiben_doc = Document.query.filter_by(user_id=self.user_id, doc_type="anschreiben").first()
            if anschreiben_doc and os.path.exists(anschreiben_doc.file_path):
                # Use uploaded Anschreiben as template
                self.anschreiben_template = read_document(anschreiben_doc.file_path)
                print("✓ Anschreiben-Vorlage aus Upload geladen")
            else:
                # Falls kein Anschreiben hochgeladen, nutze Template aus DB
                # Auto-create default template if none exists
                template = get_or_create_default_template(self.user_id)
                self.template = template
                self.anschreiben_template = template.content
                if template.name == "Standard-Vorlage (automatisch erstellt)":
                    print("✓ Standard-Template automatisch erstellt")
                else:
                    print("✓ Template geladen")
                if template.is_pdf_template:
                    print(f"  → PDF-Template erkannt: {template.pdf_path}")

        print("✓ Dokumente geladen")

    def generate_bewerbung(self, stellenanzeige_path: str, firma_name: str, output_filename: str | None = None) -> str:
        print(f"\n{'=' * 60}")
        print(f"Generiere Bewerbung für: {firma_name}")
        print(f"{'=' * 60}")

        print("1/5 Lese Stellenanzeige...")

        if is_url(stellenanzeige_path):
            print(f"  → Lade von URL: {stellenanzeige_path}")
            doc_result = read_document(stellenanzeige_path, return_links=True)
            stellenanzeige_text = doc_result["text"]

            # Zeige gefundene Links
            if doc_result.get("email_links"):
                print(f"  → {len(doc_result['email_links'])} E-Mail-Link(s) gefunden")
            if doc_result.get("application_links"):
                print(f"  → {len(doc_result['application_links'])} Bewerbungs-Link(s) gefunden")

            # Speichere Links für spätere Verwendung
            self.extracted_links = doc_result
        else:
            stellenanzeige_text = read_document(stellenanzeige_path)
            self.extracted_links = None

        print("✓ Stellenanzeige geladen")

        print("2/5 Extrahiere Details (Position, Ansprechpartner, Quelle)...")
        details = self.api_client.extract_bewerbung_details(stellenanzeige_text, firma_name)
        print("✓ Details extrahiert:")
        print(f"  - Position: {details['position']}")
        print(f"  - Ansprechpartner: {details['ansprechpartner']}")
        print(f"  - Quelle: {details['quelle']}")

        print("3/5 Generiere personalisierten Einleitungsabsatz mit Claude...")
        einleitung = self.api_client.generate_einleitung(
            cv_text=self.cv_text,
            stellenanzeige_text=stellenanzeige_text,
            firma_name=firma_name,
            zeugnis_text=self.zeugnis_text,
            details=details,
            use_extraction=config.USE_EXTRACTION,
        )
        print(f"✓ Einleitung generiert ({len(einleitung)} Zeichen)")
        print(f"\nGenerierte Einleitung:\n{'-' * 60}\n{einleitung}\n{'-' * 60}\n")

        # Prepare variable replacements
        replacements = {
            "FIRMA": firma_name,
            "ANSPRECHPARTNER": details["ansprechpartner"],
            "POSITION": details["position"],
            "QUELLE": details["quelle"],
            "EINLEITUNG": einleitung,
        }

        # Create user-specific PDF directory
        pdf_dir = os.path.join(config.UPLOAD_FOLDER, f"user_{self.user_id}", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        output_filename = output_filename or f"Anschreiben_{firma_name.replace(' ', '_')}.pdf"
        output_path = os.path.join(pdf_dir, output_filename)

        # Check if using PDF template or text template
        if self.template and self.template.is_pdf_template:
            print("4/5 PDF-Template wird verwendet...")
            print("5/5 Erstelle PDF aus Template...")

            # Use PDFTemplateModifier to generate PDF from template
            modifier = PDFTemplateModifier()
            pdf_bytes = modifier.generate_from_template(
                pdf_path=self.template.pdf_path,
                variable_positions=self.template.variable_positions or {},
                replacements=replacements,
            )

            # Write the PDF bytes to output file
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
        else:
            print("4/5 Erstelle vollständiges Anschreiben...")
            anschreiben_vollstaendig = self.anschreiben_template
            for var_name, value in replacements.items():
                placeholder = f"{{{{{var_name}}}}}"
                anschreiben_vollstaendig = anschreiben_vollstaendig.replace(placeholder, value)

            print("5/5 Erstelle PDF...")
            create_anschreiben_pdf(anschreiben_vollstaendig, output_path, firma_name)

        print(f"✓ Bewerbung erstellt: {output_path}")

        # Email-Daten generieren mit verbesserter Personalisierung
        betreff = self.api_client.generate_betreff(details["position"], firma_name, style="professional")
        email_text = self.api_client.generate_email_text(
            position=details["position"], ansprechperson=details["ansprechpartner"], firma_name=firma_name
        )

        # Sammle alle extrahierten Informationen
        extracted_info = {
            "email_from_text": details.get("email", ""),
            "email_links": [],
            "application_links": [],
            "all_links": [],
        }

        if self.extracted_links:
            extracted_info["email_links"] = self.extracted_links.get("email_links", [])
            extracted_info["application_links"] = self.extracted_links.get("application_links", [])
            extracted_info["all_links"] = self.extracted_links.get("all_links", [])

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
            links_json=json.dumps(extracted_info),
        )
        # Initialize status history with 'erstellt'
        application.add_status_change("erstellt")
        db.session.add(application)
        db.session.commit()

        # Extract and save job requirements in background
        self._extract_requirements(application.id, stellenanzeige_text)

        # Zeige Email-Informationen an
        print(f"\n{'=' * 60}")
        print("📧 EMAIL-INFORMATIONEN")
        print(f"{'=' * 60}")
        print(f"An: {details.get('email') or 'Keine E-Mail-Adresse gefunden'}")
        print(f"Betreff: {betreff}")
        print(f"\nText:\n{email_text}")

        # Zeige extrahierte Links
        if extracted_info["email_links"]:
            print("\n📧 Gefundene E-Mail-Links:")
            for link in extracted_info["email_links"]:
                print(f"  - {link['email']} ({link['text']})")

        if extracted_info["application_links"]:
            print("\n🔗 Gefundene Bewerbungs-Links:")
            for link in extracted_info["application_links"][:5]:  # Max 5 zeigen
                print(f"  - {link['text']}: {link['url']}")

        print(f"{'=' * 60}\n")

        return output_path

    def process_firma(self, firma_config: dict[str, str]) -> str | None:
        try:
            firma_name = firma_config.get("name")
            stellenanzeige_path = firma_config.get("stellenanzeige")

            if not firma_name or not stellenanzeige_path:
                raise ValueError("Firma-Config muss 'name' und 'stellenanzeige' enthalten")

            return self.generate_bewerbung(stellenanzeige_path, firma_name)
        except Exception as e:
            print(f"✗ Fehler bei {firma_config.get('name', 'unbekannt')}: {str(e)}")
            return None

    def _extract_requirements(self, application_id: int, job_text: str) -> None:
        """Extract job requirements from job posting text and save to database.

        This runs silently and doesn't block the main application generation.
        Errors are logged but don't cause the main flow to fail.
        """
        try:
            print("→ Extrahiere Anforderungen aus Stellenanzeige...")
            analyzer = RequirementAnalyzer()
            requirements = analyzer.analyze_requirements(job_text)

            if not requirements:
                print("  → Keine Anforderungen gefunden")
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
            print(f"✓ {len(requirements)} Anforderungen extrahiert ({must_have_count} Pflicht, {nice_to_have_count} Optional)")

        except Exception as e:
            print(f"⚠ Anforderungs-Extraktion fehlgeschlagen: {str(e)}")
