#!/usr/bin/env python3
"""
Migration: Create interview_questions table for generated interview questions.
Stores interview questions with type, difficulty, and sample answers.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Create interview_questions table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if table already exists (for idempotency)
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "interview_questions" not in existing_tables:
            connection.execute(
                db.text("""
                CREATE TABLE interview_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type VARCHAR(30) NOT NULL,
                    difficulty VARCHAR(20) DEFAULT 'medium',
                    sample_answer TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
                )
            """)
            )
            connection.execute(db.text("CREATE INDEX idx_interview_questions_application_id ON interview_questions(application_id)"))
            print("Created interview_questions table")
        else:
            print("interview_questions table already exists")

        connection.commit()
        connection.close()
        print("Interview questions migration completed")


def downgrade(app):
    """Drop interview_questions table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "interview_questions" in existing_tables:
            connection.execute(db.text("DROP TABLE interview_questions"))
            print("Dropped interview_questions table")
        else:
            print("interview_questions table does not exist")

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_interview_questions import upgrade")
