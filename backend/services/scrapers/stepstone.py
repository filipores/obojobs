import re
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
        json_ld_data = extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Fallback/supplement with HTML parsing
        result = self._parse_html(soup, result)

        return result

    def _parse_json_ld(self, data: dict, result: dict) -> dict:
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
        result["application_deadline"] = parse_date(data.get("validThrough"))

        # Employment type
        result["employment_type"] = parse_json_ld_employment_type(data)

        # Salary
        result["salary"] = parse_json_ld_salary(data)

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
            result["contact_email"] = find_contact_email(soup, ["support@stepstone"])

        return result
