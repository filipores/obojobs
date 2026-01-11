#!/usr/bin/env python3
import sys
import argparse
from src.tracker import BewerbungsTracker
from config import config


def main():
    parser = argparse.ArgumentParser(description='Bewerbungs-Tracking: Statistiken und Übersicht')
    parser.add_argument('--list', type=int, default=10,
                       help='Anzahl der letzten Bewerbungen (Standard: 10)')
    parser.add_argument('--all', action='store_true', help='Alle Bewerbungen anzeigen')
    parser.add_argument('--latest', action='store_true', help='Zeigt Email-Info der letzten Bewerbung')
    args = parser.parse_args()

    try:
        tracker = BewerbungsTracker(config.TRACKING_JSON_PATH)

        if args.latest:
            bew = tracker.get_latest_bewerbung()
            if bew:
                print(f"\n{'='*80}")
                print("📧 LETZTE BEWERBUNG - EMAIL-INFORMATIONEN")
                print(f"{'='*80}\n")
                print(f"Firma: {bew['firma']}")
                print(f"Position: {bew['position']}")
                print(f"An: {bew['email'] or 'Keine E-Mail-Adresse'}")
                print(f"Betreff: {bew['betreff']}")
                print(f"\nEmail-Text:\n{bew['email_text']}")
                print(f"\n{'='*80}\n")
            else:
                print("Noch keine Bewerbungen vorhanden")
            return 0

        stats = tracker.get_statistik()
        print(f"\n{'='*80}")
        print("📊 BEWERBUNGS-STATISTIKEN")
        print(f"{'='*80}\n")
        print(f"Gesamt: {stats['gesamt']} Bewerbungen")
        print(f"  └─ Erstellt: {stats['erstellt']}")
        print(f"  └─ Versendet: {stats['versendet']}")
        print(f"  └─ Antwort erhalten: {stats['antwort_erhalten']}")
        print()

        limit = None if args.all else args.list
        tracker.list_bewerbungen(limit=limit if limit else 1000)
        return 0
    except Exception as e:
        print(f"\n✗ Fehler: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
