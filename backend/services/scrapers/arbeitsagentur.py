import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from services.scrapers.base import (
    JobBoardParser,
    extract_json_ld,
    find_contact_email,
    parse_date,
    parse_json_ld_employment_type,
    parse_json_ld_location,
    parse_json_ld_salary,
)


class ArbeitsagenturParser(JobBoardParser):
    """Parser for Bundesagentur fur Arbeit job postings."""

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

    def parse(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
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
        result["application_deadline"] = parse_date(data.get("validThrough"))

        # Employment type
        result["employment_type"] = parse_json_ld_employment_type(data)

        # Salary
        result["salary"] = parse_json_ld_salary(data)

        # Identifier (Referenznummer)
        identifier = data.get("identifier", {})
        if isinstance(identifier, dict):
            result["reference_number"] = identifier.get("value")
        elif isinstance(identifier, str):
            result["reference_number"] = identifier

        return result

    def _find_by_label(
        self, soup: BeautifulSoup, label_pattern: str, parent_tags: list[str] | None = None
    ) -> str | None:
        """Find a value adjacent to a label like 'Arbeitgeber:' in the HTML.

        Searches for text matching '{label_pattern}:' then navigates to the parent
        element and returns the next sibling's text, or strips the label prefix from
        the parent text if no sibling is found.
        """
        if parent_tags is None:
            parent_tags = ["div", "p", "span", "dt", "li"]

        label = soup.find(string=re.compile(label_pattern + r"\s*:", re.I))
        if not label:
            return None

        parent = label.find_parent(parent_tags)
        if not parent:
            return None

        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
        if next_sibling:
            return next_sibling.get_text(strip=True)

        text = parent.get_text(strip=True)
        cleaned = re.sub(r"^" + label_pattern + r"\s*:\s*", "", text, flags=re.I)
        return cleaned or None

    def _parse_html(self, soup: BeautifulSoup, result: dict[str, Any]) -> dict[str, Any]:
        """Parse HTML for Arbeitsagentur-specific elements."""
        # Title - look for various patterns
        if not result["title"]:
            title_elem = soup.find(attrs={"data-testid": "job-title"})
            if not title_elem:
                title_elem = soup.find(class_=re.compile(r"job-title|jobtitle|stellentitel", re.I))
            if not title_elem:
                # On jobdetail pages, h1 is generic ("Detailansicht des Stellenangebots")
                # The actual job title is in h2
                h1 = soup.find("h1")
                if h1 and "detailansicht" in h1.get_text(strip=True).lower():
                    title_elem = soup.find("h2")
                else:
                    title_elem = h1
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company name - Arbeitsagentur uses "Arbeitgeber" (employer)
        if not result["company"]:
            company_elem = soup.find(attrs={"data-testid": "company-name"})
            if not company_elem:
                company_elem = soup.find(class_=re.compile(r"arbeitgeber|employer|company|firma", re.I))
            if not company_elem:
                result["company"] = self._find_by_label(soup, r"Arbeitgeber", ["div", "p", "span", "dt", "li", "h3"])
            if company_elem and not result["company"]:
                # Clean "Arbeitgeber:" prefix from the extracted text
                raw = company_elem.get_text(strip=True)
                result["company"] = re.sub(r"^Arbeitgeber\s*:\s*", "", raw, flags=re.I)

        # Location - "Arbeitsort"
        if not result["location"]:
            location_elem = soup.find(attrs={"data-testid": "job-location"})
            if not location_elem:
                location_elem = soup.find(class_=re.compile(r"arbeitsort|location|standort", re.I))
            if not location_elem:
                result["location"] = self._find_by_label(soup, r"Arbeitsort")
            if location_elem and not result["location"]:
                result["location"] = location_elem.get_text(strip=True)

        # Reference number (Referenznummer) - specific to Arbeitsagentur
        if not result["reference_number"]:
            ref_elem = soup.find(class_=re.compile(r"referenz|reference|stellennummer", re.I))
            if not ref_elem:
                result["reference_number"] = self._find_by_label(soup, r"(?:Referenz|Stellen)nummer")
            if ref_elem and not result["reference_number"]:
                result["reference_number"] = ref_elem.get_text(strip=True)
            # Fallback: search for common reference number patterns in page text
            if not result["reference_number"]:
                page_text = soup.get_text()
                ref_match = re.search(
                    r"(?:Referenz(?:nummer)?|Stellen(?:nummer)?)[:\s]+([A-Z0-9\-/]+)", page_text, re.I
                )
                if ref_match:
                    result["reference_number"] = ref_match.group(1).strip()

        # Contact person (Ansprechpartner)
        if not result["contact_person"]:
            contact_elem = soup.find(class_=re.compile(r"ansprechpartner|kontakt|contact-person", re.I))
            if not contact_elem:
                result["contact_person"] = self._find_by_label(soup, r"Ansprechpartner")
            if contact_elem and not result["contact_person"]:
                result["contact_person"] = contact_elem.get_text(strip=True)

        # Contact phone (Telefon)
        if not result["contact_phone"]:
            phone_elem = soup.find(class_=re.compile(r"telefon|phone", re.I))
            if not phone_elem:
                result["contact_phone"] = self._find_by_label(soup, r"Telefon")
            if phone_elem and not result["contact_phone"]:
                result["contact_phone"] = phone_elem.get_text(strip=True)
            # Fallback: search for German phone number patterns in page text
            if not result["contact_phone"]:
                page_text = soup.get_text()
                phone_match = re.search(
                    r"(?:Tel(?:efon)?\.?\s*:?\s*)?((?:\+49|0)[\s\-/]*(?:\(\d+\)|\d+)[\s\-/]*[\d\s\-/]{6,})",
                    page_text,
                    re.I,
                )
                if phone_match:
                    phone = re.sub(r"\s+", " ", phone_match.group(1).strip())
                    if len(phone) >= 8:
                        result["contact_phone"] = phone

        # Description
        if not result["description"]:
            desc_elem = soup.find(attrs={"data-testid": "job-description"})
            if not desc_elem:
                desc_elem = soup.find(class_=re.compile(r"job-description|beschreibung|stellenbeschreibung", re.I))
            if not desc_elem:
                desc_elem = soup.find("article") or soup.find("main")
            if desc_elem:
                result["description"] = desc_elem.get_text(separator="\n", strip=True)

        # Requirements
        if not result["requirements"]:
            req_section = soup.find(string=re.compile(r"(Anforderungen|Ihr Profil|Qualifikation|Voraussetzung)", re.I))
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

        # Employment type
        if not result["employment_type"]:
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

        # Posted date
        if not result["posted_date"]:
            date_label = soup.find(string=re.compile(r"(Online seit|Eingestellt am|Veröffentlicht)\s*:", re.I))
            if date_label:
                parent = date_label.find_parent(["div", "p", "span", "dt", "li"])
                if parent:
                    text = parent.get_text(strip=True)
                    date_pattern = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
                    date_match = date_pattern.search(text)
                    if date_match:
                        day, month, year = date_match.groups()
                        result["posted_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Contact email
        if not result["contact_email"]:
            result["contact_email"] = find_contact_email(
                soup,
                ["@arbeitsagentur.de", "support@", "info@arbeitsagentur"],
            )

        # Fallback: if description is empty, look for Kooperationspartner
        # external link that may contain the full job posting
        if not result.get("description"):
            koop_link = soup.find(
                "a", href=re.compile(r"https?://", re.I), string=re.compile(r"Kooperationspartner", re.I)
            )
            if koop_link:
                result["kooperationspartner_url"] = koop_link["href"]

        return result
