"""WSGI entry point for production deployment"""

import os

from app import create_app
from config import config

app = create_app()

# Validate config
config.validate_config()

# In production, migrations are run via entrypoint.sh (flask db upgrade).
# Only use init_database for development (local dev server).
if os.getenv("FLASK_ENV") != "production":
    with app.app_context():
        from migrations.init_db import init_database

        init_database(app)

if __name__ == "__main__":
    app.run()
