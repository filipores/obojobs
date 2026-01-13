import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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

    # File uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
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

    # Credits
    DEFAULT_CREDITS = 5  # Changed from 50 to 5 (free credits)

    # PayPal (Legacy - to be removed)
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
    PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Stripe Subscription Plans (Price IDs from Stripe Dashboard)
    STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC")  # €9.99/month
    STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")  # €19.99/month

    # Credit Packages
    CREDIT_PACKAGES = {
        "small": {"credits": 10, "price": 1.00, "name": "Small Paket"},
        "medium": {"credits": 50, "price": 4.00, "name": "Medium Paket"},
        "large": {"credits": 100, "price": 7.00, "name": "Large Paket"},
    }

    @staticmethod
    def validate_config():
        """Validate required configuration"""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        print("✓ Configuration validated")


config = Config()
