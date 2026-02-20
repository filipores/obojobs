"""Prompt templates and constants for AI cover letter generation."""

from services.industry_rules import get_industry_prompt_block

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
    # AI connection patterns
    "die Verbindung von",
    "die Verbindung aus",
]


def create_details_extraction_prompt(stellenanzeige_text: str, firma_name: str) -> str:
    return f"""Extrahiere folgende Informationen aus dieser Stellenanzeige für eine Bewerbung bei {firma_name}.

STELLENANZEIGE:
{stellenanzeige_text[:5000]}

Extrahiere präzise folgende Informationen:

1. ansprechpartner: Wenn ein konkreter Name genannt wird (z.B. "Frau Schmidt", "Herr Müller"), gib "Sehr geehrte/r [Name]" zurück. Wenn kein Name vorhanden ist, gib "Sehr geehrte Damen und Herren" zurück.

2. position: Die Stellenbezeichnung/Position (z.B. "Fullstack Developer", "Frontend Engineer"). Falls keine konkrete Position genannt wird, gib "Softwareentwickler" zurück.

3. quelle: Wo wurde die Anzeige gefunden/wo ist das Unternehmen präsent? (z.B. "LinkedIn", "StepStone", "Indeed"). Falls nicht erkennbar, gib "Manuelle Eingabe" zurück.

4. email: Die E-Mail-Adresse für Bewerbungen (z.B. "bewerbung@firma.de", "jobs@company.com"). Falls keine E-Mail-Adresse erkennbar ist, gib "" zurück.

5. zusammenfassung: Eine kompakte Zusammenfassung der wichtigsten Infos (Firma, Branche, Kernaufgaben, Skills) in Stichpunkten.

6. branche: Die Branche des Unternehmens. Wähle EINEN der folgenden Werte: "it_software", "consulting", "maschinenbau", "marketing", "gesundheit", "andere". Falls unklar, gib "andere" zurück.

7. unternehmensgroesse: Die Größe des Unternehmens. Wähle EINEN der folgenden Werte: "kmu" (unter ~500 Mitarbeiter, Startup, Mittelstand, Agentur, Pflegeheim), "konzern" (über ~500 Mitarbeiter, DAX, MBB, Big4, Krankenhaus-Kette), "unbekannt". Falls unklar, gib "unbekannt" zurück.

Antworte NUR als JSON-Objekt mit den Keys: ansprechpartner, position, quelle, email, zusammenfassung, branche, unternehmensgroesse

Beispiel:
{{"ansprechpartner": "Sehr geehrte Frau Schmidt", "position": "Frontend Developer", "quelle": "LinkedIn", "email": "bewerbung@firma.de", "zusammenfassung": "- IT-Unternehmen\\n- Webentwicklung mit React\\n- Teamarbeit", "branche": "it_software", "unternehmensgroesse": "kmu"}}

Extrahiere jetzt die Informationen als JSON:"""


def create_extraction_prompt(stellenanzeige_text: str) -> str:
    return f"""Analyze this German job posting in depth. Go beyond the surface. Output in German.

JOB POSTING:
{stellenanzeige_text}

Extract the following in compact form:

1. FACTS: Company name, industry, position (max 2 lines)

2. WHAT THEY REALLY NEED: What are the 2-3 most important requirements? Not the buzzword list — what actually matters most to them. Read between the lines.

3. PAIN POINTS: What problems or challenges are hinted at in the text? (e.g. "fast-growing team" = they urgently need people, "independent work" = little structure/onboarding, "modernization" = legacy code)

4. COMPANY CULTURE: What tone comes through? (startup vs. corporate, casual vs. formal, remote vs. on-site, flat vs. hierarchical). Back up with specific phrases from the posting.

5. CORE TASKS: The 3-4 most important responsibilities (not the full list, only what truly counts).

IMPORTANT: Keep it short. Bullet points or brief sentences. No long descriptions.
Be analytical, not descriptive. "They need someone who can X" not "The role involves X"."""


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
    branche: str | None = None,
    unternehmensgroesse: str | None = None,
) -> str:
    """Build the v4 system prompt for full cover letter generation.

    Based on kimi-lab v5 eval winner (3.66 weighted).
    Key improvements over v3: voice & tone at top, factual integrity with
    anti-inflation rules, personality check, flexible missing-skills handling.
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
        "spricht mich besonders an / hat mich sofort angesprochen",
        "bin ich der ideale Kandidat",
        "einen wertvollen Beitrag leisten",
        "genau die Mischung aus",
        "meine Leidenschaft für",
        "freue mich auf die Herausforderung",
        "die Verbindung von/aus",
    ]
    forbidden_block = "\n".join(f"- {p}" for p in key_forbidden)

    industry_block = get_industry_prompt_block(branche, unternehmensgroesse)
    industry_section = f"{industry_block}\n" if industry_block else ""

    # Sign-off based on tonalitaet
    if tonalitaet == "formal":
        sign_off_instruction = '"Mit freundlichen Grüßen"'
    else:
        sign_off_instruction = '"Viele Grüße"'

    return f"""You write a German cover letter (Anschreiben). Body only: from greeting to closing with name.
ALL OUTPUT MUST BE IN GERMAN. These instructions are in English for precision.

## VOICE & TONE
{tone_instruction}
- {persona}
- ACTIVE VOICE only. "Ich habe X entwickelt" — NOT "Mit Vue wurden X entwickelt". Every action needs a clear subject.
- Vary sentence length. Short punchy sentences next to longer ones. Not every sentence starts with "Ich".
- Sound like a real person, not like a prompt-following robot. If a sentence could appear in any random application, rewrite it with specifics.

{industry_section}## CONTEXT
- Position: {position}
- Source: {quelle}
- Greeting: {ansprechpartner}

## CV (LEBENSLAUF)
{cv_text[:2500]}

## FACTUAL INTEGRITY (CRITICAL)
Three rules. Zero exceptions.

1. **CV-only facts.** Every skill, tool, duration, qualification, and achievement you mention must come directly from the CV above. If you can't point to a specific line in the CV, don't write it.
2. **Exact durations.** Count actual months between start and end dates. "18 Monate" stays "18 Monate" or "anderthalb Jahre" — never round to "zwei Jahre". Approximate totals across ALL positions are OK ("drei Jahre" for 35 months total) but individual positions must be exact.
3. **No inflation.** Don't upgrade hobbies to jobs, startups to corporations, or interests to expertise. If the CV lists something under PERSÖNLICHES/Hobbies, it's a personal interest — not professional experience.

- {skills_reference}
- Cherry-pick only the 2-4 most RELEVANT skills/experiences for THIS specific job. Quality over quantity.
- Education note: Get universities, degrees, Nebenfächer, and completion status exactly right. Never mix subjects between universities.

## HANDLING MISSING SKILLS
- Combine ALL missing skills into ONE sentence. Reference a real career change or learning example from the CV to show adaptability.
- Maximum ONE such sentence per letter. Vary the phrasing naturally.
- For jobs requiring qualifications the applicant doesn't have (nursing, engineering degree, etc.): see OUT-OF-FIELD below.

## OUT-OF-FIELD JOBS
If the job requires a professional qualification the applicant does NOT have:
1. Acknowledge the career change directly in the opening.
2. Don't bridge unbridgeable gaps (software skills ≠ clinical care, database queries ≠ patient documentation).
3. Focus on genuinely transferable skills: structured thinking, communication, languages, self-organization.
4. Keep it SHORT (200-220 words). No irrelevant technical padding.

## STRUCTURE
1. Greeting: "{ansprechpartner}," (exactly as given)
2. Opening (2-3 sentences): Why THIS job at THIS company. One SPECIFIC company detail (product, market, technology).
3. Main body (5-8 sentences): 2-3 CV experiences mapped to job requirements. Name projects, tools, situations.
4. Closing (2-3 sentences): Interview interest, availability, forward-looking.
5. Sign-off: {sign_off_instruction}
6. Name: {closing_name}
{f"7. Sender line: {sender_line}" if sender_line else ""}

## LENGTH — HARD LIMITS
- Minimum 200 words. Maximum 300 words. Aim for 240.
- 3-4 paragraphs, 3-5 sentences each. No single-sentence paragraphs.
- If your draft exceeds 300 words, cut your weakest paragraph. No exceptions.{length_note}

## OPENING — BANNED PATTERNS
NEVER start with:
- "die Verbindung von/aus..."
- "habe ich auf eurer Website entdeckt/gestoßen"
- "Die Möglichkeit bei..." / "Die Aussicht bei..."
- "was mich reizt/besonders anspricht"
- "[Company] verbindet [X] mit [Y]"
- "[Company] steht für..."
- "Hiermit bewerbe ich mich..."

INSTEAD: Start with YOUR experience, a SPECIFIC company detail, a career-narrative statement, or the job requirement.

## FORBIDDEN PHRASES
{forbidden_block}

## FORMAT RULES
- Separate paragraphs with blank lines
- Use the EXACT job title from the posting
- FORBIDDEN: "–" (en-dash), "—" (em-dash), "-" as punctuation (OK in compound words)
- Proper greeting: "Sehr geehrte Frau Schmidt" / "Sehr geehrter Herr Müller". NEVER "Sehr geehrte/r".

## PERSONALITY CHECK (IMPORTANT — do this LAST)
After writing, re-read your letter and ask: "Does this sound like a confident person talking, or like a machine following instructions?" If the latter:
- Replace stiff constructions with natural speech
- Add one concrete, human detail (a location, a product you actually used, a situation)
- Make sure at least one sentence has genuine personality — something only THIS person would write
- Don't repeat the same evidence across paragraphs. Diversify from the CV.
- Each letter must feel unique to this company.

## SELF-CHECK (6 points — verify BEFORE outputting)
1. **WORD COUNT**: 200-300 words? If over 300, CUT.
2. **FACTS**: Every claim traceable to a CV line? No invented metrics, no role inflation, no skills not listed?
3. **DURATIONS**: All time periods match CV dates? No rounding up?
4. **OPENING**: Uses a banned pattern? → Rewrite.
5. **ACTIVE VOICE**: Any passive? → Rewrite.
6. **HUMAN**: Would a real person actually say this? If not → Rewrite.

## OUTPUT
Write ONLY the cover letter in German. No explanation, no "Hier ist...", no markdown.
Start with the greeting. End with the name after the sign-off.
Separate paragraphs with blank lines."""
