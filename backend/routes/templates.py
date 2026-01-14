import json
import os
import re

from flask import Blueprint, jsonify, request

from middleware.api_key_required import api_key_required
from middleware.jwt_required import jwt_required_custom
from models import Document, Template, db
from services.api_client import ClaudeAPIClient
from services.pdf_handler import read_document

# Validation constants
MAX_NAME_LENGTH = 200
MAX_CONTENT_LENGTH = 100000  # 100KB
MAX_PROMPT_INPUT_LENGTH = 2000
MAX_CV_LENGTH = 10000


def sanitize_text(text, max_length=None):
    """Sanitize text input by removing control characters"""
    if not text:
        return ""
    text = str(text).strip()
    # Remove control characters except newlines and tabs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    if max_length:
        text = text[:max_length]
    return text


def sanitize_prompt_input(text, max_length=MAX_PROMPT_INPUT_LENGTH):
    """Sanitize user input for AI prompts to prevent prompt injection"""
    if not text:
        return ""

    text = sanitize_text(text, max_length)

    # Remove potential prompt injection markers
    dangerous_patterns = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?previous",
        r"system\s*:",
        r"assistant\s*:",
        r"human\s*:",
        r"<\s*/?\s*script",
        r"---SUGGESTIONS_JSON---",
        r"---END_SUGGESTIONS---",
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()


def parse_ai_response_with_suggestions(response_text):
    """
    Parse AI response to extract template and suggestions.
    Expected format:
    [Template content]
    ---SUGGESTIONS_JSON---
    [{"text": "...", "variable": "FIRMA", "reason": "..."}]
    ---END_SUGGESTIONS---
    """
    template_text = response_text
    suggestions = []

    if "---SUGGESTIONS_JSON---" in response_text:
        parts = response_text.split("---SUGGESTIONS_JSON---")
        template_text = parts[0].strip()

        if len(parts) > 1 and "---END_SUGGESTIONS---" in parts[1]:
            json_part = parts[1].split("---END_SUGGESTIONS---")[0].strip()
            try:
                raw_suggestions = json.loads(json_part)

                # Process suggestions and calculate indices
                for i, sug in enumerate(raw_suggestions):
                    text = sug.get("text", "")
                    start_idx = template_text.find(text)

                    if start_idx != -1:
                        suggestions.append(
                            {
                                "id": f"sug_{i}_{hash(text) % 10000}",
                                "text": text,
                                "suggestedVariable": sug.get("variable", "FIRMA"),
                                "reason": sug.get("reason", ""),
                            }
                        )
            except json.JSONDecodeError as e:
                # Log parsing failure for debugging, but continue without suggestions
                print(f"Warning: Failed to parse suggestions JSON: {str(e)}")
                print(f"Raw JSON part (first 200 chars): {json_part[:200] if json_part else 'empty'}")

    return template_text, suggestions


templates_bp = Blueprint("templates", __name__)


@templates_bp.route("", methods=["GET"])
@jwt_required_custom
def list_templates(current_user):
    """List user's templates"""
    templates = Template.query.filter_by(user_id=current_user.id).all()
    return jsonify({"success": True, "templates": [t.to_dict() for t in templates]}), 200


@templates_bp.route("", methods=["POST"])
@jwt_required_custom
def create_template(current_user):
    """Create a template"""
    data = request.json

    name = sanitize_text(data.get("name", ""), MAX_NAME_LENGTH)
    content = sanitize_text(data.get("content", ""), MAX_CONTENT_LENGTH)

    if not name or not content:
        return jsonify({"error": "Name und Inhalt sind erforderlich"}), 400

    if len(name) > MAX_NAME_LENGTH:
        return jsonify({"error": f"Name zu lang (max. {MAX_NAME_LENGTH} Zeichen)"}), 400

    if len(content) > MAX_CONTENT_LENGTH:
        return jsonify({"error": f"Inhalt zu lang (max. {MAX_CONTENT_LENGTH} Zeichen)"}), 400

    is_default = bool(data.get("is_default", False))

    # Use transaction for atomic default switching
    try:
        if is_default:
            Template.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})
            db.session.flush()

        template = Template(user_id=current_user.id, name=name, content=content, is_default=is_default)

        db.session.add(template)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Fehler beim Erstellen des Templates"}), 500

    return jsonify({"success": True, "template": template.to_dict()}), 201


@templates_bp.route("/<int:template_id>", methods=["GET"])
@jwt_required_custom
def get_template(template_id, current_user):
    """Get a template"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({"error": "Template nicht gefunden"}), 404

    return jsonify({"success": True, "template": template.to_dict()}), 200


@templates_bp.route("/<int:template_id>", methods=["PUT"])
@jwt_required_custom
def update_template(template_id, current_user):
    """Update a template"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({"error": "Template nicht gefunden"}), 404

    data = request.json

    try:
        if "name" in data:
            name = sanitize_text(data["name"], MAX_NAME_LENGTH)
            if not name:
                return jsonify({"error": "Name darf nicht leer sein"}), 400
            template.name = name

        if "content" in data:
            content = sanitize_text(data["content"], MAX_CONTENT_LENGTH)
            if not content:
                return jsonify({"error": "Inhalt darf nicht leer sein"}), 400
            template.content = content

        # Handle is_default with proper transaction
        if "is_default" in data:
            if data["is_default"]:
                Template.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})
                template.is_default = True
            else:
                template.is_default = False

        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Fehler beim Aktualisieren des Templates"}), 500

    return jsonify({"success": True, "template": template.to_dict()}), 200


@templates_bp.route("/<int:template_id>/default", methods=["PUT"])
@jwt_required_custom
def set_default_template(template_id, current_user):
    """Set template as default"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({"error": "Template nicht gefunden"}), 404

    # Unset all defaults
    Template.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})

    # Set this as default
    template.is_default = True
    db.session.commit()

    return jsonify({"success": True, "template": template.to_dict()}), 200


@templates_bp.route("/<int:template_id>", methods=["DELETE"])
@jwt_required_custom
def delete_template(template_id, current_user):
    """Delete a template"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({"error": "Template nicht gefunden"}), 404

    db.session.delete(template)
    db.session.commit()

    return jsonify({"success": True, "message": "Template gelöscht"}), 200


@templates_bp.route("/generate", methods=["POST"])
@jwt_required_custom
def generate_template_with_ai(current_user):
    """Generate a template using AI based on CV and user inputs"""
    data = request.json

    # Sanitize and validate all user inputs to prevent prompt injection
    sektor = sanitize_prompt_input(data.get("sektor", ""), 200)
    projekte = sanitize_prompt_input(data.get("projekte", ""), MAX_PROMPT_INPUT_LENGTH)
    leidenschaften = sanitize_prompt_input(data.get("leidenschaften", ""), MAX_PROMPT_INPUT_LENGTH)
    hobbys = sanitize_prompt_input(data.get("hobbys", ""), 500)
    tonalitaet = sanitize_text(data.get("tonalitaet", ""), 20)

    # Validate tonalitaet is one of allowed values
    allowed_tones = ["formal", "modern", "kreativ"]
    if tonalitaet not in allowed_tones:
        tonalitaet = "modern"

    if not sektor or not projekte or not leidenschaften:
        return jsonify({"error": "Sektor, Projekte und Leidenschaften sind erforderlich"}), 400

    # Lebenslauf laden
    cv_doc = Document.query.filter_by(user_id=current_user.id, doc_type="lebenslauf").first()
    if not cv_doc or not os.path.exists(cv_doc.file_path):
        return jsonify({"error": "Lebenslauf nicht gefunden. Bitte lade zuerst deinen Lebenslauf hoch."}), 400

    try:
        cv_text = read_document(cv_doc.file_path)
        # Sanitize CV text as well (user-uploaded content)
        cv_text = sanitize_prompt_input(cv_text, MAX_CV_LENGTH)

        # Claude API Prompt erstellen
        api_client = ClaudeAPIClient()

        # Tonalität-Beschreibungen
        tone_descriptions = {
            "formal": 'sehr professionell, höflich und klassisch. Verwende Formulierungen wie "Sehr geehrte Damen und Herren" und "Mit freundlichen Grüßen".',
            "modern": "professionell aber etwas lockerer. Verwende moderne Formulierungen, bleibe aber respektvoll.",
            "kreativ": "persönlich und authentisch. Zeige Persönlichkeit, aber bleibe professionell.",
        }
        tone_desc = tone_descriptions.get(tonalitaet, tone_descriptions["modern"])

        prompt = f"""Erstelle ein Anschreiben-Template für Bewerbungen basierend auf den folgenden Informationen:

**Lebenslauf des Bewerbers:**
{cv_text}

**Zielsektor:** {sektor}

**Wichtige Projekte/Erfolge:**
{projekte}

**Was dem Bewerber wichtig ist:**
{leidenschaften}

**Hobbys/Interessen** (falls relevant):
{hobbys if hobbys else "Keine angegeben"}

**Gewünschte Tonalität:**
Das Anschreiben soll {tone_desc}

**WICHTIG - AUSGABEFORMAT:**
1. Schreibe zuerst das VOLLSTÄNDIGE Anschreiben als normalen Text (OHNE Platzhalter wie {{{{FIRMA}}}} etc.)
2. Das Anschreiben soll ca. 200-300 Wörter lang sein
3. Danach füge ZWINGEND eine JSON-Sektion hinzu mit Vorschlägen, welche Passagen dynamisch sein sollten

**FORMAT:**
[Dein vollständiges Anschreiben hier - ohne Platzhalter, mit echten Beispieltexten]

---SUGGESTIONS_JSON---
[
  {{"text": "der exakte Text der ersetzt werden soll", "variable": "FIRMA", "reason": "Kurze Begründung"}},
  {{"text": "weiterer Text", "variable": "POSITION", "reason": "Begründung"}}
]
---END_SUGGESTIONS---

**VERFÜGBARE VARIABLEN:**
- FIRMA: Firmenname (z.B. "Musterfirma GmbH" → wird zu dynamischem Platzhalter)
- POSITION: Stellenbezeichnung (z.B. "Softwareentwickler" → dynamisch)
- ANSPRECHPARTNER: Komplette Anrede (z.B. "Sehr geehrte Frau Müller" → dynamisch)
- QUELLE: Wo die Stelle gefunden wurde (z.B. "auf LinkedIn" → dynamisch)
- EINLEITUNG: Ein personalisierbarer Einleitungsabsatz (2-4 Sätze, die auf die Stelle eingehen)

**REGELN FÜR SUGGESTIONS:**
- Schlage 3-6 Passagen vor, die dynamisch sein sollten
- Der "text" muss EXAKT im Anschreiben vorkommen
- Mindestens FIRMA, POSITION und ANSPRECHPARTNER vorschlagen
- Optional: QUELLE oder EINLEITUNG wenn passend

Generiere jetzt das Anschreiben mit Suggestions:"""

        # Claude API Call
        response = api_client.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_response = response.content[0].text.strip()

        # Parse response to extract template and suggestions
        generated_content, suggestions = parse_ai_response_with_suggestions(raw_response)

        # Template speichern
        template_name = f"KI-generiert ({sektor})"

        # Unset andere defaults
        Template.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})

        template = Template(user_id=current_user.id, name=template_name, content=generated_content, is_default=True)

        db.session.add(template)
        db.session.commit()

        # Return template with suggestions
        template_dict = template.to_dict()
        template_dict["suggestions"] = suggestions

        return jsonify({"success": True, "message": "Template erfolgreich generiert!", "template": template_dict}), 201

    except Exception as e:
        print(f"Fehler bei Template-Generierung: {str(e)}")
        return jsonify({"error": f"Fehler beim Generieren: {str(e)}"}), 500


@templates_bp.route("/list-simple", methods=["GET"])
@api_key_required  # Extension uses API key
def list_templates_simple(current_user):
    """List user's templates (simplified for extension)"""
    templates = (
        Template.query.filter_by(user_id=current_user.id)
        .order_by(Template.is_default.desc(), Template.created_at.desc())
        .all()
    )

    return jsonify(
        {"success": True, "templates": [{"id": t.id, "name": t.name, "is_default": t.is_default} for t in templates]}
    ), 200
