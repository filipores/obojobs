"""
Tests for email verification service.
"""

from datetime import datetime, timedelta

from models import User, db
from services.email_verification_service import EmailVerificationService


class TestEmailVerificationService:
    """Tests for EmailVerificationService"""

    def test_generate_token_returns_urlsafe_string(self):
        """Test that generate_token returns a URL-safe token."""
        token = EmailVerificationService.generate_token()

        assert token is not None
        assert isinstance(token, str)
        # 32 bytes in base64url = 43 chars
        assert len(token) == 43

    def test_generate_token_returns_unique_tokens(self):
        """Test that generate_token returns unique tokens each time."""
        token1 = EmailVerificationService.generate_token()
        token2 = EmailVerificationService.generate_token()

        assert token1 != token2

    def test_create_verification_token_stores_token(self, app):
        """Test that create_verification_token stores token on user."""
        with app.app_context():
            user = User(
                email="verify@example.com",
                full_name="Verify User",
            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            token = EmailVerificationService.create_verification_token(user)

            # Refetch user from DB
            user = User.query.filter_by(email="verify@example.com").first()

            assert user.email_verification_token == token
            assert user.email_verification_sent_at is not None
            assert isinstance(user.email_verification_sent_at, datetime)

    def test_is_token_expired_returns_false_for_fresh_token(self, app):
        """Test that fresh token is not expired."""
        with app.app_context():
            user = User(
                email="fresh@example.com",
                full_name="Fresh User",
            )
            user.set_password("TestPass123")
            user.email_verification_sent_at = datetime.utcnow()
            db.session.add(user)
            db.session.commit()

            assert EmailVerificationService.is_token_expired(user) is False

    def test_is_token_expired_returns_true_for_expired_token(self, app):
        """Test that token older than 24 hours is expired."""
        with app.app_context():
            user = User(
                email="expired@example.com",
                full_name="Expired User",
            )
            user.set_password("TestPass123")
            # Set sent_at to 25 hours ago
            user.email_verification_sent_at = datetime.utcnow() - timedelta(hours=25)
            db.session.add(user)
            db.session.commit()

            assert EmailVerificationService.is_token_expired(user) is True

    def test_is_token_expired_returns_true_when_no_sent_at(self, app):
        """Test that token without sent_at is considered expired."""
        with app.app_context():
            user = User(
                email="nosent@example.com",
                full_name="No Sent User",
            )
            user.set_password("TestPass123")
            user.email_verification_sent_at = None
            db.session.add(user)
            db.session.commit()

            assert EmailVerificationService.is_token_expired(user) is True

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

            token = EmailVerificationService.create_verification_token(user)
            result = EmailVerificationService.verify_token(token)

            assert result["success"] is True
            assert "user" in result

            # Refetch user to verify state
            user = User.query.filter_by(email="valid@example.com").first()
            assert user.email_verified is True
            assert user.email_verification_token is None
            assert user.email_verification_sent_at is None

    def test_verify_token_fails_with_invalid_token(self, app):
        """Test that verify_token fails with invalid token."""
        with app.app_context():
            result = EmailVerificationService.verify_token("invalid-token-123")

            assert result["success"] is False
            assert "Ungültiger Bestätigungstoken" in result["message"]

    def test_verify_token_fails_with_empty_token(self, app):
        """Test that verify_token fails with empty token."""
        with app.app_context():
            result = EmailVerificationService.verify_token("")

            assert result["success"] is False
            assert "Token ist erforderlich" in result["message"]

    def test_verify_token_fails_with_none_token(self, app):
        """Test that verify_token fails with None token."""
        with app.app_context():
            result = EmailVerificationService.verify_token(None)

            assert result["success"] is False
            assert "Token ist erforderlich" in result["message"]

    def test_verify_token_fails_when_already_verified(self, app):
        """Test that verify_token fails when email is already verified."""
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

            result = EmailVerificationService.verify_token("some-token")

            assert result["success"] is False
            assert "bereits bestätigt" in result["message"]

    def test_verify_token_fails_when_token_expired(self, app):
        """Test that verify_token fails when token is expired."""
        with app.app_context():
            user = User(
                email="expiredtoken@example.com",
                full_name="Expired Token User",
            )
            user.set_password("TestPass123")
            user.email_verification_token = "expired-token-123"
            user.email_verification_sent_at = datetime.utcnow() - timedelta(hours=25)
            db.session.add(user)
            db.session.commit()

            result = EmailVerificationService.verify_token("expired-token-123")

            assert result["success"] is False
            assert "abgelaufen" in result["message"]

    def test_get_token_expiry_time_returns_correct_time(self, app):
        """Test that get_token_expiry_time returns correct expiry."""
        with app.app_context():
            user = User(
                email="expirytime@example.com",
                full_name="Expiry Time User",
            )
            user.set_password("TestPass123")
            sent_at = datetime.utcnow()
            user.email_verification_sent_at = sent_at
            db.session.add(user)
            db.session.commit()

            expiry = EmailVerificationService.get_token_expiry_time(user)

            expected_expiry = sent_at + timedelta(hours=24)
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
            user.email_verification_sent_at = None
            db.session.add(user)
            db.session.commit()

            expiry = EmailVerificationService.get_token_expiry_time(user)

            assert expiry is None


class TestUserModelEmailVerification:
    """Tests for email verification fields on User model"""

    def test_new_user_has_email_verified_false(self, app):
        """Test that new users have email_verified set to False by default."""
        with app.app_context():
            user = User(
                email="newuser@example.com",
                full_name="New User",
            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            assert user.email_verified is False

    def test_user_to_dict_includes_email_verified(self, app):
        """Test that user.to_dict() includes email_verified field."""
        with app.app_context():
            user = User(
                email="dicttest@example.com",
                full_name="Dict Test",
            )
            user.set_password("TestPass123")
            db.session.add(user)
            db.session.commit()

            user_dict = user.to_dict()

            assert "email_verified" in user_dict
            assert user_dict["email_verified"] is False

    def test_user_to_dict_email_verified_true_after_verification(self, app):
        """Test that email_verified is True in to_dict after verification."""
        with app.app_context():
            user = User(
                email="verifieddict@example.com",
                full_name="Verified Dict",
            )
            user.set_password("TestPass123")
            user.email_verified = True
            db.session.add(user)
            db.session.commit()

            user_dict = user.to_dict()

            assert user_dict["email_verified"] is True
