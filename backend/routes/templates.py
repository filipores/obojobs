import os

from flask import Blueprint, request, jsonify

from middleware.jwt_required import jwt_required_custom
from middleware.api_key_required import api_key_required
from models import db, Template, Document
from services.api_client import ClaudeAPIClient
from services.pdf_handler import read_document

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('', methods=['GET'])
@jwt_required_custom
def list_templates(current_user):
    """List user's templates"""
    templates = Template.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'success': True,
        'templates': [t.to_dict() for t in templates]
    }), 200


@templates_bp.route('', methods=['POST'])
@jwt_required_custom
def create_template(current_user):
    """Create a template"""
    data = request.json

    name = data.get('name')
    content = data.get('content')

    if not name or not content:
        return jsonify({'error': 'Name and content are required'}), 400

    template = Template(
        user_id=current_user.id,
        name=name,
        content=content,
        is_default=data.get('is_default', False)
    )

    # If this is set as default, unset others
    if template.is_default:
        Template.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})

    db.session.add(template)
    db.session.commit()

    return jsonify({
        'success': True,
        'template': template.to_dict()
    }), 201


@templates_bp.route('/<int:template_id>', methods=['GET'])
@jwt_required_custom
def get_template(template_id, current_user):
    """Get a template"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    return jsonify({
        'success': True,
        'template': template.to_dict()
    }), 200


@templates_bp.route('/<int:template_id>', methods=['PUT'])
@jwt_required_custom
def update_template(template_id, current_user):
    """Update a template"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    data = request.json

    if 'name' in data:
        template.name = data['name']
    if 'content' in data:
        template.content = data['content']

    db.session.commit()

    return jsonify({
        'success': True,
        'template': template.to_dict()
    }), 200


@templates_bp.route('/<int:template_id>/default', methods=['PUT'])
@jwt_required_custom
def set_default_template(template_id, current_user):
    """Set template as default"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    # Unset all defaults
    Template.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})

    # Set this as default
    template.is_default = True
    db.session.commit()

    return jsonify({
        'success': True,
        'template': template.to_dict()
    }), 200


@templates_bp.route('/<int:template_id>', methods=['DELETE'])
@jwt_required_custom
def delete_template(template_id, current_user):
    """Delete a template"""
    template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    db.session.delete(template)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Template deleted'}), 200


@templates_bp.route('/generate', methods=['POST'])
@jwt_required_custom
def generate_template_with_ai(current_user):
    """Generate a template using AI based on CV and user inputs"""
    data = request.json

    # Validierung
    sektor = data.get('sektor', '').strip()
    projekte = data.get('projekte', '').strip()
    leidenschaften = data.get('leidenschaften', '').strip()
    hobbys = data.get('hobbys', '').strip()
    tonalitaet = data.get('tonalitaet', '').strip()

    if not sektor or not projekte or not leidenschaften or not tonalitaet:
        return jsonify({'error': 'Sektor, Projekte, Leidenschaften und Tonalität sind erforderlich'}), 400

    # Lebenslauf laden
    cv_doc = Document.query.filter_by(user_id=current_user.id, doc_type='lebenslauf').first()
    if not cv_doc or not os.path.exists(cv_doc.file_path):
        return jsonify({'error': 'Lebenslauf nicht gefunden. Bitte lade zuerst deinen Lebenslauf hoch.'}), 400

    try:
        cv_text = read_document(cv_doc.file_path)

        # Claude API Prompt erstellen
        api_client = ClaudeAPIClient()

        # Tonalität-Beschreibungen
        tone_descriptions = {
            'formal': 'sehr professionell, höflich und klassisch. Verwende Formulierungen wie "Sehr geehrte Damen und Herren" und "Mit freundlichen Grüßen".',
            'modern': 'professionell aber etwas lockerer. Verwende moderne Formulierungen, bleibe aber respektvoll.',
            'kreativ': 'persönlich und authentisch. Zeige Persönlichkeit, aber bleibe professionell.'
        }
        tone_desc = tone_descriptions.get(tonalitaet, tone_descriptions['modern'])

        prompt = f"""Erstelle ein Anschreiben-Template für Bewerbungen basierend auf den folgenden Informationen:

**Lebenslauf des Bewerbers:**
{cv_text}

**Zielsektor:** {sektor}

**Wichtige Projekte/Erfolge:**
{projekte}

**Was dem Bewerber wichtig ist:**
{leidenschaften}

**Hobbys/Interessen** (falls relevant):
{hobbys if hobbys else 'Keine angegeben'}

**Gewünschte Tonalität:**
Das Anschreiben soll {tone_desc}

**WICHTIG:**
1. Erstelle ein TEMPLATE, kein fertiges Anschreiben!
2. Verwende diese Platzhalter, die später ersetzt werden:
   - {{{{FIRMA}}}} für den Firmennamen
   - {{{{POSITION}}}} für die Stellenbezeichnung
   - {{{{ANSPRECHPARTNER}}}} für die Anrede (z.B. "Sehr geehrte/r Frau/Herr XY" oder "Hallo Team")

3. Das Template soll:
   - Eine passende Einleitung haben (ca. 2-3 Sätze)
   - Die Stärken und Erfahrungen des Bewerbers hervorheben
   - Zur Tonalität passen
   - Motivation zeigen
   - Mit einer passenden Schlussformel enden

4. Schreibe NUR das Template, keine Erklärungen davor oder danach.
5. Das Template sollte ca. 200-300 Wörter lang sein.

Generiere jetzt das Anschreiben-Template:"""

        # Claude API Call
        response = api_client.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1500,
            temperature=0.8,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        generated_content = response.content[0].text.strip()

        # Template speichern
        template_name = f"KI-generiert ({sektor})"

        # Unset andere defaults
        Template.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})

        template = Template(
            user_id=current_user.id,
            name=template_name,
            content=generated_content,
            is_default=True
        )

        db.session.add(template)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Template erfolgreich generiert!',
            'template': template.to_dict()
        }), 201

    except Exception as e:
        print(f"Fehler bei Template-Generierung: {str(e)}")
        return jsonify({'error': f'Fehler beim Generieren: {str(e)}'}), 500


@templates_bp.route('/list-simple', methods=['GET'])
@api_key_required  # Extension uses API key
def list_templates_simple(current_user):
    """List user's templates (simplified for extension)"""
    templates = Template.query.filter_by(user_id=current_user.id).order_by(
        Template.is_default.desc(), Template.created_at.desc()
    ).all()

    return jsonify({
        'success': True,
        'templates': [{
            'id': t.id,
            'name': t.name,
            'is_default': t.is_default
        } for t in templates]
    }), 200
