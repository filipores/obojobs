"""
Data models for Job-Fit Calculator Service.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LearningRecommendation:
    """Learning recommendation for a missing skill."""

    skill_name: str
    category: str  # online_course, certification, project_idea, book
    title: str
    description: str
    resource_url: str | None
    priority: str  # high, medium, low (based on requirement type)


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
    learning_recommendations: list[LearningRecommendation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "score_category": self.score_category,
            "score_label": self._get_score_label(),
            "must_have_score": self.must_have_score,
            "nice_to_have_score": self.nice_to_have_score,
            "matched_skills": [self._skill_match_to_dict(s) for s in self.matched_skills],
            "partial_matches": [self._skill_match_to_dict(s) for s in self.partial_matches],
            "missing_skills": [self._skill_match_to_dict(s) for s in self.missing_skills],
            "learning_recommendations": [self._recommendation_to_dict(r) for r in self.learning_recommendations],
            "summary": {
                "total_must_have": self.total_must_have,
                "matched_must_have": self.matched_must_have,
                "total_nice_to_have": self.total_nice_to_have,
                "matched_nice_to_have": self.matched_nice_to_have,
            },
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
    def _skill_match_to_dict(match: SkillMatch) -> dict[str, Any]:
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

    @staticmethod
    def _recommendation_to_dict(rec: LearningRecommendation) -> dict[str, Any]:
        return {
            "skill_name": rec.skill_name,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "resource_url": rec.resource_url,
            "priority": rec.priority,
        }
