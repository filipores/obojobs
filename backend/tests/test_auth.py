"""
Tests for authentication endpoints.
"""

from datetime import datetime, timedelta

from models import User, db
from routes.auth import (
    MAX_VERIFICATION_EMAILS_PER_HOUR,
    _check_verification_rate_limit,
    _record_verification_request,
    _verification_rate_limits,
)
from services.email_verification_service import EmailVerificationService
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


class TestSendVerification:
    """Tests for POST /api/auth/send-verification"""

    def setup_method(self):
        """Clear rate limit storage before each test."""
        _verification_rate_limits.clear()

    def test_send_verification_requires_authentication(self, client):
        """Test that send-verification requires JWT token."""
        response = client.post("/api/auth/send-verification")

        assert response.status_code == 401

    def test_send_verification_returns_200_for_unverified_user(
        self, client, test_user, auth_headers
    ):
        """Test successful verification email request."""
        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["email"] == test_user["email"]

    def test_send_verification_returns_400_for_already_verified_user(
        self, app, client, test_user, auth_headers
    ):
        """Test that already verified users get 400."""
        # Mark user as verified
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            user.email_verified = True
            db.session.commit()

        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "already verified" in data["error"]

    def test_send_verification_rate_limited_after_max_requests(
        self, client, test_user, auth_headers
    ):
        """Test that rate limiting kicks in after max requests."""
        # Send max allowed requests
        for _ in range(MAX_VERIFICATION_EMAILS_PER_HOUR):
            response = client.post(
                "/api/auth/send-verification",
                headers=auth_headers,
            )
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers,
        )

        assert response.status_code == 429
        data = response.get_json()
        assert "Too many verification requests" in data["error"]
        assert "retry_after_minutes" in data

    def test_send_verification_creates_token(self, app, client, test_user, auth_headers):
        """Test that send-verification creates a token for the user."""
        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers,
        )

        assert response.status_code == 200

        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.email_verification_token is not None
            assert user.email_verification_sent_at is not None


class TestVerifyEmail:
    """Tests for POST /api/auth/verify-email"""

    def test_verify_email_with_valid_token_returns_200(self, app, client):
        """Test successful email verification with valid token."""
        # Create user with verification token
        with app.app_context():
            user = User(
                email="toverify@example.com",
                full_name="To Verify",
                credits_remaining=5,
            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            token = EmailVerificationService.create_verification_token(user)

        response = client.post(
            "/api/auth/verify-email",
            json={"token": token},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Email verified successfully"
        assert data["user"]["email_verified"] is True

    def test_verify_email_with_invalid_token_returns_400(self, client):
        """Test verification fails with invalid token."""
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "invalid-token-12345"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid verification token" in data["error"]

    def test_verify_email_without_token_returns_400(self, client):
        """Test verification fails without token."""
        response = client.post(
            "/api/auth/verify-email",
            json={},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Token is required" in data["error"]

    def test_verify_email_with_expired_token_returns_400(self, app, client):
        """Test verification fails with expired token."""
        with app.app_context():
            user = User(
                email="expired@example.com",
                full_name="Expired Token",
                credits_remaining=5,
            )
            user.set_password("TestPass123")
            user.email_verification_token = "expired-token"
            user.email_verification_sent_at = datetime.utcnow() - timedelta(hours=25)
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/verify-email",
            json={"token": "expired-token"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "expired" in data["error"]

    def test_verify_email_for_already_verified_returns_400(self, app, client):
        """Test verification fails when email already verified."""
        with app.app_context():
            user = User(
                email="alreadyverified@example.com",
                full_name="Already Verified",
                credits_remaining=5,
                email_verified=True,
            )
            user.set_password("TestPass123")
            user.email_verification_token = "some-token"
            user.email_verification_sent_at = datetime.utcnow()
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/verify-email",
            json={"token": "some-token"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "already verified" in data["error"]


class TestMeEndpointEmailVerified:
    """Tests for GET /api/auth/me returning email_verified"""

    def test_me_returns_email_verified_false_for_new_user(
        self, client, test_user, auth_headers
    ):
        """Test that /me returns email_verified: false for new users."""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "email_verified" in data
        assert data["email_verified"] is False

    def test_me_returns_email_verified_true_after_verification(
        self, app, client, test_user, auth_headers
    ):
        """Test that /me returns email_verified: true after verification."""
        # Mark user as verified
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            user.email_verified = True
            db.session.commit()

        response = client.get(
            "/api/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["email_verified"] is True


class TestVerificationRateLimiting:
    """Tests for verification email rate limiting"""

    def setup_method(self):
        """Clear rate limit storage before each test."""
        _verification_rate_limits.clear()

    def test_rate_limit_allows_up_to_max_requests(self):
        """Test that rate limit allows exactly max requests."""
        user_id = 999

        for _ in range(MAX_VERIFICATION_EMAILS_PER_HOUR):
            assert _check_verification_rate_limit(user_id) is True
            _record_verification_request(user_id)

        assert _check_verification_rate_limit(user_id) is False

    def test_rate_limit_resets_after_one_hour(self):
        """Test that rate limit resets after entries expire."""
        user_id = 888

        # Record requests with old timestamps
        key = str(user_id)
        _verification_rate_limits[key] = [
            datetime.utcnow() - timedelta(hours=2)
            for _ in range(MAX_VERIFICATION_EMAILS_PER_HOUR)
        ]

        # Should allow new requests since old ones expired
        assert _check_verification_rate_limit(user_id) is True

    def test_rate_limit_is_per_user(self):
        """Test that rate limits are separate per user."""
        user_id_1 = 111
        user_id_2 = 222

        # Max out user 1
        for _ in range(MAX_VERIFICATION_EMAILS_PER_HOUR):
            _record_verification_request(user_id_1)

        # User 1 should be rate limited
        assert _check_verification_rate_limit(user_id_1) is False

        # User 2 should still be allowed
        assert _check_verification_rate_limit(user_id_2) is True
