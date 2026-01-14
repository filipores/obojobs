"""
Contact Data Extractor Service

Extracts contact information (names, emails, locations) from job posting text
using a combination of regex patterns and AI-based NLP extraction.

UX-004: Automatische Extraktion von Kontaktdaten aus manuellem Text
"""

import re

from anthropic import Anthropic

from config import config


class ContactExtractor:
    """Extract contact data from job posting text using NLP and regex patterns."""

    # German cities (top 100+ cities and regions)
    GERMAN_CITIES = {
        # Top cities
        "berlin", "hamburg", "münchen", "munich", "köln", "cologne", "frankfurt",
        "düsseldorf", "dortmund", "essen", "leipzig", "bremen", "dresden",
        "hannover", "nürnberg", "nuremberg", "duisburg", "bochum", "wuppertal",
        "bielefeld", "bonn", "münster", "karlsruhe", "mannheim", "augsburg",
        "wiesbaden", "gelsenkirchen", "mönchengladbach", "braunschweig",
        "chemnitz", "kiel", "aachen", "halle", "magdeburg", "freiburg",
        "krefeld", "lübeck", "oberhausen", "erfurt", "mainz", "rostock",
        "kassel", "hagen", "hamm", "saarbrücken", "mülheim", "potsdam",
        "ludwigshafen", "oldenburg", "leverkusen", "osnabrück", "solingen",
        "heidelberg", "herne", "neuss", "darmstadt", "paderborn", "regensburg",
        "ingolstadt", "würzburg", "wolfsburg", "ulm", "heilbronn", "göttingen",
        "pforzheim", "offenbach", "bottrop", "recklinghausen", "remscheid",
        "bergisch gladbach", "reutlingen", "jena", "trier", "erlangen",
        "moers", "salzgitter", "siegen", "hildesheim", "cottbus", "kaiserslautern",
        # Regions
        "ruhrgebiet", "rhein-main", "rheinland", "bayern", "bavaria",
        "baden-württemberg", "nordrhein-westfalen", "nrw", "niedersachsen",
        "hessen", "sachsen", "thüringen", "brandenburg", "schleswig-holstein",
        # Common location indicators
        "deutschlandweit", "bundesweit", "remote", "home office", "homeoffice",
    }

    # Email patterns to exclude (not personal contact emails)
    EXCLUDED_EMAIL_PATTERNS = [
        r"noreply", r"no-reply", r"newsletter", r"support@indeed",
        r"info@indeed", r"support@stepstone", r"info@stepstone",
        r"donotreply", r"mailer-daemon", r"postmaster",
    ]

    # German salutation patterns for contact person detection
    SALUTATION_PATTERNS = [
        r"Ansprechpartner(?:in)?[:\s]+(?:Frau|Herr)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)",
        r"Kontakt[:\s]+(?:Frau|Herr)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)",
        r"(?:Frau|Herr)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)\s+(?:freut sich|steht Ihnen)",
        r"Ihre Ansprechpartnerin[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)",
        r"Ihr Ansprechpartner[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)",
        r"Bewerbung(?:en)?\s+(?:an|bei)[:\s]+(?:Frau|Herr)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)",
    ]

    def __init__(self):
        """Initialize the contact extractor."""
        self.api_key = config.ANTHROPIC_API_KEY
        self.client = None
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def extract_contact_data(self, job_text: str) -> dict:
        """
        Extract contact information from job posting text.

        Args:
            job_text: The full job posting text

        Returns:
            dict with keys:
                - contact_person: Name of contact person (or None)
                - contact_email: Contact email address (or None)
                - location: Job location/city (or None)
                - employment_type: Employment type if found (or None)
        """
        if not job_text or len(job_text) < 50:
            return {
                "contact_person": None,
                "contact_email": None,
                "location": None,
                "employment_type": None,
            }

        # First try regex-based extraction (fast, no API calls)
        result = self._extract_with_regex(job_text)

        # If key fields are missing, use Claude for NLP extraction
        if not result["contact_person"] or not result["location"]:
            nlp_result = self._extract_with_nlp(job_text)
            # Merge results, preferring NLP for missing fields
            if not result["contact_person"] and nlp_result.get("contact_person"):
                result["contact_person"] = nlp_result["contact_person"]
            if not result["location"] and nlp_result.get("location"):
                result["location"] = nlp_result["location"]
            if not result["employment_type"] and nlp_result.get("employment_type"):
                result["employment_type"] = nlp_result["employment_type"]
            # Email from NLP only if regex didn't find one
            if not result["contact_email"] and nlp_result.get("contact_email"):
                result["contact_email"] = nlp_result["contact_email"]

        return result

    def _extract_with_regex(self, text: str) -> dict:
        """Extract contact data using regex patterns."""
        result = {
            "contact_person": None,
            "contact_email": None,
            "location": None,
            "employment_type": None,
        }

        # Extract email addresses
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, text)

        # Filter out excluded email patterns
        valid_emails = []
        for email in emails:
            email_lower = email.lower()
            is_excluded = any(
                re.search(pattern, email_lower)
                for pattern in self.EXCLUDED_EMAIL_PATTERNS
            )
            if not is_excluded:
                valid_emails.append(email)

        if valid_emails:
            # Prefer emails that look like personal/HR contacts
            for email in valid_emails:
                email_lower = email.lower()
                if any(
                    keyword in email_lower
                    for keyword in ["bewerbung", "jobs", "karriere", "career", "hr", "personal", "recruiting"]
                ):
                    result["contact_email"] = email
                    break
            # Fallback to first valid email
            if not result["contact_email"]:
                result["contact_email"] = valid_emails[0]

        # Extract contact person using salutation patterns
        for pattern in self.SALUTATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["contact_person"] = match.group(1).strip()
                break

        # Extract location/city
        text_lower = text.lower()
        for city in self.GERMAN_CITIES:
            # Match city as word boundary (not part of another word)
            city_pattern = rf"\b{re.escape(city)}\b"
            if re.search(city_pattern, text_lower):
                # Capitalize properly
                result["location"] = city.title() if city not in ["nrw", "nrw"] else city.upper()
                break

        # Also check for "Standort:" pattern
        standort_match = re.search(
            r"Standort[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s*[-/,]\s*[A-ZÄÖÜ][a-zäöüß]+)?)",
            text,
            re.IGNORECASE,
        )
        if standort_match and not result["location"]:
            result["location"] = standort_match.group(1).strip()

        # Extract employment type
        employment_patterns = [
            (r"\b(Vollzeit|Full-?time)\b", "Vollzeit"),
            (r"\b(Teilzeit|Part-?time)\b", "Teilzeit"),
            (r"\b(Remote|100%?\s*Remote|Homeoffice|Home\s*Office)\b", "Remote"),
            (r"\b(Hybrid|Hybrid-?Modell)\b", "Hybrid"),
            (r"\b(Festanstellung|Unbefristet)\b", "Festanstellung"),
            (r"\b(Befristet|Zeitvertrag)\b", "Befristet"),
            (r"\b(Freelance|Freiberuflich)\b", "Freelance"),
            (r"\b(Werkstudent|Working\s*Student)\b", "Werkstudent"),
            (r"\b(Praktikum|Internship)\b", "Praktikum"),
        ]

        for pattern, employment_type in employment_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result["employment_type"] = employment_type
                break

        return result

    def _extract_with_nlp(self, text: str) -> dict:
        """Extract contact data using Claude NLP."""
        if not self.client:
            return {}

        # Limit text length for API efficiency
        text_truncated = text[:3000]

        prompt = f"""Extrahiere die folgenden Kontaktdaten aus diesem Stellentext. Antworte NUR im angegebenen Format.

STELLENTEXT:
{text_truncated}

Extrahiere folgende Informationen:
1. ANSPRECHPARTNER: Name der Kontaktperson (z.B. "Frau Schmidt", "Herr Müller"). Falls kein Name erkennbar, schreibe "NICHT_GEFUNDEN".
2. EMAIL: E-Mail-Adresse für Bewerbungen. Falls keine erkennbar, schreibe "NICHT_GEFUNDEN".
3. STANDORT: Stadt/Region des Arbeitsplatzes (z.B. "Berlin", "München", "Remote"). Falls nicht erkennbar, schreibe "NICHT_GEFUNDEN".
4. ANSTELLUNGSART: Art der Anstellung (z.B. "Vollzeit", "Teilzeit", "Remote", "Hybrid"). Falls nicht erkennbar, schreibe "NICHT_GEFUNDEN".

WICHTIG: Antworte EXAKT in diesem Format (eine Zeile pro Feld):
ANSPRECHPARTNER: [Wert]
EMAIL: [Wert]
STANDORT: [Wert]
ANSTELLUNGSART: [Wert]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()
            return self._parse_nlp_response(response_text)

        except Exception as e:
            print(f"NLP extraction failed: {e}")
            return {}

    def _parse_nlp_response(self, response_text: str) -> dict:
        """Parse the NLP response into a structured dict."""
        result = {}

        for line in response_text.split("\n"):
            line = line.strip()
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().upper()
            value = value.strip()

            # Skip "not found" values
            if value.upper() in ["NICHT_GEFUNDEN", "NICHT GEFUNDEN", "N/A", "KEINE ANGABE", ""]:
                continue

            if key == "ANSPRECHPARTNER":
                result["contact_person"] = value
            elif key == "EMAIL":
                # Validate email format
                if re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", value):
                    result["contact_email"] = value
            elif key == "STANDORT":
                result["location"] = value
            elif key == "ANSTELLUNGSART":
                result["employment_type"] = value

        return result

    def format_contact_person_salutation(self, contact_person: str | None, company_name: str = "") -> str:
        """
        Format contact person name into a proper salutation.

        Args:
            contact_person: Name like "Frau Schmidt" or "Max Müller"
            company_name: Company name as fallback

        Returns:
            Formatted salutation like "Sehr geehrte Frau Schmidt" or fallback
        """
        if not contact_person:
            if company_name:
                return f"Moin Moin liebes {company_name} Team"
            return "Sehr geehrte Damen und Herren"

        contact_lower = contact_person.lower()

        # Already has salutation prefix
        if contact_lower.startswith("frau "):
            return f"Sehr geehrte {contact_person}"
        elif contact_lower.startswith("herr "):
            return f"Sehr geehrter {contact_person}"
        elif contact_lower.startswith("sehr geehrte"):
            return contact_person

        # Try to determine gender from name (simple heuristic)
        # This is a simplified approach - in production, a more sophisticated
        # name database would be used
        return f"Sehr geehrte/r {contact_person}"
