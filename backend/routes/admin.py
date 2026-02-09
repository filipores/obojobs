from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from middleware.admin_required import admin_required
from models import Application, Subscription, User, db
from models.subscription import SubscriptionPlan, SubscriptionStatus

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def get_stats(current_user):
    total_users = User.query.count()
    total_applications = Application.query.count()

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Active users: created in last 30 days OR have applications with datum in last 30 days
    users_created_recently = db.session.query(User.id).filter(User.created_at >= thirty_days_ago)
    users_with_recent_apps = (
        db.session.query(Application.user_id).filter(Application.datum >= thirty_days_ago).distinct()
    )
    active_users_30d = User.query.filter(
        db.or_(
            User.id.in_(users_created_recently),
            User.id.in_(users_with_recent_apps),
        )
    ).count()

    # Applications this month: sum of all users' applications_this_month
    applications_this_month = db.session.query(func.coalesce(func.sum(User.applications_this_month), 0)).scalar()

    # Subscription counts
    basic_count = Subscription.query.filter(
        Subscription.plan == SubscriptionPlan.basic,
        Subscription.status == SubscriptionStatus.active,
    ).count()
    pro_count = Subscription.query.filter(
        Subscription.plan == SubscriptionPlan.pro,
        Subscription.status == SubscriptionStatus.active,
    ).count()

    free_count = total_users - basic_count - pro_count

    signups_last_7_days = User.query.filter(User.created_at >= seven_days_ago).count()
    email_verified_count = User.query.filter(User.email_verified.is_(True)).count()

    revenue_estimate = round(basic_count * 9.99 + pro_count * 19.99, 2)

    return jsonify(
        {
            "total_users": total_users,
            "active_users_30d": active_users_30d,
            "total_applications": total_applications,
            "applications_this_month": applications_this_month,
            "subscriptions": {
                "free": free_count,
                "basic": basic_count,
                "pro": pro_count,
            },
            "signups_last_7_days": signups_last_7_days,
            "email_verified_count": email_verified_count,
            "revenue_estimate": revenue_estimate,
        }
    )


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users(current_user):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    plan_filter = request.args.get("plan", "")
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    query = User.query

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(db.or_(User.email.ilike(search_term), User.full_name.ilike(search_term)))

    # Plan filter
    if plan_filter:
        if plan_filter == "free":
            # Users with no subscription or free plan
            subquery = db.session.query(Subscription.user_id).filter(
                Subscription.plan.in_([SubscriptionPlan.basic, SubscriptionPlan.pro]),
                Subscription.status == SubscriptionStatus.active,
            )
            query = query.filter(~User.id.in_(subquery))
        elif plan_filter in ("basic", "pro"):
            plan_enum = SubscriptionPlan.basic if plan_filter == "basic" else SubscriptionPlan.pro
            subquery = db.session.query(Subscription.user_id).filter(
                Subscription.plan == plan_enum,
                Subscription.status == SubscriptionStatus.active,
            )
            query = query.filter(User.id.in_(subquery))

    # Sorting — 'name' and 'application_count' are frontend aliases
    sort_column = {
        "created_at": User.created_at,
        "email": User.email,
        "name": User.full_name,
        "application_count": User.applications_this_month,
        "applications_this_month": User.applications_this_month,
    }.get(sort, User.created_at)

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Paginate
    total = query.count()
    pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    users = query.offset((page - 1) * per_page).limit(per_page).all()

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
def get_user_detail(user_id, current_user):
    user = User.query.get(user_id)
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
        "template_count": len(user.templates),
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
def patch_user(user_id, current_user):
    user = User.query.get(user_id)
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
            return jsonify({"error": "Sie können Ihr eigenes Konto nicht deaktivieren"}), 400
        if "is_admin" in data and not data["is_admin"]:
            return jsonify({"error": "Sie können sich nicht selbst die Admin-Rechte entziehen"}), 400

    for field in allowed_fields & data.keys():
        setattr(user, field, bool(data[field]))

    db.session.commit()

    return jsonify({"user": user.to_dict()})
