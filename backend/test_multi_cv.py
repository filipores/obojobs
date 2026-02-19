"""Test pipeline with diverse CVs against matching and non-matching postings."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

from services.ai_client import AIClient
from services.prompts import FORBIDDEN_PHRASES
from services.output_validator import OutputValidator

with open("evals/fixtures/postings.json") as f:
    postings = json.load(f)
posting_map = {p["id"]: p for p in postings}

client = AIClient()
validator = OutputValidator()

# === 4 DIVERSE CVs ===

CV_MARKETING = """SARAH MÜLLER
Online Marketing Managerin | Berlin
+49 176 55443322 | sarah.mueller@mail.de

PROFIL
Erfahrene Online Marketing Managerin mit 5 Jahren Berufserfahrung in Performance Marketing,
SEA/SEO und Social Media. Datengetriebene Arbeitsweise mit Fokus auf Conversion-Optimierung.

BERUFSERFAHRUNG

Online Marketing Managerin | fashionette AG, Düsseldorf | 2021 – heute
- Verantwortung für Google Ads und Meta Ads mit Budgets bis 500k EUR/Monat
- SEA-Kampagnen mit ROAS von 4.2 (Branchendurchschnitt: 2.8)
- A/B-Testing von Landingpages, Conversion Rate +35%
- Google Analytics 4, Looker Studio, Google Tag Manager
- Zusammenarbeit mit CRM-Team für Retention-Kampagnen

Junior Online Marketing Managerin | aboutyou GmbH, Hamburg | 2019 – 2021
- SEO-Strategie: Organischer Traffic +60% in 12 Monaten
- Social Media Kampagnen auf Instagram, TikTok, Pinterest
- Influencer-Marketing Kooperationen koordiniert
- Content-Erstellung mit Canva und Adobe Creative Suite
- Reporting in Google Data Studio und Excel

Praktikum Marketing | Tchibo GmbH, Hamburg | 2018 – 2019
- Unterstützung bei Newsletter-Kampagnen (Mailchimp)
- Wettbewerbsanalysen und Marktrecherche

AUSBILDUNG
B.A. Medien- und Kommunikationswissenschaft | Universität Hamburg | 2015 – 2018

SKILLS
Google Ads, Meta Ads, Google Analytics 4, SEO (Sistrix, Screaming Frog), Looker Studio,
Google Tag Manager, Mailchimp, Canva, Adobe Photoshop, Excel, HTML/CSS (Grundlagen),
A/B-Testing, Conversion-Optimierung, Shopify (Backend)

SPRACHEN
Deutsch (Muttersprache), Englisch (C1), Französisch (B1)
"""

CV_PFLEGE = """THOMAS WEBER
Gesundheits- und Krankenpfleger | Hamburg
+49 151 77889900 | t.weber@gmx.de

PROFIL
Examinierter Gesundheits- und Krankenpfleger mit 8 Jahren Berufserfahrung in der
stationären Akutpflege. Weiterbildung in Intensivpflege und Notfallmedizin.

BERUFSERFAHRUNG

Gesundheits- und Krankenpfleger | UKE Hamburg, Intensivstation | 2020 – heute
- Pflege und Überwachung von beatmeten Patient:innen auf der ITS
- Manchester Triage in der interdisziplinären Notaufnahme (Vertretung)
- Anleitung von Auszubildenden und neuen Teammitgliedern
- Qualitätsmanagement und Hygienebeauftragter der Station
- Schichtleitung im Drei-Schicht-System (bis 12 Patient:innen)

Gesundheits- und Krankenpfleger | Asklepios Klinik Barmbek | 2016 – 2020
- Allgemeinchirurgische Station, postoperative Versorgung
- Wundmanagement und Schmerztherapie-Dokumentation
- Mobilisation und Rehabilitation nach Eingriffen
- Zusammenarbeit mit Physiotherapie und Sozialdienst

AUSBILDUNG
Examen Gesundheits- und Krankenpflege | Albertinen Schule, Hamburg | 2013 – 2016
Weiterbildung Intensivpflege und Anästhesie | UKE Hamburg | 2021 – 2022

QUALIFIKATIONEN
- Fachweiterbildung Intensivpflege und Anästhesie (DKG-anerkannt)
- Praxisanleiter (200 Std.)
- BLS/ALS-Zertifizierung (aktuell)
- Hygienebeauftragter (Grundkurs)

SPRACHEN
Deutsch (Muttersprache), Englisch (B2), Türkisch (B1)
"""

CV_BWL = """LISA SCHMIDT
Controllerin | Frankfurt am Main
+49 170 12345678 | lisa.schmidt@outlook.de

PROFIL
Controllerin mit 4 Jahren Erfahrung in Finanzplanung, Reporting und Kostenrechnung.
SAP-Kenntnisse (FI/CO) und fortgeschrittene Excel/Power BI-Anwendung.

BERUFSERFAHRUNG

Controllerin | Continental AG, Frankfurt | 2022 – heute
- Monatliches Reporting für 3 Business Units (Umsatz >200 Mio EUR)
- Budgetplanung und Forecast-Erstellung in SAP BPC
- Abweichungsanalysen und Ad-hoc-Reporting für das Management
- Aufbau automatisierter Dashboards in Power BI
- Mitarbeit an der Einführung von SAP S/4HANA

Junior Controllerin | Daimler AG, Stuttgart | 2020 – 2022
- Kostenstellenrechnung und Profit-Center-Auswertungen
- Investitionscontrolling und Business Cases
- Konsolidierung in SAP BPC
- Excel-Modellierung für Szenarioanalysen

Werkstudentin Controlling | KPMG AG, Frankfurt | 2018 – 2020
- Unterstützung bei Jahresabschlussprüfungen
- Datenaufbereitung und Analyse in Excel und IDEA

AUSBILDUNG
M.Sc. Finance & Accounting | Goethe-Universität Frankfurt | 2018 – 2020
B.Sc. Betriebswirtschaftslehre | Universität Mannheim | 2015 – 2018

SKILLS
SAP FI/CO, SAP BPC, SAP S/4HANA (Grundlagen), Power BI, Excel (VBA-Makros),
IDEA, Kostenrechnung, Budgetplanung, IFRS, HGB, Konsolidierung

SPRACHEN
Deutsch (Muttersprache), Englisch (C1), Spanisch (A2)
"""

CV_INGENIEUR = """MARKUS HARTMANN
Maschinenbauingenieur | München
+49 160 98765432 | m.hartmann@web.de

PROFIL
Maschinenbauingenieur mit 6 Jahren Erfahrung in Konstruktion und Fertigungstechnik.
Spezialisiert auf CAD-Design und Produktionsoptimierung in der Automobilindustrie.

BERUFSERFAHRUNG

Konstruktionsingenieur | BMW Group, München | 2021 – heute
- 3D-Konstruktion von Karosseriebauteilen in CATIA V5 und NX
- FEM-Simulation mit ANSYS für Crashsicherheit und Steifigkeit
- Toleranzmanagement und GD&T nach ISO GPS
- Zusammenarbeit mit Zulieferern und Werkzeugbau
- Prototypenbegleitung und Erstmusterprüfung

Entwicklungsingenieur | Continental AG, Regensburg | 2018 – 2021
- Konstruktion von Bremssystemkomponenten in SolidWorks
- FMEA-Erstellung und Risikobewertung
- Optimierung von Spritzgussprozessen, Zykluszeit -15%
- Technische Dokumentation nach IATF 16949

AUSBILDUNG
M.Eng. Maschinenbau | TU München | 2016 – 2018
Schwerpunkt: Leichtbau und Faserverbundtechnologie
B.Eng. Maschinenbau | Hochschule München | 2012 – 2016

SKILLS
CATIA V5, Siemens NX, SolidWorks, ANSYS (FEM), AutoCAD, SAP PLM,
GD&T/ISO GPS, FMEA, IATF 16949, Lean Manufacturing, Six Sigma (Green Belt)

SPRACHEN
Deutsch (Muttersprache), Englisch (C1), Tschechisch (A2)
"""

# === TEST MATRIX ===
# Each CV gets 3 postings: good match, partial match, completely different field

TEST_MATRIX = [
    {
        "name": "Sarah (Marketing)",
        "cv": CV_MARKETING,
        "vorname": "Sarah",
        "full_name": "Sarah Müller",
        "tests": [
            (23, "gut passend — Otto Marketing Manager"),
            (24, "teilweise — Henkel Brand Manager"),
            (13, "fachfremd — Siemens Ingenieur"),
        ],
    },
    {
        "name": "Thomas (Pflege)",
        "cv": CV_PFLEGE,
        "vorname": "Thomas",
        "full_name": "Thomas Weber",
        "tests": [
            (8, "gut passend — Asklepios Pflegefachkraft"),
            (42, "teilweise — UKE Physiotherapeut"),
            (30, "fachfremd — N26 Frontend Engineer"),
        ],
    },
    {
        "name": "Lisa (Controlling)",
        "cv": CV_BWL,
        "vorname": "Lisa",
        "full_name": "Lisa Schmidt",
        "tests": [
            (16, "gut passend — Deutsche Bank Controller"),
            (20, "teilweise — KPMG Consulting PM"),
            (28, "fachfremd — Continental Maschinenbau"),
        ],
    },
    {
        "name": "Markus (Maschinenbau)",
        "cv": CV_INGENIEUR,
        "vorname": "Markus",
        "full_name": "Markus Hartmann",
        "tests": [
            (17, "gut passend — BMW Entwicklungsingenieur"),
            (33, "teilweise — VW Quality Engineer"),
            (15, "fachfremd — Zalando Data Engineer"),
        ],
    },
]

results = []

for profile in TEST_MATRIX:
    cv = profile["cv"]
    print(f"\n{'#'*60}")
    print(f"# CV: {profile['name']}")
    print(f"{'#'*60}")

    for posting_id, label in profile["tests"]:
        posting = posting_map[posting_id]
        firma = posting["firma"]
        text = posting["text"]
        print(f"\n{'='*60}")
        print(f"ID {posting_id}: {firma} [{label}]")
        print(f"{'='*60}")

        details = client.extract_bewerbung_details(text, firma)
        position = details.get("position", "Mitarbeiter")
        ansprechpartner = details.get("ansprechpartner", "Sehr geehrte Damen und Herren")
        quelle = details.get("quelle", "eure Website")
        print(f"Position: {position}")

        body = client.generate_anschreiben(
            cv_text=cv,
            stellenanzeige_text=text,
            firma_name=firma,
            position=position,
            ansprechpartner=ansprechpartner,
            quelle=quelle,
            zeugnis_text=None,
            bewerber_vorname=profile["vorname"],
            bewerber_name=profile["full_name"],
            user_skills=None,
            tonalitaet="modern",
            details=details,
        )

        body_before = body
        body = validator.fix_gray_zone_claims(text=body, cv_text=cv)
        filtered = body != body_before
        if filtered:
            print("[FILTER] Gray-zone sentences removed!")

        validation = validator.validate(text=body, cv_text=cv)
        found_forbidden = [p for p in FORBIDDEN_PHRASES if p.lower() in body.lower()]

        print(f"\n--- OUTPUT ({len(body.split())} words) ---")
        print(body)
        print("\n--- VALIDATION ---")
        print(f"Valid: {validation.is_valid} | Warnings: {validation.warnings}")
        if found_forbidden:
            print(f"FORBIDDEN: {found_forbidden}")

        gray_phrases = [
            "konzepte kenne",
            "konzepte sind mir",
            "konzepte versteh",
            "aus der praxis vertraut",
            "aus der praxis bekannt",
            "ist mir vertraut",
            "ist mir bekannt",
            "ist mir nicht fremd",
            "sind mir vertraut",
            "sind mir bekannt",
            "sind mir nicht fremd",
            "grundlagen kenne",
            "grundlagen versteh",
            "erste erfahrung",
            "erste berührungspunkte",
            "in kleinen projekten",
            "in kleineren projekten",
        ]
        body_lower = body.lower()
        gray_found = [p for p in gray_phrases if p in body_lower]

        sentences = re.split(r"[.!?]\s+", body)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        ich = sum(1 for s in sentences if s.startswith("Ich "))
        ich_ratio = ich / len(sentences) if sentences else 0

        results.append(
            {
                "cv": profile["name"],
                "posting_id": posting_id,
                "firma": firma,
                "label": label,
                "word_count": len(body.split()),
                "forbidden": found_forbidden,
                "hallucination_warns": [w for w in validation.warnings if "erfundene" in w],
                "gray_found": gray_found,
                "filtered": filtered,
                "ich_ratio": f"{ich}/{len(sentences)} = {ich_ratio:.0%}",
                "valid": validation.is_valid,
            }
        )

# === FINAL SUMMARY ===
print(f"\n\n{'='*70}")
print("GESAMTÜBERSICHT — 4 CVs × 3 Stellenanzeigen = 12 Tests")
print(f"{'='*70}")

print(f"\n{'CV':<25} {'Stelle':<35} {'Wörter':>6} {'Verboten':>8} {'GrayZone':>10} {'Filter':>7} {'Ich%':>10}")
print("-" * 101)
for r in results:
    forbidden = "YES" if r["forbidden"] else "-"
    gray = ", ".join(r["gray_found"][:2]) if r["gray_found"] else "-"
    filt = "YES" if r["filtered"] else "-"
    print(
        f"{r['cv']:<25} {r['label'][:33]:<35} {r['word_count']:>6} {forbidden:>8} {gray:>10} {filt:>7} {r['ich_ratio']:>10}"
    )

print("\n## Statistik:")
print(f"  Verbotene Phrasen: {sum(1 for r in results if r['forbidden'])}/12")
print(f"  Gray-Zone Filter aktiv: {sum(1 for r in results if r['filtered'])}/12")
print(f"  Gray-Zone Reste: {sum(1 for r in results if r['gray_found'])}/12")
print(f"  Halluzination Warnings: {sum(1 for r in results if r['hallucination_warns'])}/12")
print(f"  Alle valide: {sum(1 for r in results if r['valid'])}/12")
