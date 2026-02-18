"""
Profile Extractor Service - Extracts personal profile data from CV text using Qwen API.
"""

import logging

from services.qwen_client import QwenAPIClient

logger = logging.getLogger(__name__)


class ProfileExtractor:
    """Service to extract personal contact/profile data from CV documents using Qwen API."""

    PROFILE_FIELDS = ["full_name", "phone", "email", "address", "city", "postal_code", "website"]

    def __init__(self):
        self.client = QwenAPIClient()

    def extract_profile_from_cv(self, cv_text: str) -> dict:
        """
        Extract personal profile data from CV text using Qwen API.

        Args:
            cv_text: The text content of the CV

        Returns:
            Dict with keys: full_name, phone, email, address, city, postal_code, website.
            Values are strings or None if not found.
        """
        prompt = self._create_extraction_prompt(cv_text)

        try:
            data = self.client._call_api_json_with_retry(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1,
                model=self.client.fast_model,
            )
            return self._normalize_profile(data)
        except Exception as e:
            logger.error("Profil-Extraktion fehlgeschlagen: %s", e)
            return dict.fromkeys(self.PROFILE_FIELDS)

    def _create_extraction_prompt(self, cv_text: str) -> str:
        """Create the prompt for profile data extraction."""
        return f"""Analysiere diesen Lebenslauf und extrahiere die persönlichen Kontaktdaten.

LEBENSLAUF:
{cv_text[:4000]}

Extrahiere folgende Felder als JSON-Objekt:
- full_name: Vollständiger Name (Vor- und Nachname)
- phone: Telefonnummer
- email: E-Mail-Adresse
- address: Straße und Hausnummer
- city: Stadt/Ort
- postal_code: Postleitzahl
- website: Website oder LinkedIn-URL

Setze null für Felder, die nicht im Lebenslauf gefunden werden."""

    def _normalize_profile(self, data: dict) -> dict:
        """Normalize API response into a profile dictionary."""
        return {
            field: (data.get(field).strip() or None) if isinstance(data.get(field), str) else None
            for field in self.PROFILE_FIELDS
        }
