#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.generator import BewerbungsGenerator
from config import config
import tempfile
import os
import traceback

app = Flask(__name__)
CORS(app)
generator = BewerbungsGenerator()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        company = data.get('company')
        text = data.get('text')
        url = data.get('url', '')

        if not company or not text:
            return jsonify({'success': False, 'error': 'Missing company or text'}), 400

        # Temp file für job text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            if url:
                f.write(f"URL: {url}\n\n")
            f.write(text)
            temp_path = f.name

        try:
            # Generate
            pdf_path = generator.generate_bewerbung(temp_path, company)
            latest = generator.tracker.get_latest_bewerbung()

            return jsonify({
                'success': True,
                'pdf_path': pdf_path,
                'company': company,
                'position': latest.get('position', '') if latest else '',
                'email': latest.get('email', '') if latest else '',
                'betreff': latest.get('betreff', '') if latest else '',
                'email_text': latest.get('email_text', '') if latest else '',
                'message': f'Bewerbung für {company} erstellt'
            })
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    try:
        return jsonify({
            'success': True,
            'stats': generator.tracker.get_statistik()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("obojobs API Server")
    print("="*60)

    config.validate_config()
    print("✓ Configuration valid")

    print("Loading standard documents...")
    generator.load_standard_documents()

    print("\n" + "="*60)
    print("Server running on http://localhost:8000")
    print("="*60)
    print("Endpoints:")
    print("  GET  /api/health   - Health check")
    print("  POST /api/generate - Generate application")
    print("  GET  /api/stats    - Statistics")
    print("="*60 + "\n")

    app.run(host='localhost', port=8000, debug=True)
