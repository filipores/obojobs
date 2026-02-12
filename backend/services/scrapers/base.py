import json
import re
from abc import ABC, abstractmethod
from datetime import datetime

from bs4 import BeautifulSoup


class JobBoardParser(ABC):
    """Abstract base class for job board specific parsers."""

    @staticmethod
    @abstractmethod
    def matches_url(url: str) -> bool:
        """Check if this parser can handle the given URL."""

    @abstractmethod
    def parse(self, soup: BeautifulSoup, url: str) -> dict:
        """Parse the job posting and return structured data."""


def extract_json_ld(soup: BeautifulSoup) -> dict | None:
    """Extract JSON-LD structured data with @type JobPosting from page."""
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


def parse_json_ld_location(job_location) -> str | None:
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
            for field in ["streetAddress", "postalCode", "addressLocality", "addressRegion"]:
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
            parsed = parse_json_ld_location(loc)
            if parsed:
                locations.append(parsed)
        return ", ".join(locations) if locations else None

    return None


def parse_json_ld_salary(data: dict) -> str | None:
    """Parse baseSalary from JSON-LD data."""
    salary = data.get("baseSalary", {})
    if isinstance(salary, dict):
        value = salary.get("value", {})
        if isinstance(value, dict):
            min_val = value.get("minValue")
            max_val = value.get("maxValue")
            currency = salary.get("currency", "EUR")
            if min_val and max_val:
                return f"{min_val}-{max_val} {currency}"
            if min_val:
                return f"ab {min_val} {currency}"
        elif isinstance(value, int | float):
            currency = salary.get("currency", "EUR")
            return f"{value} {currency}"
    return None


def parse_json_ld_employment_type(data: dict) -> str | None:
    """Parse employmentType from JSON-LD data."""
    emp_type = data.get("employmentType")
    if emp_type:
        if isinstance(emp_type, list):
            return ", ".join(emp_type)
        return emp_type
    return None


def parse_date(date_str: str | None) -> str | None:
    """Parse date string to YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        pass
    # Try German format (DD.MM.YYYY)
    try:
        match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except (ValueError, AttributeError):
        pass
    return date_str


def find_contact_email(soup: BeautifulSoup, exclude_patterns: list[str] | None = None) -> str | None:
    """Search page text for contact email addresses, filtering out common non-contact ones."""
    default_exclude = ["noreply", "no-reply", "newsletter"]
    all_exclude = default_exclude + (exclude_patterns or [])
    email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    page_text = soup.get_text()
    emails = email_pattern.findall(page_text)
    contact_emails = [e for e in emails if not any(x in e.lower() for x in all_exclude)]
    return contact_emails[0] if contact_emails else None
