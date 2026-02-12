"""
Company Researcher Service - Gathers public information about companies for interview preparation.

Uses web scraping to collect company data from their website (About/Über uns page)
and provides structured information for interview preparation.
"""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from services.company_research_extraction import (
    determine_industry,
    extract_about_info,
    extract_products_services,
    generate_interview_tips,
)
from services.company_research_models import CompanyResearchResult


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
        import re

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
        """Find the About/Uber uns page URL from the homepage."""
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
                result.industry = determine_industry(homepage_text, None)
                result.products_services = extract_products_services(soup, homepage_text)

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

                        about_info = extract_about_info(about_soup, about_url)
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
                            result.industry = determine_industry(homepage_text, result.about_text)

            except requests.RequestException:
                # Website fetch failed - continue with limited data
                pass

        # Generate interview tips based on gathered info
        result.interview_tips = generate_interview_tips(result)
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
                        ) and href.startswith("http"):
                            website_url = href
                            break

                        # Check if href contains company name
                        if (
                            company_name.lower().replace(" ", "").replace("-", "") in href.lower().replace("-", "")
                            and href.startswith("http")
                            and not any(portal in href for portal in ["indeed", "stepstone", "xing", "linkedin"])
                        ):
                            website_url = href
                            break

            except requests.RequestException:
                pass

        return self.research_company(company_name, website_url)
