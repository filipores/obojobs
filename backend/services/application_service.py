"""
Application service layer.

Provides data-access functions for Application, JobRequirement,
InterviewQuestion, UserSkill, and Document models so that route
handlers never import models directly.
"""

import os
from datetime import datetime, timedelta
from typing import Any

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func

from models import Application, Document, InterviewQuestion, JobRequirement, UserSkill, db

# ---------------------------------------------------------------------------
# Application CRUD
# ---------------------------------------------------------------------------


def get_application(app_id: int, user_id: int) -> Application | None:
    """Return a single application owned by *user_id*, or None."""
    return Application.query.filter_by(id=app_id, user_id=user_id).first()


def list_applications(user_id: int, page: int = 1, per_page: int = 20) -> Pagination:
    """Return a paginated query result of the user's applications."""
    return (
        Application.query.filter_by(user_id=user_id)
        .order_by(Application.datum.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_timeline_applications(user_id: int, days_filter: str = "all") -> list[Application]:
    """Return applications for the timeline view, optionally filtered by days."""
    query = Application.query.filter_by(user_id=user_id)

    if days_filter != "all":
        try:
            days = int(days_filter)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Application.datum >= cutoff_date)
        except ValueError:
            pass

    return query.order_by(Application.datum.desc()).all()


def update_application(app: Application, data: dict[str, Any]) -> Application:
    """Update application fields from *data* dict and commit."""
    if "status" in data:
        new_status = data["status"]
        if new_status != app.status:
            app.add_status_change(new_status)
        app.status = new_status
    if "notizen" in data:
        app.notizen = data["notizen"]
    db.session.commit()
    return app


def delete_application(app: Application) -> None:
    """Delete an application and its PDF file (if any)."""
    if app.pdf_path and os.path.exists(app.pdf_path):
        os.remove(app.pdf_path)
    db.session.delete(app)
    db.session.commit()


def create_application(
    user_id: int,
    firma: str,
    position: str,
    quelle: str | None = None,
    status: str = "erstellt",
    notizen: str | None = None,
) -> Application:
    """Create and persist a new Application."""
    app = Application(
        user_id=user_id,
        firma=firma,
        position=position,
        quelle=quelle,
        status=status,
        notizen=notizen,
    )
    db.session.add(app)
    db.session.commit()
    return app


def get_latest_application(user_id: int) -> Application | None:
    """Return the most recent application for *user_id*."""
    return Application.query.filter_by(user_id=user_id).order_by(Application.datum.desc()).first()


def save_application_email_text(app: Application, text: str) -> None:
    """Update the email_text field and commit."""
    app.email_text = text
    db.session.commit()


def update_application_fields(app: Application, **kwargs: Any) -> None:
    """Set arbitrary fields on *app* and commit."""
    for key, value in kwargs.items():
        setattr(app, key, value)
    db.session.commit()


# ---------------------------------------------------------------------------
# JobRequirement helpers
# ---------------------------------------------------------------------------


def get_requirements(app_id: int) -> list[JobRequirement]:
    """Return all JobRequirement rows for a given application."""
    return JobRequirement.query.filter_by(application_id=app_id).all()


def delete_requirements(app_id: int) -> None:
    """Delete all requirements for the given application."""
    JobRequirement.query.filter_by(application_id=app_id).delete()


def create_requirement(
    app_id: int, requirement_text: str, requirement_type: str, skill_category: str | None = None
) -> JobRequirement:
    """Create a single JobRequirement and add it to the session (no commit)."""
    req = JobRequirement(
        application_id=app_id,
        requirement_text=requirement_text,
        requirement_type=requirement_type,
        skill_category=skill_category,
    )
    db.session.add(req)
    return req


def save_requirements(app_id: int, extracted_requirements: list[dict[str, Any]]) -> list[JobRequirement]:
    """Delete existing requirements then bulk-create from *extracted_requirements*."""
    delete_requirements(app_id)
    for req_data in extracted_requirements:
        create_requirement(
            app_id,
            requirement_text=req_data["requirement_text"],
            requirement_type=req_data["requirement_type"],
            skill_category=req_data.get("skill_category"),
        )
    db.session.commit()
    return get_requirements(app_id)


# ---------------------------------------------------------------------------
# InterviewQuestion helpers
# ---------------------------------------------------------------------------


def get_interview_question(question_id: int) -> InterviewQuestion | None:
    """Return an InterviewQuestion by primary key."""
    return InterviewQuestion.query.get(question_id)


def get_interview_questions(app_id: int, question_type: str | None = None) -> list[InterviewQuestion]:
    """Return interview questions, optionally filtered by type."""
    query = InterviewQuestion.query.filter_by(application_id=app_id)
    if question_type and question_type in InterviewQuestion.VALID_TYPES:
        query = query.filter_by(question_type=question_type)
    return query.all()


def delete_interview_questions(app_id: int) -> None:
    """Delete all interview questions for the given application."""
    InterviewQuestion.query.filter_by(application_id=app_id).delete()


def create_interview_question(
    app_id: int,
    question_text: str,
    question_type: str,
    difficulty: str = "medium",
    sample_answer: str | None = None,
) -> InterviewQuestion:
    """Create a single InterviewQuestion and add to session (no commit)."""
    q = InterviewQuestion(
        application_id=app_id,
        question_text=question_text,
        question_type=question_type,
        difficulty=difficulty,
        sample_answer=sample_answer,
    )
    db.session.add(q)
    return q


def save_interview_questions(app_id: int, questions_data: list[dict[str, Any]]) -> list[InterviewQuestion]:
    """Delete existing then bulk-create interview questions."""
    delete_interview_questions(app_id)
    for q_data in questions_data:
        create_interview_question(
            app_id,
            question_text=q_data["question_text"],
            question_type=q_data["question_type"],
            difficulty=q_data.get("difficulty", "medium"),
            sample_answer=q_data.get("sample_answer"),
        )
    db.session.commit()
    return get_interview_questions(app_id)


# ---------------------------------------------------------------------------
# UserSkill helpers
# ---------------------------------------------------------------------------


def get_user_skills(user_id: int) -> list[UserSkill]:
    """Return all UserSkill rows for the given user."""
    return UserSkill.query.filter_by(user_id=user_id).all()


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------


def get_document(user_id: int, doc_type: str) -> Document | None:
    """Return a Document of the given type for *user_id*, or None."""
    return Document.query.filter_by(user_id=user_id, doc_type=doc_type).first()


# ---------------------------------------------------------------------------
# Interview statistics
# ---------------------------------------------------------------------------


def get_interview_statistics(user_id: int) -> dict[str, Any]:
    """Return aggregated interview statistics for the given user.

    Returns a dict with total_with_results, result_counts (list of tuples),
    upcoming (list of Application), and recent_results (list of Application).
    """
    base_query = Application.query.filter_by(user_id=user_id)

    total_with_results = base_query.filter(Application.interview_result.isnot(None)).count()

    result_counts = (
        db.session.query(Application.interview_result, func.count(Application.id))
        .filter_by(user_id=user_id)
        .filter(Application.interview_result.isnot(None))
        .group_by(Application.interview_result)
        .all()
    )

    upcoming = (
        base_query.filter(
            Application.interview_result == "scheduled",
            Application.interview_date.isnot(None),
            Application.interview_date >= datetime.utcnow(),
        )
        .order_by(Application.interview_date.asc())
        .limit(5)
        .all()
    )

    recent_results = (
        base_query.filter(Application.interview_result.in_(["completed", "passed", "rejected", "offer_received"]))
        .order_by(Application.interview_date.desc().nulls_last())
        .limit(10)
        .all()
    )

    return {
        "total_with_results": total_with_results,
        "result_counts": result_counts,
        "upcoming": upcoming,
        "recent_results": recent_results,
    }


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------


def get_filtered_applications(
    user_id: int, search_query: str = "", filter_status: str = "", filter_firma: str = ""
) -> list[Application]:
    """Return applications with optional search/filter, ordered by date desc."""
    query = Application.query.filter_by(user_id=user_id)

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(Application.firma.ilike(search_pattern), Application.position.ilike(search_pattern))
        )

    if filter_status:
        query = query.filter(Application.status == filter_status)

    if filter_firma:
        query = query.filter(Application.firma == filter_firma)

    return query.order_by(Application.datum.desc()).all()


def commit() -> None:
    """Commit the current database session."""
    db.session.commit()
