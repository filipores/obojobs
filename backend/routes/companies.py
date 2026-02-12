"""
Companies routes - Endpoints for company research and information.
"""

from typing import Any

from flask import Blueprint, Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from services.company_researcher import CompanyResearcher

companies_bp = Blueprint("companies", __name__)


@companies_bp.route("/<path:company_name>/research", methods=["GET"])
@jwt_required_custom
def research_company(company_name: str, current_user: Any) -> tuple[Response, int]:
    """Research a company and gather public information for interview preparation.

    Path params:
        - company_name: Name of the company to research (URL encoded)

    Query params:
        - website_url: Optional URL of the company website (speeds up research)
        - job_url: Optional URL of the job posting (can extract company website)
        - force_refresh: Set to 'true' to bypass cache and fetch fresh data

    Returns:
        - company_name: Name of the company
        - website_url: Company website URL (if found)
        - industry: Detected industry/sector
        - company_size: Number of employees (if found)
        - locations: List of office locations
        - products_services: List of products/services offered
        - about_text: Text from About page
        - mission_values: Company mission/values
        - founded_year: Year company was founded
        - interview_tips: Tips for using this info in interviews
        - source_urls: URLs used for research
        - cached_at: When this data was cached
    """
    if not company_name or len(company_name.strip()) < 2:
        return jsonify({"success": False, "error": "Firmenname ist erforderlich (mindestens 2 Zeichen)"}), 400

    company_name = company_name.strip()

    # Get optional parameters
    website_url = request.args.get("website_url", "").strip() or None
    job_url = request.args.get("job_url", "").strip() or None
    force_refresh = request.args.get("force_refresh", "").lower() == "true"

    try:
        researcher = CompanyResearcher()

        # Clear cache if force refresh requested
        if force_refresh:
            cache_path = researcher._get_cache_path(company_name)
            import os

            if os.path.exists(cache_path):
                os.remove(cache_path)

        # Perform research
        if job_url:
            result = researcher.research_from_job_posting(company_name, job_url)
        else:
            result = researcher.research_company(company_name, website_url)

        return jsonify({"success": True, "data": result.to_dict()}), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Firmenrecherche: {str(e)}"}), 500


@companies_bp.route("/<path:company_name>/cache-status", methods=["GET"])
@jwt_required_custom
def get_cache_status(company_name: str, current_user: Any) -> tuple[Response, int]:
    """Check if company research data is cached and when it expires.

    Path params:
        - company_name: Name of the company

    Returns:
        - is_cached: Whether data is currently cached
        - cached_at: When data was cached (if cached)
        - expires_at: When cache will expire (if cached)
    """
    import os
    from datetime import datetime, timedelta

    if not company_name:
        return jsonify({"success": False, "error": "Firmenname ist erforderlich"}), 400

    try:
        researcher = CompanyResearcher()
        cache_path = researcher._get_cache_path(company_name.strip())

        if not os.path.exists(cache_path):
            return jsonify({"success": True, "data": {"is_cached": False, "cached_at": None, "expires_at": None}}), 200

        # Load cache to get timestamp
        import json

        with open(cache_path, encoding="utf-8") as f:
            cached_data = json.load(f)

        cached_at = cached_data.get("cached_at")
        if not cached_at:
            return jsonify({"success": True, "data": {"is_cached": False, "cached_at": None, "expires_at": None}}), 200

        cached_time = datetime.fromisoformat(cached_at)
        expires_at = cached_time + timedelta(hours=researcher.CACHE_DURATION_HOURS)
        is_valid = datetime.now() < expires_at

        return jsonify(
            {
                "success": True,
                "data": {
                    "is_cached": is_valid,
                    "cached_at": cached_at,
                    "expires_at": expires_at.isoformat() if is_valid else None,
                },
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler beim Abrufen des Cache-Status: {str(e)}"}), 500
