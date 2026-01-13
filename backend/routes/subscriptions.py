import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from config import config
from models import User, db
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint("subscriptions", __name__)

# Subscription plan definitions
SUBSCRIPTION_PLANS = {
    "free": {
        "plan_id": "free",
        "name": "Free",
        "price": 0,
        "price_formatted": "€0/Monat",
        "features": [
            "3 Bewerbungen pro Monat",
            "Basis-Templates",
            "PDF Export",
        ],
        "limits": {
            "applications_per_month": 3,
        },
        "stripe_price_id": None,  # No payment needed
    },
    "basic": {
        "plan_id": "basic",
        "name": "Basic",
        "price": 9.99,
        "price_formatted": "€9,99/Monat",
        "features": [
            "20 Bewerbungen pro Monat",
            "Alle Templates",
            "PDF Export",
            "ATS-Optimierung",
            "E-Mail Support",
        ],
        "limits": {
            "applications_per_month": 20,
        },
        "stripe_price_id": config.STRIPE_PRICE_BASIC,
    },
    "pro": {
        "plan_id": "pro",
        "name": "Pro",
        "price": 19.99,
        "price_formatted": "€19,99/Monat",
        "features": [
            "Unbegrenzte Bewerbungen",
            "Alle Templates",
            "PDF Export",
            "ATS-Optimierung",
            "Prioritäts-Support",
            "Erweiterte Analyse",
        ],
        "limits": {
            "applications_per_month": -1,  # -1 = unlimited
        },
        "stripe_price_id": config.STRIPE_PRICE_PRO,
    },
}


@subscriptions_bp.route("/plans", methods=["GET"])
def get_plans():
    """
    Get available subscription plans (public endpoint).

    Returns a list of all subscription plans with their features and limits.
    """
    plans = []
    for plan_key in ["free", "basic", "pro"]:  # Maintain order
        plan = SUBSCRIPTION_PLANS[plan_key]
        plans.append(
            {
                "plan_id": plan["plan_id"],
                "name": plan["name"],
                "price": plan["price"],
                "price_formatted": plan["price_formatted"],
                "features": plan["features"],
                "limits": plan["limits"],
                # Only include stripe_price_id if it exists (not for free plan)
                "stripe_price_id": plan["stripe_price_id"] if plan["stripe_price_id"] else None,
            }
        )

    return jsonify({"success": True, "data": plans}), 200


def get_plan_limits(plan_name: str) -> dict:
    """
    Get the limits for a specific plan.

    Args:
        plan_name: Name of the plan (free, basic, pro)

    Returns:
        Dictionary with plan limits
    """
    plan = SUBSCRIPTION_PLANS.get(plan_name, SUBSCRIPTION_PLANS["free"])
    return plan["limits"]


@subscriptions_bp.route("/create-checkout", methods=["POST"])
@jwt_required()
def create_checkout():
    """
    Create a Stripe Checkout Session for subscription purchase.

    Request Body:
        plan: 'basic' or 'pro'
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels

    Returns:
        checkout_url: URL to redirect user to Stripe Checkout
        session_id: Stripe Checkout Session ID
    """
    data = request.json or {}

    plan = data.get("plan")
    success_url = data.get("success_url")
    cancel_url = data.get("cancel_url")

    # Validate plan
    if plan not in ["basic", "pro"]:
        return jsonify({"success": False, "error": "Invalid plan. Must be 'basic' or 'pro'"}), 400

    # Validate URLs
    if not success_url or not cancel_url:
        return jsonify({"success": False, "error": "success_url and cancel_url are required"}), 400

    # Get the Stripe price ID for this plan
    plan_data = SUBSCRIPTION_PLANS.get(plan)
    if not plan_data or not plan_data.get("stripe_price_id"):
        return jsonify({"success": False, "error": "Plan not configured"}), 400

    price_id = plan_data["stripe_price_id"]

    # Get current user
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    try:
        stripe_service = StripeService()

        # Create Stripe Customer if not exists
        if not user.stripe_customer_id:
            customer_id = stripe_service.create_customer(
                email=user.email,
                name=user.full_name
            )
            user.stripe_customer_id = customer_id
            db.session.commit()
            logger.info(f"Created Stripe customer {customer_id} for user {user.id}")
        else:
            customer_id = user.stripe_customer_id

        # Create Checkout Session
        session = stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        logger.info(f"Created checkout session {session.id} for user {user.id}, plan {plan}")

        return jsonify({
            "success": True,
            "data": {
                "checkout_url": session.url,
                "session_id": session.id
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return jsonify({"success": False, "error": "Failed to create checkout session"}), 500


@subscriptions_bp.route("/portal", methods=["POST"])
@jwt_required()
def create_portal_session():
    """
    Create a Stripe Customer Portal session for subscription management.

    Request Body:
        return_url: URL to return to after portal session

    Returns:
        portal_url: URL to redirect user to Stripe Customer Portal
    """
    data = request.json or {}
    return_url = data.get("return_url")

    if not return_url:
        return jsonify({"success": False, "error": "return_url is required"}), 400

    # Get current user
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    # User must have a Stripe customer ID to access portal
    if not user.stripe_customer_id:
        return jsonify({
            "success": False,
            "error": "No active subscription. Please subscribe first."
        }), 400

    try:
        stripe_service = StripeService()

        session = stripe_service.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=return_url
        )

        logger.info(f"Created portal session for user {user.id}")

        return jsonify({
            "success": True,
            "data": {
                "portal_url": session.url
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        return jsonify({"success": False, "error": "Failed to create portal session"}), 500


@subscriptions_bp.route("/current", methods=["GET"])
@jwt_required()
def get_current_subscription():
    """
    Get the current user's subscription details and usage.

    Returns:
        plan: Current plan name
        status: Subscription status
        usage: Usage details (used, limit, remaining, unlimited)
        next_billing_date: Next billing date (if applicable)
    """
    from middleware.subscription_limit import get_subscription_usage

    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Get usage info
    usage = get_subscription_usage(user)

    # Get subscription details
    subscription_data = {
        "plan": usage["plan"],
        "status": "active",
        "usage": {
            "used": usage["used"],
            "limit": usage["limit"],
            "remaining": usage["remaining"],
            "unlimited": usage["unlimited"]
        },
        "plan_details": SUBSCRIPTION_PLANS.get(usage["plan"], SUBSCRIPTION_PLANS["free"]),
        "has_stripe_customer": bool(user.stripe_customer_id)
    }

    # If user has a subscription record, get additional details
    if user.subscription:
        subscription_data["status"] = user.subscription.status.value
        if user.subscription.current_period_end:
            subscription_data["next_billing_date"] = user.subscription.current_period_end.isoformat()

    return jsonify({"success": True, "data": subscription_data}), 200
