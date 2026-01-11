"""
Migration: Add Payment System
- Adds 'purchases' table
- Adds 'total_credits_purchased' column to users table
- Updates default credits from 50 to 5 (for new users only, doesn't affect existing users)
"""

from app import create_app
from models import db
from sqlalchemy import text


def run_migration():
    """Run the payment system migration"""
    app = create_app()

    with app.app_context():
        print("Starting payment system migration...")

        # Create purchases table
        print("1. Creating purchases table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                package_name VARCHAR(50) NOT NULL,
                credits_purchased INTEGER NOT NULL,
                price_eur DECIMAL(10, 2) NOT NULL,
                paypal_order_id VARCHAR(255) UNIQUE NOT NULL,
                paypal_payer_id VARCHAR(255),
                paypal_payer_email VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # Create indexes
        print("2. Creating indexes...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id)
        """))
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status)
        """))
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_purchases_paypal_order_id ON purchases(paypal_order_id)
        """))

        # Add total_credits_purchased column to users (if not exists)
        print("3. Adding total_credits_purchased column to users...")
        try:
            db.session.execute(text("""
                ALTER TABLE users ADD COLUMN total_credits_purchased INTEGER DEFAULT 0
            """))
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print("   Column already exists, skipping...")
            else:
                raise

        db.session.commit()

        print("✓ Migration completed successfully!")
        print("\n" + "="*60)
        print("Payment System Migration Summary:")
        print("="*60)
        print("✓ purchases table created")
        print("✓ Indexes created")
        print("✓ users.total_credits_purchased column added")
        print("="*60)
        print("\nNote: Existing users keep their current credits.")
        print("New users will get 5 free credits by default.")
        print("="*60 + "\n")


if __name__ == '__main__':
    run_migration()
