import logging

import stripe
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from config import config
from middleware.jwt_required import get_current_user_id
from services import subscription_data_service
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint("subscriptions", __name__)

# Plan ordering for upgrade/downgrade detection
PLAN_ORDER = {"free": 0, "basic": 1, "pro": 2}

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
    """Get available subscription plans (public endpoint)."""
    plans = list(SUBSCRIPTION_PLANS.values())
    return jsonify(
        {
            "success": True,
            "data": plans,
            "payments_available": config.is_stripe_enabled(),
        }
    ), 200


def get_plan_limits(plan_name: str) -> dict:
    """Get the limits for a specific plan (free, basic, pro)."""
    return SUBSCRIPTION_PLANS.get(plan_name, SUBSCRIPTION_PLANS["free"])["limits"]


@subscriptions_bp.route("/create-checkout", methods=["POST"])
@jwt_required()
def create_checkout() -> tuple[Response, int]:
    """Create a Stripe Checkout Session for subscription purchase."""
    # Check if payments are available
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

    # Validate plan
    if plan not in ["basic", "pro"]:
        return jsonify({"success": False, "error": "Ungültiger Plan. Muss 'basic' oder 'pro' sein."}), 400

    # Validate URLs
    if not success_url or not cancel_url:
        return jsonify({"success": False, "error": "success_url und cancel_url sind erforderlich"}), 400

    # Get the Stripe price ID for this plan
    plan_data = SUBSCRIPTION_PLANS.get(plan)
    if not plan_data or not plan_data.get("stripe_price_id"):
        return jsonify({"success": False, "error": "Plan nicht konfiguriert"}), 400

    price_id = plan_data["stripe_price_id"]

    # Get current user
    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    try:
        stripe_service = StripeService()

        # Create Stripe Customer if not exists
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

        # Create Checkout Session
        session = stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id), "plan": plan},
        )

        logger.info(f"Created checkout session {session.id} for user {user.id}, plan {plan}")

        return jsonify({"success": True, "data": {"checkout_url": session.url, "session_id": session.id}}), 200

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return jsonify({"success": False, "error": "Fehler beim Erstellen der Checkout-Sitzung"}), 500


@subscriptions_bp.route("/portal", methods=["POST"])
@jwt_required()
def create_portal_session() -> tuple[Response, int]:
    """Create a Stripe Customer Portal session for subscription management."""
    # Check if payments are available
    if not config.is_stripe_enabled():
        return jsonify(
            {
                "success": False,
                "error": "Zahlungssystem wird eingerichtet",
                "payments_available": False,
            }
        ), 503

    data = request.json or {}
    return_url = data.get("return_url")

    if not return_url:
        return jsonify({"success": False, "error": "return_url ist erforderlich"}), 400

    # Get current user
    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    # User must have a Stripe customer ID to access portal
    if not user.stripe_customer_id:
        return jsonify({"success": False, "error": "Kein aktives Abonnement. Bitte abonniere zuerst einen Plan."}), 400

    try:
        stripe_service = StripeService()

        session = stripe_service.create_portal_session(customer_id=user.stripe_customer_id, return_url=return_url)

        logger.info(f"Created portal session for user {user.id}")

        return jsonify({"success": True, "data": {"portal_url": session.url}}), 200

    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        return jsonify({"success": False, "error": "Fehler beim Erstellen der Portal-Sitzung"}), 500


@subscriptions_bp.route("/preview-change", methods=["POST"])
@jwt_required()
def preview_change() -> tuple[Response, int]:
    """Preview proration costs before changing subscription plan."""
    if not config.is_stripe_enabled():
        return jsonify(
            {
                "success": False,
                "error": "Zahlungssystem wird eingerichtet",
                "payments_available": False,
            }
        ), 503

    data = request.json or {}
    new_plan = data.get("plan")

    # Validate plan
    if new_plan not in ["basic", "pro"]:
        return jsonify({"success": False, "error": "Ungültiger Plan. Muss 'basic' oder 'pro' sein."}), 400

    # Get current user
    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    # Check existing subscription
    subscription = subscription_data_service.get_subscription_by_user(user.id)
    if not subscription or not subscription.stripe_subscription_id:
        return jsonify(
            {"success": False, "error": "Kein aktives Abonnement vorhanden. Bitte zuerst ein Abo abschließen."}
        ), 400

    # Check if same plan
    current_plan = subscription.plan.value if subscription.plan else "free"
    if current_plan == new_plan:
        return jsonify({"success": False, "error": "Sie haben bereits diesen Plan."}), 400

    # Get new price ID
    plan_data = SUBSCRIPTION_PLANS.get(new_plan)
    if not plan_data or not plan_data.get("stripe_price_id"):
        return jsonify({"success": False, "error": "Plan nicht konfiguriert"}), 400

    new_price_id = plan_data["stripe_price_id"]

    # Determine if upgrade or downgrade
    current_order = PLAN_ORDER.get(current_plan, 0)
    new_order = PLAN_ORDER.get(new_plan, 0)
    is_upgrade = new_order > current_order

    try:
        stripe_service = StripeService()

        # Retrieve the current subscription to get the item ID
        stripe_sub = stripe_service.get_subscription(subscription.stripe_subscription_id)

        # Ensure Stripe API key is set
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Use Stripe's invoice preview API (create_preview in stripe v14+)
        upcoming_invoice = stripe.Invoice.create_preview(
            customer=stripe_sub["customer"],
            subscription=subscription.stripe_subscription_id,
            subscription_details={
                "items": [
                    {
                        "id": stripe_sub["items"]["data"][0]["id"],
                        "price": new_price_id,
                    }
                ],
                "proration_behavior": "create_prorations",
            },
        )

        # Calculate proration from invoice line items
        proration_amount = 0
        for line in upcoming_invoice["lines"]["data"]:
            if line.get("proration"):
                proration_amount += line["amount"]

        # Convert from cents to euros
        immediate_charge = max(0, proration_amount / 100) if is_upgrade else 0
        proration_display = proration_amount / 100

        return jsonify(
            {
                "success": True,
                "data": {
                    "immediate_charge": round(immediate_charge, 2),
                    "proration_amount": round(proration_display, 2),
                    "next_billing_date": upcoming_invoice["period_end"],
                    "is_upgrade": is_upgrade,
                    "new_plan_name": plan_data["name"],
                    "new_plan_price": plan_data["price_formatted"],
                },
            }
        ), 200

    except Exception as e:
        logger.error(f"Failed to preview plan change for user {user.id}: {e}")
        return jsonify({"success": False, "error": "Fehler bei der Vorschau des Planwechsels"}), 500


@subscriptions_bp.route("/change-plan", methods=["POST"])
@jwt_required()
def change_plan() -> tuple[Response, int]:
    """Change subscription plan (upgrade or downgrade via Stripe)."""
    if not config.is_stripe_enabled():
        return jsonify(
            {
                "success": False,
                "error": "Zahlungssystem wird eingerichtet",
                "payments_available": False,
            }
        ), 503

    data = request.json or {}
    new_plan = data.get("plan")

    # Validate plan
    if new_plan not in ["basic", "pro"]:
        return jsonify({"success": False, "error": "Ungültiger Plan. Muss 'basic' oder 'pro' sein."}), 400

    # Get current user
    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    # Check existing subscription
    subscription = subscription_data_service.get_subscription_by_user(user.id)
    if not subscription or not subscription.stripe_subscription_id:
        return jsonify(
            {"success": False, "error": "Kein aktives Abonnement vorhanden. Bitte zuerst ein Abo abschließen."}
        ), 400

    # Check if same plan
    current_plan = subscription.plan.value if subscription.plan else "free"
    if current_plan == new_plan:
        return jsonify({"success": False, "error": "Sie haben bereits diesen Plan."}), 400

    # Get new price ID
    plan_data = SUBSCRIPTION_PLANS.get(new_plan)
    if not plan_data or not plan_data.get("stripe_price_id"):
        return jsonify({"success": False, "error": "Plan nicht konfiguriert"}), 400

    new_price_id = plan_data["stripe_price_id"]

    # Determine proration behavior
    current_order = PLAN_ORDER.get(current_plan, 0)
    new_order = PLAN_ORDER.get(new_plan, 0)
    is_upgrade = new_order > current_order

    proration_behavior = "always_invoice" if is_upgrade else "create_prorations"

    try:
        stripe_service = StripeService()
        stripe_service.modify_subscription(
            subscription_id=subscription.stripe_subscription_id,
            new_price_id=new_price_id,
            proration_behavior=proration_behavior,
        )

        logger.info(
            f"User {user.id} changed plan from {current_plan} to {new_plan} "
            f"({'upgrade' if is_upgrade else 'downgrade'})"
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "previous_plan": current_plan,
                    "new_plan": new_plan,
                    "is_upgrade": is_upgrade,
                },
            }
        ), 200

    except Exception as e:
        logger.error(f"Failed to change plan for user {user.id}: {e}")
        return jsonify({"success": False, "error": "Fehler beim Planwechsel"}), 500


@subscriptions_bp.route("/cancel", methods=["POST"])
@jwt_required()
def cancel_subscription() -> tuple[Response, int]:
    """Cancel the current subscription at end of billing period (§312k BGB)."""
    if not config.is_stripe_enabled():
        return jsonify(
            {
                "success": False,
                "error": "Zahlungssystem wird eingerichtet",
                "payments_available": False,
            }
        ), 503

    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

    subscription = subscription_data_service.get_subscription_by_user(user.id)
    if not subscription or not subscription.stripe_subscription_id:
        return jsonify({"success": False, "error": "Kein aktives Abonnement vorhanden."}), 400

    if subscription.cancel_at_period_end:
        return jsonify({"success": False, "error": "Abonnement wurde bereits gekündigt."}), 400

    try:
        stripe_service = StripeService()
        stripe_service.cancel_subscription(subscription.stripe_subscription_id)

        subscription_data_service.mark_subscription_canceled(subscription)

        access_until = subscription.current_period_end.isoformat() if subscription.current_period_end else None
        plan = subscription.plan.value if subscription.plan else "free"

        logger.info(f"User {user.id} canceled subscription {subscription.stripe_subscription_id}")

        return jsonify(
            {
                "success": True,
                "data": {
                    "message": "Abonnement wird zum Ende der Laufzeit gekündigt.",
                    "access_until": access_until,
                    "plan": plan,
                },
            }
        ), 200

    except Exception as e:
        logger.error(f"Failed to cancel subscription for user {user.id}: {e}")
        return jsonify({"success": False, "error": "Fehler beim Kündigen des Abonnements"}), 500


@subscriptions_bp.route("/current", methods=["GET"])
@jwt_required()
def get_current_subscription() -> tuple[Response, int]:
    """Get the current user's subscription details and usage."""
    from middleware.subscription_limit import get_subscription_usage

    user_id = get_current_user_id()
    user = subscription_data_service.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Benutzer nicht gefunden"}), 404

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
            "unlimited": usage["unlimited"],
        },
        "plan_details": SUBSCRIPTION_PLANS.get(usage["plan"], SUBSCRIPTION_PLANS["free"]),
        "has_stripe_customer": bool(user.stripe_customer_id),
    }

    # If user has a subscription record, get additional details
    if user.subscription:
        subscription_data["status"] = user.subscription.status.value
        if user.subscription.current_period_end:
            subscription_data["next_billing_date"] = user.subscription.current_period_end.isoformat()
        subscription_data["cancel_at_period_end"] = user.subscription.cancel_at_period_end
        subscription_data["canceled_at"] = (
            user.subscription.canceled_at.isoformat() if user.subscription.canceled_at else None
        )

    subscription_data["payments_available"] = config.is_stripe_enabled()

    return jsonify({"success": True, "data": subscription_data}), 200
