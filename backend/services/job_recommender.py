"""
Job Recommender Service - Finds and recommends jobs based on user skills and profile.
"""

from datetime import datetime, timedelta

from sqlalchemy import func

from models import JobRecommendation, UserSkill, db
from services.bundesagentur_client import BundesagenturClient
from services.job_fit_calculator import JobFitCalculator
from services.requirement_analyzer import RequirementAnalyzer
from services.web_scraper import WebScraper


class JobRecommender:
    """Service to find and recommend jobs based on user profile."""

    MIN_FIT_SCORE = 40
    MAX_RECOMMENDATIONS = 10
    SEARCH_URLS = {
        "indeed": "https://de.indeed.com/jobs?q={query}&l={location}&sort=date",
    }

    @staticmethod
    def score_to_category(score: int) -> str:
        """Map a fit score to a category label."""
        if score >= 80:
            return "sehr_gut"
        if score >= 60:
            return "gut"
        if score >= 40:
            return "mittel"
        return "niedrig"

    def __init__(self):
        self.scraper = WebScraper()
        self.fit_calculator = JobFitCalculator()
        self.requirement_analyzer = RequirementAnalyzer()
        self.ba_client = BundesagenturClient()

    def get_user_search_keywords(self, user_id: int) -> list[str]:
        """Extract top search keywords from user's skills, prioritizing technical skills."""
        skills = UserSkill.query.filter_by(user_id=user_id).all()

        if not skills:
            return []

        # Prioritize technical skills and tools for search
        priority_categories = ["technical", "tools", "certifications", "soft_skills"]
        keywords = []

        for category in priority_categories:
            category_skills = [s for s in skills if s.skill_category == category]
            # Take top 3 skills per category (by experience years or alphabetically)
            sorted_skills = sorted(category_skills, key=lambda s: s.experience_years or 0, reverse=True)
            for skill in sorted_skills[:3]:
                if skill.skill_name not in keywords:
                    keywords.append(skill.skill_name)

        # Add remaining skills if we don't have enough
        if len(keywords) < 5:
            remaining = [s for s in skills if s.skill_name not in keywords]
            for skill in remaining[: (5 - len(keywords))]:
                keywords.append(skill.skill_name)

        return keywords[:5]

    def _search_deduplicated(self, search_keywords: list[str], **search_params) -> tuple[list, int]:
        """Search Bundesagentur API per keyword and deduplicate results by refnr.

        Returns (unique_jobs, total_found_across_searches).
        """
        seen_refnrs = set()
        all_jobs = []
        total = 0

        for keyword in search_keywords[:5]:
            jobs, found = self.ba_client.search_jobs(keywords=keyword, **search_params)
            total += found
            for job in jobs:
                if job.refnr not in seen_refnrs:
                    seen_refnrs.add(job.refnr)
                    all_jobs.append(job)

        return all_jobs, total

    def find_jobs_for_user(self, user_id: int, location: str = "Deutschland", max_results: int = 20) -> list[dict]:
        """Search for jobs matching user's skill profile via Bundesagentur API."""
        keywords = self.get_user_search_keywords(user_id)

        if not keywords:
            return []

        all_jobs, _ = self._search_deduplicated(keywords, location=location, size=max_results)

        results = []
        for job in all_jobs:
            job_data = job.to_job_data()
            if job_data.get("url") and self.check_duplicate(user_id, job_data["url"]):
                continue
            results.append(job_data)

        return results

    def search_and_score_jobs(
        self,
        user_id: int,
        location: str = "",
        working_time: str = "",
        max_results: int = 10,
        keywords: str = "",
        page: int = 1,
    ) -> dict:
        """Search Bundesagentur API, fetch details, and score each job."""
        if keywords.strip():
            search_keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        else:
            search_keywords = self.get_user_search_keywords(user_id)
        if not search_keywords:
            return {"results": [], "total_found": 0, "saved_count": 0, "page": page, "has_more": False}

        all_jobs, total = self._search_deduplicated(
            search_keywords,
            location=location,
            working_time=working_time,
            size=min(max_results, 25),
            page=page,
        )

        if keywords.strip():
            all_jobs = [job for job in all_jobs if self._is_relevant(job, search_keywords)]

        if not all_jobs:
            return {
                "results": [],
                "total_found": total,
                "saved_count": 0,
                "page": page,
                "has_more": total > page * max_results,
            }

        user_skills = UserSkill.query.filter_by(user_id=user_id).all()
        if not user_skills:
            return {"results": [], "total_found": total, "saved_count": 0, "page": page, "has_more": False}

        results = []

        for job in all_jobs[: max_results * 2]:
            job_data = job.to_job_data()

            if job_data.get("url") and self.check_duplicate(user_id, job_data["url"]):
                continue

            description = job_data.get("description", "")
            fit_result = None
            if description and len(description) > 50:
                requirements = self.requirement_analyzer.analyze_requirements(job_text=description)
                if requirements:
                    fit_result = self._calculate_fit_from_requirements(user_skills, requirements)

            if not fit_result:
                fit_result = self._title_based_score(job, user_skills)
                fit_result["missing"] = []

            job_data["fit_score"] = fit_result["score"]
            job_data["fit_category"] = fit_result["category"]
            job_data["matched_skills"] = fit_result["matched"]
            job_data["missing_skills"] = fit_result["missing"]

            results.append(job_data)

            if len(results) >= max_results:
                break

        results.sort(key=lambda x: x.get("fit_score", 0), reverse=True)

        return {
            "results": results,
            "total_found": total,
            "saved_count": 0,
            "page": page,
            "has_more": total > page * max_results,
        }

    def analyze_job_for_user(self, user_id: int, job_url: str) -> dict | None:
        """Analyze a job posting URL and calculate fit score for the user."""
        try:
            job_data = self.scraper.fetch_structured_job_posting(job_url)
            if not job_data or not job_data.get("description"):
                return None
            return self._score_job_data(user_id, job_data, job_data.get("description", ""))
        except Exception as e:
            return {
                "error": f"Fehler bei der Analyse: {str(e)}",
                "fit_score": 0,
                "fit_category": "niedrig",
            }

    def analyze_manual_job_for_user(
        self, user_id: int, job_text: str, company: str = "", title: str = ""
    ) -> dict | None:
        """Analyze manually pasted job text and calculate fit score."""
        try:
            job_data = {
                "title": title or "Unbekannte Position",
                "company": company or "Unbekanntes Unternehmen",
                "description": job_text,
                "location": None,
                "url": None,
                "source": "manual",
            }
            return self._score_job_data(user_id, job_data, job_text)
        except Exception as e:
            return {
                "error": f"Fehler bei der Analyse: {str(e)}",
                "fit_score": 0,
                "fit_category": "niedrig",
            }

    def _score_job_data(self, user_id: int, job_data: dict, job_text: str) -> dict:
        """Score job data against user skills and return analysis result."""
        user_skills = UserSkill.query.filter_by(user_id=user_id).all()

        if not user_skills:
            return {
                "job_data": job_data,
                "fit_score": 0,
                "fit_category": "niedrig",
                "error": "Keine Skills im Profil gefunden. Bitte lade deinen Lebenslauf hoch.",
            }

        requirements = self.requirement_analyzer.analyze_requirements(job_text=job_text)

        if not requirements:
            return {
                "job_data": job_data,
                "fit_score": 50,
                "fit_category": "mittel",
                "warning": "Anforderungen konnten nicht vollständig analysiert werden.",
            }

        fit_result = self._calculate_fit_from_requirements(user_skills, requirements)

        return {
            "job_data": job_data,
            "fit_score": fit_result["score"],
            "fit_category": fit_result["category"],
            "matched_skills": fit_result["matched"],
            "missing_skills": fit_result["missing"],
        }

    def _calculate_fit_from_requirements(self, user_skills: list[UserSkill], requirements: list[dict]) -> dict:
        """Calculate fit score from requirements and user skills via JobFitCalculator."""
        return self.fit_calculator.calculate_fit_from_dicts(user_skills, requirements)

    def _fuzzy_match(self, skill: str, text: str) -> bool:
        """Simple fuzzy matching for skills using word overlap and known variations."""
        if any(len(word) >= 3 and word in text for word in skill.split()):
            return True

        # Reuse the canonical skill variations from JobFitCalculator
        for base_skill, alts in JobFitCalculator.SKILL_VARIATIONS.items():
            if base_skill in skill and any(alt in text for alt in alts):
                return True
            if skill in alts and base_skill in text:
                return True

        return False

    def _title_based_score(self, job, user_skills: list) -> dict:
        """Score a job based on title/beruf matching against user skills (fallback when no description)."""
        if not user_skills:
            return {"score": 50, "category": "mittel", "matched": []}

        text = f"{job.titel} {job.beruf}".lower()
        matched = []
        for skill in user_skills:
            skill_name = skill.skill_name.lower()
            if skill_name in text or self._fuzzy_match(skill_name, text):
                matched.append({"requirement": job.titel, "skill": skill.skill_name, "type": "title_match"})

        # Score based on number of matches (title-only has limited signal)
        score_tiers = (30, 50, 65, 78, 85)
        score = score_tiers[min(len(matched), len(score_tiers) - 1)]
        return {"score": score, "category": self.score_to_category(score), "matched": matched}

    @staticmethod
    def _is_relevant(job, keywords: list[str]) -> bool:
        """Check if a job is relevant to the user's keywords (at least one must appear in title or beruf)."""
        text = f"{job.titel} {job.beruf}".lower()
        return any(kw.lower() in text for kw in keywords)

    def create_recommendation(
        self, user_id: int, job_data: dict, fit_score: int, fit_category: str
    ) -> JobRecommendation:
        """Create and persist a job recommendation."""
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
        self, user_id: int, include_dismissed: bool = False, limit: int = 20, offset: int = 0
    ) -> tuple[list[JobRecommendation], int]:
        """Get job recommendations for a user, sorted by fit score, deduplicated by job_title+company_name.

        When multiple recommendations share the same (job_title, company_name), only the most
        recent one (highest id) is kept.  Returns (recommendations, total_count).
        """
        base = JobRecommendation.query.filter_by(user_id=user_id)

        if not include_dismissed:
            base = base.filter_by(dismissed=False)

        # Subquery: for each (job_title, company_name) group keep the highest id (most recent).
        dedup_sub = db.session.query(func.max(JobRecommendation.id).label("max_id")).filter(
            JobRecommendation.user_id == user_id
        )
        if not include_dismissed:
            dedup_sub = dedup_sub.filter(JobRecommendation.dismissed == False)  # noqa: E712
        dedup_sub = dedup_sub.group_by(JobRecommendation.job_title, JobRecommendation.company_name).subquery()

        query = base.filter(JobRecommendation.id.in_(db.session.query(dedup_sub.c.max_id)))

        total = query.count()

        recommendations = (
            query.order_by(JobRecommendation.fit_score.desc(), JobRecommendation.recommended_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return recommendations, total

    def dismiss_recommendation(self, recommendation_id: int, user_id: int) -> bool:
        """Dismiss a recommendation. Returns True on success."""
        recommendation = JobRecommendation.query.filter_by(id=recommendation_id, user_id=user_id).first()

        if not recommendation:
            return False

        recommendation.dismissed = True
        db.session.commit()
        return True

    def mark_as_applied(self, recommendation_id: int, user_id: int, application_id: int | None = None) -> bool:
        """Mark a recommendation as applied. Returns True on success."""
        recommendation = JobRecommendation.query.filter_by(id=recommendation_id, user_id=user_id).first()

        if not recommendation:
            return False

        recommendation.applied = True
        if application_id:
            recommendation.application_id = application_id
        db.session.commit()
        return True

    def check_duplicate(self, user_id: int, job_url: str) -> bool:
        """Check if a job URL already exists as a recommendation for the user."""
        return JobRecommendation.query.filter_by(user_id=user_id, job_url=job_url).first() is not None

    def cleanup_old_recommendations(self, days: int = 30) -> int:
        """Remove unapplied recommendations older than the specified number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = JobRecommendation.query.filter(
            JobRecommendation.recommended_at < cutoff_date,
            JobRecommendation.applied == False,  # noqa: E712
        ).delete()

        db.session.commit()
        return deleted
