"""
Tests for GenericJobParser fallback scraper.

The GenericJobParser is used for job postings from unknown sources
(company career pages, Lever, Greenhouse, etc.) when no specific
parser matches.
"""

import pytest
from bs4 import BeautifulSoup

from services.web_scraper import GenericJobParser, WebScraper


class TestGenericJobParserJSONLD:
    """Test JSON-LD Schema.org extraction."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_parses_json_ld_job_posting(self, parser):
        """Should extract data from JSON-LD JobPosting schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Fullstack Engineer",
                "description": "We are looking for a talented engineer...",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Acme Corp"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Hamburg",
                        "addressCountry": "Germany"
                    }
                },
                "datePosted": "2026-01-15",
                "employmentType": "FULL_TIME"
            }
            </script>
        </head>
        <body><h1>Fullstack Engineer</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/jobs/123")

        assert result["source"] == "generic"
        assert result["title"] == "Fullstack Engineer"
        assert result["company"] == "Acme Corp"
        assert "Hamburg" in result["location"]
        assert result["posted_date"] == "2026-01-15"
        assert result["employment_type"] == "FULL_TIME"

    def test_parses_json_ld_in_graph_format(self, parser):
        """Should handle JSON-LD @graph array format."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@graph": [
                    {"@type": "WebSite", "name": "Company Site"},
                    {
                        "@type": "JobPosting",
                        "title": "Backend Developer",
                        "hiringOrganization": {"name": "Graph Corp"}
                    }
                ]
            }
            </script>
        </head>
        <body><h1>Backend Developer</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/jobs/456")

        assert result["title"] == "Backend Developer"
        assert result["company"] == "Graph Corp"

    def test_parses_salary_range(self, parser):
        """Should extract salary range from JSON-LD."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Engineer",
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
        result = parser.parse(soup, "https://example.com/jobs/789")

        assert result["salary"] == "50000-70000 EUR"


class TestGenericJobParserOpenGraph:
    """Test OpenGraph meta tag extraction."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_extracts_opengraph_tags(self, parser):
        """Should extract data from og: meta tags."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Product Manager - Berlin">
            <meta property="og:description" content="Join our team as a Product Manager...">
            <meta property="og:site_name" content="StartupXYZ">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://startupxyz.com/careers/pm")

        assert result["title"] == "Product Manager - Berlin"
        assert "Join our team" in result["description"]
        assert result["company"] == "StartupXYZ"


class TestGenericJobParserMetaTags:
    """Test standard meta tag extraction."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_extracts_meta_tags(self, parser):
        """Should extract data from standard meta tags."""
        html = """
        <html>
        <head>
            <meta name="title" content="Software Architect">
            <meta name="description" content="Looking for a senior architect...">
            <meta name="author" content="Enterprise Solutions GmbH">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://enterprise.com/jobs/architect")

        assert result["title"] == "Software Architect"
        assert "senior architect" in result["description"]
        assert result["company"] == "Enterprise Solutions GmbH"


class TestGenericJobParserTitleTag:
    """Test title tag parsing."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_parses_title_with_dash_separator(self, parser):
        """Should parse 'Job Title - Company' format."""
        html = """
        <html>
        <head><title>Frontend Developer - Tech Startup GmbH</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://techstartup.com/jobs/fe")

        assert result["title"] == "Frontend Developer"
        assert result["company"] == "Tech Startup GmbH"

    def test_parses_title_with_pipe_separator(self, parser):
        """Should parse 'Job Title | Company' format."""
        html = """
        <html>
        <head><title>Data Scientist | Analytics Inc</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://analytics.com/jobs/ds")

        assert result["title"] == "Data Scientist"
        assert result["company"] == "Analytics Inc"

    def test_parses_title_with_at_pattern(self, parser):
        """Should parse 'Job Title at Company' format."""
        html = """
        <html>
        <head><title>DevOps Engineer at Cloud Systems</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://cloudsystems.com/jobs/devops")

        assert result["title"] == "DevOps Engineer"
        assert result["company"] == "Cloud Systems"

    def test_parses_title_with_bei_pattern_german(self, parser):
        """Should parse 'Job Title bei Company' German format."""
        html = """
        <html>
        <head><title>Entwickler bei Deutsche Firma GmbH</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://deutschefirma.de/jobs/dev")

        assert result["title"] == "Entwickler"
        assert result["company"] == "Deutsche Firma GmbH"


class TestGenericJobParserHTMLPatterns:
    """Test common HTML pattern extraction."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_extracts_from_data_testid(self, parser):
        """Should extract from data-testid attributes."""
        html = """
        <html>
        <body>
            <h1 data-testid="job-title">QA Engineer</h1>
            <span data-testid="company-name">Quality First Ltd</span>
            <div data-testid="job-location">Munich, Germany</div>
            <div data-testid="job-description">Testing responsibilities...</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://qualityfirst.com/jobs/qa")

        assert result["title"] == "QA Engineer"
        assert result["company"] == "Quality First Ltd"
        assert result["location"] == "Munich, Germany"
        assert "Testing responsibilities" in result["description"]

    def test_extracts_from_class_patterns(self, parser):
        """Should extract from common CSS class patterns."""
        html = """
        <html>
        <body>
            <h1 class="job-title">Mobile Developer</h1>
            <div class="company-name">App Makers AG</div>
            <span class="job-location">Stuttgart</span>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://appmakers.de/careers/mobile")

        assert result["title"] == "Mobile Developer"
        assert result["company"] == "App Makers AG"
        assert result["location"] == "Stuttgart"

    def test_extracts_employment_type_from_badges(self, parser):
        """Should extract employment type from badge/tag elements."""
        html = """
        <html>
        <body>
            <span class="badge">Full-time</span>
            <span class="tag">Remote</span>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/jobs/1")

        assert result["employment_type"] in ["Full-time", "Remote"]

    def test_extracts_email_from_page(self, parser):
        """Should extract contact email from page text."""
        html = """
        <html>
        <body>
            <p>Contact us at: jobs@company.com</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://company.com/careers")

        assert result["contact_email"] == "jobs@company.com"

    def test_filters_noreply_emails(self, parser):
        """Should filter out noreply emails."""
        html = """
        <html>
        <body>
            <p>System: noreply@company.com</p>
            <p>Contact: recruiting@company.com</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://company.com/careers")

        assert result["contact_email"] == "recruiting@company.com"


class TestGenericJobParserHeuristics:
    """Test heuristic fallback extraction."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_uses_h1_as_title_fallback(self, parser):
        """Should use first h1 as job title when other methods fail."""
        html = """
        <html>
        <body>
            <h1>Senior UX Designer</h1>
            <p>Some content here...</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://unknown.com/job")

        assert result["title"] == "Senior UX Designer"

    def test_extracts_company_from_domain(self, parser):
        """Should extract company name from domain when no other source."""
        html = """
        <html>
        <body>
            <h1>Job Opening</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://zeit-verlagsgruppe.de/careers/job")

        assert result["company"] == "Zeit Verlagsgruppe"

    def test_skips_job_board_domains_for_company(self, parser):
        """Should not use job board domains as company name."""
        html = """
        <html>
        <body>
            <h1>Job Opening</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://lever.co/some-company/job")

        # Should not set company to "Lever"
        assert result["company"] != "Lever"

    def test_extracts_salary_pattern_german(self, parser):
        """Should extract German salary patterns from text."""
        html = """
        <html>
        <body>
            <p>Gehalt: 50.000 - 70.000 €</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/job")

        assert "50.000" in result["salary"]
        assert "70.000" in result["salary"]


class TestGenericJobParserPartialData:
    """Test that parser returns partial data rather than all-or-nothing."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_returns_partial_data(self, parser):
        """Should return whatever data can be extracted."""
        html = """
        <html>
        <head><title>Software Engineer - SomeCompany</title></head>
        <body>
            <p>No structured data here, just plain text content.</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://somecompany.com/jobs/se")

        # Should have title and company from title tag
        assert result["title"] == "Software Engineer"
        assert result["company"] == "SomeCompany"
        # Other fields may be None, but that's OK
        assert result["source"] == "generic"


class TestGenericJobParserCleanText:
    """Test text cleaning functionality."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_cleans_whitespace(self, parser):
        """Should normalize excessive whitespace."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="  Job   Title   With   Spaces  ">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/job")

        assert result["title"] == "Job Title With Spaces"

    def test_removes_zero_width_chars(self, parser):
        """Should remove zero-width characters."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Job\u200bTitle\u200cWith\u200dZeroWidth">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/job")

        assert "\u200b" not in result["title"]
        assert "\u200c" not in result["title"]
        assert "\u200d" not in result["title"]


class TestGenericJobParserDateParsing:
    """Test date parsing functionality."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_parses_iso_date(self, parser):
        """Should parse ISO format dates."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Test",
                "datePosted": "2026-01-15T10:00:00Z"
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://example.com/job")

        assert result["posted_date"] == "2026-01-15"


class TestWebScraperGenericFallback:
    """Test that WebScraper uses GenericJobParser as fallback."""

    def test_detect_job_board_returns_none_for_unknown(self):
        """detect_job_board should return None for unknown sites."""
        scraper = WebScraper()

        unknown_urls = [
            "https://zeit-verlagsgruppe.de/jobs/engineer",
            "https://jobs.lever.co/company/12345",
            "https://boards.greenhouse.io/company/jobs/123",
            "https://careers.company.com/job/456",
        ]

        for url in unknown_urls:
            result = scraper.detect_job_board(url)
            assert result is None, f"Should return None for: {url}"


class TestGenericJobParserLeverStyle:
    """Test parsing Lever-style job pages."""

    @pytest.fixture
    def parser(self):
        return GenericJobParser()

    def test_parses_lever_style_page(self, parser):
        """Should extract data from Lever-style job pages."""
        html = """
        <html>
        <head>
            <title>Research Engineer - ResearchGate</title>
            <meta property="og:title" content="Research Engineer">
            <meta property="og:site_name" content="ResearchGate">
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Research Engineer",
                "hiringOrganization": {"name": "ResearchGate"},
                "jobLocation": {
                    "address": {
                        "addressLocality": "Berlin"
                    }
                }
            }
            </script>
        </head>
        <body>
            <div class="posting-headline">
                <h2>Research Engineer</h2>
            </div>
            <div class="location">Berlin, Germany</div>
            <div class="posting-description">
                <p>We're looking for a Research Engineer to join our team...</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://jobs.lever.co/researchgate/12345")

        assert result["title"] == "Research Engineer"
        assert result["company"] == "ResearchGate"
        assert "Berlin" in result["location"]
