import json
import os
import re
import time

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from config import config
from middleware.api_key_required import api_key_required
from middleware.jwt_required import jwt_required_custom
from models import Document, Template, db
from services.api_client import ClaudeAPIClient
from services.pdf_handler import read_document
from services.pdf_template_extractor import PDFTemplateExtractor

# Validation constants
MAX_NAME_LENGTH = 200
MAX_CONTENT_LENGTH = 100000  # 100KB
MAX_PROMPT_INPUT_LENGTH = 2000
MAX_CV_LENGTH = 10000
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_pdf_file(filename):
    """Check if file is a PDF based on extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


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


@templates_bp.route("/upload-pdf", methods=["POST"])
@jwt_required_custom
def upload_pdf_template(current_user):
    """Upload a PDF template and extract text with positions"""
    # Validate file presence
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    # Validate file type (PDF only)
    if not allowed_pdf_file(file.filename):
        return jsonify({"error": "Nur PDF-Dateien erlaubt"}), 400

    # Validate file size (max 10MB)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > MAX_PDF_SIZE:
        return jsonify({"error": f"Datei zu groß. Maximale Größe: {MAX_PDF_SIZE // (1024 * 1024)}MB"}), 400

    # Get optional template name from form data
    template_name = sanitize_text(request.form.get("name", ""), MAX_NAME_LENGTH)
    if not template_name:
        template_name = os.path.splitext(file.filename)[0][:MAX_NAME_LENGTH]

    # Create user templates directory
    user_dir = os.path.join(config.UPLOAD_FOLDER, f"user_{current_user.id}", "templates")
    os.makedirs(user_dir, exist_ok=True)

    # Save PDF file
    filename = secure_filename(file.filename)
    # Add timestamp to avoid conflicts
    timestamp = int(time.time())
    pdf_filename = f"{timestamp}_{filename}"
    pdf_path = os.path.join(user_dir, pdf_filename)
    file.save(pdf_path)

    try:
        # Extract text with positions using PDFTemplateExtractor
        extractor = PDFTemplateExtractor()
        extraction_result = extractor.extract_text_with_positions(pdf_path)

        text_blocks = extraction_result.get("text_blocks", [])

        # Concatenate text for template content
        plain_text = extractor.get_plain_text(pdf_path)

        # Create Template record
        template = Template(
            user_id=current_user.id,
            name=template_name,
            content=plain_text,
            is_pdf_template=True,
            pdf_path=pdf_path,
            is_default=False,
        )

        db.session.add(template)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "PDF-Template erfolgreich hochgeladen",
            "template": template.to_dict(),
            "text_blocks": text_blocks,
            "extraction_source": extraction_result.get("source", "unknown"),
            "total_blocks": extraction_result.get("total_blocks", 0),
        }), 201

    except Exception as e:
        # Cleanup on error
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        print(f"Fehler beim PDF-Template Upload: {str(e)}")
        return jsonify({"error": f"Fehler beim Verarbeiten der PDF: {str(e)}"}), 500


@templates_bp.route("/<int:template_id>/analyze-variables", methods=["POST"])
@jwt_required_custom
def analyze_template_variables(template_id, current_user):
    """Analyze template text with AI to identify variable candidates"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({"error": "Template nicht gefunden"}), 404

    if not template.is_pdf_template:
        return jsonify({"error": "Nur PDF-Templates können analysiert werden"}), 400

    # Get text blocks if PDF exists
    text_blocks = []
    if template.pdf_path and os.path.exists(template.pdf_path):
        try:
            extractor = PDFTemplateExtractor()
            extraction_result = extractor.extract_text_with_positions(template.pdf_path)
            text_blocks = extraction_result.get("text_blocks", [])
        except Exception as e:
            print(f"Warnung: Konnte Text-Blöcke nicht neu extrahieren: {str(e)}")

    # Use template content for analysis
    template_text = template.content
    if not template_text:
        return jsonify({"error": "Template enthält keinen Text"}), 400

    try:
        # Send to Claude API for variable analysis
        api_client = ClaudeAPIClient()

        prompt = f"""Analysiere diesen Bewerbungs-Template-Text und identifiziere Passagen, die als dynamische Variablen markiert werden sollten.

TEMPLATE TEXT:
{template_text[:5000]}

VERFÜGBARE VARIABLEN:
- FIRMA: Firmenname (z.B. "Musterfirma GmbH", "ABC AG")
- POSITION: Stellenbezeichnung (z.B. "Softwareentwickler", "Marketing Manager")
- ANSPRECHPARTNER: Komplette Anrede (z.B. "Sehr geehrte Frau Müller", "Sehr geehrter Herr Schmidt")
- QUELLE: Wo die Stelle gefunden wurde (z.B. "auf LinkedIn", "auf StepStone")
- EINLEITUNG: Ein personalisierbarer Einleitungsabsatz

AUFGABE:
Identifiziere konkrete Textpassagen, die bei jeder Bewerbung angepasst werden sollten.

AUSGABEFORMAT (NUR JSON, keine Erklärungen):
[
  {{"text": "exakter Text aus dem Template", "variable": "FIRMA", "confidence": 0.95, "reason": "Kurze Begründung"}},
  {{"text": "weiterer Text", "variable": "POSITION", "confidence": 0.85, "reason": "Begründung"}}
]

WICHTIG:
- Der "text" muss EXAKT im Template vorkommen
- "confidence" ist ein Wert zwischen 0.0 und 1.0
- Identifiziere mindestens FIRMA, POSITION und ANSPRECHPARTNER falls vorhanden
- Gib NUR das JSON-Array zurück, keine anderen Texte"""

        response = api_client.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text.strip()

        # Parse JSON response
        suggestions = []
        try:
            # Try to extract JSON from response
            if response_text.startswith("["):
                suggestions = json.loads(response_text)
            else:
                # Try to find JSON array in response
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    suggestions = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"Warnung: JSON-Parsing fehlgeschlagen: {str(e)}")
            print(f"Response: {response_text[:500]}")

        # Calculate line numbers for each page based on Y positions
        page_line_numbers: dict[int, list[float]] = {}
        for block in text_blocks:
            page_num = block.get("page", 0)
            if page_num not in page_line_numbers:
                page_line_numbers[page_num] = []
            y_pos = block.get("y", 0)
            # Group similar Y positions (within 5px tolerance)
            found_similar = False
            for existing_y in page_line_numbers[page_num]:
                if abs(existing_y - y_pos) < 5:
                    found_similar = True
                    break
            if not found_similar:
                page_line_numbers[page_num].append(y_pos)

        # Sort Y positions to get line numbers
        for page_num in page_line_numbers:
            page_line_numbers[page_num].sort()

        def get_line_number(page: int, y: float) -> int:
            """Get line number for a given Y position on a page."""
            if page not in page_line_numbers:
                return 1
            lines = page_line_numbers[page]
            for i, line_y in enumerate(lines):
                if abs(line_y - y) < 5:
                    return i + 1
            # If not found exactly, find closest
            for i, line_y in enumerate(lines):
                if y <= line_y + 5:
                    return i + 1
            return len(lines)

        # Enrich suggestions with position data from text_blocks
        enriched_suggestions = []
        for i, sug in enumerate(suggestions):
            suggestion_text = sug.get("text", "")
            variable = sug.get("variable", "")
            confidence = sug.get("confidence", 0.5)
            reason = sug.get("reason", "")

            # Find position in text blocks
            position_data = None
            for block in text_blocks:
                if suggestion_text in block.get("text", "") or block.get("text", "") in suggestion_text:
                    page_num = block.get("page", 0)
                    y_pos = block.get("y", 0)
                    line_num = get_line_number(page_num, y_pos)
                    position_data = {
                        "x": block.get("x"),
                        "y": block.get("y"),
                        "width": block.get("width"),
                        "height": block.get("height"),
                        "page": page_num + 1,  # Convert to 1-based indexing for display
                        "line": line_num,
                    }
                    break

            enriched_suggestions.append({
                "id": f"var_{i}_{hash(suggestion_text) % 10000}",
                "text": suggestion_text,
                "variable": variable,
                "confidence": confidence,
                "reason": reason,
                "position": position_data,
            })

        return jsonify({
            "success": True,
            "template_id": template.id,
            "suggestions": enriched_suggestions,
            "total_suggestions": len(enriched_suggestions),
        }), 200

    except Exception as e:
        print(f"Fehler bei der Variablen-Analyse: {str(e)}")
        return jsonify({"error": f"Fehler bei der Analyse: {str(e)}"}), 500


@templates_bp.route("/<int:template_id>/variable-positions", methods=["PUT"])
@jwt_required_custom
def save_variable_positions(template_id, current_user):
    """Save user-confirmed variable positions for a template and replace text with placeholders"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({"error": "Template nicht gefunden"}), 404

    data = request.json

    if not data:
        return jsonify({"error": "Keine Daten übermittelt"}), 400

    # Validate the variable positions format
    variable_positions = data.get("variable_positions")

    if variable_positions is None:
        return jsonify({"error": "variable_positions ist erforderlich"}), 400

    if not isinstance(variable_positions, (list, dict)):
        return jsonify({"error": "variable_positions muss ein Array oder Objekt sein"}), 400

    # Allowed variable names
    allowed_variables = {"FIRMA", "POSITION", "ANSPRECHPARTNER", "QUELLE", "EINLEITUNG"}

    # Validate structure if it's a list
    if isinstance(variable_positions, list):
        for item in variable_positions:
            if not isinstance(item, dict):
                return jsonify({"error": "Jeder Eintrag muss ein Objekt sein"}), 400

            variable = item.get("variable_name") or item.get("variable")
            if variable and variable not in allowed_variables:
                return jsonify({
                    "error": f"Unbekannte Variable: {variable}. Erlaubt: {', '.join(allowed_variables)}"
                }), 400

    # Validate structure if it's a dict (variable name -> positions)
    elif isinstance(variable_positions, dict):
        for key in variable_positions.keys():
            if key not in allowed_variables:
                return jsonify({
                    "error": f"Unbekannte Variable: {key}. Erlaubt: {', '.join(allowed_variables)}"
                }), 400

    try:
        # Update template content by replacing matched text with {{VARIABLE}} placeholders
        updated_content = template.content

        if isinstance(variable_positions, list):
            # Sort by text length descending to replace longer matches first
            # This prevents partial replacements (e.g., "XXX Hamburg" before "XXX")
            sorted_positions = sorted(
                variable_positions,
                key=lambda x: len(x.get("suggested_text", "") or x.get("text", "")),
                reverse=True
            )

            for item in sorted_positions:
                variable_name = item.get("variable_name") or item.get("variable")
                suggested_text = item.get("suggested_text") or item.get("text", "")

                if variable_name and suggested_text and suggested_text in updated_content:
                    placeholder = "{{" + variable_name + "}}"
                    updated_content = updated_content.replace(suggested_text, placeholder, 1)

        # Update template with variable positions and transformed content
        template.variable_positions = variable_positions
        template.content = updated_content
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Variablen-Positionen erfolgreich gespeichert",
            "template": template.to_dict(),
            "variables_replaced": len(variable_positions) if isinstance(variable_positions, list) else 0,
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Fehler beim Speichern der Variablen-Positionen: {str(e)}")
        return jsonify({"error": f"Fehler beim Speichern: {str(e)}"}), 500
