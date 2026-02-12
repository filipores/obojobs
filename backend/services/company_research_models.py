"""
Data models for Company Researcher Service.
"""


class CompanyResearchResult:
    """Data class for company research results."""

    def __init__(
        self,
        company_name: str,
        website_url: str | None = None,
        industry: str | None = None,
        company_size: str | None = None,
        locations: list[str] | None = None,
        products_services: list[str] | None = None,
        about_text: str | None = None,
        mission_values: str | None = None,
        founded_year: str | None = None,
        interview_tips: list[str] | None = None,
        source_urls: list[str] | None = None,
        cached_at: str | None = None,
    ):
        self.company_name = company_name
        self.website_url = website_url
        self.industry = industry
        self.company_size = company_size
        self.locations = locations or []
        self.products_services = products_services or []
        self.about_text = about_text
        self.mission_values = mission_values
        self.founded_year = founded_year
        self.interview_tips = interview_tips or []
        self.source_urls = source_urls or []
        self.cached_at = cached_at

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "company_name": self.company_name,
            "website_url": self.website_url,
            "industry": self.industry,
            "company_size": self.company_size,
            "locations": self.locations,
            "products_services": self.products_services,
            "about_text": self.about_text,
            "mission_values": self.mission_values,
            "founded_year": self.founded_year,
            "interview_tips": self.interview_tips,
            "source_urls": self.source_urls,
            "cached_at": self.cached_at,
        }
