import json
import os

_translations = {}
_current_locale = 'en'
_fallback_locale = 'en'

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')


def load_translations():
    """Load all translation files from locales directory."""
    global _translations
    _translations = {}

    for filename in os.listdir(LOCALES_DIR):
        if filename.endswith('.json'):
            locale = filename[:-5]
            filepath = os.path.join(LOCALES_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                _translations[locale] = json.load(f)


def set_locale(locale):
    """Set the current locale."""
    global _current_locale
    if locale in _translations:
        _current_locale = locale
    else:
        _current_locale = _fallback_locale


def get_locale():
    """Get the current locale."""
    return _current_locale


def t(key, locale=None, **kwargs):
    """
    Translate a key to the current or specified locale.

    Args:
        key: Dot-notation key (e.g., 'auth.login')
        locale: Optional locale override
        **kwargs: Format string arguments

    Returns:
        Translated string or key if not found
    """
    locale = locale or _current_locale
    translations = _translations.get(locale, _translations.get(_fallback_locale, {}))

    keys = key.split('.')
    value = translations

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return key

    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value

    return value if isinstance(value, str) else key


def get_available_locales():
    """Return list of available locales."""
    return list(_translations.keys())


# Load translations on module import
if os.path.exists(LOCALES_DIR):
    load_translations()
