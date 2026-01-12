from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Models must be imported after db is defined to avoid circular imports
from .api_key import APIKey  # noqa: E402
from .application import Application  # noqa: E402
from .document import Document  # noqa: E402
from .purchase import Purchase  # noqa: E402
from .template import Template  # noqa: E402
from .token_blacklist import TokenBlacklist  # noqa: E402
from .user import User  # noqa: E402

__all__ = ["db", "User", "Document", "Template", "Application", "APIKey", "Purchase", "TokenBlacklist"]
