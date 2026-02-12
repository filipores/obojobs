"""
Extraction helpers for Company Researcher Service.

Handles parsing company information from HTML pages: about text, products/services,
industry detection, and interview tip generation.
"""

import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from services.company_research_models import CompanyResearchResult


def extract_about_info(soup: BeautifulSoup, url: str) -> dict[str, str | list[str] | None]:
    """Extract company information from About page."""
    about_text: str | None = None
    mission_values: str | None = None
    founded_year: str | None = None
    company_size: str | None = None
    locations: list[str] = []

    # Remove navigation, header, footer for cleaner text
    for element in soup(["nav", "header", "footer", "script", "style"]):
        element.decompose()

    # Get main text content
    main_content = soup.find("main") or soup.find("article") or soup
    text = main_content.get_text(separator="\n", strip=True)

    # Clean up text (limit length)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines[:100])  # Limit to first 100 lines

    if clean_text and len(clean_text) > 50:
        about_text = clean_text[:2000]  # Limit to 2000 chars

    # Try to extract founded year
    year_pattern = re.compile(r"(?:gegründet|founded|seit|since)[:\s]*(\d{4})", re.I)
    year_match = year_pattern.search(text)
    if year_match:
        founded_year = year_match.group(1)

    # Try to extract company size
    size_patterns = [
        (r"(\d+[\.\d]*)\s*(?:mitarbeiter|employees|beschäftigte)", re.I),
        (r"(?:über|mehr als|more than)\s*(\d+[\.\d]*)\s*(?:mitarbeiter|employees)", re.I),
    ]
    for pattern, flags in size_patterns:
        size_match = re.search(pattern, text, flags)
        if size_match:
            company_size = f"{size_match.group(1)} Mitarbeiter"
            break

    # Try to extract locations from text
    german_cities = [
        "Berlin",
        "Hamburg",
        "München",
        "Köln",
        "Frankfurt",
        "Stuttgart",
        "Düsseldorf",
        "Leipzig",
        "Dresden",
        "Hannover",
        "Nürnberg",
        "Bremen",
        "Essen",
        "Dortmund",
        "Bonn",
    ]
    for city in german_cities:
        if city.lower() in text.lower():
            locations.append(city)

    # Look for mission/vision sections
    mission_keywords = ["mission", "vision", "werte", "values", "philosophie", "leitbild"]
    for keyword in mission_keywords:
        # Find headers or sections with these keywords
        mission_elem = soup.find(["h2", "h3", "h4", "section"], string=re.compile(keyword, re.I))
        if mission_elem:
            # Get the next sibling content
            next_content = mission_elem.find_next(["p", "div", "ul"])
            if next_content:
                mission_text_content = next_content.get_text(strip=True)
                if mission_text_content and len(mission_text_content) > 20:
                    mission_values = mission_text_content[:500]
                    break

    return {
        "about_text": about_text,
        "mission_values": mission_values,
        "founded_year": founded_year,
        "company_size": company_size,
        "locations": locations,
    }


def extract_products_services(soup: BeautifulSoup, text: str) -> list[str]:
    """Extract products/services from page content."""
    products = []

    # Look for product/service sections
    product_keywords = ["produkte", "products", "leistungen", "services", "lösungen", "solutions"]

    for keyword in product_keywords:
        section = soup.find(
            ["h2", "h3", "section", "div"],
            string=re.compile(keyword, re.I),
        )
        if section:
            # Find list items or paragraphs in this section
            parent = section.find_parent(["section", "div"]) or section
            if not isinstance(parent, Tag):
                continue
            items = parent.find_all(["li", "h4", "strong"])
            for item in items[:8]:  # Limit to 8 items
                item_text = item.get_text(strip=True)
                if item_text and len(item_text) > 3 and len(item_text) < 100:
                    products.append(item_text)

    return products[:8] if products else []


def determine_industry(text: str, about_text: str | None) -> str | None:
    """Try to determine the industry from page content."""
    combined = f"{text} {about_text or ''}"
    combined_lower = combined.lower()

    industry_keywords = {
        "Software & IT": [
            "software",
            "it-dienstleistung",
            "saas",
            "cloud",
            "digital",
            "technologie",
        ],
        "E-Commerce": ["e-commerce", "online-shop", "online-handel", "webshop"],
        "Finanzdienstleistungen": [
            "bank",
            "finanz",
            "versicherung",
            "investment",
            "fintech",
        ],
        "Beratung": ["beratung", "consulting", "unternehmensberatung"],
        "Industrie & Fertigung": [
            "fertigung",
            "produktion",
            "maschinen",
            "industrie",
            "automotive",
        ],
        "Gesundheitswesen": [
            "gesundheit",
            "medizin",
            "pharma",
            "klinik",
            "healthcare",
        ],
        "Einzelhandel": ["einzelhandel", "retail", "geschäft", "filiale"],
        "Logistik": ["logistik", "transport", "spedition", "lieferung"],
        "Medien & Marketing": ["medien", "marketing", "agentur", "werbung", "media"],
        "Energie": ["energie", "strom", "erneuerbar", "solar", "wind"],
        "Telekommunikation": ["telekommunikation", "telecom", "mobilfunk", "netz"],
    }

    for industry, keywords in industry_keywords.items():
        if any(keyword in combined_lower for keyword in keywords):
            return industry

    return None


def generate_interview_tips(result: CompanyResearchResult) -> list[str]:
    """Generate interview tips based on gathered company information."""
    tips = []

    # Tip about company knowledge
    tips.append(
        f"Zeigen Sie, dass Sie sich über {result.company_name} informiert haben - "
        "erwähnen Sie spezifische Fakten aus Ihrer Recherche."
    )

    # Industry-specific tip
    if result.industry:
        tips.append(
            f"Die Firma ist in der Branche '{result.industry}' tätig. "
            "Informieren Sie sich über aktuelle Trends und Herausforderungen in diesem Bereich."
        )

    # Products/Services tip
    if result.products_services:
        products_str = ", ".join(result.products_services[:3])
        tips.append(
            f"Das Unternehmen bietet folgende Produkte/Dienstleistungen: {products_str}. "
            "Überlegen Sie, wie Ihre Fähigkeiten dazu beitragen können."
        )

    # Mission/Values tip
    if result.mission_values:
        tips.append(
            "Das Unternehmen hat bestimmte Werte und eine Mission. "
            "Beziehen Sie sich in Ihren Antworten auf diese Werte und zeigen Sie, dass Sie diese teilen."
        )

    # Company size tip
    if result.company_size:
        # Determine company size category
        size_category = "mittelständisches"
        if "über" in result.company_size.lower():
            size_category = "größeres"
        else:
            size_match = re.search(r"\d+", result.company_size)
            if size_match and int(size_match.group()) > 500:
                size_category = "größeres"
        tips.append(
            f"Mit {result.company_size} ist dies ein {size_category} Unternehmen. "
            "Erwarten Sie entsprechende Strukturen und Prozesse."
        )

    # Founded year tip
    if result.founded_year:
        try:
            year = int(result.founded_year)
            age = datetime.now().year - year
            if age > 50:
                tips.append(
                    f"Das Unternehmen wurde {result.founded_year} gegründet und hat eine lange Tradition. "
                    "Betonen Sie Ihre Wertschätzung für etablierte Prozesse und Unternehmenskultur."
                )
            elif age < 10:
                tips.append(
                    f"Als {age}-jähriges Unternehmen ist die Firma noch relativ jung. "
                    "Zeigen Sie Flexibilität und Bereitschaft, in einem dynamischen Umfeld zu arbeiten."
                )
        except ValueError:
            pass

    # Generic tips
    tips.append("Bereiten Sie eigene Fragen zum Unternehmen vor - das zeigt echtes Interesse.")

    return tips[:6]  # Limit to 6 tips
