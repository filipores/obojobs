"""
Requirement Analyzer Service - Extracts job requirements from job posting text using Claude API.
"""

import json
import logging

from anthropic import Anthropic

from config import config
from services.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class RequirementAnalyzer:
    """Service to extract job requirements from job postings using Claude API."""

    VALID_TYPES = ["must_have", "nice_to_have"]
    VALID_CATEGORIES = ["technical", "soft_skills", "languages", "tools", "certifications"]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def analyze_requirements(self, job_text: str) -> list[dict]:
        """
        Extract requirements from job posting text using Claude API.

        Args:
            job_text: The text content of the job posting

        Returns:
            List of requirement dictionaries with keys:
            - requirement_text: Description of the requirement
            - requirement_type: "must_have" or "nice_to_have"
            - skill_category: One of technical, soft_skills, languages, tools, certifications (or null)
        """
        prompt = self._create_extraction_prompt(job_text)

        try:
            response = self._call_api_with_retry(prompt)
            return self._parse_requirements_response(response)
        except Exception as e:
            logger.error("Requirement-Analyse fehlgeschlagen: %s", e)
            return []

    @retry_with_backoff(max_attempts=3, base_delay=2.0)
    def _call_api_with_retry(self, prompt: str) -> str:
        """Send a message to the Claude API with automatic retry on failure."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def _create_extraction_prompt(self, job_text: str) -> str:
        """Create the prompt for requirement extraction."""
        return f"""Analysiere diese Stellenanzeige und extrahiere alle Anforderungen an den Bewerber.

STELLENANZEIGE:
{job_text[:6000]}

Extrahiere alle Anforderungen und kategorisiere sie. Für jede Anforderung gib an:

1. requirement_text: Die Anforderung als kurzer, prägnanter Text (z.B. "5 Jahre Erfahrung mit Python", "Teamfähigkeit", "Fließend Deutsch")

2. requirement_type: Ob es sich um eine Pflicht-Anforderung oder optionale Anforderung handelt:
   - "must_have": Pflicht-Anforderungen (erkennbar an Wörtern wie "erforderlich", "zwingend", "vorausgesetzt", "müssen", "Voraussetzung", "notwendig")
   - "nice_to_have": Optionale Anforderungen (erkennbar an Wörtern wie "wünschenswert", "idealerweise", "von Vorteil", "optional", "gerne", "Plus")

3. skill_category: Die Kategorie der Anforderung (oder null wenn unklar):
   - "technical": Technische Skills wie Programmiersprachen, Frameworks, Methoden (z.B. Python, Scrum, SQL)
   - "soft_skills": Soziale Kompetenzen (z.B. Teamfähigkeit, Kommunikation, Eigeninitiative)
   - "languages": Sprachkenntnisse (z.B. Deutsch, Englisch, Französisch)
   - "tools": Software und Tools (z.B. Git, Docker, SAP, Jira)
   - "certifications": Zertifikate und Abschlüsse (z.B. Studium, AWS Certified, ISTQB)

WICHTIG:
- Antworte NUR mit einem JSON-Array. Keine anderen Texte.
- Extrahiere auch allgemeine Anforderungen wie "Berufserfahrung", "Studium", etc.
- Bei Unsicherheit ob must_have oder nice_to_have: Wähle must_have für explizit geforderte Dinge.

Beispiel-Antwort:
[
  {{"requirement_text": "5 Jahre Erfahrung mit Python", "requirement_type": "must_have", "skill_category": "technical"}},
  {{"requirement_text": "Teamfähigkeit", "requirement_type": "must_have", "skill_category": "soft_skills"}},
  {{"requirement_text": "Docker Kenntnisse", "requirement_type": "nice_to_have", "skill_category": "tools"}},
  {{"requirement_text": "Fließend Deutsch", "requirement_type": "must_have", "skill_category": "languages"}},
  {{"requirement_text": "Abgeschlossenes Studium Informatik", "requirement_type": "must_have", "skill_category": "certifications"}}
]

Extrahiere jetzt alle Anforderungen als JSON-Array:"""

    def _parse_requirements_response(self, response_text: str) -> list[dict]:
        """Parse the Claude response into a list of requirement dictionaries."""
        # Clean up the response - find JSON array
        text = response_text.strip()

        # Find JSON array bounds
        start_idx = text.find("[")
        end_idx = text.rfind("]")

        if start_idx == -1 or end_idx == -1:
            logger.warning("Keine JSON-Struktur in der Antwort gefunden")
            return []

        json_text = text[start_idx : end_idx + 1]

        try:
            requirements = json.loads(json_text)

            # Validate and clean requirements
            valid_requirements = []
            for req in requirements:
                if not isinstance(req, dict):
                    continue

                requirement_text = req.get("requirement_text", "").strip()
                requirement_type = req.get("requirement_type", "").strip().lower()
                skill_category = req.get("skill_category")

                # Skip invalid entries
                if not requirement_text:
                    continue

                # Validate requirement type
                if requirement_type not in self.VALID_TYPES:
                    # Default to must_have for unknown types
                    requirement_type = "must_have"

                # Validate skill category
                if skill_category:
                    skill_category = skill_category.strip().lower()
                    if skill_category not in self.VALID_CATEGORIES:
                        # Try to map common variations
                        category_mapping = {
                            "programming": "technical",
                            "programmierung": "technical",
                            "sprachen": "languages",
                            "language": "languages",
                            "soft_skill": "soft_skills",
                            "softskills": "soft_skills",
                            "tool": "tools",
                            "certification": "certifications",
                            "zertifikat": "certifications",
                            "zertifikate": "certifications",
                            "ausbildung": "certifications",
                            "education": "certifications",
                        }
                        skill_category = category_mapping.get(skill_category)

                valid_requirements.append(
                    {
                        "requirement_text": requirement_text,
                        "requirement_type": requirement_type,
                        "skill_category": skill_category,
                    }
                )

            return valid_requirements

        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error: %s", e)
            return []
