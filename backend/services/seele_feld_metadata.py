"""Seele Feld-Metadata - Beschreibt alle 36 Profil-Felder fuer AI-Prompts und Lücken-Analyse."""

# Feld-Metadata: beschreibt alle Profil-Felder fuer AI-Prompt und Lücken-Analyse
FELD_METADATA = {
    # -- Persoenliche Daten --
    "persoenliche_daten.name": {
        "beschreibung": "Vollstaendiger Name des Bewerbers",
        "auto_extract": True,
        "prioritaet": "niedrig",
        "typ_empfehlung": "freitext",
    },
    "persoenliche_daten.standort": {
        "beschreibung": "Aktueller Wohnort / Stadt",
        "auto_extract": True,
        "prioritaet": "niedrig",
        "typ_empfehlung": "freitext",
    },
    "persoenliche_daten.umzugsbereit": {
        "beschreibung": "Bereitschaft umzuziehen fuer den Job",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips",
    },
    "persoenliche_daten.wunsch_standorte": {
        "beschreibung": "Gewuenschte Arbeitsorte/Regionen",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    "persoenliche_daten.verfuegbar_ab": {
        "beschreibung": "Ab wann der Bewerber verfuegbar ist",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips",
    },
    "persoenliche_daten.kuendigungsfrist": {
        "beschreibung": "Aktuelle Kuendigungsfrist",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips",
    },
    # -- Berufserfahrung --
    "berufserfahrung.aktuelle_position": {
        "beschreibung": "Aktuelle oder letzte Jobtitel/Position",
        "auto_extract": True,
        "prioritaet": "hoch",
        "typ_empfehlung": "freitext",
    },
    "berufserfahrung.aktueller_arbeitgeber": {
        "beschreibung": "Aktueller oder letzter Arbeitgeber/Firma",
        "auto_extract": True,
        "prioritaet": "mittel",
        "typ_empfehlung": "freitext",
    },
    "berufserfahrung.branche": {
        "beschreibung": "Branche/Industrie in der der Bewerber arbeitet",
        "auto_extract": True,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips",
    },
    "berufserfahrung.erfahrungsjahre": {
        "beschreibung": "Anzahl Jahre Berufserfahrung",
        "auto_extract": True,
        "prioritaet": "mittel",
        "typ_empfehlung": "slider",
    },
    "berufserfahrung.fuehrungserfahrung": {
        "beschreibung": "Art und Umfang der Fuehrungserfahrung",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips",
    },
    "berufserfahrung.highlights": {
        "beschreibung": "Wichtigste berufliche Erfolge und Highlights",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    # -- Qualifikationen --
    "qualifikationen.ausbildung": {
        "beschreibung": "Hoechster Bildungsabschluss (z.B. Bachelor, Master, Ausbildung)",
        "auto_extract": True,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips",
    },
    "qualifikationen.zertifikate": {
        "beschreibung": "Relevante Zertifikate und Weiterbildungen",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    "qualifikationen.sprachen": {
        "beschreibung": "Gesprochene Sprachen mit Niveau",
        "auto_extract": True,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips_freitext",
    },
    "qualifikationen.top_skills": {
        "beschreibung": "Wichtigste fachliche Skills und Kompetenzen",
        "auto_extract": True,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips_freitext",
    },
    # -- Arbeitsstil --
    "arbeitsstil.typ": {
        "beschreibung": "Allgemeiner Arbeitstyp (z.B. kreativ, analytisch, operativ)",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips",
    },
    "arbeitsstil.arbeitsmodell": {
        "beschreibung": "Bevorzugtes Arbeitsmodell (Remote, Hybrid, Vor Ort)",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips",
    },
    "arbeitsstil.teamrolle": {
        "beschreibung": "Typische Rolle in Teams (Leader, Umsetzer, Ideengeber...)",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips",
    },
    "arbeitsstil.kommunikation": {
        "beschreibung": "Bevorzugter Kommunikationsstil",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips",
    },
    "arbeitsstil.staerken": {
        "beschreibung": "Persoenliche Staerken und Soft Skills",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips_freitext",
    },
    "arbeitsstil.entwicklungsbereiche": {
        "beschreibung": "Bereiche in denen sich der Bewerber weiterentwickeln moechte",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    # -- Motivation --
    "motivation.aktuelle_situation": {
        "beschreibung": "Aktuelle berufliche Situation (Jobsuche, offen, Wechsel...)",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips",
    },
    "motivation.wechselgrund": {
        "beschreibung": "Grund fuer den Jobwechsel",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips",
    },
    "motivation.karriereziel": {
        "beschreibung": "Langfristiges Karriereziel",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "freitext",
    },
    "motivation.wichtig_im_job": {
        "beschreibung": "Was im naechsten Job besonders wichtig ist",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips_freitext",
    },
    "motivation.wechsel_tempo": {
        "beschreibung": "Wie schnell ein Wechsel gewuenscht ist",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "chips",
    },
    "motivation.dealbreaker": {
        "beschreibung": "Absolute No-Gos und Dealbreaker bei Jobs",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "chips_freitext",
    },
    "motivation.werte": {
        "beschreibung": "Persoenliche Werte die im Beruf wichtig sind",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    # -- Gehaltsvorstellung --
    "gehaltsvorstellung.minimum": {
        "beschreibung": "Absolutes Mindestgehalt (Jahresbrutto)",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "slider",
    },
    "gehaltsvorstellung.wunsch": {
        "beschreibung": "Wunschgehalt (Jahresbrutto)",
        "auto_extract": False,
        "prioritaet": "hoch",
        "typ_empfehlung": "slider",
    },
    "gehaltsvorstellung.verhandelbar": {
        "beschreibung": "Ob das Gehalt verhandelbar ist",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips",
    },
    "gehaltsvorstellung.benefits_wichtig": {
        "beschreibung": "Wichtige Benefits neben dem Gehalt",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    # -- Persoenlichkeit --
    "persoenlichkeit.selbstbeschreibung": {
        "beschreibung": "Selbstbeschreibung in wenigen Worten",
        "auto_extract": False,
        "prioritaet": "mittel",
        "typ_empfehlung": "freitext",
    },
    "persoenlichkeit.hobbys_relevant": {
        "beschreibung": "Berufsrelevante Hobbys und Interessen",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "chips_freitext",
    },
    "persoenlichkeit.fun_fact": {
        "beschreibung": "Interessanter Fun Fact ueber den Bewerber",
        "auto_extract": False,
        "prioritaet": "niedrig",
        "typ_empfehlung": "freitext",
    },
}

# Alle gueltigen Profil-Keys (alles ausser meta)
ALLE_PROFIL_KEYS = set(FELD_METADATA.keys())

# Auto-extrahierbare Felder
AUTO_EXTRACT_KEYS = [k for k, v in FELD_METADATA.items() if v["auto_extract"]]
