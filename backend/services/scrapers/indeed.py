import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from services.scrapers.base import (
    JobBoardParser,
    extract_json_ld,
    find_contact_email,
    parse_date,
    parse_json_ld_employment_type,
    parse_json_ld_location,
    parse_json_ld_salary,
)


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

    def parse(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
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
        json_ld_data = extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Parse HTML for additional/fallback data
        result = self._parse_html(soup, result)

        return result

    def _parse_json_ld(self, data: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        """Parse JSON-LD JobPosting data into result dict."""
        result["title"] = data.get("title")
        result["description"] = data.get("description")

        # Company info
        hiring_org = data.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            result["company"] = hiring_org.get("name")

        # Location
        result["location"] = parse_json_ld_location(data.get("jobLocation"))

        # Dates
        result["posted_date"] = parse_date(data.get("datePosted"))

        # Employment type
        result["employment_type"] = parse_json_ld_employment_type(data)

        # Salary
        result["salary"] = parse_json_ld_salary(data)

        return result

    def _parse_html(self, soup: BeautifulSoup, result: dict[str, Any]) -> dict[str, Any]:
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
                # Check if it's a salary (contains EUR or numbers with ranges)
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
            result["contact_email"] = find_contact_email(soup, ["support@indeed", "info@indeed"])

        return result
