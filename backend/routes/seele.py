import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from services import seele_service

logger = logging.getLogger(__name__)
seele_bp = Blueprint("seele", __name__)


@seele_bp.route("/profil", methods=["GET"])
@jwt_required_custom
def get_profil(current_user: Any) -> tuple[Response, int]:
    """Get user's Seele profile."""
    try:
        profil = seele_service.get_or_create_profil(current_user.id)
        return jsonify({"success": True, "profil": profil}), 200
    except Exception as e:
        logger.error("Fehler beim Laden des Seele-Profils: %s", e)
        return jsonify({"error": "Profil konnte nicht geladen werden"}), 500


@seele_bp.route("/profil", methods=["PUT"])
@jwt_required_custom
def update_profil(current_user: Any) -> tuple[Response, int]:
    """Manually update profile fields."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Keine Daten gesendet"}), 400

        profil = seele_service.update_profil(current_user.id, data)
        return jsonify({"success": True, "profil": profil}), 200
    except Exception as e:
        logger.error("Fehler beim Aktualisieren des Seele-Profils: %s", e)
        return jsonify({"error": "Profil konnte nicht aktualisiert werden"}), 500


@seele_bp.route("/sessions", methods=["POST"])
@jwt_required_custom
def starte_session(current_user: Any) -> tuple[Response, int]:
    """Start a new Seele session."""
    try:
        data = request.get_json(silent=True) or {}
        session_typ = data.get("session_typ", "onboarding")
        kontext = data.get("kontext")

        if session_typ not in ("onboarding", "pre_bewerbung", "profil", "micro"):
            return jsonify({"error": "Ungueltiger Session-Typ"}), 400

        result = seele_service.starte_session(current_user.id, session_typ, kontext=kontext)
        return jsonify({"success": True, **result}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Fehler beim Starten der Seele-Session: %s", e)
        return jsonify({"error": "Session konnte nicht gestartet werden"}), 500


@seele_bp.route("/sessions/aktuell", methods=["GET"])
@jwt_required_custom
def aktuelle_session(current_user: Any) -> tuple[Response, int]:
    """Get current active session with open questions."""
    try:
        result = seele_service.get_aktuelle_session(current_user.id)
        if not result:
            return jsonify({"success": True, "session": None, "fragen": []}), 200
        return jsonify({"success": True, **result}), 200
    except Exception as e:
        logger.error("Fehler beim Laden der aktuellen Session: %s", e)
        return jsonify({"error": "Session konnte nicht geladen werden"}), 500


@seele_bp.route("/sessions/<int:session_id>/beenden", methods=["POST"])
@jwt_required_custom
def beende_session(current_user: Any, session_id: int) -> tuple[Response, int]:
    """End/abort an active session."""
    try:
        result = seele_service.beende_session(current_user.id, session_id)
        return jsonify({"success": True, "session": result}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Fehler beim Beenden der Seele-Session: %s", e)
        return jsonify({"error": "Session konnte nicht beendet werden"}), 500


@seele_bp.route("/antworten", methods=["POST"])
@jwt_required_custom
def antwort_einreichen(current_user: Any) -> tuple[Response, int]:
    """Submit an answer to a question."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Keine Daten gesendet"}), 400

        session_id = data.get("session_id")
        frage_key = data.get("frage_key")
        antwort = data.get("antwort")

        if not session_id or not frage_key:
            return jsonify({"error": "session_id und frage_key sind erforderlich"}), 400

        result = seele_service.beantworte_frage(
            user_id=current_user.id,
            session_id=session_id,
            frage_key=frage_key,
            antwort=antwort,
        )
        return jsonify({"success": True, **result}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Fehler beim Einreichen der Antwort: %s", e)
        return jsonify({"error": "Antwort konnte nicht gespeichert werden"}), 500


@seele_bp.route("/antworten/ueberspringen", methods=["POST"])
@jwt_required_custom
def frage_ueberspringen(current_user: Any) -> tuple[Response, int]:
    """Skip a question."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Keine Daten gesendet"}), 400

        session_id = data.get("session_id")
        frage_key = data.get("frage_key")

        if not session_id or not frage_key:
            return jsonify({"error": "session_id und frage_key sind erforderlich"}), 400

        result = seele_service.ueberspringe_frage(
            user_id=current_user.id,
            session_id=session_id,
            frage_key=frage_key,
        )
        return jsonify({"success": True, **result}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Fehler beim Ueberspringen der Frage: %s", e)
        return jsonify({"error": "Frage konnte nicht uebersprungen werden"}), 500


@seele_bp.route("/check", methods=["GET"])
@jwt_required_custom
def check_session(current_user: Any) -> tuple[Response, int]:
    """Check if a session should be triggered."""
    try:
        trigger = request.args.get("trigger", "dashboard")
        result = seele_service.soll_session_starten(current_user.id, trigger)
        return jsonify({"success": True, **result}), 200
    except Exception as e:
        logger.error("Fehler beim Session-Check: %s", e)
        return jsonify({"error": "Check fehlgeschlagen"}), 500
