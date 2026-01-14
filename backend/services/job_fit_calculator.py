"""
Job-Fit Calculator Service - Calculates match score between user skills and job requirements.
"""

import re
from dataclasses import dataclass

from models import JobRequirement, UserSkill


@dataclass
class SkillMatch:
    """Represents a matched skill between user and job requirement."""
    requirement_text: str
    requirement_type: str  # must_have or nice_to_have
    skill_category: str | None
    user_skill_name: str
    user_experience_years: float | None
    required_experience_years: float | None
    match_type: str  # full, partial, missing
    match_reason: str


@dataclass
class JobFitResult:
    """Result of job-fit calculation."""
    overall_score: int  # 0-100
    score_category: str  # sehr_gut, gut, mittel, niedrig
    must_have_score: int  # 0-100
    nice_to_have_score: int  # 0-100
    matched_skills: list[SkillMatch]
    partial_matches: list[SkillMatch]
    missing_skills: list[SkillMatch]
    total_must_have: int
    matched_must_have: int
    total_nice_to_have: int
    matched_nice_to_have: int

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "score_category": self.score_category,
            "score_label": self._get_score_label(),
            "must_have_score": self.must_have_score,
            "nice_to_have_score": self.nice_to_have_score,
            "matched_skills": [self._skill_match_to_dict(s) for s in self.matched_skills],
            "partial_matches": [self._skill_match_to_dict(s) for s in self.partial_matches],
            "missing_skills": [self._skill_match_to_dict(s) for s in self.missing_skills],
            "summary": {
                "total_must_have": self.total_must_have,
                "matched_must_have": self.matched_must_have,
                "total_nice_to_have": self.total_nice_to_have,
                "matched_nice_to_have": self.matched_nice_to_have,
            }
        }

    def _get_score_label(self) -> str:
        labels = {
            "sehr_gut": "Sehr gut",
            "gut": "Gut",
            "mittel": "Mittel",
            "niedrig": "Niedrig",
        }
        return labels.get(self.score_category, self.score_category)

    @staticmethod
    def _skill_match_to_dict(match: SkillMatch) -> dict:
        return {
            "requirement_text": match.requirement_text,
            "requirement_type": match.requirement_type,
            "skill_category": match.skill_category,
            "user_skill_name": match.user_skill_name,
            "user_experience_years": match.user_experience_years,
            "required_experience_years": match.required_experience_years,
            "match_type": match.match_type,
            "match_reason": match.match_reason,
        }


class JobFitCalculator:
    """Service to calculate job-fit score between user skills and job requirements."""

    # Weighting: 70% must-have, 30% nice-to-have
    MUST_HAVE_WEIGHT = 0.70
    NICE_TO_HAVE_WEIGHT = 0.30

    # Score categories
    SCORE_SEHR_GUT = 80
    SCORE_GUT = 60
    SCORE_MITTEL = 40

    def __init__(self):
        pass

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
            overall_score = int(
                must_have_score * self.MUST_HAVE_WEIGHT +
                nice_to_have_score * self.NICE_TO_HAVE_WEIGHT
            )

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

            # Check if skill matches requirement
            match_score = self._calculate_match_score(req_text, skill_name_lower, requirement.skill_category, skill.skill_category)

            if match_score > best_match_score:
                best_match_score = match_score
                best_match = skill

        if best_match and best_match_score >= 0.5:
            # Found a matching skill
            if req_years is not None and best_match.experience_years is not None:
                # Check experience years
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
                else:
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
            else:
                # No experience years comparison needed
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

        # No match found
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
        self,
        req_text: str,
        skill_name: str,
        req_category: str | None,
        skill_category: str | None
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
        elif score >= self.SCORE_GUT:
            return "gut"
        elif score >= self.SCORE_MITTEL:
            return "mittel"
        else:
            return "niedrig"
