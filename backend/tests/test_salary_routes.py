"""Tests for salary routes (routes/salary.py)."""

from unittest.mock import MagicMock, patch

from models import SalaryCoachData, db


class TestResearchSalary:
    """Tests for POST /api/salary/research"""

    def test_requires_auth(self, client):
        response = client.post("/api/salary/research", json={"position": "Dev"})
        assert response.status_code == 401

    def test_missing_body(self, client, auth_headers):
        response = client.post(
            "/api/salary/research",
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_missing_position(self, client, auth_headers):
        response = client.post(
            "/api/salary/research",
            json={"region": "Berlin"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_empty_position(self, client, auth_headers):
        response = client.post(
            "/api/salary/research",
            json={"position": "  "},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.salary.SalaryCoach")
    def test_research_success(self, mock_coach_cls, client, auth_headers):
        mock_coach = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "position": "Software Engineer",
            "region": "Berlin",
            "min_salary": 55000,
            "max_salary": 85000,
            "median_salary": 70000,
        }
        mock_coach.research_salary.return_value = mock_result
        mock_coach_cls.return_value = mock_coach

        response = client.post(
            "/api/salary/research",
            json={"position": "Software Engineer", "region": "Berlin", "experience_years": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "research" in data
        assert data["research"]["min_salary"] == 55000

    @patch("routes.salary.SalaryCoach")
    def test_research_value_error(self, mock_coach_cls, client, auth_headers):
        mock_coach = MagicMock()
        mock_coach.research_salary.side_effect = ValueError("Bad input")
        mock_coach_cls.return_value = mock_coach

        response = client.post(
            "/api/salary/research",
            json={"position": "Dev"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.salary.SalaryCoach")
    def test_research_internal_error(self, mock_coach_cls, client, auth_headers):
        mock_coach = MagicMock()
        mock_coach.research_salary.side_effect = RuntimeError("API down")
        mock_coach_cls.return_value = mock_coach

        response = client.post(
            "/api/salary/research",
            json={"position": "Dev"},
            headers=auth_headers,
        )
        assert response.status_code == 500

    def test_invalid_experience_years_uses_default(self, client, auth_headers):
        """Invalid experience_years should fallback to default 3."""
        with patch("routes.salary.SalaryCoach") as mock_coach_cls:
            mock_coach = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"position": "Dev"}
            mock_coach.research_salary.return_value = mock_result
            mock_coach_cls.return_value = mock_coach

            response = client.post(
                "/api/salary/research",
                json={"position": "Dev", "experience_years": "abc"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            # Verify fallback was used
            call_kwargs = mock_coach.research_salary.call_args
            assert call_kwargs.kwargs["experience_years"] == 3


class TestNegotiationTips:
    """Tests for POST /api/salary/negotiation-tips"""

    def test_requires_auth(self, client):
        response = client.post("/api/salary/negotiation-tips", json={"target_salary": 70000})
        assert response.status_code == 401

    def test_missing_body(self, client, auth_headers):
        response = client.post(
            "/api/salary/negotiation-tips",
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_missing_target_salary(self, client, auth_headers):
        response = client.post(
            "/api/salary/negotiation-tips",
            json={"position": "Dev"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_negative_target_salary(self, client, auth_headers):
        response = client.post(
            "/api/salary/negotiation-tips",
            json={"target_salary": -1000},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_zero_target_salary(self, client, auth_headers):
        response = client.post(
            "/api/salary/negotiation-tips",
            json={"target_salary": 0},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_target_salary(self, client, auth_headers):
        response = client.post(
            "/api/salary/negotiation-tips",
            json={"target_salary": "abc"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.salary.SalaryCoach")
    def test_negotiation_tips_success(self, mock_coach_cls, client, auth_headers):
        mock_coach = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "target_salary": 70000,
            "recommended_range": {"min": 66500, "max": 77000},
            "tips": ["Be confident"],
        }
        mock_coach.generate_negotiation_tips.return_value = mock_result
        mock_coach_cls.return_value = mock_coach

        response = client.post(
            "/api/salary/negotiation-tips",
            json={
                "target_salary": 70000,
                "current_salary": 55000,
                "position": "Dev",
                "experience_years": 5,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["strategy"]["target_salary"] == 70000

    @patch("routes.salary.SalaryCoach")
    def test_negotiation_tips_value_error(self, mock_coach_cls, client, auth_headers):
        mock_coach = MagicMock()
        mock_coach.generate_negotiation_tips.side_effect = ValueError("Bad")
        mock_coach_cls.return_value = mock_coach

        response = client.post(
            "/api/salary/negotiation-tips",
            json={"target_salary": 70000},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.salary.SalaryCoach")
    def test_negotiation_tips_internal_error(self, mock_coach_cls, client, auth_headers):
        mock_coach = MagicMock()
        mock_coach.generate_negotiation_tips.side_effect = RuntimeError("API down")
        mock_coach_cls.return_value = mock_coach

        response = client.post(
            "/api/salary/negotiation-tips",
            json={"target_salary": 70000},
            headers=auth_headers,
        )
        assert response.status_code == 500

    def test_invalid_current_salary_ignored(self, client, auth_headers):
        """Invalid current_salary should be set to None."""
        with patch("routes.salary.SalaryCoach") as mock_coach_cls:
            mock_coach = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"target_salary": 70000}
            mock_coach.generate_negotiation_tips.return_value = mock_result
            mock_coach_cls.return_value = mock_coach

            response = client.post(
                "/api/salary/negotiation-tips",
                json={"target_salary": 70000, "current_salary": "not-a-number"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            call_kwargs = mock_coach.generate_negotiation_tips.call_args
            assert call_kwargs.kwargs["current_salary"] is None


class TestGetSalaryData:
    """Tests for GET /api/salary/data"""

    def test_requires_auth(self, client):
        response = client.get("/api/salary/data")
        assert response.status_code == 401

    def test_no_data_returns_null(self, client, auth_headers):
        response = client.get("/api/salary/data", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"] is None

    def test_returns_existing_data(self, app, client, test_user, auth_headers):
        with app.app_context():
            salary_data = SalaryCoachData(
                user_id=test_user["id"],
                position="Software Engineer",
                region="Berlin",
                experience_years=5,
                target_salary=70000,
            )
            db.session.add(salary_data)
            db.session.commit()

        response = client.get("/api/salary/data", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"] is not None


class TestSaveSalaryData:
    """Tests for POST /api/salary/data"""

    def test_requires_auth(self, client):
        response = client.post("/api/salary/data", json={"formData": {}})
        assert response.status_code == 401

    def test_missing_body(self, client, auth_headers):
        response = client.post(
            "/api/salary/data",
            headers=auth_headers,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_save_new_data(self, client, auth_headers):
        response = client.post(
            "/api/salary/data",
            json={
                "formData": {
                    "position": "Software Engineer",
                    "region": "Berlin",
                    "experienceYears": 5,
                    "targetSalary": 70000,
                    "currentSalary": 55000,
                    "industry": "IT",
                },
                "research": {"min_salary": 55000},
                "strategy": {"tips": ["Be confident"]},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["success"] is True

    def test_update_existing_data(self, app, client, test_user, auth_headers):
        with app.app_context():
            salary_data = SalaryCoachData(
                user_id=test_user["id"],
                position="Dev",
            )
            db.session.add(salary_data)
            db.session.commit()

        response = client.post(
            "/api/salary/data",
            json={
                "formData": {"position": "Senior Dev", "region": ""},
                "research": None,
                "strategy": None,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_save_with_null_research_and_strategy(self, client, auth_headers):
        response = client.post(
            "/api/salary/data",
            json={
                "formData": {"position": "Dev"},
                "research": None,
                "strategy": None,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestDeleteSalaryData:
    """Tests for DELETE /api/salary/data"""

    def test_requires_auth(self, client):
        response = client.delete("/api/salary/data")
        assert response.status_code == 401

    def test_delete_existing_data(self, app, client, test_user, auth_headers):
        with app.app_context():
            salary_data = SalaryCoachData(
                user_id=test_user["id"],
                position="Dev",
            )
            db.session.add(salary_data)
            db.session.commit()

        response = client.delete("/api/salary/data", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert response.get_json()["message"] == "Daten gelöscht"

    def test_delete_nonexistent_data(self, client, auth_headers):
        """Deleting when no data exists should still succeed."""
        response = client.delete("/api/salary/data", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
