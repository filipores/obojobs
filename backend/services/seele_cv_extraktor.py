"""Seele CV-Extraktor - Automatische Profil-Feld-Extraktion aus Lebenslauf."""

import json
import logging

from config import config as app_config
from models import SeeleProfile, db
from services.ai_client import AIClient
from services.seele_feld_metadata import AUTO_EXTRACT_KEYS
from services.seele_fragen import _ist_feld_leer
from services.seele_profile_builder import erstelle_leeres_profil

logger = logging.getLogger(__name__)


def auto_extrahiere_cv_felder(user_id, cv_text, profil_data, profile):
    """Extrahiere offensichtliche Fakten aus dem CV und fuelle leere Profil-Felder.

    Wird einmalig bei Session-Start aufgerufen. Fuellt nur leere Felder,
    ueberschreibt niemals bestehende Werte.

    Returns:
        tuple: (updated profil_data, updated profile model)
    """
    # Finde leere auto-extrahierbare Felder
    leere_felder = [k for k in AUTO_EXTRACT_KEYS if _ist_feld_leer(profil_data, k)]

    if not leere_felder:
        return profil_data, profile

    prompt = f"""Extrahiere die folgenden Informationen aus dem Lebenslauf.
Antworte als JSON-Objekt. Fuer jedes Feld, das du findest, gib den Wert an.
Fuer Felder die nicht im CV stehen, setze null.
Bei Listen-Feldern gib ein Array zurueck.

LEBENSLAUF:
{cv_text[:4000]}

GESUCHTE FELDER:
{chr(10).join(f'- {k}' for k in leere_felder)}

Antworte als JSON:
{{{', '.join(f'"{k}": ...' for k in leere_felder)}}}
"""

    try:
        client = AIClient(api_key=app_config.OPENROUTER_API_KEY)
        result = client._call_api_json_with_retry(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )

        if not isinstance(result, dict):
            return profil_data, profile

        # Ensure profile exists
        if not profile:
            profil_data = erstelle_leeres_profil()
            profile = SeeleProfile(
                user_id=user_id,
                profil_json=json.dumps(profil_data, ensure_ascii=False),
                version=1,
            )
            db.session.add(profile)

        updates = 0
        for key in leere_felder:
            val = result.get(key)
            if val is None or val == "" or val == []:
                continue

            section, field = key.split(".", 1)
            if section not in profil_data:
                profil_data[section] = {}
            profil_data[section][field] = val
            updates += 1

        if updates > 0:
            profile.set_profil(profil_data)
            profile.berechne_vollstaendigkeit()
            db.session.commit()
            logger.info("Auto-Extraktion: %d Felder aus CV extrahiert fuer User %s", updates, user_id)

        return profil_data, profile

    except Exception as e:
        logger.warning("CV Auto-Extraktion fehlgeschlagen: %s", e)
        return profil_data, profile
