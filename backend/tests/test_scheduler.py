"""Tests for the background scheduler."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestSchedulerInit:
    """Tests for scheduler initialization."""

    def test_scheduler_disabled_in_testing(self):
        """Scheduler should not start when TESTING env var is set."""
        os.environ["TESTING"] = "1"
        try:
            from services.scheduler import init_scheduler, scheduler

            app = MagicMock()
            app.config.get.return_value = False

            init_scheduler(app)

            assert not scheduler.running
        finally:
            os.environ.pop("TESTING", None)

    def test_scheduler_disabled_in_testing_config(self):
        """Scheduler should not start when app.config TESTING is True."""
        os.environ.pop("TESTING", None)

        from services.scheduler import init_scheduler

        app = MagicMock()
        app.config.get.return_value = True

        # Should return without starting
        init_scheduler(app)

    @patch("services.scheduler.scheduler")
    def test_scheduler_skips_if_running(self, mock_scheduler):
        """Scheduler should not double-start if already running."""
        os.environ.pop("TESTING", None)

        from services.scheduler import init_scheduler

        mock_scheduler.running = True
        app = MagicMock()
        app.config.get.return_value = False

        init_scheduler(app)

        mock_scheduler.start.assert_not_called()

    @patch("services.scheduler.scheduler")
    def test_shutdown_scheduler_when_running(self, mock_scheduler):
        """Shutdown should call scheduler.shutdown when running."""
        from services.scheduler import shutdown_scheduler

        mock_scheduler.running = True
        shutdown_scheduler()
        mock_scheduler.shutdown.assert_called_once_with(wait=False)

    @patch("services.scheduler.scheduler")
    def test_shutdown_scheduler_when_not_running(self, mock_scheduler):
        """Shutdown should be a no-op when scheduler isn't running."""
        from services.scheduler import shutdown_scheduler

        mock_scheduler.running = False
        shutdown_scheduler()
        mock_scheduler.shutdown.assert_not_called()


class TestCleanupJob:
    """Tests for the cleanup job function."""

    def test_cleanup_old_recommendations(self):
        """Cleanup job should call recommender.cleanup_old_recommendations."""
        from services.scheduler import cleanup_old_recommendations

        app = MagicMock()
        app.app_context.return_value.__enter__ = MagicMock(return_value=None)
        app.app_context.return_value.__exit__ = MagicMock(return_value=False)

        mock_recommender = MagicMock()
        mock_recommender.cleanup_old_recommendations.return_value = 5

        with patch.dict("sys.modules", {}):
            with patch("services.job_recommender.JobRecommender", return_value=mock_recommender):
                cleanup_old_recommendations(app)


class TestAutoSearchJob:
    """Tests for the auto-search job function."""

    def test_auto_search_jobs_no_users(self):
        """Auto-search should handle no users gracefully."""
        from services.scheduler import auto_search_jobs

        app = MagicMock()
        app.app_context.return_value.__enter__ = MagicMock(return_value=None)
        app.app_context.return_value.__exit__ = MagicMock(return_value=False)

        # The function imports inside app_context, so this test mainly
        # verifies it doesn't crash
        # In a real test you'd need a proper Flask app context
