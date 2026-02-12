"""
Salary Coach Service - Provides salary negotiation coaching and market research using Claude API.
Supports German salary negotiation culture with personalized tips and negotiation scripts.
"""

import json
import logging
import time

from anthropic import Anthropic

from config import config
from services.salary_coach_data import (
    VALID_CATEGORIES,
    NegotiationStrategy,
    NegotiationTip,
    SalaryResearch,
    get_fallback_negotiation_strategy,
    get_fallback_salary_research,
)

logger = logging.getLogger(__name__)


class SalaryCoach:
    """Service for salary negotiation coaching using Claude API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht gesetzt")
        self.client = Anthropic(api_key=self.api_key)
        self.model = config.CLAUDE_MODEL

    def research_salary(
        self,
        position: str,
        region: str = "deutschland",
        experience_years: int = 3,
        industry: str | None = None,
        retry_count: int = 3,
    ) -> SalaryResearch:
        """
        Research salary range for a position in a specific region.

        Args:
            position: Job title/position
            region: City or region in Germany
            experience_years: Years of experience
            industry: Optional industry for more accurate ranges
            retry_count: Number of retries on failure

        Returns:
            SalaryResearch with min/max/median salary and sources
        """
        prompt = self._create_salary_research_prompt(position, region, experience_years, industry)

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                return self._parse_salary_research(response_text, position, region, experience_years)

            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning("Salary research failed (attempt %s/%s): %s", attempt + 1, retry_count, e)
                    time.sleep(2)
                else:
                    logger.error("Salary research failed after %s attempts: %s", retry_count, e)
                    return get_fallback_salary_research(position, region, experience_years, industry)

        return get_fallback_salary_research(position, region, experience_years, industry)

    def generate_negotiation_tips(
        self,
        target_salary: int,
        current_salary: int | None = None,
        position: str = "",
        experience_years: int = 3,
        company_name: str | None = None,
        job_offer_details: str | None = None,
        retry_count: int = 3,
    ) -> NegotiationStrategy:
        """
        Generate personalized salary negotiation tips and strategy.

        Args:
            target_salary: Desired salary
            current_salary: Current salary (optional)
            position: Job position
            experience_years: Years of experience
            company_name: Company name for context
            job_offer_details: Details about the job offer
            retry_count: Number of retries on failure

        Returns:
            NegotiationStrategy with tips, scripts, and arguments
        """
        prompt = self._create_negotiation_tips_prompt(
            target_salary,
            current_salary,
            position,
            experience_years,
            company_name,
            job_offer_details,
        )

        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()
                return self._parse_negotiation_strategy(response_text, target_salary, current_salary)

            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        "Negotiation tips generation failed (attempt %s/%s): %s", attempt + 1, retry_count, e
                    )
                    time.sleep(2)
                else:
                    logger.error("Negotiation tips generation failed after %s attempts: %s", retry_count, e)
                    return get_fallback_negotiation_strategy(target_salary, current_salary, position)

        return get_fallback_negotiation_strategy(target_salary, current_salary, position)

    def _create_salary_research_prompt(
        self,
        position: str,
        region: str,
        experience_years: int,
        industry: str | None,
    ) -> str:
        """Create prompt for salary research."""
        industry_context = f"\nBRANCHE: {industry}" if industry else ""

        return f"""Du bist ein Experte für Gehälter und Vergütung auf dem deutschen Arbeitsmarkt.
Recherchiere die aktuelle Gehaltsspanne für folgende Position:

POSITION: {position}
REGION: {region}
BERUFSERFAHRUNG: {experience_years} Jahre{industry_context}

Analysiere und gib eine realistische Gehaltsspanne für den deutschen Arbeitsmarkt an.
Berücksichtige:
- Regionale Unterschiede (München/Frankfurt zahlen mehr als ländliche Gebiete)
- Unternehmensgröße (Konzerne vs. Startups vs. Mittelstand)
- Aktuelle Markttrends
- Tarifliche vs. außertarifliche Vergütung

WICHTIG: Antworte NUR mit einem JSON-Objekt in folgendem Format:

{{
  "min_salary": <zahl>,
  "max_salary": <zahl>,
  "median_salary": <zahl>,
  "currency": "EUR",
  "data_sources": ["<quelle1>", "<quelle2>"],
  "factors": ["<faktor1>", "<faktor2>"],
  "notes": "<zusätzliche hinweise>"
}}

Beispiel:
{{
  "min_salary": 55000,
  "max_salary": 75000,
  "median_salary": 65000,
  "currency": "EUR",
  "data_sources": ["Stepstone Gehaltsreport 2024", "Kununu Gehaltsvergleich", "IG Metall Tarifvertrag"],
  "factors": ["Hohe Nachfrage nach IT-Fachkräften", "Region München mit überdurchschnittlichen Gehältern", "3 Jahre Erfahrung entspricht Mid-Level"],
  "notes": "Zusätzlich sind in der IT-Branche oft Boni, Aktienoptionen und weitere Benefits üblich."
}}

Recherchiere jetzt für: {position} in {region} mit {experience_years} Jahren Erfahrung."""

    def _create_negotiation_tips_prompt(
        self,
        target_salary: int,
        current_salary: int | None,
        position: str,
        experience_years: int,
        company_name: str | None,
        job_offer_details: str | None,
    ) -> str:
        """Create prompt for negotiation tips generation."""
        current_context = f"\nAKTUELLES GEHALT: {current_salary:,}\u20ac".replace(",", ".") if current_salary else ""
        company_context = f"\nUNTERNEHMEN: {company_name}" if company_name else ""
        offer_context = f"\n\nJOB-DETAILS:\n{job_offer_details}" if job_offer_details else ""

        return f"""Du bist ein erfahrener Karriereberater und Experte für Gehaltsverhandlungen in Deutschland.
Erstelle eine personalisierte Verhandlungsstrategie für folgende Situation:

POSITION: {position}
BERUFSERFAHRUNG: {experience_years} Jahre
WUNSCHGEHALT: {target_salary:,}\u20ac{current_context}{company_context}{offer_context}

Berücksichtige die deutsche Geschäftskultur:
- Gehalt wird oft erst im 2. oder 3. Gespräch besprochen
- Direktheit wird geschätzt, aber höflich verpackt
- Sachliche Argumente sind wichtiger als emotionale
- Gesamtpaket beachten (Urlaub, Bonus, Benefits, Weiterbildung)
- Tarifverträge und Betriebsvereinbarungen können relevant sein

WICHTIG: Antworte NUR mit einem JSON-Objekt in folgendem Format:

{{
  "recommended_range": {{
    "min": <zahl>,
    "max": <zahl>
  }},
  "opening_statement": "<formulierung für den einstieg>",
  "counter_arguments": ["<argument1>", "<argument2>", "<argument3>"],
  "fallback_positions": ["<fallback1>", "<fallback2>", "<fallback3>"],
  "tips": [
    {{
      "category": "preparation|opening|counter|closing|timing",
      "title": "<kurzer titel>",
      "description": "<beschreibung>",
      "example_script": "<beispiel-formulierung>",
      "priority": "high|medium|low"
    }}
  ],
  "german_culture_notes": ["<kulturhinweis1>", "<kulturhinweis2>"],
  "common_objections": [
    {{
      "objection": "<typischer einwand>",
      "response": "<empfohlene antwort>"
    }}
  ]
}}

Gib mindestens 5 praktische Tipps und 3 typische Einwände mit Antworten.
Die Tipps sollten verschiedene Kategorien abdecken: preparation, opening, counter, closing, timing.

Erstelle jetzt die Verhandlungsstrategie:"""

    def _parse_salary_research(
        self,
        response_text: str,
        position: str,
        region: str,
        experience_years: int,
    ) -> SalaryResearch:
        """Parse Claude response into SalaryResearch."""
        text = response_text.strip()

        # Find JSON object bounds
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx == -1 or end_idx == -1:
            logger.warning("No JSON structure found in salary research response")
            return get_fallback_salary_research(position, region, experience_years, None)

        json_text = text[start_idx : end_idx + 1]

        try:
            data = json.loads(json_text)

            return SalaryResearch(
                position=position,
                region=region,
                experience_years=experience_years,
                min_salary=int(data.get("min_salary", 45000)),
                max_salary=int(data.get("max_salary", 65000)),
                median_salary=int(data.get("median_salary", 55000)),
                currency=data.get("currency", "EUR"),
                data_sources=data.get("data_sources", []),
                factors=data.get("factors", []),
                notes=data.get("notes", ""),
            )

        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error in salary research: %s", e)
            return get_fallback_salary_research(position, region, experience_years, None)

    def _parse_negotiation_strategy(
        self,
        response_text: str,
        target_salary: int,
        current_salary: int | None,
    ) -> NegotiationStrategy:
        """Parse Claude response into NegotiationStrategy."""
        text = response_text.strip()

        # Find JSON object bounds
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx == -1 or end_idx == -1:
            logger.warning("No JSON structure found in negotiation strategy response")
            return get_fallback_negotiation_strategy(target_salary, current_salary, "")

        json_text = text[start_idx : end_idx + 1]

        try:
            data = json.loads(json_text)

            # Parse tips
            tips = []
            for tip_data in data.get("tips", []):
                category = tip_data.get("category", "preparation").lower()
                if category not in VALID_CATEGORIES:
                    category = "preparation"

                tips.append(
                    NegotiationTip(
                        category=category,
                        title=tip_data.get("title", ""),
                        description=tip_data.get("description", ""),
                        example_script=tip_data.get("example_script", ""),
                        priority=tip_data.get("priority", "medium"),
                    )
                )

            # Parse recommended range
            range_data = data.get("recommended_range", {})
            recommended_min = int(range_data.get("min", int(target_salary * 0.95)))
            recommended_max = int(range_data.get("max", int(target_salary * 1.1)))

            return NegotiationStrategy(
                target_salary=target_salary,
                current_salary=current_salary,
                recommended_range=(recommended_min, recommended_max),
                opening_statement=data.get("opening_statement", ""),
                counter_arguments=data.get("counter_arguments", []),
                fallback_positions=data.get("fallback_positions", []),
                tips=tips,
                german_culture_notes=data.get("german_culture_notes", []),
                common_objections=data.get("common_objections", []),
            )

        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error in negotiation strategy: %s", e)
            return get_fallback_negotiation_strategy(target_salary, current_salary, "")
