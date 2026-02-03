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
from services.auth_service import LOCKOUT_DURATION_MINUTES, MAX_FAILED_ATTEMPTS
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

    def test_send_verification_returns_200_for_unverified_user(self, client, test_user, auth_headers):
        """Test successful verification email request."""
        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["email"] == test_user["email"]

    def test_send_verification_returns_400_for_already_verified_user(self, app, client, test_user, auth_headers):
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
        assert "bereits bestätigt" in data["error"]

    def test_send_verification_rate_limited_after_max_requests(self, client, test_user, auth_headers):
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
        assert "Zu viele Bestätigungsanfragen" in data["error"]
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
        assert data["message"] == "E-Mail erfolgreich bestätigt"
        assert data["user"]["email_verified"] is True

    def test_verify_email_with_invalid_token_returns_400(self, client):
        """Test verification fails with invalid token."""
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "invalid-token-12345"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Ungültiger Bestätigungstoken" in data["error"]

    def test_verify_email_without_token_returns_400(self, client):
        """Test verification fails without token."""
        response = client.post(
            "/api/auth/verify-email",
            json={},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Token ist erforderlich" in data["error"]

    def test_verify_email_with_expired_token_returns_400(self, app, client):
        """Test verification fails with expired token."""
        with app.app_context():
            user = User(
                email="expired@example.com",
                full_name="Expired Token",
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
        assert "abgelaufen" in data["error"]

    def test_verify_email_for_already_verified_returns_400(self, app, client):
        """Test verification fails when email already verified."""
        with app.app_context():
            user = User(
                email="alreadyverified@example.com",
                full_name="Already Verified",
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
        assert "bereits bestätigt" in data["error"]


class TestMeEndpointEmailVerified:
    """Tests for GET /api/auth/me returning email_verified"""

    def test_me_returns_email_verified_false_for_new_user(self, client, test_user, auth_headers):
        """Test that /me returns email_verified: false for new users."""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "email_verified" in data
        assert data["email_verified"] is False

    def test_me_returns_email_verified_true_after_verification(self, app, client, test_user, auth_headers):
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
            datetime.utcnow() - timedelta(hours=2) for _ in range(MAX_VERIFICATION_EMAILS_PER_HOUR)
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


class TestAccountLockout:
    """Tests for account lockout after failed login attempts"""

    def test_failed_login_increments_counter(self, app, client, test_user):
        """Test that failed login attempts increment the counter."""
        # Make a failed login attempt
        client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword",
            },
        )

        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.failed_login_attempts == 1

    def test_multiple_failed_logins_increment_counter(self, app, client, test_user):
        """Test that multiple failed logins increment the counter."""
        for _ in range(3):
            client.post(
                "/api/auth/login",
                json={
                    "email": test_user["email"],
                    "password": "wrongpassword",
                },
            )

        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.failed_login_attempts == 3

    def test_account_locks_after_max_failed_attempts(self, app, client, test_user):
        """Test that account locks after MAX_FAILED_ATTEMPTS."""
        # Make MAX_FAILED_ATTEMPTS failed login attempts
        for _ in range(MAX_FAILED_ATTEMPTS):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": test_user["email"],
                    "password": "wrongpassword",
                },
            )

        # Check that the last response indicates account is locked
        assert response.status_code == 401
        data = response.get_json()
        assert "gesperrt" in data["error"]
        assert str(LOCKOUT_DURATION_MINUTES) in data["error"]

        # Verify the account is locked in the database
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.locked_until is not None
            assert user.failed_login_attempts == MAX_FAILED_ATTEMPTS

    def test_locked_account_cannot_login_even_with_correct_password(self, app, client, test_user):
        """Test that locked account cannot login with correct password."""
        # Lock the account
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            user.failed_login_attempts = MAX_FAILED_ATTEMPTS
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            db.session.commit()

        # Try to login with correct password
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "vorübergehend gesperrt" in data["error"]

    def test_successful_login_resets_failed_attempts(self, app, client, test_user):
        """Test that successful login resets the failed attempts counter."""
        # First make some failed attempts
        for _ in range(2):
            client.post(
                "/api/auth/login",
                json={
                    "email": test_user["email"],
                    "password": "wrongpassword",
                },
            )

        # Verify counter is incremented
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.failed_login_attempts == 2

        # Now login successfully
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200

        # Verify counter is reset
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.failed_login_attempts == 0

    def test_lock_expires_after_lockout_duration(self, app, client, test_user):
        """Test that lock expires after LOCKOUT_DURATION_MINUTES."""
        # Lock the account with an expired lockout
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            user.failed_login_attempts = MAX_FAILED_ATTEMPTS
            # Set lockout to have expired 1 minute ago
            user.locked_until = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()

        # Try to login with correct password - should succeed
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200

        # Verify lockout was reset
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.locked_until is None
            assert user.failed_login_attempts == 0

    def test_failed_login_for_nonexistent_user_does_not_error(self, client):
        """Test that failed login for non-existent user doesn't cause errors."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "Ungültige E-Mail oder Passwort" in data["error"]

    def test_lockout_message_shows_remaining_time(self, app, client, test_user):
        """Test that lockout message shows approximate remaining time."""
        # Lock the account with 10 minutes remaining
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            user.failed_login_attempts = MAX_FAILED_ATTEMPTS
            user.locked_until = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()

        # Try to login
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        # Should show remaining time in message
        assert "vorübergehend gesperrt" in data["error"]
        assert "Minuten" in data["error"]

    def test_lock_resets_after_expiry_on_failed_login(self, app, client, test_user):
        """Test that expired lock is reset even on failed login attempt."""
        # Lock the account with an expired lockout
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            user.failed_login_attempts = MAX_FAILED_ATTEMPTS
            user.locked_until = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()

        # Try to login with wrong password - should reset lock but fail auth
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "Ungültige E-Mail oder Passwort" in data["error"]

        # Verify lockout was reset but now has 1 failed attempt
        with app.app_context():
            user = User.query.filter_by(email=test_user["email"]).first()
            assert user.locked_until is None
            assert user.failed_login_attempts == 1


class TestChangePassword:
    """Tests for PUT /api/auth/change-password"""

    def test_change_password_success(self, client, test_user, auth_headers):
        """Test successful password change."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": "NewSecure456",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "erfolgreich" in data["message"]

    def test_change_password_can_login_with_new_password(self, client, test_user, auth_headers):
        """Test that user can login with new password after change."""
        new_password = "ChangedPass789"

        # Change password
        client.put(
            "/api/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": new_password,
            },
            headers=auth_headers,
        )

        # Login with new password
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": new_password,
            },
        )

        assert response.status_code == 200

    def test_change_password_wrong_current_password(self, client, auth_headers):
        """Test that wrong current password is rejected."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "NewSecure456",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Aktuelles Passwort ist falsch" in data["error"]

    def test_change_password_weak_new_password(self, client, test_user, auth_headers):
        """Test that weak new password is rejected."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": "weak",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_change_password_same_as_current(self, client, test_user, auth_headers):
        """Test that same password as current is rejected."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": test_user["password"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "unterscheiden" in data["error"]

    def test_change_password_missing_current_password(self, client, auth_headers):
        """Test that missing current password returns 400."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "new_password": "NewSecure456",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Aktuelles Passwort ist erforderlich" in data["error"]

    def test_change_password_missing_new_password(self, client, test_user, auth_headers):
        """Test that missing new password returns 400."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": test_user["password"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Neues Passwort ist erforderlich" in data["error"]

    def test_change_password_requires_authentication(self, client):
        """Test that change-password requires authentication."""
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": "TestPass123",
                "new_password": "NewSecure456",
            },
        )

        assert response.status_code == 401

    def test_change_password_old_password_cannot_login(self, client, test_user, auth_headers):
        """Test that old password no longer works after change."""
        new_password = "ChangedPass789"

        # Change password
        client.put(
            "/api/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": new_password,
            },
            headers=auth_headers,
        )

        # Try to login with old password
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for POST /api/auth/logout"""

    def test_logout_requires_authentication(self, client):
        """Test that logout requires authentication."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401

    def test_logout_success_returns_200(self, client, auth_headers):
        """Test successful logout returns 200."""
        response = client.post(
            "/api/auth/logout",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "abgemeldet" in data["message"].lower()

    def test_logout_invalidates_token(self, client, auth_headers):
        """Test that token is invalid after logout."""
        # First logout
        response = client.post(
            "/api/auth/logout",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Try to use the same token again
        response = client.get(
            "/api/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "widerrufen" in data["error"]

    def test_logout_token_cannot_be_used_for_other_endpoints(self, client, auth_headers):
        """Test that logged out token cannot be used for any authenticated endpoint."""
        # First logout
        client.post(
            "/api/auth/logout",
            headers=auth_headers,
        )

        # Try to use token for send-verification
        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers,
        )

        assert response.status_code == 401

    def test_logout_does_not_affect_other_tokens(self, client, test_user):
        """Test that logging out one token doesn't affect other tokens."""
        # Get two tokens by logging in twice
        response1 = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        token1 = response1.get_json()["access_token"]

        response2 = client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        token2 = response2.get_json()["access_token"]

        # Logout with token1
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token1}"},
        )

        # Token1 should be revoked
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 401

        # Token2 should still work
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 200

    def test_logout_can_login_again_after_logout(self, client, test_user, auth_headers):
        """Test that user can login again after logout."""
        # First logout
        client.post(
            "/api/auth/logout",
            headers=auth_headers,
        )

        # Login again
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

        # New token should work
        new_headers = {"Authorization": f"Bearer {data['access_token']}"}
        response = client.get(
            "/api/auth/me",
            headers=new_headers,
        )
        assert response.status_code == 200


class TestDeleteAccount:
    """Tests for DELETE /api/auth/delete-account"""

    def test_delete_account_requires_authentication(self, client):
        """Test that delete-account requires authentication."""
        response = client.delete("/api/auth/delete-account")
        assert response.status_code == 401

    def test_delete_account_success_returns_200(self, client, test_user, auth_headers):
        """Test successful account deletion returns 200."""
        response = client.delete(
            "/api/auth/delete-account",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "erfolgreich gelöscht" in data["message"]

    def test_delete_account_removes_user_from_database(self, app, client, test_user, auth_headers):
        """Test that user is actually removed from database."""
        # Get user ID before deletion
        user_id = test_user["id"]

        response = client.delete(
            "/api/auth/delete-account",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify user no longer exists in database
        with app.app_context():
            from models import User

            deleted_user = User.query.get(user_id)
            assert deleted_user is None

    def test_delete_account_invalidates_token(self, client, test_user, auth_headers):
        """Test that current token becomes invalid after user deletion."""
        # Delete account
        response = client.delete(
            "/api/auth/delete-account",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Try to use the same token - should be invalid (user not found)
        response = client.get(
            "/api/auth/me",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_account_removes_related_data(self, app, client, test_user, auth_headers):
        """Test that user's related data is also deleted via cascade."""
        # Create some related data first
        with app.app_context():
            from models import APIKey, Document, User, db

            user = User.query.get(test_user["id"])

            # Create an API key
            api_key = APIKey(user_id=user.id, key_hash="test_hash", key_prefix="test_prefix", name="Test Key")
            db.session.add(api_key)

            # Create a document
            document = Document(
                user_id=user.id, original_filename="test.pdf", file_path="/test/path", doc_type="cv_pdf"
            )
            db.session.add(document)
            db.session.commit()

            api_key_id = api_key.id
            document_id = document.id

        # Delete account
        response = client.delete(
            "/api/auth/delete-account",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify related data is also deleted
        with app.app_context():
            from models import APIKey, Document

            # API key should be gone
            deleted_api_key = APIKey.query.get(api_key_id)
            assert deleted_api_key is None

            # Document should be gone
            deleted_document = Document.query.get(document_id)
            assert deleted_document is None

    def test_delete_account_nonexistent_user_returns_404(self, app, client):
        """Test that deleting account for nonexistent user returns 404."""
        # Create a JWT for a nonexistent user
        from flask_jwt_extended import create_access_token

        with app.app_context():
            # Use a user ID that doesn't exist
            fake_token = create_access_token(identity="99999")

        headers = {"Authorization": f"Bearer {fake_token}"}
        response = client.delete(
            "/api/auth/delete-account",
            headers=headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "Benutzer nicht gefunden" in data["error"]

    def test_delete_account_handles_database_errors_gracefully(self, app, client, test_user, auth_headers, monkeypatch):
        """Test that database errors are handled gracefully during deletion."""

        # Mock db.session.commit to raise an exception
        def mock_commit():
            raise Exception("Database error")

        with app.app_context():
            from models import db

            monkeypatch.setattr(db.session, "commit", mock_commit)

            response = client.delete(
                "/api/auth/delete-account",
                headers=auth_headers,
            )

            assert response.status_code == 500
            data = response.get_json()
            assert "Fehler beim Löschen" in data["error"]

        # Verify user still exists after failed deletion
        with app.app_context():
            from models import User

            user = User.query.get(test_user["id"])
            assert user is not None

    def test_delete_account_logs_deletion_for_gdpr_compliance(self, app, client, test_user, auth_headers, capfd):
        """Test that account deletion is logged for GDPR compliance."""
        response = client.delete(
            "/api/auth/delete-account",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Check that GDPR log entry was created
        captured = capfd.readouterr()
        assert "[GDPR]" in captured.out
        assert test_user["email"] in captured.out
        assert "Account deleted" in captured.out
