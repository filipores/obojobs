import logging
import os

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from config import config
from middleware.jwt_required import jwt_required_custom
from models import Document, UserSkill, db
from services.pdf_handler import extract_text_from_pdf
from services.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)

documents_bp = Blueprint("documents", __name__)

# Nur 3 Dokumenttypen erlaubt
ALLOWED_DOC_TYPES = ["lebenslauf", "anschreiben", "arbeitszeugnis"]


def allowed_file(filename):
    # Nur PDFs erlaubt
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


@documents_bp.route("", methods=["GET"])
@jwt_required_custom
def list_documents(current_user):
    """List user's documents"""
    documents = Document.query.filter_by(user_id=current_user.id).all()
    return jsonify({"success": True, "documents": [doc.to_dict() for doc in documents]}), 200


@documents_bp.route("", methods=["POST"])
@jwt_required_custom
def upload_document(current_user):
    """Upload a document (PDF only) - extracts text and saves as .txt"""
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]
    doc_type = request.form.get("doc_type")

    # Validierung
    if not doc_type or doc_type not in ALLOWED_DOC_TYPES:
        return jsonify({"error": f"Ungültiger Dokumenttyp. Erlaubt: {', '.join(ALLOWED_DOC_TYPES)}"}), 400

    if file.filename == "":
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Nur PDF-Dateien erlaubt"}), 400

    # User-Verzeichnis erstellen
    user_dir = os.path.join(config.UPLOAD_FOLDER, f"user_{current_user.id}", "documents")
    os.makedirs(user_dir, exist_ok=True)

    # Temporär PDF speichern
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(user_dir, f"temp_{filename}")
    file.save(pdf_path)

    try:
        # Text aus PDF extrahieren
        extracted_text = extract_text_from_pdf(pdf_path)

        if not extracted_text.strip():
            os.remove(pdf_path)
            return jsonify({"error": "Konnte keinen Text aus PDF extrahieren"}), 400

        # Text als .txt speichern
        txt_filename = f"{doc_type}.txt"
        txt_path = os.path.join(user_dir, txt_filename)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        # Original-PDF behalten (umbenennen statt löschen)
        permanent_pdf_path = os.path.join(user_dir, f"{doc_type}.pdf")
        os.replace(pdf_path, permanent_pdf_path)

        # Prüfen ob bereits ein Dokument dieses Typs existiert
        existing_doc = Document.query.filter_by(user_id=current_user.id, doc_type=doc_type).first()

        if existing_doc:
            # Altes Dokument aktualisieren
            existing_doc.file_path = txt_path
            existing_doc.pdf_path = permanent_pdf_path
            existing_doc.original_filename = filename
            db.session.commit()
            document = existing_doc
        else:
            # Neues Dokument erstellen
            document = Document(
                user_id=current_user.id,
                doc_type=doc_type,
                file_path=txt_path,
                pdf_path=permanent_pdf_path,
                original_filename=filename,
            )
            db.session.add(document)
            db.session.commit()

        # Automatische Skill-Extraktion für Lebensläufe
        skills_extracted = 0
        if doc_type == "lebenslauf":
            try:
                extractor = SkillExtractor()
                extracted_skills = extractor.extract_skills_from_cv(extracted_text)

                # Remove old skills from this document
                UserSkill.query.filter_by(user_id=current_user.id, source_document_id=document.id).delete()

                for skill_data in extracted_skills:
                    # Check if skill already exists
                    existing = UserSkill.query.filter_by(
                        user_id=current_user.id, skill_name=skill_data["skill_name"]
                    ).first()

                    if existing:
                        # Update if new experience is higher
                        if skill_data["experience_years"] and (
                            existing.experience_years is None
                            or skill_data["experience_years"] > existing.experience_years
                        ):
                            existing.experience_years = skill_data["experience_years"]
                            existing.source_document_id = document.id
                        continue

                    skill = UserSkill(
                        user_id=current_user.id,
                        skill_name=skill_data["skill_name"],
                        skill_category=skill_data["skill_category"],
                        experience_years=skill_data["experience_years"],
                        source_document_id=document.id,
                    )
                    db.session.add(skill)
                    skills_extracted += 1

                db.session.commit()
            except Exception as skill_error:
                logger.warning("Skill-Extraktion fehlgeschlagen: %s", skill_error)
                # Continue anyway, document upload was successful

            # Profile data extraction from CV
            profile_fields_updated = []
            try:
                from services.profile_extractor import ProfileExtractor

                profile_extractor = ProfileExtractor()
                profile_data = profile_extractor.extract_profile_from_cv(extracted_text)

                # Only fill empty fields, never overwrite existing data
                for field_name in ["full_name", "phone", "address", "city", "postal_code", "website"]:
                    current_value = getattr(current_user, field_name, None)
                    new_value = profile_data.get(field_name)
                    if not current_value and new_value:
                        setattr(current_user, field_name, new_value)
                        profile_fields_updated.append(field_name)

                if profile_fields_updated:
                    db.session.commit()
                    logger.info("Profildaten aus CV extrahiert: %s", profile_fields_updated)
            except Exception as profile_err:
                logger.warning("Profil-Extraktion fehlgeschlagen: %s", profile_err)

        response_data = {
            "success": True,
            "message": f"{doc_type.capitalize()} erfolgreich hochgeladen und Text extrahiert",
            "document": document.to_dict(),
            "text_length": len(extracted_text),
        }

        if doc_type == "lebenslauf":
            response_data["skills_extracted"] = skills_extracted
            if profile_fields_updated:
                response_data["profile_updated"] = True
                response_data["profile_fields_updated"] = profile_fields_updated

        return jsonify(response_data), 201

    except Exception as e:
        # Aufräumen bei Fehler
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return jsonify({"error": f"Fehler beim Verarbeiten der PDF: {str(e)}"}), 500


@documents_bp.route("/<int:doc_id>", methods=["GET"])
@jwt_required_custom
def get_document(doc_id, current_user):
    """Download a document (text file)"""
    document = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not document:
        return jsonify({"error": "Dokument nicht gefunden"}), 404

    if not os.path.exists(document.file_path):
        return jsonify({"error": "Datei nicht gefunden"}), 404

    # Download als .txt (extrahierter Text)
    txt_filename = f"{document.doc_type}.txt"
    return send_file(os.path.abspath(document.file_path), as_attachment=True, download_name=txt_filename)


@documents_bp.route("/<int:doc_id>", methods=["DELETE"])
@jwt_required_custom
def delete_document(doc_id, current_user):
    """Delete a document, optionally including extracted skills"""
    document = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Check if we should also delete skills
    delete_skills = request.args.get("delete_skills", "false").lower() == "true"
    skills_deleted = 0

    if delete_skills and document.doc_type == "lebenslauf":
        # Delete all skills associated with this document
        skills_deleted = UserSkill.query.filter_by(user_id=current_user.id, source_document_id=document.id).delete()
        db.session.flush()

    # Delete files
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    if document.pdf_path and os.path.exists(document.pdf_path):
        os.remove(document.pdf_path)

    # Delete record
    db.session.delete(document)
    db.session.commit()

    response = {"success": True, "message": "Dokument gelöscht"}
    if delete_skills and skills_deleted > 0:
        response["skills_deleted"] = skills_deleted
        response["message"] = f"Dokument und {skills_deleted} Skills gelöscht"

    return jsonify(response), 200
