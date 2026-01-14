#!/usr/bin/env python3
"""
Migration: Create subscriptions table and add stripe_customer_id to users.
Implements Stripe subscription system for SaaS model.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def upgrade(app):
    """Create subscriptions table and add stripe_customer_id to users"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # Create subscriptions table
        if "subscriptions" not in existing_tables:
            connection.execute(
                db.text("""
                CREATE TABLE subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    stripe_customer_id VARCHAR(255),
                    stripe_subscription_id VARCHAR(255) UNIQUE,
                    plan VARCHAR(50) NOT NULL DEFAULT 'free',
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    current_period_start DATETIME,
                    current_period_end DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            )
            connection.execute(
                db.text("CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id)")
            )
            connection.execute(
                db.text("CREATE INDEX idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id)")
            )
            connection.execute(
                db.text("CREATE UNIQUE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id)")
            )
            print("✓ Created subscriptions table")
        else:
            print("✓ subscriptions table already exists")

        # Add stripe_customer_id to users table
        # Note: SQLite cannot add UNIQUE columns directly, so we add without UNIQUE
        # and create a unique index instead
        columns = [col["name"] for col in inspector.get_columns("users")]
        if "stripe_customer_id" not in columns:
            connection.execute(
                db.text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255)")
            )
            connection.execute(
                db.text("CREATE UNIQUE INDEX idx_users_stripe_customer_id ON users(stripe_customer_id)")
            )
            print("✓ Added stripe_customer_id to users table")
        else:
            print("✓ stripe_customer_id already exists in users table")

        connection.commit()
        connection.close()
        print("✓ Subscription migration completed")


def downgrade(app):
    """Drop subscriptions table and stripe_customer_id from users"""
    from models import db

    with app.app_context():
        connection = db.engine.connect()

        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # Drop subscriptions table
        if "subscriptions" in existing_tables:
            connection.execute(db.text("DROP TABLE subscriptions"))
            print("✓ Dropped subscriptions table")
        else:
            print("✓ subscriptions table does not exist")

        # Note: SQLite doesn't support DROP COLUMN directly
        # For production, you'd need to recreate the table without the column
        print("⚠ Note: stripe_customer_id column not removed (SQLite limitation)")

        connection.commit()
        connection.close()


if __name__ == "__main__":
    print("Use this script by importing: from migrations.add_subscription import upgrade")
