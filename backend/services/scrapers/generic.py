import json
import logging
from typing import Any

from bs4 import BeautifulSoup

from services.scrapers.base import parse_date
from services.scrapers.generic_extractors import (
    apply_heuristics,
    clean_text,
    extract_from_title_tag,
    extract_html_patterns,
    extract_meta_tags,
    extract_opengraph,
    is_search_results_page,
)

logger = logging.getLogger(__name__)


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

    def parse(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
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
        result, og_extracted = extract_opengraph(soup, result)
        if og_extracted:
            result["extraction_methods"].append("opengraph")
            logger.debug("GenericJobParser: Extracted data via OpenGraph")

        # Strategy 3: Standard meta tags
        result, meta_extracted = extract_meta_tags(soup, result)
        if meta_extracted:
            result["extraction_methods"].append("meta-tags")
            logger.debug("GenericJobParser: Extracted data via meta tags")

        # Strategy 4: Title tag parsing
        result, title_extracted = extract_from_title_tag(soup, result)
        if title_extracted:
            result["extraction_methods"].append("title-tag")
            logger.debug("GenericJobParser: Extracted data via title tag")

        # Strategy 5: Common HTML patterns
        result, html_extracted = extract_html_patterns(soup, result, url)
        if html_extracted:
            result["extraction_methods"].append("html-patterns")
            logger.debug("GenericJobParser: Extracted data via HTML patterns")

        # Strategy 6: Heuristics
        result, heuristic_used = apply_heuristics(soup, result, url)
        if heuristic_used:
            result["extraction_methods"].append("heuristics")
            logger.debug("GenericJobParser: Applied heuristic extraction")

        # Check if this appears to be a search results page
        if is_search_results_page(soup, url):
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

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict[str, Any] | None:
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

    def _parse_json_ld(self, data: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        """Parse JSON-LD JobPosting schema into result dict."""
        if not result["title"] and data.get("title"):
            result["title"] = clean_text(data["title"])

        if not result["description"] and data.get("description"):
            result["description"] = clean_text(data["description"])

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
            result["posted_date"] = parse_date(data["datePosted"])

        if not result["application_deadline"] and data.get("validThrough"):
            result["application_deadline"] = parse_date(data["validThrough"])

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
                elif isinstance(value, int | float):
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
