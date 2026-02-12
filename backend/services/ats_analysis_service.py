"""Service layer for ATS analysis data access."""

from datetime import datetime, timedelta

from models import ATSAnalysis, Document, db


def find_cached_analysis(user_id, job_url, cache_hours=24):
    """Return a cached analysis for the given URL within the cache window, or None."""
    cache_cutoff = datetime.utcnow() - timedelta(hours=cache_hours)
    return (
        ATSAnalysis.query.filter(
            ATSAnalysis.user_id == user_id,
            ATSAnalysis.job_url == job_url,
            ATSAnalysis.created_at >= cache_cutoff,
        )
        .order_by(ATSAnalysis.created_at.desc())
        .first()
    )


def get_cv_document(user_id):
    """Return the user's CV document, or None."""
    return Document.query.filter_by(user_id=user_id, doc_type="lebenslauf").first()


def hash_job_text(job_text):
    """Return a hash of the job text for deduplication."""
    return ATSAnalysis.hash_job_text(job_text)


def create_analysis(user_id, job_url, job_text_hash, title, score, result_json):
    """Create and return a new ATSAnalysis record."""
    analysis = ATSAnalysis(
        user_id=user_id,
        job_url=job_url,
        job_text_hash=job_text_hash,
        title=title,
        score=score,
        result_json=result_json,
    )
    db.session.add(analysis)
    db.session.commit()
    return analysis


def rollback():
    """Rollback the current database session."""
    db.session.rollback()


def get_history(user_id, limit=20):
    """Return ATS analysis history for a user."""
    return ATSAnalysis.query.filter_by(user_id=user_id).order_by(ATSAnalysis.created_at.desc()).limit(limit).all()


def get_analysis(analysis_id, user_id):
    """Return a single analysis owned by user, or None."""
    return ATSAnalysis.query.filter_by(id=analysis_id, user_id=user_id).first()


def delete_analysis(analysis_id, user_id):
    """Delete an analysis. Returns the analysis or None if not found."""
    analysis = ATSAnalysis.query.filter_by(id=analysis_id, user_id=user_id).first()
    if not analysis:
        return None
    db.session.delete(analysis)
    db.session.commit()
    return analysis
