"""Service layer for application statistics data access."""

from datetime import datetime

from sqlalchemy import func

from models import Application, User, db


def count_applications_in_range(user_id: int, start: datetime, end: datetime) -> int:
    """Count applications created between start and end dates."""
    return Application.query.filter(
        Application.user_id == user_id,
        Application.datum >= start,
        Application.datum < end,
    ).count()


def update_weekly_goal(user: User, new_goal: int) -> None:
    """Update the user's weekly goal and commit."""
    user.weekly_goal = new_goal
    db.session.commit()


def count_by_status(user_id: int, status: str | None = None) -> int:
    """Count applications, optionally filtered by status."""
    query = Application.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    return query.count()


def count_sent_today(user_id: int, today_start: datetime) -> int:
    """Count applications sent today."""
    return Application.query.filter(
        Application.user_id == user_id,
        Application.sent_at >= today_start,
    ).count()


def get_apps_with_status_history(user_id: int, statuses: list[str]) -> list[Application]:
    """Return applications with status in the given list."""
    return Application.query.filter(
        Application.user_id == user_id,
        Application.status.in_(statuses),
    ).all()


def get_all_applications(user_id: int) -> list[Application]:
    """Return all applications for a user."""
    return Application.query.filter_by(user_id=user_id).all()


def get_top_companies(user_id: int, limit: int = 5) -> list[tuple[str, int]]:
    """Return top companies by application count."""
    return (
        db.session.query(Application.firma, func.count(Application.id).label("anzahl"))
        .filter(Application.user_id == user_id)
        .group_by(Application.firma)
        .order_by(func.count(Application.id).desc())
        .limit(limit)
        .all()
    )
