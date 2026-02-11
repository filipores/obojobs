"""
Salary Coach Service - Provides salary negotiation coaching and market research using Claude API.
Supports German salary negotiation culture with personalized tips and negotiation scripts.
"""

import json
import logging
import time
from dataclasses import dataclass, field

from anthropic import Anthropic

from config import config

logger = logging.getLogger(__name__)


@dataclass
class SalaryResearch:
    """Result of salary research for a position."""

    position: str
    region: str
    experience_years: int
    min_salary: int
    max_salary: int
    median_salary: int
    currency: str = "EUR"
    data_sources: list[str] = field(default_factory=list)
    factors: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "region": self.region,
            "experience_years": self.experience_years,
            "min_salary": self.min_salary,
            "max_salary": self.max_salary,
            "median_salary": self.median_salary,
            "currency": self.currency,
            "data_sources": self.data_sources,
            "factors": self.factors,
            "notes": self.notes,
        }


@dataclass
class NegotiationTip:
    """A salary negotiation tip."""

    category: str  # preparation, opening, counter, closing, timing
    title: str
    description: str
    example_script: str
    priority: str = "medium"  # high, medium, low

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "example_script": self.example_script,
            "priority": self.priority,
        }


@dataclass
class NegotiationStrategy:
    """Complete negotiation strategy with tips and scripts."""

    target_salary: int
    current_salary: int | None
    recommended_range: tuple[int, int]
    opening_statement: str
    counter_arguments: list[str]
    fallback_positions: list[str]
    tips: list[NegotiationTip]
    german_culture_notes: list[str]
    common_objections: list[dict]

    def to_dict(self) -> dict:
        return {
            "target_salary": self.target_salary,
            "current_salary": self.current_salary,
            "recommended_range": {
                "min": self.recommended_range[0],
                "max": self.recommended_range[1],
            },
            "opening_statement": self.opening_statement,
            "counter_arguments": self.counter_arguments,
            "fallback_positions": self.fallback_positions,
            "tips": [tip.to_dict() for tip in self.tips],
            "german_culture_notes": self.german_culture_notes,
            "common_objections": self.common_objections,
        }


class SalaryCoach:
    """Service for salary negotiation coaching using Claude API."""

    # German salary ranges by industry and experience (approximate, in EUR)
    GERMAN_SALARY_RANGES = {
        "software": {
            "junior": (45000, 55000),
            "mid": (55000, 75000),
            "senior": (75000, 100000),
            "lead": (90000, 130000),
        },
        "marketing": {
            "junior": (35000, 45000),
            "mid": (45000, 60000),
            "senior": (60000, 85000),
            "lead": (80000, 110000),
        },
        "finance": {
            "junior": (45000, 55000),
            "mid": (55000, 75000),
            "senior": (75000, 110000),
            "lead": (100000, 150000),
        },
        "sales": {
            "junior": (40000, 50000),
            "mid": (50000, 70000),
            "senior": (70000, 100000),
            "lead": (90000, 140000),
        },
        "hr": {
            "junior": (38000, 48000),
            "mid": (48000, 65000),
            "senior": (65000, 90000),
            "lead": (85000, 120000),
        },
        "default": {
            "junior": (40000, 50000),
            "mid": (50000, 70000),
            "senior": (70000, 95000),
            "lead": (90000, 130000),
        },
    }

    # Regional salary adjustments (relative to national average)
    REGIONAL_ADJUSTMENTS = {
        "muenchen": 1.15,
        "munich": 1.15,
        "münchen": 1.15,
        "frankfurt": 1.12,
        "stuttgart": 1.10,
        "hamburg": 1.08,
        "berlin": 1.05,
        "duesseldorf": 1.05,
        "düsseldorf": 1.05,
        "koeln": 1.03,
        "köln": 1.03,
        "default": 1.00,
    }

    VALID_CATEGORIES = ["preparation", "opening", "counter", "closing", "timing"]

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
                    return self._get_fallback_salary_research(position, region, experience_years, industry)

        return self._get_fallback_salary_research(position, region, experience_years, industry)

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
                    return self._get_fallback_negotiation_strategy(target_salary, current_salary, position)

        return self._get_fallback_negotiation_strategy(target_salary, current_salary, position)

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
        current_context = f"\nAKTUELLES GEHALT: {current_salary:,}€".replace(",", ".") if current_salary else ""
        company_context = f"\nUNTERNEHMEN: {company_name}" if company_name else ""
        offer_context = f"\n\nJOB-DETAILS:\n{job_offer_details}" if job_offer_details else ""

        return f"""Du bist ein erfahrener Karriereberater und Experte für Gehaltsverhandlungen in Deutschland.
Erstelle eine personalisierte Verhandlungsstrategie für folgende Situation:

POSITION: {position}
BERUFSERFAHRUNG: {experience_years} Jahre
WUNSCHGEHALT: {target_salary:,}€{current_context}{company_context}{offer_context}

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
            return self._get_fallback_salary_research(position, region, experience_years, None)

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
            return self._get_fallback_salary_research(position, region, experience_years, None)

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
            return self._get_fallback_negotiation_strategy(target_salary, current_salary, "")

        json_text = text[start_idx : end_idx + 1]

        try:
            data = json.loads(json_text)

            # Parse tips
            tips = []
            for tip_data in data.get("tips", []):
                category = tip_data.get("category", "preparation").lower()
                if category not in self.VALID_CATEGORIES:
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
            return self._get_fallback_negotiation_strategy(target_salary, current_salary, "")

    def _get_fallback_salary_research(
        self,
        position: str,
        region: str,
        experience_years: int,
        industry: str | None,
    ) -> SalaryResearch:
        """Generate fallback salary research without API."""
        # Determine experience level
        if experience_years <= 2:
            level = "junior"
        elif experience_years <= 5:
            level = "mid"
        elif experience_years <= 10:
            level = "senior"
        else:
            level = "lead"

        # Determine industry
        industry_key = "default"
        if industry:
            industry_lower = industry.lower()
            for key in self.GERMAN_SALARY_RANGES:
                if key in industry_lower:
                    industry_key = key
                    break

        # Also check position for industry hints
        position_lower = position.lower()
        if any(kw in position_lower for kw in ["software", "entwickler", "developer", "engineer", "it "]):
            industry_key = "software"
        elif any(kw in position_lower for kw in ["marketing", "brand", "content"]):
            industry_key = "marketing"
        elif any(kw in position_lower for kw in ["finan", "account", "controller"]):
            industry_key = "finance"
        elif any(kw in position_lower for kw in ["sales", "vertrieb", "account manager"]):
            industry_key = "sales"
        elif any(kw in position_lower for kw in ["hr", "personal", "recruiting"]):
            industry_key = "hr"

        # Get base salary range
        ranges = self.GERMAN_SALARY_RANGES.get(industry_key, self.GERMAN_SALARY_RANGES["default"])
        base_min, base_max = ranges.get(level, (50000, 70000))

        # Apply regional adjustment
        region_lower = region.lower().replace(" ", "")
        adjustment = self.REGIONAL_ADJUSTMENTS.get(region_lower, self.REGIONAL_ADJUSTMENTS["default"])

        min_salary = int(base_min * adjustment)
        max_salary = int(base_max * adjustment)
        median_salary = int((min_salary + max_salary) / 2)

        return SalaryResearch(
            position=position,
            region=region,
            experience_years=experience_years,
            min_salary=min_salary,
            max_salary=max_salary,
            median_salary=median_salary,
            currency="EUR",
            data_sources=[
                "Branchendurchschnitt Deutschland",
                "Regionale Gehaltsanpassung",
            ],
            factors=[
                f"Erfahrungslevel: {level}",
                f"Regionale Anpassung: {int(adjustment * 100)}%",
                f"Branche: {industry_key}",
            ],
            notes="Diese Schätzung basiert auf allgemeinen Marktdaten. Für genauere Werte empfehlen wir Gehaltsportale wie Stepstone, Kununu oder Glassdoor zu konsultieren.",
        )

    def _get_fallback_negotiation_strategy(
        self,
        target_salary: int,
        current_salary: int | None,
        position: str,
    ) -> NegotiationStrategy:
        """Generate fallback negotiation strategy without API."""
        # Calculate recommended range
        recommended_min = int(target_salary * 0.95)
        recommended_max = int(target_salary * 1.1)

        # Format salary for display
        target_formatted = f"{target_salary:,}".replace(",", ".")

        tips = [
            NegotiationTip(
                category="preparation",
                title="Marktrecherche durchführen",
                description="Recherchieren Sie Gehälter für vergleichbare Positionen auf Stepstone, Kununu und Glassdoor. Dokumentieren Sie Ihre Qualifikationen und Erfolge.",
                example_script="Ich habe den Markt analysiert und sehe, dass vergleichbare Positionen in der Region zwischen X und Y Euro liegen.",
                priority="high",
            ),
            NegotiationTip(
                category="preparation",
                title="Eigene Erfolge quantifizieren",
                description="Listen Sie messbare Erfolge aus Ihrer bisherigen Tätigkeit auf. Zahlen und Fakten überzeugen.",
                example_script="In meiner letzten Position konnte ich den Umsatz um 25% steigern und die Prozesseffizienz um 30% verbessern.",
                priority="high",
            ),
            NegotiationTip(
                category="opening",
                title="Gehaltsspanne nennen",
                description="Nennen Sie eine Gehaltsspanne statt einer fixen Zahl. Setzen Sie die untere Grenze bei Ihrem Wunschgehalt.",
                example_script=f"Basierend auf meiner Erfahrung und den Marktdaten liegt meine Gehaltsvorstellung bei {target_formatted}€ bis {int(target_salary * 1.1):,}€.".replace(
                    ",", "."
                ),
                priority="high",
            ),
            NegotiationTip(
                category="counter",
                title="Bei niedrigem Angebot nachfragen",
                description="Fragen Sie nach der Begründung und zeigen Sie Verhandlungsbereitschaft.",
                example_script="Ich verstehe. Können Sie mir erläutern, wie sich dieses Angebot zusammensetzt? Welche Entwicklungsmöglichkeiten gibt es?",
                priority="medium",
            ),
            NegotiationTip(
                category="counter",
                title="Gesamtpaket verhandeln",
                description="Wenn das Grundgehalt fix ist, verhandeln Sie Benefits: Bonus, Home-Office, Urlaub, Weiterbildung.",
                example_script="Wenn das Grundgehalt festgelegt ist, wären mir flexible Arbeitszeiten und ein höherer Urlaubsanspruch wichtig.",
                priority="medium",
            ),
            NegotiationTip(
                category="closing",
                title="Bedenkzeit erbeten",
                description="Akzeptieren Sie nicht sofort. Bitten Sie um Zeit zum Nachdenken.",
                example_script="Vielen Dank für das Angebot. Ich würde gerne noch eine Nacht darüber schlafen und mich morgen melden.",
                priority="medium",
            ),
            NegotiationTip(
                category="timing",
                title="Richtiger Zeitpunkt",
                description="In Deutschland wird das Gehalt meist erst im 2. oder 3. Gespräch besprochen. Warten Sie, bis der Arbeitgeber das Thema anspricht.",
                example_script="Ich freue mich, dass wir über die Konditionen sprechen. Bevor wir das Gehalt besprechen, hätte ich noch eine Frage zu den Aufgaben...",
                priority="low",
            ),
        ]

        # Generate opening statement
        opening = f"Basierend auf meiner {position}-Erfahrung und den aktuellen Marktdaten liegt meine Gehaltsvorstellung bei {target_formatted}€."

        # Counter arguments
        counter_arguments = [
            "Ich bringe X Jahre Erfahrung in diesem Bereich mit, die direkt auf diese Position übertragbar sind.",
            "In meiner letzten Position konnte ich nachweisbare Erfolge erzielen, die einen Mehrwert für Ihr Unternehmen bringen.",
            "Die Marktdaten zeigen, dass vergleichbare Positionen in dieser Region bei diesem Gehaltsniveau liegen.",
        ]

        # Fallback positions
        fallback_positions = [
            "Wenn das Grundgehalt festgelegt ist, wäre ein Signing-Bonus eine Option.",
            "Eine Gehaltsüberprüfung nach 6 Monaten mit konkreten Zielen wäre akzeptabel.",
            "Zusätzliche Benefits wie Home-Office-Tage oder Weiterbildungsbudget könnten das Paket attraktiver machen.",
        ]

        # German culture notes
        german_culture_notes = [
            "In Deutschland ist es üblich, dass das Gehalt erst nach dem fachlichen Interview besprochen wird.",
            "Sachliche Argumente und Marktdaten sind überzeugender als persönliche Bedürfnisse.",
            "Das Gesamtpaket (Urlaub, Bonus, Benefits) ist oft verhandelbar, auch wenn das Grundgehalt fix ist.",
            "Bei tarifgebundenen Unternehmen sind die Gehaltsbänder oft festgelegt, aber die Eingruppierung verhandelbar.",
        ]

        # Common objections with responses
        common_objections = [
            {
                "objection": "Das liegt über unserem Budget für diese Position.",
                "response": "Ich verstehe. Könnten wir über eine stufenweise Erhöhung nach der Probezeit sprechen, wenn ich meine Leistung unter Beweis gestellt habe?",
            },
            {
                "objection": "Andere Bewerber haben geringere Gehaltsvorstellungen.",
                "response": "Ich bin überzeugt, dass meine Qualifikationen und Erfahrung einen entsprechenden Mehrwert bringen. Darf ich Ihnen konkret erläutern, was Sie von mir erwarten können?",
            },
            {
                "objection": "Wir haben feste Gehaltsbänder.",
                "response": "Das verstehe ich. Gibt es Spielraum bei anderen Komponenten wie Urlaubstagen, einem Signing-Bonus oder dem Weiterbildungsbudget?",
            },
        ]

        return NegotiationStrategy(
            target_salary=target_salary,
            current_salary=current_salary,
            recommended_range=(recommended_min, recommended_max),
            opening_statement=opening,
            counter_arguments=counter_arguments,
            fallback_positions=fallback_positions,
            tips=tips,
            german_culture_notes=german_culture_notes,
            common_objections=common_objections,
        )
