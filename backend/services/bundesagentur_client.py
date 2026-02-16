"""
Bundesagentur für Arbeit Job Search API Client.

Uses the free public API at rest.arbeitsagentur.de to search for jobs.
API docs: https://jobsuche.api.bund.dev/
"""

import logging
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)


@dataclass
class BundesagenturJob:
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
        """Convert to the standard job data format used by the recommender."""
        return {
            "title": self.titel,
            "company": self.arbeitgeber,
            "location": self.arbeitsort,
            "url": self.url or f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{self.refnr}",
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
        self.session.headers.update(
            {
                "X-API-Key": self.API_KEY,
                "User-Agent": "obojobs/1.0",
            }
        )

    def search_jobs(
        self,
        keywords: str,
        location: str = "",
        radius_km: int = 50,
        working_time: str = "",
        published_since_days: int = 14,
        page: int = 1,
        size: int = 25,
    ) -> tuple[list[BundesagenturJob], int]:
        """Search for jobs. working_time: 'vz' (Vollzeit), 'tz' (Teilzeit), 'ho' (Homeoffice)."""
        params = {
            "was": keywords,
            "page": page,
            "size": min(size, 100),
            "veroeffentlichtseit": published_since_days,
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
            logger.error("Bundesagentur API error: %s", e)
            return [], 0
        except ValueError:
            logger.error("Bundesagentur API returned invalid JSON")
            return [], 0

        total = data.get("maxErgebnisse", 0)
        stellenangebote = data.get("stellenangebote", [])

        jobs = [self._parse_job(item) for item in stellenangebote]

        return jobs, total

    def get_job_details(self, refnr: str) -> BundesagenturJob | None:
        """Fetch full job details including description, or None if not found.

        NOTE: This endpoint currently returns 403 (deprecated by Bundesagentur).
        Kept for backwards compatibility; callers should handle None gracefully.
        """
        url = f"{self.BASE_URL}/{refnr}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Bundesagentur detail API error for %s: %s", refnr, e)
            return None
        except ValueError:
            return None

        description_parts = [data[key] for key in ("stellenbeschreibung", "arbeitgeberdarstellung") if data.get(key)]

        job = self._parse_job(data)
        job.refnr = data.get("refnr", refnr)
        job.beschreibung = "\n\n".join(description_parts)
        return job

    def _job_url(self, refnr: str) -> str:
        return f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

    def _parse_job(self, item: dict) -> BundesagenturJob:
        arbeitsort = item.get("arbeitsort", {})
        refnr = item.get("refnr", "")
        return BundesagenturJob(
            refnr=refnr,
            titel=item.get("titel", ""),
            beruf=item.get("beruf", ""),
            arbeitgeber=item.get("arbeitgeber", ""),
            arbeitsort=self._parse_arbeitsort(arbeitsort),
            arbeitsort_plz=arbeitsort.get("plz", ""),
            eintrittsdatum=item.get("eintrittsdatum", ""),
            veroeffentlicht_am=item.get("aktuelleVeroeffentlichungsdatum", ""),
            befristung=item.get("befristung", ""),
            arbeitszeit=item.get("arbeitszeit", ""),
            url=self._job_url(refnr),
        )

    def _parse_arbeitsort(self, ort_data: dict) -> str:
        """Parse location data into a readable string."""
        if not ort_data:
            return ""
        parts = []
        for key in ("ort", "region"):
            val = ort_data.get(key)
            if val and val not in parts:
                parts.append(val)
        return ", ".join(parts)
