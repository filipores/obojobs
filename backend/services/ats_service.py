"""
ATS (Applicant Tracking System) Service.

Analyzes a CV against a job description to provide a match score,
matched/missing keywords, and improvement suggestions.
"""

import json
import re

from anthropic import Anthropic

from config import config


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
                - score: int (0-100) match percentage
                - matched_keywords: list of keywords found in both CV and job
                - missing_keywords: list of keywords in job but not in CV
                - suggestions: list of improvement suggestions

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

Analysiere:
1. Welche Keywords/Skills aus der Stellenanzeige sind im Lebenslauf vorhanden?
2. Welche wichtigen Keywords/Skills fehlen im Lebenslauf?
3. Berechne einen Match-Score (0-100) basierend auf der Übereinstimmung
4. Gib konkrete Verbesserungsvorschläge

WICHTIG: Antworte NUR mit einem JSON-Objekt in genau diesem Format:
{{
  "score": <zahl 0-100>,
  "matched_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...],
  "suggestions": ["Vorschlag 1", "Vorschlag 2", ...]
}}

Antworte NUR mit dem JSON, keine zusätzlichen Erklärungen."""

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse the API response into structured data."""
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            return self._get_default_response()

        try:
            data = json.loads(json_match.group())

            score = data.get("score", 0)
            if not isinstance(score, (int, float)):
                score = 0
            score = max(0, min(100, int(score)))

            matched = data.get("matched_keywords", [])
            if not isinstance(matched, list):
                matched = []
            matched = [str(k) for k in matched if k]

            missing = data.get("missing_keywords", [])
            if not isinstance(missing, list):
                missing = []
            missing = [str(k) for k in missing if k]

            suggestions = data.get("suggestions", [])
            if not isinstance(suggestions, list):
                suggestions = []
            suggestions = [str(s) for s in suggestions if s]

            return {
                "score": score,
                "matched_keywords": matched,
                "missing_keywords": missing,
                "suggestions": suggestions,
            }
        except json.JSONDecodeError:
            return self._get_default_response()

    def _get_default_response(self) -> dict:
        """Return a default response when parsing fails."""
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": ["Analyse konnte nicht durchgeführt werden"],
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
