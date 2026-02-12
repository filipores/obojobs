"""Prompt templates and constants for Qwen AI cover letter generation."""

FORBIDDEN_PHRASES = [
    "genau die Mischung aus",
    "spricht mich besonders an",
    "reizt mich besonders",
    "hat mich sofort angesprochen",
    "hat meine Aufmerksamkeit geweckt",
    "mit großem Interesse",
    "Hiermit bewerbe ich mich",
    "hochmotiviert",
    "vielfältige Herausforderungen",
    "bin ich der ideale Kandidat",
    "freue mich auf die Herausforderung",
    "in einem dynamischen Umfeld",
    "meine Leidenschaft für",
    "passt genau zu meinen Erfahrungen",
    "technische Tiefe",
    "Lösungskompetenz",
    "praktische Erfahrung mitbringen",
    "bringe ich mit",
    "konnte ich unter Beweis stellen",
    "erfolgreich einsetzen",
    "ich bewerbe mich auf die Stelle",
]


def create_details_extraction_prompt(stellenanzeige_text: str, firma_name: str) -> str:
    return f"""Extrahiere folgende Informationen aus dieser Stellenanzeige für eine Bewerbung:

STELLENANZEIGE:
{stellenanzeige_text}

Extrahiere präzise folgende Informationen:

1. ANSPRECHPARTNER: Wenn ein konkreter Name genannt wird (z.B. "Frau Schmidt", "Herr Müller"), gib "Sehr geehrte/r [Name]" zurück. Wenn kein Name vorhanden ist, gib "Sehr geehrte Damen und Herren" zurück.

2. POSITION: Die Stellenbezeichnung/Position (z.B. "Fullstack Developer", "Frontend Engineer"). Falls keine konkrete Position genannt wird, gib "Softwareentwickler" zurück.

3. QUELLE: Wo wurde die Anzeige gefunden/wo ist das Unternehmen präsent? (z.B. "LinkedIn", "eure Website", "StepStone"). Falls nicht erkennbar, gib "eure Website" zurück.

4. EMAIL: Die E-Mail-Adresse für Bewerbungen (z.B. "bewerbung@firma.de", "jobs@company.com"). Falls keine E-Mail-Adresse erkennbar ist, gib "keine Angabe" zurück.

5. Danach: Schreibe eine kompakte Zusammenfassung der wichtigsten Infos (Firma, Branche, Kernaufgaben, Skills) in Stichpunkten.

WICHTIG: Formatiere deine Antwort genau so:

ANSPRECHPARTNER: [Anrede]
POSITION: [Position]
QUELLE: [Quelle]
EMAIL: [E-Mail oder "keine Angabe"]

[Kompakte Zusammenfassung in Stichpunkten]

Extrahiere jetzt die Informationen:"""


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
    # Skills section - dynamic based on user_skills
    if user_skills:
        skills_list = ", ".join(skill.skill_name for skill in user_skills)
        skills_section = f"- Die Skills im CV sind: {skills_list}"
    else:
        skills_section = "- Lies die Skills direkt aus dem Lebenslauf"

    # Persona personalization
    if bewerber_vorname:
        persona = f"Schreibe wie {bewerber_vorname}: locker, authentisch, 'bei euch' statt 'bei Ihnen'"
        stil_schluss = f"im Stil von {bewerber_vorname}"
    else:
        persona = "Schreibe locker und authentisch: 'bei euch' statt 'bei Ihnen'"
        stil_schluss = "im lockeren, authentischen Stil"

    return f"""Du schreibst den Einleitungsabsatz eines Bewerbungsanschreibens. Nur diesen einen Absatz, nicht das ganze Anschreiben.

## KONTEXT:
- Position: {position}
- Quelle: {quelle}

## LEBENSLAUF:
{cv_text[:2000]}

## KRITISCHE REGEL — FAKTENTREUE:
- Nenne NUR Skills, Tools und Erfahrungen die EXAKT im Lebenslauf stehen
- ERFINDE KEINE Kenntnisse. Wenn ein Skill nicht im CV steht, erwähne ihn NICHT
- Beispiele für VERBOTENE Erfindungen: React, Angular, Spring Boot, Python, C++, XSLT, Kubernetes — wenn es nicht im CV steht, NICHT verwenden
{skills_section}
- Wenn die Stelle Skills fordert die nicht im CV stehen: Sage ehrlich dass du dich einarbeiten willst, statt die Skills zu erfinden
- Lieber eine ehrliche Lücke als eine erfundene Qualifikation
- KEINE Pflegeerfahrung, Laborerfahrung oder andere fachfremde Erfahrung erfinden

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

### VERBOTENE ZEICHEN:
- Das Zeichen "–" (Gedankenstrich/En-Dash) ist VERBOTEN
- Das Zeichen "—" (Em-Dash) ist VERBOTEN
- Das Zeichen "-" als Satzzeichen ist VERBOTEN (als Bindestrich in Wörtern wie "Full-Stack" ist es OK)
- Verwende stattdessen Kommas, Punkte oder Semikolons

### VERBOTENE PHRASEN (NIEMALS verwenden):
- "Hiermit bewerbe ich mich" — das ist der langweiligste Einstieg überhaupt
- "mit großem Interesse"
- "hochmotiviert"
- "hat meine Aufmerksamkeit geweckt"
- "vielfältige Herausforderungen"
- "bin ich der ideale Kandidat"
- "freue mich auf die Herausforderung"
- "in einem dynamischen Umfeld"
- "meine Leidenschaft für"
- "hat mich sofort angesprochen"
- "genau die Mischung aus"
- "spricht mich besonders an"
- "reizt mich besonders"
- "passt genau zu meinen Erfahrungen"
- "technische Tiefe"
- "Lösungskompetenz"
- "praktische Erfahrung mitbringen"

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
    # Skills section
    if user_skills:
        skills_list = ", ".join(skill.skill_name for skill in user_skills)
        skills_section = f"- Die Skills im CV sind: {skills_list}"
    else:
        skills_section = "- Lies die Skills direkt aus dem Lebenslauf"

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

## KRITISCHE REGEL — FAKTENTREUE:
- Nenne NUR Skills, Tools und Erfahrungen die EXAKT im Lebenslauf stehen
- ERFINDE KEINE Kenntnisse. Wenn ein Skill nicht im CV steht, erwähne ihn NICHT
- Beispiele für VERBOTENE Erfindungen: React, Angular, Spring Boot, Python, C++, XSLT, Kubernetes — wenn es nicht im CV steht, NICHT verwenden
{skills_section}
- Wenn die Stelle Skills fordert die nicht im CV stehen: Sage ehrlich dass du dich einarbeiten willst, statt die Skills zu erfinden
- Lieber eine ehrliche Lücke als eine erfundene Qualifikation
- KEINE Pflegeerfahrung, Laborerfahrung oder andere fachfremde Erfahrung erfinden

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

## REGELN:

### Länge:
- 250-400 Wörter, 3-5 Absätze (plus Anrede und Grußformel)
- Absätze durch eine Leerzeile trennen{length_guidance}

### VERBOTENE ZEICHEN:
- Das Zeichen "–" (Gedankenstrich/En-Dash) ist VERBOTEN
- Das Zeichen "—" (Em-Dash) ist VERBOTEN
- Das Zeichen "-" als Satzzeichen ist VERBOTEN (als Bindestrich in Wörtern wie "Full-Stack" ist es OK)
- Verwende stattdessen Kommas, Punkte oder Semikolons

### VERBOTENE PHRASEN (NIEMALS verwenden):
- "Hiermit bewerbe ich mich"
- "mit großem Interesse"
- "hochmotiviert"
- "hat meine Aufmerksamkeit geweckt"
- "vielfältige Herausforderungen"
- "bin ich der ideale Kandidat"
- "freue mich auf die Herausforderung"
- "in einem dynamischen Umfeld"
- "meine Leidenschaft für"
- "hat mich sofort angesprochen"
- "genau die Mischung aus"
- "spricht mich besonders an"
- "reizt mich besonders"
- "passt genau zu meinen Erfahrungen"
- "technische Tiefe"
- "Lösungskompetenz"
- "praktische Erfahrung mitbringen"
- "bringe ich mit"
- "konnte ich unter Beweis stellen"
- "erfolgreich einsetzen"

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
