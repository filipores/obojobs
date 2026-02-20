"""Branchenspezifische Prompt-Regeln für Anschreiben-Generierung.

Jede Branche hat eigene Tonalität, Hook-Strategie, Body-Struktur und No-Gos.
KMU vs. Konzern wird als Overlay auf die Basisregeln angewendet.
"""

INDUSTRY_RULES = {
    "it_software": {
        "label": "IT / Software-Entwicklung",
        "base_rules": {
            "tone": "Pragmatisch, faktenbasiert, lösungsorientiert. Keine emotionalen Füllwörter.",
            "hook": "Einstieg über Tech-Stack, IT-Architektur oder aktuellen Makro-Trend (Cloud-nativ, MLOps, AI-Governance).",
            "body": (
                "- Max. 3 Hard Skills mit höchstem Matching zur Stellenanzeige + messbare Ergebnisse verknüpfen\n"
                "- Architektur-Entscheidungen begründen, nicht Lebenslauf nacherzählen\n"
                "- Soft Skills nur durch konkrete Projektsituationen belegen (agile Methodik, Code Reviews, Teamführung)\n"
                "- Zukunftstechnologien im Kontext nennen, wenn im CV vorhanden"
            ),
            "avoid": (
                "- Programmiersprachen-Listen ohne Architektur-Kontext\n"
                "- Nur Hard Skills ohne kommunikative Fähigkeiten\n"
                "- CV nacherzählen statt Architektur-Entscheidungen begründen"
            ),
        },
        "size_rules": {
            "kmu": "KMU/Startup: Hands-on, Full-Stack-Denkweise betonen, interdisziplinäre Zusammenarbeit, direkter Business-Impact.",
            "konzern": "Konzern: Skalierbarkeit, tiefe Spezialisierung, Governance-Verständnis, verteilte internationale Teams.",
        },
    },
    "consulting": {
        "label": "Consulting / Unternehmensberatung",
        "base_rules": {
            "tone": "Hochformell, analytisch exzellent, quantitativ. Minto-Prinzip: Hauptaussage zuerst, dann Evidenz.",
            "hook": "Networking-Kontakt im ersten Satz (wenn vorhanden) oder Publikation/Brancheninsight.",
            "body": (
                "- SPOT-Framework: Situation → Problem → Opportunity → Traction\n"
                "- Nur 2 relevanteste Karrierestationen mit harten Zahlen (€, %, Zeitersparnis)\n"
                "- Aktuelle Makro-Themen einbinden: ESG, CSRD-Regulatorik, GenAI (wenn zum Profil passend)\n"
                "- Motivation: Nie 'Consulting allgemein', sondern intellektuelle Problemlösung + Klientenwert"
            ),
            "avoid": (
                "- Vage Adjektive ohne Zahlen-Validierung ('sehr erfolgreich', 'innovativ')\n"
                "- Motivation für 'Consulting allgemein' statt spezifische Firma\n"
                "- Erfahrungen älter als 5 Jahre prominent nennen\n"
                "- Länger als 1 Seite (= Unfähigkeit zur Priorisierung)"
            ),
        },
        "size_rules": {
            "kmu": "Boutique-Beratung: Tiefes Industrie-Know-how, sofortige operative Einsetzbarkeit, Nischenwissen betonen.",
            "konzern": "MBB/Big4: Globale Perspektive, Top-Akademiker, Blue-Chip-Vorerfahrung, Skalierbarkeit.",
        },
    },
    "maschinenbau": {
        "label": "Maschinenbau / Ingenieurwesen",
        "base_rules": {
            "tone": "Höchste Präzision, absolut sachlich, fachlich untermauert. Kein Marketing-Sprech.",
            "hook": "Einstieg über Fachrichtung + technischer Bezug zu Produkten/Maschinen/Patenten des Zielunternehmens.",
            "body": (
                "- Exakte akademische Fachrichtung im ersten Absatz\n"
                "- Praktische Erfahrung prominent (Ausbildung, Werkstudent, Projektarbeit)\n"
                "- Industrie 4.0 im Kontext: Digitale Zwillinge, IIoT, Automatisierung (wenn im CV)\n"
                "- Interdisziplinäre Fähigkeiten (Mechatronik-Schnittstelle)\n"
                "- Soft Skills als 'Ingenieurs-Tugenden': analytisches Konfliktmanagement, Schnittstellenkompetenz"
            ),
            "avoid": (
                "- Leere 'innovative Lösungen' ohne Belege\n"
                "- Generischer Einstieg ohne Produkt-/Technologiebezug\n"
                "- Superlative ohne Beleg ('herausragend', 'einzigartig')"
            ),
        },
        "size_rules": {
            "kmu": "KMU: Realistische Gehaltserwartung, breites Einsatzspektrum, pragmatische Umsetzungsstärke.",
            "konzern": "Konzern: Tiefe Spezialisierung, Matrixorganisation-Erfahrung, internationale Projektfähigkeit.",
        },
    },
    "marketing": {
        "label": "Marketing / Kommunikation",
        "base_rules": {
            "tone": "Kreativ, fesselnd, story-getrieben. Starke aktive Verben, keine passive Sprache.",
            "hook": "Kreativer Hook mit Bezug auf Kampagne, Marke oder USP des Zielunternehmens.",
            "body": (
                "- Persönlichen USP klar definieren: analytisch (Performance, SEO, Data) ODER gestalterisch (Content, Copywriting)\n"
                "- Fachbegriffe natürlich einweben (Conversion-Rate, Traffic-Steigerung, Agentursteuerung)\n"
                "- Soft Skills nur mit messbaren Marketing-Ergebnissen verknüpft\n"
                "- Storytelling: Konkrete Kampagnen-Ergebnisse als Mini-Narrativ"
            ),
            "avoid": (
                "- Generische 'Leidenschaft für Marketing' ohne Substanz\n"
                "- Soft Skills ohne Kontext ('kreativ, kommunikativ, flexibel')\n"
                "- Lebenslauf nacherzählen ohne Schwerpunkt"
            ),
        },
        "size_rules": {
            "kmu": "Agentur: Out-of-the-Box-Denken, Pitch-Readiness, Stressresistenz, diverse Markenstimmen, mutiger Stil.",
            "konzern": "Konzern/Inhouse: Agentursteuerung, KPI-Reporting, Vertriebsschnittstelle, strategischer Markenaufbau.",
        },
    },
    "gesundheit": {
        "label": "Gesundheitswesen / Pflege",
        "base_rules": {
            "tone": "Empathisch, verbindlich, belastbar, praxisorientiert. Keine leeren Floskeln.",
            "hook": "Direkt: aktuelle Qualifikation + Motivation für DIESE spezifische Einrichtungsart.",
            "body": (
                "- Pflegealltag greifbar machen: konkrete klinische Handlungen (Deeskalation, Triage, Medikamentengabe)\n"
                "- Passung zur spezifischen Einrichtungsart (Maximalversorger vs. Altenheim vs. Hospiz)\n"
                "- Keine abstrakten Empathie-Floskeln, sondern erlebte Situationen"
            ),
            "avoid": (
                "- 'Ich helfe gerne Menschen' (leere Floskel, keine Profilschärfe)\n"
                "- Nicht zwischen Akut- und Langzeitpflege differenzieren\n"
                "- Abstrakte Empathie statt konkreter Pflegesituationen"
            ),
        },
        "size_rules": {
            "kmu": "Pflegeheim/Langzeit: Beziehungsgestaltung, Biografiearbeit, Demenzkompetenz, Palliativversorgung, Angehörigenarbeit.",
            "konzern": "Krankenhaus/Akut: Schnelle Akutversorgung, Medizintechnik, Triage-Denken, multiprofessionelles Team.",
        },
        "mandatory_fields": "MANDATORISCH am Ende nennen: Schichtbereitschaft, Startdatum, Kündigungsfrist, gewünschte Wochenstunden.",
    },
}

VALID_BRANCHES = set(INDUSTRY_RULES.keys())
VALID_SIZES = {"kmu", "konzern"}


def get_industry_prompt_block(
    branche: str | None,
    unternehmensgroesse: str | None = None,
) -> str:
    """Build a formatted prompt block for industry-specific rules.

    Returns an empty string if branche is None, unknown, or "andere".
    """
    if not branche or branche not in INDUSTRY_RULES:
        return ""

    rules = INDUSTRY_RULES[branche]
    base = rules["base_rules"]

    lines = [
        f"## INDUSTRY RULES ({rules['label']})",
        f"- TONE: {base['tone']}",
        f"- HOOK: {base['hook']}",
        "- BODY STRATEGY:",
        base["body"],
        "- AVOID:",
        base["avoid"],
    ]

    # Add size-specific overlay
    if unternehmensgroesse in VALID_SIZES:
        lines.append(f"- COMPANY SIZE: {rules['size_rules'][unternehmensgroesse]}")

    # Add mandatory fields if present
    if rules.get("mandatory_fields"):
        lines.append(f"- {rules['mandatory_fields']}")

    return "\n".join(lines)
