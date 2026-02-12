from flask import Blueprint

email_bp = Blueprint("email", __name__)

# Import sub-modules to register route handlers on the blueprint
from routes.email import (  # noqa: E402
    accounts,  # noqa: F401
    oauth,  # noqa: F401
    send,  # noqa: F401
)
