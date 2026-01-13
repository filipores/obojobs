from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func

from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import get_subscription_usage
from models import Application, db

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


@stats_bp.route("/stats/extended", methods=["GET"])
@jwt_required_custom
def get_extended_stats(current_user):
    """Get extended user statistics for analytics dashboard"""
    user_id = current_user.id

    # Get all applications for the user
    applications = Application.query.filter_by(user_id=user_id).all()
    total = len(applications)

    # Count by status
    status_counts = {
        "erstellt": 0,
        "versendet": 0,
        "antwort_erhalten": 0,
        "interview": 0,
        "absage": 0,
        "zusage": 0,
    }
    for app in applications:
        if app.status in status_counts:
            status_counts[app.status] += 1

    # Calculate success rates (funnel)
    erfolgsquote = {
        "bewerbungen_gesamt": total,
        "versendet": status_counts["versendet"]
        + status_counts["antwort_erhalten"]
        + status_counts["interview"]
        + status_counts["absage"]
        + status_counts["zusage"],
        "antworten": status_counts["antwort_erhalten"]
        + status_counts["interview"]
        + status_counts["absage"]
        + status_counts["zusage"],
        "interviews": status_counts["interview"] + status_counts["zusage"],
        "zusagen": status_counts["zusage"],
    }

    # Calculate percentages
    if erfolgsquote["versendet"] > 0:
        erfolgsquote["antwort_rate"] = round(
            (erfolgsquote["antworten"] / erfolgsquote["versendet"]) * 100, 1
        )
    else:
        erfolgsquote["antwort_rate"] = 0

    if erfolgsquote["antworten"] > 0:
        erfolgsquote["interview_rate"] = round(
            (erfolgsquote["interviews"] / erfolgsquote["antworten"]) * 100, 1
        )
    else:
        erfolgsquote["interview_rate"] = 0

    if erfolgsquote["interviews"] > 0:
        erfolgsquote["zusage_rate"] = round(
            (erfolgsquote["zusagen"] / erfolgsquote["interviews"]) * 100, 1
        )
    else:
        erfolgsquote["zusage_rate"] = 0

    # Overall success rate (zusagen / versendet)
    if erfolgsquote["versendet"] > 0:
        erfolgsquote["gesamt_erfolgsrate"] = round(
            (erfolgsquote["zusagen"] / erfolgsquote["versendet"]) * 100, 1
        )
    else:
        erfolgsquote["gesamt_erfolgsrate"] = 0

    # Calculate average response time (datum -> sent_at)
    antwortzeiten = {"erstellt_zu_versendet": None, "versendet_zu_antwort": None}

    # For erstellt -> versendet, use sent_at if available
    sent_apps = [a for a in applications if a.sent_at and a.datum]
    if sent_apps:
        total_days = sum(
            (a.sent_at - a.datum).total_seconds() / 86400 for a in sent_apps
        )
        antwortzeiten["erstellt_zu_versendet"] = round(total_days / len(sent_apps), 1)

    # Applications per week (last 12 weeks)
    now = datetime.utcnow()
    bewerbungen_pro_woche = []
    for i in range(11, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        count = Application.query.filter(
            Application.user_id == user_id,
            Application.datum >= week_start,
            Application.datum < week_end,
        ).count()
        bewerbungen_pro_woche.append(
            {
                "woche": (now - timedelta(weeks=i)).strftime("KW %W"),
                "start": week_start.strftime("%Y-%m-%d"),
                "ende": week_end.strftime("%Y-%m-%d"),
                "anzahl": count,
            }
        )

    # Applications per month (last 12 months)
    bewerbungen_pro_monat = []
    for i in range(11, -1, -1):
        # Calculate month boundaries
        target_month = now.month - i
        target_year = now.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_start = datetime(target_year, target_month, 1)
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1)
        else:
            month_end = datetime(target_year, target_month + 1, 1)

        count = Application.query.filter(
            Application.user_id == user_id,
            Application.datum >= month_start,
            Application.datum < month_end,
        ).count()
        bewerbungen_pro_monat.append(
            {
                "monat": month_start.strftime("%B %Y"),
                "monat_kurz": month_start.strftime("%m/%Y"),
                "anzahl": count,
            }
        )

    # Top 5 companies by application count
    top_firmen = (
        db.session.query(Application.firma, func.count(Application.id).label("anzahl"))
        .filter(Application.user_id == user_id)
        .group_by(Application.firma)
        .order_by(func.count(Application.id).desc())
        .limit(5)
        .all()
    )

    top_firmen_list = [{"firma": firma, "anzahl": anzahl} for firma, anzahl in top_firmen]

    return jsonify(
        {
            "success": True,
            "data": {
                "erfolgsquote": erfolgsquote,
                "antwortzeiten": antwortzeiten,
                "bewerbungen_pro_woche": bewerbungen_pro_woche,
                "bewerbungen_pro_monat": bewerbungen_pro_monat,
                "top_firmen": top_firmen_list,
                "status_verteilung": status_counts,
            },
        }
    ), 200
