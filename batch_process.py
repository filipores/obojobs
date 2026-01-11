#!/usr/bin/env python3
import sys
import os
import json
import argparse
from typing import List, Dict
from src.generator import BewerbungsGenerator
from config import config


def load_firmen_config(config_file: str) -> List[Dict[str, str]]:
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_firmen_directory(directory: str) -> List[Dict[str, str]]:
    firmen = []
    for filename in os.listdir(directory):
        if filename.endswith(('.txt', '.pdf')) and not filename.startswith('.'):
            filepath = os.path.join(directory, filename)
            firma_name = os.path.splitext(filename)[0].replace('_', ' ')
            firmen.append({'name': firma_name, 'stellenanzeige': filepath})
    return firmen


def load_firmen_from_urls_file(urls_file: str) -> List[Dict[str, str]]:
    """
    Lädt Firmen aus einer URL-Liste.
    Format: URL | Firmenname (eine pro Zeile)
    """
    firmen = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse: URL | Firmenname
            if '|' in line:
                parts = line.split('|', 1)
                url = parts[0].strip()
                firma_name = parts[1].strip()
            else:
                # Nur URL, versuche Firmennamen zu erraten
                url = line.strip()
                from src.web_scraper import WebScraper
                scraper = WebScraper()
                firma_name = scraper.extract_company_name_from_url(url)
                print(f"  → Zeile {line_num}: Kein Firmenname angegeben, verwende '{firma_name}'")

            firmen.append({
                'name': firma_name,
                'stellenanzeige': url
            })

    return firmen


def main():
    parser = argparse.ArgumentParser(description='Batch-Verarbeitung mehrerer Bewerbungen')
    parser.add_argument('--config', help='Pfad zur JSON-Config-Datei')
    parser.add_argument('--directory', help='Verzeichnis mit Stellenanzeigen')
    parser.add_argument('--urls', help='Pfad zu URL-Liste (Format: URL | Firmenname)')
    parser.add_argument('--limit', type=int, help='Maximale Anzahl')
    parser.add_argument('--no-extraction', action='store_true',
                       help='Deaktiviert zweistufige Informationsextraktion')
    args = parser.parse_args()

    try:
        config.validate_config()

        if args.urls:
            print(f"Lade Firmen aus URL-Liste: {args.urls}")
            firmen = load_firmen_from_urls_file(args.urls)
        elif args.config:
            print(f"Lade Firmen aus Config-Datei: {args.config}")
            firmen = load_firmen_config(args.config)
        elif args.directory:
            print(f"Scanne Verzeichnis: {args.directory}")
            firmen = scan_firmen_directory(args.directory)
        else:
            print(f"Scanne Standard-Verzeichnis: {config.FIRMEN_DIR}")
            firmen = scan_firmen_directory(config.FIRMEN_DIR)

        if not firmen:
            print("Keine Firmen gefunden")
            return 1

        if args.limit:
            firmen = firmen[:args.limit]

        print(f"\n{'='*60}")
        print(f"Verarbeite {len(firmen)} Firma(en)")
        print(f"{'='*60}\n")

        generator = BewerbungsGenerator()
        generator.load_standard_documents()

        if args.no_extraction:
            config.USE_EXTRACTION = False

        erfolg = 0
        fehler = 0

        for i, firma in enumerate(firmen, 1):
            print(f"\n[{i}/{len(firmen)}] {firma['name']}")
            print("-" * 60)
            if generator.process_firma(firma):
                erfolg += 1
            else:
                fehler += 1

        print(f"\n{'='*60}")
        print("ZUSAMMENFASSUNG")
        print(f"{'='*60}")
        print(f"Erfolgreich: {erfolg}")
        print(f"Fehler: {fehler}")
        print(f"Gesamt: {len(firmen)}")
        print(f"{'='*60}\n")

        return 0 if fehler == 0 else 1
    except KeyboardInterrupt:
        print("\n\nAbbruch durch Benutzer")
        return 130
    except Exception as e:
        print(f"\n✗ Fehler: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
