import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


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
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
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
                if isinstance(company_link, Tag):
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
                salary_pattern = re.compile(
                    r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*[-–]\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)", re.IGNORECASE
                )
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
            contact_emails = [
                e
                for e in emails
                if not any(
                    x in e.lower() for x in ["noreply", "no-reply", "newsletter", "support@indeed", "info@indeed"]
                )
            ]
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
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
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
                if isinstance(meta_company, Tag):
                    content = meta_company.get("content")
                    if isinstance(content, str):
                        result["company"] = content

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
            contact_emails = [
                e
                for e in emails
                if not any(x in e.lower() for x in ["noreply", "no-reply", "newsletter", "support@stepstone"])
            ]
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


class XingParser(JobBoardParser):
    """Parser for XING Jobs postings."""

    # XING-specific headers
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
        """Check if URL is a XING job posting."""
        parsed = urlparse(url)
        hostname = parsed.netloc.lower().replace("www.", "")
        # Match xing.com/jobs/* pattern
        is_xing = hostname == "xing.com"
        is_job_page = "/jobs/" in parsed.path
        return is_xing and is_job_page

    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse XING job posting."""
        result = {
            "source": "xing",
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
            "company_profile_url": None,
            "contact_person": None,
        }

        # Try JSON-LD first (XING often has structured data)
        json_ld_data = self._extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Parse HTML for additional/fallback data
        result = self._parse_html(soup, result, url)

        return result

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict | None:
        """Extract JSON-LD structured data from page."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
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
            # XING may include company profile URL
            if hiring_org.get("url"):
                result["company_profile_url"] = hiring_org["url"]
            elif hiring_org.get("sameAs"):
                result["company_profile_url"] = hiring_org["sameAs"]

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

    def _parse_html(self, soup: BeautifulSoup, result: dict, url: str) -> dict:
        """Parse HTML for XING-specific elements."""
        # Title fallback
        if not result["title"]:
            # XING uses h1 or specific data attributes for title
            title_elem = soup.find("h1", class_=re.compile(r"job-title|headline", re.I))
            if not title_elem:
                title_elem = soup.find("h1")
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company name
        if not result["company"]:
            # XING company name often in specific elements
            company_elem = soup.find(attrs={"data-testid": "company-name"})
            if not company_elem:
                company_elem = soup.find(class_=re.compile(r"company-name|employer", re.I))
            if not company_elem:
                # Try finding in a link to company profile
                company_link = soup.find("a", href=re.compile(r"/companies/"))
                if company_link:
                    company_elem = company_link
            if company_elem:
                result["company"] = company_elem.get_text(strip=True)

        # Location
        if not result["location"]:
            location_elem = soup.find(attrs={"data-testid": "job-location"})
            if not location_elem:
                location_elem = soup.find(class_=re.compile(r"location|city", re.I))
            if not location_elem:
                # Look for location icon followed by text
                for elem in soup.find_all(class_=re.compile(r"meta|info", re.I)):
                    text = elem.get_text(strip=True)
                    # German cities pattern
                    if re.search(
                        r"\b(Berlin|Hamburg|München|Köln|Frankfurt|Stuttgart|Düsseldorf|Leipzig|Dresden|Hannover)\b",
                        text,
                        re.I,
                    ):
                        result["location"] = text
                        break
            if location_elem:
                result["location"] = location_elem.get_text(strip=True)

        # Company profile URL
        if not result["company_profile_url"]:
            company_link = soup.find("a", href=re.compile(r"xing\.com/companies/"))
            if not company_link:
                company_link = soup.find("a", href=re.compile(r"/companies/"))
            if isinstance(company_link, Tag):
                href = company_link.get("href")
                if isinstance(href, str):
                    if href.startswith("/"):
                        result["company_profile_url"] = urljoin("https://www.xing.com", href)
                    else:
                        result["company_profile_url"] = href

        # Contact person / Ansprechpartner
        if not result["contact_person"]:
            # XING often shows recruiter/contact person
            contact_elem = soup.find(class_=re.compile(r"contact|recruiter|ansprechpartner", re.I))
            if not contact_elem:
                # Look for person profile links
                person_link = soup.find("a", href=re.compile(r"xing\.com/profile/"))
                if not person_link:
                    person_link = soup.find("a", href=re.compile(r"/profile/"))
                if person_link:
                    contact_elem = person_link
            if contact_elem:
                contact_text = contact_elem.get_text(strip=True)
                # Clean up contact name (remove "Recruiter:", "Ansprechpartner:", etc.)
                contact_text = re.sub(
                    r"^(Recruiter|Ansprechpartner|Contact|Kontakt)[:\s]*", "", contact_text, flags=re.I
                )
                if contact_text and len(contact_text) > 2:
                    result["contact_person"] = contact_text

        # Description
        if not result["description"]:
            # Try common XING job description containers
            desc_elem = soup.find(attrs={"data-testid": "job-description"})
            if not desc_elem:
                desc_elem = soup.find(class_=re.compile(r"job-description|description-content", re.I))
            if not desc_elem:
                # Try finding main content area
                desc_elem = soup.find("article") or soup.find(class_=re.compile(r"content|body", re.I))
            if desc_elem:
                result["description"] = desc_elem.get_text(separator="\n", strip=True)

        # Requirements - often in a separate section
        if not result["requirements"]:
            req_section = soup.find(string=re.compile(r"(Anforderungen|Requirements|Profil|Qualifikation)", re.I))
            if req_section:
                parent = req_section.find_parent(["div", "section", "li"])
                if parent:
                    # Get the parent's next sibling or the parent itself
                    req_text = parent.get_text(separator="\n", strip=True)
                    if len(req_text) < 50:  # If too short, try parent's parent
                        grandparent = parent.find_parent(["div", "section"])
                        if grandparent:
                            req_text = grandparent.get_text(separator="\n", strip=True)
                    result["requirements"] = req_text

        # Employment type
        if not result["employment_type"]:
            # Search for employment type keywords
            for elem in soup.find_all(class_=re.compile(r"meta|info|type|tag", re.I)):
                text = elem.get_text(strip=True).lower()
                job_types = []
                type_mapping = {
                    "vollzeit": "Vollzeit",
                    "full-time": "Vollzeit",
                    "teilzeit": "Teilzeit",
                    "part-time": "Teilzeit",
                    "festanstellung": "Festanstellung",
                    "befristet": "Befristet",
                    "praktikum": "Praktikum",
                    "werkstudent": "Werkstudent",
                    "remote": "Remote",
                    "homeoffice": "Homeoffice",
                }
                for keyword, label in type_mapping.items():
                    if keyword in text and label not in job_types:
                        job_types.append(label)
                if job_types:
                    result["employment_type"] = ", ".join(job_types)
                    break

        # Contact email - search in entire page
        if not result["contact_email"]:
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            page_text = soup.get_text()
            emails = email_pattern.findall(page_text)
            # Filter out common non-contact emails
            contact_emails = [
                e
                for e in emails
                if not any(
                    x in e.lower()
                    for x in [
                        "noreply",
                        "no-reply",
                        "newsletter",
                        "support@xing",
                        "info@xing",
                        "kundenservice@xing",
                        "werbung@xing",
                    ]
                )
            ]
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


class SoftgardenParser(JobBoardParser):
    """Parser for Softgarden.io job postings.

    Softgarden is a German ATS used by companies like ZEIT Verlagsgruppe.
    URLs match pattern: *.softgarden.io/job/*
    """

    # Anti-bot headers for Softgarden
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
        """Check if URL is a Softgarden job posting."""
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        # Match *.softgarden.io/job/* pattern
        is_softgarden = hostname.endswith(".softgarden.io") or hostname == "softgarden.io"
        is_job_page = "/job/" in parsed.path
        return is_softgarden and is_job_page

    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse Softgarden job posting."""
        result = {
            "source": "softgarden",
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
            "contact_person": None,
        }

        # Try JSON-LD first (Softgarden typically has structured data)
        json_ld_data = self._extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Parse HTML for additional/fallback data
        result = self._parse_html(soup, result, url)

        return result

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict | None:
        """Extract JSON-LD structured data from page."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
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
                if address.get("addressCountry"):
                    country = address["addressCountry"]
                    if isinstance(country, dict):
                        country = country.get("name", "")
                    if country and country not in parts:
                        parts.append(country)
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
            elif isinstance(value, (int, float)):
                currency = salary.get("currency", "EUR")
                result["salary"] = f"{value} {currency}"

        return result

    def _parse_html(self, soup: BeautifulSoup, result: dict, url: str) -> dict:
        """Parse HTML for Softgarden-specific elements."""
        # Title fallback
        if not result["title"]:
            # Softgarden typically uses h1 for job title
            title_elem = soup.find("h1", class_=re.compile(r"job-title|title|headline", re.I))
            if not title_elem:
                title_elem = soup.find("h1")
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company name fallback
        if not result["company"]:
            # Try to extract from URL subdomain (e.g., zeit-verlagsgruppe.softgarden.io)
            parsed = urlparse(url)
            subdomain = parsed.netloc.replace(".softgarden.io", "")
            if subdomain and subdomain != "www":
                # Convert hyphenated name to title case
                company_name = subdomain.replace("-", " ").title()
                result["company"] = company_name

            # Also look for company name in page elements
            company_elem = soup.find(class_=re.compile(r"company-name|employer|arbeitgeber|firma", re.I))
            if not company_elem:
                company_elem = soup.find(attrs={"data-testid": "company-name"})
            if company_elem:
                result["company"] = company_elem.get_text(strip=True)

        # Location fallback
        if not result["location"]:
            location_elem = soup.find(class_=re.compile(r"location|standort|arbeitsort", re.I))
            if not location_elem:
                location_elem = soup.find(attrs={"data-testid": "job-location"})
            if not location_elem:
                # Look for location patterns in meta elements
                for elem in soup.find_all(class_=re.compile(r"meta|info|detail", re.I)):
                    text = elem.get_text(strip=True)
                    # German cities pattern
                    city_match = re.search(
                        r"\b(Berlin|Hamburg|München|Köln|Frankfurt|Stuttgart|Düsseldorf|"
                        r"Leipzig|Dresden|Hannover|Bremen|Nürnberg|Essen|Dortmund)\b",
                        text,
                        re.I,
                    )
                    if city_match:
                        result["location"] = text
                        break
            if location_elem and not result["location"]:
                result["location"] = location_elem.get_text(strip=True)

        # Contact person (Ansprechpartner)
        if not result["contact_person"]:
            # Softgarden often shows contact person
            contact_elem = soup.find(class_=re.compile(r"contact|ansprechpartner|recruiter", re.I))
            if not contact_elem:
                ansprech_label = soup.find(
                    string=re.compile(r"Ansprechpartner\s*:?|Kontakt\s*:?|Ihr Ansprechpartner", re.I)
                )
                if ansprech_label:
                    parent = ansprech_label.find_parent(["div", "p", "span", "section"])
                    if parent:
                        # Try to find name in same or next element
                        contact_text = parent.get_text(strip=True)
                        # Remove label prefix
                        contact_text = re.sub(
                            r"^(Ansprechpartner|Kontakt|Ihr Ansprechpartner)[:\s]*", "", contact_text, flags=re.I
                        )
                        if contact_text and len(contact_text) > 2 and len(contact_text) < 100:
                            result["contact_person"] = contact_text
            if contact_elem and not result["contact_person"]:
                contact_text = contact_elem.get_text(strip=True)
                if len(contact_text) > 2 and len(contact_text) < 100:
                    result["contact_person"] = contact_text

        # Description fallback
        if not result["description"]:
            desc_elem = soup.find(class_=re.compile(r"job-description|description|stellenbeschreibung", re.I))
            if not desc_elem:
                desc_elem = soup.find(attrs={"data-testid": "job-description"})
            if not desc_elem:
                # Try finding main content area
                desc_elem = (
                    soup.find("article") or soup.find("main") or soup.find(class_=re.compile(r"content|body", re.I))
                )
            if desc_elem:
                result["description"] = desc_elem.get_text(separator="\n", strip=True)

        # Requirements - often in a separate section
        if not result["requirements"]:
            req_section = soup.find(
                string=re.compile(r"(Anforderungen|Requirements|Ihr Profil|Qualifikation|Was Sie mitbringen)", re.I)
            )
            if req_section:
                parent = req_section.find_parent(["div", "section", "li", "h2", "h3"])
                if parent:
                    next_sibling = parent.find_next_sibling(["div", "section", "ul", "p"])
                    if next_sibling:
                        req_text = next_sibling.get_text(separator="\n", strip=True)
                    else:
                        req_text = parent.get_text(separator="\n", strip=True)
                    if len(req_text) >= 20:
                        result["requirements"] = req_text

        # Employment type fallback
        if not result["employment_type"]:
            for elem in soup.find_all(class_=re.compile(r"meta|info|type|tag|employment|arbeitszeit", re.I)):
                text = elem.get_text(strip=True).lower()
                job_types = []
                type_mapping = {
                    "vollzeit": "Vollzeit",
                    "full-time": "Vollzeit",
                    "full time": "Vollzeit",
                    "teilzeit": "Teilzeit",
                    "part-time": "Teilzeit",
                    "part time": "Teilzeit",
                    "festanstellung": "Festanstellung",
                    "unbefristet": "Unbefristet",
                    "befristet": "Befristet",
                    "praktikum": "Praktikum",
                    "internship": "Praktikum",
                    "werkstudent": "Werkstudent",
                    "working student": "Werkstudent",
                    "remote": "Remote",
                    "homeoffice": "Homeoffice",
                    "hybrid": "Hybrid",
                }
                for keyword, label in type_mapping.items():
                    if keyword in text and label not in job_types:
                        job_types.append(label)
                if job_types:
                    result["employment_type"] = ", ".join(job_types)
                    break

        # Salary fallback - search for salary patterns
        if not result["salary"]:
            page_text = soup.get_text()
            # German salary patterns: "50.000 - 70.000 €", "ab 45.000 EUR"
            salary_pattern = re.compile(
                r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*[-–bis]\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*(?:€|EUR|Euro))"
                r"|(?:ab\s+)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*(?:€|EUR|Euro))",
                re.I,
            )
            salary_match = salary_pattern.search(page_text)
            if salary_match:
                result["salary"] = salary_match.group(0).strip()

        # Posted date - look for German date formats
        if not result["posted_date"]:
            date_label = soup.find(string=re.compile(r"(Online seit|Eingestellt am|Veröffentlicht|Datum|Posted)", re.I))
            if date_label:
                parent = date_label.find_parent(["div", "p", "span", "dt", "li"])
                if parent:
                    text = parent.get_text(strip=True)
                    # Try German date format (DD.MM.YYYY)
                    date_pattern = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
                    date_match = date_pattern.search(text)
                    if date_match:
                        day, month, year = date_match.groups()
                        result["posted_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Contact email - search in entire page
        if not result["contact_email"]:
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            page_text = soup.get_text()
            emails = email_pattern.findall(page_text)
            # Filter out common non-contact emails
            contact_emails = [
                e
                for e in emails
                if not any(
                    x in e.lower()
                    for x in [
                        "noreply",
                        "no-reply",
                        "newsletter",
                        "support@softgarden",
                        "info@softgarden",
                        "datenschutz",
                        "privacy",
                        "tracking",
                    ]
                )
            ]
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
            # Try German date format (DD.MM.YYYY)
            try:
                date_match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
                if date_match:
                    day, month, year = date_match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except (ValueError, AttributeError):
                pass
            return date_str


class ArbeitsagenturParser(JobBoardParser):
    """Parser for Bundesagentur für Arbeit job postings."""

    # Anti-bot headers for Arbeitsagentur
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
        """Check if URL is an Arbeitsagentur job posting."""
        parsed = urlparse(url)
        hostname = parsed.netloc.lower().replace("www.", "")
        # Match arbeitsagentur.de job posting URLs
        # Typical patterns:
        # - arbeitsagentur.de/jobsuche/suche?...
        # - arbeitsagentur.de/jobsuche/jobdetail/...
        # - con.arbeitsagentur.de/prod/jobboerse/...
        is_arbeitsagentur = hostname in ["arbeitsagentur.de", "con.arbeitsagentur.de"] or hostname.endswith(
            ".arbeitsagentur.de"
        )
        is_job_page = (
            "/jobsuche/" in parsed.path
            or "/jobboerse/" in parsed.path
            or "/stellenangebot/" in parsed.path
            or "stelle" in parsed.path.lower()
        )
        return is_arbeitsagentur and is_job_page

    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse Arbeitsagentur job posting."""
        result = {
            "source": "arbeitsagentur",
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
            "reference_number": None,  # Referenznummer - specific to Arbeitsagentur
            "contact_person": None,
            "contact_phone": None,
        }

        # Try JSON-LD first (Arbeitsagentur may have structured data)
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
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
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

        # Identifier (Referenznummer)
        identifier = data.get("identifier", {})
        if isinstance(identifier, dict):
            result["reference_number"] = identifier.get("value")
        elif isinstance(identifier, str):
            result["reference_number"] = identifier

        return result

    def _parse_html(self, soup: BeautifulSoup, result: dict) -> dict:
        """Parse HTML for Arbeitsagentur-specific elements."""
        # Title - look for various patterns
        if not result["title"]:
            # Try data attributes and common class patterns
            title_elem = soup.find(attrs={"data-testid": "job-title"})
            if not title_elem:
                title_elem = soup.find(class_=re.compile(r"job-title|jobtitle|stellentitel", re.I))
            if not title_elem:
                title_elem = soup.find("h1")
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company name - Arbeitsagentur uses "Arbeitgeber" (employer)
        if not result["company"]:
            # Look for employer/company sections
            company_elem = soup.find(attrs={"data-testid": "company-name"})
            if not company_elem:
                company_elem = soup.find(class_=re.compile(r"arbeitgeber|employer|company|firma", re.I))
            if not company_elem:
                # Search for "Arbeitgeber:" label
                arbeitgeber_label = soup.find(string=re.compile(r"Arbeitgeber\s*:", re.I))
                if arbeitgeber_label:
                    parent = arbeitgeber_label.find_parent(["div", "p", "span", "dt", "li"])
                    if parent:
                        # Get next sibling or text after label
                        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
                        if next_sibling:
                            company_elem = next_sibling
                        else:
                            # Try to extract from same element
                            text = parent.get_text(strip=True)
                            company_text = re.sub(r"^Arbeitgeber\s*:\s*", "", text, flags=re.I)
                            if company_text:
                                result["company"] = company_text
            if company_elem and not result["company"]:
                result["company"] = company_elem.get_text(strip=True)

        # Location - "Arbeitsort"
        if not result["location"]:
            location_elem = soup.find(attrs={"data-testid": "job-location"})
            if not location_elem:
                location_elem = soup.find(class_=re.compile(r"arbeitsort|location|standort", re.I))
            if not location_elem:
                # Search for "Arbeitsort:" label
                arbeitsort_label = soup.find(string=re.compile(r"Arbeitsort\s*:", re.I))
                if arbeitsort_label:
                    parent = arbeitsort_label.find_parent(["div", "p", "span", "dt", "li"])
                    if parent:
                        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
                        if next_sibling:
                            location_elem = next_sibling
                        else:
                            text = parent.get_text(strip=True)
                            location_text = re.sub(r"^Arbeitsort\s*:\s*", "", text, flags=re.I)
                            if location_text:
                                result["location"] = location_text
            if location_elem and not result["location"]:
                result["location"] = location_elem.get_text(strip=True)

        # Reference number (Referenznummer) - specific to Arbeitsagentur
        if not result["reference_number"]:
            ref_elem = soup.find(class_=re.compile(r"referenz|reference|stellennummer", re.I))
            if not ref_elem:
                # Search for "Referenznummer:" or "Stellennummer:" label
                ref_label = soup.find(string=re.compile(r"(Referenz|Stellen)nummer\s*:", re.I))
                if ref_label:
                    parent = ref_label.find_parent(["div", "p", "span", "dt", "li"])
                    if parent:
                        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
                        if next_sibling:
                            ref_elem = next_sibling
                        else:
                            text = parent.get_text(strip=True)
                            ref_text = re.sub(r"^(Referenz|Stellen)nummer\s*:\s*", "", text, flags=re.I)
                            if ref_text:
                                result["reference_number"] = ref_text.strip()
            if ref_elem and not result["reference_number"]:
                result["reference_number"] = ref_elem.get_text(strip=True)
            # Fallback: search for common reference number patterns
            if not result["reference_number"]:
                page_text = soup.get_text()
                ref_pattern = re.compile(r"(?:Referenz(?:nummer)?|Stellen(?:nummer)?)[:\s]+([A-Z0-9\-/]+)", re.I)
                ref_match = ref_pattern.search(page_text)
                if ref_match:
                    result["reference_number"] = ref_match.group(1).strip()

        # Contact person (Ansprechpartner) - Arbeitsagentur often has this
        if not result["contact_person"]:
            contact_elem = soup.find(class_=re.compile(r"ansprechpartner|kontakt|contact-person", re.I))
            if not contact_elem:
                ansprech_label = soup.find(string=re.compile(r"Ansprechpartner\s*:", re.I))
                if ansprech_label:
                    parent = ansprech_label.find_parent(["div", "p", "span", "dt", "li"])
                    if parent:
                        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
                        if next_sibling:
                            contact_elem = next_sibling
                        else:
                            text = parent.get_text(strip=True)
                            contact_text = re.sub(r"^Ansprechpartner\s*:\s*", "", text, flags=re.I)
                            if contact_text:
                                result["contact_person"] = contact_text
            if contact_elem and not result["contact_person"]:
                result["contact_person"] = contact_elem.get_text(strip=True)

        # Contact phone (Telefon)
        if not result["contact_phone"]:
            phone_elem = soup.find(class_=re.compile(r"telefon|phone", re.I))
            if not phone_elem:
                telefon_label = soup.find(string=re.compile(r"Telefon\s*:", re.I))
                if telefon_label:
                    parent = telefon_label.find_parent(["div", "p", "span", "dt", "li"])
                    if parent:
                        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
                        if next_sibling:
                            phone_elem = next_sibling
                        else:
                            text = parent.get_text(strip=True)
                            phone_text = re.sub(r"^Telefon\s*:\s*", "", text, flags=re.I)
                            if phone_text:
                                result["contact_phone"] = phone_text
            if phone_elem and not result["contact_phone"]:
                result["contact_phone"] = phone_elem.get_text(strip=True)
            # Fallback: search for German phone number patterns
            if not result["contact_phone"]:
                page_text = soup.get_text()
                # German phone patterns: +49, 0xxx, (0xxx)
                phone_pattern = re.compile(
                    r"(?:Tel(?:efon)?\.?\s*:?\s*)?((?:\+49|0)[\s\-/]*(?:\(\d+\)|\d+)[\s\-/]*[\d\s\-/]{6,})", re.I
                )
                phone_match = phone_pattern.search(page_text)
                if phone_match:
                    phone = phone_match.group(1).strip()
                    # Clean up phone number
                    phone = re.sub(r"\s+", " ", phone)
                    if len(phone) >= 8:  # Minimum valid phone length
                        result["contact_phone"] = phone

        # Description
        if not result["description"]:
            desc_elem = soup.find(attrs={"data-testid": "job-description"})
            if not desc_elem:
                desc_elem = soup.find(class_=re.compile(r"job-description|beschreibung|stellenbeschreibung", re.I))
            if not desc_elem:
                # Try finding main content area
                desc_elem = soup.find("article") or soup.find("main")
            if desc_elem:
                result["description"] = desc_elem.get_text(separator="\n", strip=True)

        # Requirements - often labeled as "Anforderungen" or "Ihr Profil"
        if not result["requirements"]:
            req_section = soup.find(string=re.compile(r"(Anforderungen|Ihr Profil|Qualifikation|Voraussetzung)", re.I))
            if req_section:
                parent = req_section.find_parent(["div", "section", "li", "h2", "h3"])
                if parent:
                    # Get the next sibling or parent content
                    next_sibling = parent.find_next_sibling(["div", "section", "ul", "p"])
                    if next_sibling:
                        req_text = next_sibling.get_text(separator="\n", strip=True)
                    else:
                        req_text = parent.get_text(separator="\n", strip=True)
                    if len(req_text) >= 20:
                        result["requirements"] = req_text

        # Employment type
        if not result["employment_type"]:
            # Search for employment type keywords in meta elements
            for elem in soup.find_all(class_=re.compile(r"meta|info|type|tag|arbeitszeit|befristung", re.I)):
                text = elem.get_text(strip=True).lower()
                job_types = []
                type_mapping = {
                    "vollzeit": "Vollzeit",
                    "full-time": "Vollzeit",
                    "teilzeit": "Teilzeit",
                    "part-time": "Teilzeit",
                    "unbefristet": "Unbefristet",
                    "befristet": "Befristet",
                    "minijob": "Minijob",
                    "praktikum": "Praktikum",
                    "ausbildung": "Ausbildung",
                    "werkstudent": "Werkstudent",
                }
                for keyword, label in type_mapping.items():
                    if keyword in text and label not in job_types:
                        job_types.append(label)
                if job_types:
                    result["employment_type"] = ", ".join(job_types)
                    break

        # Posted date - look for "Online seit" or "Eingestellt am"
        if not result["posted_date"]:
            date_label = soup.find(string=re.compile(r"(Online seit|Eingestellt am|Veröffentlicht)\s*:", re.I))
            if date_label:
                parent = date_label.find_parent(["div", "p", "span", "dt", "li"])
                if parent:
                    text = parent.get_text(strip=True)
                    # Try to extract date in German format (DD.MM.YYYY)
                    date_pattern = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
                    date_match = date_pattern.search(text)
                    if date_match:
                        day, month, year = date_match.groups()
                        result["posted_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Contact email - search in entire page
        if not result["contact_email"]:
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            page_text = soup.get_text()
            emails = email_pattern.findall(page_text)
            # Filter out common non-contact emails
            contact_emails = [
                e
                for e in emails
                if not any(
                    x in e.lower()
                    for x in [
                        "noreply",
                        "no-reply",
                        "newsletter",
                        "@arbeitsagentur.de",
                        "support@",
                        "info@arbeitsagentur",
                    ]
                )
            ]
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


class GenericJobParser:
    """Generic fallback parser for job postings from unknown sources.

    Uses multiple extraction strategies in priority order:
    1. JSON-LD Schema.org JobPosting
    2. OpenGraph meta tags
    3. Standard meta tags
    4. Title tag parsing
    5. Common HTML patterns/selectors
    6. Heuristics (first h1, domain-based company name)

    Returns partial data - extracts whatever is available rather than
    requiring all fields to be present.
    """

    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse job posting using multiple fallback strategies."""
        result = {
            "source": "generic",
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
            "extraction_methods": [],  # Track which methods succeeded
        }

        # Strategy 1: JSON-LD Schema.org
        json_ld_data = self._extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)
            if any(result.get(k) for k in ["title", "company", "description"]):
                result["extraction_methods"].append("json-ld")
                logger.debug("GenericJobParser: Extracted data via JSON-LD")

        # Strategy 2: OpenGraph meta tags
        result = self._extract_opengraph(soup, result)

        # Strategy 3: Standard meta tags
        result = self._extract_meta_tags(soup, result)

        # Strategy 4: Title tag parsing
        result = self._extract_from_title_tag(soup, result)

        # Strategy 5: Common HTML patterns
        result = self._extract_html_patterns(soup, result, url)

        # Strategy 6: Heuristics
        result = self._apply_heuristics(soup, result, url)

        # Check if this appears to be a search results page
        if self._is_search_results_page(soup, url):
            result["is_search_results_page"] = True
            logger.warning(
                f"GenericJobParser: URL appears to be a search results page, not a single job posting: {url}"
            )

        # Clean up extraction_methods for logging
        if result["extraction_methods"]:
            logger.info(
                f"GenericJobParser: Extracted data for {url} using methods: {', '.join(result['extraction_methods'])}"
            )
        else:
            logger.warning(f"GenericJobParser: No structured data found for {url}")

        # Remove internal tracking field from final result
        del result["extraction_methods"]

        return result

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict | None:
        """Extract JSON-LD structured data with @type JobPosting."""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)

                # Handle array of objects
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
                        # Check for nested @graph
                        if isinstance(item, dict) and "@graph" in item:
                            for graph_item in item["@graph"]:
                                if isinstance(graph_item, dict) and graph_item.get("@type") == "JobPosting":
                                    return graph_item

                # Handle single object
                elif isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        return data
                    # Check for @graph array
                    if "@graph" in data:
                        for graph_item in data["@graph"]:
                            if isinstance(graph_item, dict) and graph_item.get("@type") == "JobPosting":
                                return graph_item

            except (json.JSONDecodeError, TypeError, KeyError):
                continue
        return None

    def _parse_json_ld(self, data: dict, result: dict) -> dict:
        """Parse JSON-LD JobPosting schema into result dict."""
        # Title
        if not result["title"] and data.get("title"):
            result["title"] = self._clean_text(data["title"])

        # Description
        if not result["description"] and data.get("description"):
            result["description"] = self._clean_text(data["description"])

        # Company (hiringOrganization)
        if not result["company"]:
            hiring_org = data.get("hiringOrganization", {})
            if isinstance(hiring_org, dict):
                result["company"] = hiring_org.get("name")
            elif isinstance(hiring_org, str):
                result["company"] = hiring_org

        # Location (jobLocation)
        if not result["location"]:
            job_location = data.get("jobLocation")
            result["location"] = self._parse_json_ld_location(job_location)

        # Dates
        if not result["posted_date"] and data.get("datePosted"):
            result["posted_date"] = self._parse_date(data["datePosted"])

        if not result["application_deadline"] and data.get("validThrough"):
            result["application_deadline"] = self._parse_date(data["validThrough"])

        # Employment type
        if not result["employment_type"]:
            emp_type = data.get("employmentType")
            if emp_type:
                if isinstance(emp_type, list):
                    result["employment_type"] = ", ".join(emp_type)
                else:
                    result["employment_type"] = emp_type

        # Salary (baseSalary)
        if not result["salary"]:
            salary = data.get("baseSalary", {})
            if isinstance(salary, dict):
                value = salary.get("value", {})
                currency = salary.get("currency", "EUR")
                if isinstance(value, dict):
                    min_val = value.get("minValue")
                    max_val = value.get("maxValue")
                    if min_val and max_val:
                        result["salary"] = f"{min_val}-{max_val} {currency}"
                    elif min_val:
                        result["salary"] = f"ab {min_val} {currency}"
                    elif max_val:
                        result["salary"] = f"bis {max_val} {currency}"
                elif isinstance(value, (int, float)):
                    result["salary"] = f"{value} {currency}"

        return result

    def _parse_json_ld_location(self, job_location: Any) -> str | None:
        """Parse jobLocation from JSON-LD which can be dict, list, or string."""
        if not job_location:
            return None

        if isinstance(job_location, str):
            return job_location

        if isinstance(job_location, dict):
            address = job_location.get("address", {})
            if isinstance(address, str):
                return address
            if isinstance(address, dict):
                parts = []
                for field in ["streetAddress", "postalCode", "addressLocality", "addressRegion", "addressCountry"]:
                    val = address.get(field)
                    if val:
                        if isinstance(val, dict):
                            val = val.get("name", "")
                        if val and val not in parts:
                            parts.append(str(val))
                return ", ".join(parts) if parts else None

        if isinstance(job_location, list):
            locations = []
            for loc in job_location:
                parsed = self._parse_json_ld_location(loc)
                if parsed:
                    locations.append(parsed)
            return ", ".join(locations) if locations else None

        return None

    def _extract_opengraph(self, soup: BeautifulSoup, result: dict) -> dict:
        """Extract data from OpenGraph meta tags."""
        og_extracted = False

        # og:title -> title
        if not result["title"]:
            og_title = soup.find("meta", property="og:title")
            if isinstance(og_title, Tag):
                content = og_title.get("content")
                if content:
                    result["title"] = self._clean_text(str(content))
                    og_extracted = True

        # og:description -> description
        if not result["description"]:
            og_desc = soup.find("meta", property="og:description")
            if isinstance(og_desc, Tag):
                content = og_desc.get("content")
                if content:
                    result["description"] = self._clean_text(str(content))
                    og_extracted = True

        # og:site_name -> company (as hint)
        if not result["company"]:
            og_site = soup.find("meta", property="og:site_name")
            if isinstance(og_site, Tag):
                content = og_site.get("content")
                if content:
                    result["company"] = self._clean_text(str(content))
                    og_extracted = True

        if og_extracted:
            result["extraction_methods"].append("opengraph")
            logger.debug("GenericJobParser: Extracted data via OpenGraph")

        return result

    def _extract_meta_tags(self, soup: BeautifulSoup, result: dict) -> dict:
        """Extract data from standard meta tags."""
        meta_extracted = False

        # <meta name="title">
        if not result["title"]:
            meta_title = soup.find("meta", attrs={"name": "title"})
            if isinstance(meta_title, Tag):
                content = meta_title.get("content")
                if content:
                    result["title"] = self._clean_text(str(content))
                    meta_extracted = True

        # <meta name="description">
        if not result["description"]:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if isinstance(meta_desc, Tag):
                content = meta_desc.get("content")
                if content:
                    result["description"] = self._clean_text(str(content))
                    meta_extracted = True

        # <meta name="author"> -> company hint
        if not result["company"]:
            meta_author = soup.find("meta", attrs={"name": "author"})
            if isinstance(meta_author, Tag):
                content = meta_author.get("content")
                if content:
                    result["company"] = self._clean_text(str(content))
                    meta_extracted = True

        if meta_extracted:
            result["extraction_methods"].append("meta-tags")
            logger.debug("GenericJobParser: Extracted data via meta tags")

        return result

    def _extract_from_title_tag(self, soup: BeautifulSoup, result: dict) -> dict:
        """Extract job title and company from <title> tag.

        Common patterns:
        - "Job Title - Company Name"
        - "Job Title | Company Name"
        - "Job Title at Company Name"
        - "Job Title bei Company Name" (German)
        """
        if result["title"] and result["company"]:
            return result  # Already have both

        title_tag = soup.find("title")
        if not title_tag:
            return result

        title_text = title_tag.get_text(strip=True)
        if not title_text:
            return result

        title_extracted = False

        # Try splitting by common separators
        separators = [" - ", " | ", " – ", " — ", " · "]
        for sep in separators:
            if sep in title_text:
                parts = title_text.split(sep)
                if len(parts) >= 2:
                    # First part is usually the job title
                    if not result["title"]:
                        result["title"] = self._clean_text(parts[0])
                        title_extracted = True
                    # Last part (or second) is often the company
                    if not result["company"]:
                        company_part = parts[-1] if len(parts) > 2 else parts[1]
                        # Clean common suffixes
                        company_part = re.sub(
                            r"\s*[-–|]\s*(Jobs?|Karriere|Career|Stellenangebote?).*$", "", company_part, flags=re.I
                        )
                        if company_part:
                            result["company"] = self._clean_text(company_part)
                            title_extracted = True
                    break

        # Try "at" / "bei" pattern
        if not result["title"] or not result["company"]:
            at_match = re.match(r"^(.+?)\s+(?:at|bei|@)\s+(.+?)(?:\s*[-|–].*)?$", title_text, re.I)
            if at_match:
                if not result["title"]:
                    result["title"] = self._clean_text(at_match.group(1))
                    title_extracted = True
                if not result["company"]:
                    result["company"] = self._clean_text(at_match.group(2))
                    title_extracted = True

        # Fallback: use entire title if nothing else worked
        if not result["title"] and title_text:
            # Clean common suffixes from title (order matters - more specific first)
            cleanup_patterns = [
                # Austrian/German job board patterns
                r"\s*\|\s*aktuell\s+\d+\s+offen",  # | aktuell 9 offen
                r"\s*\|\s*karriere\.at",  # | karriere.at
                r"\s*\|\s*stepstone\.at",  # | stepstone.at
                r"\s*\|\s*stepstone\.de",  # | stepstone.de
                r"\s+Jobs?\s+in\s+[\wäöüÄÖÜß]+(?:\s|$)",  # Jobs in Oberösterreich
                # Generic patterns
                r"\s*[-–|]\s*(Jobs?|Karriere|Career|Stellenangebote?|Apply|Bewerben).*$",
            ]
            clean_title = title_text
            for pattern in cleanup_patterns:
                clean_title = re.sub(pattern, "", clean_title, flags=re.I)
            clean_title = clean_title.strip()
            if clean_title:
                result["title"] = self._clean_text(clean_title)
                title_extracted = True

        if title_extracted:
            result["extraction_methods"].append("title-tag")
            logger.debug("GenericJobParser: Extracted data via title tag")

        return result

    def _extract_html_patterns(self, soup: BeautifulSoup, result: dict, url: str) -> dict:
        """Extract data using common HTML patterns and selectors."""
        html_extracted = False

        # Job title selectors (in priority order)
        if not result["title"]:
            title_selectors = [
                {"attrs": {"data-testid": re.compile(r"job[-_]?title", re.I)}},
                {"class_": re.compile(r"job[-_]?title|position[-_]?title|posting[-_]?title", re.I)},
                {"attrs": {"itemprop": "title"}},
                {"attrs": {"data-qa": re.compile(r"job[-_]?title", re.I)}},
            ]
            for selector in title_selectors:
                elem = soup.find(**selector)
                if elem:
                    result["title"] = self._clean_text(elem.get_text())
                    html_extracted = True
                    break

        # Company name selectors
        if not result["company"]:
            company_selectors = [
                {"attrs": {"data-testid": re.compile(r"company[-_]?name|employer", re.I)}},
                {"class_": re.compile(r"company[-_]?name|employer[-_]?name|hiring[-_]?company", re.I)},
                {"attrs": {"itemprop": "hiringOrganization"}},
                {"attrs": {"data-company": True}},
                {"attrs": {"data-qa": re.compile(r"company", re.I)}},
            ]
            for selector in company_selectors:
                elem = soup.find(**selector)
                if elem:
                    # May be nested, look for name attribute or direct text
                    name_elem = elem.find(attrs={"itemprop": "name"})
                    if name_elem:
                        result["company"] = self._clean_text(name_elem.get_text())
                    else:
                        result["company"] = self._clean_text(elem.get_text())
                    html_extracted = True
                    break

        # Location selectors
        if not result["location"]:
            location_selectors = [
                {"attrs": {"data-testid": re.compile(r"job[-_]?location|location", re.I)}},
                {"class_": re.compile(r"job[-_]?location|location|arbeitsort|standort", re.I)},
                {"attrs": {"itemprop": "jobLocation"}},
                {"attrs": {"data-location": True}},
            ]
            for selector in location_selectors:
                elem = soup.find(**selector)
                if elem:
                    # Handle nested address
                    addr_elem = elem.find(attrs={"itemprop": "address"})
                    if addr_elem:
                        result["location"] = self._clean_text(addr_elem.get_text())
                    else:
                        result["location"] = self._clean_text(elem.get_text())
                    html_extracted = True
                    break

        # Job description selectors
        if not result["description"]:
            desc_selectors = [
                {"attrs": {"data-testid": re.compile(r"job[-_]?description|description", re.I)}},
                {"class_": re.compile(r"job[-_]?description|description[-_]?content|posting[-_]?description", re.I)},
                {"attrs": {"itemprop": "description"}},
                {"attrs": {"id": re.compile(r"job[-_]?description", re.I)}},
            ]
            for selector in desc_selectors:
                elem = soup.find(**selector)
                if elem:
                    result["description"] = self._clean_text(elem.get_text(separator="\n"))
                    html_extracted = True
                    break

            # Fallback: try article or main content
            if not result["description"]:
                for tag in ["article", "main"]:
                    elem = soup.find(tag)
                    if elem:
                        text = elem.get_text(separator="\n", strip=True)
                        if len(text) > 200:  # Minimum content threshold
                            result["description"] = self._clean_text(text)
                            html_extracted = True
                            break

        # Employment type - look for keywords in tagged elements
        if not result["employment_type"]:
            emp_keywords = {
                "vollzeit": "Vollzeit",
                "full-time": "Full-time",
                "full time": "Full-time",
                "teilzeit": "Teilzeit",
                "part-time": "Part-time",
                "part time": "Part-time",
                "festanstellung": "Festanstellung",
                "permanent": "Permanent",
                "befristet": "Befristet",
                "temporary": "Temporary",
                "remote": "Remote",
                "homeoffice": "Homeoffice",
                "hybrid": "Hybrid",
                "freelance": "Freelance",
                "praktikum": "Praktikum",
                "internship": "Internship",
                "werkstudent": "Werkstudent",
                "minijob": "Minijob",
            }
            for elem in soup.find_all(class_=re.compile(r"type|tag|badge|chip|label|employment", re.I)):
                text = elem.get_text(strip=True).lower()
                for keyword, label in emp_keywords.items():
                    if keyword in text:
                        result["employment_type"] = label
                        html_extracted = True
                        break
                if result["employment_type"]:
                    break

        # Contact email - search page text
        if not result["contact_email"]:
            page_text = soup.get_text()
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            emails = email_pattern.findall(page_text)
            # Filter out common non-contact emails
            blocked_patterns = [
                "noreply",
                "no-reply",
                "newsletter",
                "support@",
                "info@",
                "privacy",
                "datenschutz",
                "tracking",
                "analytics",
                "example.com",
                "test.com",
            ]
            contact_emails = [e for e in emails if not any(bp in e.lower() for bp in blocked_patterns)]
            if contact_emails:
                result["contact_email"] = contact_emails[0]
                html_extracted = True

        if html_extracted:
            result["extraction_methods"].append("html-patterns")
            logger.debug("GenericJobParser: Extracted data via HTML patterns")

        return result

    def _apply_heuristics(self, soup: BeautifulSoup, result: dict, url: str) -> dict:
        """Apply heuristic extraction as last resort."""
        heuristic_used = False

        # First h1 as job title
        if not result["title"]:
            h1 = soup.find("h1")
            if h1:
                title_text = h1.get_text(strip=True)
                # Avoid generic headings
                generic_headings = ["jobs", "karriere", "career", "stellenangebote", "home"]
                if title_text.lower() not in generic_headings and len(title_text) > 3:
                    result["title"] = self._clean_text(title_text)
                    heuristic_used = True

        # Company from domain name
        if not result["company"]:
            parsed = urlparse(url)
            hostname = parsed.netloc.lower().replace("www.", "")
            # Extract base domain (before TLD)
            domain_parts = hostname.split(".")
            if len(domain_parts) >= 2:
                # Skip common job board domains
                job_board_domains = [
                    "indeed",
                    "stepstone",
                    "xing",
                    "linkedin",
                    "glassdoor",
                    "monster",
                    "lever",
                    "greenhouse",
                    "workday",
                    "smartrecruiters",
                    "softgarden",
                    "arbeitsagentur",
                    "jobs",
                    "careers",
                    # Austrian/German job boards
                    "karriere",
                    "jobware",
                    "stellenanzeigen",
                    "hokify",
                    "willhaben",
                ]
                base_domain = domain_parts[0]
                if base_domain not in job_board_domains:
                    # Convert to title case, replace hyphens with spaces
                    company_name = base_domain.replace("-", " ").replace("_", " ").title()
                    result["company"] = company_name
                    heuristic_used = True

        # Look for salary patterns in page text
        if not result["salary"]:
            page_text = soup.get_text()
            # German salary patterns
            salary_patterns = [
                # Range: 50.000 - 70.000 € or 50,000-70,000 EUR
                r"(\d{1,3}(?:[.,]\d{3})*)\s*[-–bis]+\s*(\d{1,3}(?:[.,]\d{3})*)\s*(?:€|EUR|Euro)",
                # Single value: ab 50.000 €
                r"(?:ab|from|starting)\s+(\d{1,3}(?:[.,]\d{3})*)\s*(?:€|EUR|Euro)",
                # Hourly: 15-20 €/h
                r"(\d{1,3})\s*[-–]\s*(\d{1,3})\s*(?:€|EUR)/\s*(?:h|Stunde|hour)",
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, page_text, re.I)
                if match:
                    result["salary"] = match.group(0).strip()
                    heuristic_used = True
                    break

        if heuristic_used:
            result["extraction_methods"].append("heuristics")
            logger.debug("GenericJobParser: Applied heuristic extraction")

        return result

    def _is_search_results_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Detect if URL is a search results page rather than a single job posting.

        Returns True if multiple indicators suggest this is a listing page.
        """
        indicators = 0

        # URL pattern indicators
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in ["/search", "/jobs?", "/suche", "?q=", "&q=", "/results"]):
            indicators += 1

        # Multiple job cards/listings on page
        job_card_selectors = [
            "[data-job-id]",
            ".job-card",
            ".job-listing",
            ".job-item",
            "[data-testid*='job-card']",
            ".search-result",
            ".stellenangebot",  # German
        ]
        for selector in job_card_selectors:
            cards = soup.select(selector)
            if len(cards) > 3:
                indicators += 1
                break

        # Text patterns indicating search results
        page_text = soup.get_text()
        search_patterns = [
            r"aktuell\s+\d+\s+offen",  # "aktuell 9 offen"
            r"\d+\s+jobs?\s+gefunden",  # "15 Jobs gefunden"
            r"\d+\s+ergebnisse",  # "25 Ergebnisse"
            r"showing\s+\d+\s+of\s+\d+",  # "Showing 10 of 50"
            r"\d+\s+results?\s+found",  # "10 results found"
        ]
        for pattern in search_patterns:
            if re.search(pattern, page_text, re.I):
                indicators += 1
                break

        return indicators >= 2

    def _clean_text(self, text: str | None) -> str | None:
        """Clean extracted text: strip whitespace, normalize spaces, decode entities."""
        if not text:
            return None

        # Strip leading/trailing whitespace
        text = text.strip()

        # Normalize whitespace (multiple spaces/newlines to single space)
        text = re.sub(r"\s+", " ", text)

        # Remove zero-width characters
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)

        # Limit length for certain fields
        if len(text) > 10000:
            text = text[:10000] + "..."

        return text if text else None

    def _parse_date(self, date_str: str | None) -> str | None:
        """Parse date string to YYYY-MM-DD format."""
        if not date_str:
            return None

        try:
            # Try ISO format first (2024-01-15, 2024-01-15T10:00:00Z)
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass

        # Try German format (15.01.2024)
        try:
            match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
            if match:
                day, month, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except (ValueError, AttributeError):
            pass

        # Try US format (01/15/2024)
        try:
            match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
            if match:
                month, day, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except (ValueError, AttributeError):
            pass

        # Return original if parsing fails
        return date_str


# Registry of available job board parsers
JOB_BOARD_PARSERS: list[type[JobBoardParser]] = [
    IndeedParser,
    StepStoneParser,
    XingParser,
    SoftgardenParser,
    ArbeitsagenturParser,
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

    def fetch_job_posting(self, url: str) -> dict[str, Any]:
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

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception(
                    "Die Stellenanzeige ist nicht zugänglich (403 Forbidden). Job-Portale blockieren oft automatisierte Zugriffe. Versuchen Sie es mit manueller Eingabe."
                ) from e
            elif e.response.status_code == 404:
                raise Exception("Stellenanzeige nicht gefunden (404). Bitte überprüfen Sie die URL.") from e
            elif e.response.status_code == 429:
                raise Exception(
                    "Zu viele Anfragen (429). Bitte warten Sie einen Moment und versuchen Sie es erneut."
                ) from e
            else:
                raise Exception(
                    f"HTTP-Fehler beim Laden der Stellenanzeige ({e.response.status_code}): {str(e)}"
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

    def fetch_structured_job_posting(self, url: str) -> dict[str, Any]:
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

            return result

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception(
                    "Die Stellenanzeige ist nicht zugänglich (403 Forbidden). Job-Portale blockieren oft automatisierte Zugriffe. Versuchen Sie es mit manueller Eingabe."
                ) from e
            elif e.response.status_code == 404:
                raise Exception("Stellenanzeige nicht gefunden (404). Bitte überprüfen Sie die URL.") from e
            elif e.response.status_code == 429:
                raise Exception(
                    "Zu viele Anfragen (429). Bitte warten Sie einen Moment und versuchen Sie es erneut."
                ) from e
            else:
                raise Exception(
                    f"HTTP-Fehler beim Laden der Stellenanzeige ({e.response.status_code}): {str(e)}"
                ) from e
        except requests.RequestException as e:
            raise Exception(f"Fehler beim Laden der URL: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Fehler beim Parsen der Seite: {str(e)}") from e
