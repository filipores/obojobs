"""Data models and fallback strategies for salary negotiation coaching."""

from dataclasses import dataclass, field


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


def get_fallback_salary_research(
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
        for key in GERMAN_SALARY_RANGES:
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
    ranges = GERMAN_SALARY_RANGES.get(industry_key, GERMAN_SALARY_RANGES["default"])
    base_min, base_max = ranges.get(level, (50000, 70000))

    # Apply regional adjustment
    region_lower = region.lower().replace(" ", "")
    adjustment = REGIONAL_ADJUSTMENTS.get(region_lower, REGIONAL_ADJUSTMENTS["default"])

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


def get_fallback_negotiation_strategy(
    target_salary: int,
    current_salary: int | None,
    position: str,
) -> NegotiationStrategy:
    """Generate fallback negotiation strategy without API."""
    recommended_min = int(target_salary * 0.95)
    recommended_max = int(target_salary * 1.1)

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
            example_script=f"Basierend auf meiner Erfahrung und den Marktdaten liegt meine Gehaltsvorstellung bei {target_formatted}\u20ac bis {int(target_salary * 1.1):,}\u20ac.".replace(
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

    opening = f"Basierend auf meiner {position}-Erfahrung und den aktuellen Marktdaten liegt meine Gehaltsvorstellung bei {target_formatted}\u20ac."

    counter_arguments = [
        "Ich bringe X Jahre Erfahrung in diesem Bereich mit, die direkt auf diese Position übertragbar sind.",
        "In meiner letzten Position konnte ich nachweisbare Erfolge erzielen, die einen Mehrwert für Ihr Unternehmen bringen.",
        "Die Marktdaten zeigen, dass vergleichbare Positionen in dieser Region bei diesem Gehaltsniveau liegen.",
    ]

    fallback_positions = [
        "Wenn das Grundgehalt festgelegt ist, wäre ein Signing-Bonus eine Option.",
        "Eine Gehaltsüberprüfung nach 6 Monaten mit konkreten Zielen wäre akzeptabel.",
        "Zusätzliche Benefits wie Home-Office-Tage oder Weiterbildungsbudget könnten das Paket attraktiver machen.",
    ]

    german_culture_notes = [
        "In Deutschland ist es üblich, dass das Gehalt erst nach dem fachlichen Interview besprochen wird.",
        "Sachliche Argumente und Marktdaten sind überzeugender als persönliche Bedürfnisse.",
        "Das Gesamtpaket (Urlaub, Bonus, Benefits) ist oft verhandelbar, auch wenn das Grundgehalt fix ist.",
        "Bei tarifgebundenen Unternehmen sind die Gehaltsbänder oft festgelegt, aber die Eingruppierung verhandelbar.",
    ]

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
