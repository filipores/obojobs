#!/usr/bin/env python3
"""
Migration: Create job_requirements table for extracted job posting requirements.
Stores requirements extracted from job postings with type (must_have/nice_to_have) and skill category.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Create job_requirements table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if table already exists (for idempotency)
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "job_requirements" not in existing_tables:
            connection.execute(
                db.text("""
                CREATE TABLE job_requirements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    requirement_text TEXT NOT NULL,
                    requirement_type VARCHAR(20) NOT NULL,
                    skill_category VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
                )
            """)
            )
            connection.execute(
                db.text("CREATE INDEX idx_job_requirements_application_id ON job_requirements(application_id)")
            )
            print("Created job_requirements table")
        else:
            print("job_requirements table already exists")

        connection.commit()
        connection.close()
        print("Job requirements migration completed")


def downgrade(app):
    """Drop job_requirements table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "job_requirements" in existing_tables:
            connection.execute(db.text("DROP TABLE job_requirements"))
            print("Dropped job_requirements table")
        else:
            print("job_requirements table does not exist")

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_job_requirements import upgrade")
