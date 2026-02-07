from datetime import datetime
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy import text

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

    # Refresh the user object to get the latest counter value
    db.session.refresh(user)

    return {
        "plan": plan.value,
        "limit": limit,
        "used": user.applications_this_month,
        "remaining": -1 if limit == -1 else max(0, limit - user.applications_this_month),
        "unlimited": limit == -1,
    }


def try_increment_application_count(user, plan_limit):
    """Atomically check limit and increment counter.

    Uses a single UPDATE with a WHERE clause to prevent TOCTOU race conditions.
    The row is only updated if the current count is still below the limit.

    Args:
        user: The User model instance.
        plan_limit: The maximum number of applications allowed (-1 for unlimited).

    Returns:
        True if the increment succeeded (was within limit), False otherwise.
    """
    if plan_limit == -1:  # unlimited
        return True

    _check_and_reset_monthly_counter(user)

    result = db.session.execute(
        text(
            "UPDATE users"
            " SET applications_this_month = applications_this_month + 1"
            " WHERE id = :user_id AND applications_this_month < :limit"
        ),
        {"user_id": user.id, "limit": plan_limit},
    )
    db.session.commit()

    # Refresh user object so it reflects the new counter value
    db.session.refresh(user)

    return result.rowcount > 0


def decrement_application_count(user):
    """Decrement the user's monthly application counter (rollback on failure).

    Used when a generation fails after the atomic increment already happened,
    so the user is not penalised for a failed attempt.
    """
    _check_and_reset_monthly_counter(user)

    db.session.execute(
        text(
            "UPDATE users"
            " SET applications_this_month = CASE"
            "   WHEN applications_this_month > 0 THEN applications_this_month - 1"
            "   ELSE 0"
            " END"
            " WHERE id = :user_id"
        ),
        {"user_id": user.id},
    )
    db.session.commit()

    # Refresh user object so it reflects the new counter value
    db.session.refresh(user)


def check_subscription_limit(fn):
    """
    Decorator that atomically checks the subscription limit AND increments the
    counter in one step, preventing TOCTOU race conditions.

    Must be used with @jwt_required() or @jwt_required_custom before this decorator.
    Expects current_user in kwargs (from jwt_required_custom) or fetches it from JWT identity.

    On success the counter is already incremented -- the wrapped function does NOT
    need to call increment_application_count().  If the wrapped function raises an
    exception, the counter is rolled back via decrement_application_count().

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

        # Atomically check limit and increment
        if not try_increment_application_count(current_user, limit):
            # Refresh to get accurate count for the error response
            db.session.refresh(current_user)
            plan_name = plan.value.capitalize()
            return jsonify(
                {
                    "success": False,
                    "error": f"Monatliches Limit erreicht. Dein {plan_name}-Plan erlaubt {limit} Bewerbungen pro Monat. Upgrade für mehr Bewerbungen.",
                    "error_code": "SUBSCRIPTION_LIMIT_REACHED",
                    "usage": {
                        "plan": plan.value,
                        "limit": limit,
                        "used": current_user.applications_this_month,
                    },
                }
            ), 403

        # Increment succeeded -- call the wrapped function
        try:
            return fn(*args, **kwargs)
        except Exception:
            # Roll back the counter so the user isn't penalised for a failed generation
            decrement_application_count(current_user)
            raise

    return wrapper


def increment_application_count(user):
    """
    Increment the user's monthly application counter.

    .. deprecated::
        Kept for backwards compatibility (e.g. the extension ``/generate``
        endpoint which uses ``@api_key_required`` instead of
        ``@check_subscription_limit``).  Endpoints that use the
        ``@check_subscription_limit`` decorator no longer need to call this
        because the decorator performs the increment atomically.
    """
    _check_and_reset_monthly_counter(user)
    user.applications_this_month += 1
    db.session.commit()
