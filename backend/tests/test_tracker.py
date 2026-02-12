"""Tests for the BewerbungsTracker service (services/tracker.py)."""

import json
import os
import tempfile

from services.tracker import BewerbungsTracker


class TestBewerbungsTracker:
    """Tests for the BewerbungsTracker JSON-based tracker."""

    def _create_tracker(self, tmp_dir):
        """Create a tracker with a temporary JSON file."""
        json_path = os.path.join(tmp_dir, "bewerbungen.json")
        return BewerbungsTracker(json_path), json_path

    def test_creates_empty_json_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, json_path = self._create_tracker(tmp_dir)
            assert os.path.exists(json_path)
            with open(json_path) as f:
                data = json.load(f)
            assert data == []

    def test_loads_existing_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = os.path.join(tmp_dir, "bewerbungen.json")
            with open(json_path, "w") as f:
                json.dump([{"firma": "Test", "status": "erstellt"}], f)

            tracker = BewerbungsTracker(json_path)
            assert len(tracker.bewerbungen) == 1
            assert tracker.bewerbungen[0]["firma"] == "Test"

    def test_log_bewerbung(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, json_path = self._create_tracker(tmp_dir)
            tracker.log_bewerbung(
                firma="Test GmbH",
                position="Developer",
                ansprechpartner="Herr Mueller",
                email="hr@test.de",
                quelle="Indeed",
                status="erstellt",
                pdf_pfad="/tmp/test.pdf",
                notizen="Gute Firma",
                betreff="Bewerbung",
                email_text="Sehr geehrte...",
            )

            assert len(tracker.bewerbungen) == 1
            bew = tracker.bewerbungen[0]
            assert bew["firma"] == "Test GmbH"
            assert bew["position"] == "Developer"
            assert bew["ansprechpartner"] == "Herr Mueller"
            assert bew["email"] == "hr@test.de"
            assert bew["quelle"] == "Indeed"
            assert bew["status"] == "erstellt"

            # Verify persistence
            with open(json_path) as f:
                persisted = json.load(f)
            assert len(persisted) == 1

    def test_log_bewerbung_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, _ = self._create_tracker(tmp_dir)
            tracker.log_bewerbung(
                firma="Test",
                position="Dev",
                ansprechpartner="Frau Schmidt",
            )

            bew = tracker.bewerbungen[0]
            assert bew["email"] == ""
            assert bew["quelle"] == ""
            assert bew["pdf_pfad"] == ""
            assert bew["notizen"] == ""
            assert bew["betreff"] == ""
            assert bew["email_text"] == ""
            assert bew["links"] == {}

    def test_update_status(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, _ = self._create_tracker(tmp_dir)
            tracker.log_bewerbung(
                firma="Test GmbH",
                position="Dev",
                ansprechpartner="Test",
            )
            datum = tracker.bewerbungen[0]["datum"]

            tracker.update_status("Test GmbH", datum[:10], "versendet")
            assert tracker.bewerbungen[0]["status"] == "versendet"

    def test_get_statistik(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, _ = self._create_tracker(tmp_dir)
            tracker.log_bewerbung(firma="A", position="Dev", ansprechpartner="X", status="erstellt")
            tracker.log_bewerbung(firma="B", position="Dev", ansprechpartner="Y", status="versendet")
            tracker.log_bewerbung(firma="C", position="Dev", ansprechpartner="Z", status="erstellt")

            stats = tracker.get_statistik()
            assert stats["gesamt"] == 3
            assert stats["erstellt"] == 2
            assert stats["versendet"] == 1

    def test_get_latest_bewerbung(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, _ = self._create_tracker(tmp_dir)
            assert tracker.get_latest_bewerbung() is None

            tracker.log_bewerbung(firma="First", position="Dev", ansprechpartner="X")
            tracker.log_bewerbung(firma="Second", position="Dev", ansprechpartner="Y")

            latest = tracker.get_latest_bewerbung()
            assert latest["firma"] == "Second"

    def test_list_bewerbungen(self):
        """list_bewerbungen should not raise errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tracker, _ = self._create_tracker(tmp_dir)
            # Empty list
            tracker.list_bewerbungen()

            # With data
            tracker.log_bewerbung(firma="Test", position="Dev", ansprechpartner="X")
            tracker.list_bewerbungen(limit=5)

    def test_csv_migration(self):
        """Test migration from CSV to JSON format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, "bewerbungen.csv")
            json_path = os.path.join(tmp_dir, "bewerbungen.json")

            # Create a CSV file
            with open(csv_path, "w") as f:
                f.write("datum,firma,position,ansprechpartner,status\n")
                f.write("2024-01-01,Test GmbH,Dev,Herr Test,erstellt\n")

            tracker = BewerbungsTracker(json_path)
            assert len(tracker.bewerbungen) == 1
            assert tracker.bewerbungen[0]["firma"] == "Test GmbH"
            assert os.path.exists(json_path)
            assert not os.path.exists(csv_path)  # CSV should be removed
