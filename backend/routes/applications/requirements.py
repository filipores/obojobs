from typing import Any

from flask import Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from routes.applications import applications_bp
from services import application_service
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
from services.web_scraper import WebScraper


@applications_bp.route("/<int:app_id>/requirements", methods=["GET"])
@jwt_required_custom
def get_requirements(app_id: int, current_user: Any) -> tuple[Response, int]:
    """Get job requirements for an application."""
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    # Get requirements from database
    requirements = application_service.get_requirements(app_id)

    # Group requirements by type
    must_have = [r.to_dict() for r in requirements if r.requirement_type == "must_have"]
    nice_to_have = [r.to_dict() for r in requirements if r.requirement_type == "nice_to_have"]

    return jsonify(
        {
            "success": True,
            "data": {
                "application_id": app_id,
                "must_have": must_have,
                "nice_to_have": nice_to_have,
                "total": len(requirements),
            },
        }
    ), 200


@applications_bp.route("/<int:app_id>/analyze-requirements", methods=["POST"])
@jwt_required_custom
def analyze_requirements(app_id: int, current_user: Any) -> tuple[Response, int]:
    """Analyze and extract requirements from job posting for an application.

    This endpoint uses Claude API to extract requirements from the job posting text
    stored in the application's notizen field or from a provided URL.
    """
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    data = request.json or {}
    job_text = data.get("job_text")

    # If no job_text provided, try to get it from the application's source
    if not job_text:
        # Try to use notizen as fallback (might contain job description)
        if app.notizen:
            job_text = app.notizen
        # Or try to scrape from quelle URL if it's a valid URL
        elif app.quelle and app.quelle.startswith(("http://", "https://")):
            try:
                scraper = WebScraper()
                job_data = scraper.fetch_job_posting(app.quelle)
                job_text = job_data.get("text", "")
            except Exception:
                pass

    if not job_text:
        return jsonify({"success": False, "error": "Kein Stellentext vorhanden. Bitte gib den Stellentext an."}), 400

    try:
        # Analyze requirements using Claude
        analyzer = RequirementAnalyzer()
        extracted_requirements = analyzer.analyze_requirements(job_text)

        if not extracted_requirements:
            return jsonify(
                {"success": False, "error": "Keine Anforderungen gefunden. Bitte überprüfe den Stellentext."}
            ), 400

        # Delete existing and save new requirements
        requirements = application_service.save_requirements(app_id, extracted_requirements)
        must_have = [r.to_dict() for r in requirements if r.requirement_type == "must_have"]
        nice_to_have = [r.to_dict() for r in requirements if r.requirement_type == "nice_to_have"]

        return jsonify(
            {
                "success": True,
                "data": {
                    "application_id": app_id,
                    "must_have": must_have,
                    "nice_to_have": nice_to_have,
                    "total": len(requirements),
                },
                "message": f"{len(requirements)} Anforderungen extrahiert",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Anforderungs-Analyse: {str(e)}"}), 500


@applications_bp.route("/<int:app_id>/job-fit", methods=["GET"])
@jwt_required_custom
def get_job_fit(app_id: int, current_user: Any) -> tuple[Response, int]:
    """Calculate and return the job-fit score for an application.

    Compares user skills against job requirements and returns:
    - overall_score: 0-100 weighted score (70% must-have, 30% nice-to-have)
    - score_category: sehr_gut (80%+), gut (60-79%), mittel (40-59%), niedrig (<40%)
    - matched_skills: Requirements the user fully meets
    - partial_matches: Requirements partially met (e.g., less experience than required)
    - missing_skills: Requirements the user doesn't meet
    - learning_recommendations: Suggestions for how to learn missing skills

    Query params:
    - include_recommendations: 'true' to include learning recommendations (default: true)
    """
    app = application_service.get_application(app_id, current_user.id)

    if not app:
        return jsonify({"success": False, "error": "Application not found"}), 404

    # Check if requirements exist
    requirements = application_service.get_requirements(app_id)
    if not requirements:
        return jsonify(
            {
                "success": False,
                "error": "Keine Anforderungen für diese Bewerbung vorhanden. Bitte zuerst Anforderungen analysieren.",
            }
        ), 400

    include_recommendations = request.args.get("include_recommendations", "true").lower() == "true"

    try:
        calculator = JobFitCalculator()
        result = calculator.calculate_job_fit(current_user.id, app_id)

        # Generate learning recommendations if there are missing/partial skills
        if include_recommendations and (result.missing_skills or result.partial_matches):
            recommendations = calculator.generate_learning_recommendations(
                result.missing_skills, result.partial_matches
            )
            result.learning_recommendations = recommendations

        return jsonify({"success": True, "job_fit": result.to_dict()}), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Job-Fit Berechnung: {str(e)}"}), 500


@applications_bp.route("/analyze-job-fit", methods=["POST"])
@jwt_required_custom
def analyze_job_fit_preview(current_user: Any) -> tuple[Response, int]:
    """Create a temporary application for job-fit analysis before generating.

    This endpoint:
    1. Creates a temporary (draft) application
    2. Analyzes and extracts job requirements
    3. Returns the application ID for job-fit score calculation

    The temporary application can be used for the full generation later
    or deleted if the user decides not to proceed.
    """
    data = request.json or {}
    url = data.get("url", "").strip()
    description = data.get("description", "")
    company = data.get("company", "")
    title = data.get("title", "")

    if not description:
        return jsonify({"success": False, "error": "Stellenbeschreibung ist erforderlich"}), 400

    try:
        # Create a temporary application for analysis
        app = application_service.create_application(
            user_id=current_user.id,
            firma=company or "Unbekannt",
            position=title or "Unbekannt",
            quelle=url,
            status="erstellt",
            notizen=f"[Draft - Job-Fit Analyse]\n\n{description[:2000]}",
        )

        # Analyze requirements using Claude
        analyzer = RequirementAnalyzer()
        extracted_requirements = analyzer.analyze_requirements(description)

        if extracted_requirements:
            application_service.save_requirements(app.id, extracted_requirements)

        return jsonify(
            {
                "success": True,
                "application_id": app.id,
                "requirements_count": len(extracted_requirements) if extracted_requirements else 0,
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Fehler bei der Job-Fit Analyse: {str(e)}"}), 500
