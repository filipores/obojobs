import re
from urllib.parse import urljoin, urlparse

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
        json_ld_data = extract_json_ld(soup)
        if json_ld_data:
            result = self._parse_json_ld(json_ld_data, result)

        # Parse HTML for additional/fallback data
        result = self._parse_html(soup, result, url)

        return result

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
        result["location"] = parse_json_ld_location(data.get("jobLocation"))

        # Dates
        result["posted_date"] = parse_date(data.get("datePosted"))
        result["application_deadline"] = parse_date(data.get("validThrough"))

        # Employment type
        result["employment_type"] = parse_json_ld_employment_type(data)

        # Salary
        result["salary"] = parse_json_ld_salary(data)

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
            result["contact_email"] = find_contact_email(
                soup,
                ["support@xing", "info@xing", "kundenservice@xing", "werbung@xing"],
            )

        return result
