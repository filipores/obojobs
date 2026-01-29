"""
Recommendations Routes - API endpoints for job recommendations.
"""

from flask import Blueprint, jsonify, request

from middleware.jwt_required import jwt_required_custom
from models import JobRecommendation, db
from services.job_recommender import JobRecommender

bp = Blueprint("recommendations", __name__)


@bp.route("/recommendations", methods=["GET"])
@jwt_required_custom
def get_recommendations(current_user):
    """Get job recommendations for the current user."""
    include_dismissed = request.args.get("include_dismissed", "false").lower() == "true"
    try:
        limit = min(int(request.args.get("limit", 20)), 50)
    except ValueError:
        limit = 20

    recommender = JobRecommender()
    recommendations = recommender.get_recommendations(
        user_id=current_user.id,
        include_dismissed=include_dismissed,
        limit=limit
    )

    return jsonify({
        "recommendations": [r.to_dict() for r in recommendations],
        "total": len(recommendations),
    })


@bp.route("/recommendations/analyze", methods=["POST"])
@jwt_required_custom
def analyze_job(current_user):
    """
    Analyze a job URL and calculate fit score.

    Request body:
        {
            "job_url": "https://example.com/job/123"
        }
    """
    data = request.get_json()
    if not data or not data.get("job_url"):
        return jsonify({"error": "job_url ist erforderlich"}), 400

    job_url = data["job_url"]

    recommender = JobRecommender()

    # Check for duplicate
    if recommender.check_duplicate(current_user.id, job_url):
        existing = JobRecommendation.query.filter_by(
            user_id=current_user.id,
            job_url=job_url
        ).first()
        if existing:
            return jsonify({
                "message": "Diese Stelle wurde bereits analysiert",
                "recommendation": existing.to_dict(),
                "is_duplicate": True,
            })

    # Analyze the job
    result = recommender.analyze_job_for_user(current_user.id, job_url)

    if not result:
        return jsonify({
            "error": "Job konnte nicht analysiert werden"
        }), 400

    if result.get("error"):
        return jsonify(result), 400

    # Only create recommendation if fit score meets minimum threshold
    if result.get("fit_score", 0) >= JobRecommender.MIN_FIT_SCORE:
        recommendation = recommender.create_recommendation(
            user_id=current_user.id,
            job_data=result["job_data"],
            fit_score=result["fit_score"],
            fit_category=result["fit_category"],
        )
        result["recommendation_id"] = recommendation.id
        result["saved"] = True
    else:
        result["saved"] = False
        result["message"] = f"Job-Fit Score ({result.get('fit_score')}%) liegt unter der Empfehlungsgrenze von {JobRecommender.MIN_FIT_SCORE}%"

    return jsonify(result)


@bp.route("/recommendations/analyze-manual", methods=["POST"])
@jwt_required_custom
def analyze_manual_job(current_user):
    """
    Analyze manually pasted job text and calculate fit score.
    Fallback when URL scraping fails.

    Request body:
        {
            "job_text": "Full job posting text...",
            "company": "Example GmbH",  # Optional
            "title": "Software Developer"  # Optional
        }
    """
    data = request.get_json()
    if not data or not data.get("job_text"):
        return jsonify({"error": "Stellentext ist erforderlich"}), 400

    job_text = data["job_text"].strip()
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()

    if len(job_text) < 100:
        return jsonify({
            "error": "Stellentext zu kurz. Bitte fügen Sie den vollständigen Text ein."
        }), 400

    recommender = JobRecommender()

    # Analyze the manually entered job text
    result = recommender.analyze_manual_job_for_user(
        current_user.id,
        job_text,
        company=company,
        title=title
    )

    if not result:
        return jsonify({
            "error": "Job konnte nicht analysiert werden"
        }), 400

    if result.get("error"):
        return jsonify(result), 400

    # Only create recommendation if fit score meets minimum threshold
    if result.get("fit_score", 0) >= JobRecommender.MIN_FIT_SCORE:
        recommendation = recommender.create_recommendation(
            user_id=current_user.id,
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

    return jsonify(result)


@bp.route("/recommendations/<int:recommendation_id>", methods=["GET"])
@jwt_required_custom
def get_recommendation(current_user, recommendation_id):
    """Get a specific recommendation by ID."""
    recommendation = JobRecommendation.query.filter_by(
        id=recommendation_id,
        user_id=current_user.id
    ).first()

    if not recommendation:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"recommendation": recommendation.to_dict()})


@bp.route("/recommendations/<int:recommendation_id>/dismiss", methods=["POST"])
@jwt_required_custom
def dismiss_recommendation(current_user, recommendation_id):
    """Dismiss a job recommendation."""
    recommender = JobRecommender()
    success = recommender.dismiss_recommendation(recommendation_id, current_user.id)

    if not success:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"message": "Empfehlung ausgeblendet", "success": True})


@bp.route("/recommendations/<int:recommendation_id>/apply", methods=["POST"])
@jwt_required_custom
def mark_applied(current_user, recommendation_id):
    """Mark a recommendation as applied."""
    data = request.get_json() or {}
    application_id = data.get("application_id")

    recommender = JobRecommender()
    success = recommender.mark_as_applied(
        recommendation_id,
        current_user.id,
        application_id
    )

    if not success:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    return jsonify({"message": "Als beworben markiert", "success": True})


@bp.route("/recommendations/<int:recommendation_id>", methods=["DELETE"])
@jwt_required_custom
def delete_recommendation(current_user, recommendation_id):
    """Delete a job recommendation."""
    recommendation = JobRecommendation.query.filter_by(
        id=recommendation_id,
        user_id=current_user.id
    ).first()

    if not recommendation:
        return jsonify({"error": "Empfehlung nicht gefunden"}), 404

    db.session.delete(recommendation)
    db.session.commit()

    return jsonify({"message": "Empfehlung gelöscht", "success": True})


@bp.route("/recommendations/save", methods=["POST"])
@jwt_required_custom
def save_recommendation(current_user):
    """
    Manually save a job as recommendation.

    Request body:
        {
            "job_url": "https://...",
            "job_data": { ... },  # Optional pre-analyzed job data
            "fit_score": 75,  # Optional, will analyze if not provided
            "fit_category": "gut"  # Optional
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten angegeben"}), 400

    job_url = data.get("job_url")
    job_data = data.get("job_data")
    fit_score = data.get("fit_score")
    fit_category = data.get("fit_category")

    recommender = JobRecommender()

    # Check for duplicate
    if job_url and recommender.check_duplicate(current_user.id, job_url):
        return jsonify({
            "error": "Diese Stelle ist bereits gespeichert",
            "is_duplicate": True,
        }), 400

    # If no job data provided, analyze the URL
    if not job_data and job_url:
        result = recommender.analyze_job_for_user(current_user.id, job_url)
        if result and not result.get("error"):
            job_data = result.get("job_data", {})
            fit_score = result.get("fit_score", fit_score)
            fit_category = result.get("fit_category", fit_category)

    if not job_data:
        return jsonify({"error": "Job-Daten konnten nicht ermittelt werden"}), 400

    # Ensure job_url is in job_data
    if job_url and not job_data.get("url"):
        job_data["url"] = job_url

    # Default fit values if not provided
    if fit_score is None:
        fit_score = 50
    if fit_category is None:
        if fit_score >= 80:
            fit_category = "sehr_gut"
        elif fit_score >= 60:
            fit_category = "gut"
        elif fit_score >= 40:
            fit_category = "mittel"
        else:
            fit_category = "niedrig"

    recommendation = recommender.create_recommendation(
        user_id=current_user.id,
        job_data=job_data,
        fit_score=fit_score,
        fit_category=fit_category,
    )

    return jsonify({
        "message": "Job-Empfehlung gespeichert",
        "recommendation": recommendation.to_dict(),
    }), 201


@bp.route("/recommendations/stats", methods=["GET"])
@jwt_required_custom
def get_recommendation_stats(current_user):
    """Get recommendation statistics for the current user."""
    total = JobRecommendation.query.filter_by(user_id=current_user.id).count()
    dismissed = JobRecommendation.query.filter_by(
        user_id=current_user.id, dismissed=True
    ).count()
    applied = JobRecommendation.query.filter_by(
        user_id=current_user.id, applied=True
    ).count()
    active = JobRecommendation.query.filter_by(
        user_id=current_user.id, dismissed=False, applied=False
    ).count()

    # Score breakdown
    sehr_gut = JobRecommendation.query.filter_by(
        user_id=current_user.id, fit_category="sehr_gut", dismissed=False
    ).count()
    gut = JobRecommendation.query.filter_by(
        user_id=current_user.id, fit_category="gut", dismissed=False
    ).count()

    return jsonify({
        "total": total,
        "active": active,
        "dismissed": dismissed,
        "applied": applied,
        "by_score": {
            "sehr_gut": sehr_gut,
            "gut": gut,
        }
    })
