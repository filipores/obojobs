"""Seele Profile Builder - Manages profile data structure and merging."""

import copy

LEERES_PROFIL = {
    "persoenliche_daten": {
        "name": None,
        "standort": None,
        "umzugsbereit": None,
        "wunsch_standorte": [],
        "verfuegbar_ab": None,
        "kuendigungsfrist": None,
    },
    "berufserfahrung": {
        "aktuelle_position": None,
        "aktueller_arbeitgeber": None,
        "branche": None,
        "erfahrungsjahre": None,
        "fuehrungserfahrung": None,
        "highlights": [],
    },
    "qualifikationen": {
        "ausbildung": None,
        "zertifikate": [],
        "sprachen": [],
        "top_skills": [],
    },
    "arbeitsstil": {
        "typ": None,
        "arbeitsmodell": None,
        "teamrolle": None,
        "kommunikation": None,
        "staerken": [],
        "entwicklungsbereiche": [],
    },
    "motivation": {
        "aktuelle_situation": None,
        "wechselgrund": None,
        "karriereziel": None,
        "wichtig_im_job": [],
        "wechsel_tempo": None,
        "dealbreaker": [],
        "werte": [],
    },
    "gehaltsvorstellung": {
        "minimum": None,
        "wunsch": None,
        "verhandelbar": None,
        "benefits_wichtig": [],
    },
    "persoenlichkeit": {
        "selbstbeschreibung": None,
        "hobbys_relevant": [],
        "fun_fact": None,
    },
    "meta": {
        "quellen": {},
        "confidence": {},
        "letzte_session": None,
    },
}


def erstelle_leeres_profil():
    """Create an empty profile structure with all sections."""
    return copy.deepcopy(LEERES_PROFIL)


def merge_antwort(profil, frage_key, antwort):
    """Merge a single answer into the profile using dot-path navigation.

    Args:
        profil: Current profile dict
        frage_key: Dot-separated path like "arbeitsstil.typ"
        antwort: The answer value (string, list, or number)

    Returns:
        Updated profile dict
    """
    if not profil:
        profil = erstelle_leeres_profil()

    parts = frage_key.split(".")
    if len(parts) != 2:
        return profil

    section, field = parts

    if section not in profil:
        profil[section] = {}

    profil[section][field] = antwort
    return profil


def berechne_vollstaendigkeit(profil):
    """Calculate profile completeness as percentage (0-100).

    Counts filled fields vs total fields across all sections (excluding meta).
    """
    if not profil:
        return 0

    total = 0
    filled = 0

    for section_key, section_data in profil.items():
        if section_key == "meta":
            continue
        if not isinstance(section_data, dict):
            continue
        for field_val in section_data.values():
            total += 1
            if field_val is not None and field_val != [] and field_val != {}:
                filled += 1

    return round((filled / total * 100) if total > 0 else 0)


def profil_fuer_prompt(profil):
    """Format profile as readable text block for Anschreiben prompt injection.

    Returns None if profile is empty or has very low completeness.
    """
    if not profil:
        return None

    vollstaendigkeit = berechne_vollstaendigkeit(profil)
    if vollstaendigkeit < 10:
        return None

    lines = []

    # Motivation / Situation
    motivation = profil.get("motivation", {})
    if motivation.get("aktuelle_situation"):
        lines.append(f"- Aktuelle Situation: {motivation['aktuelle_situation']}")
    if motivation.get("wechsel_tempo"):
        lines.append(f"- Verfuegbarkeit: {motivation['wechsel_tempo']}")
    if motivation.get("wichtig_im_job"):
        items = motivation["wichtig_im_job"]
        if isinstance(items, list) and items:
            lines.append(f"- Wichtig im Job: {', '.join(items)}")
    if motivation.get("wechselgrund"):
        lines.append(f"- Wechselgrund: {motivation['wechselgrund']}")

    # Arbeitsstil
    arbeitsstil = profil.get("arbeitsstil", {})
    if arbeitsstil.get("arbeitsmodell"):
        modell = arbeitsstil["arbeitsmodell"]
        if isinstance(modell, list):
            modell = ", ".join(modell)
        lines.append(f"- Arbeitsmodell: {modell}")
    if arbeitsstil.get("staerken"):
        items = arbeitsstil["staerken"]
        if isinstance(items, list) and items:
            lines.append(f"- Staerken: {', '.join(items)}")
    if arbeitsstil.get("teamrolle"):
        lines.append(f"- Teamrolle: {arbeitsstil['teamrolle']}")

    # Gehaltsvorstellung
    gehalt = profil.get("gehaltsvorstellung", {})
    if gehalt.get("wunsch"):
        lines.append(f"- Gehaltsvorstellung: {gehalt['wunsch']}EUR")

    # Persoenlichkeit
    persoenlichkeit = profil.get("persoenlichkeit", {})
    if persoenlichkeit.get("selbstbeschreibung"):
        lines.append(f"- Selbstbeschreibung: {persoenlichkeit['selbstbeschreibung']}")

    if not lines:
        return None

    return "\n".join(lines)
