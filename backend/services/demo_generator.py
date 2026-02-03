"""
Demo Generator Service.

Provides simplified cover letter generation for anonymous users using a sample CV.
No database storage, no PDF generation - just returns the generated text.
"""

import json
import os

from .api_client import ClaudeAPIClient

# Cache the sample CV at module load
_SAMPLE_CV_CACHE: dict | None = None


def get_sample_cv() -> dict:
    """Load and cache the sample CV from disk."""
    global _SAMPLE_CV_CACHE
    if _SAMPLE_CV_CACHE is None:
        sample_cv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_cv.json")
        with open(sample_cv_path, encoding="utf-8") as f:
            _SAMPLE_CV_CACHE = json.load(f)
    return _SAMPLE_CV_CACHE


class DemoGenerator:
    """Simplified generator for anonymous demo users.

    Uses a pre-cached sample CV instead of user documents.
    Returns generated text only (no PDF, no DB storage).
    """

    def __init__(self):
        self.api_client = ClaudeAPIClient()
        self.sample_cv = get_sample_cv()

    def generate_demo(self, job_text: str, company_name: str) -> dict:
        """Generate a demo cover letter introduction from job text.

        Args:
            job_text: The job posting text (scraped or provided)
            company_name: The company name

        Returns:
            dict with:
                - einleitung: The generated cover letter introduction
                - position: Extracted position
                - company: Company name
                - sample_cv_name: Name of the sample CV persona
        """
        # Extract details from job posting
        details = self.api_client.extract_bewerbung_details(job_text, company_name)

        # Generate the cover letter introduction using sample CV
        einleitung = self.api_client.generate_einleitung(
            cv_text=self.sample_cv["cv_text"],
            stellenanzeige_text=job_text,
            firma_name=company_name,
            zeugnis_text=None,  # No work reference for demo
            details=details,
            use_extraction=True,
        )

        return {
            "einleitung": einleitung,
            "position": details.get("position", "Softwareentwickler"),
            "company": company_name,
            "ansprechpartner": details.get("ansprechpartner", "Sehr geehrte Damen und Herren"),
            "sample_cv_name": self.sample_cv["name"],
        }
