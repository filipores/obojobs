"""
ATS (Applicant Tracking System) Service.

Analyzes a CV against a job description to provide a match score,
matched/missing keywords, and improvement suggestions.

Keywords are categorized into:
- hard_skills: Technical skills, programming languages, tools
- soft_skills: Communication, leadership, teamwork, etc.
- qualifications: Degrees, certifications, licenses
- experience: Years of experience, specific roles

Score is weighted: hard_skills (40%), qualifications (25%),
experience (20%), soft_skills (15%)
"""

import json
import re

from anthropic import Anthropic

from config import config

# Weights for score calculation
CATEGORY_WEIGHTS = {
    "hard_skills": 0.40,
    "qualifications": 0.25,
    "experience": 0.20,
    "soft_skills": 0.15,
}


class ATSService:
    """Service for analyzing CVs against job descriptions."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def analyze_cv_against_job(
        self, cv_text: str, job_description: str, retry_count: int = 3
    ) -> dict:
        """
        Analyze a CV against a job description.

        Args:
            cv_text: The text content of the CV/resume
            job_description: The job posting text
            retry_count: Number of retries on API failure

        Returns:
            dict with keys:
                - score: int (0-100) weighted match percentage
                - matched_keywords: list of all keywords found in both CV and job
                - missing_keywords: list of all keywords in job but not in CV
                - suggestions: list of dicts with content and priority
                - categories: dict with hard_skills, soft_skills, qualifications,
                              experience, each containing matched and missing lists

        Raises:
            ValueError: If cv_text or job_description is empty
            Exception: If API call fails after all retries
        """
        if not cv_text or not cv_text.strip():
            raise ValueError("CV text cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty")

        prompt = self._create_analysis_prompt(cv_text, job_description)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = response.content[0].text.strip()
                return self._parse_analysis_response(response_text)
            except ValueError:
                raise
            except Exception as e:
                if attempt < retry_count - 1:
                    continue
                raise Exception(
                    f"ATS analysis failed after {retry_count} attempts: {str(e)}"
                ) from e

    def _create_analysis_prompt(self, cv_text: str, job_description: str) -> str:
        """Create the prompt for ATS analysis."""
        return f"""Du bist ein ATS (Applicant Tracking System) Experte. Analysiere den folgenden Lebenslauf gegen die Stellenanzeige.

LEBENSLAUF:
{cv_text[:4000]}

STELLENANZEIGE:
{job_description[:4000]}

Analysiere und kategorisiere die Keywords in folgende Kategorien:
1. hard_skills: Technische Fähigkeiten, Programmiersprachen, Tools, Software
2. soft_skills: Kommunikation, Führung, Teamarbeit, Problemlösung
3. qualifications: Abschlüsse, Zertifikate, Lizenzen, Ausbildungen
4. experience: Berufserfahrung in Jahren, spezifische Rollen, Branchen

Für jeden Verbesserungsvorschlag, gib eine Priorität an:
- high: Kritisch für die Bewerbung, sollte unbedingt hinzugefügt werden
- medium: Wichtig, würde die Bewerbung deutlich verbessern
- low: Nice-to-have, würde die Bewerbung leicht verbessern

WICHTIG: Antworte NUR mit einem JSON-Objekt in genau diesem Format:
{{
  "categories": {{
    "hard_skills": {{
      "matched": ["skill1", "skill2"],
      "missing": ["skill3", "skill4"]
    }},
    "soft_skills": {{
      "matched": ["skill1"],
      "missing": ["skill2"]
    }},
    "qualifications": {{
      "matched": ["qual1"],
      "missing": ["qual2"]
    }},
    "experience": {{
      "matched": ["exp1"],
      "missing": ["exp2"]
    }}
  }},
  "suggestions": [
    {{"content": "Vorschlag 1", "priority": "high"}},
    {{"content": "Vorschlag 2", "priority": "medium"}},
    {{"content": "Vorschlag 3", "priority": "low"}}
  ]
}}

Antworte NUR mit dem JSON, keine zusätzlichen Erklärungen."""

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse the API response into structured data."""
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            return self._get_default_response()

        try:
            data = json.loads(json_match.group())

            # Parse categories
            categories = self._parse_categories(data.get("categories", {}))

            # Calculate weighted score
            score = self._calculate_weighted_score(categories)

            # Flatten keywords for backward compatibility
            matched_keywords = []
            missing_keywords = []
            for cat_data in categories.values():
                matched_keywords.extend(cat_data.get("matched", []))
                missing_keywords.extend(cat_data.get("missing", []))

            # Parse suggestions with priority
            suggestions = self._parse_suggestions(data.get("suggestions", []))

            return {
                "score": score,
                "matched_keywords": matched_keywords,
                "missing_keywords": missing_keywords,
                "suggestions": suggestions,
                "categories": categories,
            }
        except json.JSONDecodeError:
            return self._get_default_response()

    def _parse_categories(self, categories_data: dict) -> dict:
        """Parse and validate category data."""
        valid_categories = ["hard_skills", "soft_skills", "qualifications", "experience"]
        result = {}

        for category in valid_categories:
            cat_data = categories_data.get(category, {})
            if not isinstance(cat_data, dict):
                cat_data = {}

            matched = cat_data.get("matched", [])
            if not isinstance(matched, list):
                matched = []
            matched = [str(k) for k in matched if k]

            missing = cat_data.get("missing", [])
            if not isinstance(missing, list):
                missing = []
            missing = [str(k) for k in missing if k]

            result[category] = {"matched": matched, "missing": missing}

        return result

    def _calculate_weighted_score(self, categories: dict) -> int:
        """Calculate weighted score based on category matches."""
        total_score = 0.0

        for category, weight in CATEGORY_WEIGHTS.items():
            cat_data = categories.get(category, {})
            matched = len(cat_data.get("matched", []))
            missing = len(cat_data.get("missing", []))
            total = matched + missing

            if total > 0:
                category_score = (matched / total) * 100
            else:
                # If no keywords in this category, give full score for this weight
                category_score = 100

            total_score += category_score * weight

        return max(0, min(100, int(round(total_score))))

    def _parse_suggestions(self, suggestions_data: list) -> list:
        """Parse suggestions with priority validation."""
        if not isinstance(suggestions_data, list):
            return []

        valid_priorities = ["high", "medium", "low"]
        result = []

        for suggestion in suggestions_data:
            if isinstance(suggestion, dict):
                content = suggestion.get("content", "")
                priority = suggestion.get("priority", "medium")
                if content and isinstance(content, str):
                    if priority not in valid_priorities:
                        priority = "medium"
                    result.append({"content": content, "priority": priority})
            elif isinstance(suggestion, str) and suggestion:
                # Backward compatibility: plain string suggestions
                result.append({"content": suggestion, "priority": "medium"})

        return result

    def _get_default_response(self) -> dict:
        """Return a default response when parsing fails."""
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": [
                {"content": "Analyse konnte nicht durchgeführt werden", "priority": "high"}
            ],
            "categories": {
                "hard_skills": {"matched": [], "missing": []},
                "soft_skills": {"matched": [], "missing": []},
                "qualifications": {"matched": [], "missing": []},
                "experience": {"matched": [], "missing": []},
            },
        }


def analyze_cv_against_job(
    cv_text: str, job_description: str, api_key: str | None = None
) -> dict:
    """
    Convenience function to analyze a CV against a job description.

    Args:
        cv_text: The text content of the CV/resume
        job_description: The job posting text
        api_key: Optional API key (uses config default if not provided)

    Returns:
        dict with score, matched_keywords, missing_keywords, suggestions
    """
    service = ATSService(api_key=api_key)
    return service.analyze_cv_against_job(cv_text, job_description)
