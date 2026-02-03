"""
Password Reset Service
Handles token generation and verification for password reset functionality.
"""

import secrets
from datetime import datetime, timedelta

from models import User, db


class PasswordResetService:
    """Service for password reset token management"""

    # Token expires after 1 hour (more restrictive than email verification)
    TOKEN_EXPIRY_HOURS = 1

    @staticmethod
    def generate_token() -> str:
        """
        Generate a secure reset token using secrets.token_urlsafe.

        Returns:
            A URL-safe token string (32 bytes = 43 characters)
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_reset_token(user: User) -> str:
        """
        Create and store a new password reset token for a user.

        Args:
            user: User object to create token for

        Returns:
            The generated token string
        """
        token = PasswordResetService.generate_token()
        user.password_reset_token = token
        user.password_reset_sent_at = datetime.utcnow()
        db.session.commit()
        return token

    @staticmethod
    def is_token_expired(user: User) -> bool:
        """
        Check if the user's reset token has expired.

        Args:
            user: User object to check

        Returns:
            True if token is expired or doesn't exist, False otherwise
        """
        if not user.password_reset_sent_at:
            return True

        expiry_time = user.password_reset_sent_at + timedelta(hours=PasswordResetService.TOKEN_EXPIRY_HOURS)
        return datetime.utcnow() > expiry_time

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify a reset token is valid (not expired, exists).

        Args:
            token: The reset token to check

        Returns:
            dict with 'success' boolean and 'message' or 'user' data
        """
        if not token:
            return {"success": False, "message": "Token ist erforderlich"}

        user = User.query.filter_by(password_reset_token=token).first()

        if not user:
            return {"success": False, "message": "Ungültiger oder abgelaufener Reset-Token"}

        if PasswordResetService.is_token_expired(user):
            return {"success": False, "message": "Reset-Token ist abgelaufen"}

        return {"success": True, "user": user}

    @staticmethod
    def reset_password(token: str, new_password: str) -> dict:
        """
        Reset user's password using the provided token.

        Args:
            token: The reset token
            new_password: The new password (should be validated before calling)

        Returns:
            dict with 'success' boolean and 'message'
        """
        # Verify token first
        result = PasswordResetService.verify_token(token)

        if not result["success"]:
            return result

        user = result["user"]

        # Set new password and clear reset token
        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        db.session.commit()

        return {"success": True, "message": "Passwort erfolgreich zurückgesetzt"}

    @staticmethod
    def get_token_expiry_time(user: User) -> datetime | None:
        """
        Get the expiry time for a user's reset token.

        Args:
            user: User object

        Returns:
            datetime when token expires, or None if no token exists
        """
        if not user.password_reset_sent_at:
            return None

        return user.password_reset_sent_at + timedelta(hours=PasswordResetService.TOKEN_EXPIRY_HOURS)

    @staticmethod
    def clear_reset_token(user: User) -> None:
        """
        Clear the reset token for a user (e.g., after successful login).

        Args:
            user: User object
        """
        user.password_reset_token = None
        user.password_reset_sent_at = None
        db.session.commit()
