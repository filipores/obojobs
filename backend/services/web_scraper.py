import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class JobBoardParser(ABC):
    """Abstract base class for job board specific parsers."""

    @staticmethod
    @abstractmethod
    def matches_url(url: str) -> bool:
        """Check if this parser can handle the given URL."""
        pass

    @abstractmethod
    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse the job posting and return structured data."""
        pass


class IndeedParser(JobBoardParser):
    """Parser for Indeed.de job postings."""

    # Anti-bot headers for Indeed
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if URL is an Indeed job posting."""
        parsed = urlparse(url)
        hostname = parsed.netloc.lower().replace("www.", "")
        # Match de.indeed.com/viewjob* and indeed.com/viewjob* patterns
        # Also match /jobs/ and /job/ URLs (alternative formats)
        is_indeed = hostname in ["de.indeed.com", "indeed.com", "indeed.de"]
        is_job_page = (
            "/viewjob" in parsed.path
            or "/job/" in parsed.path
            or "/jobs/" in parsed.path
            or "jk=" in parsed.query  # Job key parameter
        )
        return is_indeed and is_job_page

    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse Indeed job posting."""
        result = {
            "source": "indeed",
            "url": url,
            "title": None,
            "company": None,
            "location": None,
            "description": None,
            "requirements": None,
            "contact_email": None,
            "posted_date": None,
            "application_deadline": None,
            "employment_type": None,
            "salary": None,
        }

        # Try JSON-LD first (Indeed sometimes has structured data)
        json_ld_data = self._extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Parse HTML for additional/fallback data
        result = self._parse_html(soup, result)

        return result

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict | None:
        """Extract JSON-LD structured data from page."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            return item
                elif data.get("@type") == "JobPosting":
                    return data
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    def _parse_json_ld(self, data: dict, result: dict) -> dict:
        """Parse JSON-LD JobPosting data into result dict."""
        result["title"] = data.get("title")
        result["description"] = data.get("description")

        # Company info
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            result["company"] = hiring_org.get("name")

        # Location
        job_location = data.get("jobLocation", {})
        if isinstance(job_location, dict):
            address = job_location.get("address", {})
            if isinstance(address, dict):
                parts = []
                if address.get("addressLocality"):
                    parts.append(address["addressLocality"])
                if address.get("addressRegion"):
                    parts.append(address["addressRegion"])
                if address.get("postalCode"):
                    parts.append(address["postalCode"])
                result["location"] = ", ".join(parts) if parts else None
            elif isinstance(address, str):
                result["location"] = address
        elif isinstance(job_location, list) and job_location:
            locations = []
            for loc in job_location:
                if isinstance(loc, dict):
                    addr = loc.get("address", {})
                    if isinstance(addr, dict) and addr.get("addressLocality"):
                        locations.append(addr["addressLocality"])
            result["location"] = ", ".join(locations) if locations else None

        # Dates
        result["posted_date"] = self._parse_date(data.get("datePosted"))

        # Employment type
        emp_type = data.get("employmentType")
        if emp_type:
            if isinstance(emp_type, list):
                result["employment_type"] = ", ".join(emp_type)
            else:
                result["employment_type"] = emp_type

        # Salary
        salary = data.get("baseSalary", {})
        if isinstance(salary, dict):
            value = salary.get("value", {})
            if isinstance(value, dict):
                min_val = value.get("minValue")
                max_val = value.get("maxValue")
                currency = salary.get("currency", "EUR")
                if min_val and max_val:
                    result["salary"] = f"{min_val}-{max_val} {currency}"
                elif min_val:
                    result["salary"] = f"ab {min_val} {currency}"

        return result

    def _parse_html(self, soup: BeautifulSoup, result: dict) -> dict:
        """Parse HTML for Indeed-specific elements."""
        # Title - Indeed uses specific selectors
        if not result["title"]:
            # Try data-testid first (modern Indeed)
            title_elem = soup.find(attrs={"data-testid": "jobsearch-JobInfoHeader-title"})
            if not title_elem:
                title_elem = soup.find("h1", class_=re.compile(r"jobsearch-JobInfoHeader"))
            if not title_elem:
                title_elem = soup.find("h1")
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company name
        if not result["company"]:
            company_elem = soup.find(attrs={"data-testid": "inlineHeader-companyName"})
            if not company_elem:
                company_elem = soup.find(attrs={"data-testid": "company-name"})
            if not company_elem:
                company_elem = soup.find(class_=re.compile(r"companyName"))
            if company_elem:
                # Company name might be in a link
                company_link = company_elem.find("a")
                if company_link:
                    result["company"] = company_link.get_text(strip=True)
                else:
                    result["company"] = company_elem.get_text(strip=True)

        # Location
        if not result["location"]:
            location_elem = soup.find(attrs={"data-testid": "inlineHeader-companyLocation"})
            if not location_elem:
                location_elem = soup.find(attrs={"data-testid": "job-location"})
            if not location_elem:
                location_elem = soup.find(class_=re.compile(r"companyLocation"))
            if location_elem:
                result["location"] = location_elem.get_text(strip=True)

        # Salary - Indeed often shows salary in a specific section
        if not result["salary"]:
            salary_elem = soup.find(attrs={"data-testid": "attribute_snippet_testid"})
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                # Check if it's a salary (contains € or EUR or numbers with ranges)
                if "€" in salary_text or "EUR" in salary_text or re.search(r"\d+.*[-–]\s*\d+", salary_text):
                    result["salary"] = salary_text
            # Fallback: look for salary patterns in meta or specific divs
            if not result["salary"]:
                salary_pattern = re.compile(r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*[-–]\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)", re.IGNORECASE)
                for elem in soup.find_all(class_=re.compile(r"salary|gehalt", re.I)):
                    text = elem.get_text(strip=True)
                    match = salary_pattern.search(text)
                    if match:
                        result["salary"] = match.group(1)
                        break

        # Job Type (Vollzeit, Teilzeit, etc.)
        if not result["employment_type"]:
            # Indeed shows job type in metadata section
            job_type_elem = soup.find(attrs={"data-testid": "jobsearch-JobMetadataFooter"})
            if job_type_elem:
                text = job_type_elem.get_text(strip=True).lower()
                job_types = []
                type_mapping = {
                    "vollzeit": "Vollzeit",
                    "full-time": "Vollzeit",
                    "teilzeit": "Teilzeit",
                    "part-time": "Teilzeit",
                    "festanstellung": "Festanstellung",
                    "permanent": "Festanstellung",
                    "befristet": "Befristet",
                    "temporary": "Befristet",
                    "minijob": "Minijob",
                    "praktikum": "Praktikum",
                    "internship": "Praktikum",
                    "freelance": "Freelance",
                    "remote": "Remote",
                    "homeoffice": "Homeoffice",
                }
                for keyword, label in type_mapping.items():
                    if keyword in text and label not in job_types:
                        job_types.append(label)
                if job_types:
                    result["employment_type"] = ", ".join(job_types)

            # Fallback: search in specific attribute spans
            if not result["employment_type"]:
                for span in soup.find_all("span", class_=re.compile(r"attribute")):
                    text = span.get_text(strip=True).lower()
                    for keyword in ["vollzeit", "teilzeit", "festanstellung", "befristet"]:
                        if keyword in text:
                            result["employment_type"] = text.capitalize()
                            break

        # Description - main job description content
        if not result["description"]:
            desc_elem = soup.find(attrs={"id": "jobDescriptionText"})
            if not desc_elem:
                desc_elem = soup.find(attrs={"data-testid": "jobDescriptionText"})
            if not desc_elem:
                desc_elem = soup.find(class_=re.compile(r"jobsearch-jobDescriptionText"))
            if desc_elem:
                result["description"] = desc_elem.get_text(separator="\n", strip=True)

        # Contact email - search in entire page
        if not result["contact_email"]:
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            page_text = soup.get_text()
            emails = email_pattern.findall(page_text)
            # Filter out common non-contact emails
            contact_emails = [e for e in emails if not any(
                x in e.lower() for x in ["noreply", "no-reply", "newsletter", "support@indeed", "info@indeed"]
            )]
            if contact_emails:
                result["contact_email"] = contact_emails[0]

        return result

    def _parse_date(self, date_str: str | None) -> str | None:
        """Parse date string to standardized format."""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return date_str


class StepStoneParser(JobBoardParser):
    """Parser for StepStone.de job postings."""

    @staticmethod
    def matches_url(url: str) -> bool:
        """Check if URL is a StepStone job posting."""
        parsed = urlparse(url)
        hostname = parsed.netloc.lower().replace("www.", "")
        # Match stepstone.de/stellenangebote--* pattern
        return hostname == "stepstone.de" and "/stellenangebote--" in parsed.path

    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse StepStone job posting, preferring JSON-LD over HTML."""
        result = {
            "source": "stepstone",
            "url": url,
            "title": None,
            "company": None,
            "location": None,
            "description": None,
            "requirements": None,
            "contact_email": None,
            "posted_date": None,
            "application_deadline": None,
            "employment_type": None,
            "salary": None,
        }

        # Try JSON-LD first (structured data)
        json_ld_data = self._extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Fallback/supplement with HTML parsing
        result = self._parse_html(soup, result)

        return result

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict | None:
        """Extract JSON-LD structured data from page."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Handle array of JSON-LD objects
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            return item
                elif data.get("@type") == "JobPosting":
                    return data
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    def _parse_json_ld(self, data: dict, result: dict) -> dict:
        """Parse JSON-LD JobPosting data into result dict."""
        result["title"] = data.get("title")
        result["description"] = data.get("description")

        # Company info
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            result["company"] = hiring_org.get("name")

        # Location
        job_location = data.get("jobLocation", {})
        if isinstance(job_location, dict):
            address = job_location.get("address", {})
            if isinstance(address, dict):
                parts = []
                if address.get("streetAddress"):
                    parts.append(address["streetAddress"])
                if address.get("postalCode"):
                    parts.append(address["postalCode"])
                if address.get("addressLocality"):
                    parts.append(address["addressLocality"])
                if address.get("addressRegion"):
                    parts.append(address["addressRegion"])
                result["location"] = ", ".join(parts) if parts else None
            elif isinstance(address, str):
                result["location"] = address
        elif isinstance(job_location, list) and job_location:
            # Multiple locations
            locations = []
            for loc in job_location:
                if isinstance(loc, dict):
                    addr = loc.get("address", {})
                    if isinstance(addr, dict) and addr.get("addressLocality"):
                        locations.append(addr["addressLocality"])
            result["location"] = ", ".join(locations) if locations else None

        # Dates
        result["posted_date"] = self._parse_date(data.get("datePosted"))
        result["application_deadline"] = self._parse_date(data.get("validThrough"))

        # Employment type
        emp_type = data.get("employmentType")
        if emp_type:
            if isinstance(emp_type, list):
                result["employment_type"] = ", ".join(emp_type)
            else:
                result["employment_type"] = emp_type

        # Salary
        salary = data.get("baseSalary", {})
        if isinstance(salary, dict):
            value = salary.get("value", {})
            if isinstance(value, dict):
                min_val = value.get("minValue")
                max_val = value.get("maxValue")
                currency = salary.get("currency", "EUR")
                if min_val and max_val:
                    result["salary"] = f"{min_val}-{max_val} {currency}"
                elif min_val:
                    result["salary"] = f"ab {min_val} {currency}"

        return result

    def _parse_html(self, soup: BeautifulSoup, result: dict) -> dict:
        """Parse HTML as fallback or to supplement JSON-LD data."""
        # Title fallback
        if not result["title"]:
            title_elem = soup.find("h1")
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company fallback - look for common patterns
        if not result["company"]:
            # StepStone often has company in data attributes or specific classes
            company_elem = soup.find(attrs={"data-at": "header-company-name"})
            if company_elem:
                result["company"] = company_elem.get_text(strip=True)
            else:
                # Try meta tag
                meta_company = soup.find("meta", property="og:site_name")
                if meta_company and meta_company.get("content"):
                    result["company"] = meta_company["content"]

        # Location fallback
        if not result["location"]:
            location_elem = soup.find(attrs={"data-at": "header-job-location"})
            if location_elem:
                result["location"] = location_elem.get_text(strip=True)

        # Description - try to get the job description section
        if not result["description"]:
            desc_section = soup.find(attrs={"data-at": "job-ad-content"})
            if desc_section:
                result["description"] = desc_section.get_text(separator="\n", strip=True)
            else:
                # Fallback: look for article or main content
                article = soup.find("article") or soup.find("main")
                if article:
                    result["description"] = article.get_text(separator="\n", strip=True)

        # Requirements - often in a separate section
        if not result["requirements"]:
            req_section = soup.find(string=re.compile(r"(Anforderungen|Requirements|Profil)", re.I))
            if req_section:
                parent = req_section.find_parent(["div", "section"])
                if parent:
                    result["requirements"] = parent.get_text(separator="\n", strip=True)

        # Contact email - search in entire page
        if not result["contact_email"]:
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            page_text = soup.get_text()
            emails = email_pattern.findall(page_text)
            # Filter out common non-contact emails
            contact_emails = [e for e in emails if not any(
                x in e.lower() for x in ["noreply", "no-reply", "newsletter", "support@stepstone"]
            )]
            if contact_emails:
                result["contact_email"] = contact_emails[0]

        return result

    def _parse_date(self, date_str: str | None) -> str | None:
        """Parse date string to standardized format."""
        if not date_str:
            return None
        try:
            # Try ISO format first
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return date_str


# Registry of available job board parsers
JOB_BOARD_PARSERS: list[type[JobBoardParser]] = [
    IndeedParser,
    StepStoneParser,
]


class WebScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )

    def detect_job_board(self, url: str) -> str | None:
        """Detect which job board a URL belongs to."""
        for parser_class in JOB_BOARD_PARSERS:
            if parser_class.matches_url(url):
                return parser_class.__name__.replace("Parser", "").lower()
        return None

    def fetch_job_posting(self, url: str) -> dict[str, any]:
        """
        Fetched eine Stellenanzeige von einer URL und extrahiert Text + Links.

        Returns:
            Dict mit 'text', 'links', 'email_links', 'application_links'
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
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

    def fetch_structured_job_posting(self, url: str) -> dict[str, any]:
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
        try:
            # Use job-board-specific headers if available
            request_headers = None
            for parser_class in JOB_BOARD_PARSERS:
                if parser_class.matches_url(url) and hasattr(parser_class, "HEADERS"):
                    request_headers = parser_class.HEADERS
                    break

            response = self.session.get(url, timeout=self.timeout, headers=request_headers)
            response.raise_for_status()
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
                for key in ["title", "company", "location", "description", "requirements",
                           "contact_email", "posted_date", "application_deadline",
                           "employment_type", "salary"]:
                    if structured_data.get(key):
                        result[key] = structured_data[key]

            # Use email from links if not found by parser
            if not result["contact_email"] and email_links:
                result["contact_email"] = email_links[0]["email"]

            return result

        except requests.RequestException as e:
            raise Exception(f"Fehler beim Laden der URL: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Fehler beim Parsen der Seite: {str(e)}") from e
