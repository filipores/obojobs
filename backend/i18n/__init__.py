"""
Lightweight i18n module for Flask backend.

Provides translation functionality using JSON locale files.
Supports German (default) and English.
"""

import json
import os
from functools import lru_cache
from typing import Any

from flask import g, request

# Supported locales
SUPPORTED_LOCALES = ["de", "en"]
DEFAULT_LOCALE = "de"

# Path to locale files
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")


@lru_cache(maxsize=2)
def load_translations(locale: str) -> dict[str, Any]:
    """
    Load translations for a given locale.

    Args:
        locale: The locale code (de, en)

    Returns:
        Dictionary of translations
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    locale_file = os.path.join(LOCALES_DIR, f"{locale}.json")

    try:
        with open(locale_file, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data
    except FileNotFoundError:
        # Fallback to default locale
        if locale != DEFAULT_LOCALE:
            return load_translations(DEFAULT_LOCALE)
        return {}
    except json.JSONDecodeError:
        return {}


def get_locale() -> str:
    """
    Get the current locale from the request context.

    Priority:
    1. g.locale (set by middleware from user preference)
    2. Accept-Language header
    3. Default locale (de)

    Returns:
        Locale code string
    """
    # Check if locale was set by middleware (from user preference)
    if hasattr(g, "locale") and g.locale in SUPPORTED_LOCALES:
        return str(g.locale)

    # Try Accept-Language header
    if request:
        accept_languages = request.accept_languages
        for lang in accept_languages:
            lang_code = lang[0].split("-")[0].lower()
            if lang_code in SUPPORTED_LOCALES:
                return lang_code

    return DEFAULT_LOCALE


def t(key: str, **kwargs: Any) -> str:
    """
    Translate a key to the current locale.

    Args:
        key: Dot-notation key (e.g., 'auth.loginRequired')
        **kwargs: Interpolation values (e.g., minutes=5)

    Returns:
        Translated string or the key if not found
    """
    locale = get_locale()
    translations = load_translations(locale)

    # Navigate nested keys
    keys = key.split(".")
    value = translations
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Key not found, try fallback locale
            if locale != DEFAULT_LOCALE:
                fallback = load_translations(DEFAULT_LOCALE)
                value = fallback
                for k2 in keys:
                    if isinstance(value, dict) and k2 in value:
                        value = value[k2]
                    else:
                        return key  # Return key as fallback
                break
            else:
                return key  # Return key as fallback

    if not isinstance(value, str):
        return key

    # Interpolate variables (e.g., {minutes})
    if kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass  # Return string without interpolation if key missing

    return value


def set_locale(locale: str) -> None:
    """
    Set the locale for the current request context.

    Args:
        locale: Locale code (de, en)
    """
    if locale in SUPPORTED_LOCALES:
        g.locale = locale


def clear_translation_cache() -> None:
    """Clear the translation cache (useful for development/testing)."""
    load_translations.cache_clear()
