import json
import os
from typing import Optional, Dict

from config import config
from models import db, Document, Template, Application
from .api_client import ClaudeAPIClient
from .pdf_handler import read_document, create_anschreiben_pdf, is_url


class BewerbungsGenerator:
    def __init__(self, user_id: int, template_id: Optional[int] = None):
        self.user_id = user_id
        self.template_id = template_id
        self.api_client = ClaudeAPIClient()
        self.cv_text = None
        self.anschreiben_template = None
        self.zeugnis_text = None
        self.extracted_links = None
        self.load_user_documents()

    def load_user_documents(self):
        """Load documents from database for this user"""
        print(f"Lade Dokumente für User {self.user_id}...")

        # Load Lebenslauf (Pflicht)
        cv_doc = Document.query.filter_by(user_id=self.user_id, doc_type='lebenslauf').first()
        if cv_doc and os.path.exists(cv_doc.file_path):
            self.cv_text = read_document(cv_doc.file_path)
            print("✓ Lebenslauf geladen")
        else:
            raise ValueError("Lebenslauf nicht gefunden. Bitte lade deinen Lebenslauf hoch.")

        # Load Arbeitszeugnis (Pflicht)
        zeugnis_doc = Document.query.filter_by(user_id=self.user_id, doc_type='arbeitszeugnis').first()
        if zeugnis_doc and os.path.exists(zeugnis_doc.file_path):
            self.zeugnis_text = read_document(zeugnis_doc.file_path)
            print("✓ Arbeitszeugnis geladen")
        else:
            raise ValueError("Arbeitszeugnis nicht gefunden. Bitte lade dein letztes Arbeitszeugnis hoch.")

        # Load Anschreiben-Template
        if self.template_id:
            # Specific template requested
            template = Template.query.filter_by(id=self.template_id, user_id=self.user_id).first()
            if template:
                self.anschreiben_template = template.content
                print(f"✓ Template '{template.name}' geladen (ID: {self.template_id})")
            else:
                raise ValueError(f"Template mit ID {self.template_id} nicht gefunden.")
        else:
            # Load Anschreiben-Template (falls hochgeladen)
            anschreiben_doc = Document.query.filter_by(user_id=self.user_id, doc_type='anschreiben').first()
            if anschreiben_doc and os.path.exists(anschreiben_doc.file_path):
                # Use uploaded Anschreiben as template
                self.anschreiben_template = read_document(anschreiben_doc.file_path)
                print("✓ Anschreiben-Vorlage aus Upload geladen")
            else:
                # Falls kein Anschreiben hochgeladen, nutze Template aus DB
                template = Template.query.filter_by(user_id=self.user_id, is_default=True).first()
                if not template:
                    template = Template.query.filter_by(user_id=self.user_id).first()
                if template:
                    self.anschreiben_template = template.content
                    print("✓ Template geladen")
                else:
                    raise ValueError("Kein Template gefunden. Bitte erstelle ein Template oder lade ein Anschreiben hoch.")

        print("✓ Dokumente geladen")

    def generate_bewerbung(self, stellenanzeige_path: str, firma_name: str,
                          output_filename: Optional[str] = None) -> str:
        print(f"\n{'='*60}")
        print(f"Generiere Bewerbung für: {firma_name}")
        print(f"{'='*60}")

        print("1/5 Lese Stellenanzeige...")

        if is_url(stellenanzeige_path):
            print(f"  → Lade von URL: {stellenanzeige_path}")
            doc_result = read_document(stellenanzeige_path, return_links=True)
            stellenanzeige_text = doc_result['text']

            # Zeige gefundene Links
            if doc_result.get('email_links'):
                print(f"  → {len(doc_result['email_links'])} E-Mail-Link(s) gefunden")
            if doc_result.get('application_links'):
                print(f"  → {len(doc_result['application_links'])} Bewerbungs-Link(s) gefunden")

            # Speichere Links für spätere Verwendung
            self.extracted_links = doc_result
        else:
            stellenanzeige_text = read_document(stellenanzeige_path)
            self.extracted_links = None

        print("✓ Stellenanzeige geladen")

        print("2/5 Extrahiere Details (Position, Ansprechpartner, Quelle)...")
        details = self.api_client.extract_bewerbung_details(stellenanzeige_text, firma_name)
        print(f"✓ Details extrahiert:")
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
            use_extraction=config.USE_EXTRACTION
        )
        print(f"✓ Einleitung generiert ({len(einleitung)} Zeichen)")
        print(f"\nGenerierte Einleitung:\n{'-'*60}\n{einleitung}\n{'-'*60}\n")

        print("4/5 Erstelle vollständiges Anschreiben...")
        anschreiben_vollstaendig = self.anschreiben_template
        for placeholder, value in {
            '{{FIRMA}}': firma_name,
            '{{ANSPRECHPARTNER}}': details['ansprechpartner'],
            '{{POSITION}}': details['position'],
            '{{QUELLE}}': details['quelle'],
            '{{EINLEITUNG}}': einleitung
        }.items():
            anschreiben_vollstaendig = anschreiben_vollstaendig.replace(placeholder, value)

        print("5/5 Erstelle PDF...")
        # Create user-specific PDF directory
        pdf_dir = os.path.join(config.UPLOAD_FOLDER, f'user_{self.user_id}', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)

        output_filename = output_filename or f"Anschreiben_{firma_name.replace(' ', '_')}.pdf"
        output_path = os.path.join(pdf_dir, output_filename)
        create_anschreiben_pdf(anschreiben_vollstaendig, output_path, firma_name)
        print(f"✓ Bewerbung erstellt: {output_path}")

        # Email-Daten generieren mit verbesserter Personalisierung
        betreff = self.api_client.generate_betreff(details['position'], firma_name, style='professional')
        email_text = self.api_client.generate_email_text(
            position=details['position'],
            ansprechperson=details['ansprechpartner'],
            firma_name=firma_name
        )

        # Sammle alle extrahierten Informationen
        extracted_info = {
            'email_from_text': details.get('email', ''),
            'email_links': [],
            'application_links': [],
            'all_links': []
        }

        if self.extracted_links:
            extracted_info['email_links'] = self.extracted_links.get('email_links', [])
            extracted_info['application_links'] = self.extracted_links.get('application_links', [])
            extracted_info['all_links'] = self.extracted_links.get('all_links', [])

        # Save to database
        application = Application(
            user_id=self.user_id,
            firma=firma_name,
            position=details['position'],
            ansprechpartner=details['ansprechpartner'],
            email=details.get('email', ''),
            quelle=details['quelle'],
            status='erstellt',
            pdf_path=output_path,
            betreff=betreff,
            email_text=email_text,
            links_json=json.dumps(extracted_info)
        )
        db.session.add(application)
        db.session.commit()

        # Zeige Email-Informationen an
        print(f"\n{'='*60}")
        print("📧 EMAIL-INFORMATIONEN")
        print(f"{'='*60}")
        print(f"An: {details.get('email') or 'Keine E-Mail-Adresse gefunden'}")
        print(f"Betreff: {betreff}")
        print(f"\nText:\n{email_text}")

        # Zeige extrahierte Links
        if extracted_info['email_links']:
            print(f"\n📧 Gefundene E-Mail-Links:")
            for link in extracted_info['email_links']:
                print(f"  - {link['email']} ({link['text']})")

        if extracted_info['application_links']:
            print(f"\n🔗 Gefundene Bewerbungs-Links:")
            for link in extracted_info['application_links'][:5]:  # Max 5 zeigen
                print(f"  - {link['text']}: {link['url']}")

        print(f"{'='*60}\n")

        return output_path

    def process_firma(self, firma_config: Dict[str, str]) -> Optional[str]:
        try:
            firma_name = firma_config.get('name')
            stellenanzeige_path = firma_config.get('stellenanzeige')

            if not firma_name or not stellenanzeige_path:
                raise ValueError("Firma-Config muss 'name' und 'stellenanzeige' enthalten")

            return self.generate_bewerbung(stellenanzeige_path, firma_name)
        except Exception as e:
            print(f"✗ Fehler bei {firma_config.get('name', 'unbekannt')}: {str(e)}")
            return None
