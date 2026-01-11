from flask import Blueprint, jsonify

from middleware.jwt_required import jwt_required_custom
from models import Application

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats', methods=['GET'])
@jwt_required_custom
def get_stats(current_user):
    """Get user statistics"""
    # Count applications by status
    total = Application.query.filter_by(user_id=current_user.id).count()
    erstellt = Application.query.filter_by(user_id=current_user.id, status='erstellt').count()
    versendet = Application.query.filter_by(user_id=current_user.id, status='versendet').count()
    antwort_erhalten = Application.query.filter_by(user_id=current_user.id, status='antwort_erhalten').count()

    return jsonify({
        'success': True,
        'stats': {
            'gesamt': total,
            'erstellt': erstellt,
            'versendet': versendet,
            'antwort_erhalten': antwort_erhalten,
            'credits_remaining': current_user.credits_remaining,
            'credits_max': current_user.credits_max
        }
    }), 200
