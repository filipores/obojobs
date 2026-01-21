"""
Internationalization (i18n) module for backend translations.

Provides a t() function that translates keys based on the current request locale.
"""

import json
import os
from typing import Any

from flask import g, has_request_context

# Default locale when none is specified
DEFAULT_LOCALE = "de"

# Supported locales
SUPPORTED_LOCALES = ["de", "en"]

# Cache for loaded translations
_translations: dict[str, dict] = {}


def _load_translations() -> None:
    """Load all translation files into memory."""
    global _translations
    if _translations:
        return

    locales_dir = os.path.join(os.path.dirname(__file__), "locales")

    for locale in SUPPORTED_LOCALES:
        locale_file = os.path.join(locales_dir, f"{locale}.json")
        if os.path.exists(locale_file):
            with open(locale_file, "r", encoding="utf-8") as f:
                _translations[locale] = json.load(f)


def get_locale() -> str:
    """
    Get the current locale from the request context.

    Returns:
        The current locale code (e.g., 'de', 'en')
    """
    if has_request_context():
        return getattr(g, "locale", DEFAULT_LOCALE)
    return DEFAULT_LOCALE


def set_locale(locale: str) -> None:
    """
    Set the locale for the current request context.

    Args:
        locale: The locale code to set
    """
    if locale in SUPPORTED_LOCALES:
        g.locale = locale
    else:
        g.locale = DEFAULT_LOCALE


def t(key: str, **params: Any) -> str:
    """
    Translate a key to the current locale.

    Args:
        key: Dot-notation key (e.g., 'auth.userNotFound')
        **params: Parameters to interpolate into the translation

    Returns:
        The translated string, or the key if not found
    """
    _load_translations()

    locale = get_locale()
    translations = _translations.get(locale, {})

    # Navigate through nested keys
    value = translations
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is None:
        # Fallback to default locale
        if locale != DEFAULT_LOCALE:
            translations = _translations.get(DEFAULT_LOCALE, {})
            value = translations
            for part in key.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

    if value is None:
        return key

    # Interpolate parameters
    if params and isinstance(value, str):
        try:
            value = value.format(**params)
        except KeyError:
            pass

    return value if isinstance(value, str) else key
