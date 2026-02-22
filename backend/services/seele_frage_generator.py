"""Seele Frage Generator - AI-generated contextual questions for micro sessions."""

import logging

from config import config
from services.ai_client import AIClient

logger = logging.getLogger(__name__)


def generiere_micro_frage(profil, kontext=None, cv_text=None, zeugnis_text=None, skills=None):
    """Generate a single contextual question based on profile gaps and context.

    Used for micro sessions to fill specific profile gaps.
    Returns a frage dict compatible with the question format, or None on failure.
    """
    # Find profile gaps
    luecken = _finde_profil_luecken(profil)
    if not luecken:
        return None

    kontext_text = ""
    if kontext:
        if kontext.get("position"):
            kontext_text += f"Bewirbt sich auf: {kontext['position']}\n"
        if kontext.get("firma"):
            kontext_text += f"Bei: {kontext['firma']}\n"

    cv_info = ""
    if cv_text:
        cv_info += f"\nLEBENSLAUF:\n{cv_text[:2000]}\n"
    if zeugnis_text:
        cv_info += f"\nARBEITSZEUGNIS:\n{zeugnis_text[:1000]}\n"
    if skills:
        cv_info += f"\nSKILLS: {', '.join(s if isinstance(s, str) else s.skill_name for s in skills[:20])}\n"

    prompt = f"""Generiere EINE Frage fuer ein Bewerberprofil.

Offene Felder: {', '.join(luecken[:5])}
{kontext_text}
{cv_info}

Die Frage soll:
- Natuerlich und gespraechig klingen (Du-Form)
- Kurz sein (max 15 Woerter)
- Eines der offenen Felder abdecken
- Sich auf den konkreten Lebenslauf beziehen, falls vorhanden (Branche, Position, Skills erwaehnen)

Antworte als JSON:
{{"key": "section.field", "frage": "Fragetext?", "typ": "chips", "optionen": ["Option1", "Option2", "Option3"], "mehrfach": false}}

Moegliche Typen: chips, freitext, chips_freitext, slider
Bei slider: {{"key": "...", "frage": "...", "typ": "slider", "optionen": null, "mehrfach": false, "min_wert": 0, "max_wert": 100, "schritt": 1}}
"""

    try:
        client = AIClient(api_key=config.OPENROUTER_API_KEY)
        result = client._call_api_json_with_retry(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        # Validate required fields
        if not result.get("key") or not result.get("frage") or not result.get("typ"):
            logger.warning("AI micro frage ungueltig: %s", result)
            return None
        return result
    except Exception as e:
        logger.error("Micro-Frage Generierung fehlgeschlagen: %s", e)
        return None


def _finde_profil_luecken(profil):
    """Find empty fields in profile that could be asked about."""
    if not profil:
        return ["motivation.aktuelle_situation", "arbeitsstil.staerken", "arbeitsstil.teamrolle"]

    luecken = []
    for section_key, section_data in profil.items():
        if section_key == "meta":
            continue
        if not isinstance(section_data, dict):
            continue
        for field_key, field_val in section_data.items():
            if field_val is None or field_val == [] or field_val == {}:
                luecken.append(f"{section_key}.{field_key}")

    return luecken
