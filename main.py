#!/usr/bin/env python3
import sys
import os
import argparse
import tempfile
import pyperclip
from src.generator import BewerbungsGenerator
from config import config


def main():
    parser = argparse.ArgumentParser(
        description='Bewerbungsautomation mit Claude AI',
        epilog='Beispiele:\n'
               '  python main.py "Firma AG"                        # Aus Zwischenablage\n'
               '  python main.py stellenanzeige.txt "Firma AG"     # Aus Datei\n'
               '  python main.py https://firma.de/job "Firma AG"   # Aus URL',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('firma_oder_datei', help='Firmenname oder Pfad zur Stellenanzeige')
    parser.add_argument('firma_name', nargs='?', help='Name der Firma (falls erster Parameter Dateipfad ist)')
    parser.add_argument('--no-extraction', action='store_true',
                       help='Deaktiviert zweistufige Informationsextraktion')
    args = parser.parse_args()

    try:
        config.validate_config()
        generator = BewerbungsGenerator()
        if args.no_extraction:
            config.USE_EXTRACTION = False

        # Bestimme, ob erster Parameter Datei oder Firmenname ist
        if args.firma_name:
            # Zwei Parameter: erster ist Datei, zweiter ist Firmenname
            stellenanzeige_path = args.firma_oder_datei
            firma_name = args.firma_name
        else:
            # Ein Parameter: Firmenname, lese aus Zwischenablage
            firma_name = args.firma_oder_datei
            print("📋 Lese Stellenanzeige aus Zwischenablage...")

            try:
                clipboard_content = pyperclip.paste()
                if not clipboard_content or len(clipboard_content.strip()) < 50:
                    print("✗ Zwischenablage ist leer oder zu kurz.")
                    print("Kopiere die Stellenanzeige und versuche es erneut.")
                    return 1

                # Temporäre Datei erstellen
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(clipboard_content)
                    stellenanzeige_path = f.name

                print(f"✓ Stellenanzeige aus Zwischenablage geladen ({len(clipboard_content)} Zeichen)")

            except Exception as e:
                print(f"✗ Fehler beim Lesen der Zwischenablage: {str(e)}")
                return 1

        anschreiben_path = generator.process_firma({
            'name': firma_name,
            'stellenanzeige': stellenanzeige_path
        })

        # Temporäre Datei löschen falls erstellt
        if not args.firma_name and os.path.exists(stellenanzeige_path):
            os.unlink(stellenanzeige_path)

        if anschreiben_path:
            print(f"\n{'='*60}")
            print("✓ Erfolgreich abgeschlossen!")
            print(f"{'='*60}")
            return 0
        else:
            print("\n✗ Fehler bei der Verarbeitung")
            return 1
    except KeyboardInterrupt:
        print("\n\nAbbruch durch Benutzer")
        return 130
    except Exception as e:
        print(f"\n✗ Fehler: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
