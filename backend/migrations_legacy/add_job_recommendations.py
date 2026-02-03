"""
Migration: Add job_recommendations table.

Run with: python -c "from migrations.add_job_recommendations import migrate; migrate()"
"""

from flask import Flask
from sqlalchemy import text

from config import config
from models import db


def migrate():
    """Add job_recommendations table."""
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    with app.app_context():
        # Check if table exists
        result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='job_recommendations'")
        )
        if result.fetchone():
            print("Table 'job_recommendations' already exists, skipping migration.")
            return

        # Create the table
        db.session.execute(
            text("""
            CREATE TABLE job_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                job_data_json TEXT NOT NULL,
                fit_score INTEGER NOT NULL,
                fit_category VARCHAR(50) NOT NULL,
                source VARCHAR(100),
                job_url VARCHAR(500),
                job_title VARCHAR(255),
                company_name VARCHAR(255),
                location VARCHAR(255),
                recommended_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                dismissed BOOLEAN DEFAULT 0,
                applied BOOLEAN DEFAULT 0,
                application_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
        """)
        )

        # Create index on user_id
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_job_recommendations_user_id ON job_recommendations(user_id)")
        )

        db.session.commit()
        print("Migration completed: job_recommendations table created.")


if __name__ == "__main__":
    migrate()
