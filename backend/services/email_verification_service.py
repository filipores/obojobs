"""
Email Verification Service
Handles token generation and verification for email confirmation.
"""

import secrets
from datetime import datetime, timedelta

from models import User, db


class EmailVerificationService:
    """Service for email verification token management"""

    # Token expires after 24 hours
    TOKEN_EXPIRY_HOURS = 24

    @staticmethod
    def generate_token() -> str:
        """
        Generate a secure verification token using secrets.token_urlsafe.

        Returns:
            A URL-safe token string (32 bytes = 43 characters)
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_verification_token(user: User) -> str:
        """
        Create and store a new verification token for a user.

        Args:
            user: User object to create token for

        Returns:
            The generated token string
        """
        token = EmailVerificationService.generate_token()
        user.email_verification_token = token
        user.email_verification_sent_at = datetime.utcnow()
        db.session.commit()
        return token

    @staticmethod
    def is_token_expired(user: User) -> bool:
        """
        Check if the user's verification token has expired.

        Args:
            user: User object to check

        Returns:
            True if token is expired or doesn't exist, False otherwise
        """
        if not user.email_verification_sent_at:
            return True

        expiry_time = user.email_verification_sent_at + timedelta(hours=EmailVerificationService.TOKEN_EXPIRY_HOURS)
        return datetime.utcnow() > expiry_time

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify a token and mark the user's email as verified.

        Args:
            token: The verification token to check

        Returns:
            dict with 'success' boolean and 'message' or 'user' data
        """
        if not token:
            return {"success": False, "message": "Token ist erforderlich"}

        user = User.query.filter_by(email_verification_token=token).first()

        if not user:
            return {"success": False, "message": "Ungültiger Bestätigungstoken"}

        if user.email_verified:
            return {"success": False, "message": "E-Mail ist bereits bestätigt"}

        if EmailVerificationService.is_token_expired(user):
            return {"success": False, "message": "Bestätigungstoken ist abgelaufen"}

        # Mark email as verified and clear token
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None
        db.session.commit()

        return {"success": True, "user": user}

    @staticmethod
    def get_token_expiry_time(user: User) -> datetime | None:
        """
        Get the expiry time for a user's verification token.

        Args:
            user: User object

        Returns:
            datetime when token expires, or None if no token exists
        """
        if not user.email_verification_sent_at:
            return None

        return user.email_verification_sent_at + timedelta(hours=EmailVerificationService.TOKEN_EXPIRY_HOURS)
