"""
Skill Extractor Service - Extracts skills from CV text using DeepSeek via Fireworks.
"""

import logging

from services.ai_client import AIClient

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Service to extract skills from CV documents using DeepSeek."""

    VALID_CATEGORIES = ["technical", "soft_skills", "languages", "tools", "certifications"]

    CATEGORY_MAPPING = {
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

    def __init__(self):
        self.client = AIClient()

    def extract_skills_from_cv(self, cv_text: str) -> list[dict]:
        """Extract skills from CV text using DeepSeek via Fireworks.

        Returns list of skill dicts with keys: skill_name, skill_category, experience_years
        """
        prompt = self._create_extraction_prompt(cv_text)

        try:
            data = self.client._call_api_json_with_retry(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2,
                model=self.client.model,
            )

            skills = data.get("skills", [])
            return self._validate_skills(skills)

        except Exception as e:
            logger.error("Skill-Extraktion fehlgeschlagen: %s", e)
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

Antworte als JSON-Objekt mit einem "skills"-Array.

Beispiel:
{{"skills": [
  {{"skill_name": "Python", "skill_category": "technical", "experience_years": 5}},
  {{"skill_name": "Englisch", "skill_category": "languages", "experience_years": null}},
  {{"skill_name": "Git", "skill_category": "tools", "experience_years": 3}}
]}}"""

    def _validate_skills(self, skills: list) -> list[dict]:
        """Validate and normalize extracted skills."""
        valid_skills = []
        for skill in skills:
            if not isinstance(skill, dict):
                continue

            skill_name = skill.get("skill_name", "").strip()
            skill_category = skill.get("skill_category", "").strip().lower()
            experience_years = skill.get("experience_years")

            if not skill_name:
                continue

            if skill_category not in self.VALID_CATEGORIES:
                skill_category = self.CATEGORY_MAPPING.get(skill_category, "technical")

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
