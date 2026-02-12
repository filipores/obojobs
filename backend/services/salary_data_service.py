"""Service layer for salary coach data persistence."""

import json
from typing import Any

from models import SalaryCoachData, db


def get_salary_data(user_id: int) -> SalaryCoachData | None:
    """Return the SalaryCoachData record for the user, or None."""
    return SalaryCoachData.query.filter_by(user_id=user_id).first()


def save_salary_data(user_id: int, data: dict[str, Any]) -> None:
    """Create or update salary coach data for the user.

    Args:
        user_id: The user's ID.
        data: Dict with keys formData, research, strategy.

    Raises:
        Exception: on commit failure (caller should handle).
    """
    salary_data = SalaryCoachData.query.filter_by(user_id=user_id).first()

    if not salary_data:
        salary_data = SalaryCoachData(user_id=user_id)
        db.session.add(salary_data)

    form_data = data.get("formData", {})
    salary_data.position = form_data.get("position", "").strip() or None
    salary_data.region = form_data.get("region", "").strip() or None
    salary_data.experience_years = form_data.get("experienceYears")
    salary_data.target_salary = form_data.get("targetSalary")
    salary_data.current_salary = form_data.get("currentSalary")
    salary_data.industry = form_data.get("industry", "").strip() or None

    research = data.get("research")
    salary_data.research_json = json.dumps(research) if research is not None else None

    strategy = data.get("strategy")
    salary_data.strategy_json = json.dumps(strategy) if strategy is not None else None

    db.session.commit()


def delete_salary_data(user_id: int) -> None:
    """Delete salary coach data for the user.

    Raises:
        Exception: on commit failure (caller should handle).
    """
    salary_data = SalaryCoachData.query.filter_by(user_id=user_id).first()
    if salary_data:
        db.session.delete(salary_data)
        db.session.commit()
