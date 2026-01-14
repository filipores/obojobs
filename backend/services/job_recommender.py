"""
Job Recommender Service - Finds and recommends jobs based on user skills and profile.

Scrapes job boards for relevant jobs and calculates Job-Fit scores.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from models import JobRecommendation, UserSkill, db
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
from services.web_scraper import WebScraper


@dataclass
class JobSearchResult:
    """Result of a job search from a job board."""
    title: str
    company: str
    location: str | None
    url: str
    source: str
    description: str | None = None
    salary: str | None = None
    employment_type: str | None = None


class JobRecommender:
    """Service to find and recommend jobs based on user profile."""

    # Minimum fit score to recommend a job
    MIN_FIT_SCORE = 60

    # Maximum recommendations to generate per run
    MAX_RECOMMENDATIONS = 10

    # Job board search URLs (simplified - using Indeed DE as primary source)
    SEARCH_URLS = {
        "indeed": "https://de.indeed.com/jobs?q={query}&l={location}&sort=date",
    }

    def __init__(self):
        self.scraper = WebScraper()
        self.fit_calculator = JobFitCalculator()
        self.requirement_analyzer = RequirementAnalyzer()

    def get_user_search_keywords(self, user_id: int) -> list[str]:
        """
        Extract search keywords from user's skills.

        Returns top skills by category for job search.
        """
        skills = UserSkill.query.filter_by(user_id=user_id).all()

        if not skills:
            return []

        # Prioritize technical skills and tools for search
        priority_categories = ["technical", "tools", "certifications"]
        keywords = []

        for category in priority_categories:
            category_skills = [s for s in skills if s.skill_category == category]
            # Take top 3 skills per category (by experience years or alphabetically)
            sorted_skills = sorted(
                category_skills,
                key=lambda s: s.experience_years or 0,
                reverse=True
            )
            for skill in sorted_skills[:3]:
                if skill.skill_name not in keywords:
                    keywords.append(skill.skill_name)

        # Add remaining skills if we don't have enough
        if len(keywords) < 5:
            remaining = [s for s in skills if s.skill_name not in keywords]
            for skill in remaining[:(5 - len(keywords))]:
                keywords.append(skill.skill_name)

        return keywords[:5]  # Limit to 5 keywords

    def find_jobs_for_user(
        self,
        user_id: int,
        location: str = "Deutschland",
        max_results: int = 20
    ) -> list[dict]:
        """
        Search for jobs matching user's skill profile.

        This is a simplified implementation that works with manual triggers.
        For production, this could be enhanced with actual job board API access.

        Args:
            user_id: User ID to search for
            location: Location to search in
            max_results: Maximum number of jobs to fetch

        Returns:
            List of job data dicts with scraped job information
        """
        keywords = self.get_user_search_keywords(user_id)

        if not keywords:
            return []

        # Note: This is a placeholder implementation.
        # In production, you would integrate with job board APIs or
        # use a more sophisticated scraping approach.
        # For now, we support manual job URL input and analysis.

        return []

    def analyze_job_for_user(self, user_id: int, job_url: str) -> dict | None:
        """
        Analyze a specific job posting for a user and calculate fit score.

        Args:
            user_id: The user's ID
            job_url: URL of the job posting to analyze

        Returns:
            Dict with job data and fit score, or None if analysis fails
        """
        try:
            # Scrape the job posting
            job_data = self.scraper.fetch_structured_job_posting(job_url)

            if not job_data or not job_data.get("description"):
                return None

            # Get user skills
            user_skills = UserSkill.query.filter_by(user_id=user_id).all()

            if not user_skills:
                return {
                    "job_data": job_data,
                    "fit_score": 0,
                    "fit_category": "niedrig",
                    "error": "Keine Skills im Profil gefunden. Bitte laden Sie Ihren Lebenslauf hoch.",
                }

            # Analyze requirements from job posting
            requirements = self.requirement_analyzer.analyze_requirements(
                job_text=job_data.get("description", ""),
                job_title=job_data.get("title", ""),
            )

            if not requirements:
                # If no requirements could be extracted, provide basic analysis
                return {
                    "job_data": job_data,
                    "fit_score": 50,
                    "fit_category": "mittel",
                    "warning": "Anforderungen konnten nicht vollständig analysiert werden.",
                }

            # Calculate fit score
            fit_result = self._calculate_fit_from_requirements(user_skills, requirements)

            return {
                "job_data": job_data,
                "fit_score": fit_result["score"],
                "fit_category": fit_result["category"],
                "matched_skills": fit_result["matched"],
                "missing_skills": fit_result["missing"],
            }

        except Exception as e:
            return {
                "error": f"Fehler bei der Analyse: {str(e)}",
                "fit_score": 0,
                "fit_category": "niedrig",
            }

    def _calculate_fit_from_requirements(
        self,
        user_skills: list[UserSkill],
        requirements: list[dict]
    ) -> dict:
        """
        Calculate fit score from requirements and user skills.

        Args:
            user_skills: User's skills from database
            requirements: Extracted requirements from job posting

        Returns:
            Dict with score, category, matched and missing skills
        """
        must_haves = [r for r in requirements if r.get("requirement_type") == "must_have"]
        nice_to_haves = [r for r in requirements if r.get("requirement_type") == "nice_to_have"]

        matched = []
        missing = []

        # Check each requirement against user skills
        for req in requirements:
            req_text = req.get("requirement_text", "").lower()
            found = False

            for skill in user_skills:
                skill_name = skill.skill_name.lower()
                # Simple matching: check if skill name appears in requirement
                if skill_name in req_text or self._fuzzy_match(skill_name, req_text):
                    matched.append({
                        "requirement": req.get("requirement_text"),
                        "skill": skill.skill_name,
                        "type": req.get("requirement_type"),
                    })
                    found = True
                    break

            if not found:
                missing.append({
                    "requirement": req.get("requirement_text"),
                    "type": req.get("requirement_type"),
                })

        # Calculate scores
        must_have_matched = len([m for m in matched if m["type"] == "must_have"])
        nice_to_have_matched = len([m for m in matched if m["type"] == "nice_to_have"])

        total_must_have = len(must_haves)
        total_nice_to_have = len(nice_to_haves)

        # Calculate percentages
        must_have_pct = (must_have_matched / total_must_have * 100) if total_must_have else 100
        nice_to_have_pct = (nice_to_have_matched / total_nice_to_have * 100) if total_nice_to_have else 100

        # Weighted score: 70% must-have, 30% nice-to-have
        if total_must_have == 0 and total_nice_to_have == 0:
            score = 50  # No requirements found
        elif total_must_have == 0:
            score = int(nice_to_have_pct)
        elif total_nice_to_have == 0:
            score = int(must_have_pct)
        else:
            score = int(must_have_pct * 0.7 + nice_to_have_pct * 0.3)

        # Determine category
        if score >= 80:
            category = "sehr_gut"
        elif score >= 60:
            category = "gut"
        elif score >= 40:
            category = "mittel"
        else:
            category = "niedrig"

        return {
            "score": score,
            "category": category,
            "matched": matched,
            "missing": missing,
        }

    def _fuzzy_match(self, skill: str, text: str) -> bool:
        """Simple fuzzy matching for skills."""
        # Split skill into words and check if any word appears in text
        skill_words = skill.split()
        for word in skill_words:
            if len(word) >= 3 and word in text:
                return True

        # Check for common variations
        variations = {
            "javascript": ["js", "node", "react", "vue", "angular"],
            "python": ["py", "django", "flask", "pandas"],
            "java": ["spring", "maven", "gradle"],
            "sql": ["mysql", "postgresql", "postgres", "oracle", "database"],
            "css": ["sass", "scss", "less", "tailwind"],
        }

        for base_skill, alts in variations.items():
            if base_skill in skill:
                for alt in alts:
                    if alt in text:
                        return True
            if skill in alts:
                if base_skill in text:
                    return True

        return False

    def create_recommendation(
        self,
        user_id: int,
        job_data: dict,
        fit_score: int,
        fit_category: str
    ) -> JobRecommendation:
        """
        Create a job recommendation for the user.

        Args:
            user_id: User ID
            job_data: Scraped job data
            fit_score: Calculated fit score
            fit_category: Score category (sehr_gut, gut, etc.)

        Returns:
            Created JobRecommendation instance
        """
        recommendation = JobRecommendation.from_job_data(
            user_id=user_id,
            job_data=job_data,
            fit_score=fit_score,
            fit_category=fit_category,
        )

        db.session.add(recommendation)
        db.session.commit()

        return recommendation

    def get_recommendations(
        self,
        user_id: int,
        include_dismissed: bool = False,
        limit: int = 20
    ) -> list[JobRecommendation]:
        """
        Get job recommendations for a user.

        Args:
            user_id: User ID
            include_dismissed: Whether to include dismissed recommendations
            limit: Maximum number of recommendations to return

        Returns:
            List of JobRecommendation objects
        """
        query = JobRecommendation.query.filter_by(user_id=user_id)

        if not include_dismissed:
            query = query.filter_by(dismissed=False)

        return query.order_by(
            JobRecommendation.fit_score.desc(),
            JobRecommendation.recommended_at.desc()
        ).limit(limit).all()

    def dismiss_recommendation(self, recommendation_id: int, user_id: int) -> bool:
        """
        Dismiss a job recommendation.

        Args:
            recommendation_id: ID of the recommendation to dismiss
            user_id: User ID (for authorization)

        Returns:
            True if dismissed successfully, False otherwise
        """
        recommendation = JobRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()

        if not recommendation:
            return False

        recommendation.dismissed = True
        db.session.commit()
        return True

    def mark_as_applied(
        self,
        recommendation_id: int,
        user_id: int,
        application_id: int | None = None
    ) -> bool:
        """
        Mark a recommendation as applied.

        Args:
            recommendation_id: ID of the recommendation
            user_id: User ID (for authorization)
            application_id: Optional application ID if an application was created

        Returns:
            True if updated successfully, False otherwise
        """
        recommendation = JobRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()

        if not recommendation:
            return False

        recommendation.applied = True
        if application_id:
            recommendation.application_id = application_id
        db.session.commit()
        return True

    def check_duplicate(self, user_id: int, job_url: str) -> bool:
        """
        Check if a job URL already exists as a recommendation for the user.

        Args:
            user_id: User ID
            job_url: Job URL to check

        Returns:
            True if duplicate exists, False otherwise
        """
        existing = JobRecommendation.query.filter_by(
            user_id=user_id,
            job_url=job_url
        ).first()
        return existing is not None

    def cleanup_old_recommendations(self, days: int = 30) -> int:
        """
        Remove recommendations older than specified days.

        Args:
            days: Number of days after which to remove recommendations

        Returns:
            Number of deleted recommendations
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = JobRecommendation.query.filter(
            JobRecommendation.recommended_at < cutoff_date,
            JobRecommendation.applied == False  # noqa: E712
        ).delete()

        db.session.commit()
        return deleted
