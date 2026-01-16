#!/usr/bin/env python3
"""
Migration: Add interview tracking fields to applications table.
Tracks interview date, result, and personal feedback.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Add interview tracking columns to applications table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("applications")]

        # Add interview_date column if it doesn't exist
        if "interview_date" not in columns:
            connection.execute(
                db.text("ALTER TABLE applications ADD COLUMN interview_date DATETIME")
            )
            print("✓ Added interview_date column to applications table")
        else:
            print("✓ interview_date column already exists")

        # Add interview_feedback column if it doesn't exist
        if "interview_feedback" not in columns:
            connection.execute(
                db.text("ALTER TABLE applications ADD COLUMN interview_feedback TEXT")
            )
            print("✓ Added interview_feedback column to applications table")
        else:
            print("✓ interview_feedback column already exists")

        # Add interview_result column if it doesn't exist
        if "interview_result" not in columns:
            connection.execute(
                db.text("ALTER TABLE applications ADD COLUMN interview_result VARCHAR(50)")
            )
            print("✓ Added interview_result column to applications table")
        else:
            print("✓ interview_result column already exists")

        connection.commit()
        connection.close()
        print("✓ Interview tracking migration completed")


def downgrade(app):
    """Remove interview tracking columns from applications table"""

    with app.app_context():
        # SQLite doesn't support DROP COLUMN directly
        print("Note: SQLite doesn't support DROP COLUMN. Columns will remain.")


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_interview_tracking import upgrade")
