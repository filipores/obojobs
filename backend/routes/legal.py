from flask import Blueprint, jsonify

from config import config

legal_bp = Blueprint("legal", __name__)


@legal_bp.route("/info", methods=["GET"])
def legal_info():
    """Return legal/company info from environment variables. Public endpoint."""
    return jsonify(
        {
            "company_name": config.COMPANY_NAME,
            "company_address": config.COMPANY_ADDRESS,
            "company_postal_code": config.COMPANY_POSTAL_CODE,
            "company_city": config.COMPANY_CITY,
            "company_email": config.COMPANY_EMAIL,
            "company_phone": config.COMPANY_PHONE,
        }
    )
