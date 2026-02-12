"""Service layer for document data access."""

from models import Document, UserSkill, db


def list_documents(user_id):
    """Return all documents for a user."""
    return Document.query.filter_by(user_id=user_id).all()


def get_document(doc_id, user_id):
    """Return a single document owned by user, or None."""
    return Document.query.filter_by(id=doc_id, user_id=user_id).first()


def get_document_by_type(user_id, doc_type):
    """Return a document of a specific type for a user, or None."""
    return Document.query.filter_by(user_id=user_id, doc_type=doc_type).first()


def create_document(user_id, doc_type, file_path, pdf_path, original_filename):
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


def delete_document_skills(user_id, document_id):
    """Delete all skills associated with a document. Returns count deleted."""
    return UserSkill.query.filter_by(user_id=user_id, source_document_id=document_id).delete()


def delete_document(document):
    """Delete a document record from the database."""
    db.session.delete(document)
    db.session.commit()


def flush():
    """Flush the current database session."""
    db.session.flush()


def commit():
    """Commit the current database session."""
    db.session.commit()


def save_extracted_skills_for_upload(user_id, extracted_skills, document_id):
    """Save extracted skills during document upload. Returns count of new skills added."""
    UserSkill.query.filter_by(user_id=user_id, source_document_id=document_id).delete()

    skills_extracted = 0
    for skill_data in extracted_skills:
        existing = UserSkill.query.filter_by(user_id=user_id, skill_name=skill_data["skill_name"]).first()

        if existing:
            if skill_data["experience_years"] and (
                existing.experience_years is None or skill_data["experience_years"] > existing.experience_years
            ):
                existing.experience_years = skill_data["experience_years"]
                existing.source_document_id = document_id
            continue

        skill = UserSkill(
            user_id=user_id,
            skill_name=skill_data["skill_name"],
            skill_category=skill_data["skill_category"],
            experience_years=skill_data["experience_years"],
            source_document_id=document_id,
        )
        db.session.add(skill)
        skills_extracted += 1

    db.session.commit()
    return skills_extracted
