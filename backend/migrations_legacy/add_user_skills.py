#!/usr/bin/env python3
"""
Migration: Create user_skills table for extracted CV skills.
Stores skills extracted from user's CV documents with categories and experience years.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Create user_skills table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if table already exists (for idempotency)
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "user_skills" not in existing_tables:
            connection.execute(
                db.text("""
                CREATE TABLE user_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    skill_name VARCHAR(255) NOT NULL,
                    skill_category VARCHAR(50) NOT NULL,
                    experience_years REAL,
                    source_document_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (source_document_id) REFERENCES documents(id)
                )
            """)
            )
            connection.execute(db.text("CREATE INDEX idx_user_skills_user_id ON user_skills(user_id)"))
            print("Created user_skills table")
        else:
            print("user_skills table already exists")

        connection.commit()
        connection.close()
        print("User skills migration completed")


def downgrade(app):
    """Drop user_skills table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "user_skills" in existing_tables:
            connection.execute(db.text("DROP TABLE user_skills"))
            print("Dropped user_skills table")
        else:
            print("user_skills table does not exist")

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_user_skills import upgrade")
