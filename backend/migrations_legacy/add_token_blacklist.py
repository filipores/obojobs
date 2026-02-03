#!/usr/bin/env python3
"""
Migration: Create token_blacklist table for JWT invalidation.
Used for implementing logout functionality.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Create token_blacklist table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        # Check if table already exists (for idempotency)
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "token_blacklist" not in existing_tables:
            connection.execute(
                db.text("""
                CREATE TABLE token_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jti VARCHAR(36) UNIQUE NOT NULL,
                    token_type VARCHAR(10) NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            )
            connection.execute(db.text("CREATE INDEX idx_token_blacklist_jti ON token_blacklist(jti)"))
            print("✓ Created token_blacklist table")
        else:
            print("✓ token_blacklist table already exists")

        connection.commit()
        connection.close()
        print("✓ Token blacklist migration completed")


def downgrade(app):
    """Drop token_blacklist table"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "token_blacklist" in existing_tables:
            connection.execute(db.text("DROP TABLE token_blacklist"))
            print("✓ Dropped token_blacklist table")
        else:
            print("✓ token_blacklist table does not exist")

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_token_blacklist import upgrade")
