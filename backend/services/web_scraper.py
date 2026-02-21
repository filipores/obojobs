import logging
import os
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import cloudscraper
import requests
from bs4 import BeautifulSoup

from services.scrapers import (
    ArbeitsagenturParser,
    GenericJobParser,
    IndeedParser,
    JobBoardParser,
    SoftgardenParser,
    StepStoneParser,
    XingParser,
)

# Re-export parser classes for backward compatibility
__all__ = [
    "ArbeitsagenturParser",
    "GenericJobParser",
    "IndeedParser",
    "JobBoardParser",
    "SoftgardenParser",
    "StepStoneParser",
    "WebScraper",
    "XingParser",
]

logger = logging.getLogger(__name__)

# Registry of available job board parsers
JOB_BOARD_PARSERS: list[type[JobBoardParser]] = [
    IndeedParser,
    StepStoneParser,
    XingParser,
    SoftgardenParser,
    ArbeitsagenturParser,
]


class WebScraper:
    SCRAPER_API_BASE = "https://api.scraperapi.com"

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self.scraper_api_key = os.getenv("SCRAPER_API_KEY")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            }
        )

    def _fetch_via_scraper_api(self, url: str) -> requests.Response | None:
        """Fetch a page through ScraperAPI proxy. Returns None if not configured."""
        if not self.scraper_api_key:
            return None
        proxy_url = f"{self.SCRAPER_API_BASE}?api_key={self.scraper_api_key}&url={url}&country_code=de"
        try:
            response = self.session.get(proxy_url, timeout=max(self.timeout, 30))
            response.raise_for_status()
            logger.info("ScraperAPI success for %s", urlparse(url).netloc)
            return response
        except Exception as e:
            logger.warning("ScraperAPI failed for %s: %s", urlparse(url).netloc, e)
            return None

    def _fetch_page(self, url: str, headers: dict | None = None) -> requests.Response:
        """Fetch a page with environment-aware fallback strategy.

        Production (datacenter IP): ScraperAPI -> cloudscraper -> direct (last resort)
        Development (residential IP): direct -> ScraperAPI -> cloudscraper
        """
        is_production = os.getenv("FLASK_ENV") == "production"

        if is_production and self.scraper_api_key:
            return self._fetch_page_production(url, headers)
        return self._fetch_page_dev(url, headers)

    def _fetch_via_cloudscraper(self, url: str) -> requests.Response | None:
        """Fetch a page using cloudscraper for anti-bot bypass. Returns None on failure."""
        logger.info("Trying cloudscraper for %s", urlparse(url).netloc)
        try:
            scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "linux"})
            response = scraper.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except Exception:
            return None

    def _fetch_page_production(self, url: str, headers: dict | None = None) -> requests.Response:
        """Production: ScraperAPI first (datacenter IP gets blocked by job boards)."""
        # Attempt 1: ScraperAPI (residential IP rotation)
        api_response = self._fetch_via_scraper_api(url)
        if api_response is not None:
            return api_response

        # Attempt 2: cloudscraper (anti-bot bypass)
        cs_response = self._fetch_via_cloudscraper(url)
        if cs_response is not None:
            return cs_response

        # Attempt 3: Direct request (last resort)
        logger.info("Trying direct request for %s", urlparse(url).netloc)
        response = self.session.get(url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response

    def _fetch_page_dev(self, url: str, headers: dict | None = None) -> requests.Response:
        """Development: direct request first (residential IP usually works)."""
        # Attempt 1: Direct request
        try:
            response = self.session.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
            return response
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            is_403 = isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code == 403
            is_retriable = isinstance(e, requests.ConnectionError | requests.Timeout) or is_403
            if not is_retriable:
                raise
            logger.info("Direct request to %s failed (%s)", urlparse(url).netloc, type(e).__name__)

            # Attempt 2: ScraperAPI (residential IP rotation)
            api_response = self._fetch_via_scraper_api(url)
            if api_response is not None:
                return api_response

            # Attempt 3: cloudscraper (anti-bot bypass)
            cs_response = self._fetch_via_cloudscraper(url)
            if cs_response is not None:
                return cs_response

            raise e from None  # Re-raise the original error if all attempts fail

    @staticmethod
    def _make_http_error(e: requests.HTTPError) -> Exception:
        """Convert HTTPError to user-friendly German error message."""
        status = e.response.status_code if e.response is not None else 0
        if status == 403:
            return Exception(
                "Die Stellenanzeige konnte nicht geladen werden. Das Job-Portal blockiert möglicherweise den Zugriff. "
                "Bitte kopiere den Text der Stellenanzeige manuell."
            )
        if status == 404:
            return Exception("Stellenanzeige nicht gefunden (404). Bitte überprüfe die URL.")
        if status == 429:
            return Exception("Zu viele Anfragen (429). Bitte warte einen Moment und versuche es erneut.")
        return Exception(f"HTTP-Fehler beim Laden der Stellenanzeige ({status}): {e}")

    @staticmethod
    def _normalize_arbeitsagentur_url(url: str) -> str:
        """Convert Arbeitsagentur search URLs to direct detail URLs.

        The /jobsuche/suche?id={refnr} format loads a JS-based search modal
        that BeautifulSoup cannot parse. The /jobsuche/jobdetail/{refnr} format
        returns a full server-rendered detail page.
        """
        match = re.search(r"arbeitsagentur\.de/jobsuche/suche\?.*?(?:id|refnr)=([^&]+)", url)
        if match:
            refnr = match.group(1)
            return f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"
        return url

    def detect_job_board(self, url: str) -> str | None:
        """Detect which job board a URL belongs to."""
        for parser_class in JOB_BOARD_PARSERS:
            if parser_class.matches_url(url):
                return parser_class.__name__.replace("Parser", "").lower()
        return None

    def fetch_job_posting(self, url: str) -> dict[str, Any]:
        """
        Fetched eine Stellenanzeige von einer URL und extrahiert Text + Links.

        Returns:
            Dict mit 'text', 'links', 'email_links', 'application_links'
        """
        url = self._normalize_arbeitsagentur_url(url)
        try:
            response = self._fetch_page(url)
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # Entferne Script/Style Tags
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Extrahiere Text
            text = soup.get_text(separator="\n", strip=True)

            # Bereinige Text (mehrfache Leerzeilen)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            # Extrahiere alle Links
            all_links = []
            email_links = []
            application_links = []

            for link in soup.find_all("a", href=True):
                href = link["href"]
                link_text = link.get_text(strip=True)

                # Absolute URL
                absolute_url = urljoin(url, href)

                all_links.append({"url": absolute_url, "text": link_text})

                # Email Links
                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").split("?")[0]
                    email_links.append({"email": email, "text": link_text})

                # Bewerbungs-Links (Heuristik)
                if any(
                    keyword in href.lower() or keyword in link_text.lower()
                    for keyword in ["bewerbung", "apply", "application", "bewerben", "job", "karriere"]
                ):
                    application_links.append({"url": absolute_url, "text": link_text})

            return {
                "text": clean_text,
                "all_links": all_links,
                "email_links": email_links,
                "application_links": application_links,
                "source_url": url,
            }

        except requests.HTTPError as e:
            raise self._make_http_error(e) from e
        except (requests.ConnectionError, requests.Timeout) as e:
            raise Exception(
                "Die Stellenanzeige konnte nicht geladen werden. Das Job-Portal blockiert möglicherweise den Zugriff. "
                "Bitte kopiere den Text der Stellenanzeige manuell."
            ) from e
        except requests.RequestException as e:
            raise Exception(f"Fehler beim Laden der URL: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Fehler beim Parsen der Seite: {str(e)}") from e

    def extract_company_name_from_url(self, url: str) -> str:
        """Versucht, Firmennamen aus URL zu extrahieren."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        company = domain.split(".")[0]
        return company.capitalize()

    def fetch_structured_job_posting(self, url: str, _follow_external: bool = True) -> dict[str, Any]:
        """
        Fetched und parst eine Stellenanzeige mit job-board-spezifischem Parser.

        Nutzt spezialisierte Parser für bekannte Job-Boards (StepStone, Indeed, etc.)
        mit JSON-LD Parsing wenn vorhanden und HTML-Fallback.

        Returns:
            Dict mit strukturierten Daten:
            - source: Job-Board Name oder "generic"
            - url: Original URL
            - title: Stellentitel
            - company: Firmenname
            - location: Standort
            - description: Stellenbeschreibung
            - requirements: Anforderungen (falls extrahierbar)
            - contact_email: Kontakt-Email (falls vorhanden)
            - posted_date: Einstellungsdatum
            - application_deadline: Bewerbungsfrist
            - employment_type: Anstellungsart
            - salary: Gehalt (falls angegeben)
            - text: Volltext der Seite (für Kompatibilität)
            - all_links, email_links, application_links: Extrahierte Links
        """
        url = self._normalize_arbeitsagentur_url(url)
        try:
            # Use job-board-specific headers if available
            request_headers = None
            for parser_class in JOB_BOARD_PARSERS:
                if parser_class.matches_url(url) and hasattr(parser_class, "HEADERS"):
                    request_headers = parser_class.HEADERS
                    break

            response = self._fetch_page(url, headers=request_headers)
            response.encoding = response.apparent_encoding

            # Parse HTML - keep original soup for structured parsing
            soup_for_parsing = BeautifulSoup(response.text, "html.parser")

            # Try job-board-specific parser first
            structured_data = None
            for parser_class in JOB_BOARD_PARSERS:
                if parser_class.matches_url(url):
                    parser = parser_class()
                    structured_data = parser.parse(soup_for_parsing, url)
                    break

            # Fallback to generic parser if no specific parser matched
            if not structured_data:
                generic_parser = GenericJobParser()
                structured_data = generic_parser.parse(soup_for_parsing, url)

            # Create clean soup for text extraction (removes scripts etc.)
            soup_for_text = BeautifulSoup(response.text, "html.parser")
            for script in soup_for_text(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Extract clean text
            text = soup_for_text.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            # Extract links from clean soup
            all_links = []
            email_links = []
            application_links = []

            for link in soup_for_text.find_all("a", href=True):
                href = link["href"]
                link_text = link.get_text(strip=True)
                absolute_url = urljoin(url, href)

                all_links.append({"url": absolute_url, "text": link_text})

                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").split("?")[0]
                    email_links.append({"email": email, "text": link_text})

                if any(
                    keyword in href.lower() or keyword in link_text.lower()
                    for keyword in ["bewerbung", "apply", "application", "bewerben", "job", "karriere"]
                ):
                    application_links.append({"url": absolute_url, "text": link_text})

            # Build result combining structured data with generic data
            result = {
                "source": structured_data.get("source", "generic") if structured_data else "generic",
                "url": url,
                "title": None,
                "company": None,
                "location": None,
                "description": None,
                "requirements": None,
                "contact_email": None,
                "contact_person": None,
                "contact_phone": None,
                "posted_date": None,
                "application_deadline": None,
                "employment_type": None,
                "salary": None,
                "text": clean_text,
                "all_links": all_links,
                "email_links": email_links,
                "application_links": application_links,
                "source_url": url,
            }

            # Merge structured data if available
            if structured_data:
                for key in [
                    "title",
                    "company",
                    "location",
                    "description",
                    "requirements",
                    "contact_email",
                    "contact_person",
                    "contact_phone",
                    "posted_date",
                    "application_deadline",
                    "employment_type",
                    "salary",
                ]:
                    if structured_data.get(key):
                        result[key] = structured_data[key]

            # Use email from links if not found by parser
            if not result["contact_email"] and email_links:
                result["contact_email"] = email_links[0]["email"]

            # Enrichment: follow external URLs from Arbeitsagentur to get missing data
            external_url = structured_data.get("external_url") if structured_data else None
            if (
                _follow_external
                and result.get("source") == "arbeitsagentur"
                and not result.get("contact_person")
                and external_url
            ):
                try:
                    logger.info("Following external URL from Arbeitsagentur: %s", external_url)
                    original_timeout = self.timeout
                    self.timeout = 5
                    try:
                        external_data = self.fetch_structured_job_posting(external_url, _follow_external=False)
                    finally:
                        self.timeout = original_timeout
                    # Merge missing fields from external source
                    for key in ["contact_person", "contact_email", "contact_phone", "description"]:
                        if not result.get(key) and external_data.get(key):
                            result[key] = external_data[key]
                except Exception as e:
                    logger.warning("Failed to fetch external URL %s: %s", external_url, e)

            return result

        except requests.HTTPError as e:
            raise self._make_http_error(e) from e
        except (requests.ConnectionError, requests.Timeout) as e:
            raise Exception(
                "Die Stellenanzeige konnte nicht geladen werden. Das Job-Portal blockiert möglicherweise den Zugriff. "
                "Bitte kopiere den Text der Stellenanzeige manuell."
            ) from e
        except requests.RequestException as e:
            raise Exception(f"Fehler beim Laden der URL: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Fehler beim Parsen der Seite: {str(e)}") from e
