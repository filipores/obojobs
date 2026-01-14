from datetime import datetime
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models import User, db
from models.subscription import SubscriptionPlan, SubscriptionStatus

# Plan limits (applications per month)
PLAN_LIMITS = {
    SubscriptionPlan.free: 3,
    SubscriptionPlan.basic: 20,
    SubscriptionPlan.pro: -1,  # -1 = unlimited
}


def _get_user_plan(user):
    """Get the user's current subscription plan."""
    if not user.subscription:
        return SubscriptionPlan.free

    # Only count active or trialing subscriptions
    if user.subscription.status not in [SubscriptionStatus.active, SubscriptionStatus.trialing]:
        return SubscriptionPlan.free

    return user.subscription.plan or SubscriptionPlan.free


def _check_and_reset_monthly_counter(user):
    """
    Check if the monthly counter needs to be reset.
    Resets at the beginning of each month.
    """
    now = datetime.utcnow()
    current_month_start = datetime(now.year, now.month, 1)

    # If month_reset_at is not set or is from a previous month, reset the counter
    if user.month_reset_at is None or user.month_reset_at < current_month_start:
        user.applications_this_month = 0
        user.month_reset_at = current_month_start
        db.session.commit()


def get_subscription_usage(user):
    """
    Get the user's current subscription usage information.

    Returns:
        dict with plan, limit, used, and remaining counts
    """
    _check_and_reset_monthly_counter(user)

    plan = _get_user_plan(user)
    limit = PLAN_LIMITS.get(plan, 3)

    return {
        "plan": plan.value,
        "limit": limit,
        "used": user.applications_this_month,
        "remaining": -1 if limit == -1 else max(0, limit - user.applications_this_month),
        "unlimited": limit == -1,
    }


def check_subscription_limit(fn):
    """
    Decorator that checks if the user has remaining applications in their subscription plan.

    Must be used with @jwt_required() or @jwt_required_custom before this decorator.
    Expects current_user in kwargs (from jwt_required_custom) or fetches it from JWT identity.

    Returns 403 if the user has reached their monthly limit.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Get user from kwargs (if using jwt_required_custom) or fetch from JWT
        current_user = kwargs.get("current_user")

        if not current_user:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            current_user = User.query.get(int(user_id))

            if not current_user or not current_user.is_active:
                return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 401

        # Check and reset monthly counter if needed
        _check_and_reset_monthly_counter(current_user)

        # Get user's plan and limit
        plan = _get_user_plan(current_user)
        limit = PLAN_LIMITS.get(plan, 3)

        # Pro plan has unlimited applications
        if limit == -1:
            return fn(*args, **kwargs)

        # Check if limit reached
        if current_user.applications_this_month >= limit:
            plan_name = plan.value.capitalize()
            return jsonify({
                "success": False,
                "error": f"Monatliches Limit erreicht. Dein {plan_name}-Plan erlaubt {limit} Bewerbungen pro Monat. Upgrade für mehr Bewerbungen.",
                "error_code": "SUBSCRIPTION_LIMIT_REACHED",
                "usage": {
                    "plan": plan.value,
                    "limit": limit,
                    "used": current_user.applications_this_month,
                }
            }), 403

        return fn(*args, **kwargs)

    return wrapper


def increment_application_count(user):
    """
    Increment the user's monthly application counter.
    Should be called after successfully generating an application.
    """
    _check_and_reset_monthly_counter(user)
    user.applications_this_month += 1
    db.session.commit()
