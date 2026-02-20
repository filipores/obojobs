"""Credit-based usage limiter.

Each user starts with FREE_CREDITS (10).  One-time purchases (Starter / Pro)
add credits via ``add_credits``.  Every generation consumes one credit.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request
from sqlalchemy import text

from middleware.jwt_required import get_current_user_id
from models import User, db

# Credits granted per one-time purchase
CREDIT_GRANTS = {"starter": 50, "pro": 150}

# Credits given to every new user on signup
FREE_CREDITS = 10


def get_subscription_usage(user: Any) -> dict:
    """Return the user's current credit balance as a usage dict."""
    db.session.refresh(user)

    return {
        "plan": "free",
        "limit": user.credits_remaining,
        "used": 0,
        "remaining": user.credits_remaining,
        "unlimited": False,
        "credits_remaining": user.credits_remaining,
    }


def try_increment_application_count(user: Any, plan_limit: int) -> bool:
    """Atomically consume one credit.

    Uses a single UPDATE with a WHERE clause so that no credit is consumed
    when the balance is already zero.

    Args:
        user: The User model instance.
        plan_limit: Ignored (kept for API compat).

    Returns:
        True if one credit was consumed, False if balance was zero.
    """
    result = db.session.execute(
        text(
            "UPDATE users"
            " SET credits_remaining = credits_remaining - 1"
            " WHERE id = :user_id AND credits_remaining > 0"
        ),
        {"user_id": user.id},
    )
    db.session.commit()
    db.session.refresh(user)

    return result.rowcount > 0


def decrement_application_count(user: Any) -> None:
    """Refund one credit (rollback after a failed generation)."""
    db.session.execute(
        text(
            "UPDATE users"
            " SET credits_remaining = credits_remaining + 1"
            " WHERE id = :user_id"
        ),
        {"user_id": user.id},
    )
    db.session.commit()
    db.session.refresh(user)


def add_credits(user: Any, amount: int) -> None:
    """Grant *amount* credits to the user (after a purchase)."""
    db.session.execute(
        text(
            "UPDATE users"
            " SET credits_remaining = credits_remaining + :amount"
            " WHERE id = :user_id"
        ),
        {"user_id": user.id, "amount": amount},
    )
    db.session.commit()
    db.session.refresh(user)


def check_subscription_limit(fn: Callable) -> Callable:
    """Decorator that atomically consumes one credit before calling *fn*.

    Must be used with ``@jwt_required()`` or ``@jwt_required_custom`` before
    this decorator.  On success the credit is already consumed -- the wrapped
    function does NOT need to decrement manually.

    If the wrapped function raises, the credit is refunded.

    Returns 403 when no credits remain.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        current_user = kwargs.get("current_user")

        if not current_user:
            verify_jwt_in_request()
            user_id = get_current_user_id()
            current_user = User.query.get(user_id)

            if not current_user or not current_user.is_active:
                return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 401

        if not try_increment_application_count(current_user, 0):
            db.session.refresh(current_user)
            return jsonify(
                {
                    "success": False,
                    "error": "Keine Credits mehr verfügbar. Kaufe einen Karriere-Pass für mehr Bewerbungen.",
                    "error_code": "SUBSCRIPTION_LIMIT_REACHED",
                    "usage": {
                        "credits_remaining": current_user.credits_remaining,
                    },
                }
            ), 403

        try:
            return fn(*args, **kwargs)
        except Exception:
            decrement_application_count(current_user)
            raise

    return wrapper


def increment_application_count(user: Any) -> None:
    """Consume one credit (legacy helper for the extension endpoint)."""
    try_increment_application_count(user, 0)
