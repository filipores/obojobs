#!/usr/bin/env python3
"""
Migration: Add status_history field to applications table.
Tracks all status changes with timestamps for timeline view.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Add status_history column to applications table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("applications")]

        # Add status_history column if it doesn't exist
        if "status_history" not in columns:
            connection.execute(db.text("ALTER TABLE applications ADD COLUMN status_history TEXT"))
            print("✓ Added status_history column to applications table")
        else:
            print("✓ status_history column already exists")

        connection.commit()
        connection.close()
        print("✓ Status history migration completed")


def downgrade(app):
    """Remove status_history column from applications table"""

    with app.app_context():
        # SQLite doesn't support DROP COLUMN directly
        print("Note: SQLite doesn't support DROP COLUMN. Column will remain.")


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_status_history import upgrade")
