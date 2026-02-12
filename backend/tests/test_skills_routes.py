"""Tests for skills routes (routes/skills.py)."""

from unittest.mock import MagicMock, patch

from models import Document, UserSkill, db


class TestGetUserSkills:
    """Tests for GET /api/users/me/skills"""

    def test_requires_auth(self, client):
        response = client.get("/api/users/me/skills")
        assert response.status_code == 401

    def test_returns_empty_skills(self, client, auth_headers):
        response = client.get("/api/users/me/skills", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["skills"] == []
        assert data["total_count"] == 0

    def test_returns_skills_grouped_by_category(self, app, client, test_user, auth_headers):
        with app.app_context():
            db.session.add(
                UserSkill(
                    user_id=test_user["id"],
                    skill_name="Python",
                    skill_category="technical",
                    experience_years=5.0,
                )
            )
            db.session.add(
                UserSkill(
                    user_id=test_user["id"],
                    skill_name="Teamwork",
                    skill_category="soft_skills",
                )
            )
            db.session.commit()

        response = client.get("/api/users/me/skills", headers=auth_headers)
        data = response.get_json()
        assert data["total_count"] == 2
        assert "technical" in data["skills_by_category"]
        assert "soft_skills" in data["skills_by_category"]
        assert len(data["skills_by_category"]["technical"]) == 1
        assert data["skills_by_category"]["technical"][0]["skill_name"] == "Python"


class TestAddSkill:
    """Tests for POST /api/users/me/skills"""

    def test_requires_auth(self, client):
        response = client.post("/api/users/me/skills", json={"skill_name": "Python"})
        assert response.status_code == 401

    def test_add_skill_success(self, client, auth_headers):
        response = client.post(
            "/api/users/me/skills",
            json={
                "skill_name": "Python",
                "skill_category": "technical",
                "experience_years": 3,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["skill"]["skill_name"] == "Python"
        assert data["skill"]["skill_category"] == "technical"

    def test_add_skill_missing_name(self, client, auth_headers):
        response = client.post(
            "/api/users/me/skills",
            json={"skill_name": "", "skill_category": "technical"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_add_skill_invalid_category(self, client, auth_headers):
        response = client.post(
            "/api/users/me/skills",
            json={"skill_name": "Python", "skill_category": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_add_skill_missing_category(self, client, auth_headers):
        response = client.post(
            "/api/users/me/skills",
            json={"skill_name": "Python", "skill_category": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_add_skill_duplicate(self, app, client, test_user, auth_headers):
        with app.app_context():
            db.session.add(
                UserSkill(
                    user_id=test_user["id"],
                    skill_name="Python",
                    skill_category="technical",
                )
            )
            db.session.commit()

        response = client.post(
            "/api/users/me/skills",
            json={"skill_name": "Python", "skill_category": "technical"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_add_skill_negative_experience(self, client, auth_headers):
        response = client.post(
            "/api/users/me/skills",
            json={"skill_name": "Python", "skill_category": "technical", "experience_years": -1},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_add_skill_invalid_experience(self, client, auth_headers):
        response = client.post(
            "/api/users/me/skills",
            json={"skill_name": "Python", "skill_category": "technical", "experience_years": "abc"},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestUpdateSkill:
    """Tests for PUT /api/users/me/skills/<id>"""

    def test_requires_auth(self, client):
        response = client.put("/api/users/me/skills/1", json={"skill_name": "Go"})
        assert response.status_code == 401

    def test_update_skill_name(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Pythn",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"skill_name": "Python"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["skill"]["skill_name"] == "Python"

    def test_update_skill_category(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Docker",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"skill_category": "tools"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["skill"]["skill_category"] == "tools"

    def test_update_experience_years(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"experience_years": 5.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["skill"]["experience_years"] == 5.0

    def test_update_not_found(self, client, auth_headers):
        response = client.put(
            "/api/users/me/skills/9999",
            json={"skill_name": "Go"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_empty_name(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"skill_name": "  "},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_update_invalid_category(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"skill_category": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_update_negative_experience(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"experience_years": -1},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_update_invalid_experience(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"experience_years": "abc"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_update_experience_to_none(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
                experience_years=3.0,
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.put(
            f"/api/users/me/skills/{skill_id}",
            json={"experience_years": None},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["skill"]["experience_years"] is None


class TestDeleteSkill:
    """Tests for DELETE /api/users/me/skills/<id>"""

    def test_requires_auth(self, client):
        response = client.delete("/api/users/me/skills/1")
        assert response.status_code == 401

    def test_delete_skill(self, app, client, test_user, auth_headers):
        with app.app_context():
            skill = UserSkill(
                user_id=test_user["id"],
                skill_name="Python",
                skill_category="technical",
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = client.delete(
            f"/api/users/me/skills/{skill_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["success"] is True

    def test_delete_not_found(self, client, auth_headers):
        response = client.delete(
            "/api/users/me/skills/9999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestExtractSkillsFromDocument:
    """Tests for POST /api/documents/<id>/extract-skills"""

    def test_requires_auth(self, client):
        response = client.post("/api/documents/1/extract-skills")
        assert response.status_code == 401

    def test_document_not_found(self, client, auth_headers):
        response = client.post(
            "/api/documents/9999/extract-skills",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_non_cv_document_rejected(self, app, client, test_user, auth_headers):
        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="arbeitszeugnis",
                file_path="/tmp/test.txt",
                original_filename="test.txt",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.post(
            f"/api/documents/{doc_id}/extract-skills",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Lebensl" in response.get_json()["error"]

    @patch("routes.skills.os.path.exists", return_value=False)
    def test_file_not_found(self, mock_exists, app, client, test_user, auth_headers):
        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/tmp/nonexistent.txt",
                original_filename="cv.txt",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.post(
            f"/api/documents/{doc_id}/extract-skills",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @patch("routes.skills.SkillExtractor")
    @patch("builtins.open", create=True)
    @patch("routes.skills.os.path.exists", return_value=True)
    def test_extract_success(self, mock_exists, mock_open, mock_extractor_cls, app, client, test_user, auth_headers):
        import io

        mock_open.return_value.__enter__ = lambda s: io.StringIO("Python developer with 5 years experience")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_extractor = MagicMock()
        mock_extractor.extract_skills_from_cv.return_value = [
            {"skill_name": "Python", "skill_category": "technical", "experience_years": 5.0},
            {"skill_name": "Docker", "skill_category": "tools", "experience_years": None},
        ]
        mock_extractor_cls.return_value = mock_extractor

        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/tmp/cv.txt",
                original_filename="cv.txt",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.post(
            f"/api/documents/{doc_id}/extract-skills",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["new_skills_count"] == 2

    @patch("routes.skills.SkillExtractor")
    @patch("builtins.open", create=True)
    @patch("routes.skills.os.path.exists", return_value=True)
    def test_extract_no_skills_found(
        self, mock_exists, mock_open, mock_extractor_cls, app, client, test_user, auth_headers
    ):
        import io

        mock_open.return_value.__enter__ = lambda s: io.StringIO("Some text")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_extractor = MagicMock()
        mock_extractor.extract_skills_from_cv.return_value = []
        mock_extractor_cls.return_value = mock_extractor

        with app.app_context():
            doc = Document(
                user_id=test_user["id"],
                doc_type="lebenslauf",
                file_path="/tmp/cv.txt",
                original_filename="cv.txt",
            )
            db.session.add(doc)
            db.session.commit()
            doc_id = doc.id

        response = client.post(
            f"/api/documents/{doc_id}/extract-skills",
            headers=auth_headers,
        )
        assert response.status_code == 400
