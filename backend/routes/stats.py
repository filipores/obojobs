from flask import Blueprint, jsonify

from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import get_subscription_usage
from models import Application

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/stats", methods=["GET"])
@jwt_required_custom
def get_stats(current_user):
    """Get user statistics"""
    # Count applications by status
    total = Application.query.filter_by(user_id=current_user.id).count()
    erstellt = Application.query.filter_by(user_id=current_user.id, status="erstellt").count()
    versendet = Application.query.filter_by(user_id=current_user.id, status="versendet").count()
    antwort_erhalten = Application.query.filter_by(user_id=current_user.id, status="antwort_erhalten").count()

    # Get subscription usage
    usage = get_subscription_usage(current_user)

    return jsonify(
        {
            "success": True,
            "stats": {
                "gesamt": total,
                "erstellt": erstellt,
                "versendet": versendet,
                "antwort_erhalten": antwort_erhalten,
            },
            "usage": usage,
        }
    ), 200
