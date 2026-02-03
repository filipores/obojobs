"""
ATS Optimizer Service - Analyzes generated cover letters for ATS compatibility.

This service differs from ats_service.py:
- ats_service.py: Analyzes CV against job posting (before generation)
- ats_optimizer.py: Analyzes GENERATED cover letter against job posting (after generation)

The goal is to ensure the generated cover letter contains the right keywords
from the job posting to pass through ATS systems.
"""

import json
import re

from anthropic import Anthropic

from config import config


class ATSOptimizer:
    """Service for optimizing cover letters for ATS systems."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def analyze_cover_letter(self, cover_letter_text: str, job_description: str, retry_count: int = 3) -> dict:
        """
        Analyze a generated cover letter against a job description for ATS compatibility.

        Args:
            cover_letter_text: The generated cover letter/application text
            job_description: The original job posting text
            retry_count: Number of retries on API failure

        Returns:
            dict with keys:
                - ats_score: int (0-100) ATS compatibility score
                - missing_keywords: list of important keywords not in cover letter
                - keyword_suggestions: list of dicts with keyword and suggestion
                - format_issues: list of formatting problems
                - keyword_density: dict with keyword counts
        """
        if not cover_letter_text or not cover_letter_text.strip():
            raise ValueError("Cover letter text cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty")

        prompt = self._create_analysis_prompt(cover_letter_text, job_description)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = response.content[0].text.strip()
                return self._parse_analysis_response(response_text, cover_letter_text)
            except ValueError:
                raise
            except Exception as e:
                if attempt < retry_count - 1:
                    continue
                raise Exception(f"ATS optimization analysis failed after {retry_count} attempts: {str(e)}") from e

    def _create_analysis_prompt(self, cover_letter: str, job_description: str) -> str:
        """Create the prompt for ATS optimization analysis."""
        return f"""Du bist ein ATS (Applicant Tracking System) Experte. Analysiere das folgende Anschreiben auf ATS-Kompatibilität mit der Stellenanzeige.

STELLENANZEIGE:
{job_description[:4000]}

ANSCHREIBEN:
{cover_letter[:4000]}

Analysiere:
1. Welche wichtigen Keywords aus der Stellenanzeige FEHLEN im Anschreiben?
2. Wie können die fehlenden Keywords natürlich eingebaut werden?
3. Gibt es Formatierungsprobleme die ATS-Systeme verwirren könnten?

WICHTIG: Antworte NUR mit einem JSON-Objekt in genau diesem Format:
{{
  "missing_keywords": [
    "Keyword1",
    "Keyword2"
  ],
  "keyword_suggestions": [
    {{"keyword": "Python", "suggestion": "Erwähne 'Python' im Kontext deiner Projekterfahrung, z.B. 'In meiner Tätigkeit bei X entwickelte ich Python-basierte Lösungen'"}},
    {{"keyword": "Teamarbeit", "suggestion": "Füge hinzu: 'Die enge Zusammenarbeit im Team schätze ich besonders'"}}
  ],
  "format_issues": [
    "Sonderzeichen wie ★ können von ATS-Systemen nicht korrekt gelesen werden",
    "Tabellen sollten vermieden werden"
  ],
  "found_keywords": [
    "Java",
    "Kommunikation",
    "Projektmanagement"
  ]
}}

Regeln:
- missing_keywords: Nur wirklich WICHTIGE Keywords (max 10)
- keyword_suggestions: Konkrete, natürlich klingende Einbauvorschläge (max 5)
- format_issues: Nur wenn tatsächliche Probleme vorliegen (kann leer sein)
- found_keywords: Keywords die bereits gut abgedeckt sind

Antworte NUR mit dem JSON, keine zusätzlichen Erklärungen."""

    def _parse_analysis_response(self, response_text: str, cover_letter: str) -> dict:
        """Parse the API response and calculate ATS score."""
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            return self._get_default_response()

        try:
            data = json.loads(json_match.group())

            missing_keywords = data.get("missing_keywords", [])
            if not isinstance(missing_keywords, list):
                missing_keywords = []
            missing_keywords = [str(k) for k in missing_keywords if k][:10]

            found_keywords = data.get("found_keywords", [])
            if not isinstance(found_keywords, list):
                found_keywords = []
            found_keywords = [str(k) for k in found_keywords if k]

            keyword_suggestions = self._parse_suggestions(data.get("keyword_suggestions", []))

            format_issues = data.get("format_issues", [])
            if not isinstance(format_issues, list):
                format_issues = []
            format_issues = [str(i) for i in format_issues if i]

            # Calculate keyword density
            keyword_density = self._calculate_keyword_density(cover_letter, found_keywords + missing_keywords)

            # Calculate ATS score
            ats_score = self._calculate_ats_score(
                found_count=len(found_keywords),
                missing_count=len(missing_keywords),
                format_issues_count=len(format_issues),
            )

            return {
                "ats_score": ats_score,
                "missing_keywords": missing_keywords,
                "keyword_suggestions": keyword_suggestions,
                "format_issues": format_issues,
                "keyword_density": keyword_density,
                "found_keywords": found_keywords,
            }

        except json.JSONDecodeError:
            return self._get_default_response()

    def _parse_suggestions(self, suggestions_data: list) -> list:
        """Parse keyword suggestions."""
        if not isinstance(suggestions_data, list):
            return []

        result = []
        for suggestion in suggestions_data[:5]:
            if isinstance(suggestion, dict):
                keyword = suggestion.get("keyword", "")
                text = suggestion.get("suggestion", "")
                if keyword and text:
                    result.append({"keyword": str(keyword), "suggestion": str(text)})

        return result

    def _calculate_keyword_density(self, text: str, keywords: list) -> dict:
        """Calculate how often each keyword appears in the text."""
        text_lower = text.lower()
        density = {}

        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Count occurrences (word boundary aware)
            pattern = rf"\b{re.escape(keyword_lower)}\b"
            count = len(re.findall(pattern, text_lower))
            density[keyword] = count

        return density

    def _calculate_ats_score(self, found_count: int, missing_count: int, format_issues_count: int) -> int:
        """
        Calculate the ATS compatibility score.

        Score is based on:
        - Ratio of found vs missing keywords (70% weight)
        - Lack of format issues (30% weight)
        """
        total_keywords = found_count + missing_count

        if total_keywords == 0:
            keyword_score = 100
        else:
            keyword_score = (found_count / total_keywords) * 100

        # Format penalty: -10 points per issue, max -30
        format_penalty = min(format_issues_count * 10, 30)
        format_score = 100 - format_penalty

        # Weighted average
        ats_score = int(keyword_score * 0.7 + format_score * 0.3)

        return max(0, min(100, ats_score))

    def _get_default_response(self) -> dict:
        """Return default response when parsing fails."""
        return {
            "ats_score": 0,
            "missing_keywords": [],
            "keyword_suggestions": [{"keyword": "Analyse", "suggestion": "Analyse konnte nicht durchgeführt werden"}],
            "format_issues": ["Analyse konnte nicht durchgeführt werden"],
            "keyword_density": {},
            "found_keywords": [],
        }


def analyze_cover_letter_ats(cover_letter_text: str, job_description: str, api_key: str | None = None) -> dict:
    """
    Convenience function to analyze a cover letter for ATS compatibility.

    Args:
        cover_letter_text: The generated cover letter text
        job_description: The job posting text
        api_key: Optional API key (uses config default if not provided)

    Returns:
        dict with ats_score, missing_keywords, keyword_suggestions, format_issues
    """
    optimizer = ATSOptimizer(api_key=api_key)
    return optimizer.analyze_cover_letter(cover_letter_text, job_description)
