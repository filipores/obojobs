#!/usr/bin/env python3
"""
Migration: Add sent_at and sent_via fields to applications table.
Tracks when and via which provider an application email was sent.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Add sent_at and sent_via columns to applications table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("applications")]

        # Add sent_at column if it doesn't exist
        if "sent_at" not in columns:
            connection.execute(
                db.text("ALTER TABLE applications ADD COLUMN sent_at DATETIME")
            )
            print("✓ Added sent_at column to applications table")
        else:
            print("✓ sent_at column already exists")

        # Add sent_via column if it doesn't exist
        if "sent_via" not in columns:
            connection.execute(
                db.text("ALTER TABLE applications ADD COLUMN sent_via VARCHAR(50)")
            )
            print("✓ Added sent_via column to applications table")
        else:
            print("✓ sent_via column already exists")

        connection.commit()
        connection.close()
        print("✓ Application sent tracking migration completed")


def downgrade(app):
    """Remove sent_at and sent_via columns from applications table"""

    with app.app_context():
        # SQLite doesn't support DROP COLUMN directly
        # We would need to recreate the table, but for simplicity we'll skip this
        print("Note: SQLite doesn't support DROP COLUMN. Columns will remain.")


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_application_sent_tracking import upgrade")
