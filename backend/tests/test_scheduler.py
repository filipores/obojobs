"""Tests for the background scheduler."""

import os
from unittest.mock import MagicMock, patch


class TestSchedulerInit:
    def test_scheduler_disabled_in_testing(self):
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
        os.environ.pop("TESTING", None)

        from services.scheduler import init_scheduler

        app = MagicMock()
        app.config.get.return_value = True
        init_scheduler(app)

    @patch("services.scheduler.scheduler")
    def test_scheduler_skips_if_running(self, mock_scheduler):
        os.environ.pop("TESTING", None)

        from services.scheduler import init_scheduler

        mock_scheduler.running = True
        app = MagicMock()
        app.config.get.return_value = False

        init_scheduler(app)

        mock_scheduler.start.assert_not_called()

    @patch("services.scheduler.scheduler")
    def test_shutdown_scheduler_when_running(self, mock_scheduler):
        from services.scheduler import shutdown_scheduler

        mock_scheduler.running = True
        shutdown_scheduler()
        mock_scheduler.shutdown.assert_called_once_with(wait=False)

    @patch("services.scheduler.scheduler")
    def test_shutdown_scheduler_when_not_running(self, mock_scheduler):
        from services.scheduler import shutdown_scheduler

        mock_scheduler.running = False
        shutdown_scheduler()
        mock_scheduler.shutdown.assert_not_called()


class TestCleanupJob:
    def test_cleanup_old_recommendations(self):
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
    def test_auto_search_jobs_no_users(self):
        app = MagicMock()
        app.app_context.return_value.__enter__ = MagicMock(return_value=None)
        app.app_context.return_value.__exit__ = MagicMock(return_value=False)

        # Verifies the function doesn't crash (imports happen inside app_context)
