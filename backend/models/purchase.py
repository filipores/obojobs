from datetime import datetime

from . import db


class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Package Info
    package_name = db.Column(db.String(50), nullable=False)
    credits_purchased = db.Column(db.Integer, nullable=False)
    price_eur = db.Column(db.Numeric(10, 2), nullable=False)

    # PayPal Info
    paypal_order_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    paypal_payer_id = db.Column(db.String(255))
    paypal_payer_email = db.Column(db.String(255))

    # Status
    status = db.Column(db.String(50), default='pending', index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationship
    user = db.relationship('User', back_populates='purchases')

    def to_dict(self):
        return {
            'id': self.id,
            'package_name': self.package_name,
            'credits_purchased': self.credits_purchased,
            'price_eur': float(self.price_eur),
            'status': self.status,
            'paypal_order_id': self.paypal_order_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
