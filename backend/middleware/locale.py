"""
Locale middleware for setting the request locale based on headers.

Parses the Accept-Language header to determine the user's preferred locale.
"""

from flask import Flask, request

from i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, set_locale


def parse_accept_language(header: str | None) -> str:
    """
    Parse the Accept-Language header and return the best matching locale.

    Args:
        header: The Accept-Language header value (e.g., "de-DE,de;q=0.9,en;q=0.8")

    Returns:
        The best matching supported locale code
    """
    if not header:
        return DEFAULT_LOCALE

    # Parse language preferences with quality values
    languages = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue

        # Check for quality value
        if ";q=" in part:
            lang, q = part.split(";q=", 1)
            try:
                quality = float(q)
            except ValueError:
                quality = 1.0
        else:
            lang = part
            quality = 1.0

        # Extract base language code (e.g., "de" from "de-DE")
        lang = lang.strip().split("-")[0].lower()
        languages.append((lang, quality))

    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)

    # Find first supported language
    for lang, _quality in languages:
        if lang in SUPPORTED_LOCALES:
            return lang

    return DEFAULT_LOCALE


def init_locale_middleware(app: Flask) -> None:
    """
    Initialize locale middleware with before_request hook.

    Args:
        app: The Flask application instance
    """

    @app.before_request
    def set_request_locale():
        """Set the locale for each request based on Accept-Language header."""
        accept_language = request.headers.get("Accept-Language")
        locale = parse_accept_language(accept_language)
        set_locale(locale)
