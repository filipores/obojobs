"""
Tests for XING Jobs scraper.
"""

import pytest
from bs4 import BeautifulSoup

from services.web_scraper import WebScraper, XingParser


class TestXingURLMatching:
    """Test URL pattern matching for XING Jobs."""

    def test_matches_xing_jobs_url(self):
        """Should match valid XING jobs URLs."""
        valid_urls = [
            "https://www.xing.com/jobs/berlin-python-developer-12345678",
            "https://xing.com/jobs/muenchen-senior-backend-engineer-87654321",
            "https://www.xing.com/jobs/hamburg-devops-engineer-11111111",
            "https://xing.com/jobs/frankfurt-software-architect-22222222",
        ]
        for url in valid_urls:
            assert XingParser.matches_url(url) is True, f"Should match: {url}"

    def test_does_not_match_xing_non_job_pages(self):
        """Should not match XING pages that are not job postings."""
        invalid_urls = [
            "https://www.xing.com/",
            "https://www.xing.com/profile/Max_Mustermann",
            "https://www.xing.com/companies/testfirma",
            "https://www.xing.com/communities/",
            "https://www.xing.com/news",
        ]
        for url in invalid_urls:
            assert XingParser.matches_url(url) is False, f"Should not match: {url}"

    def test_does_not_match_other_domains(self):
        """Should not match other job boards."""
        other_domains = [
            "https://www.stepstone.de/stellenangebote--Developer--12345.html",
            "https://de.indeed.com/viewjob?jk=abc123",
            "https://www.linkedin.com/jobs/view/12345",
        ]
        for url in other_domains:
            assert XingParser.matches_url(url) is False, f"Should not match: {url}"


class TestXingJSONLDParsing:
    """Test JSON-LD structured data parsing for XING."""

    @pytest.fixture
    def parser(self):
        return XingParser()

    def test_parses_json_ld_job_posting(self, parser):
        """Should extract data from JSON-LD JobPosting schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Senior Python Developer (m/w/d)",
                "description": "Wir suchen einen erfahrenen Python-Entwickler...",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Digital Solutions GmbH",
                    "url": "https://www.xing.com/companies/digitalsolutions"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Berlin",
                        "postalCode": "10115"
                    }
                },
                "datePosted": "2026-01-12",
                "validThrough": "2026-02-12",
                "employmentType": "FULL_TIME"
            }
            </script>
        </head>
        <body><h1>Senior Python Developer (m/w/d)</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/berlin-python-12345")

        assert result["source"] == "xing"
        assert result["title"] == "Senior Python Developer (m/w/d)"
        assert result["company"] == "Digital Solutions GmbH"
        assert "Berlin" in result["location"]
        assert "10115" in result["location"]
        assert result["posted_date"] == "2026-01-12"
        assert result["application_deadline"] == "2026-02-12"
        assert result["employment_type"] == "FULL_TIME"
        assert result["company_profile_url"] == "https://www.xing.com/companies/digitalsolutions"

    def test_parses_json_ld_with_salary(self, parser):
        """Should extract salary from JSON-LD."""
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
                        "minValue": 60000,
                        "maxValue": 80000
                    }
                }
            }
            </script>
        </head>
        <body><h1>Developer</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["salary"] == "60000-80000 EUR"


class TestXingHTMLParsing:
    """Test HTML parsing for XING-specific elements."""

    @pytest.fixture
    def parser(self):
        return XingParser()

    def test_extracts_title_from_h1(self, parser):
        """Should extract job title from H1 element."""
        html = """
        <html>
        <body>
            <h1 class="job-title">Frontend Engineer (m/w/d)</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["title"] == "Frontend Engineer (m/w/d)"

    def test_extracts_company_from_company_link(self, parser):
        """Should extract company name from company profile link."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <a href="/companies/techfirma">TechFirma GmbH</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["company"] == "TechFirma GmbH"
        assert "xing.com/companies/techfirma" in result["company_profile_url"]

    def test_extracts_location_from_class(self, parser):
        """Should extract location from location class."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="location">München, Bayern</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["location"] == "München, Bayern"

    def test_extracts_contact_person_from_profile_link(self, parser):
        """Should extract contact person from XING profile link."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="recruiter">
                <a href="/profile/Anna_Mueller123">Anna Müller</a>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["contact_person"] == "Anna Müller"

    def test_extracts_description(self, parser):
        """Should extract job description."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="job-description">
                <p>Wir sind ein innovatives Unternehmen.</p>
                <ul>
                    <li>Spannende Projekte</li>
                    <li>Flexible Arbeitszeiten</li>
                </ul>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert "innovatives Unternehmen" in result["description"]
        assert "Spannende Projekte" in result["description"]

    def test_extracts_employment_type(self, parser):
        """Should extract employment type from meta elements."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <span class="job-type">Vollzeit, Festanstellung</span>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert "Vollzeit" in result["employment_type"]
        assert "Festanstellung" in result["employment_type"]

    def test_extracts_contact_email(self, parser):
        """Should extract contact email from page content."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="job-description">
                <p>Bewerbungen bitte an: karriere@firma.de</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["contact_email"] == "karriere@firma.de"

    def test_filters_xing_system_emails(self, parser):
        """Should filter out XING system emails."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>support@xing.com</p>
            <p>noreply@xing.de</p>
            <p>info@xing.com</p>
            <p>hr@realcompany.de</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.xing.com/jobs/test-12345")

        assert result["contact_email"] == "hr@realcompany.de"


class TestXingHeaders:
    """Test anti-bot headers for XING scraper."""

    def test_xing_parser_has_headers(self):
        """XING parser should have headers defined."""
        assert hasattr(XingParser, "HEADERS")
        assert "User-Agent" in XingParser.HEADERS
        assert "Accept-Language" in XingParser.HEADERS

    def test_headers_look_like_browser(self):
        """Headers should resemble a real browser."""
        headers = XingParser.HEADERS
        assert "Mozilla" in headers["User-Agent"]
        assert "Chrome" in headers["User-Agent"]
        assert "de-DE" in headers["Accept-Language"]


class TestWebScraperXingIntegration:
    """Test WebScraper integration with XING parser."""

    def test_detect_xing_job_board(self):
        """Should detect XING as job board."""
        scraper = WebScraper()
        urls = [
            "https://www.xing.com/jobs/berlin-developer-12345",
            "https://xing.com/jobs/muenchen-engineer-67890",
        ]
        for url in urls:
            assert scraper.detect_job_board(url) == "xing", f"Should detect XING: {url}"

    def test_detect_unknown_for_xing_profile(self):
        """Should return None for XING profile pages (not job postings)."""
        scraper = WebScraper()
        url = "https://www.xing.com/profile/Max_Mustermann"
        assert scraper.detect_job_board(url) is None

    def test_detect_unknown_for_xing_company(self):
        """Should return None for XING company pages."""
        scraper = WebScraper()
        url = "https://www.xing.com/companies/testfirma"
        assert scraper.detect_job_board(url) is None
