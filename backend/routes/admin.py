from datetime import datetime
from typing import Any

from flask import Blueprint, Response, jsonify, request

from middleware.admin_required import admin_required
from services import admin_service

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def get_stats(current_user: Any) -> Response:
    total_users = admin_service.get_total_users()
    total_applications = admin_service.get_total_applications()
    active_users_30d = admin_service.get_active_users_30d()
    applications_this_month = admin_service.get_applications_this_month()
    starter_count, pro_count = admin_service.get_subscription_counts()
    free_count = total_users - starter_count - pro_count
    signups_last_7_days = admin_service.get_signups_last_7_days()
    email_verified_count = admin_service.get_email_verified_count()
    revenue_estimate = round(starter_count * 9.90 + pro_count * 19.90, 2)

    return jsonify(
        {
            "total_users": total_users,
            "active_users_30d": active_users_30d,
            "total_applications": total_applications,
            "applications_this_month": applications_this_month,
            "subscriptions": {
                "free": free_count,
                "starter": starter_count,
                "pro": pro_count,
            },
            "signups_last_7_days": signups_last_7_days,
            "email_verified_count": email_verified_count,
            "revenue_estimate": revenue_estimate,
        }
    )


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users(current_user: Any) -> Response:
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    plan_filter = request.args.get("plan", "")
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    users, total, pages = admin_service.list_users_paginated(
        page, per_page, search=search, plan_filter=plan_filter, sort=sort, order=order
    )

    users_list = []
    for user in users:
        sub = user.subscription
        app_dates = [a.datum for a in user.applications if a.datum]
        last_app_date = max(app_dates).isoformat() if app_dates else None

        users_list.append(
            {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "email_verified": user.email_verified,
                "plan": sub.plan.value if sub else "free",
                "status": sub.status.value if sub else "active",
                "application_count": len(user.applications),
                "last_application_date": last_app_date,
            }
        )

    return jsonify(
        {
            "users": users_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
    )


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user_detail(user_id: int, current_user: Any) -> Response | tuple[Response, int]:
    user = admin_service.get_user(user_id)
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    sub = user.subscription
    recent_apps = sorted(user.applications, key=lambda a: a.datum or datetime.min, reverse=True)[:10]

    user_dict = {
        "id": user.id,
        "email": user.email,
        "name": user.full_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if getattr(user, "last_login", None) else None,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "stripe_customer_id": user.stripe_customer_id,
        "plan": sub.plan.value if sub else "free",
        "document_count": len(user.documents),
        "application_count": len(user.applications),
        "recent_applications": [
            {
                "id": app.id,
                "firma": app.firma,
                "position": app.position,
                "created_at": app.datum.isoformat() if app.datum else None,
                "status": app.status,
            }
            for app in recent_apps
        ],
    }

    return jsonify({"user": user_dict})


@admin_bp.route("/users/<int:user_id>", methods=["PATCH"])
@admin_required
def patch_user(user_id: int, current_user: Any) -> Response | tuple[Response, int]:
    user = admin_service.get_user(user_id)
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten übermittelt"}), 400

    allowed_fields = {"is_active", "is_admin", "email_verified"}
    invalid_fields = set(data.keys()) - allowed_fields
    if invalid_fields:
        return jsonify({"error": f"Unzulässige Felder: {', '.join(invalid_fields)}"}), 400

    # Prevent admins from deactivating or removing admin rights from themselves
    if user.id == current_user.id:
        if "is_active" in data and not data["is_active"]:
            return jsonify({"error": "Du kannst dein eigenes Konto nicht deaktivieren"}), 400
        if "is_admin" in data and not data["is_admin"]:
            return jsonify({"error": "Du kannst dir nicht selbst die Admin-Rechte entziehen"}), 400

    for field in allowed_fields & data.keys():
        setattr(user, field, bool(data[field]))

    admin_service.commit()

    return jsonify({"user": user.to_dict()})


@admin_bp.route("/users/<int:user_id>/applications", methods=["GET"])
@admin_required
def get_user_applications(user_id: int, current_user: Any) -> Response | tuple[Response, int]:
    user = admin_service.get_user(user_id)
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    applications = sorted(user.applications, key=lambda a: a.datum or datetime.min, reverse=True)
    return jsonify({"applications": [app.to_dict() for app in applications]})
