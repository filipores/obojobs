from datetime import datetime, timedelta

from flask_jwt_extended import create_access_token, create_refresh_token

from models import User, db
from services.password_validator import PasswordValidator

# Lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class AuthService:
    """Authentication service for user management"""

    @staticmethod
    def register_user(email, password, full_name=None):
        """
        Register a new user.

        Args:
            email: User email
            password: User password
            full_name: Optional full name

        Returns:
            User object

        Raises:
            ValueError: If user already exists
        """
        # Validate password strength
        password_check = PasswordValidator.validate(password)
        if not password_check["valid"]:
            raise ValueError(password_check["errors"][0])

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError("Ein Benutzer mit dieser E-Mail existiert bereits")

        # Create new user
        user = User(email=email, full_name=full_name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def login_user(email, password):
        """
        Login user and return tokens.

        Args:
            email: User email
            password: User password

        Returns:
            dict with access_token, refresh_token, and user data

        Raises:
            ValueError: If credentials are invalid or account is locked
        """
        user = User.query.filter_by(email=email).first()

        # Check if account is locked
        if user and user.locked_until:
            if datetime.utcnow() < user.locked_until:
                remaining = user.locked_until - datetime.utcnow()
                remaining_minutes = max(1, int(remaining.total_seconds() / 60))
                raise ValueError(
                    f"Konto vorübergehend gesperrt. Versuche es in {remaining_minutes} Minuten erneut."
                )
            else:
                # Lock expired, reset lockout
                user.locked_until = None
                user.failed_login_attempts = 0
                db.session.commit()

        if not user or not user.check_password(password):
            # Increment failed attempts if user exists
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.utcnow() + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )
                    db.session.commit()
                    raise ValueError(
                        f"Konto wegen zu vieler fehlgeschlagener Anmeldeversuche gesperrt. "
                        f"Versuche es in {LOCKOUT_DURATION_MINUTES} Minuten erneut."
                    )
                db.session.commit()

            raise ValueError("Ungültige E-Mail oder Passwort")

        if not user.is_active:
            raise ValueError("Konto ist deaktiviert")

        # Successful login - reset failed attempts
        if user.failed_login_attempts and user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()

        # Create tokens (identity must be a string)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_email(email: str):
        """Get user by email"""
        return User.query.filter_by(email=email.lower()).first()

    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> dict:
        """
        Change password for authenticated user.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            dict with success status and message

        Raises:
            ValueError: If current password is wrong or new password is invalid
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Benutzer nicht gefunden")

        # Verify current password
        if not user.check_password(current_password):
            raise ValueError("Aktuelles Passwort ist falsch")

        # Validate new password strength
        password_check = PasswordValidator.validate(new_password)
        if not password_check["valid"]:
            raise ValueError(password_check["errors"][0])

        # Check that new password is different from current
        if user.check_password(new_password):
            raise ValueError("Neues Passwort muss sich vom aktuellen unterscheiden")

        # Set new password
        user.set_password(new_password)
        db.session.commit()

        return {"success": True, "message": "Passwort erfolgreich geändert"}
