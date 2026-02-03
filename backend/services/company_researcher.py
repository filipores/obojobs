"""
Company Researcher Service - Gathers public information about companies for interview preparation.

Uses web scraping to collect company data from their website (About/Über uns page)
and provides structured information for interview preparation.
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


class CompanyResearchResult:
    """Data class for company research results."""

    def __init__(
        self,
        company_name: str,
        website_url: str | None = None,
        industry: str | None = None,
        company_size: str | None = None,
        locations: list[str] | None = None,
        products_services: list[str] | None = None,
        about_text: str | None = None,
        mission_values: str | None = None,
        founded_year: str | None = None,
        interview_tips: list[str] | None = None,
        source_urls: list[str] | None = None,
        cached_at: str | None = None,
    ):
        self.company_name = company_name
        self.website_url = website_url
        self.industry = industry
        self.company_size = company_size
        self.locations = locations or []
        self.products_services = products_services or []
        self.about_text = about_text
        self.mission_values = mission_values
        self.founded_year = founded_year
        self.interview_tips = interview_tips or []
        self.source_urls = source_urls or []
        self.cached_at = cached_at

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "company_name": self.company_name,
            "website_url": self.website_url,
            "industry": self.industry,
            "company_size": self.company_size,
            "locations": self.locations,
            "products_services": self.products_services,
            "about_text": self.about_text,
            "mission_values": self.mission_values,
            "founded_year": self.founded_year,
            "interview_tips": self.interview_tips,
            "source_urls": self.source_urls,
            "cached_at": self.cached_at,
        }


class CompanyResearcher:
    """Service to gather public information about companies for interview preparation."""

    # Cache directory for company research results
    CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache", "companies")
    CACHE_DURATION_HOURS = 24

    # HTTP headers for scraping
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }

    # About page URL patterns to look for
    ABOUT_PAGE_PATTERNS = [
        "/ueber-uns",
        "/uber-uns",
        "/about-us",
        "/about",
        "/unternehmen",
        "/company",
        "/wir-ueber-uns",
        "/das-unternehmen",
        "/profil",
        "/profile",
    ]

    # Career/Jobs page patterns
    CAREER_PAGE_PATTERNS = [
        "/karriere",
        "/jobs",
        "/careers",
        "/stellenangebote",
        "/arbeiten-bei-uns",
    ]

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        # Ensure cache directory exists
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _get_cache_key(self, company_name: str) -> str:
        """Generate a cache key for a company name."""
        normalized = company_name.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_cache_path(self, company_name: str) -> str:
        """Get the cache file path for a company."""
        cache_key = self._get_cache_key(company_name)
        return os.path.join(self.CACHE_DIR, f"{cache_key}.json")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cached data is still valid (within 24h)."""
        if not os.path.exists(cache_path):
            return False

        try:
            with open(cache_path, encoding="utf-8") as f:
                cached_data = json.load(f)

            cached_at = cached_data.get("cached_at")
            if not cached_at:
                return False

            cached_time = datetime.fromisoformat(cached_at)
            expiry_time = cached_time + timedelta(hours=self.CACHE_DURATION_HOURS)

            return datetime.now() < expiry_time
        except (json.JSONDecodeError, ValueError, OSError):
            return False

    def _load_from_cache(self, company_name: str) -> CompanyResearchResult | None:
        """Load company research from cache if valid."""
        cache_path = self._get_cache_path(company_name)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, encoding="utf-8") as f:
                cached_data = json.load(f)

            return CompanyResearchResult(
                company_name=cached_data.get("company_name", company_name),
                website_url=cached_data.get("website_url"),
                industry=cached_data.get("industry"),
                company_size=cached_data.get("company_size"),
                locations=cached_data.get("locations", []),
                products_services=cached_data.get("products_services", []),
                about_text=cached_data.get("about_text"),
                mission_values=cached_data.get("mission_values"),
                founded_year=cached_data.get("founded_year"),
                interview_tips=cached_data.get("interview_tips", []),
                source_urls=cached_data.get("source_urls", []),
                cached_at=cached_data.get("cached_at"),
            )
        except (json.JSONDecodeError, OSError):
            return None

    def _save_to_cache(self, result: CompanyResearchResult) -> None:
        """Save company research result to cache."""
        cache_path = self._get_cache_path(result.company_name)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # Cache write failures are non-critical

    def _guess_company_website(self, company_name: str) -> str | None:
        """Try to guess the company website URL from the company name."""
        # Normalize company name for URL guessing
        normalized = company_name.lower().strip()

        # Remove common suffixes
        for suffix in [" gmbh", " ag", " se", " kg", " co.", " inc.", " ltd.", " & co"]:
            normalized = normalized.replace(suffix, "")

        # Replace special characters
        normalized = re.sub(r"[^a-z0-9]", "", normalized)

        if not normalized:
            return None

        # Try common domain patterns
        domains_to_try = [
            f"https://www.{normalized}.de",
            f"https://www.{normalized}.com",
            f"https://{normalized}.de",
            f"https://{normalized}.com",
        ]

        for domain in domains_to_try:
            try:
                response = self.session.head(domain, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    return response.url
            except requests.RequestException:
                continue

        return None

    def _find_about_page(self, base_url: str, soup: BeautifulSoup) -> str | None:
        """Find the About/Über uns page URL from the homepage."""
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Look for links in the page
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").lower()
            link_text = link.get_text(strip=True).lower()

            # Check if href or link text matches about page patterns
            for pattern in self.ABOUT_PAGE_PATTERNS:
                if pattern in href or any(
                    keyword in link_text for keyword in ["über uns", "about", "unternehmen", "wir sind"]
                ):
                    link_href = link.get("href")
                    if isinstance(link_href, str):
                        return urljoin(base_url, link_href)
                    return None

        # Fallback: try common about page URLs directly
        for pattern in self.ABOUT_PAGE_PATTERNS:
            try:
                url = urljoin(base, pattern)
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    return url
            except requests.RequestException:
                continue

        return None

    def _extract_about_info(self, soup: BeautifulSoup, url: str) -> dict[str, str | list[str] | None]:
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

    def _extract_products_services(self, soup: BeautifulSoup, text: str) -> list[str]:
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

    def _determine_industry(self, text: str, about_text: str | None) -> str | None:
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

    def _generate_interview_tips(self, result: CompanyResearchResult) -> list[str]:
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

    def research_company(self, company_name: str, website_url: str | None = None) -> CompanyResearchResult:
        """
        Research a company and gather public information.

        Args:
            company_name: Name of the company to research
            website_url: Optional URL of the company website

        Returns:
            CompanyResearchResult with gathered information
        """
        # Check cache first
        cached_result = self._load_from_cache(company_name)
        if cached_result:
            return cached_result

        # Initialize result
        result = CompanyResearchResult(
            company_name=company_name,
            cached_at=datetime.now().isoformat(),
        )

        source_urls = []

        # Try to get or guess website URL
        if not website_url:
            website_url = self._guess_company_website(company_name)

        if website_url:
            result.website_url = website_url
            source_urls.append(website_url)

            try:
                # Fetch homepage
                response = self.session.get(website_url, timeout=self.timeout)
                response.raise_for_status()

                # Fix encoding - prefer UTF-8, fallback to apparent_encoding
                if response.apparent_encoding and response.apparent_encoding.lower() not in ["ascii", "none"]:
                    response.encoding = response.apparent_encoding
                else:
                    response.encoding = "utf-8"

                soup = BeautifulSoup(response.text, "html.parser")

                # Extract basic info from homepage
                homepage_text = soup.get_text(separator="\n", strip=True)
                result.industry = self._determine_industry(homepage_text, None)
                result.products_services = self._extract_products_services(soup, homepage_text)

                # Try to find and fetch About page
                about_url = self._find_about_page(website_url, soup)
                if about_url and about_url != website_url:
                    source_urls.append(about_url)

                    # Small delay to be polite
                    time.sleep(0.5)

                    about_response = self.session.get(about_url, timeout=self.timeout)
                    if about_response.status_code < 400:
                        # Fix encoding - prefer UTF-8, fallback to apparent_encoding
                        if about_response.apparent_encoding and about_response.apparent_encoding.lower() not in [
                            "ascii",
                            "none",
                        ]:
                            about_response.encoding = about_response.apparent_encoding
                        else:
                            about_response.encoding = "utf-8"

                        about_soup = BeautifulSoup(about_response.text, "html.parser")

                        about_info = self._extract_about_info(about_soup, about_url)
                        about_text_val = about_info.get("about_text")
                        if isinstance(about_text_val, str) or about_text_val is None:
                            result.about_text = about_text_val
                        mission_val = about_info.get("mission_values")
                        if isinstance(mission_val, str) or mission_val is None:
                            result.mission_values = mission_val
                        founded_val = about_info.get("founded_year")
                        if isinstance(founded_val, str) or founded_val is None:
                            result.founded_year = founded_val
                        size_val = about_info.get("company_size")
                        if isinstance(size_val, str) or size_val is None:
                            result.company_size = size_val
                        locations_val = about_info.get("locations")
                        if isinstance(locations_val, list):
                            result.locations = locations_val

                        # Re-determine industry with about text
                        if not result.industry and result.about_text:
                            result.industry = self._determine_industry(homepage_text, result.about_text)

            except requests.RequestException:
                # Website fetch failed - continue with limited data
                pass

        # Generate interview tips based on gathered info
        result.interview_tips = self._generate_interview_tips(result)
        result.source_urls = source_urls

        # Cache the result
        self._save_to_cache(result)

        return result

    def research_from_job_posting(self, company_name: str, job_url: str | None = None) -> CompanyResearchResult:
        """
        Research a company from a job posting URL.

        Extracts company website from job posting if possible,
        then performs full research.

        Args:
            company_name: Name of the company
            job_url: URL of the job posting (optional)

        Returns:
            CompanyResearchResult with gathered information
        """
        website_url = None

        if job_url:
            # Try to extract company website from job posting
            try:
                response = self.session.get(job_url, timeout=self.timeout)
                if response.status_code < 400:
                    # Fix encoding - prefer UTF-8, fallback to apparent_encoding
                    if response.apparent_encoding and response.apparent_encoding.lower() not in ["ascii", "none"]:
                        response.encoding = response.apparent_encoding
                    else:
                        response.encoding = "utf-8"

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Look for company website links in job posting
                    for link in soup.find_all("a", href=True):
                        href = link.get("href", "")
                        link_text = link.get_text(strip=True).lower()

                        # Check if this looks like a company website link
                        if any(
                            keyword in link_text
                            for keyword in ["website", "homepage", "zur firma", "unternehmenswebsite"]
                        ):
                            if href.startswith("http"):
                                website_url = href
                                break

                        # Check if href contains company name
                        if company_name.lower().replace(" ", "").replace("-", "") in href.lower().replace("-", ""):
                            if href.startswith("http") and not any(
                                portal in href for portal in ["indeed", "stepstone", "xing", "linkedin"]
                            ):
                                website_url = href
                                break

            except requests.RequestException:
                pass

        return self.research_company(company_name, website_url)
