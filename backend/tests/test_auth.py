"""
Tests for authentication endpoints.
"""

from services.password_validator import PasswordValidator


class TestPasswordValidator:
    """Tests for PasswordValidator service"""

    def test_valid_password_passes_all_checks(self):
        """Test that a strong password passes all validation checks."""
        result = PasswordValidator.validate("SecurePass123")

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["checks"]["min_length"] is True
        assert result["checks"]["has_uppercase"] is True
        assert result["checks"]["has_lowercase"] is True
        assert result["checks"]["has_number"] is True

    def test_short_password_fails(self):
        """Test that password shorter than 8 chars fails."""
        result = PasswordValidator.validate("Pass1")

        assert result["valid"] is False
        assert result["checks"]["min_length"] is False
        assert "mindestens 8 Zeichen" in result["errors"][0]

    def test_password_without_uppercase_fails(self):
        """Test that password without uppercase fails."""
        result = PasswordValidator.validate("lowercase123")

        assert result["valid"] is False
        assert result["checks"]["has_uppercase"] is False
        assert any("Großbuchstaben" in e for e in result["errors"])

    def test_password_without_lowercase_fails(self):
        """Test that password without lowercase fails."""
        result = PasswordValidator.validate("UPPERCASE123")

        assert result["valid"] is False
        assert result["checks"]["has_lowercase"] is False
        assert any("Kleinbuchstaben" in e for e in result["errors"])

    def test_password_without_number_fails(self):
        """Test that password without number fails."""
        result = PasswordValidator.validate("PasswordNoNum")

        assert result["valid"] is False
        assert result["checks"]["has_number"] is False
        assert any("Zahl" in e for e in result["errors"])

    def test_get_requirements_returns_all_rules(self):
        """Test that get_requirements returns all password rules."""
        requirements = PasswordValidator.get_requirements()

        assert len(requirements) == 4
        keys = [r["key"] for r in requirements]
        assert "min_length" in keys
        assert "has_uppercase" in keys
        assert "has_lowercase" in keys
        assert "has_number" in keys


class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_with_valid_data_returns_201(self, client):
        """Test successful registration with valid data."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",  # Meets password requirements
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_with_weak_password_returns_400(self, client):
        """Test registration fails with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",  # Too short, missing requirements
                "full_name": "New User",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_register_password_without_uppercase_returns_400(self, client):
        """Test registration fails when password has no uppercase."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "lowercase123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Großbuchstaben" in data["error"]

    def test_register_password_without_number_returns_400(self, client):
        """Test registration fails when password has no number."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "PasswordNoNum",
                "full_name": "New User",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Zahl" in data["error"]

    def test_register_with_existing_email_returns_400(self, client, test_user):
        """Test registration fails with existing email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user["email"],  # Already exists from fixture
                "password": "AnotherPass123",  # Valid password
                "full_name": "Duplicate User",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_with_correct_credentials_returns_200_and_token(self, client, test_user):
        """Test successful login returns 200 and access token."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    def test_login_with_wrong_password_returns_401(self, client, test_user):
        """Test login with wrong password returns 401."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_login_with_nonexistent_email_returns_401(self, client):
        """Test login with non-existent email returns 401."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data


class TestPasswordRequirements:
    """Tests for GET /api/auth/password-requirements"""

    def test_password_requirements_returns_200(self, client):
        """Test that password requirements endpoint returns all rules."""
        response = client.get("/api/auth/password-requirements")

        assert response.status_code == 200
        data = response.get_json()
        assert "requirements" in data
        assert len(data["requirements"]) == 4


class TestValidatePassword:
    """Tests for POST /api/auth/validate-password"""

    def test_validate_strong_password_returns_valid(self, client):
        """Test that strong password validation returns valid."""
        response = client.post(
            "/api/auth/validate-password",
            json={"password": "StrongPass123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is True
        assert data["errors"] == []

    def test_validate_weak_password_returns_invalid(self, client):
        """Test that weak password validation returns invalid."""
        response = client.post(
            "/api/auth/validate-password",
            json={"password": "weak"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
