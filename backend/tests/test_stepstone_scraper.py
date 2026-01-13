"""
Tests for StepStone job board scraper.
"""

import pytest
from bs4 import BeautifulSoup

from services.web_scraper import StepStoneParser, WebScraper


class TestStepStoneURLMatching:
    """Test URL pattern matching for StepStone."""

    def test_matches_stepstone_job_url(self):
        """Should match valid StepStone job posting URLs."""
        valid_urls = [
            "https://www.stepstone.de/stellenangebote--Softwareentwickler-Berlin-Firma-XY--12345.html",
            "https://stepstone.de/stellenangebote--Python-Developer-Muenchen--67890.html",
            "https://www.stepstone.de/stellenangebote--Senior-Developer-Hamburg-ABC-GmbH--11111.html",
        ]
        for url in valid_urls:
            assert StepStoneParser.matches_url(url) is True, f"Should match: {url}"

    def test_does_not_match_other_stepstone_pages(self):
        """Should not match non-job pages on StepStone."""
        invalid_urls = [
            "https://www.stepstone.de/",
            "https://www.stepstone.de/jobs",
            "https://www.stepstone.de/kandidat/login",
            "https://www.stepstone.de/unternehmen",
        ]
        for url in invalid_urls:
            assert StepStoneParser.matches_url(url) is False, f"Should not match: {url}"

    def test_does_not_match_other_domains(self):
        """Should not match other job boards."""
        other_domains = [
            "https://www.indeed.de/viewjob?jk=12345",
            "https://www.xing.com/jobs/12345",
            "https://www.linkedin.com/jobs/view/12345",
        ]
        for url in other_domains:
            assert StepStoneParser.matches_url(url) is False, f"Should not match: {url}"


class TestStepStoneJSONLDParsing:
    """Test JSON-LD structured data parsing for StepStone."""

    @pytest.fixture
    def parser(self):
        return StepStoneParser()

    def test_parses_json_ld_job_posting(self, parser):
        """Should extract data from JSON-LD JobPosting schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Senior Python Developer",
                "description": "Wir suchen einen erfahrenen Python-Entwickler...",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "TechCorp GmbH"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "postalCode": "10115",
                        "addressLocality": "Berlin",
                        "addressRegion": "Berlin"
                    }
                },
                "datePosted": "2026-01-10",
                "validThrough": "2026-02-10",
                "employmentType": "FULL_TIME"
            }
            </script>
        </head>
        <body><h1>Senior Python Developer</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["source"] == "stepstone"
        assert result["title"] == "Senior Python Developer"
        assert result["company"] == "TechCorp GmbH"
        assert "Berlin" in result["location"]
        assert result["posted_date"] == "2026-01-10"
        assert result["application_deadline"] == "2026-02-10"
        assert result["employment_type"] == "FULL_TIME"

    def test_parses_json_ld_array_format(self, parser):
        """Should handle JSON-LD in array format."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            [
                {"@type": "BreadcrumbList"},
                {
                    "@type": "JobPosting",
                    "title": "Data Engineer",
                    "hiringOrganization": {"name": "DataCo"}
                }
            ]
            </script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["title"] == "Data Engineer"
        assert result["company"] == "DataCo"

    def test_handles_multiple_locations(self, parser):
        """Should handle multiple job locations."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Remote Developer",
                "jobLocation": [
                    {"@type": "Place", "address": {"addressLocality": "Berlin"}},
                    {"@type": "Place", "address": {"addressLocality": "München"}}
                ]
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert "Berlin" in result["location"]
        assert "München" in result["location"]

    def test_parses_salary_range(self, parser):
        """Should extract salary information."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Developer",
                "baseSalary": {
                    "@type": "MonetaryAmount",
                    "currency": "EUR",
                    "value": {
                        "@type": "QuantitativeValue",
                        "minValue": 50000,
                        "maxValue": 70000
                    }
                }
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["salary"] == "50000-70000 EUR"


class TestStepStoneHTMLFallback:
    """Test HTML fallback parsing when JSON-LD is not available."""

    @pytest.fixture
    def parser(self):
        return StepStoneParser()

    def test_extracts_title_from_h1(self, parser):
        """Should extract job title from H1 when no JSON-LD."""
        html = """
        <html>
        <body>
            <h1>Frontend Developer (m/w/d)</h1>
            <article>Job description here...</article>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["title"] == "Frontend Developer (m/w/d)"

    def test_extracts_company_from_data_attribute(self, parser):
        """Should extract company from StepStone data attributes."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <span data-at="header-company-name">Innovative Tech AG</span>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["company"] == "Innovative Tech AG"

    def test_extracts_contact_email(self, parser):
        """Should extract contact email from page content."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Bei Fragen wenden Sie sich an: bewerbung@techfirma.de</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["contact_email"] == "bewerbung@techfirma.de"

    def test_filters_noreply_emails(self, parser):
        """Should filter out noreply/newsletter emails."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>noreply@stepstone.de</p>
            <p>newsletter@stepstone.de</p>
            <p>hr@realcompany.de</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["contact_email"] == "hr@realcompany.de"

    def test_extracts_requirements_section(self, parser):
        """Should extract requirements from labeled section."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div>
                <h2>Anforderungen</h2>
                <ul>
                    <li>Python Kenntnisse</li>
                    <li>3+ Jahre Erfahrung</li>
                </ul>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://stepstone.de/stellenangebote--test")

        assert result["requirements"] is not None
        assert "Python" in result["requirements"]


class TestWebScraperIntegration:
    """Test WebScraper integration with StepStone parser."""

    def test_detect_stepstone_job_board(self):
        """Should detect StepStone as job board."""
        scraper = WebScraper()
        url = "https://www.stepstone.de/stellenangebote--Developer-Berlin--12345.html"

        assert scraper.detect_job_board(url) == "stepstone"

    def test_detect_unknown_job_board(self):
        """Should return None for unknown job boards."""
        scraper = WebScraper()
        url = "https://www.random-company.de/jobs/developer"

        assert scraper.detect_job_board(url) is None
