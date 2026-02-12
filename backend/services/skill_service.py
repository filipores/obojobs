"""Service layer for user skill data access."""

from models import Document, UserSkill, db

VALID_CATEGORIES = UserSkill.VALID_CATEGORIES


def validate_category(category):
    """Check if a category is valid."""
    return UserSkill.validate_category(category)


def get_user_skills(user_id):
    """Return all skills for a user, ordered by category and name."""
    return UserSkill.query.filter_by(user_id=user_id).order_by(UserSkill.skill_category, UserSkill.skill_name).all()


def get_skill(skill_id, user_id):
    """Return a single skill owned by user, or None."""
    return UserSkill.query.filter_by(id=skill_id, user_id=user_id).first()


def find_skill_by_name(user_id, skill_name):
    """Return an existing skill by name for a user, or None."""
    return UserSkill.query.filter_by(user_id=user_id, skill_name=skill_name).first()


def create_skill(user_id, skill_name, skill_category, experience_years=None, source_document_id=None):
    """Create and return a new UserSkill."""
    skill = UserSkill(
        user_id=user_id,
        skill_name=skill_name,
        skill_category=skill_category,
        experience_years=experience_years,
        source_document_id=source_document_id,
    )
    db.session.add(skill)
    db.session.commit()
    return skill


def delete_skill(skill_id, user_id):
    """Delete a skill. Returns the skill or None if not found."""
    skill = UserSkill.query.filter_by(id=skill_id, user_id=user_id).first()
    if not skill:
        return None
    db.session.delete(skill)
    db.session.commit()
    return skill


def commit():
    """Commit the current database session."""
    db.session.commit()


def get_document(doc_id, user_id):
    """Return a single document owned by user, or None."""
    return Document.query.filter_by(id=doc_id, user_id=user_id).first()


def delete_skills_by_document(user_id, document_id):
    """Delete all skills associated with a document. Returns the count deleted."""
    return UserSkill.query.filter_by(user_id=user_id, source_document_id=document_id).delete()


def save_extracted_skills(user_id, extracted_skills, document_id):
    """Save extracted skills, avoiding duplicates. Returns (added_skills, skipped_count)."""
    # Remove existing skills from this document
    UserSkill.query.filter_by(user_id=user_id, source_document_id=document_id).delete()

    added_skills = []
    skipped_count = 0

    for skill_data in extracted_skills:
        existing = UserSkill.query.filter_by(user_id=user_id, skill_name=skill_data["skill_name"]).first()

        if existing:
            if skill_data["experience_years"] and (
                existing.experience_years is None or skill_data["experience_years"] > existing.experience_years
            ):
                existing.experience_years = skill_data["experience_years"]
                existing.source_document_id = document_id
            skipped_count += 1
            continue

        skill = UserSkill(
            user_id=user_id,
            skill_name=skill_data["skill_name"],
            skill_category=skill_data["skill_category"],
            experience_years=skill_data["experience_years"],
            source_document_id=document_id,
        )
        db.session.add(skill)
        added_skills.append(skill)

    db.session.commit()
    return added_skills, skipped_count
