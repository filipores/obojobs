"""
Recommendations Routes - API endpoints for job recommendations.
"""

from typing import Any

from flask import Blueprint, Response, jsonify, request

from middleware.jwt_required import jwt_required_custom
from services import recommendation_service
from services.job_recommender import JobRecommender

bp = Blueprint("recommendations", __name__)


@bp.route("/recommendations", methods=["GET"])
@jwt_required_custom
def get_recommendations(current_user: Any) -> Response:
    """Get job recommendations for the current user."""
    include_dismissed = request.args.get("include_dismissed", "false").lower() == "true"
    try:
        limit = min(int(request.args.get("limit", 20)), 50)
    except ValueError:
        limit = 20

    recommender = JobRecommender()
    recommendations = recommender.get_recommendations(
        user_id=current_user.id, include_dismissed=include_dismissed, limit=limit
    )

    return jsonify(
        {
            "recommendations": [r.to_dict() for r in recommendations],
            "total": len(recommendations),
        }
    )


@bp.route("/recommendations/analyze", methods=["POST"])
@jwt_required_custom
def analyze_job(current_user: Any) -> Response | tuple[Response, int]:
    """Analyze a job URL and calculate fit score."""
    data = request.get_json()
    if not data or not data.get("job_url"):
        return jsonify({"error": "job_url ist erforderlich"}), 400

    job_url = data["job_url"]

    recommender = JobRecommender()

    existing = recommendation_service.find_by_url(current_user.id, job_url)
    if existing:
        return jsonify(
            {
                "message": "Diese Stelle wurde bereits analysiert",
                "recommendation": existing.to_dict(),
                "is_duplicate": True,
            }
        )

    result = recommender.analyze_job_for_user(current_user.id, job_url)

    if not result:
        return jsonify({"error": "Job konnte nicht analysiert werden"}), 400

    if result.get("error"):
        return jsonify(result), 400

    _maybe_save_recommendation(recommender, current_user.id, result)
    return jsonify(result)


@bp.route("/recommendations/analyze-manual", methods=["POST"])
@jwt_required_custom
def analyze_manual_job(current_user: Any) -> Response | tuple[Response, int]:
    """Analyze manually pasted job text and calculate fit score."""
    data = request.get_json()
    if not data or not data.get("job_text"):
        return jsonify({"error": "Stellentext ist erforderlich"}), 400

    job_text = data["job_text"].strip()
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()

    if len(job_text) < 100:
        return jsonify({"error": "Stellentext zu kurz. Bitte fügen Sie den vollständigen Text ein."}), 400

    recommender = JobRecommender()
    result = recommender.analyze_manual_job_for_user(current_user.id, job_text, company=company, title=title)

    if not result:
        return jsonify({"error": "Job konnte nicht analysiert werden"}), 400

    if result.get("error"):
        return jsonify(result), 400

    _maybe_save_recommendation(recommender, current_user.id, result)
    return jsonify(result)


def _maybe_save_recommendation(recommender: Any, user_id: int, result: dict[str, Any]) -> None:
    """Save the recommendation if it meets the minimum score threshold, mutates result in-place."""
    if result.get("fit_score", 0) >= JobRecommender.MIN_FIT_SCORE:
        recommendation = recommender.create_recommendation(
            user_id=user_id,
            job_data=result["job_data"],
            fit_score=result["fit_score"],
            fit_category=result["fit_category"],
        )
        result["recommendation_id"] = recommendation.id
        result["saved"] = True
    else:
        result["saved"] = False
        result["message"] = (
            f"Job-Fit Score ({result.get('fit_score')}%) liegt unter der "
            f"Empfehlungsgrenze von {JobRecommender.MIN_FIT_SCORE}%"
        )


@bp.route("/recommendations/search", methods=["POST"])
@jwt_required_custom
def search_jobs(current_user: Any) -> Response:
    """Search for jobs via Bundesagentur API, score them, and auto-save good matches."""
    data = request.get_json() or {}
    location = data.get("location", "")
    working_time = data.get("working_time", "")
    keywords = data.get("keywords", "")
    try:
        max_results = min(int(data.get("max_results", 10)), 25)
    except (ValueError, TypeError):
        max_results = 10
    try:
        page = max(1, int(data.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    recommender = JobRecommender()
    result = recommender.search_and_score_jobs(
        user_id=current_user.id,
        location=location,
        working_time=working_time,
        max_results=max_results,
        keywords=keywords,
        page=page,
    )

    saved_count = 0
    for job_data in result.get("results", []):
        if job_data.get("fit_score", 0) >= JobRecommender.MIN_FIT_SCORE and (
            not job_data.get("url") or not recommender.check_duplicate(current_user.id, job_data["url"])
        ):
            recommender.create_recommendation(
                user_id=current_user.id,
                job_data=job_data,
                fit_score=job_data["fit_score"],
                fit_category=job_data["fit_category"],
            )
            saved_count += 1

    return jsonify(
        {
            "success": True,
            "data": {
                "results": result["results"],
                "total_found": result["total_found"],
                "saved_count": saved_count,
                "page": result.get("page", 1),
                "has_more": result.get("has_more", False),
            },
        }
    )


@bp.route("/recommendations/<int:recommendation_id>", methods=["GET"])
@jwt_required_custom
def get_recommendation(current_user: Any, recommendation_id: int) -> Response | tuple[Response, int]:
    """Get a specific recommendation by ID."""
    recommendation = recommendation_service.get_recommendation(recommendation_id, current_user.id)

    if not recommendation:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"recommendation": recommendation.to_dict()})


@bp.route("/recommendations/<int:recommendation_id>/dismiss", methods=["POST"])
@jwt_required_custom
def dismiss_recommendation(current_user: Any, recommendation_id: int) -> Response | tuple[Response, int]:
    """Dismiss a job recommendation."""
    recommender = JobRecommender()
    success = recommender.dismiss_recommendation(recommendation_id, current_user.id)

    if not success:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"message": "Empfehlung ausgeblendet", "success": True})


@bp.route("/recommendations/<int:recommendation_id>/apply", methods=["POST"])
@jwt_required_custom
def mark_applied(current_user: Any, recommendation_id: int) -> Response | tuple[Response, int]:
    """Mark a recommendation as applied."""
    data = request.get_json() or {}
    application_id = data.get("application_id")

    recommender = JobRecommender()
    success = recommender.mark_as_applied(recommendation_id, current_user.id, application_id)

    if not success:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"message": "Als beworben markiert", "success": True})


@bp.route("/recommendations/<int:recommendation_id>", methods=["DELETE"])
@jwt_required_custom
def delete_recommendation(current_user: Any, recommendation_id: int) -> Response | tuple[Response, int]:
    """Delete a job recommendation."""
    recommendation = recommendation_service.delete_recommendation(recommendation_id, current_user.id)

    if not recommendation:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"message": "Empfehlung gelöscht", "success": True})


@bp.route("/recommendations/save", methods=["POST"])
@jwt_required_custom
def save_recommendation(current_user: Any) -> Response | tuple[Response, int]:
    """Manually save a job as recommendation."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten angegeben"}), 400

    job_url = data.get("job_url")
    job_data = data.get("job_data")
    fit_score = data.get("fit_score")
    fit_category = data.get("fit_category")

    recommender = JobRecommender()

    if job_url and recommender.check_duplicate(current_user.id, job_url):
        return jsonify(
            {
                "error": "Diese Stelle ist bereits gespeichert",
                "is_duplicate": True,
            }
        ), 400

    if not job_data and job_url:
        result = recommender.analyze_job_for_user(current_user.id, job_url)
        if result and not result.get("error"):
            job_data = result.get("job_data", {})
            fit_score = result.get("fit_score", fit_score)
            fit_category = result.get("fit_category", fit_category)

    if not job_data:
        return jsonify({"error": "Job-Daten konnten nicht ermittelt werden"}), 400

    if job_url and not job_data.get("url"):
        job_data["url"] = job_url

    if fit_score is None:
        fit_score = 50
    if fit_category is None:
        fit_category = JobRecommender.score_to_category(fit_score)

    recommendation = recommender.create_recommendation(
        user_id=current_user.id,
        job_data=job_data,
        fit_score=fit_score,
        fit_category=fit_category,
    )

    return jsonify(
        {
            "message": "Job-Empfehlung gespeichert",
            "recommendation": recommendation.to_dict(),
        }
    ), 201


@bp.route("/recommendations/stats", methods=["GET"])
@jwt_required_custom
def get_recommendation_stats(current_user: Any) -> Response:
    """Get recommendation statistics for the current user."""
    stats = recommendation_service.get_recommendation_stats(current_user.id)

    return jsonify(
        {
            "total": stats.total or 0,
            "active": stats.active or 0,
            "dismissed": stats.dismissed or 0,
            "applied": stats.applied or 0,
            "by_score": {
                "sehr_gut": stats.sehr_gut or 0,
                "gut": stats.gut or 0,
            },
        }
    )
