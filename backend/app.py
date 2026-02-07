from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

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
    Subscription,
    Template,
    TokenBlacklist,
    User,
    UserSkill,
    db,
)

# Initialize Flask-Migrate globally for CLI access
migrate = Migrate()


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

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

    # Middleware to intercept JWT responses and change status code
    @app.after_request
    def after_request(response):
        # Only process 422 responses with JSON content
        if response.status_code == 422 and response.content_type and "application/json" in response.content_type:
            try:
                # Try to parse the response data
                import json

                response_data = json.loads(response.data.decode("utf-8"))
                error_msg = response_data.get("msg", "")

                # Common JWT error patterns that should return 401
                jwt_error_patterns = [
                    "Not enough segments",
                    "Invalid header string",
                    "Invalid token",
                    "Token is invalid",
                    "Signature verification failed",
                    "Token has expired",
                    "Insufficient segments",
                ]

                for pattern in jwt_error_patterns:
                    if pattern in error_msg:
                        # Create new response with 401 status and German error message
                        from flask import Response

                        new_response = Response(
                            json.dumps({"error": "Ungültiger Token"}), status=401, mimetype="application/json"
                        )
                        # Copy headers from original response
                        for key, value in response.headers:
                            if key.lower() not in ["content-length", "content-type"]:
                                new_response.headers[key] = value
                        return new_response
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass

        return response

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
        storage_uri="memory://",
        strategy="fixed-window",
    )

    # Store limiter in app config for use in routes
    app.limiter = limiter

    # Initialize security headers middleware
    from middleware.security_headers import init_security_headers

    init_security_headers(app)

    # Register blueprints
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

    # Health check endpoint (no rate limit)
    @app.route("/api/health")
    @limiter.exempt
    def health():
        return {"status": "ok", "message": "Server running"}

    # Version endpoint
    @app.route("/api/version")
    @limiter.exempt
    def version():
        import os

        return {
            "version": os.environ.get("APP_VERSION", "development"),
            "commit": os.environ.get("APP_COMMIT", "unknown"),
        }

    return app


if __name__ == "__main__":
    app = create_app()

    # Validate config
    config.validate_config()

    # Initialize database
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
