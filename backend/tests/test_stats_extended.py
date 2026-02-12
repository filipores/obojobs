"""Tests for weekly-goal and company stats endpoints (routes/stats.py uncovered parts)."""

from datetime import datetime

from models import Application, db


class TestWeeklyGoal:
    """Tests for GET /api/stats/weekly-goal"""

    def test_requires_auth(self, client):
        response = client.get("/api/stats/weekly-goal")
        assert response.status_code == 401

    def test_returns_default_goal(self, client, auth_headers):
        response = client.get("/api/stats/weekly-goal", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["goal"] == 5
        assert data["data"]["completed"] == 0
        assert data["data"]["progress"] == 0
        assert data["data"]["is_achieved"] is False

    def test_returns_goal_with_progress(self, app, client, test_user, auth_headers):
        with app.app_context():
            now = datetime.utcnow()
            for _ in range(3):
                db.session.add(Application(user_id=test_user["id"], firma="Firma", status="erstellt", datum=now))
            db.session.commit()

        response = client.get("/api/stats/weekly-goal", headers=auth_headers)
        data = response.get_json()["data"]
        assert data["completed"] == 3
        assert data["progress"] == 60  # 3/5 * 100
        assert data["is_achieved"] is False

    def test_goal_achieved(self, app, client, test_user, auth_headers):
        with app.app_context():
            now = datetime.utcnow()
            for _ in range(5):
                db.session.add(Application(user_id=test_user["id"], firma="Firma", status="erstellt", datum=now))
            db.session.commit()

        response = client.get("/api/stats/weekly-goal", headers=auth_headers)
        data = response.get_json()["data"]
        assert data["is_achieved"] is True
        assert data["progress"] == 100


class TestUpdateWeeklyGoal:
    """Tests for PUT /api/stats/weekly-goal"""

    def test_requires_auth(self, client):
        response = client.put("/api/stats/weekly-goal", json={"goal": 10})
        assert response.status_code == 401

    def test_update_goal(self, client, auth_headers):
        response = client.put(
            "/api/stats/weekly-goal",
            json={"goal": 10},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["goal"] == 10

    def test_missing_goal(self, client, auth_headers):
        response = client.put(
            "/api/stats/weekly-goal",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_goal_type(self, client, auth_headers):
        response = client.put(
            "/api/stats/weekly-goal",
            json={"goal": "abc"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_goal_too_low(self, client, auth_headers):
        response = client.put(
            "/api/stats/weekly-goal",
            json={"goal": 0},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_goal_too_high(self, client, auth_headers):
        response = client.put(
            "/api/stats/weekly-goal",
            json={"goal": 51},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestCompanyStats:
    """Tests for GET /api/stats/companies"""

    def test_requires_auth(self, client):
        response = client.get("/api/stats/companies")
        assert response.status_code == 401

    def test_empty_companies(self, client, auth_headers):
        response = client.get("/api/stats/companies", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["companies"] == []
        assert data["data"]["total_companies"] == 0

    def test_companies_with_data(self, app, client, test_user, auth_headers):
        with app.app_context():
            for _ in range(3):
                db.session.add(Application(user_id=test_user["id"], firma="Firma A", status="versendet"))
            for _ in range(2):
                db.session.add(Application(user_id=test_user["id"], firma="Firma B", status="erstellt"))
            db.session.add(Application(user_id=test_user["id"], firma="Firma A", status="antwort_erhalten"))
            db.session.commit()

        response = client.get("/api/stats/companies", headers=auth_headers)
        data = response.get_json()["data"]
        assert data["total_companies"] == 2
        # Default sort is by bewerbungen desc
        assert data["companies"][0]["firma"] == "Firma A"
        assert data["companies"][0]["bewerbungen"] == 4
        assert data["companies"][0]["antworten"] == 1

    def test_sort_by_name(self, app, client, test_user, auth_headers):
        with app.app_context():
            db.session.add(Application(user_id=test_user["id"], firma="Zebra GmbH", status="erstellt"))
            db.session.add(Application(user_id=test_user["id"], firma="Alpha AG", status="erstellt"))
            db.session.commit()

        response = client.get("/api/stats/companies?sort_by=name", headers=auth_headers)
        companies = response.get_json()["data"]["companies"]
        assert companies[0]["firma"] == "Alpha AG"
        assert companies[1]["firma"] == "Zebra GmbH"

    def test_sort_by_antwortrate(self, app, client, test_user, auth_headers):
        with app.app_context():
            db.session.add(Application(user_id=test_user["id"], firma="Good Corp", status="zusage"))
            db.session.add(Application(user_id=test_user["id"], firma="Good Corp", status="erstellt"))
            db.session.add(Application(user_id=test_user["id"], firma="Bad Corp", status="erstellt"))
            db.session.commit()

        response = client.get("/api/stats/companies?sort_by=antwortrate", headers=auth_headers)
        companies = response.get_json()["data"]["companies"]
        assert companies[0]["firma"] == "Good Corp"
        assert companies[0]["antwortrate"] == 50.0

    def test_invalid_sort_defaults_to_bewerbungen(self, app, client, test_user, auth_headers):
        with app.app_context():
            db.session.add(Application(user_id=test_user["id"], firma="Test", status="erstellt"))
            db.session.commit()

        response = client.get("/api/stats/companies?sort_by=invalid", headers=auth_headers)
        data = response.get_json()["data"]
        assert data["sort_by"] == "bewerbungen"
