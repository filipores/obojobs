# obojobs - Multi-User Bewerbungsautomation

Vollständig refaktorierte Multi-User Web-App mit Vue.js Frontend, Flask Backend und Chrome Extension.

## Architektur

```
┌─────────────────┐
│ Vue.js Frontend │ (Port 3000)
│  - Dashboard    │
│  - Dokumente    │
│  - Templates    │
│  - Settings     │
└────────┬────────┘
         │ HTTP/JWT
┌────────▼────────┐
│ Flask Backend   │ (Port 5000)
│  - REST API     │
│  - SQLAlchemy   │
│  - JWT Auth     │
└────────┬────────┘
         │
┌────────▼────────┐      ┌──────────────────┐
│ SQLite Database │      │ Chrome Extension │
│  - users        │      │  - Context Menu  │
│  - documents    │◄─────┤  - API Key Auth  │
│  - templates    │      │  - Credits       │
│  - applications │      └──────────────────┘
└─────────────────┘
```

## Setup

### 1. Backend Setup

```bash
cd /Users/filipores/_Coding/mailer/backend

# Create .env file
cp ../.env.example ../.env
# Edit .env and add your ANTHROPIC_API_KEY

# Install dependencies
pip install -r requirements.txt

# Start server (creates database and test user automatically)
python app.py
```

**Test User:**
- Email: `test@example.com`
- Password: `test123`
- Credits: 50/50

Backend läuft auf: `http://localhost:5000`

### 2. Frontend Setup

```bash
cd /Users/filipores/_Coding/mailer/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend läuft auf: `http://localhost:3000`

### 3. Chrome Extension Setup

1. Chrome öffnen → `chrome://extensions/`
2. "Developer mode" aktivieren
3. "Load unpacked" → `/Users/filipores/_Coding/mailer/extension/`
4. Extension Icon klicken → "Settings" Button
5. Server URL eingeben: `http://localhost:5000`
6. API Key generieren (siehe unten)

---

## Workflow

### Erste Schritte im Dashboard

1. **Login**: `http://localhost:3000/login`
   - Email: `test@example.com`
   - Password: `test123`

2. **Dokumente hochladen** (`/documents`):
   - CV Summary (.txt) - **ERFORDERLICH**
   - Optional: CV PDF, Zeugnis, Zeugnis Summary

3. **Template erstellen** (`/templates`):
   - Name: z.B. "Standard Anschreiben"
   - Content mit Platzhaltern:
     ```
     {{FIRMA}}
     {{ANSPRECHPARTNER}}
     {{POSITION}}
     {{QUELLE}}

     {{EINLEITUNG}}

     [Rest deines Templates...]
     ```
   - "Als Default setzen" aktivieren

4. **API Key generieren** (`/settings`):
   - "Neuen API Key generieren" klicken
   - Key kopieren (wird nur einmal angezeigt!)
   - Im Chrome Extension Settings einfügen

### Bewerbung generieren (via Extension)

1. Gehe zu einer Stellenanzeigen-Website
2. Markiere den Job-Text (Ctrl+A oder manuell)
3. Rechtsklick → **"Generate Application"**
4. Firmenname bestätigen/korrigieren
5. "Generate" klicken
6. Warten (~10-30 Sekunden)
7. Notification: "Application Generated!"

→ PDF wird gespeichert in `uploads/user_<id>/pdfs/`
→ Bewerbung ist im Dashboard sichtbar
→ Credits werden decrementiert

---

## API Endpoints

### Authentication
```
POST /api/auth/register     - Register new user
POST /api/auth/login        - Login (returns JWT)
GET  /api/auth/me           - Current user info
```

### Documents
```
GET    /api/documents       - List documents
POST   /api/documents       - Upload (multipart/form-data)
DELETE /api/documents/:id   - Delete
```

### Templates
```
GET    /api/templates       - List templates
POST   /api/templates       - Create
PUT    /api/templates/:id   - Update
DELETE /api/templates/:id   - Delete
```

### Applications
```
GET    /api/applications           - List (paginated)
POST   /api/applications/generate  - Generate (API Key required)
GET    /api/applications/:id       - Get details
DELETE /api/applications/:id       - Delete
GET    /api/applications/:id/pdf   - Download PDF
```

### API Keys
```
GET    /api/keys            - List API keys
POST   /api/keys            - Generate (returns plaintext ONCE)
DELETE /api/keys/:id        - Revoke
```

### Stats
```
GET /api/stats              - User statistics
```

---

## Datenbank-Schema

**users**: id, email, password_hash, credits_remaining, credits_max
**documents**: id, user_id, doc_type, file_path, uploaded_at
**templates**: id, user_id, name, content, is_default
**applications**: id, user_id, firma, position, status, pdf_path, ...
**api_keys**: id, user_id, key_hash, key_prefix, is_active

---

## Migration von altem System

Falls du Daten aus `bewerbungen.json` migrieren willst:

```python
cd /Users/filipores/_Coding/mailer/backend
python -c "
from app import create_app
from migrations.migrate_json import migrate_bewerbungen_json

app = create_app()
migrate_bewerbungen_json(app, user_email='test@example.com', json_path='../bewerbungen.json')
"
```

---

## Troubleshooting

**Backend startet nicht:**
- Prüfe `.env` Datei (ANTHROPIC_API_KEY gesetzt?)
- `pip install -r backend/requirements.txt`

**Frontend startet nicht:**
- `cd frontend && npm install`

**Extension funktioniert nicht:**
- Settings konfiguriert? (Server URL + API Key)
- Backend läuft auf Port 5000?
- API Key gültig?

**"Credits exhausted":**
- In Settings sichtbar: Credits 0/50
- Admin kann credits_remaining in DB zurücksetzen:
  ```sql
  UPDATE users SET credits_remaining = 50 WHERE email = 'test@example.com';
  ```

**PDF wird nicht generiert:**
- CV Summary hochgeladen?
- Template erstellt?
- Logs im Backend Terminal prüfen

---

## Entwicklung

### Backend ändern
```bash
cd backend
# Edit files
python app.py  # Restarts automatically (debug=True)
```

### Frontend ändern
```bash
cd frontend
# Edit .vue files
# Vite hot-reloads automatically
```

### Extension ändern
```bash
cd extension
# Edit .js/.html files
# Chrome → Extensions → Reload icon
```

---

## Produktion

Für Production-Deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use Gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 backend.app:create_app()`
3. Build frontend: `cd frontend && npm run build`
4. Serve frontend build mit nginx
5. Use PostgreSQL statt SQLite
6. Set proper CORS_ORIGINS

---

## Credits

- Claude 3.5 Haiku für Text-Generierung
- Flask für Backend
- Vue 3 für Frontend
- SQLite für Database
- Chrome Extension Manifest V3

---

## Support

Bei Fragen siehe:
- Backend Logs: Terminal wo `python app.py` läuft
- Frontend Logs: Browser Console (F12)
- Extension Logs: `chrome://extensions/` → Details → Inspect views

**WICHTIG**: Extension benötigt Backend auf Port 5000. Frontend auf Port 3000 ist optional (nur für Management).
