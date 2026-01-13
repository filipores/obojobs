"""
Tests for Indeed.de job board scraper.
"""

import pytest
from bs4 import BeautifulSoup

from services.web_scraper import IndeedParser, WebScraper


class TestIndeedURLMatching:
    """Test URL pattern matching for Indeed."""

    def test_matches_indeed_viewjob_url(self):
        """Should match valid Indeed viewjob URLs."""
        valid_urls = [
            "https://de.indeed.com/viewjob?jk=abc123",
            "https://www.de.indeed.com/viewjob?jk=xyz789&from=search",
            "https://indeed.com/viewjob?jk=test123",
            "https://de.indeed.com/job/python-developer-abc123",
            "https://indeed.de/viewjob?jk=test456",
        ]
        for url in valid_urls:
            assert IndeedParser.matches_url(url) is True, f"Should match: {url}"

    def test_matches_indeed_jobs_url(self):
        """Should match Indeed jobs URLs with jk parameter."""
        valid_urls = [
            "https://de.indeed.com/jobs?jk=abc123&q=developer",
            "https://indeed.com/jobs?jk=test",
        ]
        for url in valid_urls:
            assert IndeedParser.matches_url(url) is True, f"Should match: {url}"

    def test_does_not_match_indeed_search_pages(self):
        """Should not match Indeed search/listing pages without job key."""
        invalid_urls = [
            "https://de.indeed.com/",
            "https://de.indeed.com/jobs?q=developer&l=berlin",
            "https://de.indeed.com/companies",
            "https://de.indeed.com/career-advice",
        ]
        for url in invalid_urls:
            assert IndeedParser.matches_url(url) is False, f"Should not match: {url}"

    def test_does_not_match_other_domains(self):
        """Should not match other job boards."""
        other_domains = [
            "https://www.stepstone.de/stellenangebote--Developer--12345.html",
            "https://www.xing.com/jobs/12345",
            "https://www.linkedin.com/jobs/view/12345",
        ]
        for url in other_domains:
            assert IndeedParser.matches_url(url) is False, f"Should not match: {url}"


class TestIndeedJSONLDParsing:
    """Test JSON-LD structured data parsing for Indeed."""

    @pytest.fixture
    def parser(self):
        return IndeedParser()

    def test_parses_json_ld_job_posting(self, parser):
        """Should extract data from JSON-LD JobPosting schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Python Backend Developer",
                "description": "Wir suchen einen erfahrenen Backend-Entwickler...",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Tech Startup GmbH"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Berlin",
                        "addressRegion": "Berlin"
                    }
                },
                "datePosted": "2026-01-10",
                "employmentType": "FULL_TIME",
                "baseSalary": {
                    "@type": "MonetaryAmount",
                    "currency": "EUR",
                    "value": {
                        "minValue": 55000,
                        "maxValue": 75000
                    }
                }
            }
            </script>
        </head>
        <body><h1>Python Backend Developer</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["source"] == "indeed"
        assert result["title"] == "Python Backend Developer"
        assert result["company"] == "Tech Startup GmbH"
        assert "Berlin" in result["location"]
        assert result["posted_date"] == "2026-01-10"
        assert result["employment_type"] == "FULL_TIME"
        assert result["salary"] == "55000-75000 EUR"


class TestIndeedHTMLParsing:
    """Test HTML parsing for Indeed-specific elements."""

    @pytest.fixture
    def parser(self):
        return IndeedParser()

    def test_extracts_title_from_data_testid(self, parser):
        """Should extract job title from data-testid attribute."""
        html = """
        <html>
        <body>
            <h1 data-testid="jobsearch-JobInfoHeader-title">
                Senior Frontend Developer (m/w/d)
            </h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["title"] == "Senior Frontend Developer (m/w/d)"

    def test_extracts_title_from_h1_fallback(self, parser):
        """Should extract job title from H1 when no data-testid."""
        html = """
        <html>
        <body>
            <h1>DevOps Engineer</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["title"] == "DevOps Engineer"

    def test_extracts_company_from_data_testid(self, parser):
        """Should extract company name from data-testid."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div data-testid="inlineHeader-companyName">
                <a href="/company">Innovation Labs AG</a>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["company"] == "Innovation Labs AG"

    def test_extracts_location(self, parser):
        """Should extract location from Indeed elements."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div data-testid="inlineHeader-companyLocation">München, Bayern</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["location"] == "München, Bayern"

    def test_extracts_salary_from_attribute(self, parser):
        """Should extract salary from Indeed salary element."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div data-testid="attribute_snippet_testid">50.000 € – 70.000 € pro Jahr</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["salary"] == "50.000 € – 70.000 € pro Jahr"

    def test_extracts_job_type_vollzeit(self, parser):
        """Should extract Vollzeit job type."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div data-testid="jobsearch-JobMetadataFooter">
                Vollzeit, Festanstellung
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert "Vollzeit" in result["employment_type"]
        assert "Festanstellung" in result["employment_type"]

    def test_extracts_job_type_teilzeit(self, parser):
        """Should extract Teilzeit job type."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div data-testid="jobsearch-JobMetadataFooter">
                Teilzeit
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["employment_type"] == "Teilzeit"

    def test_extracts_description(self, parser):
        """Should extract job description."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div id="jobDescriptionText">
                <p>Wir suchen einen motivierten Entwickler.</p>
                <ul>
                    <li>Python Kenntnisse</li>
                    <li>3+ Jahre Erfahrung</li>
                </ul>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert "motivierten Entwickler" in result["description"]
        assert "Python Kenntnisse" in result["description"]

    def test_extracts_contact_email(self, parser):
        """Should extract contact email from page content."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div id="jobDescriptionText">
                <p>Bitte senden Sie Ihre Bewerbung an: jobs@firma.de</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["contact_email"] == "jobs@firma.de"

    def test_filters_indeed_system_emails(self, parser):
        """Should filter out Indeed system emails."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>support@indeed.com</p>
            <p>noreply@indeed.de</p>
            <p>hr@realcompany.de</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://de.indeed.com/viewjob?jk=test")

        assert result["contact_email"] == "hr@realcompany.de"


class TestIndeedAntiBot:
    """Test anti-bot measures for Indeed scraper."""

    def test_indeed_parser_has_headers(self):
        """Indeed parser should have anti-bot headers defined."""
        assert hasattr(IndeedParser, "HEADERS")
        assert "User-Agent" in IndeedParser.HEADERS
        assert "Accept-Language" in IndeedParser.HEADERS
        assert "Sec-Fetch-Dest" in IndeedParser.HEADERS

    def test_headers_look_like_browser(self):
        """Headers should resemble a real browser."""
        headers = IndeedParser.HEADERS
        assert "Mozilla" in headers["User-Agent"]
        assert "Chrome" in headers["User-Agent"]
        assert "de-DE" in headers["Accept-Language"]


class TestWebScraperIndeedIntegration:
    """Test WebScraper integration with Indeed parser."""

    def test_detect_indeed_job_board(self):
        """Should detect Indeed as job board."""
        scraper = WebScraper()
        urls = [
            "https://de.indeed.com/viewjob?jk=abc123",
            "https://indeed.com/viewjob?jk=test",
            "https://indeed.de/viewjob?jk=xyz",
        ]
        for url in urls:
            assert scraper.detect_job_board(url) == "indeed", f"Should detect Indeed: {url}"

    def test_detect_unknown_for_indeed_search(self):
        """Should return None for Indeed search pages (not job postings)."""
        scraper = WebScraper()
        url = "https://de.indeed.com/jobs?q=developer&l=berlin"
        assert scraper.detect_job_board(url) is None
