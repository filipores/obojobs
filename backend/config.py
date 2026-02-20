import os
from pathlib import Path

from dotenv import load_dotenv

# WICHTIG: Nur die Root-.env wird geladen. Keine backend/.env anlegen!
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


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

    # Together.xyz / Qwen API
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507-tput")
    QWEN_FAST_MODEL = os.getenv("QWEN_FAST_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct")
    QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://api.together.xyz/v1")
    QWEN_MAX_TOKENS = int(os.getenv("QWEN_MAX_TOKENS", "400"))
    QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.7"))
    QWEN_ANSCHREIBEN_MAX_TOKENS = int(os.getenv("QWEN_ANSCHREIBEN_MAX_TOKENS", "1200"))
    QWEN_ANSCHREIBEN_TEMPERATURE = float(os.getenv("QWEN_ANSCHREIBEN_TEMPERATURE", "0.65"))

    # Kimi K2.5 (reasoning model via Fireworks AI)
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    KIMI_API_BASE = os.getenv("KIMI_API_BASE", "https://api.fireworks.ai/inference/v1")
    KIMI_MODEL = os.getenv("KIMI_MODEL", "accounts/fireworks/models/kimi-k2p5")
    KIMI_MAX_TOKENS = int(os.getenv("KIMI_MAX_TOKENS", "12000"))
    KIMI_TEMPERATURE = float(os.getenv("KIMI_TEMPERATURE", "1.0"))
    KIMI_THINKING_BUDGET = int(os.getenv("KIMI_THINKING_BUDGET", "4096"))

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

    # Stripe One-Time Purchase Plans (Price IDs from Stripe Dashboard)
    STRIPE_PRICE_STARTER = os.getenv(
        "STRIPE_PRICE_STARTER", os.getenv("STRIPE_PRICE_BASIC", "price_dev_starter_mock")
    )  # €9.90 one-time
    STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_dev_pro_mock")  # €19.90 one-time

    @staticmethod
    def is_stripe_enabled():
        """Check if Stripe payments are properly configured."""
        return bool(
            Config.STRIPE_SECRET_KEY
            and not Config.STRIPE_PRICE_STARTER.startswith("price_dev_")
            and not Config.STRIPE_PRICE_PRO.startswith("price_dev_")
        )

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Email (SMTP)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # Legal / Impressum
    COMPANY_NAME = os.getenv("COMPANY_NAME", "obo - Filip Ores")
    COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "Nöltingstraße 31")
    COMPANY_POSTAL_CODE = os.getenv("COMPANY_POSTAL_CODE", "22765")
    COMPANY_CITY = os.getenv("COMPANY_CITY", "Hamburg")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "kontakt@obojobs.de")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE", "")

    # Rate Limiting
    RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    RATE_LIMIT_WHITELIST = os.getenv("RATE_LIMIT_WHITELIST", "127.0.0.1").split(",")

    @staticmethod
    def validate_config():
        """Validate required configuration"""
        if not Config.TOGETHER_API_KEY:
            raise ValueError("TOGETHER_API_KEY environment variable is required")

        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        print("✓ Configuration validated")


def _check_production_secrets():
    """Raise ValueError if default secrets are used in production."""
    flask_env = os.getenv("FLASK_ENV", "development")
    if flask_env == "production":
        if Config.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY must be changed from its default value in production. "
                "Set a strong, unique SECRET_KEY environment variable."
            )
        if Config.JWT_SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError(
                "JWT_SECRET_KEY must be changed from its default value in production. "
                "Set a strong, unique JWT_SECRET_KEY environment variable."
            )


_check_production_secrets()

config = Config()
