"""Service layer for job recommendation data access."""

from sqlalchemy import case, func

from models import JobRecommendation, db


def get_recommendation(recommendation_id, user_id):
    """Return a single recommendation owned by user, or None."""
    return JobRecommendation.query.filter_by(id=recommendation_id, user_id=user_id).first()


def find_by_url(user_id, job_url):
    """Return an existing recommendation for the given URL, or None."""
    return JobRecommendation.query.filter_by(user_id=user_id, job_url=job_url).first()


def delete_recommendation(recommendation_id, user_id):
    """Delete a recommendation. Returns the object or None if not found."""
    recommendation = JobRecommendation.query.filter_by(id=recommendation_id, user_id=user_id).first()
    if not recommendation:
        return None
    db.session.delete(recommendation)
    db.session.commit()
    return recommendation


def get_recommendation_stats(user_id):
    """Return aggregated recommendation statistics for the user."""
    is_dismissed = JobRecommendation.dismissed == True  # noqa: E712
    is_applied = JobRecommendation.applied == True  # noqa: E712
    is_active = ~is_dismissed & ~is_applied

    def count_where(condition):
        return func.sum(case((condition, 1), else_=0))

    return (
        db.session.query(
            func.count(JobRecommendation.id).label("total"),
            count_where(is_dismissed).label("dismissed"),
            count_where(is_applied).label("applied"),
            count_where(is_active).label("active"),
            count_where((JobRecommendation.fit_category == "sehr_gut") & ~is_dismissed).label("sehr_gut"),
            count_where((JobRecommendation.fit_category == "gut") & ~is_dismissed).label("gut"),
        )
        .filter(JobRecommendation.user_id == user_id)
        .first()
    )
