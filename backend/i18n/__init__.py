"""
Internationalization module for the backend.
Provides translation support with locale detection from request headers.
"""

import json
import os
from functools import lru_cache
from threading import local

# Thread-local storage for current locale
_thread_locals = local()

# Default locale
DEFAULT_LOCALE = "de"
SUPPORTED_LOCALES = ["de", "en"]


@lru_cache(maxsize=None)
def _load_locale(locale: str) -> dict:
    """Load locale translations from JSON file."""
    locale_dir = os.path.join(os.path.dirname(__file__), "locales")
    locale_file = os.path.join(locale_dir, f"{locale}.json")

    if os.path.exists(locale_file):
        with open(locale_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_locale() -> str:
    """Get the current locale from thread-local storage."""
    return getattr(_thread_locals, "locale", DEFAULT_LOCALE)


def set_locale(locale: str) -> None:
    """Set the current locale in thread-local storage."""
    if locale in SUPPORTED_LOCALES:
        _thread_locals.locale = locale
    else:
        _thread_locals.locale = DEFAULT_LOCALE


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current locale.

    Args:
        key: Dot-separated translation key (e.g., 'auth.userNotFound')
        **kwargs: Parameters for string interpolation

    Returns:
        Translated string or the key if not found
    """
    locale = get_locale()
    translations = _load_locale(locale)

    # Navigate through nested keys
    parts = key.split(".")
    value = translations
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            # Fallback to default locale if key not found
            if locale != DEFAULT_LOCALE:
                return t(key, **kwargs) if locale == DEFAULT_LOCALE else _t_with_locale(DEFAULT_LOCALE, key, **kwargs)
            return key

    # Interpolate parameters
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass

    return value if isinstance(value, str) else key


def _t_with_locale(locale: str, key: str, **kwargs) -> str:
    """Translate with a specific locale."""
    translations = _load_locale(locale)

    parts = key.split(".")
    value = translations
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return key

    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass

    return value if isinstance(value, str) else key


def parse_accept_language(header: str) -> str:
    """
    Parse Accept-Language header and return the best matching locale.

    Args:
        header: Accept-Language header value

    Returns:
        Best matching locale code
    """
    if not header:
        return DEFAULT_LOCALE

    # Parse language preferences with quality values
    languages = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue

        if ";q=" in part:
            lang, q = part.split(";q=")
            try:
                quality = float(q)
            except ValueError:
                quality = 0.0
        else:
            lang = part
            quality = 1.0

        # Extract primary language code
        lang = lang.strip().split("-")[0].lower()
        languages.append((lang, quality))

    # Sort by quality descending
    languages.sort(key=lambda x: x[1], reverse=True)

    # Find first supported locale
    for lang, _ in languages:
        if lang in SUPPORTED_LOCALES:
            return lang

    return DEFAULT_LOCALE
