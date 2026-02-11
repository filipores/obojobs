"""
Background Scheduler Service.

Uses APScheduler to run periodic tasks:
- cleanup_old_recommendations: Daily at 3:00 AM
- auto_search_jobs: Every 6 hours
"""

import os
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def cleanup_old_recommendations(app):
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


def auto_search_jobs(app):
    """Automatically search for jobs for all users with skills."""
    with app.app_context():
        try:
            from models import User, UserSkill, db
            from services.job_recommender import JobRecommender

            recommender = JobRecommender()

            # Find users who have skills (they've uploaded a CV)
            users_with_skills = (
                db.session.query(User.id)
                .join(UserSkill, User.id == UserSkill.user_id)
                .filter(User.is_active == True)  # noqa: E712
                .distinct()
                .all()
            )

            for (user_id,) in users_with_skills:
                try:
                    jobs = recommender.find_jobs_for_user(
                        user_id=user_id, max_results=5
                    )
                    for job_data in jobs:
                        fit_score = job_data.get("fit_score", 50)
                        if fit_score >= 80:
                            fit_category = "sehr_gut"
                        elif fit_score >= 60:
                            fit_category = "gut"
                        elif fit_score >= 40:
                            fit_category = "mittel"
                        else:
                            fit_category = "niedrig"

                        if fit_score >= JobRecommender.MIN_FIT_SCORE:
                            if not job_data.get("url") or not recommender.check_duplicate(
                                user_id, job_data["url"]
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

            logger.info(
                f"Auto-search completed for {len(users_with_skills)} users"
            )
        except Exception as e:
            logger.error(f"Error in auto_search_jobs: {e}")


def init_scheduler(app):
    """
    Initialize and start the background scheduler.

    Guards:
    - Skip in testing mode
    - Skip if scheduler is already running (Flask debug reloader)
    """
    # Don't run scheduler during tests
    if os.environ.get("TESTING") or app.config.get("TESTING"):
        logger.info("Scheduler disabled in testing mode")
        return

    # Avoid double-start in Flask debug reloader
    if scheduler.running:
        logger.info("Scheduler already running, skipping init")
        return

    # Add jobs
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


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler shut down")
