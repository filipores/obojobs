"""Service layer for document data access."""

from typing import Any

from models import Document, UserSkill, db


def list_documents(user_id: int) -> list[Document]:
    """Return all documents for a user."""
    return Document.query.filter_by(user_id=user_id).all()


def get_document(doc_id: int, user_id: int) -> Document | None:
    """Return a single document owned by user, or None."""
    return Document.query.filter_by(id=doc_id, user_id=user_id).first()


def get_document_by_type(user_id: int, doc_type: str) -> Document | None:
    """Return a document of a specific type for a user, or None."""
    return Document.query.filter_by(user_id=user_id, doc_type=doc_type).first()


def create_document(user_id: int, doc_type: str, file_path: str, pdf_path: str, original_filename: str) -> Document:
    """Create and return a new Document."""
    document = Document(
        user_id=user_id,
        doc_type=doc_type,
        file_path=file_path,
        pdf_path=pdf_path,
        original_filename=original_filename,
    )
    db.session.add(document)
    db.session.commit()
    return document


def delete_document_skills(user_id: int, document_id: int) -> int:
    """Delete all skills associated with a document. Returns count deleted."""
    return UserSkill.query.filter_by(user_id=user_id, source_document_id=document_id).delete()


def delete_document(document: Document) -> None:
    """Delete a document record from the database."""
    db.session.delete(document)
    db.session.commit()


def flush() -> None:
    """Flush the current database session."""
    db.session.flush()


def commit() -> None:
    """Commit the current database session."""
    db.session.commit()


def save_extracted_skills_for_upload(user_id: int, extracted_skills: list[dict[str, Any]], document_id: int) -> int:
    """Save extracted skills during document upload. Returns count of new skills added."""
    UserSkill.query.filter_by(user_id=user_id, source_document_id=document_id).delete()

    # Pre-fetch existing skills for this user to avoid N+1 queries
    skill_names = [s["skill_name"] for s in extracted_skills]
    existing_skills = UserSkill.query.filter(
        UserSkill.user_id == user_id, UserSkill.skill_name.in_(skill_names)
    ).all()

    # Create a lookup dictionary for existing skills
    existing_map = {skill.skill_name: skill for skill in existing_skills}

    skills_extracted = 0
    for skill_data in extracted_skills:
        skill_name = skill_data["skill_name"]
        existing = existing_map.get(skill_name)

        if existing:
            if skill_data["experience_years"] and (
                existing.experience_years is None or skill_data["experience_years"] > existing.experience_years
            ):
                existing.experience_years = skill_data["experience_years"]
                existing.source_document_id = document_id
            continue

        skill = UserSkill(
            user_id=user_id,
            skill_name=skill_name,
            skill_category=skill_data["skill_category"],
            experience_years=skill_data["experience_years"],
            source_document_id=document_id,
        )
        db.session.add(skill)
        existing_map[skill_name] = skill
        skills_extracted += 1

    db.session.commit()
    return skills_extracted
