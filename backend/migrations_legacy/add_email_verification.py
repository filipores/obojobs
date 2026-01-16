#!/usr/bin/env python3
"""
Migration: Add email verification fields to users table.
Fields: email_verified, email_verification_token, email_verification_sent_at
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def upgrade(app):
    """Add email verification columns to users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if columns already exist (for idempotency)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        if 'email_verified' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE")
            )
            print("✓ Added email_verified column")
        else:
            print("✓ email_verified column already exists")

        if 'email_verification_token' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(255)")
            )
            print("✓ Added email_verification_token column")
        else:
            print("✓ email_verification_token column already exists")

        if 'email_verification_sent_at' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN email_verification_sent_at DATETIME")
            )
            print("✓ Added email_verification_sent_at column")
        else:
            print("✓ email_verification_sent_at column already exists")

        connection.commit()
        connection.close()
        print("✓ Email verification migration completed")


def downgrade(app):
    """Remove email verification columns from users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # SQLite doesn't support DROP COLUMN directly, so we skip for SQLite
        # For production with PostgreSQL, this would work
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_uri:
            print("⚠ SQLite does not support DROP COLUMN. Skipping downgrade.")
            return

        connection.execute(db.text("ALTER TABLE users DROP COLUMN email_verified"))
        connection.execute(db.text("ALTER TABLE users DROP COLUMN email_verification_token"))
        connection.execute(db.text("ALTER TABLE users DROP COLUMN email_verification_sent_at"))
        connection.commit()
        connection.close()
        print("✓ Email verification columns removed")


if __name__ == '__main__':
    print("Use this script by importing: from migrations.add_email_verification import upgrade")
