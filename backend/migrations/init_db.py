#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally seeds test data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, User, Document, Template, Application, APIKey


def init_database(app):
    """Initialize database tables"""
    with app.app_context():
        # Ensure database directory exists (important for Docker volumes)
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '').lstrip('/')
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
    """Seed database with test user"""
    with app.app_context():
        # Check if test user exists
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            print("✓ Test user already exists")
            return existing_user

        # Create test user
        test_user = User(
            email='test@example.com',
            full_name='Test User',
            credits_remaining=50,
            credits_max=50
        )
        test_user.set_password('test123')

        db.session.add(test_user)
        db.session.commit()

        print(f"✓ Test user created: {test_user.email}")
        print(f"  Password: test123")
        print(f"  Credits: {test_user.credits_remaining}/{test_user.credits_max}")

        return test_user


if __name__ == '__main__':
    # This will be called from app.py context
    print("Use this script by importing: from migrations.init_db import init_database, seed_test_data")
