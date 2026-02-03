#!/usr/bin/env python3
"""
Migration: Create email_accounts table for OAuth email integration.
Stores encrypted OAuth tokens for Gmail and Outlook email sending.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Create email_accounts table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if table already exists (for idempotency)
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "email_accounts" not in existing_tables:
            connection.execute(
                db.text("""
                CREATE TABLE email_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    access_token_encrypted TEXT,
                    refresh_token_encrypted TEXT,
                    token_expires_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            )
            connection.execute(db.text("CREATE INDEX idx_email_accounts_user_id ON email_accounts(user_id)"))
            print("✓ Created email_accounts table")
        else:
            print("✓ email_accounts table already exists")

        connection.commit()
        connection.close()
        print("✓ Email accounts migration completed")


def downgrade(app):
    """Drop email_accounts table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "email_accounts" in existing_tables:
            connection.execute(db.text("DROP TABLE email_accounts"))
            print("✓ Dropped email_accounts table")
        else:
            print("✓ email_accounts table does not exist")

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_email_accounts import upgrade")
