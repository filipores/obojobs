from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Models must be imported after db is defined to avoid circular imports
from .api_key import APIKey  # noqa: E402
from .application import Application  # noqa: E402
from .ats_analysis import ATSAnalysis  # noqa: E402
from .document import Document  # noqa: E402
from .email_account import EmailAccount, decrypt_token, encrypt_token  # noqa: E402
from .subscription import Subscription, SubscriptionPlan, SubscriptionStatus  # noqa: E402
from .template import Template  # noqa: E402
from .token_blacklist import TokenBlacklist  # noqa: E402
from .user import User  # noqa: E402
from .user_skill import UserSkill  # noqa: E402

__all__ = [
    "db",
    "User",
    "Document",
    "Template",
    "Application",
    "APIKey",
    "Subscription",
    "SubscriptionPlan",
    "SubscriptionStatus",
    "TokenBlacklist",
    "ATSAnalysis",
    "EmailAccount",
    "encrypt_token",
    "decrypt_token",
    "UserSkill",
]
