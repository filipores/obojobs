#!/usr/bin/env python3
"""
Migration: Add subscription usage tracking fields to users table.
Adds applications_this_month and month_reset_at for tracking monthly limits.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Add subscription usage fields to users table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("users")]

        # Add applications_this_month column
        if "applications_this_month" not in columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN applications_this_month INTEGER NOT NULL DEFAULT 0")
            )
            print("✓ Added applications_this_month to users table")
        else:
            print("✓ applications_this_month already exists in users table")

        # Add month_reset_at column
        if "month_reset_at" not in columns:
            connection.execute(db.text("ALTER TABLE users ADD COLUMN month_reset_at DATETIME"))
            print("✓ Added month_reset_at to users table")
        else:
            print("✓ month_reset_at already exists in users table")

        connection.commit()
        connection.close()
        print("✓ Subscription usage migration completed")


def downgrade(app):
    """Remove subscription usage fields from users table"""

    with app.app_context():
        # Note: SQLite doesn't support DROP COLUMN directly
        # For production, you'd need to recreate the table without the columns
        print("⚠ Note: columns not removed (SQLite limitation)")
        print("  - applications_this_month")
        print("  - month_reset_at")


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_subscription_usage import upgrade")
