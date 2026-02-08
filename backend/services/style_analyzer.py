"""
Style Analyzer Service - Analyzes writing style from cover letters and generates a personalized template.
"""

import json
import logging
import time

from anthropic import Anthropic

from config import config

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Service to analyze writing style from existing cover letters and generate a matching template."""

    MAX_COVER_LETTERS = 5
    MAX_LETTER_LENGTH = 2000

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def analyze_and_generate(self, cover_letters: list[str], user_name: str = "", retry_count: int = 3) -> dict:
        """
        Analyze writing style from cover letters and generate a personalized template.

        Args:
            cover_letters: List of cover letter texts (max 5, each truncated to 2000 chars)
            user_name: Optional user name for personalization
            retry_count: Number of retries on failure

        Returns:
            Dict with keys: style_profile, template_content, template_name
        """
        # Limit and truncate cover letters
        letters = cover_letters[: self.MAX_COVER_LETTERS]
        letters = [letter[: self.MAX_LETTER_LENGTH] for letter in letters]

        # Phase 1: Analyze style
        style_profile = self._analyze_style(letters, retry_count)

        # Phase 2: Generate template based on style
        template_content, template_name = self._generate_template(style_profile, user_name, retry_count)

        return {
            "style_profile": style_profile,
            "template_content": template_content,
            "template_name": template_name,
        }

    def _analyze_style(self, letters: list[str], retry_count: int = 3) -> dict:
        """Phase 1: Analyze writing style from cover letters."""
        letters_text = ""
        for i, letter in enumerate(letters, 1):
            letters_text += f"\n--- Anschreiben {i} ---\n{letter}\n"

        prompt = f"""Analysiere den Schreibstil der folgenden Anschreiben und erstelle ein detailliertes Stilprofil.

ANSCHREIBEN:
{letters_text}

Erstelle ein Stilprofil mit folgenden Aspekten:
1. tonality: Gesamttonalität (z.B. "professionell-modern", "formal-klassisch", "persönlich-authentisch")
2. sentence_length: Durchschnittliche Satzlänge ("kurz", "mittel", "lang")
3. favorite_phrases: Liste von 3-5 typischen Formulierungen oder Redewendungen des Bewerbers
4. strengths: Liste von 2-3 besonderen Stärken im Schreibstil
5. structure: Beschreibung der typischen Struktur (z.B. "Direkter Einstieg, 3 Absätze, formaler Schluss")
6. vocabulary_level: Sprachliches Niveau ("einfach", "gehoben", "fachsprachlich")
7. personal_touch: Was den Stil einzigartig macht (1-2 Sätze)

WICHTIG: Antworte NUR mit einem JSON-Objekt. Keine anderen Texte.

Beispiel-Antwort:
{{"tonality": "professionell-modern", "sentence_length": "mittel", "favorite_phrases": ["mit großem Interesse", "meine Expertise"], "strengths": ["Klare Struktur", "Authentische Sprache"], "structure": "Persönlicher Einstieg, Kernkompetenzen, Motivation, formaler Schluss", "vocabulary_level": "gehoben", "personal_touch": "Verbindet fachliche Kompetenz geschickt mit persönlicher Motivation."}}

Analysiere jetzt den Schreibstil als JSON-Objekt:"""

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                return self._parse_json_object(
                    response_text,
                    fallback={
                        "tonality": "professionell",
                        "sentence_length": "mittel",
                        "favorite_phrases": [],
                        "strengths": [],
                        "structure": "Standard",
                        "vocabulary_level": "gehoben",
                        "personal_touch": "",
                    },
                )

            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning("Stilanalyse fehlgeschlagen (Versuch %s/%s): %s", attempt + 1, retry_count, e)
                    time.sleep(2)
                else:
                    logger.error("Stilanalyse fehlgeschlagen nach %s Versuchen: %s", retry_count, e)
                    return {
                        "tonality": "professionell",
                        "sentence_length": "mittel",
                        "favorite_phrases": [],
                        "strengths": [],
                        "structure": "Standard",
                        "vocabulary_level": "gehoben",
                        "personal_touch": "",
                    }

    def _generate_template(self, style_profile: dict, user_name: str = "", retry_count: int = 3) -> tuple[str, str]:
        """Phase 2: Generate a template matching the analyzed style."""
        name_hint = f" für {user_name}" if user_name else ""

        prompt = f"""Erstelle ein Anschreiben-Template basierend auf dem folgenden Schreibstil-Profil.

STILPROFIL:
- Tonalität: {style_profile.get("tonality", "professionell")}
- Satzlänge: {style_profile.get("sentence_length", "mittel")}
- Typische Formulierungen: {", ".join(style_profile.get("favorite_phrases", []))}
- Stärken: {", ".join(style_profile.get("strengths", []))}
- Struktur: {style_profile.get("structure", "Standard")}
- Sprachniveau: {style_profile.get("vocabulary_level", "gehoben")}
- Persönliche Note: {style_profile.get("personal_touch", "")}

AUFGABE:
Erstelle ein Anschreiben-Template{name_hint}, das exakt diesen Schreibstil widerspiegelt.

PFLICHT-PLATZHALTER (müssen alle vorkommen):
- {{{{ANSPRECHPARTNER}}}} - für die Anrede (z.B. "Sehr geehrte Frau Müller")
- {{{{FIRMA}}}} - für den Firmennamen
- {{{{POSITION}}}} - für die Stellenbezeichnung
- {{{{QUELLE}}}} - für die Quelle der Stellenanzeige (z.B. "auf LinkedIn")
- {{{{EINLEITUNG}}}} - für einen personalisierten Einleitungsabsatz (2-4 Sätze)

REGELN:
1. Das Template soll 200-300 Wörter lang sein
2. Verwende den gleichen Stil und die gleichen typischen Formulierungen
3. Alle 5 Platzhalter MÜSSEN im Template vorkommen
4. Gib NUR den Template-Text zurück, keine Erklärungen oder JSON

Generiere jetzt das Template:"""

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}],
                )

                template_content = response.content[0].text.strip()

                # Generate a meaningful template name
                tonality = style_profile.get("tonality", "Persönlich")
                template_name = f"Mein Stil ({tonality})"

                return template_content, template_name

            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        "Template-Generierung fehlgeschlagen (Versuch %s/%s): %s", attempt + 1, retry_count, e
                    )
                    time.sleep(2)
                else:
                    logger.error("Template-Generierung fehlgeschlagen nach %s Versuchen: %s", retry_count, e)
                    raise

    def _parse_json_object(self, response_text: str, fallback: dict) -> dict:
        """Parse a JSON object from Claude's response text."""
        text = response_text.strip()

        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx == -1 or end_idx == -1:
            logger.warning("Keine JSON-Struktur in der Stilanalyse-Antwort gefunden")
            return fallback

        json_text = text[start_idx : end_idx + 1]

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error bei Stilanalyse: %s", e)
            return fallback
