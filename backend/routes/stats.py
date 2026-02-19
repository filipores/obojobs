from datetime import datetime, timedelta
from typing import Any

from flask import Blueprint, Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from middleware.subscription_limit import get_subscription_usage
from services import stats_service

stats_bp = Blueprint("stats", __name__)


def get_week_boundaries() -> tuple[datetime, datetime]:
    """Get the start and end of the current week (Monday to Sunday)."""
    now = datetime.utcnow()
    # Get Monday of current week (weekday() returns 0 for Monday)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    # End of week is next Monday
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


@stats_bp.route("/stats/weekly-goal", methods=["GET"])
@jwt_required_custom
def get_weekly_goal(current_user: Any) -> tuple[Response, int]:
    """Get user's weekly application goal and current progress."""
    week_start, week_end = get_week_boundaries()

    completed = stats_service.count_applications_in_range(current_user.id, week_start, week_end)

    goal = current_user.weekly_goal or 5
    progress = min(round((completed / goal) * 100) if goal > 0 else 100, 100)
    is_achieved = completed >= goal

    return jsonify(
        {
            "success": True,
            "data": {
                "goal": goal,
                "completed": completed,
                "progress": progress,
                "is_achieved": is_achieved,
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": (week_end - timedelta(days=1)).strftime("%Y-%m-%d"),
            },
        }
    ), 200


@stats_bp.route("/stats/weekly-goal", methods=["PUT"])
@jwt_required_custom
def update_weekly_goal(current_user: Any) -> tuple[Response, int]:
    """Update user's weekly application goal."""
    data = request.json or {}
    new_goal = data.get("goal")

    if new_goal is None:
        return jsonify({"success": False, "error": "goal ist erforderlich"}), 400

    try:
        new_goal = int(new_goal)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "goal muss eine Zahl sein"}), 400

    if new_goal < 1 or new_goal > 50:
        return jsonify({"success": False, "error": "goal muss zwischen 1 und 50 liegen"}), 400

    stats_service.update_weekly_goal(current_user, new_goal)

    # Get updated progress
    week_start, week_end = get_week_boundaries()
    completed = stats_service.count_applications_in_range(current_user.id, week_start, week_end)

    progress = min(round((completed / new_goal) * 100) if new_goal > 0 else 100, 100)
    is_achieved = completed >= new_goal

    return jsonify(
        {
            "success": True,
            "data": {
                "goal": new_goal,
                "completed": completed,
                "progress": progress,
                "is_achieved": is_achieved,
            },
            "message": f"Wöchentliches Ziel auf {new_goal} Bewerbungen gesetzt",
        }
    ), 200


@stats_bp.route("/stats", methods=["GET"])
@jwt_required_custom
def get_stats(current_user: Any) -> tuple[Response, int]:
    """Get user statistics"""
    user_id = current_user.id
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Count applications by status
    total = stats_service.count_by_status(user_id)
    erstellt = stats_service.count_by_status(user_id, "erstellt")
    versendet = stats_service.count_by_status(user_id, "versendet")
    antwort_erhalten = stats_service.count_by_status(user_id, "antwort_erhalten")
    interviews = stats_service.count_by_status(user_id, "interview")

    # Count today's sent applications (sent_at is today)
    versendet_heute = stats_service.count_sent_today(user_id, today_start)

    # Count today's responses and interviews by checking status_history
    antworten_heute = 0
    interviews_heute = 0
    today_str = today_start.strftime("%Y-%m-%d")

    apps_with_history = stats_service.get_apps_with_status_history(user_id, ["antwort_erhalten", "interview"])

    for app in apps_with_history:
        history = app.get_status_history()
        for entry in history:
            ts = entry.get("timestamp", "")
            status = entry.get("status", "")
            if ts.startswith(today_str):
                if status == "antwort_erhalten":
                    antworten_heute += 1
                    break
                if status == "interview":
                    interviews_heute += 1
                    break

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
                "interviews": interviews,
                "versendet_heute": versendet_heute,
                "antworten_heute": antworten_heute,
                "interviews_heute": interviews_heute,
            },
            "usage": usage,
        }
    ), 200


@stats_bp.route("/stats/extended", methods=["GET"])
@jwt_required_custom
def get_extended_stats(current_user: Any) -> tuple[Response, int]:
    """Get extended user statistics for analytics dashboard"""
    user_id = current_user.id

    # Get all applications for the user
    applications = stats_service.get_all_applications(user_id)
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
        erfolgsquote["antwort_rate"] = round((erfolgsquote["antworten"] / erfolgsquote["versendet"]) * 100, 1)
    else:
        erfolgsquote["antwort_rate"] = 0

    if erfolgsquote["antworten"] > 0:
        erfolgsquote["interview_rate"] = round((erfolgsquote["interviews"] / erfolgsquote["antworten"]) * 100, 1)
    else:
        erfolgsquote["interview_rate"] = 0

    if erfolgsquote["interviews"] > 0:
        erfolgsquote["zusage_rate"] = round((erfolgsquote["zusagen"] / erfolgsquote["interviews"]) * 100, 1)
    else:
        erfolgsquote["zusage_rate"] = 0

    # Overall success rate (zusagen / versendet)
    if erfolgsquote["versendet"] > 0:
        erfolgsquote["gesamt_erfolgsrate"] = round((erfolgsquote["zusagen"] / erfolgsquote["versendet"]) * 100, 1)
    else:
        erfolgsquote["gesamt_erfolgsrate"] = 0

    # Calculate average response time (datum -> sent_at)
    antwortzeiten = {"erstellt_zu_versendet": None, "versendet_zu_antwort": None}

    # For erstellt -> versendet, use sent_at if available
    sent_apps = [a for a in applications if a.sent_at and a.datum]
    if sent_apps:
        total_days = sum((a.sent_at - a.datum).total_seconds() / 86400 for a in sent_apps)
        antwortzeiten["erstellt_zu_versendet"] = round(total_days / len(sent_apps), 1)

    # Applications per week (last 12 weeks)
    now = datetime.utcnow()
    bewerbungen_pro_woche = []
    for i in range(11, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        count = stats_service.count_applications_in_range(user_id, week_start, week_end)
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

        count = stats_service.count_applications_in_range(user_id, month_start, month_end)
        bewerbungen_pro_monat.append(
            {
                "monat": month_start.strftime("%B %Y"),
                "monat_kurz": month_start.strftime("%m/%Y"),
                "anzahl": count,
            }
        )

    # Top 5 companies by application count
    top_firmen = stats_service.get_top_companies(user_id, limit=5)
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


@stats_bp.route("/stats/companies", methods=["GET"])
@jwt_required_custom
def get_company_stats(current_user: Any) -> tuple[Response, int]:
    """Get statistics grouped by company"""
    user_id = current_user.id

    # Get sort parameter (default: bewerbungen)
    sort_by = request.args.get("sort_by", "bewerbungen")
    valid_sorts = ["bewerbungen", "antwortrate", "name"]
    if sort_by not in valid_sorts:
        sort_by = "bewerbungen"

    # Get all applications for the user grouped by company
    applications = stats_service.get_all_applications(user_id)

    # Group applications by company (case-insensitive, trimmed)
    company_data = {}  # normalized_key -> data dict
    for app in applications:
        firma = (app.firma or "Unbekannt").strip()
        normalized = firma.lower()
        if normalized not in company_data:
            company_data[normalized] = {
                "name_variants": [],
                "bewerbungen": 0,
                "antworten": 0,
                "antwortzeiten": [],
            }
        company_data[normalized]["name_variants"].append(firma)

        company_data[normalized]["bewerbungen"] += 1

        # Count responses (antwort_erhalten, interview, absage, zusage)
        if app.status in ["antwort_erhalten", "interview", "absage", "zusage"]:
            company_data[normalized]["antworten"] += 1

            # Calculate response time from status_history if available
            history = app.get_status_history()
            sent_timestamp = None
            response_timestamp = None

            for entry in history:
                if entry.get("status") == "versendet" and not sent_timestamp:
                    sent_timestamp = entry.get("timestamp")
                elif (
                    entry.get("status") in ["antwort_erhalten", "interview", "absage", "zusage"]
                    and not response_timestamp
                ):
                    response_timestamp = entry.get("timestamp")

            if sent_timestamp and response_timestamp:
                try:
                    sent_dt = datetime.fromisoformat(sent_timestamp)
                    response_dt = datetime.fromisoformat(response_timestamp)
                    days_diff = (response_dt - sent_dt).total_seconds() / 86400
                    if days_diff >= 0:
                        company_data[normalized]["antwortzeiten"].append(days_diff)
                except (ValueError, TypeError):
                    pass

    # Calculate metrics for each company
    company_list = []
    for data in company_data.values():
        # Pick the most common casing variant as display name
        variants = data["name_variants"]
        firma = max(set(variants), key=variants.count)

        antwortrate = 0
        if data["bewerbungen"] > 0:
            antwortrate = round((data["antworten"] / data["bewerbungen"]) * 100, 1)

        avg_antwortzeit = None
        if data["antwortzeiten"]:
            avg_antwortzeit = round(sum(data["antwortzeiten"]) / len(data["antwortzeiten"]), 1)

        company_list.append(
            {
                "firma": firma,
                "bewerbungen": data["bewerbungen"],
                "antworten": data["antworten"],
                "antwortrate": antwortrate,
                "durchschnittliche_antwortzeit": avg_antwortzeit,
            }
        )

    # Sort the list
    if sort_by == "bewerbungen":
        company_list.sort(key=lambda x: x["bewerbungen"], reverse=True)
    elif sort_by == "antwortrate":
        company_list.sort(key=lambda x: x["antwortrate"], reverse=True)
    elif sort_by == "name":
        company_list.sort(key=lambda x: x["firma"].lower())

    return jsonify(
        {
            "success": True,
            "data": {
                "companies": company_list,
                "total_companies": len(company_list),
                "sort_by": sort_by,
            },
        }
    ), 200
