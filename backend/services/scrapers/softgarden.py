import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from services.scrapers.base import (
    JobBoardParser,
    extract_json_ld,
    find_contact_email,
    parse_date,
    parse_json_ld_employment_type,
    parse_json_ld_salary,
)


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

        # Location - Softgarden may include addressCountry
        job_location = data.get("jobLocation", {})
        if isinstance(job_location, dict):
            address = job_location.get("address", {})
            if isinstance(address, dict):
                parts = []
                for field in ["streetAddress", "postalCode", "addressLocality", "addressRegion"]:
                    if address.get(field):
                        parts.append(address[field])
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
        result["posted_date"] = parse_date(data.get("datePosted"))
        result["application_deadline"] = parse_date(data.get("validThrough"))

        # Employment type
        result["employment_type"] = parse_json_ld_employment_type(data)

        # Salary
        result["salary"] = parse_json_ld_salary(data)

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
            # German salary patterns: "50.000 - 70.000 EUR", "ab 45.000 EUR"
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
            result["contact_email"] = find_contact_email(
                soup,
                ["support@softgarden", "info@softgarden", "datenschutz", "privacy", "tracking"],
            )

        return result
