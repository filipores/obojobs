#!/usr/bin/env python3
"""
Live test: Generate cover letters for 10 real job postings.
Run from backend/: python3 test_anschreiben_live.py
"""

import json
import sys
import time
import traceback

# Add backend to path
sys.path.insert(0, ".")

from services.ai_client import AIClient
from services.pdf_handler import read_document

# --- Sample CV ---
SAMPLE_CV = """
LEBENSLAUF

Max Mustermann
Musterstraße 12, 80331 München
max.mustermann@email.de | 0176-12345678

BERUFSERFAHRUNG

Senior Frontend Developer | TechStartup GmbH, München | 03/2022 - heute
- Entwicklung einer SaaS-Plattform mit Vue 3, TypeScript und Tailwind CSS
- Aufbau einer Component Library mit Storybook (40+ Komponenten)
- REST-API-Integration und State Management mit Pinia
- CI/CD-Pipeline mit GitHub Actions, automatisierte E2E-Tests mit Playwright
- Mentoring von 2 Junior-Entwicklern

Fullstack Developer | WebAgentur Schmidt, München | 06/2019 - 02/2022
- Kundenwebsites und Webapplikationen mit React, Node.js und PostgreSQL
- E-Commerce-Lösung für mittelständisches Unternehmen (Shopify + Custom Backend)
- Performance-Optimierung: Core Web Vitals um 40% verbessert
- Agile Entwicklung in 2-Wochen-Sprints (Scrum)

Werkstudent Webentwicklung | Digital Minds AG, München | 09/2017 - 05/2019
- WordPress-Themes und Plugins für Kundenportale
- HTML/CSS/JavaScript Frontend-Arbeit
- Erste Erfahrungen mit React und REST-APIs

AUSBILDUNG

B.Sc. Informatik | TU München | 2015 - 2019
- Schwerpunkt: Software Engineering und Datenbanksysteme
- Bachelorarbeit: "Optimierung von Single-Page-Applications"

SKILLS
Sprachen: JavaScript, TypeScript, Python, SQL, HTML/CSS
Frameworks: Vue 3, React, Node.js, Express, Flask
Tools: Git, Docker, GitHub Actions, Jira, Figma
Datenbanken: PostgreSQL, MongoDB, Redis
Sonstiges: Agile/Scrum, REST-APIs, GraphQL, TDD, Responsive Design

SPRACHEN
Deutsch (Muttersprache), Englisch (verhandlungssicher, C1)
"""

# --- Job URLs to test ---
JOB_URLS = [
    "https://de.indeed.com/viewjob?jk=5f0bcf59402a9f05",  # Technischer Standortleiter, Berlin
    "https://de.indeed.com/viewjob?jk=6b033d58e193dacf",  # HR Manager, Schlangenbad
    "https://de.indeed.com/viewjob?jk=4ef275ad129b37fc",  # Teamassistenz, Oberhaching
    "https://de.indeed.com/viewjob?jk=6da2e8fa0d65d613",  # Filialleiter LIDL
    "https://de.indeed.com/viewjob?jk=2b0ced85e6b4dec4",  # Standort- und Operationsleiter
    "https://de.indeed.com/viewjob?jk=52d3ec8a13729fdd",  # MFA Münster
    "https://de.indeed.com/viewjob?jk=611bc9809eacf2fe",  # Gebietsleiter Ophthalmologie
    "https://de.indeed.com/viewjob?jk=89593d93b16f3765",  # Freileitungsmonteur
    "https://de.indeed.com/viewjob?jk=dfbd0647e56519ac",  # Augenheilkunde Freiburg
    "https://de.indeed.com/viewjob?jk=f9600bf3e0ea5e07",  # Leitung Familienzentrum
]

TONES = ["modern", "formal", "kreativ"]


def run_test():
    client = AIClient()
    results = []

    for i, url in enumerate(JOB_URLS):
        tone = TONES[i % 3]  # Rotate through tones
        print(f"\n{'='*80}")
        print(f"[{i+1}/10] URL: {url}")
        print(f"Tone: {tone}")
        print(f"{'='*80}")

        try:
            # Phase 1: Scrape
            print("  Scraping URL...")
            doc_result = read_document(url, return_links=True)
            text = doc_result["text"]
            if not text.strip():
                print("  !! Kein Text extrahiert, überspringe")
                results.append({"url": url, "error": "Kein Text extrahiert"})
                continue
            print(f"  Scrape OK ({len(text)} Zeichen)")

            # Phase 2: Extract details
            print("  Extrahiere Details...")
            from urllib.parse import urlparse

            parsed = urlparse(url)
            firma_name = parsed.netloc.replace("www.", "").split(".")[0].title()
            details = client.extract_bewerbung_details(text, firma_name)
            print(f"  Position: {details['position']}")
            print(f"  Ansprechpartner: {details['ansprechpartner']}")
            print(f"  Quelle: {details['quelle']}")

            # Phase 3: Generate Anschreiben
            print("  Generiere Anschreiben...")
            t0 = time.time()
            anschreiben = client.generate_anschreiben(
                cv_text=SAMPLE_CV,
                stellenanzeige_text=text,
                firma_name=firma_name,
                position=details["position"],
                ansprechpartner=details["ansprechpartner"],
                quelle=details["quelle"],
                zeugnis_text=None,
                bewerber_vorname="Max",
                bewerber_name="Max Mustermann",
                tonalitaet=tone,
            )
            duration = time.time() - t0
            print(f"  Generierung OK ({duration:.1f}s, {len(anschreiben)} Zeichen)")

            # Print the Anschreiben
            print(f"\n--- ANSCHREIBEN (tone={tone}) ---")
            print(anschreiben)
            print("--- ENDE ---\n")

            # Basic quality checks
            issues = []
            # Check for forbidden phrases
            forbidden = [
                "Hiermit bewerbe ich mich",
                "mit großem Interesse",
                "hochmotiviert",
                "hat meine Aufmerksamkeit geweckt",
                "vielfältige Herausforderungen",
                "bin ich der ideale Kandidat",
                "freue mich auf die Herausforderung",
                "in einem dynamischen Umfeld",
                "meine Leidenschaft für",
                "hat mich sofort angesprochen",
                "genau die Mischung aus",
                "spricht mich besonders an",
                "reizt mich besonders",
                "passt genau zu meinen Erfahrungen",
                "technische Tiefe",
                "Lösungskompetenz",
                "praktische Erfahrung mitbringen",
                "bringe ich mit",
                "konnte ich unter Beweis stellen",
                "erfolgreich einsetzen",
            ]
            for phrase in forbidden:
                if phrase.lower() in anschreiben.lower():
                    issues.append(f"VERBOTENE PHRASE: '{phrase}'")

            # Check for dashes
            if " – " in anschreiben:
                issues.append("EN-DASH gefunden")
            if " — " in anschreiben:
                issues.append("EM-DASH gefunden")

            # Check for preambles
            if anschreiben.lower().startswith(("hier ist", "gerne", "natürlich", "klar", "selbstverständlich")):
                issues.append("PREAMBLE nicht entfernt")

            # Check structure
            lines = [l for l in anschreiben.split("\n") if l.strip()]
            if len(lines) < 4:
                issues.append(f"Zu wenige Zeilen: {len(lines)}")

            # Check word count
            words = len(anschreiben.split())
            if words < 150:
                issues.append(f"Zu kurz: {words} Wörter (min 250)")
            elif words > 500:
                issues.append(f"Zu lang: {words} Wörter (max 400)")

            # Check greeting present
            has_greeting = any(
                g in anschreiben for g in ["Sehr geehrte", "Sehr geehrter", "Liebe ", "Lieber ", "Guten Tag", "Hallo"]
            )
            if not has_greeting:
                issues.append("KEINE ANREDE gefunden")

            # Check closing present
            has_closing = any(
                c in anschreiben
                for c in [
                    "Mit freundlichen Grüßen",
                    "Viele Grüße",
                    "Beste Grüße",
                    "Herzliche Grüße",
                    "Freundliche Grüße",
                ]
            )
            if not has_closing:
                issues.append("KEINE GRUSSFORMEL gefunden")

            # Check for hallucinated skills (skills NOT in CV)
            hallucinated_skills = [
                "Angular",
                "Spring Boot",
                "C++",
                "XSLT",
                "Kubernetes",
                "Java ",
                "C# ",
                ".NET",
                "Ruby",
                "Rust",
                "Go ",
                "Terraform",
                "AWS ",
                "Azure",
                "Pflegeerfahrung",
            ]
            for skill in hallucinated_skills:
                if skill in anschreiben:
                    issues.append(f"HALLUZINIERT: '{skill.strip()}'")

            if issues:
                print(f"  !! ISSUES ({len(issues)}):")
                for issue in issues:
                    print(f"     - {issue}")
            else:
                print("  OK - Keine Issues gefunden")

            results.append(
                {
                    "url": url,
                    "tone": tone,
                    "position": details["position"],
                    "firma": firma_name,
                    "ansprechpartner": details["ansprechpartner"],
                    "word_count": words,
                    "char_count": len(anschreiben),
                    "duration_s": round(duration, 1),
                    "issues": issues,
                    "anschreiben": anschreiben,
                }
            )

        except Exception as e:
            print(f"  !! FEHLER: {e}")
            traceback.print_exc()
            results.append({"url": url, "error": str(e)})

        # Small delay between API calls
        time.sleep(1)

    # --- Summary ---
    print(f"\n\n{'='*80}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*80}")

    success = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    print(f"\nErfolgreich: {len(success)}/{len(results)}")
    print(f"Fehler: {len(errors)}/{len(results)}")

    if success:
        avg_words = sum(r["word_count"] for r in success) / len(success)
        avg_duration = sum(r["duration_s"] for r in success) / len(success)
        total_issues = sum(len(r["issues"]) for r in success)
        print(f"Durchschnittl. Wörter: {avg_words:.0f}")
        print(f"Durchschnittl. Dauer: {avg_duration:.1f}s")
        print(f"Gesamt-Issues: {total_issues}")

        print("\n--- Pro Anschreiben ---")
        for r in success:
            status = "OK" if not r["issues"] else f"{len(r['issues'])} Issues"
            print(f"  [{r['tone']:8s}] {r['position'][:40]:40s} | {r['word_count']} W | {r['duration_s']}s | {status}")
            for issue in r["issues"]:
                print(f"           !! {issue}")

    if errors:
        print("\n--- Fehler ---")
        for r in errors:
            print(f"  {r['url']}: {r['error']}")

    # Save full results to file
    output_file = "test_anschreiben_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nVollständige Ergebnisse gespeichert in: {output_file}")


if __name__ == "__main__":
    run_test()
