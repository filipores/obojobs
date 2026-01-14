#!/usr/bin/env python3
"""
Migration: Add password reset fields to users table.
Fields: password_reset_token, password_reset_sent_at
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def upgrade(app):
    """Add password reset columns to users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if columns already exist (for idempotency)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        if 'password_reset_token' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255)")
            )
            print("✓ Added password_reset_token column")
        else:
            print("✓ password_reset_token column already exists")

        if 'password_reset_sent_at' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN password_reset_sent_at DATETIME")
            )
            print("✓ Added password_reset_sent_at column")
        else:
            print("✓ password_reset_sent_at column already exists")

        connection.commit()
        connection.close()
        print("✓ Password reset migration completed")


def downgrade(app):
    """Remove password reset columns from users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # SQLite doesn't support DROP COLUMN directly, so we skip for SQLite
        # For production with PostgreSQL, this would work
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_uri:
            print("⚠ SQLite does not support DROP COLUMN. Skipping downgrade.")
            return

        connection.execute(db.text("ALTER TABLE users DROP COLUMN password_reset_token"))
        connection.execute(db.text("ALTER TABLE users DROP COLUMN password_reset_sent_at"))
        connection.commit()
        connection.close()
        print("✓ Password reset columns removed")


if __name__ == '__main__':
    print("Use this script by importing: from migrations.add_password_reset import upgrade")
