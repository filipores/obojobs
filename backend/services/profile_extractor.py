"""
Profile Extractor Service - Extracts personal profile data from CV text using Claude API.
"""

import json
import logging
import time

from anthropic import Anthropic

from config import config

logger = logging.getLogger(__name__)


class ProfileExtractor:
    """Service to extract personal contact/profile data from CV documents using Claude API."""

    PROFILE_FIELDS = ["full_name", "phone", "email", "address", "city", "postal_code", "website"]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def extract_profile_from_cv(self, cv_text: str, retry_count: int = 3) -> dict:
        """
        Extract personal profile data from CV text using Claude API.

        Args:
            cv_text: The text content of the CV
            retry_count: Number of retries on failure

        Returns:
            Dict with keys: full_name, phone, email, address, city, postal_code, website.
            Values are strings or None if not found.
        """
        prompt = self._create_extraction_prompt(cv_text)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                return self._parse_profile_response(response_text)

            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning("Profil-Extraktion fehlgeschlagen (Versuch %s/%s): %s", attempt + 1, retry_count, e)
                    time.sleep(2)
                else:
                    logger.error("Profil-Extraktion fehlgeschlagen nach %s Versuchen: %s", retry_count, e)
                    return dict.fromkeys(self.PROFILE_FIELDS)

    def _create_extraction_prompt(self, cv_text: str) -> str:
        """Create the prompt for profile data extraction."""
        return f"""Analysiere diesen Lebenslauf und extrahiere die persönlichen Kontaktdaten.

LEBENSLAUF:
{cv_text[:4000]}

Extrahiere folgende Felder:
1. full_name: Vollständiger Name (Vor- und Nachname)
2. phone: Telefonnummer
3. email: E-Mail-Adresse
4. address: Straße und Hausnummer
5. city: Stadt/Ort
6. postal_code: Postleitzahl
7. website: Website oder LinkedIn-URL

WICHTIG: Antworte NUR mit einem JSON-Objekt. Keine anderen Texte.
Setze null für Felder, die nicht im Lebenslauf gefunden werden.

Beispiel-Antwort:
{{"full_name": "Max Mustermann", "phone": "+49 123 456789", "email": "max@example.com", "address": "Musterstraße 1", "city": "München", "postal_code": "80331", "website": "https://linkedin.com/in/maxmustermann"}}

Extrahiere jetzt die Profildaten als JSON-Objekt:"""

    def _parse_profile_response(self, response_text: str) -> dict:
        """Parse the Claude response into a profile dictionary."""
        text = response_text.strip()

        # Find JSON object bounds
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx == -1 or end_idx == -1:
            logger.warning("Keine JSON-Struktur in der Profil-Antwort gefunden")
            return dict.fromkeys(self.PROFILE_FIELDS)

        json_text = text[start_idx : end_idx + 1]

        try:
            data = json.loads(json_text)

            # Build result with only expected fields, normalizing values
            result = {}
            for field in self.PROFILE_FIELDS:
                value = data.get(field)
                if isinstance(value, str):
                    value = value.strip()
                    if not value:
                        value = None
                else:
                    value = None
                result[field] = value

            return result

        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error bei Profil-Extraktion: %s", e)
            return dict.fromkeys(self.PROFILE_FIELDS)
