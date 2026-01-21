"""
Locale Middleware

Detects and sets the user's preferred locale from request headers.
The locale is stored in Flask's g object for access throughout the request.
"""

from flask import g, request

# Supported locales with German as default
SUPPORTED_LOCALES = ["de", "en"]
DEFAULT_LOCALE = "de"


def get_locale_from_header():
    """
    Parse Accept-Language header and return the best matching locale.

    Returns:
        str: The best matching locale code (e.g., 'de', 'en')
    """
    accept_language = request.headers.get("Accept-Language", "")

    if not accept_language:
        return DEFAULT_LOCALE

    # Parse Accept-Language header (e.g., "de-DE,de;q=0.9,en;q=0.8")
    languages = []
    for lang_entry in accept_language.split(","):
        parts = lang_entry.strip().split(";")
        lang = parts[0].strip().lower()

        # Extract quality value (default to 1.0)
        quality = 1.0
        if len(parts) > 1:
            for part in parts[1:]:
                if part.strip().startswith("q="):
                    try:
                        quality = float(part.strip()[2:])
                    except ValueError:
                        quality = 0.0

        # Extract base language (e.g., 'de' from 'de-DE')
        base_lang = lang.split("-")[0]
        languages.append((base_lang, quality))

    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)

    # Find the first supported locale
    for lang, _ in languages:
        if lang in SUPPORTED_LOCALES:
            return lang

    return DEFAULT_LOCALE


def set_locale():
    """
    Set the locale for the current request in Flask's g object.
    Called before each request via before_request hook.
    """
    g.locale = get_locale_from_header()


def get_locale():
    """
    Get the current request's locale from Flask's g object.

    Returns:
        str: The current locale code, or DEFAULT_LOCALE if not set
    """
    return getattr(g, "locale", DEFAULT_LOCALE)


def init_locale_middleware(app):
    """
    Initialize locale middleware for Flask app.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def apply_locale():
        set_locale()
