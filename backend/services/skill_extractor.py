"""
Skill Extractor Service - Extracts skills from CV text using Claude API.
"""

import json
import time

from anthropic import Anthropic

from config import config


class SkillExtractor:
    """Service to extract skills from CV documents using Claude API."""

    VALID_CATEGORIES = ["technical", "soft_skills", "languages", "tools", "certifications"]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def extract_skills_from_cv(self, cv_text: str, retry_count: int = 3) -> list[dict]:
        """
        Extract skills from CV text using Claude API.

        Args:
            cv_text: The text content of the CV
            retry_count: Number of retries on failure

        Returns:
            List of skill dictionaries with keys:
            - skill_name: Name of the skill
            - skill_category: One of technical, soft_skills, languages, tools, certifications
            - experience_years: Years of experience (float or None)
        """
        prompt = self._create_extraction_prompt(cv_text)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                skills = self._parse_skills_response(response_text)
                return skills

            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"Skill-Extraktion fehlgeschlagen (Versuch {attempt + 1}/{retry_count}): {str(e)}")
                    time.sleep(2)
                else:
                    print(f"⚠ Skill-Extraktion fehlgeschlagen nach {retry_count} Versuchen: {str(e)}")
                    return []

    def _create_extraction_prompt(self, cv_text: str) -> str:
        """Create the prompt for skill extraction."""
        return f"""Analysiere diesen Lebenslauf und extrahiere alle Skills/Fähigkeiten.

LEBENSLAUF:
{cv_text[:4000]}

Extrahiere alle Skills und kategorisiere sie. Für jeden Skill gib an:
1. skill_name: Der Name des Skills (z.B. "Python", "Projektmanagement", "Englisch")
2. skill_category: Eine der folgenden Kategorien:
   - technical: Programmiersprachen, Frameworks, technische Methoden (z.B. Python, React, Scrum)
   - soft_skills: Soziale Kompetenzen (z.B. Teamführung, Kommunikation)
   - languages: Sprachkenntnisse (z.B. Deutsch, Englisch)
   - tools: Software und Tools (z.B. Git, Docker, Jira)
   - certifications: Zertifikate und Qualifikationen (z.B. AWS Certified, ISTQB)
3. experience_years: Jahre Erfahrung (Zahl oder null wenn nicht erkennbar)

WICHTIG: Antworte NUR mit einem JSON-Array. Keine anderen Texte.

Beispiel-Antwort:
[
  {{"skill_name": "Python", "skill_category": "technical", "experience_years": 5}},
  {{"skill_name": "Englisch", "skill_category": "languages", "experience_years": null}},
  {{"skill_name": "Git", "skill_category": "tools", "experience_years": 3}}
]

Extrahiere jetzt alle Skills als JSON-Array:"""

    def _parse_skills_response(self, response_text: str) -> list[dict]:
        """Parse the Claude response into a list of skill dictionaries."""
        # Clean up the response - find JSON array
        text = response_text.strip()

        # Find JSON array bounds
        start_idx = text.find("[")
        end_idx = text.rfind("]")

        if start_idx == -1 or end_idx == -1:
            print("⚠ Keine JSON-Struktur in der Antwort gefunden")
            return []

        json_text = text[start_idx : end_idx + 1]

        try:
            skills = json.loads(json_text)

            # Validate and clean skills
            valid_skills = []
            for skill in skills:
                if not isinstance(skill, dict):
                    continue

                skill_name = skill.get("skill_name", "").strip()
                skill_category = skill.get("skill_category", "").strip().lower()
                experience_years = skill.get("experience_years")

                # Skip invalid entries
                if not skill_name:
                    continue

                # Validate category
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
                    }
                    skill_category = category_mapping.get(skill_category, "technical")

                # Validate experience_years
                if experience_years is not None:
                    try:
                        experience_years = float(experience_years)
                        if experience_years < 0:
                            experience_years = None
                    except (ValueError, TypeError):
                        experience_years = None

                valid_skills.append(
                    {"skill_name": skill_name, "skill_category": skill_category, "experience_years": experience_years}
                )

            return valid_skills

        except json.JSONDecodeError as e:
            print(f"⚠ JSON Parse Error: {str(e)}")
            return []
