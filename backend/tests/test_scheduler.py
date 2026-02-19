"""Tests for the background scheduler."""

import os
from unittest.mock import MagicMock, patch


def _make_mock_user(user_id=1, location="Berlin", working_time="vz"):
    """Create a mock User with the fields the scheduler accesses."""
    user = MagicMock()
    user.id = user_id
    user.preferred_location = location
    user.preferred_working_time = working_time
    return user


def _make_search_results(jobs=None):
    """Build a search_and_score_jobs response dict with sensible defaults."""
    results = jobs or []
    return {
        "results": results,
        "total_found": len(results),
        "saved_count": 0,
        "page": 1,
        "has_more": False,
    }


def _make_job(title="Python Developer", url="https://example.com/job1", fit_score=78, fit_category="gut"):
    """Build a minimal job_data dict with the fields the scheduler uses."""
    return {"title": title, "url": url, "fit_score": fit_score, "fit_category": fit_category}


class TestSchedulerInit:
    @patch("services.scheduler.scheduler")
    def test_scheduler_disabled_in_testing(self, mock_scheduler):
        os.environ["TESTING"] = "1"
        try:
            from services.scheduler import init_scheduler

            mock_scheduler.running = False
            app = MagicMock()
            app.config.get.return_value = False

            init_scheduler(app)

            mock_scheduler.start.assert_not_called()
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
    def _make_app(self):
        app = MagicMock()
        app.app_context.return_value.__enter__ = MagicMock(return_value=None)
        app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        return app

    def _run_auto_search(self, mock_recommender, mock_users):
        """Run auto_search_jobs with mocked dependencies."""
        from services.job_recommender import JobRecommender
        from services.scheduler import auto_search_jobs

        app = self._make_app()

        mock_db_query = MagicMock()
        mock_db_query.join.return_value.filter.return_value.distinct.return_value.all.return_value = mock_users

        mock_class = MagicMock(return_value=mock_recommender)
        mock_class.MIN_FIT_SCORE = JobRecommender.MIN_FIT_SCORE

        with (
            patch("models.db") as mock_db,
            patch("models.User"),
            patch("models.UserSkill"),
            patch("services.job_recommender.JobRecommender", mock_class),
        ):
            mock_db.session.query.return_value = mock_db_query
            auto_search_jobs(app)

    def test_no_users_skips_search(self):
        """No users with skills means no searches."""
        mock_recommender = MagicMock()
        self._run_auto_search(mock_recommender, mock_users=[])
        mock_recommender.search_and_score_jobs.assert_not_called()

    def test_calls_search_and_score_with_user_preferences(self):
        """Verify scheduler passes user preferences to search_and_score_jobs."""
        mock_user = _make_mock_user(user_id=1, location="Berlin", working_time="vz")
        mock_recommender = MagicMock()
        mock_recommender.search_and_score_jobs.return_value = _make_search_results(
            [
                _make_job(fit_score=78, fit_category="gut"),
            ]
        )

        self._run_auto_search(mock_recommender, mock_users=[mock_user])

        mock_recommender.search_and_score_jobs.assert_called_once_with(
            user_id=1, location="Berlin", working_time="vz", max_results=5
        )
        mock_recommender.create_recommendation.assert_called_once()
        call_kwargs = mock_recommender.create_recommendation.call_args[1]
        assert call_kwargs["fit_score"] == 78
        assert call_kwargs["fit_category"] == "gut"

    def test_filters_low_score_jobs(self):
        """Jobs below MIN_FIT_SCORE (40) should not be saved."""
        mock_recommender = MagicMock()
        mock_recommender.search_and_score_jobs.return_value = _make_search_results(
            [
                _make_job(title="Unrelated Job", fit_score=30, fit_category="niedrig"),
            ]
        )

        self._run_auto_search(mock_recommender, mock_users=[_make_mock_user()])
        mock_recommender.create_recommendation.assert_not_called()

    def test_saves_multiple_good_jobs_skips_low_ones(self):
        """Multiple jobs above threshold saved; low-score ones skipped."""
        mock_recommender = MagicMock()
        mock_recommender.search_and_score_jobs.return_value = _make_search_results(
            [
                _make_job(title="Python Developer", fit_score=85, fit_category="sehr_gut"),
                _make_job(title="Django Developer", url="https://example.com/job2", fit_score=65, fit_category="gut"),
                _make_job(
                    title="Random Position", url="https://example.com/job3", fit_score=30, fit_category="niedrig"
                ),
            ]
        )

        self._run_auto_search(mock_recommender, mock_users=[_make_mock_user()])

        assert mock_recommender.create_recommendation.call_count == 2

    def test_handles_empty_results(self):
        """Scheduler handles search returning no results gracefully."""
        mock_recommender = MagicMock()
        mock_recommender.search_and_score_jobs.return_value = _make_search_results()

        self._run_auto_search(mock_recommender, mock_users=[_make_mock_user()])
        mock_recommender.create_recommendation.assert_not_called()

    def test_defaults_missing_fit_score_to_zero(self):
        """If fit_score is missing from results, default to 0 (below MIN_FIT_SCORE)."""
        mock_recommender = MagicMock()
        mock_recommender.search_and_score_jobs.return_value = _make_search_results(
            [
                {"title": "Some Job", "url": "https://example.com/job1"},
            ]
        )

        self._run_auto_search(mock_recommender, mock_users=[_make_mock_user()])
        mock_recommender.create_recommendation.assert_not_called()

    def test_uses_empty_string_for_null_preferences(self):
        """Users without location/working_time preferences get empty strings."""
        mock_user = _make_mock_user(user_id=2, location=None, working_time=None)
        mock_recommender = MagicMock()
        mock_recommender.search_and_score_jobs.return_value = _make_search_results()

        self._run_auto_search(mock_recommender, mock_users=[mock_user])

        mock_recommender.search_and_score_jobs.assert_called_once_with(
            user_id=2, location="", working_time="", max_results=5
        )
