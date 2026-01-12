#!/usr/bin/env python3
"""
Migration: Add account lockout fields to users table.
Fields: failed_login_attempts, locked_until
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def upgrade(app):
    """Add account lockout columns to users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if columns already exist (for idempotency)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        if 'failed_login_attempts' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
            )
            print("✓ Added failed_login_attempts column")
        else:
            print("✓ failed_login_attempts column already exists")

        if 'locked_until' not in existing_columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN locked_until DATETIME")
            )
            print("✓ Added locked_until column")
        else:
            print("✓ locked_until column already exists")

        connection.commit()
        connection.close()
        print("✓ Account lockout migration completed")


def downgrade(app):
    """Remove account lockout columns from users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # SQLite doesn't support DROP COLUMN directly, so we skip for SQLite
        # For production with PostgreSQL, this would work
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_uri:
            print("⚠ SQLite does not support DROP COLUMN. Skipping downgrade.")
            return

        connection.execute(db.text("ALTER TABLE users DROP COLUMN failed_login_attempts"))
        connection.execute(db.text("ALTER TABLE users DROP COLUMN locked_until"))
        connection.commit()
        connection.close()
        print("✓ Account lockout columns removed")


if __name__ == '__main__':
    print("Use this script by importing: from migrations.add_account_lockout import upgrade")
