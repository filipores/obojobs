from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

# Import sub-modules to register route handlers on the blueprint
from routes.auth import (  # noqa: E402
    login,  # noqa: F401
    password,  # noqa: F401
    profile,  # noqa: F401
    verification,  # noqa: F401
)

# Re-export internals used by tests
from routes.auth.password import (  # noqa: E402, F401
    MAX_PASSWORD_RESET_PER_HOUR,
    _check_password_reset_rate_limit,
    _password_reset_rate_limits,
    _record_password_reset_request,
)
from routes.auth.verification import (  # noqa: E402, F401
    MAX_VERIFICATION_EMAILS_PER_HOUR,
    _check_verification_rate_limit,
    _record_verification_request,
    _verification_rate_limits,
)
