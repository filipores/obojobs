"""
Tests for statistics endpoints.
"""

from datetime import datetime, timedelta

from models import Application, db


class TestGetStats:
    """Tests for GET /api/stats"""

    def test_get_stats_requires_authentication(self, client):
        """Test that /api/stats requires JWT token."""
        response = client.get("/api/stats")
        assert response.status_code == 401

    def test_get_stats_returns_200_for_authenticated_user(self, client, auth_headers):
        """Test that authenticated user gets stats."""
        response = client.get("/api/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "stats" in data
        assert "usage" in data

    def test_get_stats_counts_applications_by_status(
        self, app, client, test_user, auth_headers
    ):
        """Test that stats count applications by status."""
        with app.app_context():
            # Create test applications with different statuses
            for status in ["erstellt", "erstellt", "versendet", "antwort_erhalten"]:
                application = Application(
                    user_id=test_user["id"],
                    firma="Test Firma",
                    status=status,
                )
                db.session.add(application)
            db.session.commit()

        response = client.get("/api/stats", headers=auth_headers)
        data = response.get_json()

        assert data["stats"]["gesamt"] == 4
        assert data["stats"]["erstellt"] == 2
        assert data["stats"]["versendet"] == 1
        assert data["stats"]["antwort_erhalten"] == 1


class TestGetExtendedStats:
    """Tests for GET /api/stats/extended"""

    def test_extended_stats_requires_authentication(self, client):
        """Test that /api/stats/extended requires JWT token."""
        response = client.get("/api/stats/extended")
        assert response.status_code == 401

    def test_extended_stats_returns_200_for_authenticated_user(
        self, client, auth_headers
    ):
        """Test that authenticated user gets extended stats."""
        response = client.get("/api/stats/extended", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_extended_stats_contains_all_required_fields(self, client, auth_headers):
        """Test that extended stats response contains all required fields."""
        response = client.get("/api/stats/extended", headers=auth_headers)
        data = response.get_json()["data"]

        # Check all required fields are present
        assert "erfolgsquote" in data
        assert "antwortzeiten" in data
        assert "bewerbungen_pro_woche" in data
        assert "bewerbungen_pro_monat" in data
        assert "top_firmen" in data
        assert "status_verteilung" in data

    def test_extended_stats_erfolgsquote_structure(self, client, auth_headers):
        """Test that erfolgsquote has correct structure."""
        response = client.get("/api/stats/extended", headers=auth_headers)
        erfolgsquote = response.get_json()["data"]["erfolgsquote"]

        assert "bewerbungen_gesamt" in erfolgsquote
        assert "versendet" in erfolgsquote
        assert "antworten" in erfolgsquote
        assert "interviews" in erfolgsquote
        assert "zusagen" in erfolgsquote
        assert "antwort_rate" in erfolgsquote
        assert "interview_rate" in erfolgsquote
        assert "zusage_rate" in erfolgsquote
        assert "gesamt_erfolgsrate" in erfolgsquote

    def test_extended_stats_calculates_erfolgsquote_correctly(
        self, app, client, test_user, auth_headers
    ):
        """Test that erfolgsquote is calculated correctly."""
        with app.app_context():
            # Create a funnel: 10 versendet, 5 antworten, 2 interviews, 1 zusage
            for _ in range(4):
                db.session.add(
                    Application(
                        user_id=test_user["id"], firma="Firma", status="versendet"
                    )
                )
            for _ in range(2):
                db.session.add(
                    Application(
                        user_id=test_user["id"], firma="Firma", status="antwort_erhalten"
                    )
                )
            for _ in range(1):
                db.session.add(
                    Application(
                        user_id=test_user["id"], firma="Firma", status="interview"
                    )
                )
            db.session.add(
                Application(user_id=test_user["id"], firma="Firma", status="zusage")
            )
            db.session.add(
                Application(user_id=test_user["id"], firma="Firma", status="absage")
            )
            db.session.commit()

        response = client.get("/api/stats/extended", headers=auth_headers)
        erfolgsquote = response.get_json()["data"]["erfolgsquote"]

        # versendet = 4 + 2 + 1 + 1 + 1 = 9 (all except erstellt)
        assert erfolgsquote["versendet"] == 9
        # antworten = 2 + 1 + 1 + 1 = 5 (antwort_erhalten, interview, zusage, absage)
        assert erfolgsquote["antworten"] == 5
        # interviews = 1 + 1 = 2 (interview + zusage)
        assert erfolgsquote["interviews"] == 2
        # zusagen = 1
        assert erfolgsquote["zusagen"] == 1

    def test_extended_stats_top_firmen(self, app, client, test_user, auth_headers):
        """Test that top_firmen returns top 5 companies by application count."""
        with app.app_context():
            # Create applications for different companies
            companies = [
                ("Firma A", 5),
                ("Firma B", 3),
                ("Firma C", 2),
                ("Firma D", 1),
                ("Firma E", 1),
                ("Firma F", 1),  # Should not be in top 5
            ]
            for firma, count in companies:
                for _ in range(count):
                    db.session.add(
                        Application(
                            user_id=test_user["id"], firma=firma, status="erstellt"
                        )
                    )
            db.session.commit()

        response = client.get("/api/stats/extended", headers=auth_headers)
        top_firmen = response.get_json()["data"]["top_firmen"]

        assert len(top_firmen) == 5
        assert top_firmen[0]["firma"] == "Firma A"
        assert top_firmen[0]["anzahl"] == 5
        assert top_firmen[1]["firma"] == "Firma B"
        assert top_firmen[1]["anzahl"] == 3

    def test_extended_stats_bewerbungen_pro_woche(self, client, auth_headers):
        """Test that bewerbungen_pro_woche returns 12 weeks."""
        response = client.get("/api/stats/extended", headers=auth_headers)
        bewerbungen_pro_woche = response.get_json()["data"]["bewerbungen_pro_woche"]

        assert len(bewerbungen_pro_woche) == 12
        for week in bewerbungen_pro_woche:
            assert "woche" in week
            assert "start" in week
            assert "ende" in week
            assert "anzahl" in week

    def test_extended_stats_bewerbungen_pro_monat(self, client, auth_headers):
        """Test that bewerbungen_pro_monat returns 12 months."""
        response = client.get("/api/stats/extended", headers=auth_headers)
        bewerbungen_pro_monat = response.get_json()["data"]["bewerbungen_pro_monat"]

        assert len(bewerbungen_pro_monat) == 12
        for month in bewerbungen_pro_monat:
            assert "monat" in month
            assert "monat_kurz" in month
            assert "anzahl" in month

    def test_extended_stats_antwortzeiten(
        self, app, client, test_user, auth_headers
    ):
        """Test that antwortzeiten calculates average response time."""
        with app.app_context():
            now = datetime.utcnow()
            # Create applications with sent_at timestamps
            for days in [1, 2, 3]:  # Average should be 2 days
                db.session.add(
                    Application(
                        user_id=test_user["id"],
                        firma="Firma",
                        status="versendet",
                        datum=now - timedelta(days=days),
                        sent_at=now,
                    )
                )
            db.session.commit()

        response = client.get("/api/stats/extended", headers=auth_headers)
        antwortzeiten = response.get_json()["data"]["antwortzeiten"]

        assert "erstellt_zu_versendet" in antwortzeiten
        assert antwortzeiten["erstellt_zu_versendet"] == 2.0

    def test_extended_stats_status_verteilung(
        self, app, client, test_user, auth_headers
    ):
        """Test that status_verteilung contains all status counts."""
        with app.app_context():
            statuses = ["erstellt", "versendet", "antwort_erhalten", "absage", "zusage"]
            for status in statuses:
                db.session.add(
                    Application(
                        user_id=test_user["id"], firma="Firma", status=status
                    )
                )
            db.session.commit()

        response = client.get("/api/stats/extended", headers=auth_headers)
        status_verteilung = response.get_json()["data"]["status_verteilung"]

        assert status_verteilung["erstellt"] == 1
        assert status_verteilung["versendet"] == 1
        assert status_verteilung["antwort_erhalten"] == 1
        assert status_verteilung["absage"] == 1
        assert status_verteilung["zusage"] == 1

    def test_extended_stats_empty_for_new_user(self, client, auth_headers):
        """Test that extended stats work for user with no applications."""
        response = client.get("/api/stats/extended", headers=auth_headers)
        data = response.get_json()["data"]

        assert data["erfolgsquote"]["bewerbungen_gesamt"] == 0
        assert data["erfolgsquote"]["antwort_rate"] == 0
        assert data["top_firmen"] == []
