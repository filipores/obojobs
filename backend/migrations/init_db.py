#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally seeds test data.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import all models to ensure all tables are created
from models import Subscription, User, db
from models.subscription import SubscriptionPlan, SubscriptionStatus


def init_database(app):
    """Initialize database tables"""
    with app.app_context():
        # Ensure database directory exists (important for Docker volumes)
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "").lstrip("/")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"✓ Created database directory: {db_dir}")

        print("Creating database tables...")
        try:
            db.create_all()
            print("✓ Database tables created successfully")
        except Exception as e:
            # Handle race condition when multiple workers try to create tables
            if "already exists" in str(e).lower():
                print("✓ Database tables already exist (created by another worker)")
            else:
                print(f"Error creating tables: {e}")
                raise


def seed_test_data(app):
    """Seed database with test user for development/testing"""
    if os.getenv("FLASK_ENV") == "production":
        print("⚠ Skipping seed_test_data in production environment")
        return None

    with app.app_context():
        # Check if test user exists
        existing_user = User.query.filter_by(email="test@example.com").first()
        if existing_user:
            print("✓ Test user already exists")
            return existing_user

        # Create test user
        test_user = User(
            email="test@example.com",
            full_name="Test User",
            display_name="Tester",
            email_verified=True,  # Pre-verified for easier testing
        )
        test_user.set_password("Test1234!")

        db.session.add(test_user)
        db.session.flush()  # Get user ID

        # Create Pro subscription for test user
        test_subscription = Subscription(
            user_id=test_user.id,
            plan=SubscriptionPlan.pro,
            status=SubscriptionStatus.active,
        )
        db.session.add(test_subscription)

        db.session.commit()

        print(f"✓ Test user created: {test_user.email}")
        print("  Password: Test1234!")
        print(f"  Subscription: {test_subscription.plan.value} ({test_subscription.status.value})")

        return test_user


if __name__ == "__main__":
    print("Use this script by importing: from migrations.init_db import init_database, seed_test_data")
