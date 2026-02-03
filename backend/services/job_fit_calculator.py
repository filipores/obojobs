"""
Job-Fit Calculator Service - Calculates match score between user skills and job requirements.
"""

import json
import re
from dataclasses import dataclass, field

from anthropic import Anthropic

from config import config
from models import JobRequirement, UserSkill


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

    @staticmethod
    def _recommendation_to_dict(rec: LearningRecommendation) -> dict:
        return {
            "skill_name": rec.skill_name,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "resource_url": rec.resource_url,
            "priority": rec.priority,
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
            match_score = self._calculate_match_score(
                req_text, skill_name_lower, requirement.skill_category, skill.skill_category
            )

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

    def generate_learning_recommendations(
        self, missing_skills: list[SkillMatch], partial_matches: list[SkillMatch]
    ) -> list[LearningRecommendation]:
        """
        Generate learning recommendations for missing and partial skills using Claude API.

        Args:
            missing_skills: List of completely missing skills
            partial_matches: List of skills that need more experience

        Returns:
            List of LearningRecommendation objects with learning paths
        """
        # Combine missing and partial skills for recommendations
        skills_to_learn = []

        for skill in missing_skills:
            skills_to_learn.append(
                {
                    "skill": skill.requirement_text,
                    "priority": "high" if skill.requirement_type == "must_have" else "medium",
                    "type": "missing",
                    "category": skill.skill_category,
                }
            )

        for skill in partial_matches:
            skills_to_learn.append(
                {
                    "skill": skill.requirement_text,
                    "priority": "medium" if skill.requirement_type == "must_have" else "low",
                    "type": "improve",
                    "current_years": skill.user_experience_years,
                    "required_years": skill.required_experience_years,
                    "category": skill.skill_category,
                }
            )

        if not skills_to_learn:
            return []

        # Limit to top 10 skills to keep prompt manageable
        skills_to_learn = skills_to_learn[:10]

        try:
            api_key = config.ANTHROPIC_API_KEY
            if not api_key:
                return self._generate_fallback_recommendations(skills_to_learn)

            client = Anthropic(api_key=api_key)

            prompt = f"""Du bist ein Karriereberater. Erstelle Lernempfehlungen für folgende fehlende Skills.

FEHLENDE SKILLS:
{json.dumps(skills_to_learn, ensure_ascii=False, indent=2)}

Für jeden Skill, gib 1-2 Empfehlungen aus verschiedenen Kategorien:
- online_course: Online-Kurse (Coursera, Udemy, LinkedIn Learning)
- certification: Zertifizierungen
- project_idea: Praktische Projekt-Ideen zum Üben
- book: Buchempfehlungen

Antworte im JSON-Format:
{{
  "recommendations": [
    {{
      "skill_name": "Python",
      "category": "online_course",
      "title": "Python für Data Science - Coursera",
      "description": "Umfassender Kurs für Python-Grundlagen und Data Science Anwendungen",
      "resource_url": "https://www.coursera.org/learn/python",
      "priority": "high"
    }},
    {{
      "skill_name": "Python",
      "category": "project_idea",
      "title": "Datenanalyse-Projekt",
      "description": "Analysiere einen öffentlichen Datensatz (z.B. von Kaggle) und erstelle Visualisierungen",
      "resource_url": null,
      "priority": "high"
    }}
  ]
}}

WICHTIG:
- Verwende generische URLs für bekannte Plattformen (Coursera, Udemy, etc.)
- Für Zertifizierungen nenne die offiziellen Zertifizierungsstellen
- Sei konkret bei Projekt-Ideen
- priority übernehmen von den Input-Skills

Antworte NUR mit dem JSON."""

            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text.strip()

            # Parse JSON response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if not json_match:
                return self._generate_fallback_recommendations(skills_to_learn)

            result = json.loads(json_match.group())
            recommendations_data = result.get("recommendations", [])

            recommendations = []
            for rec in recommendations_data:
                recommendations.append(
                    LearningRecommendation(
                        skill_name=rec.get("skill_name", ""),
                        category=rec.get("category", "online_course"),
                        title=rec.get("title", ""),
                        description=rec.get("description", ""),
                        resource_url=rec.get("resource_url"),
                        priority=rec.get("priority", "medium"),
                    )
                )

            return recommendations

        except Exception:
            return self._generate_fallback_recommendations(skills_to_learn)

    def _generate_fallback_recommendations(self, skills_to_learn: list[dict]) -> list[LearningRecommendation]:
        """Generate basic recommendations without API call."""
        recommendations = []

        # Generic resource URLs by category
        resource_urls = {
            "technical": {
                "online_course": "https://www.coursera.org",
                "certification": "https://www.linkedin.com/learning",
                "book": "https://www.oreilly.com",
            },
            "soft_skills": {
                "online_course": "https://www.linkedin.com/learning",
                "book": "https://www.amazon.de",
            },
            "languages": {
                "online_course": "https://www.udemy.com",
                "certification": "https://www.goethe.de",
            },
            "tools": {
                "online_course": "https://www.udemy.com",
                "certification": None,
            },
            "certifications": {
                "online_course": "https://www.coursera.org",
                "certification": None,
            },
        }

        for skill_data in skills_to_learn:
            skill_name = skill_data["skill"]
            priority = skill_data["priority"]
            category = skill_data.get("category") or "technical"

            # Add online course recommendation
            recommendations.append(
                LearningRecommendation(
                    skill_name=skill_name,
                    category="online_course",
                    title=f"Online-Kurs: {skill_name}",
                    description=f"Suche nach einem passenden Online-Kurs zu '{skill_name}' auf gängigen Lernplattformen.",
                    resource_url=resource_urls.get(category, {}).get("online_course", "https://www.coursera.org"),
                    priority=priority,
                )
            )

            # Add project idea for technical skills
            if category in ["technical", "tools"]:
                recommendations.append(
                    LearningRecommendation(
                        skill_name=skill_name,
                        category="project_idea",
                        title=f"Praxis-Projekt: {skill_name}",
                        description=f"Erstelle ein kleines Projekt, das '{skill_name}' praktisch anwendet. Dokumentiere es auf GitHub.",
                        resource_url="https://github.com",
                        priority=priority,
                    )
                )

        return recommendations
