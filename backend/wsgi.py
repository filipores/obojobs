"""WSGI entry point for production deployment"""
from app import create_app
from config import config

app = create_app()

# Validate config
config.validate_config()

# Initialize database
with app.app_context():
    from migrations.init_db import init_database
    init_database(app)

if __name__ == "__main__":
    app.run()
