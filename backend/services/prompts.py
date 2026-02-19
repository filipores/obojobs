"""Prompt templates and constants for AI cover letter generation."""

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


def create_details_extraction_prompt(stellenanzeige_text: str, firma_name: str) -> str:
    return f"""Extrahiere folgende Informationen aus dieser Stellenanzeige für eine Bewerbung bei {firma_name}.

STELLENANZEIGE:
{stellenanzeige_text[:5000]}

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


def _build_persona(user_skills: list | None, position: str) -> str:
    """Derive a career-stage persona from skills and target position."""
    if user_skills and len(user_skills) >= 8:
        stage = "experienced professional"
    elif user_skills and len(user_skills) >= 4:
        stage = "mid-career professional"
    else:
        stage = "early-career professional"
    return f"Write like a real {stage} writing their application after work. NOT like an AI."


def build_anschreiben_system_prompt(
    cv_text: str,
    position: str,
    quelle: str,
    ansprechpartner: str,
    bewerber_vorname: str | None = None,
    bewerber_name: str | None = None,
    user_skills: list | None = None,
    tonalitaet: str = "modern",
    user_city: str | None = None,
) -> str:
    """Build the v3 system prompt for full cover letter generation.

    English instructions for precision; output stays German.
    ~40% shorter than v2 (~1,600 tokens vs ~2,700).
    """
    # Tone configuration
    if tonalitaet == "formal":
        tone_instruction = 'FORMAL: Use "Sie" throughout. Classic business letter style.'
    elif tonalitaet == "kreativ":
        tone_instruction = "CREATIVE: Show personality. Storytelling elements welcome. Warm and personal."
    else:  # modern (default)
        tone_instruction = 'MODERN: Relaxed but respectful. "bei euch" instead of "bei Ihnen" is OK.'

    persona = _build_persona(user_skills, position)

    # Sender line for structure section
    sender_parts = []
    if bewerber_vorname and bewerber_name and bewerber_name != bewerber_vorname:
        sender_parts.append(bewerber_name)
    elif bewerber_vorname:
        sender_parts.append(bewerber_vorname)
    if user_city:
        sender_parts.append(user_city)
    sender_line = " | ".join(sender_parts) if sender_parts else ""

    # Closing name
    closing_name = bewerber_name or bewerber_vorname or ""

    # Short CV handling
    length_note = ""
    if not cv_text or len(cv_text) < 200:
        length_note = "\n- WARNING: Very short CV. Write a shorter letter (200-250 words, 2-3 paragraphs)."

    # Skills list for factual accuracy
    if user_skills:
        skills_list = ", ".join(skill.skill_name for skill in user_skills)
        skills_reference = f"CV skills: {skills_list}"
    else:
        skills_reference = "Read skills directly from the CV below."

    # Top 10 forbidden phrases for in-prompt listing (full 45 stay in FORBIDDEN_PHRASES for post-processing)
    key_forbidden = [
        "Hiermit bewerbe ich mich",
        "mit großem Interesse",
        "hochmotiviert",
        "spricht mich besonders an",
        "hat mich sofort angesprochen",
        "bin ich der ideale Kandidat",
        "einen wertvollen Beitrag leisten",
        "genau die Mischung aus",
        "meine Leidenschaft für",
        "freue mich auf die Herausforderung",
    ]
    forbidden_block = "\n".join(f"- {p}" for p in key_forbidden)

    return f"""You write a German cover letter (Anschreiben). Body only: from greeting to closing with name.
ALL OUTPUT MUST BE IN GERMAN. These instructions are in English for precision.

## TONE
{tone_instruction}

## CONTEXT
- Position: {position}
- Source: {quelle}
- Greeting: {ansprechpartner}

## CV (LEBENSLAUF)
{cv_text[:2500]}

## FACTUAL ACCURACY (CRITICAL)
- ONLY mention skills, tools, and experiences that are EXACTLY in the CV above.
- NEVER invent qualifications. If a skill is not in the CV, do NOT mention it.
- {skills_reference}
- If the job requires skills not in the CV, honestly say you are willing to learn.
- ONLY allowed phrasing for missing skills: "[Skill] habe ich bisher nicht eingesetzt, arbeite mich aber gerne ein."
- NO hedging like "die Konzepte kenne ich" or "Grundlagen kenne ich" for skills NOT in the CV.

## STRUCTURE
1. Greeting: "{ansprechpartner}," (use exactly as given)
2. Opening (2-3 sentences): Why THIS job at THIS company. Concrete CV reference.
3. Main body (4-6 sentences): Relevant experience mapped to job requirements.
4. Closing (1-2 sentences): Interest in an interview, availability.
5. Sign-off: "Mit freundlichen Grüßen" (formal) or "Viele Grüße" (modern/creative)
6. Name: {closing_name}
{f"7. Sender line: {sender_line}" if sender_line else ""}

## OPENING VARIATION
Do NOT start with:
- "habe ich auf eurer Website entdeckt/gestoßen"
- "Die Möglichkeit bei..." / "Die Aussicht bei..."
- "was mich reizt/besonders anspricht"
Instead pick ONE: a company detail, a matching CV experience, a tech observation, or a personal moment.

## RULES
- 250-400 words, 3-5 paragraphs (plus greeting and sign-off){length_note}
- Separate paragraphs with a blank line
- Use the EXACT job title from the posting, not a simplified version
- FORBIDDEN characters: "–" (en-dash), "—" (em-dash), "-" as punctuation (OK in compound words like "Full-Stack")

### FORBIDDEN PHRASES (never use these or similar):
{forbidden_block}

## AUTHENTICITY
- {persona}
- Vary sentence length. Mix short and long. Not every sentence starts with "Ich".
- Be specific: name a real project, tool, or situation from the CV.
- No smooth AI transitions. No abstract summaries. Write like a human, not a language model.

## OUTPUT
Write ONLY the cover letter in German. No explanation, no "Hier ist...", no markdown.
Start with the greeting. End with the name after the sign-off.
Separate paragraphs with blank lines."""
