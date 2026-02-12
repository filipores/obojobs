"""
Salary routes - Endpoints for salary research and negotiation coaching.
"""

from flask import Blueprint, jsonify, request

from middleware.jwt_required import jwt_required_custom
from services import salary_data_service
from services.salary_coach import SalaryCoach

salary_bp = Blueprint("salary", __name__)


@salary_bp.route("/research", methods=["POST"])
@jwt_required_custom
def research_salary(current_user):
    """
    Research salary range for a position in a specific region.

    Request body:
    {
        "position": "Software Engineer",
        "region": "München",
        "experience_years": 5,
        "industry": "Software"  // optional
    }

    Returns:
    {
        "success": true,
        "research": {
            "position": "Software Engineer",
            "region": "München",
            "experience_years": 5,
            "min_salary": 65000,
            "max_salary": 90000,
            "median_salary": 77500,
            "currency": "EUR",
            "data_sources": [...],
            "factors": [...],
            "notes": "..."
        }
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "Keine Daten übermittelt"}), 400

    position = data.get("position", "").strip()
    if not position:
        return jsonify({"success": False, "error": "Position ist erforderlich"}), 400

    region = data.get("region", "Deutschland").strip()
    experience_years = data.get("experience_years", 3)
    industry = data.get("industry")

    # Validate experience_years
    try:
        experience_years = int(experience_years)
        experience_years = max(0, min(50, experience_years))  # Clamp to reasonable range
    except (TypeError, ValueError):
        experience_years = 3

    try:
        coach = SalaryCoach()
        research = coach.research_salary(
            position=position,
            region=region,
            experience_years=experience_years,
            industry=industry,
        )

        return jsonify(
            {
                "success": True,
                "research": research.to_dict(),
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        print(f"Error in salary research: {str(e)}")
        return jsonify(
            {
                "success": False,
                "error": "Fehler bei der Gehaltsrecherche. Bitte versuchen Sie es erneut.",
            }
        ), 500


@salary_bp.route("/negotiation-tips", methods=["POST"])
@jwt_required_custom
def get_negotiation_tips(current_user):
    """
    Generate personalized salary negotiation tips and strategy.

    Request body:
    {
        "target_salary": 70000,
        "current_salary": 55000,  // optional
        "position": "Software Engineer",
        "experience_years": 5,
        "company_name": "Example GmbH",  // optional
        "job_offer_details": "..."  // optional
    }

    Returns:
    {
        "success": true,
        "strategy": {
            "target_salary": 70000,
            "current_salary": 55000,
            "recommended_range": {"min": 66500, "max": 77000},
            "opening_statement": "...",
            "counter_arguments": [...],
            "fallback_positions": [...],
            "tips": [...],
            "german_culture_notes": [...],
            "common_objections": [...]
        }
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "Keine Daten übermittelt"}), 400

    target_salary = data.get("target_salary")
    if not target_salary:
        return jsonify({"success": False, "error": "Wunschgehalt ist erforderlich"}), 400

    # Validate and parse target_salary
    try:
        target_salary = int(target_salary)
        if target_salary <= 0:
            return jsonify({"success": False, "error": "Wunschgehalt muss positiv sein"}), 400
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Ungültiges Wunschgehalt"}), 400

    # Parse optional fields
    current_salary = data.get("current_salary")
    if current_salary is not None:
        try:
            current_salary = int(current_salary)
            if current_salary <= 0:
                current_salary = None
        except (TypeError, ValueError):
            current_salary = None

    position = data.get("position", "").strip()
    experience_years = data.get("experience_years", 3)
    company_name = data.get("company_name")
    job_offer_details = data.get("job_offer_details")

    # Validate experience_years
    try:
        experience_years = int(experience_years)
        experience_years = max(0, min(50, experience_years))
    except (TypeError, ValueError):
        experience_years = 3

    try:
        coach = SalaryCoach()
        strategy = coach.generate_negotiation_tips(
            target_salary=target_salary,
            current_salary=current_salary,
            position=position,
            experience_years=experience_years,
            company_name=company_name,
            job_offer_details=job_offer_details,
        )

        return jsonify(
            {
                "success": True,
                "strategy": strategy.to_dict(),
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        print(f"Error in negotiation tips: {str(e)}")
        return jsonify(
            {
                "success": False,
                "error": "Fehler bei der Strategieentwicklung. Bitte versuchen Sie es erneut.",
            }
        ), 500


@salary_bp.route("/data", methods=["GET"])
@jwt_required_custom
def get_salary_data(current_user):
    """
    Get saved salary coach data for the current user.

    Returns:
    {
        "success": true,
        "data": {
            "formData": {...},
            "research": {...} | null,
            "strategy": {...} | null,
            "updatedAt": "..."
        }
    }
    """
    salary_data = salary_data_service.get_salary_data(current_user.id)

    if not salary_data:
        return jsonify(
            {
                "success": True,
                "data": None,
            }
        ), 200

    return jsonify(
        {
            "success": True,
            "data": salary_data.to_dict(),
        }
    ), 200


@salary_bp.route("/data", methods=["POST"])
@jwt_required_custom
def save_salary_data(current_user):
    """
    Save salary coach data for the current user.

    Request body:
    {
        "formData": {
            "position": "...",
            "region": "...",
            "experienceYears": 5,
            "targetSalary": 70000,
            "currentSalary": 55000,
            "industry": "..."
        },
        "research": {...} | null,
        "strategy": {...} | null
    }

    Returns:
    {
        "success": true,
        "message": "Daten gespeichert"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "Keine Daten übermittelt"}), 400

    try:
        salary_data_service.save_salary_data(current_user.id, data)
        return jsonify(
            {
                "success": True,
                "message": "Daten gespeichert",
            }
        ), 200
    except Exception as e:
        print(f"Error saving salary data: {str(e)}")
        return jsonify(
            {
                "success": False,
                "error": "Fehler beim Speichern der Daten",
            }
        ), 500


@salary_bp.route("/data", methods=["DELETE"])
@jwt_required_custom
def delete_salary_data(current_user):
    """
    Delete saved salary coach data for the current user.

    Returns:
    {
        "success": true,
        "message": "Daten gelöscht"
    }
    """
    try:
        salary_data_service.delete_salary_data(current_user.id)
    except Exception as e:
        print(f"Error deleting salary data: {str(e)}")
        return jsonify(
            {
                "success": False,
                "error": "Fehler beim Löschen der Daten",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Daten gelöscht",
        }
    ), 200
