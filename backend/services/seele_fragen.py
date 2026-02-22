"""Seele Fragen - AI-generierte personalisierte Fragen basierend auf CV-Lücken."""

import logging

from config import config
from services.ai_client import AIClient
from services.seele_fallback_fragen import FALLBACK_FRAGEN
from services.seele_feld_metadata import ALLE_PROFIL_KEYS, FELD_METADATA

logger = logging.getLogger(__name__)


def _get_fallback_fragen(session_typ):
    """Get fallback questions, resolving old session types to 'profil'."""
    fragen = FALLBACK_FRAGEN.get(session_typ)
    if fragen is None:
        # Old session types resolve to profil fallback
        return list(FALLBACK_FRAGEN["profil"])
    return list(fragen)


def generiere_fragen(session_typ, cv_text=None, zeugnis_text=None, skills=None, profil=None, user=None):
    """Generiere personalisierte Fragen basierend auf CV-Lücken via AI.

    Die AI analysiert den CV und das aktuelle Profil, identifiziert Lücken,
    und generiert 3-5 gezielte Fragen zu den wichtigsten fehlenden Infos.

    Returns Liste von Frage-Dicts. Bei Fehler: Fallback auf statische Fragen.
    """
    if session_typ == "micro":
        return []

    fallback = _get_fallback_fragen(session_typ)

    # Fragbare Lücken ermitteln (nicht auto-extrahierbare leere Felder)
    luecken = _finde_fragbare_luecken(profil)

    # Ohne Lücken: alles ausgefüllt
    if not luecken:
        return []

    # Ohne CV-Text: Fallback-Fragen gefiltert auf Lücken
    if not cv_text:
        logger.info("Kein CV-Text vorhanden, nutze Fallback-Fragen gefiltert auf Luecken")
        return _fallback_fuer_luecken(luecken, fallback)

    # Bereits beantwortete Felder sammeln
    bereits_beantwortet = _sammle_beantwortete(profil)

    # Skills formatieren
    skills_text = ""
    if skills:
        skill_names = [s if isinstance(s, str) else s.skill_name for s in skills[:20]]
        skills_text = ", ".join(skill_names)

    # Lücken-Beschreibung fuer Prompt
    luecken_text = _beschreibe_luecken(luecken)

    prompt = f"""Du generierst personalisierte Fragen fuer ein Bewerberprofil.
Analysiere den Lebenslauf und entscheide, welche 3-5 Profil-Informationen
am wichtigsten sind fuer personalisierte Bewerbungsanschreiben.
Frage nur Dinge die NICHT aus dem CV ableitbar sind.

LEBENSLAUF:
{cv_text[:3000]}
"""

    if zeugnis_text:
        prompt += f"""
ARBEITSZEUGNIS:
{zeugnis_text[:1500]}
"""

    if skills_text:
        prompt += f"""
EXTRAHIERTE SKILLS:
{skills_text}
"""

    if bereits_beantwortet:
        prompt += f"""
BEREITS BEKANNT (nicht nochmal fragen):
{bereits_beantwortet}
"""

    prompt += f"""
OFFENE FELDER (Luecken im Profil - waehle die 3-5 wichtigsten):
{luecken_text}

Generiere 3-5 Fragen als JSON. Jede Frage muss:
- Sich auf den konkreten Lebenslauf beziehen (Branche, Position, Skills erwaehnen)
- Natuerlich und gespraechig klingen (Du-Form)
- 3-8 passende Chip-Optionen haben die zur Person passen
- Einen der offenen Feld-Keys verwenden

Frage-Typen:
- "chips": Einzelauswahl aus Optionen
- "chips_freitext": Mehrfachauswahl + Freitext (setze "mehrfach": true, "max_auswahl": 5)
- "slider": Zahlenwert (setze "optionen": null, "min_wert", "max_wert", "schritt")
- "freitext": Freie Texteingabe (setze "optionen": null)

Antworte als JSON-Objekt:
{{"fragen": [
  {{"key": "motivation.aktuelle_situation", "frage": "...", "typ": "chips", "optionen": ["A", "B", "C"], "mehrfach": false}},
  ...
]}}
"""

    try:
        client = AIClient(api_key=config.OPENROUTER_API_KEY)
        result = client._call_api_json_with_retry(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.7,
        )

        fragen = result.get("fragen", [])
        if not fragen or not isinstance(fragen, list):
            logger.warning("AI Fragen-Antwort ungueltig: %s", result)
            return _fallback_fuer_luecken(luecken, fallback)

        # Validiere jede Frage gegen alle Profil-Keys
        validierte = []
        for frage in fragen:
            if _validiere_frage(frage):
                validierte.append(frage)

        if not validierte:
            logger.warning("Keine validen AI-Fragen, nutze Fallback")
            return _fallback_fuer_luecken(luecken, fallback)

        logger.info("AI generierte %d personalisierte Fragen (Typ: %s)", len(validierte), session_typ)
        return validierte

    except Exception as e:
        logger.error("Fragen-Generierung fehlgeschlagen: %s, nutze Fallback", e)
        return _fallback_fuer_luecken(luecken, fallback)


def get_naechste_fragen(fragen, profil, max_fragen=4, beantwortete_keys=None):
    """Filtere bereits beantwortete Fragen aus einer Fragenliste.

    Args:
        fragen: Liste von Frage-Dicts (AI-generiert oder Fallback)
        profil: Aktuelles Profil-Dict (unused, kept for backwards compat)
        max_fragen: Maximale Anzahl zurueckzugebender Fragen
        beantwortete_keys: Set/Liste von frage_keys die in dieser Session
            bereits beantwortet/uebersprungen wurden
    """
    if not fragen:
        return []

    answered = set(beantwortete_keys or [])

    offene_fragen = []
    for frage in fragen:
        if frage["key"] in answered:
            continue

        offene_fragen.append(frage)
        if len(offene_fragen) >= max_fragen:
            break

    return offene_fragen


def vorausfuellen_aus_cv(frage_key, user):
    """Try to pre-fill a question answer from existing user/CV data."""
    prefills = {}

    if user:
        if frage_key == "persoenliche_daten.name" and user.full_name:
            prefills["vorausgefuellt"] = user.full_name
        if frage_key == "persoenliche_daten.standort" and hasattr(user, "city") and user.city:
            prefills["vorausgefuellt"] = user.city

    return prefills if prefills else None


def _finde_fragbare_luecken(profil):
    """Finde leere Profil-Felder die nicht auto-extrahierbar sind.

    Returns dict: {key: feld_metadata} fuer alle fragbaren Luecken.
    """
    luecken = {}

    for key, meta in FELD_METADATA.items():
        # Auto-extrahierbare Felder überspringen
        if meta["auto_extract"]:
            continue

        # Prüfen ob Feld leer ist
        if _ist_feld_leer(profil, key):
            luecken[key] = meta

    return luecken


def _ist_feld_leer(profil, key):
    """Prüfe ob ein Profil-Feld leer/unausgefüllt ist."""
    if not profil:
        return True

    if "." not in key:
        return True

    section, field = key.split(".", 1)
    section_data = profil.get(section, {})
    if not isinstance(section_data, dict):
        return True

    val = section_data.get(field)
    return val is None or val == [] or val == {}


def _beschreibe_luecken(luecken):
    """Formatiere Lücken-Dict als Text fuer AI-Prompt."""
    # Sortiere nach Prioritaet: hoch > mittel > niedrig
    prio_order = {"hoch": 0, "mittel": 1, "niedrig": 2}
    sorted_luecken = sorted(luecken.items(), key=lambda x: prio_order.get(x[1]["prioritaet"], 2))

    lines = []
    for key, meta in sorted_luecken:
        prio = meta["prioritaet"].upper()
        lines.append(f"- {key} [{prio}]: {meta['beschreibung']} (empfohlener Typ: {meta['typ_empfehlung']})")

    return "\n".join(lines)


def _fallback_fuer_luecken(luecken, fallback_liste):
    """Filtere Fallback-Fragen auf tatsaechliche Luecken, max 5 zurueck.

    Args:
        luecken: Dict von {key: metadata} der offenen Felder
        fallback_liste: Liste der Fallback-Frage-Dicts
    """
    if not luecken:
        return []

    luecken_keys = set(luecken.keys())
    gefiltert = [f for f in fallback_liste if f["key"] in luecken_keys]

    # Max 5 Fragen
    return gefiltert[:5]


def _validiere_frage(frage):
    """Pruefe ob eine AI-generierte Frage das richtige Format hat."""
    if not isinstance(frage, dict):
        return False
    if not frage.get("key") or not frage.get("frage") or not frage.get("typ"):
        return False
    if "." not in frage["key"]:
        return False
    if frage["key"] not in ALLE_PROFIL_KEYS:
        logger.warning("AI generierte ungueltigen Key: %s", frage["key"])
        return False
    if frage["typ"] not in ("chips", "freitext", "chips_freitext", "slider"):
        return False
    return frage["typ"] in ("slider", "freitext") or bool(frage.get("optionen"))


def _sammle_beantwortete(profil):
    """Formatiere bereits beantwortete Profil-Felder als Text fuer den Prompt."""
    if not profil:
        return ""

    teile = []
    for section_key, section_data in profil.items():
        if section_key == "meta":
            continue
        if not isinstance(section_data, dict):
            continue
        for field_key, field_val in section_data.items():
            if field_val and field_val != [] and field_val != {}:
                if isinstance(field_val, list):
                    val_text = ", ".join(str(v) for v in field_val)
                else:
                    val_text = str(field_val)
                teile.append(f"- {section_key}.{field_key}: {val_text}")

    return "\n".join(teile)
