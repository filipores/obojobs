from flask import Blueprint

applications_bp = Blueprint("applications", __name__)

# Import sub-modules to register route handlers on the blueprint
from routes.applications import (  # noqa: E402
    ats,  # noqa: F401
    crud,  # noqa: F401
    export,  # noqa: F401
    generation,  # noqa: F401
    interview,  # noqa: F401
    requirements,  # noqa: F401
    scraping,  # noqa: F401
)
