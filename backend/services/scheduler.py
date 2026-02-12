"""
Background Scheduler Service.

Runs periodic tasks via APScheduler (cleanup daily at 3 AM, job search every 6 hours).
"""

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def cleanup_old_recommendations(app: Flask) -> None:
    """Remove recommendations older than 30 days."""
    with app.app_context():
        try:
            from services.job_recommender import JobRecommender

            recommender = JobRecommender()
            deleted = recommender.cleanup_old_recommendations(days=30)
            if deleted:
                logger.info(f"Cleaned up {deleted} old recommendations")
        except Exception as e:
            logger.error(f"Error cleaning up recommendations: {e}")


def auto_search_jobs(app: Flask) -> None:
    """Automatically search for jobs for all users with skills."""
    with app.app_context():
        try:
            from models import User, UserSkill, db
            from services.job_recommender import JobRecommender

            recommender = JobRecommender()

            users_with_skills = (
                db.session.query(User.id)
                .join(UserSkill, User.id == UserSkill.user_id)
                .filter(User.is_active == True)  # noqa: E712
                .distinct()
                .all()
            )

            for (user_id,) in users_with_skills:
                try:
                    jobs = recommender.find_jobs_for_user(user_id=user_id, max_results=5)
                    for job_data in jobs:
                        fit_score = job_data.get("fit_score", 50)
                        fit_category = JobRecommender.score_to_category(fit_score)

                        if fit_score >= JobRecommender.MIN_FIT_SCORE and (
                            not job_data.get("url") or not recommender.check_duplicate(user_id, job_data["url"])
                        ):
                            recommender.create_recommendation(
                                user_id=user_id,
                                job_data=job_data,
                                fit_score=fit_score,
                                fit_category=fit_category,
                            )
                except Exception as e:
                    logger.error(f"Error searching jobs for user {user_id}: {e}")
                    continue

            logger.info(f"Auto-search completed for {len(users_with_skills)} users")
        except Exception as e:
            logger.error(f"Error in auto_search_jobs: {e}")


def init_scheduler(app: Flask) -> None:
    """Initialize and start the background scheduler (skips in testing and debug reloader)."""
    if os.environ.get("TESTING") or app.config.get("TESTING"):
        logger.info("Scheduler disabled in testing mode")
        return

    if scheduler.running:
        logger.info("Scheduler already running, skipping init")
        return

    scheduler.add_job(
        func=cleanup_old_recommendations,
        args=[app],
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_old_recommendations",
        name="Clean up old job recommendations",
        replace_existing=True,
    )

    scheduler.add_job(
        func=auto_search_jobs,
        args=[app],
        trigger=IntervalTrigger(hours=6),
        id="auto_search_jobs",
        name="Auto-search jobs for users",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Background scheduler started with 2 jobs")


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler shut down")
