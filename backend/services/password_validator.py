"""
Password validation service for secure password requirements.
"""

import re


class PasswordValidator:
    """Validates password strength according to security requirements."""

    MIN_LENGTH = 8

    @classmethod
    def validate(cls, password: str) -> dict:
        """
        Validate password strength.

        Args:
            password: The password to validate

        Returns:
            dict with:
                - valid: bool indicating if password meets all requirements
                - errors: list of specific error messages for failed rules
                - checks: dict of individual rule results
        """
        checks = {
            "min_length": len(password) >= cls.MIN_LENGTH,
            "has_uppercase": bool(re.search(r"[A-Z]", password)),
            "has_lowercase": bool(re.search(r"[a-z]", password)),
            "has_number": bool(re.search(r"\d", password)),
        }

        errors = cls._get_error_messages(checks)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "checks": checks,
        }

    @classmethod
    def _get_error_messages(cls, checks: dict[str, bool]) -> list[str]:
        """Generate specific error messages for failed checks."""
        messages = []

        if not checks["min_length"]:
            messages.append(f"Passwort muss mindestens {cls.MIN_LENGTH} Zeichen haben")
        if not checks["has_uppercase"]:
            messages.append("Passwort muss mindestens einen Großbuchstaben enthalten")
        if not checks["has_lowercase"]:
            messages.append("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        if not checks["has_number"]:
            messages.append("Passwort muss mindestens eine Zahl enthalten")

        return messages

    @classmethod
    def get_requirements(cls) -> list[dict]:
        """
        Get list of password requirements for frontend display.

        Returns:
            List of requirement dictionaries with key and label
        """
        return [
            {"key": "min_length", "label": f"Mindestens {cls.MIN_LENGTH} Zeichen"},
            {"key": "has_uppercase", "label": "Mindestens ein Großbuchstabe (A-Z)"},
            {"key": "has_lowercase", "label": "Mindestens ein Kleinbuchstabe (a-z)"},
            {"key": "has_number", "label": "Mindestens eine Zahl (0-9)"},
        ]
