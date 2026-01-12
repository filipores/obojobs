# AGENTS.md - obojobs

Diese Datei enthält wichtige Informationen für AI-Agenten (Claude Code, Amp, etc.) die an diesem Projekt arbeiten.

## Projekt-Übersicht

obojobs ist eine **Bewerbungsautomations-Plattform** (deutsch):
- Generiert personalisierte Bewerbungen aus Templates + CV
- Nutzt Claude API für Textgenerierung
- PayPal für Credit-System

## Tech Stack

| Komponente | Technologie | Port |
|------------|-------------|------|
| Frontend | Vue.js 3 + Vite | 3000 |
| Backend | Python Flask | 5001 |
| Database | SQLite (dev) / PostgreSQL (prod) | - |
| AI | Claude 3.5 Haiku | - |

## Wichtige Konventionen

### API Responses
Alle API Endpoints nutzen dieses Format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional status"
}
// Fehler:
{
  "success": false,
  "error": "Fehlermeldung"
}
```

### Deutsche Begriffe
Das Projekt nutzt deutsche Begriffe in der Datenbank und UI:
- Status: `erstellt`, `versendet`, `antwort_erhalten`, `absage`, `zusage`
- Dokument-Typen: `lebenslauf`, `arbeitszeugnis`, `anschreiben`
- Felder: `firma`, `position`, `ansprechpartner`, `betreff`, `notizen`

### Template Variablen
Templates nutzen `{{VARIABLE}}` Syntax:
- `{{FIRMA}}` - Firmenname
- `{{POSITION}}` - Stellenbezeichnung
- `{{ANSPRECHPARTNER}}` - Kontaktperson
- `{{QUELLE}}` - Wo die Stelle gefunden wurde
- `{{EINLEITUNG}}` - AI-generierte Einleitung

## Architektur-Patterns

### Frontend → Backend Kommunikation
- Vite Proxy leitet `/api/*` an `http://127.0.0.1:5001` weiter
- Axios Client in `frontend/src/api/client.js`
- JWT Token automatisch via Interceptor hinzugefügt

### Authentication
- JWT für Web-App (1h access, 7d refresh)
- API Keys für Chrome Extension (`X-API-Key` Header)
- Middleware: `backend/middleware/jwt_required.py`, `api_key_required.py`

### File Storage
```
backend/uploads/
└── user_{id}/
    ├── documents/   # Hochgeladene PDFs + extrahierte .txt
    └── pdfs/        # Generierte Bewerbungs-PDFs
```

## Gotchas & Fallstricke

### Backend
- **SQLAlchemy**: Immer `db.session.commit()` nach Änderungen
- **PDF Upload**: Nur PDF erlaubt, max 10MB
- **Rate Limiting**: 200/hour, 50/minute global
- **Credits**: Jede Generierung kostet 1 Credit, neue User starten mit 5

### Frontend
- **Auth Errors**: 401/422 → automatischer Logout + Redirect zu /login
- **Template Max Size**: 500KB
- **Design System**: Japanese 和風 - siehe `frontend/src/assets/styles.css`

### Allgemein
- **Sprache**: UI und Datenbank sind deutsch
- **Ports**: Frontend 3000, Backend 5001 - nicht verwechseln!
- **CORS**: Wird durch Vite Proxy umgangen, kein CORS-Setup nötig in Dev

## Key Files

### Entry Points
- `backend/app.py` - Flask App
- `frontend/src/main.js` - Vue App
- `extension/manifest.json` - Chrome Extension

### Business Logic
- `backend/services/generator.py` - BewerbungsGenerator (Haupt-Logik)
- `backend/services/api_client.py` - Claude API Integration
- `frontend/src/composables/useTemplateParser.js` - Template Parsing

### Database
- Models in `backend/models/`
- User, Document, Template, Application, APIKey, Purchase

## Testing & Linting

### Backend (Python)
```bash
# Tests ausführen (pytest)
cd backend && source venv/bin/activate && pytest

# Linting prüfen (Ruff)
cd backend && source venv/bin/activate && ruff check .

# Code formatieren (Ruff)
cd backend && source venv/bin/activate && ruff format .

# Auto-fix Linting-Fehler
cd backend && source venv/bin/activate && ruff check --fix .
```

Konfiguration:
- pytest: `backend/pytest.ini`
- Ruff: `backend/ruff.toml`
- Tests: `backend/tests/`
- Fixtures: `backend/tests/conftest.py` (Test-Client, Test-DB, Test-User)

### Frontend (Vue.js)
```bash
# Tests ausführen (Vitest)
cd frontend && npm test

# Tests im Watch-Modus
cd frontend && npm run test:watch

# Linting prüfen (ESLint)
cd frontend && npm run lint

# Auto-fix Linting-Fehler
cd frontend && npm run lint:fix

# Build prüfen
cd frontend && npm run build
```

Konfiguration:
- Vitest: `frontend/vitest.config.js`
- ESLint: `frontend/eslint.config.js` (Flat Config)
- Tests: `frontend/src/__tests__/`

## Deployment

Docker Compose Setup vorhanden:
- Backend: Gunicorn + tesseract + poppler
- Frontend: Nginx serving Vite build

---

*Diese Datei wird von Ralph und anderen AI-Agenten automatisch gelesen und bei Bedarf aktualisiert.*
