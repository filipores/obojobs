"""Extraction strategies for the generic job parser.

Each function takes (soup, result, ...) and returns the updated result dict.
"""

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


def clean_text(text: str | None) -> str | None:
    """Clean extracted text: strip whitespace, normalize spaces, decode entities."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    if len(text) > 10000:
        text = text[:10000] + "..."
    return text if text else None


def extract_opengraph(soup: BeautifulSoup, result: dict) -> tuple[dict, bool]:
    """Extract data from OpenGraph meta tags. Returns (result, extracted)."""
    extracted = False

    if not result["title"]:
        og_title = soup.find("meta", property="og:title")
        if isinstance(og_title, Tag):
            content = og_title.get("content")
            if content:
                result["title"] = clean_text(str(content))
                extracted = True

    if not result["description"]:
        og_desc = soup.find("meta", property="og:description")
        if isinstance(og_desc, Tag):
            content = og_desc.get("content")
            if content:
                result["description"] = clean_text(str(content))
                extracted = True

    if not result["company"]:
        og_site = soup.find("meta", property="og:site_name")
        if isinstance(og_site, Tag):
            content = og_site.get("content")
            if content:
                result["company"] = clean_text(str(content))
                extracted = True

    return result, extracted


def extract_meta_tags(soup: BeautifulSoup, result: dict) -> tuple[dict, bool]:
    """Extract data from standard meta tags. Returns (result, extracted)."""
    extracted = False

    if not result["title"]:
        meta_title = soup.find("meta", attrs={"name": "title"})
        if isinstance(meta_title, Tag):
            content = meta_title.get("content")
            if content:
                result["title"] = clean_text(str(content))
                extracted = True

    if not result["description"]:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if isinstance(meta_desc, Tag):
            content = meta_desc.get("content")
            if content:
                result["description"] = clean_text(str(content))
                extracted = True

    if not result["company"]:
        meta_author = soup.find("meta", attrs={"name": "author"})
        if isinstance(meta_author, Tag):
            content = meta_author.get("content")
            if content:
                result["company"] = clean_text(str(content))
                extracted = True

    return result, extracted


def extract_from_title_tag(soup: BeautifulSoup, result: dict) -> tuple[dict, bool]:
    """Extract job title and company from <title> tag.

    Common patterns:
    - "Job Title - Company Name"
    - "Job Title | Company Name"
    - "Job Title at Company Name"
    - "Job Title bei Company Name" (German)
    """
    if result["title"] and result["company"]:
        return result, False

    title_tag = soup.find("title")
    if not title_tag:
        return result, False

    title_text = title_tag.get_text(strip=True)
    if not title_text:
        return result, False

    extracted = False

    # Try splitting by common separators
    separators = [" - ", " | ", " – ", " — ", " · "]
    for sep in separators:
        if sep in title_text:
            parts = title_text.split(sep)
            if len(parts) >= 2:
                if not result["title"]:
                    result["title"] = clean_text(parts[0])
                    extracted = True
                if not result["company"]:
                    company_part = parts[-1] if len(parts) > 2 else parts[1]
                    company_part = re.sub(
                        r"\s*[-–|]\s*(Jobs?|Karriere|Career|Stellenangebote?).*$", "", company_part, flags=re.I
                    )
                    if company_part:
                        result["company"] = clean_text(company_part)
                        extracted = True
                break

    # Try "at" / "bei" pattern
    if not result["title"] or not result["company"]:
        at_match = re.match(r"^(.+?)\s+(?:at|bei|@)\s+(.+?)(?:\s*[-|–].*)?$", title_text, re.I)
        if at_match:
            if not result["title"]:
                result["title"] = clean_text(at_match.group(1))
                extracted = True
            if not result["company"]:
                result["company"] = clean_text(at_match.group(2))
                extracted = True

    # Fallback: use entire title if nothing else worked
    if not result["title"] and title_text:
        cleanup_patterns = [
            r"\s*\|\s*aktuell\s+\d+\s+offen",
            r"\s*\|\s*karriere\.at",
            r"\s*\|\s*stepstone\.at",
            r"\s*\|\s*stepstone\.de",
            r"\s+Jobs?\s+in\s+[\wäöüÄÖÜß]+(?:\s|$)",
            r"\s*[-–|]\s*(Jobs?|Karriere|Career|Stellenangebote?|Apply|Bewerben).*$",
        ]
        clean_title = title_text
        for pattern in cleanup_patterns:
            clean_title = re.sub(pattern, "", clean_title, flags=re.I)
        clean_title = clean_title.strip()
        if clean_title:
            result["title"] = clean_text(clean_title)
            extracted = True

    return result, extracted


def extract_html_patterns(soup: BeautifulSoup, result: dict, url: str) -> tuple[dict, bool]:
    """Extract data using common HTML patterns and selectors."""
    extracted = False

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
                result["title"] = clean_text(elem.get_text())
                extracted = True
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
                name_elem = elem.find(attrs={"itemprop": "name"})
                if name_elem:
                    result["company"] = clean_text(name_elem.get_text())
                else:
                    result["company"] = clean_text(elem.get_text())
                extracted = True
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
                addr_elem = elem.find(attrs={"itemprop": "address"})
                if addr_elem:
                    result["location"] = clean_text(addr_elem.get_text())
                else:
                    result["location"] = clean_text(elem.get_text())
                extracted = True
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
                result["description"] = clean_text(elem.get_text(separator="\n"))
                extracted = True
                break

        if not result["description"]:
            for tag in ["article", "main"]:
                elem = soup.find(tag)
                if elem:
                    text = elem.get_text(separator="\n", strip=True)
                    if len(text) > 200:
                        result["description"] = clean_text(text)
                        extracted = True
                        break

    # Employment type
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
                    extracted = True
                    break
            if result["employment_type"]:
                break

    # Contact email
    if not result["contact_email"]:
        page_text = soup.get_text()
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        emails = email_pattern.findall(page_text)
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
            extracted = True

    return result, extracted


def apply_heuristics(soup: BeautifulSoup, result: dict, url: str) -> tuple[dict, bool]:
    """Apply heuristic extraction as last resort."""
    used = False

    # First h1 as job title
    if not result["title"]:
        h1 = soup.find("h1")
        if h1:
            title_text = h1.get_text(strip=True)
            generic_headings = ["jobs", "karriere", "career", "stellenangebote", "home"]
            if title_text.lower() not in generic_headings and len(title_text) > 3:
                result["title"] = clean_text(title_text)
                used = True

    # Company from domain name
    if not result["company"]:
        parsed = urlparse(url)
        hostname = parsed.netloc.lower().replace("www.", "")
        domain_parts = hostname.split(".")
        if len(domain_parts) >= 2:
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
                "karriere",
                "jobware",
                "stellenanzeigen",
                "hokify",
                "willhaben",
            ]
            base_domain = domain_parts[0]
            if base_domain not in job_board_domains:
                company_name = base_domain.replace("-", " ").replace("_", " ").title()
                result["company"] = company_name
                used = True

    # Look for salary patterns in page text
    if not result["salary"]:
        page_text = soup.get_text()
        salary_patterns = [
            r"(\d{1,3}(?:[.,]\d{3})*)\s*[-–bis]+\s*(\d{1,3}(?:[.,]\d{3})*)\s*(?:€|EUR|Euro)",
            r"(?:ab|from|starting)\s+(\d{1,3}(?:[.,]\d{3})*)\s*(?:€|EUR|Euro)",
            r"(\d{1,3})\s*[-–]\s*(\d{1,3})\s*(?:€|EUR)/\s*(?:h|Stunde|hour)",
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                result["salary"] = match.group(0).strip()
                used = True
                break

    return result, used


def is_search_results_page(soup: BeautifulSoup, url: str) -> bool:
    """Detect if URL is a search results page rather than a single job posting."""
    indicators = 0

    url_lower = url.lower()
    if any(pattern in url_lower for pattern in ["/search", "/jobs?", "/suche", "?q=", "&q=", "/results"]):
        indicators += 1

    job_card_selectors = [
        "[data-job-id]",
        ".job-card",
        ".job-listing",
        ".job-item",
        "[data-testid*='job-card']",
        ".search-result",
        ".stellenangebot",
    ]
    for selector in job_card_selectors:
        cards = soup.select(selector)
        if len(cards) > 3:
            indicators += 1
            break

    page_text = soup.get_text()
    search_patterns = [
        r"aktuell\s+\d+\s+offen",
        r"\d+\s+jobs?\s+gefunden",
        r"\d+\s+ergebnisse",
        r"showing\s+\d+\s+of\s+\d+",
        r"\d+\s+results?\s+found",
    ]
    for pattern in search_patterns:
        if re.search(pattern, page_text, re.I):
            indicators += 1
            break

    return indicators >= 2
