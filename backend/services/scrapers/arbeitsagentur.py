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

    def _parse_html(self, soup: BeautifulSoup, result: dict[str, Any]) -> dict[str, Any]:
        """Parse HTML for Arbeitsagentur-specific elements."""
        # Title - look for various patterns
        if not result["title"]:
            title_elem = soup.find(attrs={"data-testid": "job-title"})
            if not title_elem:
                title_elem = soup.find(class_=re.compile(r"job-title|jobtitle|stellentitel", re.I))
            if not title_elem:
                title_elem = soup.find("h1")
            if title_elem:
                result["title"] = title_elem.get_text(strip=True)

        # Company name - Arbeitsagentur uses "Arbeitgeber" (employer)
        if not result["company"]:
            company_elem = soup.find(attrs={"data-testid": "company-name"})
            if not company_elem:
                company_elem = soup.find(class_=re.compile(r"arbeitgeber|employer|company|firma", re.I))
            if not company_elem:
                # Search for "Arbeitgeber:" label
                arbeitgeber_label = soup.find(string=re.compile(r"Arbeitgeber\s*:", re.I))
                if arbeitgeber_label:
                    parent = arbeitgeber_label.find_parent(["div", "p", "span", "dt", "li"])
                    if parent:
                        next_sibling = parent.find_next_sibling(["div", "p", "span", "dd"])
                        if next_sibling:
                            company_elem = next_sibling
                        else:
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

        # Contact person (Ansprechpartner)
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
                phone_pattern = re.compile(
                    r"(?:Tel(?:efon)?\.?\s*:?\s*)?((?:\+49|0)[\s\-/]*(?:\(\d+\)|\d+)[\s\-/]*[\d\s\-/]{6,})", re.I
                )
                phone_match = phone_pattern.search(page_text)
                if phone_match:
                    phone = phone_match.group(1).strip()
                    phone = re.sub(r"\s+", " ", phone)
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

        return result
