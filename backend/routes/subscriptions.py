import logging

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from config import config
from middleware.jwt_required import get_current_user_id
from middleware.subscription_limit import CREDIT_GRANTS
from services import subscription_data_service
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint("subscriptions", __name__)

# Credit-based plan definitions (one-time purchases, no subscriptions)
SUBSCRIPTION_PLANS = {
    "free": {
        "plan_id": "free",
        "name": "Free",
        "price": 0,
        "price_formatted": "Kostenlos",
        "credits": 10,
        "features": [
            "10 Credits zum Start",
            "KI-Anschreiben",
            "Basis-Vorlagen",
            "PDF-Export",
        ],
        "stripe_price_id": None,
    },
    "starter": {
        "plan_id": "starter",
        "name": "Starter",
        "price": 9.90,
        "price_formatted": "9,90 EUR",
        "credits": CREDIT_GRANTS.get("starter", 50),
        "features": [
            "50 Credits",
            "KI-Anschreiben",
            "Alle Vorlagen",
            "PDF-Export",
            "ATS-Check",
            "E-Mail-Entwurf",
            "Job-Fit Score",
        ],
        "stripe_price_id": config.STRIPE_PRICE_STARTER,
    },
    "pro": {
        "plan_id": "pro",
        "name": "Pro",
        "price": 19.90,
        "price_formatted": "19,90 EUR",
        "credits": CREDIT_GRANTS.get("pro", 150),
        "features": [
            "150 Credits",
            "KI-Anschreiben",
            "Premium-Vorlagen",
            "PDF-Export",
            "ATS-Check",
            "E-Mail-Entwurf",
            "Job-Fit Score",
            "Interview-Vorbereitung",
            "Gehalts-Coach",
            "Prioritäts-Support",
        ],
        "stripe_price_id": config.STRIPE_PRICE_PRO,
    },
}


@subscriptions_bp.route("/status", methods=["GET"])
def get_payment_status() -> tuple[Response, int]:
    """Check if payment system is available (public endpoint)."""
    return jsonify(
        {
            "success": True,
            "data": {
                "payments_available": config.is_stripe_enabled(),
            },
        }
    ), 200


@subscriptions_bp.route("/plans", methods=["GET"])
def get_plans() -> tuple[Response, int]:
    """Get available plans (public endpoint)."""
    plans = list(SUBSCRIPTION_PLANS.values())
    return jsonify(
        {
            "success": True,
            "data": plans,
            "payments_available": config.is_stripe_enabled(),
        }
    ), 200


def get_plan_limits(plan_name: str) -> dict:
    """Get the limits for a specific plan (free, starter, pro)."""
    return SUBSCRIPTION_PLANS.get(plan_name, SUBSCRIPTION_PLANS["free"]).get("credits", 0)


@subscriptions_bp.route("/create-checkout", methods=["POST"])
@jwt_required()
def create_checkout() -> tuple[Response, int]:
    """Create a Stripe Checkout Session for one-time credit purchase."""
    if not config.is_stripe_enabled():
        return jsonify(
            {
                "success": False,
                "error": "Zahlungssystem wird eingerichtet",
                "payments_available": False,
            }
        ), 503

    data = request.json or {}

    plan = data.get("plan")
    success_url = data.get("success_url")
    cancel_url = data.get("cancel_url")

    if plan not in ["starter", "pro"]:
        return jsonify({"success": False, "error": "Ungültiger Plan. Muss 'starter' oder 'pro' sein."}), 400

    if not success_url or not cancel_url:
        return jsonify({"success": False, "error": "success_url und cancel_url sind erforderlich"}), 400

    plan_data = SUBSCRIPTION_PLANS.get(plan)
    if not plan_data or not plan_data.get("stripe_price_id"):
        return jsonify({"success": False, "error": "Plan nicht konfiguriert"}), 400

    price_id = plan_data["stripe_price_id"]
    credits = plan_data.get("credits", 0)

    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    try:
        stripe_service = StripeService()

        if not user.stripe_customer_id:
            customer_id = stripe_service.create_customer(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user.id)},
            )
            subscription_data_service.save_stripe_customer_id(user, customer_id)
            logger.info(f"Created Stripe customer {customer_id} for user {user.id}")
        else:
            customer_id = user.stripe_customer_id

        session = stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id), "plan": plan, "credits": str(credits)},
        )

        logger.info(f"Created checkout session {session.id} for user {user.id}, plan {plan}")

        return jsonify({"success": True, "data": {"checkout_url": session.url, "session_id": session.id}}), 200

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return jsonify({"success": False, "error": "Fehler beim Erstellen der Checkout-Sitzung"}), 500


@subscriptions_bp.route("/current", methods=["GET"])
@jwt_required()
def get_current_subscription() -> tuple[Response, int]:
    """Get the current user's credit balance and plan details."""
    from middleware.subscription_limit import get_subscription_usage

    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    usage = get_subscription_usage(user)

    subscription_data = {
        "plan": "free",
        "status": "active",
        "credits_remaining": user.credits_remaining,
        "usage": {
            "used": 0,
            "limit": user.credits_remaining,
            "remaining": user.credits_remaining,
            "unlimited": False,
        },
        "plan_details": SUBSCRIPTION_PLANS.get("free"),
        "has_stripe_customer": bool(user.stripe_customer_id),
        "payments_available": config.is_stripe_enabled(),
    }

    return jsonify({"success": True, "data": subscription_data}), 200
