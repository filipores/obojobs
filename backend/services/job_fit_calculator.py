"""
Job-Fit Calculator Service - Calculates match score between user skills and job requirements.
"""

import re

from models import JobRequirement, UserSkill
from services.job_fit_models import JobFitResult, LearningRecommendation, SkillMatch
from services.job_fit_recommendations import (
    generate_learning_recommendations,
)


class JobFitCalculator:
    """Service to calculate job-fit score between user skills and job requirements."""

    # Weighting: 70% must-have, 30% nice-to-have
    MUST_HAVE_WEIGHT = 0.70
    NICE_TO_HAVE_WEIGHT = 0.30

    # Score categories
    SCORE_SEHR_GUT = 80
    SCORE_GUT = 60
    SCORE_MITTEL = 40

    # Known skill variations for fuzzy matching
    SKILL_VARIATIONS = {
        "javascript": ["js", "node", "react", "vue", "angular", "next.js", "nuxt"],
        "typescript": ["ts", "angular", "next.js", "nuxt"],
        "python": ["py", "django", "flask", "pandas", "fastapi"],
        "java": ["spring", "maven", "gradle", "jvm"],
        "c#": ["csharp", ".net", "dotnet", "asp.net"],
        "php": ["laravel", "symfony", "wordpress"],
        "ruby": ["rails", "ruby on rails"],
        "go": ["golang"],
        "rust": ["cargo", "rustlang"],
        "sql": ["mysql", "postgresql", "postgres", "oracle", "database", "mariadb"],
        "css": ["sass", "scss", "less", "tailwind", "bootstrap"],
        "react": ["next.js", "redux", "jsx"],
        "vue": ["nuxt", "vuex", "pinia"],
        "angular": ["rxjs", "ngrx"],
        "node": ["express", "nestjs", "npm"],
        "docker": ["kubernetes", "k8s", "container"],
        "aws": ["amazon web services", "ec2", "s3", "lambda"],
        "azure": ["microsoft cloud", "az-"],
        "gcp": ["google cloud", "firebase"],
        "cloud": ["aws", "azure", "gcp"],
        "devops": ["ci/cd", "ci-cd", "pipeline", "jenkins", "github actions"],
        "agile": ["scrum", "kanban", "sprint"],
        "sap": ["abap", "hana", "s/4hana"],
        "marketing": ["seo", "sem", "google ads", "social media"],
        "projektmanagement": ["project management", "pmp", "prince2", "jira"],
    }

    def calculate_job_fit(self, user_id: int, application_id: int) -> JobFitResult:
        """
        Calculate the job-fit score for a user and an application.

        Args:
            user_id: The user's ID
            application_id: The application's ID

        Returns:
            JobFitResult with overall score and detailed breakdown
        """
        # Get user skills
        user_skills = UserSkill.query.filter_by(user_id=user_id).all()

        # Get job requirements
        requirements = JobRequirement.query.filter_by(application_id=application_id).all()

        if not requirements:
            # No requirements = perfect match (nothing to fail)
            return JobFitResult(
                overall_score=100,
                score_category="sehr_gut",
                must_have_score=100,
                nice_to_have_score=100,
                matched_skills=[],
                partial_matches=[],
                missing_skills=[],
                total_must_have=0,
                matched_must_have=0,
                total_nice_to_have=0,
                matched_nice_to_have=0,
            )

        # Separate requirements by type
        must_have_reqs = [r for r in requirements if r.requirement_type == "must_have"]
        nice_to_have_reqs = [r for r in requirements if r.requirement_type == "nice_to_have"]

        # Match skills
        matched_skills = []
        partial_matches = []
        missing_skills = []

        # Process must-have requirements
        must_have_matched = 0
        for req in must_have_reqs:
            match_result = self._match_requirement(req, user_skills)
            if match_result.match_type == "full":
                matched_skills.append(match_result)
                must_have_matched += 1
            elif match_result.match_type == "partial":
                partial_matches.append(match_result)
                must_have_matched += 0.5  # Partial counts as half
            else:
                missing_skills.append(match_result)

        # Process nice-to-have requirements
        nice_to_have_matched = 0
        for req in nice_to_have_reqs:
            match_result = self._match_requirement(req, user_skills)
            if match_result.match_type == "full":
                matched_skills.append(match_result)
                nice_to_have_matched += 1
            elif match_result.match_type == "partial":
                partial_matches.append(match_result)
                nice_to_have_matched += 0.5
            else:
                missing_skills.append(match_result)

        # Calculate scores
        must_have_score = self._calculate_percentage(must_have_matched, len(must_have_reqs))
        nice_to_have_score = self._calculate_percentage(nice_to_have_matched, len(nice_to_have_reqs))

        # Calculate weighted overall score
        if len(must_have_reqs) == 0:
            # Only nice-to-haves, use 100% nice-to-have weight
            overall_score = nice_to_have_score
        elif len(nice_to_have_reqs) == 0:
            # Only must-haves, use 100% must-have weight
            overall_score = must_have_score
        else:
            # Both types exist, use weighted calculation
            overall_score = int(must_have_score * self.MUST_HAVE_WEIGHT + nice_to_have_score * self.NICE_TO_HAVE_WEIGHT)

        # Determine score category
        score_category = self._get_score_category(overall_score)

        return JobFitResult(
            overall_score=overall_score,
            score_category=score_category,
            must_have_score=must_have_score,
            nice_to_have_score=nice_to_have_score,
            matched_skills=matched_skills,
            partial_matches=partial_matches,
            missing_skills=missing_skills,
            total_must_have=len(must_have_reqs),
            matched_must_have=int(must_have_matched),
            total_nice_to_have=len(nice_to_have_reqs),
            matched_nice_to_have=int(nice_to_have_matched),
        )

    def calculate_fit_from_dicts(self, user_skills: list[UserSkill], requirements: list[dict]) -> dict:
        """Calculate fit score from requirement dicts (from RequirementAnalyzer) and UserSkill objects.

        Same matching logic as calculate_job_fit but works with dicts instead of DB models.
        Returns dict with keys: score, category, matched, missing.
        """
        must_haves = [r for r in requirements if r.get("requirement_type") == "must_have"]
        nice_to_haves = [r for r in requirements if r.get("requirement_type") == "nice_to_have"]

        matched = []
        missing = []

        must_have_matched = 0
        nice_to_have_matched = 0

        for req in requirements:
            req_text = req.get("requirement_text", "")
            req_type = req.get("requirement_type", "nice_to_have")
            req_category = req.get("skill_category")

            match_result = self._match_requirement_from_text(req_text, req_type, req_category, user_skills)

            if match_result["match_type"] == "full":
                matched.append(
                    {
                        "requirement": req_text,
                        "skill": match_result["skill_name"],
                        "type": req_type,
                    }
                )
                if req_type == "must_have":
                    must_have_matched += 1
                else:
                    nice_to_have_matched += 1
            elif match_result["match_type"] == "partial":
                matched.append(
                    {
                        "requirement": req_text,
                        "skill": match_result["skill_name"],
                        "type": req_type,
                        "partial": True,
                    }
                )
                if req_type == "must_have":
                    must_have_matched += 0.5
                else:
                    nice_to_have_matched += 0.5
            else:
                missing.append(
                    {
                        "requirement": req_text,
                        "type": req_type,
                    }
                )

        total_must_have = len(must_haves)
        total_nice_to_have = len(nice_to_haves)

        must_have_pct = self._calculate_percentage(must_have_matched, total_must_have)
        nice_to_have_pct = self._calculate_percentage(nice_to_have_matched, total_nice_to_have)

        if total_must_have == 0 and total_nice_to_have == 0:
            score = 50
        elif total_must_have == 0:
            score = nice_to_have_pct
        elif total_nice_to_have == 0:
            score = must_have_pct
        else:
            score = int(must_have_pct * self.MUST_HAVE_WEIGHT + nice_to_have_pct * self.NICE_TO_HAVE_WEIGHT)

        return {
            "score": score,
            "category": self._get_score_category(score),
            "matched": matched,
            "missing": missing,
        }

    def _match_requirement_from_text(
        self, req_text: str, req_type: str, req_category: str | None, user_skills: list[UserSkill]
    ) -> dict:
        """Match a requirement (raw text) against user skills.

        Returns dict with match_type (full/partial/missing) and skill_name.
        """
        req_text_lower = req_text.lower()
        req_years = self._extract_years(req_text_lower)

        best_match = None
        best_match_score = 0

        for skill in user_skills:
            skill_name_lower = skill.skill_name.lower()

            match_score = self._calculate_match_score(
                req_text_lower, skill_name_lower, req_category, skill.skill_category
            )

            if match_score > best_match_score:
                best_match_score = match_score
                best_match = skill

        if best_match and best_match_score >= 0.5:
            if req_years is not None and best_match.experience_years is not None:
                if best_match.experience_years >= req_years:
                    return {"match_type": "full", "skill_name": best_match.skill_name}
                return {"match_type": "partial", "skill_name": best_match.skill_name}
            return {"match_type": "full", "skill_name": best_match.skill_name}

        return {"match_type": "missing", "skill_name": ""}

    def _match_requirement(self, requirement: JobRequirement, user_skills: list[UserSkill]) -> SkillMatch:
        """
        Try to match a job requirement against user skills.

        Returns a SkillMatch indicating if the requirement is matched, partially matched, or missing.
        """
        req_text = requirement.requirement_text.lower()
        req_years = self._extract_years(req_text)

        best_match = None
        best_match_score = 0

        for skill in user_skills:
            skill_name_lower = skill.skill_name.lower()
            match_score = self._calculate_match_score(
                req_text, skill_name_lower, requirement.skill_category, skill.skill_category
            )

            if match_score > best_match_score:
                best_match_score = match_score
                best_match = skill

        if best_match and best_match_score >= 0.5:
            if req_years is not None and best_match.experience_years is not None:
                if best_match.experience_years >= req_years:
                    return SkillMatch(
                        requirement_text=requirement.requirement_text,
                        requirement_type=requirement.requirement_type,
                        skill_category=requirement.skill_category,
                        user_skill_name=best_match.skill_name,
                        user_experience_years=best_match.experience_years,
                        required_experience_years=req_years,
                        match_type="full",
                        match_reason=f"Skill '{best_match.skill_name}' mit {best_match.experience_years} Jahren Erfahrung erfüllt Anforderung",
                    )
                return SkillMatch(
                    requirement_text=requirement.requirement_text,
                    requirement_type=requirement.requirement_type,
                    skill_category=requirement.skill_category,
                    user_skill_name=best_match.skill_name,
                    user_experience_years=best_match.experience_years,
                    required_experience_years=req_years,
                    match_type="partial",
                    match_reason=f"Skill '{best_match.skill_name}' vorhanden, aber nur {best_match.experience_years} statt {req_years} Jahre Erfahrung",
                )
            return SkillMatch(
                requirement_text=requirement.requirement_text,
                requirement_type=requirement.requirement_type,
                skill_category=requirement.skill_category,
                user_skill_name=best_match.skill_name,
                user_experience_years=best_match.experience_years,
                required_experience_years=req_years,
                match_type="full",
                match_reason=f"Skill '{best_match.skill_name}' erfüllt Anforderung",
            )

        return SkillMatch(
            requirement_text=requirement.requirement_text,
            requirement_type=requirement.requirement_type,
            skill_category=requirement.skill_category,
            user_skill_name="",
            user_experience_years=None,
            required_experience_years=req_years,
            match_type="missing",
            match_reason="Skill nicht im Profil gefunden",
        )

    def _calculate_match_score(
        self, req_text: str, skill_name: str, req_category: str | None, skill_category: str | None
    ) -> float:
        """
        Calculate how well a user skill matches a requirement.

        Returns a score between 0 and 1.
        """
        score = 0.0

        # Direct name match (highest score)
        if skill_name in req_text:
            score = 1.0
        elif req_text in skill_name:
            score = 0.9
        else:
            # Check for known skill variations (e.g. "python" matches "django")
            if self._check_variation_match(skill_name, req_text):
                score = 0.8
            else:
                # Check for partial word matches
                skill_words = set(skill_name.split())
                req_words = set(req_text.split())
                common_words = skill_words & req_words
                if common_words:
                    # Filter out common stop words
                    meaningful_common = [w for w in common_words if len(w) > 2]
                    if meaningful_common:
                        score = len(meaningful_common) / max(len(skill_words), 1) * 0.7

        # Boost score if categories match
        if req_category and skill_category and req_category == skill_category:
            score = min(1.0, score + 0.2)

        return score

    def _check_variation_match(self, skill_name: str, req_text: str) -> bool:
        """Check if a skill matches requirement text via known variations."""
        for base_skill, alts in self.SKILL_VARIATIONS.items():
            if base_skill in skill_name and any(alt in req_text for alt in alts):
                return True
            if skill_name in alts and base_skill in req_text:
                return True
        return False

    def _extract_years(self, text: str) -> float | None:
        """Extract years of experience from requirement text."""
        patterns = [
            r"(\d+)\s*(?:\+\s*)?(?:jahre?|years?)",
            r"(\d+)\s*(?:\+\s*)?(?:j\.|jr\.?)",
            r"mind(?:estens)?\.?\s*(\d+)\s*(?:jahre?)?",
            r"(\d+)\s*-\s*\d+\s*(?:jahre?)",  # Ranges like "3-5 Jahre"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return None

    def _calculate_percentage(self, matched: float, total: int) -> int:
        """Calculate percentage score."""
        if total == 0:
            return 100
        return int((matched / total) * 100)

    def _get_score_category(self, score: int) -> str:
        """Get score category based on score value."""
        if score >= self.SCORE_SEHR_GUT:
            return "sehr_gut"
        if score >= self.SCORE_GUT:
            return "gut"
        if score >= self.SCORE_MITTEL:
            return "mittel"
        return "niedrig"

    def generate_learning_recommendations(
        self, missing_skills: list[SkillMatch], partial_matches: list[SkillMatch]
    ) -> list[LearningRecommendation]:
        """
        Generate learning recommendations for missing and partial skills using Claude API.

        Delegates to the job_fit_recommendations module.
        """
        return generate_learning_recommendations(missing_skills, partial_matches)
