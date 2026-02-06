import os

from dotenv import load_dotenv

# Load environment variables from project root .env (single source of truth)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///obojobs.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days

    # File uploads - resolve relative paths against project root (parent of backend/)
    _upload_folder_env = os.getenv("UPLOAD_FOLDER", "uploads")
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = (
        _upload_folder_env
        if os.path.isabs(_upload_folder_env)
        else os.path.join(os.path.dirname(_backend_dir), _upload_folder_env)
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {"pdf"}  # Nur PDFs erlaubt

    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = "claude-3-5-haiku-20241022"
    MAX_TOKENS = 300
    TEMPERATURE = 0.7
    USE_EXTRACTION = True

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # Security Headers (only in production by default)
    SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "false").lower() == "true"
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"

    # Registration (set to "false" to disable public registration)
    REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "true").lower() == "true"

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Stripe Subscription Plans (Price IDs from Stripe Dashboard)
    STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC", "price_dev_basic_mock")  # €9.99/month
    STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_dev_pro_mock")  # €19.99/month

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Email (SMTP)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # Rate Limit Whitelist (comma-separated IPs that bypass rate limiting)
    RATE_LIMIT_WHITELIST = os.getenv("RATE_LIMIT_WHITELIST", "127.0.0.1").split(",")

    @staticmethod
    def validate_config():
        """Validate required configuration"""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        print("✓ Configuration validated")


config = Config()
