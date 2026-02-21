import logging
from datetime import datetime, timedelta

from flask_jwt_extended import create_access_token, create_refresh_token

from models import TokenBlacklist, User, db
from services.password_validator import PasswordValidator

logger = logging.getLogger(__name__)

# Lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Valid working time preference values
VALID_WORKING_TIMES = ("vz", "tz", "ho")


class AuthService:
    """Authentication service for user management"""

    @staticmethod
    def register_user(email: str, password: str, full_name: str | None = None) -> User:
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
    def login_user(email: str, password: str) -> dict[str, str | dict]:
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
                raise ValueError(f"Konto vorübergehend gesperrt. Versuche es in {remaining_minutes} Minuten erneut.")
            # Lock expired, reset lockout
            user.locked_until = None
            user.failed_login_attempts = 0
            db.session.commit()

        if not user or not user.check_password(password):
            # Increment failed attempts if user exists
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
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

        # Create tokens (JWT spec requires string subject)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}

    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        """Get user by ID"""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_email(email: str) -> User | None:
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

    @staticmethod
    def check_email_verification_for_login(email: str) -> dict | None:
        """Check if user needs email verification before login.

        Returns:
            dict with error info if login should be blocked, None if login is allowed.
        """
        user = User.query.filter_by(email=email).first()
        if user and not user.google_id:
            return {
                "error": "Bitte bestätige zuerst deine E-Mail-Adresse.",
                "email_not_verified": True,
            }
        return None

    @staticmethod
    def google_auth_login(
        google_id: str, email: str, email_verified: bool, full_name: str | None, registration_enabled: bool
    ) -> dict:
        """Handle Google OAuth login/registration.

        Args:
            google_id: Google user ID
            email: User email (lowercased)
            email_verified: Whether Google says the email is verified
            full_name: User's full name from Google
            registration_enabled: Whether new registrations are allowed

        Returns:
            dict with access_token, refresh_token, and user data

        Raises:
            ValueError: If user is inactive or registration is disabled
        """
        # Check if user exists by Google ID
        user = User.query.filter_by(google_id=google_id).first()

        if not user:
            # Check if user exists by email
            user = User.query.filter_by(email=email).first()

            if user:
                # Link Google account to existing user
                user.google_id = google_id
                if email_verified and not user.email_verified:
                    user.email_verified = True
                db.session.commit()
            else:
                if not registration_enabled:
                    raise ValueError("Registrierung ist derzeit deaktiviert. Bitte kontaktiere den Administrator.")
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    full_name=full_name,
                    email_verified=email_verified,
                )
                db.session.add(user)
                db.session.commit()

        if not user.is_active:
            raise ValueError("Konto ist deaktiviert")

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}

    @staticmethod
    def logout_user(jti: str, token_type: str, user_id: int, expires_at: datetime) -> None:
        """Add token to blacklist for logout."""
        TokenBlacklist.add_token(jti=jti, token_type=token_type, user_id=user_id, expires_at=expires_at)

    @staticmethod
    def update_language(user_id: int, language: str) -> dict:
        """Update user language preference.

        Args:
            user_id: User ID
            language: Language code ('de' or 'en')

        Returns:
            dict with message and language

        Raises:
            ValueError: If user not found or invalid language
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Benutzer nicht gefunden")

        if language not in ["de", "en"]:
            raise ValueError("Ungültige Sprache. Muss 'de' oder 'en' sein.")

        user.language = language
        db.session.commit()

        return {"message": "Spracheinstellung aktualisiert", "language": user.language}

    @staticmethod
    def update_profile(user_id: int, data: dict) -> dict:
        """Update user profile fields.

        Args:
            user_id: User ID
            data: dict with profile fields to update

        Returns:
            dict with message and user data

        Raises:
            ValueError: If user not found or validation fails
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Benutzer nicht gefunden")

        profile_fields = [
            ("full_name", 255, "Name"),
            ("display_name", 100, "Anzeigename"),
            ("phone", 50, "Telefonnummer"),
            ("address", 255, "Adresse"),
            ("city", 100, "Stadt"),
            ("postal_code", 20, "PLZ"),
            ("website", 255, "Website"),
            ("preferred_location", 255, "Bevorzugter Standort"),
            ("preferred_working_time", 10, "Bevorzugte Arbeitszeit"),
        ]

        for field, max_length, label in profile_fields:
            if field not in data:
                continue
            value = data[field]
            if value and len(value) > max_length:
                raise ValueError(f"{label} darf maximal {max_length} Zeichen haben")
            setattr(user, field, value.strip() if value else None)

        if user.preferred_working_time and user.preferred_working_time not in VALID_WORKING_TIMES:
            raise ValueError("Bevorzugte Arbeitszeit muss 'vz', 'tz' oder 'ho' sein")

        db.session.commit()

        return {"message": "Profil erfolgreich aktualisiert", "user": user.to_dict()}

    @staticmethod
    def delete_account(user_id: int) -> dict:
        """Delete user account and all associated data (GDPR right to be forgotten).

        Args:
            user_id: User ID

        Returns:
            dict with success message

        Raises:
            ValueError: If user not found
            RuntimeError: If deletion fails
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Benutzer nicht gefunden")

        try:
            # Cancel Stripe subscription if exists
            if user.stripe_customer_id:
                try:
                    pass  # Stripe cancellation placeholder
                except Exception as e:
                    logger.warning("Could not cancel Stripe subscription for user %s: %s", user.id, e)

            user_email = user.email

            # Delete all TokenBlacklist entries for this user to avoid foreign key issues
            TokenBlacklist.query.filter_by(user_id=user_id).delete()

            # Delete user (cascade will handle all other related data)
            db.session.delete(user)
            db.session.commit()

            logger.info("[GDPR] Account deleted for user %s (ID: %s)", user_email, user_id)

            return {"message": "Dein Konto und alle zugehörigen Daten wurden erfolgreich gelöscht."}
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting account for user %s: %s", user_id, e)
            raise RuntimeError("Fehler beim Löschen des Kontos. Bitte kontaktiere den Support.") from e
