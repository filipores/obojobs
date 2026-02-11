"""Tests for the Bundesagentur API client."""

import pytest
from unittest.mock import patch, MagicMock

from services.bundesagentur_client import BundesagenturClient, BundesagenturJob


class TestBundesagenturJob:
    """Tests for the BundesagenturJob dataclass."""

    def test_to_job_data(self):
        job = BundesagenturJob(
            refnr="10000-1234567890-S",
            titel="Software Entwickler (m/w/d)",
            beruf="Software Developer",
            arbeitgeber="Test GmbH",
            arbeitsort="Berlin",
            beschreibung="Eine tolle Stelle",
        )
        data = job.to_job_data()

        assert data["title"] == "Software Entwickler (m/w/d)"
        assert data["company"] == "Test GmbH"
        assert data["location"] == "Berlin"
        assert data["source"] == "arbeitsagentur"
        assert data["description"] == "Eine tolle Stelle"
        assert "arbeitsagentur.de" in data["url"]

    def test_to_job_data_generates_url(self):
        job = BundesagenturJob(refnr="10000-123", titel="Test")
        data = job.to_job_data()
        assert data["url"] == "https://www.arbeitsagentur.de/jobsuche/suche?id=10000-123"


class TestBundesagenturClient:
    """Tests for the BundesagenturClient."""

    def setup_method(self):
        self.client = BundesagenturClient()

    @patch("services.bundesagentur_client.requests.Session.get")
    def test_search_jobs_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "maxErgebnisse": 42,
            "stellenangebote": [
                {
                    "refnr": "10000-1234567890-S",
                    "titel": "Python Developer",
                    "beruf": "Softwareentwickler",
                    "arbeitgeber": "Tech GmbH",
                    "arbeitsort": {"ort": "Berlin", "region": "Berlin"},
                    "aktuelleVeroeffentlichungsdatum": "2024-01-15",
                    "arbeitszeit": "vz",
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        jobs, total = self.client.search_jobs("Python", location="Berlin")

        assert total == 42
        assert len(jobs) == 1
        assert jobs[0].titel == "Python Developer"
        assert jobs[0].arbeitgeber == "Tech GmbH"
        assert jobs[0].arbeitsort == "Berlin, Berlin"

    @patch("services.bundesagentur_client.requests.Session.get")
    def test_search_jobs_empty_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"maxErgebnisse": 0, "stellenangebote": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        jobs, total = self.client.search_jobs("Nonexistent")

        assert total == 0
        assert len(jobs) == 0

    @patch("services.bundesagentur_client.requests.Session.get")
    def test_search_jobs_api_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("Connection error")

        jobs, total = self.client.search_jobs("Python")

        assert total == 0
        assert len(jobs) == 0

    @patch("services.bundesagentur_client.requests.Session.get")
    def test_get_job_details_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "refnr": "10000-123",
            "titel": "Python Developer",
            "arbeitgeber": "Tech GmbH",
            "arbeitsort": {"ort": "Berlin"},
            "stellenbeschreibung": "Full job description here",
            "arbeitgeberdarstellung": "Company description",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        job = self.client.get_job_details("10000-123")

        assert job is not None
        assert job.titel == "Python Developer"
        assert "Full job description here" in job.beschreibung
        assert "Company description" in job.beschreibung

    @patch("services.bundesagentur_client.requests.Session.get")
    def test_get_job_details_not_found(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("404")

        job = self.client.get_job_details("nonexistent")

        assert job is None

    def test_parse_arbeitsort_full(self):
        result = self.client._parse_arbeitsort({"ort": "Berlin", "region": "Berlin"})
        assert result == "Berlin, Berlin"

    def test_parse_arbeitsort_empty(self):
        result = self.client._parse_arbeitsort({})
        assert result == ""

    def test_parse_arbeitsort_none(self):
        result = self.client._parse_arbeitsort(None)
        assert result == ""
