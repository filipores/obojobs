"""Seele Service - Orchestrates personality profile sessions and data."""

import json
import logging
from datetime import datetime

from models import SeeleAntwort, SeeleProfile, SeeleSession, UserSkill, db
from services.doc_cache import get_cached_doc_text
from services.document_service import get_document_by_type
from services.seele_frage_generator import generiere_micro_frage
from services.seele_fragen import FALLBACK_FRAGEN, generiere_fragen, get_naechste_fragen
from services.seele_profile_builder import (
    erstelle_leeres_profil,
    merge_antwort,
    profil_fuer_prompt,
)

logger = logging.getLogger(__name__)


def get_or_create_profil(user_id):
    """Get or create the user's Seele profile. Returns profile dict."""
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profil_data = erstelle_leeres_profil()
        profile = SeeleProfile(
            user_id=user_id,
            profil_json=json.dumps(profil_data, ensure_ascii=False),
            version=1,
            vollstaendigkeit=0,
        )
        db.session.add(profile)
        db.session.commit()
    return profile.to_dict()


def update_profil(user_id, data):
    """Manually update profile fields from a dict. Returns updated profile dict."""
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profil_data = erstelle_leeres_profil()
        profile = SeeleProfile(
            user_id=user_id,
            profil_json=json.dumps(profil_data, ensure_ascii=False),
            version=1,
        )
        db.session.add(profile)

    current = profile.get_profil()
    if not current:
        current = erstelle_leeres_profil()

    # Merge incoming data section by section
    for section_key, section_data in data.items():
        if section_key == "meta":
            continue
        if not isinstance(section_data, dict):
            continue
        if section_key not in current:
            current[section_key] = {}
        for field_key, field_val in section_data.items():
            current[section_key][field_key] = field_val

    profile.set_profil(current)
    profile.berechne_vollstaendigkeit()
    db.session.commit()
    return profile.to_dict()


def _lade_cv_kontext(user_id):
    """Lade CV-Text, Zeugnis-Text und Skills fuer personalisierte Fragen."""
    cv_text = None
    zeugnis_text = None
    skills = None

    try:
        cv_doc = get_document_by_type(user_id, "lebenslauf")
        if cv_doc and cv_doc.file_path:
            cv_text = get_cached_doc_text(cv_doc.file_path, user_id, cv_doc.id, cv_doc.updated_at)
    except Exception as e:
        logger.warning("CV-Text laden fehlgeschlagen: %s", e)

    try:
        zeugnis_doc = get_document_by_type(user_id, "arbeitszeugnis")
        if zeugnis_doc and zeugnis_doc.file_path:
            zeugnis_text = get_cached_doc_text(zeugnis_doc.file_path, user_id, zeugnis_doc.id, zeugnis_doc.updated_at)
    except Exception as e:
        logger.warning("Zeugnis-Text laden fehlgeschlagen: %s", e)

    try:
        user_skills = UserSkill.query.filter_by(user_id=user_id).all()
        if user_skills:
            skills = [s.skill_name for s in user_skills]
    except Exception as e:
        logger.warning("Skills laden fehlgeschlagen: %s", e)

    return cv_text, zeugnis_text, skills


def starte_session(user_id, session_typ, kontext=None):
    """Start a new Seele session. Returns session dict with first questions."""
    # Check for existing active session
    aktive = SeeleSession.query.filter_by(user_id=user_id, status="aktiv").first()
    if aktive:
        raise ValueError("Es laeuft bereits eine aktive Session")

    # Get current profile
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    profil_data = profile.get_profil() if profile else {}

    # Determine questions
    if session_typ == "micro":
        fragen = []
        cv_text, zeugnis_text, skills = _lade_cv_kontext(user_id)
        micro_frage = generiere_micro_frage(
            profil_data, kontext, cv_text=cv_text, zeugnis_text=zeugnis_text, skills=skills
        )
        if micro_frage:
            fragen = [micro_frage]
    else:
        # CV-basierte personalisierte Fragen generieren
        cv_text, zeugnis_text, skills = _lade_cv_kontext(user_id)
        fragen = generiere_fragen(
            session_typ,
            cv_text=cv_text,
            zeugnis_text=zeugnis_text,
            skills=skills,
            profil=profil_data,
        )

    if not fragen:
        raise ValueError("Keine offenen Fragen fuer diesen Session-Typ")

    # Cache generierte Fragen in kontext_json
    kontext_data = kontext or {}
    if session_typ != "micro":
        kontext_data["generierte_fragen"] = fragen

    session = SeeleSession(
        user_id=user_id,
        session_typ=session_typ,
        status="aktiv",
        fragen_geplant=len(fragen),
        kontext_json=json.dumps(kontext_data, ensure_ascii=False) if kontext_data else None,
    )
    db.session.add(session)
    db.session.commit()

    return {
        "session": session.to_dict(),
        "fragen": fragen,
    }


def get_aktuelle_session(user_id):
    """Get the current active session with remaining questions. Returns None if none."""
    session = SeeleSession.query.filter_by(user_id=user_id, status="aktiv").first()
    if not session:
        return None

    # Get profile to filter answered questions
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    profil_data = profile.get_profil() if profile else {}

    if session.session_typ == "micro":
        # For micro sessions, regenerate if needed
        fragen = []
        kontext = json.loads(session.kontext_json) if session.kontext_json else None
        micro_frage = generiere_micro_frage(profil_data, kontext)
        if micro_frage:
            fragen = [micro_frage]
    else:
        # Fragen aus Cache lesen, nicht neu generieren
        cached_fragen = _get_cached_fragen(session)
        fragen = get_naechste_fragen(cached_fragen, profil_data)

    # Auto-close if no more questions
    if not fragen:
        session.status = "abgeschlossen"
        session.beendet_am = datetime.utcnow()
        db.session.commit()
        return None

    return {
        "session": session.to_dict(),
        "fragen": fragen,
    }


def beantworte_frage(user_id, session_id, frage_key, antwort):
    """Save an answer, update the profile, return next questions."""
    session = SeeleSession.query.filter_by(id=session_id, user_id=user_id, status="aktiv").first()
    if not session:
        raise ValueError("Session nicht gefunden oder nicht aktiv")

    # Find the question text from cached questions
    cached_fragen = _get_cached_fragen(session)
    frage_text = _get_frage_text(frage_key, cached_fragen)
    antwort_typ = _get_antwort_typ(frage_key, cached_fragen)

    # Save the answer
    antwort_obj = SeeleAntwort(
        session_id=session_id,
        user_id=user_id,
        frage_key=frage_key,
        frage_text=frage_text,
        antwort_typ=antwort_typ,
        antwort_json=json.dumps(antwort, ensure_ascii=False) if antwort is not None else None,
        uebersprungen=False,
    )
    db.session.add(antwort_obj)
    session.fragen_beantwortet += 1

    # Update profile
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profil_data = erstelle_leeres_profil()
        profile = SeeleProfile(
            user_id=user_id,
            profil_json=json.dumps(profil_data, ensure_ascii=False),
            version=1,
        )
        db.session.add(profile)
    else:
        profil_data = profile.get_profil()
        if not profil_data:
            profil_data = erstelle_leeres_profil()

    profil_data = merge_antwort(profil_data, frage_key, antwort)
    profile.set_profil(profil_data)
    profile.berechne_vollstaendigkeit()

    # Get next questions from cache
    if session.session_typ == "micro":
        naechste_fragen = []
    else:
        naechste_fragen = get_naechste_fragen(cached_fragen, profil_data)

    # Auto-close if done
    if not naechste_fragen:
        session.status = "abgeschlossen"
        session.beendet_am = datetime.utcnow()

    db.session.commit()

    return {
        "session": session.to_dict(),
        "profil": profile.to_dict(),
        "naechste_fragen": naechste_fragen,
        "fertig": len(naechste_fragen) == 0,
    }


def ueberspringe_frage(user_id, session_id, frage_key):
    """Skip a question, return next questions."""
    session = SeeleSession.query.filter_by(id=session_id, user_id=user_id, status="aktiv").first()
    if not session:
        raise ValueError("Session nicht gefunden oder nicht aktiv")

    cached_fragen = _get_cached_fragen(session)
    frage_text = _get_frage_text(frage_key, cached_fragen)
    antwort_typ = _get_antwort_typ(frage_key, cached_fragen)

    # Save skip record
    antwort_obj = SeeleAntwort(
        session_id=session_id,
        user_id=user_id,
        frage_key=frage_key,
        frage_text=frage_text,
        antwort_typ=antwort_typ,
        antwort_json=None,
        uebersprungen=True,
    )
    db.session.add(antwort_obj)
    session.fragen_uebersprungen += 1

    # Get profile for next questions
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    profil_data = profile.get_profil() if profile else {}

    if session.session_typ == "micro":
        naechste_fragen = []
    else:
        naechste_fragen = get_naechste_fragen(cached_fragen, profil_data)

    # Auto-close if done
    if not naechste_fragen:
        session.status = "abgeschlossen"
        session.beendet_am = datetime.utcnow()

    db.session.commit()

    return {
        "session": session.to_dict(),
        "naechste_fragen": naechste_fragen,
        "fertig": len(naechste_fragen) == 0,
    }


def beende_session(user_id, session_id):
    """End a session early (abort)."""
    session = SeeleSession.query.filter_by(id=session_id, user_id=user_id, status="aktiv").first()
    if not session:
        raise ValueError("Session nicht gefunden oder nicht aktiv")

    session.status = "abgebrochen"
    session.beendet_am = datetime.utcnow()
    db.session.commit()
    return session.to_dict()


def get_profil_fuer_generation(user_id):
    """Get formatted profile text for Anschreiben prompt injection.

    Returns None if no profile exists or profile is too sparse.
    """
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None
    profil_data = profile.get_profil()
    return profil_fuer_prompt(profil_data)


def soll_session_starten(user_id, trigger):
    """Check if a Seele session should be triggered.

    Args:
        user_id: The user's ID
        trigger: Context trigger ('dashboard', 'pre_bewerbung', 'settings')

    Returns:
        Dict with soll_starten (bool), session_typ, and grund (reason).
    """
    # Check if there's already an active session
    aktive = SeeleSession.query.filter_by(user_id=user_id, status="aktiv").first()
    if aktive:
        return {
            "soll_starten": True,
            "session_typ": aktive.session_typ,
            "grund": "Aktive Session vorhanden",
            "session_id": aktive.id,
        }

    # Check profile status
    profile = SeeleProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        # No profile at all -> onboarding
        return {
            "soll_starten": True,
            "session_typ": "onboarding",
            "grund": "Kein Profil vorhanden",
            "session_id": None,
        }

    vollstaendigkeit = profile.vollstaendigkeit or 0

    if trigger == "dashboard" and vollstaendigkeit < 30:
        return {
            "soll_starten": True,
            "session_typ": "onboarding",
            "grund": "Profil unvollstaendig",
            "session_id": None,
        }

    if trigger == "pre_bewerbung" and vollstaendigkeit < 50:
        return {
            "soll_starten": True,
            "session_typ": "pre_bewerbung",
            "grund": "Profil-Luecken vor Bewerbung",
            "session_id": None,
        }

    return {
        "soll_starten": False,
        "session_typ": None,
        "grund": None,
        "session_id": None,
    }


def _get_cached_fragen(session):
    """Lese gecachte Fragen aus session.kontext_json."""
    if not session.kontext_json:
        return FALLBACK_FRAGEN.get(session.session_typ, [])

    try:
        kontext = json.loads(session.kontext_json)
        fragen = kontext.get("generierte_fragen")
        if fragen and isinstance(fragen, list):
            return fragen
    except (json.JSONDecodeError, TypeError):
        pass

    return FALLBACK_FRAGEN.get(session.session_typ, [])


def _get_frage_text(frage_key, cached_fragen=None):
    """Get the question text by key from cached or fallback questions."""
    if cached_fragen:
        for frage in cached_fragen:
            if frage.get("key") == frage_key:
                return frage.get("frage", frage_key)
    return frage_key


def _get_antwort_typ(frage_key, cached_fragen=None):
    """Get the answer type by key from cached or fallback questions."""
    if cached_fragen:
        for frage in cached_fragen:
            if frage.get("key") == frage_key:
                return frage.get("typ", "freitext")
    return "freitext"
