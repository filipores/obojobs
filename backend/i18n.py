"""
Internationalization (i18n) module for backend translations.

Provides a t() function that returns translated messages based on
the current request's locale (set by the locale middleware).
"""

from middleware.locale import get_locale

# Translation dictionaries keyed by locale
# Format: { locale: { key: translation } }
TRANSLATIONS = {
    "de": {
        # Auth errors
        "Email and password are required": "E-Mail und Passwort sind erforderlich",
        "Registration successful": "Registrierung erfolgreich",
        "User not found": "Benutzer nicht gefunden",
        "Email is already verified": "E-Mail ist bereits bestätigt",
        "Too many verification requests. Please try again later.": "Zu viele Bestätigungsanfragen. Bitte später erneut versuchen.",
        "Verification email sent": "Bestätigungs-E-Mail gesendet",
        "Token is required": "Token ist erforderlich",
        "Email successfully verified": "E-Mail erfolgreich bestätigt",
        "If an account with this email exists, a reset link has been sent.": "Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet.",
        "New password is required": "Neues Passwort ist erforderlich",
        "Password does not meet requirements": "Passwort erfüllt nicht die Anforderungen",
        "Password successfully reset": "Passwort erfolgreich zurückgesetzt",
        "Current password is required": "Aktuelles Passwort ist erforderlich",
        "Successfully logged out": "Erfolgreich abgemeldet",
        "Name cannot exceed 255 characters": "Name darf maximal 255 Zeichen haben",
        "Display name cannot exceed 100 characters": "Anzeigename darf maximal 100 Zeichen haben",
        "Profile successfully updated": "Profil erfolgreich aktualisiert",
        "Your account and all associated data have been successfully deleted.": "Ihr Konto und alle zugehörigen Daten wurden erfolgreich gelöscht.",
        "Error deleting account. Please contact support.": "Fehler beim Löschen des Kontos. Bitte kontaktieren Sie den Support.",
        "Token has been revoked": "Token wurde widerrufen",
        "Invalid token": "Ungültiger Token",
        "Token has expired": "Token ist abgelaufen",
        "Token missing": "Token fehlt",
    },
    "en": {
        # English is the base language - keys map to themselves
        # Only include translations if the key differs from the English text
    },
}


def t(key: str, **kwargs) -> str:
    """
    Translate a message key to the current locale.

    Args:
        key: The message key (typically English text)
        **kwargs: Optional format arguments for string interpolation

    Returns:
        The translated message, or the key itself if no translation found
    """
    locale = get_locale()

    # Get translation for current locale
    translations = TRANSLATIONS.get(locale, {})
    translated = translations.get(key, key)

    # Apply string formatting if kwargs provided
    if kwargs:
        try:
            translated = translated.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting fails, return the translated string without formatting
            pass

    return translated
