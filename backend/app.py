import atexit
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config

# Import all models for Flask-Migrate to detect them
from models import (  # noqa: F401
    APIKey,
    Application,
    ATSAnalysis,
    Document,
    EmailAccount,
    InterviewQuestion,
    JobRecommendation,
    JobRequirement,
    SalaryCoachData,
    SeeleAntwort,
    SeeleProfile,
    SeeleSession,
    Subscription,
    Template,
    TokenBlacklist,
    User,
    UserSkill,
    WebhookEvent,
    db,
)

# Initialize Flask-Migrate globally for CLI access
migrate = Migrate()


def create_app():
    """Create and configure Flask application"""
    # Enable debugpy in dev containers (only in reloader's child process)
    if os.environ.get("DEBUGPY_ENABLE") and os.environ.get("WERKZEUG_RUN_MAIN"):
        import debugpy

        debugpy.listen(("0.0.0.0", 5678))

    app = Flask(__name__)

    # Trust X-Forwarded-For from reverse proxy (Caddy)
    # x_for=1: trust 1 proxy hop for the client IP
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Load configuration
    app.config.from_object(config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=config.CORS_ORIGINS)
    jwt = JWTManager(app)

    # Register JWT token blacklist callback
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return TokenBlacklist.is_token_blacklisted(jti)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token wurde widerrufen"}), 401

    # Handle invalid/expired JWT tokens
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({"error": "Ungültiger Token"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token ist abgelaufen"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return jsonify({"error": "Token fehlt"}), 401

    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Ungültiger Token"}), 401

    # Custom key function that exempts whitelisted IPs
    def get_rate_limit_key():
        remote_addr = get_remote_address()
        # Return None to exempt whitelisted IPs from rate limiting
        if remote_addr in config.RATE_LIMIT_WHITELIST:
            return None
        return remote_addr

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_rate_limit_key,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri=config.RATE_LIMIT_STORAGE_URI,
        strategy="fixed-window",
    )

    # Store limiter in app config for use in routes
    app.limiter = limiter

    # Initialize security headers middleware
    from middleware.security_headers import init_security_headers

    init_security_headers(app)

    # Register blueprints
    from routes.admin import admin_bp
    from routes.api_keys import api_keys_bp
    from routes.applications import applications_bp
    from routes.ats import ats_bp
    from routes.auth import auth_bp
    from routes.companies import companies_bp
    from routes.demo import demo_bp
    from routes.documents import documents_bp
    from routes.email import email_bp
    from routes.legal import legal_bp
    from routes.recommendations import bp as recommendations_bp
    from routes.salary import salary_bp
    from routes.seele import seele_bp
    from routes.skills import skills_bp
    from routes.stats import stats_bp
    from routes.subscriptions import subscriptions_bp
    from routes.templates import templates_bp
    from routes.webhooks import webhooks_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(demo_bp, url_prefix="/api/demo")
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(templates_bp, url_prefix="/api/templates")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(api_keys_bp, url_prefix="/api/keys")
    app.register_blueprint(stats_bp, url_prefix="/api")
    app.register_blueprint(subscriptions_bp, url_prefix="/api/subscriptions")
    app.register_blueprint(ats_bp, url_prefix="/api/ats")
    app.register_blueprint(email_bp, url_prefix="/api/email")
    app.register_blueprint(webhooks_bp, url_prefix="/api/webhooks")
    app.register_blueprint(skills_bp, url_prefix="/api")
    app.register_blueprint(companies_bp, url_prefix="/api/companies")
    app.register_blueprint(recommendations_bp, url_prefix="/api")
    app.register_blueprint(salary_bp, url_prefix="/api/salary")
    app.register_blueprint(legal_bp, url_prefix="/api/legal")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(seele_bp, url_prefix="/api/seele")

    # Initialize background scheduler
    from services.scheduler import init_scheduler, shutdown_scheduler

    init_scheduler(app)
    atexit.register(shutdown_scheduler)

    # Health check endpoint (no rate limit)
    @app.route("/api/health")
    @limiter.exempt
    def health():
        return {"status": "ok", "message": "Server running"}

    # Version endpoint
    @app.route("/api/version")
    @limiter.exempt
    def version():
        return {
            "version": os.environ.get("APP_VERSION", "development"),
            "commit": os.environ.get("APP_COMMIT", "unknown"),
        }

    return app


if __name__ == "__main__":
    app = create_app()

    # Validate config
    config.validate_config()

    # Initialize database (only in development)
    if os.getenv("FLASK_ENV") != "production":
        with app.app_context():
            from migrations.init_db import init_database, seed_test_data

            init_database(app)
            seed_test_data(app)

    print("\n" + "=" * 60)
    print("obojobs API Server")
    print("=" * 60)
    print("Server running on http://localhost:5002")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5002, debug=config.DEBUG)
