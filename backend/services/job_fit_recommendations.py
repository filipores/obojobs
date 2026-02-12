"""
Learning recommendation generation for Job-Fit Calculator Service.

Generates learning recommendations for missing/partial skills using Claude API
with a fallback to generic recommendations.
"""

import json
import re

from anthropic import Anthropic

from config import config
from services.job_fit_models import LearningRecommendation, SkillMatch


def generate_learning_recommendations(
    missing_skills: list[SkillMatch], partial_matches: list[SkillMatch]
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
            return _generate_fallback_recommendations(skills_to_learn)

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
            return _generate_fallback_recommendations(skills_to_learn)

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
        return _generate_fallback_recommendations(skills_to_learn)


def _generate_fallback_recommendations(skills_to_learn: list[dict]) -> list[LearningRecommendation]:
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
