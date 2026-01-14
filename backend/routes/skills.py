"""
Skills API Routes - Manage user skills extracted from CV documents.
"""

import os

from flask import Blueprint, jsonify, request

from middleware.jwt_required import jwt_required_custom
from models import Document, UserSkill, db
from services.skill_extractor import SkillExtractor

skills_bp = Blueprint("skills", __name__)


@skills_bp.route("/users/me/skills", methods=["GET"])
@jwt_required_custom
def get_user_skills(current_user):
    """Get all skills for the current user."""
    skills = UserSkill.query.filter_by(user_id=current_user.id).order_by(UserSkill.skill_category, UserSkill.skill_name).all()

    # Group by category for easier frontend consumption
    skills_by_category = {}
    for skill in skills:
        category = skill.skill_category
        if category not in skills_by_category:
            skills_by_category[category] = []
        skills_by_category[category].append(skill.to_dict())

    return jsonify(
        {
            "success": True,
            "skills": [skill.to_dict() for skill in skills],
            "skills_by_category": skills_by_category,
            "total_count": len(skills),
        }
    ), 200


@skills_bp.route("/users/me/skills/<int:skill_id>", methods=["PUT"])
@jwt_required_custom
def update_skill(skill_id, current_user):
    """Update a skill (edit name, category, or experience years)."""
    skill = UserSkill.query.filter_by(id=skill_id, user_id=current_user.id).first()

    if not skill:
        return jsonify({"error": "Skill nicht gefunden"}), 404

    data = request.get_json()

    # Update fields if provided
    if "skill_name" in data:
        skill_name = data["skill_name"].strip()
        if not skill_name:
            return jsonify({"error": "Skill-Name darf nicht leer sein"}), 400
        skill.skill_name = skill_name

    if "skill_category" in data:
        skill_category = data["skill_category"].strip().lower()
        if not UserSkill.validate_category(skill_category):
            return jsonify({"error": f"Ungültige Kategorie. Erlaubt: {', '.join(UserSkill.VALID_CATEGORIES)}"}), 400
        skill.skill_category = skill_category

    if "experience_years" in data:
        exp_years = data["experience_years"]
        if exp_years is not None:
            try:
                exp_years = float(exp_years)
                if exp_years < 0:
                    return jsonify({"error": "Erfahrungsjahre dürfen nicht negativ sein"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Ungültiger Wert für Erfahrungsjahre"}), 400
        skill.experience_years = exp_years

    db.session.commit()

    return jsonify({"success": True, "message": "Skill aktualisiert", "skill": skill.to_dict()}), 200


@skills_bp.route("/users/me/skills/<int:skill_id>", methods=["DELETE"])
@jwt_required_custom
def delete_skill(skill_id, current_user):
    """Delete a skill."""
    skill = UserSkill.query.filter_by(id=skill_id, user_id=current_user.id).first()

    if not skill:
        return jsonify({"error": "Skill nicht gefunden"}), 404

    db.session.delete(skill)
    db.session.commit()

    return jsonify({"success": True, "message": "Skill gelöscht"}), 200


@skills_bp.route("/users/me/skills", methods=["POST"])
@jwt_required_custom
def add_skill(current_user):
    """Manually add a skill."""
    data = request.get_json()

    skill_name = data.get("skill_name", "").strip()
    skill_category = data.get("skill_category", "").strip().lower()
    experience_years = data.get("experience_years")

    # Validation
    if not skill_name:
        return jsonify({"error": "Skill-Name ist erforderlich"}), 400

    if not skill_category or not UserSkill.validate_category(skill_category):
        return jsonify({"error": f"Gültige Kategorie erforderlich: {', '.join(UserSkill.VALID_CATEGORIES)}"}), 400

    # Check for duplicate
    existing = UserSkill.query.filter_by(user_id=current_user.id, skill_name=skill_name).first()
    if existing:
        return jsonify({"error": f"Skill '{skill_name}' existiert bereits"}), 409

    # Validate experience_years
    if experience_years is not None:
        try:
            experience_years = float(experience_years)
            if experience_years < 0:
                return jsonify({"error": "Erfahrungsjahre dürfen nicht negativ sein"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Ungültiger Wert für Erfahrungsjahre"}), 400

    skill = UserSkill(
        user_id=current_user.id,
        skill_name=skill_name,
        skill_category=skill_category,
        experience_years=experience_years,
        source_document_id=None,  # Manual entry
    )

    db.session.add(skill)
    db.session.commit()

    return jsonify({"success": True, "message": "Skill hinzugefügt", "skill": skill.to_dict()}), 201


@skills_bp.route("/documents/<int:doc_id>/extract-skills", methods=["POST"])
@jwt_required_custom
def extract_skills_from_document(doc_id, current_user):
    """Extract skills from a document using AI."""
    document = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not document:
        return jsonify({"error": "Dokument nicht gefunden"}), 404

    # Only extract from CV documents
    if document.doc_type != "lebenslauf":
        return jsonify({"error": "Skill-Extraktion nur für Lebensläufe verfügbar"}), 400

    # Read document text
    if not os.path.exists(document.file_path):
        return jsonify({"error": "Dokumentdatei nicht gefunden"}), 404

    with open(document.file_path, encoding="utf-8") as f:
        cv_text = f.read()

    if not cv_text.strip():
        return jsonify({"error": "Dokument ist leer"}), 400

    try:
        # Extract skills using AI
        extractor = SkillExtractor()
        extracted_skills = extractor.extract_skills_from_cv(cv_text)

        if not extracted_skills:
            return jsonify({"error": "Keine Skills konnten extrahiert werden"}), 400

        # Remove existing skills from this document
        UserSkill.query.filter_by(user_id=current_user.id, source_document_id=doc_id).delete()

        # Add new skills (avoid duplicates by skill_name)
        added_skills = []
        skipped_count = 0

        for skill_data in extracted_skills:
            # Check if skill already exists for user
            existing = UserSkill.query.filter_by(user_id=current_user.id, skill_name=skill_data["skill_name"]).first()

            if existing:
                # Update experience years if new is higher
                if skill_data["experience_years"] and (
                    existing.experience_years is None or skill_data["experience_years"] > existing.experience_years
                ):
                    existing.experience_years = skill_data["experience_years"]
                    existing.source_document_id = doc_id
                skipped_count += 1
                continue

            skill = UserSkill(
                user_id=current_user.id,
                skill_name=skill_data["skill_name"],
                skill_category=skill_data["skill_category"],
                experience_years=skill_data["experience_years"],
                source_document_id=doc_id,
            )
            db.session.add(skill)
            added_skills.append(skill)

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"{len(added_skills)} neue Skills extrahiert, {skipped_count} bereits vorhanden",
                "skills": [skill.to_dict() for skill in added_skills],
                "total_extracted": len(extracted_skills),
                "new_skills_count": len(added_skills),
                "skipped_count": skipped_count,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Fehler bei der Skill-Extraktion: {str(e)}"}), 500
