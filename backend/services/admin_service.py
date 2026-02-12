"""Service layer for admin data access."""

from datetime import datetime, timedelta

from sqlalchemy import func

from models import Application, Subscription, User, db
from models.subscription import SubscriptionPlan, SubscriptionStatus


def get_user(user_id):
    """Return a user by ID, or None."""
    return User.query.get(user_id)


def get_total_users():
    """Return total user count."""
    return User.query.count()


def get_total_applications():
    """Return total application count."""
    return Application.query.count()


def get_active_users_30d():
    """Return count of users active in the last 30 days."""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    users_created_recently = db.session.query(User.id).filter(User.created_at >= thirty_days_ago)
    users_with_recent_apps = (
        db.session.query(Application.user_id).filter(Application.datum >= thirty_days_ago).distinct()
    )
    return User.query.filter(
        db.or_(
            User.id.in_(users_created_recently),
            User.id.in_(users_with_recent_apps),
        )
    ).count()


def get_applications_this_month():
    """Return sum of all users' applications_this_month."""
    return db.session.query(func.coalesce(func.sum(User.applications_this_month), 0)).scalar()


def get_subscription_counts():
    """Return counts of basic and pro active subscriptions."""
    basic_count = Subscription.query.filter(
        Subscription.plan == SubscriptionPlan.basic,
        Subscription.status == SubscriptionStatus.active,
    ).count()
    pro_count = Subscription.query.filter(
        Subscription.plan == SubscriptionPlan.pro,
        Subscription.status == SubscriptionStatus.active,
    ).count()
    return basic_count, pro_count


def get_signups_last_7_days():
    """Return count of users signed up in the last 7 days."""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    return User.query.filter(User.created_at >= seven_days_ago).count()


def get_email_verified_count():
    """Return count of users with verified emails."""
    return User.query.filter(User.email_verified.is_(True)).count()


def list_users_paginated(page, per_page, search="", plan_filter="", sort="created_at", order="desc"):
    """Return paginated user list with filtering and sorting."""
    query = User.query

    if search:
        search_term = f"%{search}%"
        query = query.filter(db.or_(User.email.ilike(search_term), User.full_name.ilike(search_term)))

    if plan_filter:
        if plan_filter == "free":
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

    total = query.count()
    pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    return users, total, pages


def commit():
    """Commit the current database session."""
    db.session.commit()
