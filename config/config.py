import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = 'claude-3-5-haiku-20241022'
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '300'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
USE_EXTRACTION = os.getenv('USE_EXTRACTION', 'true').lower() == 'true'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
# OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
OUTPUT_DIR = "/Users/filipores/Documents/Bewerbungsunterlagen/Anschreiben"
FIRMEN_DIR = os.path.join(DATA_DIR, 'firmen')

CV_PATH = os.path.join(DATA_DIR, 'cv_summary.txt')
CV_PDF_PATH = os.path.join(DATA_DIR, 'cv-ger.pdf')
ZEUGNIS_SUMMARY_PATH = os.path.join(DATA_DIR, 'zeugnis_summary.txt')
ANSCHREIBEN_TEMPLATE_PATH = os.path.join(DATA_DIR, 'anschreiben_template.txt')
ARBEITSZEUGNIS_PATH = os.path.join(DATA_DIR, 'Filip Zeugnis.pdf')
TRACKING_JSON_PATH = os.path.join(BASE_DIR, 'bewerbungen.json')

PLACEHOLDERS = {
    'FIRMA': '{{FIRMA}}',
    'ANSPRECHPARTNER': '{{ANSPRECHPARTNER}}',
    'POSITION': '{{POSITION}}',
    'QUELLE': '{{QUELLE}}',
    'EINLEITUNG': '{{EINLEITUNG}}'
}

def validate_config():
    if not ANTHROPIC_API_KEY:
        raise ValueError("Konfigurationsfehler:\n- ANTHROPIC_API_KEY fehlt in .env")
    return True
