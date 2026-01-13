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
                    if re.search(r"\b(Berlin|Hamburg|München|Köln|Frankfurt|Stuttgart|Düsseldorf|Leipzig|Dresden|Hannover)\b", text, re.I):
                        result["location"] = text
                        break
            if location_elem:
                result["location"] = location_elem.get_text(strip=True)

        # Company profile URL
        if not result["company_profile_url"]:
            company_link = soup.find("a", href=re.compile(r"xing\.com/companies/"))
            if not company_link:
                company_link = soup.find("a", href=re.compile(r"/companies/"))
            if company_link:
                href = company_link.get("href", "")
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
                contact_text = re.sub(r"^(Recruiter|Ansprechpartner|Contact|Kontakt)[:\s]*", "", contact_text, flags=re.I)
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
            contact_emails = [e for e in emails if not any(
                x in e.lower() for x in ["noreply", "no-reply", "newsletter", "support@xing",
                                         "info@xing", "kundenservice@xing", "werbung@xing"]
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
        is_arbeitsagentur = (
            hostname in ["arbeitsagentur.de", "con.arbeitsagentur.de"]
            or hostname.endswith(".arbeitsagentur.de")
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
                phone_pattern = re.compile(r"(?:Tel(?:efon)?\.?\s*:?\s*)?((?:\+49|0)[\s\-/]*(?:\(\d+\)|\d+)[\s\-/]*[\d\s\-/]{6,})", re.I)
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
            contact_emails = [e for e in emails if not any(
                x in e.lower() for x in ["noreply", "no-reply", "newsletter",
                                         "@arbeitsagentur.de", "support@", "info@arbeitsagentur"]
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


# Registry of available job board parsers
JOB_BOARD_PARSERS: list[type[JobBoardParser]] = [
    IndeedParser,
    StepStoneParser,
    XingParser,
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
