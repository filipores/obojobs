"""
Tests for Arbeitsagentur (Bundesagentur für Arbeit) scraper.
"""

import pytest
from bs4 import BeautifulSoup

from services.web_scraper import ArbeitsagenturParser, WebScraper


class TestArbeitsagenturURLMatching:
    """Test URL pattern matching for Arbeitsagentur."""

    def test_matches_arbeitsagentur_jobsuche_urls(self):
        """Should match valid Arbeitsagentur jobsuche URLs."""
        valid_urls = [
            "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345678",
            "https://arbeitsagentur.de/jobsuche/suche?was=Python",
            "https://www.arbeitsagentur.de/jobsuche/stellenangebot/987654",
            "https://con.arbeitsagentur.de/prod/jobboerse/jobsuche/12345",
        ]
        for url in valid_urls:
            assert ArbeitsagenturParser.matches_url(url) is True, f"Should match: {url}"

    def test_matches_arbeitsagentur_jobboerse_urls(self):
        """Should match Arbeitsagentur jobboerse URLs."""
        valid_urls = [
            "https://con.arbeitsagentur.de/prod/jobboerse/jobsuche-detail/123",
            "https://jobboerse.arbeitsagentur.de/stellenangebot/456",
        ]
        for url in valid_urls:
            assert ArbeitsagenturParser.matches_url(url) is True, f"Should match: {url}"

    def test_does_not_match_arbeitsagentur_non_job_pages(self):
        """Should not match Arbeitsagentur pages that are not job postings."""
        invalid_urls = [
            "https://www.arbeitsagentur.de/",
            "https://www.arbeitsagentur.de/arbeitslos-arbeit-finden",
            "https://www.arbeitsagentur.de/kontakt",
            "https://www.arbeitsagentur.de/unternehmen",
        ]
        for url in invalid_urls:
            assert ArbeitsagenturParser.matches_url(url) is False, f"Should not match: {url}"

    def test_does_not_match_other_domains(self):
        """Should not match other job boards."""
        other_domains = [
            "https://www.stepstone.de/stellenangebote--Developer--12345.html",
            "https://de.indeed.com/viewjob?jk=abc123",
            "https://www.xing.com/jobs/berlin-developer-12345",
        ]
        for url in other_domains:
            assert ArbeitsagenturParser.matches_url(url) is False, f"Should not match: {url}"


class TestArbeitsagenturJSONLDParsing:
    """Test JSON-LD structured data parsing for Arbeitsagentur."""

    @pytest.fixture
    def parser(self):
        return ArbeitsagenturParser()

    def test_parses_json_ld_job_posting(self, parser):
        """Should extract data from JSON-LD JobPosting schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "title": "Fachinformatiker/in - Anwendungsentwicklung",
                "description": "Wir suchen einen erfahrenen Fachinformatiker...",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Muster GmbH"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Berlin",
                        "postalCode": "10115",
                        "addressRegion": "Berlin"
                    }
                },
                "datePosted": "2026-01-10",
                "validThrough": "2026-02-10",
                "employmentType": "FULL_TIME",
                "identifier": {
                    "value": "10000-1234567890-S"
                }
            }
            </script>
        </head>
        <body><h1>Fachinformatiker/in</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["source"] == "arbeitsagentur"
        assert result["title"] == "Fachinformatiker/in - Anwendungsentwicklung"
        assert result["company"] == "Muster GmbH"
        assert "Berlin" in result["location"]
        assert "10115" in result["location"]
        assert result["posted_date"] == "2026-01-10"
        assert result["application_deadline"] == "2026-02-10"
        assert result["employment_type"] == "FULL_TIME"
        assert result["reference_number"] == "10000-1234567890-S"

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
                        "minValue": 45000,
                        "maxValue": 65000
                    }
                }
            }
            </script>
        </head>
        <body><h1>Developer</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["salary"] == "45000-65000 EUR"


class TestArbeitsagenturHTMLParsing:
    """Test HTML parsing for Arbeitsagentur-specific elements."""

    @pytest.fixture
    def parser(self):
        return ArbeitsagenturParser()

    def test_extracts_title_from_h1(self, parser):
        """Should extract job title from H1 element."""
        html = """
        <html>
        <body>
            <h1>Software Entwickler (m/w/d)</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["title"] == "Software Entwickler (m/w/d)"

    def test_extracts_company_from_arbeitgeber_label(self, parser):
        """Should extract company name from Arbeitgeber label."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div>
                <dt>Arbeitgeber:</dt>
                <dd>TechFirma Berlin GmbH</dd>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["company"] == "TechFirma Berlin GmbH"

    def test_extracts_location_from_arbeitsort_label(self, parser):
        """Should extract location from Arbeitsort label."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div>
                <dt>Arbeitsort:</dt>
                <dd>10115 Berlin</dd>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["location"] == "10115 Berlin"

    def test_extracts_reference_number(self, parser):
        """Should extract Referenznummer from page."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Referenznummer: 10000-1234567890-S</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["reference_number"] == "10000-1234567890-S"

    def test_extracts_contact_person(self, parser):
        """Should extract Ansprechpartner from page."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="ansprechpartner">Frau Anna Schmidt</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["contact_person"] == "Frau Anna Schmidt"

    def test_extracts_contact_phone(self, parser):
        """Should extract phone number from page."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Telefon: +49 30 12345678</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert "+49 30 12345678" in result["contact_phone"]

    def test_extracts_description(self, parser):
        """Should extract job description."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="stellenbeschreibung">
                <p>Wir sind ein innovatives Unternehmen im Bereich IT.</p>
                <p>Ihre Aufgaben umfassen Softwareentwicklung.</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert "innovatives Unternehmen" in result["description"]

    def test_extracts_employment_type(self, parser):
        """Should extract employment type from meta elements."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <span class="arbeitszeit">Vollzeit, unbefristet</span>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert "Vollzeit" in result["employment_type"]
        assert "Unbefristet" in result["employment_type"]

    def test_extracts_contact_email(self, parser):
        """Should extract contact email from page content."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Bewerbungen an: bewerbung@firma.de</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["contact_email"] == "bewerbung@firma.de"

    def test_filters_arbeitsagentur_system_emails(self, parser):
        """Should filter out Arbeitsagentur system emails."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>info@arbeitsagentur.de</p>
            <p>noreply@test.de</p>
            <p>hr@realcompany.de</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["contact_email"] == "hr@realcompany.de"

    def test_extracts_posted_date_german_format(self, parser):
        """Should extract and convert German date format."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Online seit: 15.01.2026</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["posted_date"] == "2026-01-15"

    def test_extracts_title_from_h2_when_h1_is_generic(self, parser):
        """Should skip generic 'Detailansicht' h1 and use h2 for title."""
        html = """
        <html>
        <body>
            <h1>Detailansicht des Stellenangebots</h1>
            <h2>Python Backend Developer (m/w/d)</h2>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["title"] == "Python Backend Developer (m/w/d)"

    def test_cleans_arbeitgeber_prefix_from_company(self, parser):
        """Should strip 'Arbeitgeber:' prefix from company name."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <h3>Arbeitgeber: TechFirma Berlin GmbH</h3>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result["company"] == "TechFirma Berlin GmbH"

    def test_extracts_kooperationspartner_url_when_no_description(self, parser):
        """Should extract Kooperationspartner link as fallback when description is empty."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <a href="https://external-portal.de/job/123">Kooperationspartner</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result.get("kooperationspartner_url") == "https://external-portal.de/job/123"

    def test_no_kooperationspartner_when_description_exists(self, parser):
        """Should not set kooperationspartner_url when description is present."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <div class="stellenbeschreibung">Full job description here.</div>
            <a href="https://external-portal.de/job/123">Kooperationspartner</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = parser.parse(soup, "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345")

        assert result.get("kooperationspartner_url") is None


class TestArbeitsagenturHeaders:
    """Test anti-bot headers for Arbeitsagentur scraper."""

    def test_arbeitsagentur_parser_has_headers(self):
        """Arbeitsagentur parser should have headers defined."""
        assert hasattr(ArbeitsagenturParser, "HEADERS")
        assert "User-Agent" in ArbeitsagenturParser.HEADERS
        assert "Accept-Language" in ArbeitsagenturParser.HEADERS

    def test_headers_look_like_browser(self):
        """Headers should resemble a real browser."""
        headers = ArbeitsagenturParser.HEADERS
        assert "Mozilla" in headers["User-Agent"]
        assert "Chrome" in headers["User-Agent"]
        assert "de-DE" in headers["Accept-Language"]


class TestWebScraperArbeitsagenturIntegration:
    """Test WebScraper integration with Arbeitsagentur parser."""

    def test_detect_arbeitsagentur_job_board(self):
        """Should detect Arbeitsagentur as job board."""
        scraper = WebScraper()
        urls = [
            "https://www.arbeitsagentur.de/jobsuche/jobdetail/12345",
            "https://arbeitsagentur.de/jobsuche/suche?was=Python",
            "https://con.arbeitsagentur.de/prod/jobboerse/jobsuche/123",
        ]
        for url in urls:
            assert scraper.detect_job_board(url) == "arbeitsagentur", f"Should detect Arbeitsagentur: {url}"

    def test_detect_unknown_for_arbeitsagentur_homepage(self):
        """Should return None for Arbeitsagentur homepage (not job posting)."""
        scraper = WebScraper()
        url = "https://www.arbeitsagentur.de/"
        assert scraper.detect_job_board(url) is None

    def test_detect_unknown_for_arbeitsagentur_service_pages(self):
        """Should return None for Arbeitsagentur service pages."""
        scraper = WebScraper()
        url = "https://www.arbeitsagentur.de/arbeitslos-arbeit-finden"
        assert scraper.detect_job_board(url) is None


class TestArbeitsagenturURLNormalization:
    """Test URL normalization from suche?id= to jobdetail/ format."""

    def test_normalizes_suche_id_to_jobdetail(self):
        """Should convert suche?id= URL to jobdetail/ URL."""
        url = "https://www.arbeitsagentur.de/jobsuche/suche?id=10000-1234567890-S"
        result = WebScraper._normalize_arbeitsagentur_url(url)
        assert result == "https://www.arbeitsagentur.de/jobsuche/jobdetail/10000-1234567890-S"

    def test_normalizes_suche_with_extra_params(self):
        """Should extract refnr even with extra query params."""
        url = "https://www.arbeitsagentur.de/jobsuche/suche?id=10000-123&was=Python"
        result = WebScraper._normalize_arbeitsagentur_url(url)
        assert result == "https://www.arbeitsagentur.de/jobsuche/jobdetail/10000-123"

    def test_leaves_jobdetail_url_unchanged(self):
        """Should not modify already-correct jobdetail URLs."""
        url = "https://www.arbeitsagentur.de/jobsuche/jobdetail/10000-123"
        result = WebScraper._normalize_arbeitsagentur_url(url)
        assert result == url

    def test_leaves_non_arbeitsagentur_url_unchanged(self):
        """Should not modify URLs from other domains."""
        url = "https://www.stepstone.de/stellenangebote--Developer--12345.html"
        result = WebScraper._normalize_arbeitsagentur_url(url)
        assert result == url
