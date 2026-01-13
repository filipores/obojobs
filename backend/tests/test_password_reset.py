"""
Tests for password reset service and endpoints.
"""

from datetime import datetime, timedelta

from models import User, db
from routes.auth import (
    MAX_PASSWORD_RESET_PER_HOUR,
    _check_password_reset_rate_limit,
    _password_reset_rate_limits,
    _record_password_reset_request,
)
from services.password_reset_service import PasswordResetService


class TestPasswordResetService:
    """Tests for PasswordResetService"""

    def test_generate_token_returns_urlsafe_string(self):
        """Test that generate_token returns a URL-safe token."""
        token = PasswordResetService.generate_token()

        assert token is not None
        assert isinstance(token, str)
        # 32 bytes in base64url = 43 chars
        assert len(token) == 43

    def test_generate_token_returns_unique_tokens(self):
        """Test that generate_token returns unique tokens each time."""
        token1 = PasswordResetService.generate_token()
        token2 = PasswordResetService.generate_token()

        assert token1 != token2

    def test_create_reset_token_stores_token(self, app):
        """Test that create_reset_token stores token on user."""
        with app.app_context():
            user = User(
                email="reset@example.com",
                full_name="Reset User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            token = PasswordResetService.create_reset_token(user)

            # Refetch user from DB
            user = User.query.filter_by(email="reset@example.com").first()

            assert user.password_reset_token == token
            assert user.password_reset_sent_at is not None
            assert isinstance(user.password_reset_sent_at, datetime)

    def test_is_token_expired_returns_false_for_fresh_token(self, app):
        """Test that fresh token is not expired."""
        with app.app_context():
            user = User(
                email="fresh@example.com",
                full_name="Fresh User",

            )
            user.set_password("TestPass123")
            user.password_reset_sent_at = datetime.utcnow()
            db.session.add(user)
            db.session.commit()

            assert PasswordResetService.is_token_expired(user) is False

    def test_is_token_expired_returns_true_for_expired_token(self, app):
        """Test that token older than 1 hour is expired."""
        with app.app_context():
            user = User(
                email="expired@example.com",
                full_name="Expired User",

            )
            user.set_password("TestPass123")
            # Set sent_at to 2 hours ago
            user.password_reset_sent_at = datetime.utcnow() - timedelta(hours=2)
            db.session.add(user)
            db.session.commit()

            assert PasswordResetService.is_token_expired(user) is True

    def test_is_token_expired_returns_true_when_no_sent_at(self, app):
        """Test that token without sent_at is considered expired."""
        with app.app_context():
            user = User(
                email="nosent@example.com",
                full_name="No Sent User",

            )
            user.set_password("TestPass123")
            user.password_reset_sent_at = None
            db.session.add(user)
            db.session.commit()

            assert PasswordResetService.is_token_expired(user) is True

    def test_verify_token_succeeds_with_valid_token(self, app):
        """Test that verify_token succeeds with valid token."""
        with app.app_context():
            user = User(
                email="valid@example.com",
                full_name="Valid User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            token = PasswordResetService.create_reset_token(user)
            result = PasswordResetService.verify_token(token)

            assert result["success"] is True
            assert "user" in result

    def test_verify_token_fails_with_invalid_token(self, app):
        """Test that verify_token fails with invalid token."""
        with app.app_context():
            result = PasswordResetService.verify_token("invalid-token-123")

            assert result["success"] is False
            assert "Invalid or expired" in result["message"]

    def test_verify_token_fails_with_empty_token(self, app):
        """Test that verify_token fails with empty token."""
        with app.app_context():
            result = PasswordResetService.verify_token("")

            assert result["success"] is False
            assert "Token is required" in result["message"]

    def test_verify_token_fails_with_none_token(self, app):
        """Test that verify_token fails with None token."""
        with app.app_context():
            result = PasswordResetService.verify_token(None)

            assert result["success"] is False
            assert "Token is required" in result["message"]

    def test_verify_token_fails_when_token_expired(self, app):
        """Test that verify_token fails when token is expired."""
        with app.app_context():
            user = User(
                email="expiredtoken@example.com",
                full_name="Expired Token User",

            )
            user.set_password("TestPass123")
            user.password_reset_token = "expired-token-123"
            user.password_reset_sent_at = datetime.utcnow() - timedelta(hours=2)
            db.session.add(user)
            db.session.commit()

            result = PasswordResetService.verify_token("expired-token-123")

            assert result["success"] is False
            assert "expired" in result["message"]

    def test_reset_password_succeeds_with_valid_token(self, app):
        """Test that reset_password succeeds with valid token."""
        with app.app_context():
            user = User(
                email="resetpw@example.com",
                full_name="Reset PW User",

            )
            user.set_password("OldPass123")
            db.session.add(user)
            db.session.commit()

            token = PasswordResetService.create_reset_token(user)
            result = PasswordResetService.reset_password(token, "NewPass456")

            assert result["success"] is True

            # Refetch user and verify password changed
            user = User.query.filter_by(email="resetpw@example.com").first()
            assert user.check_password("NewPass456") is True
            assert user.check_password("OldPass123") is False
            assert user.password_reset_token is None
            assert user.password_reset_sent_at is None

    def test_reset_password_fails_with_invalid_token(self, app):
        """Test that reset_password fails with invalid token."""
        with app.app_context():
            result = PasswordResetService.reset_password("invalid-token", "NewPass456")

            assert result["success"] is False
            assert "Invalid or expired" in result["message"]

    def test_reset_password_fails_with_expired_token(self, app):
        """Test that reset_password fails with expired token."""
        with app.app_context():
            user = User(
                email="expiredreset@example.com",
                full_name="Expired Reset User",

            )
            user.set_password("OldPass123")
            user.password_reset_token = "expired-reset-token"
            user.password_reset_sent_at = datetime.utcnow() - timedelta(hours=2)
            db.session.add(user)
            db.session.commit()

            result = PasswordResetService.reset_password(
                "expired-reset-token", "NewPass456"
            )

            assert result["success"] is False
            assert "expired" in result["message"]

    def test_get_token_expiry_time_returns_correct_time(self, app):
        """Test that get_token_expiry_time returns correct expiry (1 hour)."""
        with app.app_context():
            user = User(
                email="expirytime@example.com",
                full_name="Expiry Time User",

            )
            user.set_password("TestPass123")
            sent_at = datetime.utcnow()
            user.password_reset_sent_at = sent_at
            db.session.add(user)
            db.session.commit()

            expiry = PasswordResetService.get_token_expiry_time(user)

            expected_expiry = sent_at + timedelta(hours=1)
            # Compare with small tolerance for test execution time
            assert abs((expiry - expected_expiry).total_seconds()) < 1

    def test_get_token_expiry_time_returns_none_when_no_token(self, app):
        """Test that get_token_expiry_time returns None when no token."""
        with app.app_context():
            user = User(
                email="noexpiry@example.com",
                full_name="No Expiry User",

            )
            user.set_password("TestPass123")
            user.password_reset_sent_at = None
            db.session.add(user)
            db.session.commit()

            expiry = PasswordResetService.get_token_expiry_time(user)

            assert expiry is None

    def test_clear_reset_token_clears_token_fields(self, app):
        """Test that clear_reset_token clears token and sent_at."""
        with app.app_context():
            user = User(
                email="cleartoken@example.com",
                full_name="Clear Token User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            PasswordResetService.create_reset_token(user)
            assert user.password_reset_token is not None

            PasswordResetService.clear_reset_token(user)

            user = User.query.filter_by(email="cleartoken@example.com").first()
            assert user.password_reset_token is None
            assert user.password_reset_sent_at is None


class TestUserModelPasswordReset:
    """Tests for password reset fields on User model"""

    def test_new_user_has_no_reset_token(self, app):
        """Test that new users have no password reset token."""
        with app.app_context():
            user = User(
                email="newuser@example.com",
                full_name="New User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            assert user.password_reset_token is None
            assert user.password_reset_sent_at is None


class TestForgotPassword:
    """Tests for POST /api/auth/forgot-password"""

    def setup_method(self):
        """Clear rate limit storage before each test."""
        _password_reset_rate_limits.clear()

    def test_forgot_password_returns_200_for_existing_email(self, app, client):
        """Test that forgot-password returns 200 for existing email."""
        with app.app_context():
            user = User(
                email="exists@example.com",
                full_name="Existing User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "exists@example.com"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "If an account with this email exists" in data["message"]

    def test_forgot_password_returns_200_for_nonexistent_email(self, client):
        """Test that forgot-password returns 200 for non-existent email (prevent enumeration)."""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200
        data = response.get_json()
        assert "If an account with this email exists" in data["message"]

    def test_forgot_password_returns_200_for_empty_email(self, client):
        """Test that forgot-password returns 200 for empty email."""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": ""},
        )

        assert response.status_code == 200

    def test_forgot_password_creates_token_for_existing_user(self, app, client):
        """Test that forgot-password creates a token for existing user."""
        with app.app_context():
            user = User(
                email="createtoken@example.com",
                full_name="Create Token User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "createtoken@example.com"},
        )

        assert response.status_code == 200

        with app.app_context():
            user = User.query.filter_by(email="createtoken@example.com").first()
            assert user.password_reset_token is not None
            assert user.password_reset_sent_at is not None

    def test_forgot_password_does_not_create_token_for_nonexistent_user(
        self, app, client
    ):
        """Test that forgot-password does not create tokens for non-existent users."""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nouser@example.com"},
        )

        assert response.status_code == 200

        # No token should exist since user doesn't exist
        with app.app_context():
            user = User.query.filter_by(email="nouser@example.com").first()
            assert user is None

    def test_forgot_password_does_not_create_token_for_inactive_user(self, app, client):
        """Test that forgot-password does not create token for inactive user."""
        with app.app_context():
            user = User(
                email="inactive@example.com",
                full_name="Inactive User",

                is_active=False,
            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "inactive@example.com"},
        )

        assert response.status_code == 200

        with app.app_context():
            user = User.query.filter_by(email="inactive@example.com").first()
            assert user.password_reset_token is None


class TestResetPassword:
    """Tests for POST /api/auth/reset-password"""

    def test_reset_password_with_valid_token_returns_200(self, app, client):
        """Test successful password reset with valid token."""
        with app.app_context():
            user = User(
                email="toreset@example.com",
                full_name="To Reset",

            )
            user.set_password("OldPass123")
            db.session.add(user)
            db.session.commit()

            token = PasswordResetService.create_reset_token(user)

        response = client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "NewSecurePass123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Password reset successfully"

        # Verify password was changed
        with app.app_context():
            user = User.query.filter_by(email="toreset@example.com").first()
            assert user.check_password("NewSecurePass123") is True
            assert user.password_reset_token is None

    def test_reset_password_with_invalid_token_returns_400(self, client):
        """Test reset fails with invalid token."""
        response = client.post(
            "/api/auth/reset-password",
            json={"token": "invalid-token-12345", "new_password": "NewPass123"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid or expired" in data["error"]

    def test_reset_password_without_token_returns_400(self, client):
        """Test reset fails without token."""
        response = client.post(
            "/api/auth/reset-password",
            json={"new_password": "NewPass123"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Token is required" in data["error"]

    def test_reset_password_without_password_returns_400(self, client):
        """Test reset fails without new password."""
        response = client.post(
            "/api/auth/reset-password",
            json={"token": "some-token"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "New password is required" in data["error"]

    def test_reset_password_with_expired_token_returns_400(self, app, client):
        """Test reset fails with expired token."""
        with app.app_context():
            user = User(
                email="expiredreset@example.com",
                full_name="Expired Reset",

            )
            user.set_password("OldPass123")
            user.password_reset_token = "expired-token"
            user.password_reset_sent_at = datetime.utcnow() - timedelta(hours=2)
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/auth/reset-password",
            json={"token": "expired-token", "new_password": "NewPass123"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "expired" in data["error"]

    def test_reset_password_with_weak_password_returns_400(self, app, client):
        """Test reset fails with weak password."""
        with app.app_context():
            user = User(
                email="weakpw@example.com",
                full_name="Weak PW User",

            )
            user.set_password("OldPass123")
            db.session.add(user)
            db.session.commit()

            token = PasswordResetService.create_reset_token(user)

        response = client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "weak"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Password does not meet requirements" in data["error"]
        assert "failed_rules" in data

    def test_reset_password_validates_password_requirements(self, app, client):
        """Test that password validation rules are enforced."""
        with app.app_context():
            user = User(
                email="pwreqs@example.com",
                full_name="PW Reqs User",

            )
            user.set_password("OldPass123")
            db.session.add(user)
            db.session.commit()

            token = PasswordResetService.create_reset_token(user)

        # Password without uppercase
        response = client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "lowercase123"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert any("Großbuchstaben" in rule for rule in data["failed_rules"])


class TestPasswordResetRateLimiting:
    """Tests for password reset rate limiting"""

    def setup_method(self):
        """Clear rate limit storage before each test."""
        _password_reset_rate_limits.clear()

    def test_rate_limit_allows_up_to_max_requests(self):
        """Test that rate limit allows exactly max requests."""
        email = "test@example.com"

        for _ in range(MAX_PASSWORD_RESET_PER_HOUR):
            assert _check_password_reset_rate_limit(email) is True
            _record_password_reset_request(email)

        assert _check_password_reset_rate_limit(email) is False

    def test_rate_limit_resets_after_one_hour(self):
        """Test that rate limit resets after entries expire."""
        email = "expired@example.com"

        # Record requests with old timestamps
        key = email.lower()
        _password_reset_rate_limits[key] = [
            datetime.utcnow() - timedelta(hours=2)
            for _ in range(MAX_PASSWORD_RESET_PER_HOUR)
        ]

        # Should allow new requests since old ones expired
        assert _check_password_reset_rate_limit(email) is True

    def test_rate_limit_is_per_email(self):
        """Test that rate limits are separate per email."""
        email_1 = "user1@example.com"
        email_2 = "user2@example.com"

        # Max out email 1
        for _ in range(MAX_PASSWORD_RESET_PER_HOUR):
            _record_password_reset_request(email_1)

        # Email 1 should be rate limited
        assert _check_password_reset_rate_limit(email_1) is False

        # Email 2 should still be allowed
        assert _check_password_reset_rate_limit(email_2) is True

    def test_rate_limit_is_case_insensitive(self):
        """Test that rate limit treats emails as case-insensitive."""
        # Record with lowercase
        for _ in range(MAX_PASSWORD_RESET_PER_HOUR):
            _record_password_reset_request("test@example.com")

        # Check with uppercase - should be rate limited
        assert _check_password_reset_rate_limit("TEST@EXAMPLE.COM") is False

    def test_forgot_password_rate_limits_requests(self, app, client):
        """Test that forgot-password endpoint rate limits requests."""
        with app.app_context():
            user = User(
                email="ratelimit@example.com",
                full_name="Rate Limit User",

            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

        # Send max allowed requests
        for _ in range(MAX_PASSWORD_RESET_PER_HOUR):
            response = client.post(
                "/api/auth/forgot-password",
                json={"email": "ratelimit@example.com"},
            )
            assert response.status_code == 200

        # Next request should still return 200 (to prevent enumeration)
        # but should not create a new token
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "ratelimit@example.com"},
        )
        assert response.status_code == 200

        # Verify token wasn't overwritten
        with app.app_context():
            user = User.query.filter_by(email="ratelimit@example.com").first()
            # Token should exist from earlier request
            assert user.password_reset_token is not None
