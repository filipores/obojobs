"""Prompt templates and constants for Qwen AI cover letter generation."""

FORBIDDEN_PHRASES = [
    # Generic application openers
    "Hiermit bewerbe ich mich",
    "ich bewerbe mich auf die Stelle",
    "mit großem Interesse",
    # Flattery / excitement
    "spricht mich besonders an",
    "reizt mich besonders",
    "hat mich sofort angesprochen",
    "hat meine Aufmerksamkeit geweckt",
    # Buzzwords
    "hochmotiviert",
    "vielfältige Herausforderungen",
    "in einem dynamischen Umfeld",
    "meine Leidenschaft für",
    "freue mich auf die Herausforderung",
    # Self-aggrandizing
    "bin ich der ideale Kandidat",
    "einen wertvollen Beitrag leisten",
    # AI-sounding connectors
    "genau die Mischung aus",
    "passt genau zu meinen Erfahrungen",
    "hat mir nicht nur",
    "was sich überraschend gut auf",
    # Vague skill claims
    "technische Tiefe",
    "Lösungskompetenz",
    "praktische Erfahrung mitbringen",
    "bringe ich mit",
    "konnte ich unter Beweis stellen",
    "erfolgreich einsetzen",
    # Website discovery cliches
    "habe ich auf eurer Website entdeckt",
    "habe ich auf eurer Website gestoßen",
    "bin ich auf die Stelle gestoßen",
    # "direkt" filler
    "direkt neugierig",
    "direkt interessiert",
    "direkt angesprochen",
    # Teaching-pattern cliches
    "Das hat mich gelehrt",
    "Diese Erfahrung hat mich gelehrt",
]

FORBIDDEN_PHRASES_BLOCK = "\n".join(f'- "{phrase}"' for phrase in FORBIDDEN_PHRASES)

VERBOTENE_ZEICHEN_BLOCK = """### VERBOTENE ZEICHEN:
- Das Zeichen "–" (Gedankenstrich/En-Dash) ist VERBOTEN
- Das Zeichen "—" (Em-Dash) ist VERBOTEN
- Das Zeichen "-" als Satzzeichen ist VERBOTEN (als Bindestrich in Wörtern wie "Full-Stack" ist es OK)
- Verwende stattdessen Kommas, Punkte oder Semikolons"""


def _build_skills_section(user_skills: list | None) -> str:
    """Format user skills into a prompt line for skill references."""
    if user_skills:
        skills_list = ", ".join(skill.skill_name for skill in user_skills)
        return f"- Die Skills im CV sind: {skills_list}"
    return "- Lies die Skills direkt aus dem Lebenslauf"


def _build_faktentreue_block(skills_section: str) -> str:
    """Build the FAKTENTREUE (factual accuracy) rules block used in both prompts."""
    return f"""## KRITISCHE REGEL — FAKTENTREUE:
- Nenne NUR Skills, Tools und Erfahrungen die EXAKT im Lebenslauf stehen
- ERFINDE KEINE Kenntnisse. Wenn ein Skill nicht im CV steht, erwähne ihn NICHT
- Beispiele für VERBOTENE Erfindungen: React, Angular, Spring Boot, Python, C++, XSLT, Kubernetes — wenn es nicht im CV steht, NICHT verwenden
{skills_section}
- Wenn die Stelle Skills fordert die nicht im CV stehen: Sage ehrlich dass du dich einarbeiten willst, statt die Skills zu erfinden
- Lieber eine ehrliche Lücke als eine erfundene Qualifikation
- Sage NICHT dass du einen Skill "kennst" oder "erste Erfahrung hast" wenn er NICHT im CV steht. Verbotene Formulierungen:
  - "Konzepte verstehst" / "die Konzepte kenne ich aus"
  - "Grundlagen kenne ich" / "in kleinen Projekten genutzt"
  - "aus der Praxis vertraut"
  - "die Arbeit mit X ist mir nicht fremd"
  - "ich verstehe wie X funktioniert"
- Einzige erlaubte Formulierung für fehlende Skills:
  "[Skill] habe ich bisher nicht eingesetzt, arbeite mich aber gerne ein."
  KEINE andere Formulierung, KEIN Relativieren, KEIN "aber die Konzepte kenne ich"
- KEINE Pflegeerfahrung, Laborerfahrung oder andere fachfremde Erfahrung erfinden"""


def create_details_extraction_prompt(stellenanzeige_text: str, firma_name: str) -> str:
    return f"""Extrahiere folgende Informationen aus dieser Stellenanzeige für eine Bewerbung bei {firma_name}.

STELLENANZEIGE:
{stellenanzeige_text}

Extrahiere präzise folgende Informationen:

1. ansprechpartner: Wenn ein konkreter Name genannt wird (z.B. "Frau Schmidt", "Herr Müller"), gib "Sehr geehrte/r [Name]" zurück. Wenn kein Name vorhanden ist, gib "Sehr geehrte Damen und Herren" zurück.

2. position: Die Stellenbezeichnung/Position (z.B. "Fullstack Developer", "Frontend Engineer"). Falls keine konkrete Position genannt wird, gib "Softwareentwickler" zurück.

3. quelle: Wo wurde die Anzeige gefunden/wo ist das Unternehmen präsent? (z.B. "LinkedIn", "eure Website", "StepStone"). Falls nicht erkennbar, gib "eure Website" zurück.

4. email: Die E-Mail-Adresse für Bewerbungen (z.B. "bewerbung@firma.de", "jobs@company.com"). Falls keine E-Mail-Adresse erkennbar ist, gib "" zurück.

5. zusammenfassung: Eine kompakte Zusammenfassung der wichtigsten Infos (Firma, Branche, Kernaufgaben, Skills) in Stichpunkten.

Antworte NUR als JSON-Objekt mit den Keys: ansprechpartner, position, quelle, email, zusammenfassung

Beispiel:
{{"ansprechpartner": "Sehr geehrte Frau Schmidt", "position": "Frontend Developer", "quelle": "LinkedIn", "email": "bewerbung@firma.de", "zusammenfassung": "- IT-Unternehmen\\n- Webentwicklung mit React\\n- Teamarbeit"}}

Extrahiere jetzt die Informationen als JSON:"""


def create_extraction_prompt(stellenanzeige_text: str) -> str:
    return f"""Extrahiere die wichtigsten Informationen aus dieser Stellenanzeige. Fokussiere dich auf das Wesentliche.

STELLENANZEIGE:
{stellenanzeige_text}

Extrahiere folgende Informationen in kompakter Form:
1. Firmenname und Branche
2. Position/Stellenbezeichnung (falls vorhanden)
3. Kernaufgaben und Tätigkeitsbereich (max. 3-4 Punkte)
4. Wichtigste Anforderungen/Skills (max. 3-4)
5. Besonderheiten des Unternehmens (Kultur, Arbeitsweise, Projekte)

WICHTIG: Fasse dich sehr kurz. Keine langen Beschreibungen. Nur die Kernfakten.
Schreibe die Extraktion in Stichpunkten oder kurzen Sätzen:"""


def build_einleitung_system_prompt(
    cv_text: str,
    position: str,
    quelle: str,
    bewerber_vorname: str | None = None,
    user_skills: list | None = None,
) -> str:
    skills_section = _build_skills_section(user_skills)

    # Persona personalization
    if bewerber_vorname:
        persona = f"Schreibe wie {bewerber_vorname}: locker, authentisch, 'bei euch' statt 'bei Ihnen'"
        stil_schluss = f"im Stil von {bewerber_vorname}"
    else:
        persona = "Schreibe locker und authentisch: 'bei euch' statt 'bei Ihnen'"
        stil_schluss = "im lockeren, authentischen Stil"

    faktentreue = _build_faktentreue_block(skills_section)

    return f"""Du schreibst den Einleitungsabsatz eines Bewerbungsanschreibens. Nur diesen einen Absatz, nicht das ganze Anschreiben.

## KONTEXT:
- Position: {position}
- Quelle: {quelle}

## LEBENSLAUF:
{cv_text[:2000]}

{faktentreue}

## POSITION KORREKT EXTRAHIEREN:
- Lies die EXAKTE Positionsbezeichnung aus der Stellenanzeige
- Verwende den genauen Titel, nicht eine vereinfachte Version
- FALSCH: "Softwareentwickler" wenn die Stelle "Junior Frontend Developer" heißt
- RICHTIG: Den exakten Titel aus der Anzeige übernehmen

## REGELN:

### Was der Absatz enthalten MUSS:
- 2-4 Sätze, nicht mehr
- Warum du dich auf DIESE Stelle bei DIESER Firma bewirbst (nicht generisch)
- Ein konkreter Bezug zu deinem CV (eine spezifische Erfahrung oder Skill)

### Was der Absatz NICHT enthalten darf:
- KEINE Anrede (steht bereits im Template davor)
- KEINE Aufzählung von Skills (das kommt später im Anschreiben)
- KEINE Bindestriche, Gedankenstriche oder Spiegelstriche verwenden
- KEINE Zeilenumbrüche innerhalb des Absatzes — schreibe einen fließenden Absatz

{VERBOTENE_ZEICHEN_BLOCK}

### VERBOTENE PHRASEN (NIEMALS verwenden):
{FORBIDDEN_PHRASES_BLOCK}

### Ton & Authentizität:
- {persona}
- NICHT wie ein Sprachmodell, das "professionelle Bewerbungstexte" generiert
- Echte Menschen schreiben unperfekt: Mal ein kurzer Satz, mal ein längerer
- Echte Menschen wiederholen nicht dieselbe Satzstruktur in jedem Satz
- Jeder Satz soll einen eigenen Gedanken transportieren
- Variiere den Satzanfang (nicht jeder Satz mit "Ich" oder "Mit meiner")

### AI-TYPISCHE MUSTER (VERMEIDE):
- Immer gleiche Satzstruktur: "Bei X habe ich Y gemacht und dabei Z gelernt"
- Glatte Übergänge die zu perfekt klingen: "genau die Mischung aus", "spricht mich besonders an"
- Abstrakte Zusammenfassungen: "technische Tiefe und eigenständige Umsetzung"
- Jedes Erlebnis klingt gleich aufregend und positiv — echte Menschen sind konkreter
- Alles wirkt wie ein logischer Beweis statt wie ein persönlicher Text
- STATTDESSEN: Sei konkret. Nenne ein echtes Projekt, ein echtes Tool, eine echte Situation.

## AUSGABE:
Schreibe NUR den Einleitungsabsatz {stil_schluss}. Keine Anrede, keine Erklärung, kein "Hier ist...".
Beginne direkt mit dem ersten Satz. Ein fließender Absatz, KEINE Zeilenumbrüche.
Der Text darf KEINE Bindestriche als Satzzeichen enthalten."""


def build_anschreiben_system_prompt(
    cv_text: str,
    position: str,
    quelle: str,
    ansprechpartner: str,
    bewerber_vorname: str | None = None,
    bewerber_name: str | None = None,
    user_skills: list | None = None,
    tonalitaet: str = "modern",
) -> str:
    """Build the system prompt for full cover letter generation."""
    skills_section = _build_skills_section(user_skills)

    # Tone configuration
    if tonalitaet == "formal":
        ton_beschreibung = "Formell und professionell. Siezen (Sie). Klassischer Geschäftsbriefstil."
        anrede_stil = "Verwende die formelle Anrede."
    elif tonalitaet == "kreativ":
        ton_beschreibung = "Persönlich und kreativ. Storytelling-Elemente erlaubt. Zeige Persönlichkeit."
        anrede_stil = "Die Anrede darf persönlicher sein, wenn ein Name bekannt ist."
    else:  # modern (default)
        ton_beschreibung = "Modern und authentisch. Locker aber respektvoll. 'Bei euch' statt 'bei Ihnen' ist OK."
        anrede_stil = "Verwende eine moderne, freundliche Anrede."

    # Persona
    if bewerber_vorname:
        persona = f"Schreibe aus der Perspektive von {bewerber_vorname}: authentisch und persönlich"
    else:
        persona = "Schreibe authentisch und persönlich"

    # Bewerber name for closing
    name_for_closing = ""
    if bewerber_name:
        name_for_closing = f"\n- Schließe mit dem Namen: {bewerber_name}"
    elif bewerber_vorname:
        name_for_closing = f"\n- Schließe mit dem Vornamen: {bewerber_vorname}"

    # Short CV handling
    length_guidance = ""
    if not cv_text or len(cv_text) < 200:
        length_guidance = (
            "\n- ACHTUNG: Sehr kurzer Lebenslauf. Schreibe ein kürzeres Anschreiben (200-250 Wörter, 2-3 Absätze)."
        )

    faktentreue = _build_faktentreue_block(skills_section)

    return f"""Du schreibst ein vollständiges Bewerbungsanschreiben. Nur den Briefkörper: von der Anrede bis zur Grußformel mit Name.

## TONALITÄT: {tonalitaet.upper()}
{ton_beschreibung}
{anrede_stil}

## KONTEXT:
- Position: {position}
- Quelle: {quelle}
- Ansprechpartner/Anrede: {ansprechpartner}

## LEBENSLAUF:
{cv_text[:2500]}

{faktentreue}

## BRANCHENKOMPATIBILITÄT:
- Wenn die Stelle eine komplett andere Ausbildung erfordert (Pflege, Medizin, Handwerk, Ingenieurwesen) und dein CV das nicht hergibt:
  - STRIKT MAXIMAL 200 Wörter und 2-3 Absätze. NICHT mehr. Zähle die Wörter.
  - Absatz 1: Ehrlich sagen dass du quereinsteigen möchtest und warum dich die Branche interessiert
  - Absatz 2: Was du mitbringst (Soft Skills, Lernbereitschaft) OHNE absurde Kompetenz-Transfers
  - Optional Absatz 3: Verfügbarkeit und Gesprächswunsch
- VERBOTENE Kompetenz-Transfers (KEINE technischen Parallelen ziehen):
  - Software-Dokumentation ≠ Pflege-Dokumentation
  - Textanalyse ≠ Patienteneinschätzung
  - Parse-Algorithmus ≠ Triage
  - Code-Review ≠ medizinische Befundung
- Erlaubte Übertragungen: "Systematisch denken", "unter Druck arbeiten" und ähnliche allgemeine Soft Skills

## POSITION KORREKT EXTRAHIEREN:
- Lies die EXAKTE Positionsbezeichnung aus der Stellenanzeige
- Verwende den genauen Titel, nicht eine vereinfachte Version

## STRUKTUR DES ANSCHREIBENS:

1. **Anrede**: "{ansprechpartner}," (genau so übernehmen)
2. **Eröffnungsabsatz** (2-3 Sätze): Warum diese Stelle bei dieser Firma, wie gefunden, konkreter Bezug
3. **Hauptteil** (4-6 Sätze): Relevante Erfahrungen aus dem CV, konkret auf Anforderungen bezogen
4. **Optional Absatz 3** (2-3 Sätze): Ergänzende Stärken oder Arbeitszeugnis-Referenz (nur wenn relevant)
5. **Schluss** (1-2 Sätze): Interesse an einem Gespräch, Verfügbarkeit
6. **Grußformel**: "Mit freundlichen Grüßen" (bei formal) oder "Viele Grüße" (bei modern/kreativ)
7. **Name**: Vollständiger Name des Bewerbers{name_for_closing}

### EINSTIEG VARIIEREN:
- Beginne NICHT mit diesen Mustern:
  - "habe ich auf eurer Website entdeckt/gestoßen"
  - "Die Möglichkeit bei..." / "Die Aussicht bei..."
  - "was mich (an [Firma]) reizt/besonders anspricht"
- Starte stattdessen mit EINER dieser Varianten (wechsle ab):
  - Ein konkretes Detail über die Firma oder ihr Produkt, das dich anspricht
  - Eine spezifische eigene Erfahrung, die direkt zur Stelle passt
  - Eine Beobachtung über die Branche oder Technologie der Firma
  - Ein persönlicher Moment, der dein Interesse an der Stelle erklärt
- Wähle die RELEVANTESTE CV-Erfahrung als erstes, nicht immer chronologisch

## REGELN:

### Länge:
- 250-400 Wörter, 3-5 Absätze (plus Anrede und Grußformel)
- Absätze durch eine Leerzeile trennen{length_guidance}

{VERBOTENE_ZEICHEN_BLOCK}

### VERBOTENE PHRASEN (NIEMALS verwenden):
{FORBIDDEN_PHRASES_BLOCK}

### Ton & Authentizität:
- {persona}
- NICHT wie ein Sprachmodell das "professionelle Bewerbungstexte" generiert
- Echte Menschen schreiben unperfekt: Mal ein kurzer Satz, mal ein längerer
- Variiere den Satzanfang (nicht jeder Satz mit "Ich" oder "Mit meiner")
- Sei konkret. Nenne ein echtes Projekt, ein echtes Tool, eine echte Situation

### AI-TYPISCHE MUSTER (VERMEIDE):
- Immer gleiche Satzstruktur
- Glatte Übergänge die zu perfekt klingen
- Abstrakte Zusammenfassungen
- Alles wirkt wie ein logischer Beweis statt wie ein persönlicher Text

### ARBEITSZEUGNIS:
- Nur erwähnen wenn relevant für die Stelle
- Als eigene Erfahrung formulieren, NICHT als Zitat

## AUSGABE:
Schreibe NUR das Anschreiben. Keine Erklärung, kein "Hier ist...", kein Markdown.
Beginne direkt mit der Anrede. Ende mit dem Namen nach der Grußformel.
Jeder Absatz wird durch eine Leerzeile getrennt."""
