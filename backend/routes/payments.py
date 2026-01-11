from datetime import datetime

from flask import Blueprint, request, jsonify

from config import config
from middleware.jwt_required import jwt_required_custom
from models import db, Purchase
from services.paypal_service import PayPalService

payments_bp = Blueprint('payments', __name__)
paypal_service = PayPalService()


@payments_bp.route('/packages', methods=['GET'])
def get_packages():
    """Get available credit packages (public endpoint)"""
    packages = []
    for key, pkg in config.CREDIT_PACKAGES.items():
        packages.append({
            'id': key,
            'name': pkg['name'],
            'credits': pkg['credits'],
            'price': pkg['price'],
            'price_per_credit': round(pkg['price'] / pkg['credits'], 2)
        })

    return jsonify({
        'success': True,
        'packages': packages
    }), 200


@payments_bp.route('/create-order', methods=['POST'])
@jwt_required_custom
def create_order(current_user):
    """Create PayPal payment order"""
    data = request.json
    package_name = data.get('package')

    if package_name not in config.CREDIT_PACKAGES:
        return jsonify({'error': 'Invalid package'}), 400

    package = config.CREDIT_PACKAGES[package_name]

    # Frontend URLs
    return_url = data.get('return_url', 'http://localhost:3000/payment/success')
    cancel_url = data.get('cancel_url', 'http://localhost:3000/buy-credits')

    try:
        # Create PayPal order
        result = paypal_service.create_order(package_name, return_url, cancel_url)

        # Create pending purchase record
        purchase = Purchase(
            user_id=current_user.id,
            package_name=package_name,
            credits_purchased=package['credits'],
            price_eur=package['price'],
            paypal_order_id=result['payment_id'],
            status='pending'
        )
        db.session.add(purchase)
        db.session.commit()

        return jsonify({
            'success': True,
            'payment_id': result['payment_id'],
            'approval_url': result['approval_url'],
            'purchase_id': purchase.id
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error creating payment order: {str(e)}")
        return jsonify({'error': f'Payment creation failed: {str(e)}'}), 500


@payments_bp.route('/execute-payment', methods=['POST'])
@jwt_required_custom
def execute_payment(current_user):
    """Execute/Capture PayPal payment after user approval"""
    data = request.json
    payment_id = data.get('payment_id')
    payer_id = data.get('payer_id')

    if not payment_id or not payer_id:
        return jsonify({'error': 'Missing payment_id or payer_id'}), 400

    # Find purchase record
    purchase = Purchase.query.filter_by(
        paypal_order_id=payment_id,
        user_id=current_user.id
    ).first()

    if not purchase:
        return jsonify({'error': 'Purchase not found'}), 404

    if purchase.status == 'completed':
        return jsonify({'error': 'Payment already completed'}), 400

    try:
        # Execute payment with PayPal
        result = paypal_service.execute_payment(payment_id, payer_id)

        # Update purchase record
        purchase.status = 'completed'
        purchase.paypal_payer_id = payer_id
        purchase.paypal_payer_email = result.get('payer_email')
        purchase.completed_at = datetime.utcnow()

        # Add credits to user
        current_user.credits_remaining += purchase.credits_purchased
        current_user.total_credits_purchased += purchase.credits_purchased

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{purchase.credits_purchased} Credits erfolgreich gekauft!',
            'new_credits': current_user.credits_remaining,
            'purchase': purchase.to_dict()
        }), 200

    except Exception as e:
        print(f"Error executing payment: {str(e)}")
        purchase.status = 'failed'
        db.session.commit()
        return jsonify({'error': f'Payment execution failed: {str(e)}'}), 500


@payments_bp.route('/history', methods=['GET'])
@jwt_required_custom
def get_purchase_history(current_user):
    """Get user's purchase history"""
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(
        Purchase.created_at.desc()
    ).all()

    total_spent = sum(
        float(p.price_eur) for p in purchases if p.status == 'completed'
    )

    return jsonify({
        'success': True,
        'purchases': [p.to_dict() for p in purchases],
        'total_spent': round(total_spent, 2)
    }), 200


@payments_bp.route('/cancel', methods=['POST'])
@jwt_required_custom
def cancel_payment(current_user):
    """Mark a payment as cancelled"""
    data = request.json
    payment_id = data.get('payment_id')

    if not payment_id:
        return jsonify({'error': 'Missing payment_id'}), 400

    purchase = Purchase.query.filter_by(
        paypal_order_id=payment_id,
        user_id=current_user.id
    ).first()

    if purchase and purchase.status == 'pending':
        purchase.status = 'cancelled'
        db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Payment cancelled'
    }), 200
