#!/usr/bin/env python3
"""
Migration script to import data from bewerbungen.json into SQLite database.
"""
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.models import Application, User, db


def migrate_bewerbungen_json(app, user_email='migration@example.com', json_path='bewerbungen.json'):
    """
    Migrate bewerbungen.json data to database.

    Args:
        app: Flask app instance
        user_email: Email of user to assign applications to
        json_path: Path to bewerbungen.json file
    """
    with app.app_context():
        # Find or create migration user
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"Creating migration user: {user_email}")
            user = User(
                email=user_email,
                full_name='Migration User',
                credits_remaining=50,
                credits_max=50
            )
            user.set_password('migration123')
            db.session.add(user)
            db.session.commit()
            print("✓ Migration user created")

        # Load bewerbungen.json
        if not os.path.exists(json_path):
            print(f"✗ File not found: {json_path}")
            return

        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        print(f"Found {len(data)} applications to migrate")

        # Migrate each application
        migrated = 0
        for bew in data:
            # Parse datum
            try:
                datum = datetime.strptime(bew['datum'], '%Y-%m-%d %H:%M')
            except (ValueError, KeyError):
                datum = datetime.utcnow()

            # Create application
            app_obj = Application(
                user_id=user.id,
                datum=datum,
                firma=bew.get('firma', ''),
                position=bew.get('position', ''),
                ansprechpartner=bew.get('ansprechpartner', ''),
                email=bew.get('email', ''),
                quelle=bew.get('quelle', ''),
                status=bew.get('status', 'erstellt'),
                pdf_path=bew.get('pdf_pfad', ''),
                betreff=bew.get('betreff', ''),
                email_text=bew.get('email_text', ''),
                notizen=bew.get('notizen', ''),
                links_json=json.dumps(bew.get('links', {}))
            )
            db.session.add(app_obj)
            migrated += 1

        db.session.commit()
        print(f"✓ Migrated {migrated} applications to user: {user_email}")
        print(f"  User ID: {user.id}")


if __name__ == '__main__':
    print("Use this script by importing: from migrations.migrate_json import migrate_bewerbungen_json")
