"""Seele Fragen - AI-generierte personalisierte Fragen basierend auf Lebenslauf."""

import logging

from config import config
from services.ai_client import AIClient

logger = logging.getLogger(__name__)

# Fallback-Fragen wenn AI nicht verfuegbar oder fehlschlaegt
FALLBACK_FRAGEN = {
    "onboarding": [
        {
            "key": "motivation.aktuelle_situation",
            "frage": "Was beschreibt deine aktuelle Situation am besten?",
            "typ": "chips",
            "optionen": [
                "Aktiv auf Jobsuche",
                "Offen für Neues",
                "Karrierewechsel",
                "Erster Job",
                "Wiedereinstieg",
            ],
            "mehrfach": False,
        },
        {
            "key": "arbeitsstil.arbeitsmodell",
            "frage": "Welches Arbeitsmodell passt zu dir?",
            "typ": "chips",
            "optionen": ["Remote", "Hybrid", "Vor Ort", "Ist mir egal"],
            "mehrfach": True,
        },
        {
            "key": "motivation.wichtig_im_job",
            "frage": "Was ist dir im nächsten Job besonders wichtig?",
            "typ": "chips_freitext",
            "optionen": [
                "Work-Life-Balance",
                "Gehalt",
                "Teamkultur",
                "Weiterbildung",
                "Aufstiegschancen",
                "Sinnvolle Arbeit",
                "Flexibilität",
                "Technische Herausforderung",
            ],
            "mehrfach": True,
            "max_auswahl": 5,
        },
        {
            "key": "motivation.wechsel_tempo",
            "frage": "Wie schnell möchtest du wechseln?",
            "typ": "chips",
            "optionen": ["Sofort verfügbar", "In 1-3 Monaten", "Schaue mich nur um"],
            "mehrfach": False,
        },
    ],
    "pre_bewerbung": [
        {
            "key": "arbeitsstil.staerken",
            "frage": "Welche Stärken würdest du dir zuschreiben?",
            "typ": "chips_freitext",
            "optionen": [
                "Analytisches Denken",
                "Kommunikation",
                "Problemlösung",
                "Teamarbeit",
                "Kreativität",
                "Organisationstalent",
                "Eigeninitiative",
                "Führungskompetenz",
            ],
            "mehrfach": True,
            "max_auswahl": 5,
        },
        {
            "key": "arbeitsstil.teamrolle",
            "frage": "Welche Rolle nimmst du in Teams ein?",
            "typ": "chips",
            "optionen": [
                "Teamleader",
                "Koordinator",
                "Ideengeber",
                "Umsetzer",
                "Vermittler",
                "Analyst",
            ],
            "mehrfach": False,
        },
        {
            "key": "gehaltsvorstellung.wunsch",
            "frage": "In welchem Gehaltsbereich siehst du dich?",
            "typ": "slider",
            "optionen": None,
            "mehrfach": False,
            "min_wert": 25000,
            "max_wert": 150000,
            "schritt": 5000,
        },
    ],
    "micro": [],
}

SESSION_TYP_FOKUS = {
    "onboarding": "Motivation, Arbeitsmodell, Prioritaeten im naechsten Job, Wechselbereitschaft",
    "pre_bewerbung": "Staerken, Teamrolle, Gehaltsvorstellung",
}

GUELTIGE_KEYS = {
    "onboarding": [
        "motivation.aktuelle_situation",
        "arbeitsstil.arbeitsmodell",
        "motivation.wichtig_im_job",
        "motivation.wechsel_tempo",
    ],
    "pre_bewerbung": [
        "arbeitsstil.staerken",
        "arbeitsstil.teamrolle",
        "gehaltsvorstellung.wunsch",
    ],
}


def generiere_fragen(session_typ, cv_text=None, zeugnis_text=None, skills=None, profil=None, user=None):
    """Generiere personalisierte Fragen basierend auf CV und Profil via AI.

    Returns Liste von Frage-Dicts. Bei Fehler: Fallback auf statische Fragen.
    """
    if session_typ == "micro":
        return []

    fallback = FALLBACK_FRAGEN.get(session_typ, [])
    if not fallback:
        return []

    # Ohne CV-Text koennen wir keine personalisierten Fragen generieren
    if not cv_text:
        logger.info("Kein CV-Text vorhanden, nutze Fallback-Fragen fuer %s", session_typ)
        return list(fallback)

    # Bereits beantwortete Felder sammeln
    bereits_beantwortet = _sammle_beantwortete(profil)

    # Skills formatieren
    skills_text = ""
    if skills:
        skill_names = [s if isinstance(s, str) else s.skill_name for s in skills[:20]]
        skills_text = ", ".join(skill_names)

    gueltige_keys = GUELTIGE_KEYS.get(session_typ, [])
    fokus = SESSION_TYP_FOKUS.get(session_typ, "")

    prompt = f"""Du generierst personalisierte Fragen fuer ein Bewerberprofil.

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
SESSION-TYP: {session_typ}
FOKUS: {fokus}

Generiere {len(gueltige_keys)} Fragen als JSON. Jede Frage muss:
- Sich auf den konkreten Lebenslauf beziehen (Branche, Position, Skills erwaehnen)
- Natuerlich und gespraechig klingen (Du-Form)
- 3-6 passende Chip-Optionen haben die zur Person passen
- Einen der folgenden Keys verwenden: {', '.join(gueltige_keys)}

Frage-Typen:
- "chips": Einzelauswahl aus Optionen
- "chips_freitext": Mehrfachauswahl + Freitext (setze "mehrfach": true, "max_auswahl": 5)
- "slider": Zahlenwert (setze "optionen": null, "min_wert", "max_wert", "schritt")

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
            max_tokens=800,
            temperature=0.7,
        )

        fragen = result.get("fragen", [])
        if not fragen or not isinstance(fragen, list):
            logger.warning("AI Fragen-Antwort ungueltig: %s", result)
            return list(fallback)

        # Validiere jede Frage
        validierte = []
        for frage in fragen:
            if _validiere_frage(frage, gueltige_keys):
                validierte.append(frage)

        if not validierte:
            logger.warning("Keine validen AI-Fragen, nutze Fallback")
            return list(fallback)

        logger.info("AI generierte %d personalisierte Fragen fuer %s", len(validierte), session_typ)
        return validierte

    except Exception as e:
        logger.error("Fragen-Generierung fehlgeschlagen: %s, nutze Fallback", e)
        return list(fallback)


def get_naechste_fragen(fragen, profil, max_fragen=4):
    """Filtere bereits beantwortete Fragen aus einer Fragenliste.

    Args:
        fragen: Liste von Frage-Dicts (AI-generiert oder Fallback)
        profil: Aktuelles Profil-Dict
        max_fragen: Maximale Anzahl zurueckzugebender Fragen
    """
    if not fragen:
        return []

    offene_fragen = []
    for frage in fragen:
        key_parts = frage["key"].split(".")
        section = key_parts[0] if key_parts else None
        field = key_parts[1] if len(key_parts) > 1 else None

        if section and field and profil:
            section_data = profil.get(section, {})
            if isinstance(section_data, dict):
                existing = section_data.get(field)
                if existing and existing != [] and existing != {}:
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


def _validiere_frage(frage, gueltige_keys):
    """Pruefe ob eine AI-generierte Frage das richtige Format hat."""
    if not isinstance(frage, dict):
        return False
    if not frage.get("key") or not frage.get("frage") or not frage.get("typ"):
        return False
    if "." not in frage["key"]:
        return False
    if frage["key"] not in gueltige_keys:
        logger.warning("AI generierte ungueltigen Key: %s", frage["key"])
        return False
    if frage["typ"] not in ("chips", "freitext", "chips_freitext", "slider"):
        return False
    return frage["typ"] == "slider" or bool(frage.get("optionen"))


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
