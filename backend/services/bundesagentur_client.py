"""
Bundesagentur für Arbeit Job Search API Client.

Uses the free public API at rest.arbeitsagentur.de to search for jobs.
API docs: https://jobsuche.api.bund.dev/
"""

import time
from dataclasses import dataclass, field
from datetime import datetime

import requests


@dataclass
class BundesagenturJob:
    """A job listing from the Bundesagentur API."""
    refnr: str
    titel: str
    beruf: str = ""
    arbeitgeber: str = ""
    arbeitsort: str = ""
    arbeitsort_plz: str = ""
    eintrittsdatum: str = ""
    veroeffentlicht_am: str = ""
    befristung: str = ""
    arbeitszeit: str = ""
    beschreibung: str = ""
    url: str = ""
    extras: dict = field(default_factory=dict)

    def to_job_data(self) -> dict:
        """Convert to the standard job data format used by JobRecommender."""
        return {
            "title": self.titel,
            "company": self.arbeitgeber,
            "location": self.arbeitsort,
            "url": self.url or f"https://www.arbeitsagentur.de/jobsuche/suche?id={self.refnr}",
            "source": "arbeitsagentur",
            "description": self.beschreibung,
        }


class BundesagenturClient:
    """Client for the Bundesagentur für Arbeit Job Search API."""

    BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
    API_KEY = "jobboerse-jobsuche"
    DETAIL_DELAY = 0.5  # seconds between detail requests

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.API_KEY,
            "User-Agent": "obojobs/1.0",
        })

    def search_jobs(
        self,
        keywords: str,
        location: str = "",
        radius_km: int = 50,
        working_time: str = "",
        published_since_days: int = 7,
        page: int = 1,
        size: int = 25,
    ) -> tuple[list[BundesagenturJob], int]:
        """
        Search for jobs on the Bundesagentur API.

        Args:
            keywords: Search keywords (e.g. "Python Developer")
            location: City or region name
            radius_km: Search radius in km (default 50)
            working_time: Filter: "vz" (Vollzeit), "tz" (Teilzeit), "ho" (Homeoffice), or "" (all)
            published_since_days: Only show jobs published within N days
            page: Page number (1-based)
            size: Results per page (max 100)

        Returns:
            Tuple of (list of BundesagenturJob, total_count)
        """
        params = {
            "was": keywords,
            "page": page,
            "size": min(size, 100),
            "pav": f"D{published_since_days}",  # published since: D7 = 7 days
        }

        if location:
            params["wo"] = location
            params["umkreis"] = radius_km

        if working_time:
            params["arbeitszeit"] = working_time

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Bundesagentur API error: {e}")
            return [], 0
        except ValueError:
            print("Bundesagentur API returned invalid JSON")
            return [], 0

        total = data.get("maxErgebnisse", 0)
        stellenangebote = data.get("stellenangebote", [])

        jobs = []
        for item in stellenangebote:
            job = BundesagenturJob(
                refnr=item.get("refnr", ""),
                titel=item.get("titel", ""),
                beruf=item.get("beruf", ""),
                arbeitgeber=item.get("arbeitgeber", ""),
                arbeitsort=self._parse_arbeitsort(item.get("arbeitsort", {})),
                arbeitsort_plz=item.get("arbeitsort", {}).get("plz", ""),
                eintrittsdatum=item.get("eintrittsdatum", ""),
                veroeffentlicht_am=item.get("aktuelleVeroeffentlichungsdatum", ""),
                befristung=item.get("befristung", ""),
                arbeitszeit=item.get("arbeitszeit", ""),
                url=f"https://www.arbeitsagentur.de/jobsuche/suche?id={item.get('refnr', '')}",
            )
            jobs.append(job)

        return jobs, total

    def get_job_details(self, refnr: str) -> BundesagenturJob | None:
        """
        Get full details for a job listing including description.

        Args:
            refnr: The job reference number

        Returns:
            BundesagenturJob with full description, or None if not found
        """
        url = f"{self.BASE_URL}/{refnr}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Bundesagentur detail API error for {refnr}: {e}")
            return None
        except ValueError:
            return None

        # Build description from available fields
        description_parts = []
        if data.get("stellenbeschreibung"):
            description_parts.append(data["stellenbeschreibung"])
        if data.get("arbeitgeberdarstellung"):
            description_parts.append(data["arbeitgeberdarstellung"])

        arbeitsort = data.get("arbeitsort", {})

        return BundesagenturJob(
            refnr=data.get("refnr", refnr),
            titel=data.get("titel", ""),
            beruf=data.get("beruf", ""),
            arbeitgeber=data.get("arbeitgeber", ""),
            arbeitsort=self._parse_arbeitsort(arbeitsort),
            arbeitsort_plz=arbeitsort.get("plz", ""),
            eintrittsdatum=data.get("eintrittsdatum", ""),
            veroeffentlicht_am=data.get("aktuelleVeroeffentlichungsdatum", ""),
            befristung=data.get("befristung", ""),
            arbeitszeit=data.get("arbeitszeit", ""),
            beschreibung="\n\n".join(description_parts),
            url=f"https://www.arbeitsagentur.de/jobsuche/suche?id={refnr}",
        )

    def _parse_arbeitsort(self, ort_data: dict) -> str:
        """Parse location data into a readable string."""
        if not ort_data:
            return ""

        parts = []
        if ort_data.get("ort"):
            parts.append(ort_data["ort"])
        if ort_data.get("region"):
            parts.append(ort_data["region"])

        return ", ".join(parts) if parts else ""
