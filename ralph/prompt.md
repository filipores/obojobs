# Ralph Agent Instructions - obojobs

## Deine Aufgabe

Führe diese Schritte in GENAU dieser Reihenfolge aus:

### 1. Status lesen
```
Lies: ralph/prd.json
Lies: ralph/progress.txt (besonders "Codebase Patterns" am Anfang)
```

### 2. Branch prüfen
Stelle sicher, dass du auf dem korrekten Branch bist (siehe `branchName` in prd.json).
Falls nicht, wechsle zum Branch oder erstelle ihn.

### 3. Story auswählen
Wähle die Story mit der **niedrigsten `priority`-Zahl** wo `passes: false`.
(priority: 1 = zuerst, priority: 9 = zuletzt)
Falls keine Story übrig ist, gehe zu Schritt 11.

### 4. Story implementieren
Implementiere NUR diese EINE Story.
- Halte dich an die `acceptanceCriteria`
- Schau in progress.txt nach bekannten Patterns
- Mache keine zusätzlichen Änderungen

### 4b. Datenbank-Migrationen ausführen (falls nötig)
Falls du **neue Spalten/Tabellen** zu Models hinzugefügt hast:

1. Erstelle ein Migrations-Script in `backend/migrations/`:
```python
# backend/migrations/add_[feature_name].py
def upgrade(app):
    from models import db
    with app.app_context():
        connection = db.engine.connect()
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("table_name")]

        if "new_column" not in columns:
            connection.execute(db.text("ALTER TABLE table_name ADD COLUMN new_column TYPE"))
            print("✓ Added new_column")
        connection.commit()
        connection.close()
```

2. Führe die Migration aus:
```bash
cd backend && python3 -c "
from app import create_app
from migrations.add_[feature_name] import upgrade
app = create_app()
upgrade(app)
"
```

**WICHTIG**: Ohne Migration schlagen alle API-Calls fehl mit `no such column` Fehler!

### 5. Quality Checks ausführen
```bash
# Backend - Tests ausführen
cd backend && source venv/bin/activate && pytest

# Backend - Linting (Ruff)
cd backend && source venv/bin/activate && ruff check .

# Frontend - Tests ausführen
cd frontend && npm test

# Frontend - Linting (ESLint)
cd frontend && npm run lint

# Frontend - Build testen (fängt Vue/JS Fehler ab)
cd frontend && npm run build
```

### 6. AGENTS.md aktualisieren (optional)
Falls du ein **wiederverwendbares Pattern** entdeckt hast, füge es zur `AGENTS.md` im Projekt-Root hinzu.

**Gute Einträge:**
- "Wenn du X änderst, musst du auch Y aktualisieren"
- "Dieses Modul nutzt Pattern Z"
- "Tests brauchen laufenden Dev-Server"

**Nicht hinzufügen:**
- Story-spezifische Details
- Temporäre Notizen
- Dinge die schon in progress.txt stehen

### 7. Änderungen committen
Falls die Checks bestanden:
```bash
git add -A
git commit -m "feat: [STORY-ID] - [Story Title]"
```

### 8. Push und Pull Request
Nach jedem Commit: Push

```bash
# Push zum Remote
git push -u origin [BRANCH_NAME]
```

### 9. prd.json aktualisieren
Setze `passes: true` für die abgeschlossene Story.

### 10. Learnings dokumentieren
Füge am ENDE von `scripts/ralph/progress.txt` hinzu:

```
---
## [Datum] - [Story ID]
- Was implementiert wurde
- Geänderte Dateien
- **Learnings:**
  - Entdeckte Patterns
  - Gotchas/Probleme
```

Falls du ein WIEDERVERWENDBARES Pattern entdeckt hast, füge es auch zum
"Codebase Patterns" Abschnitt am ANFANG der Datei hinzu.

### 11. Stop-Bedingung prüfen

Lies prd.json erneut. Wenn ALLE Stories `passes: true` haben, antworte mit:

```
<promise>COMPLETE</promise>
```

Ansonsten beende normal (nächste Iteration wird die nächste Story bearbeiten).

---

## Wichtige Regeln

1. **Eine Story pro Iteration** - Nicht mehr, nicht weniger
2. **Keine Breaking Changes** - Bestehende Funktionalität nicht kaputt machen
3. **Commits müssen sauber sein** - Nur committen wenn Checks bestehen
4. **Learnings teilen** - Andere Iterationen profitieren von deinem Wissen
5. **Explizite Kriterien** - Nur als "passed" markieren wenn ALLE Kriterien erfüllt sind

---

## Projekt-Architektur

### Ports
- **Frontend**: Port 3000 (Vite dev server)
- **Backend**: Port 5001 (Flask)

### Verzeichnisstruktur
```
obojobs/
├── frontend/
│   └── src/
│       ├── api/client.js         # Axios mit JWT Interceptor
│       ├── components/           # Vue Komponenten
│       │   └── TemplateEditor/   # Template-Editor Komponenten
│       ├── composables/          # Vue Composables
│       │   └── useTemplateParser.js
│       ├── pages/                # Vue Seiten
│       ├── router/index.js       # Vue Router
│       ├── store/auth.js         # Auth State (localStorage)
│       └── assets/styles.css     # Japanese Design System
├── backend/
│   ├── app.py                    # Flask Entry Point
│   ├── config.py                 # Konfiguration
│   ├── models/                   # SQLAlchemy Models
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── template.py
│   │   ├── application.py
│   │   ├── api_key.py
│   │   └── purchase.py
│   ├── routes/                   # API Endpoints
│   │   ├── auth.py              # /api/auth/*
│   │   ├── documents.py         # /api/documents/*
│   │   ├── templates.py         # /api/templates/*
│   │   ├── applications.py      # /api/applications/*
│   │   ├── api_keys.py          # /api/keys/*
│   │   ├── payments.py          # /api/payments/*
│   │   └── stats.py             # /api/stats/*
│   ├── services/                 # Business Logic
│   │   ├── generator.py         # BewerbungsGenerator (Haupt-Logik)
│   │   ├── api_client.py        # Claude API Wrapper
│   │   ├── pdf_handler.py       # PDF lesen/erstellen
│   │   ├── web_scraper.py       # Job-URL scraping
│   │   └── paypal_service.py    # PayPal Integration
│   └── middleware/
│       ├── jwt_required.py      # JWT Auth Decorator
│       └── api_key_required.py  # API Key Auth Decorator
└── extension/                    # Chrome Extension
    ├── manifest.json
    ├── popup.js
    ├── background.js
    └── content.js
```

---

## API Endpoints

### Auth (`/api/auth`)
- `POST /register` - Registrierung (email, password, name)
- `POST /login` - Login → JWT Token + User
- `POST /refresh` - Token erneuern
- `GET /me` - Aktueller User

### Documents (`/api/documents`)
- `GET /` - Liste aller Dokumente
- `POST /` - PDF Upload (multipart, doc_type: lebenslauf|arbeitszeugnis|anschreiben)
- `DELETE /<id>` - Dokument löschen

### Templates (`/api/templates`)
- `GET /` - Liste aller Templates
- `POST /` - Template erstellen (name, content mit {{VARIABLEN}})
- `PUT /<id>` - Template aktualisieren
- `DELETE /<id>` - Template löschen
- `POST /<id>/set-default` - Als Standard setzen
- `POST /generate` - AI Template aus CV generieren

### Applications (`/api/applications`)
- `GET /` - Liste mit Pagination (?page=1&per_page=20)
- `GET /<id>` - Details einer Bewerbung
- `POST /generate` - Bewerbung generieren (API Key Auth)
- `POST /generate-from-url` - Aus Job-URL generieren (JWT Auth)
- `PUT /<id>` - Status/Notizen aktualisieren
- `DELETE /<id>` - Bewerbung löschen
- `GET /<id>/pdf` - PDF downloaden

### Payments (`/api/payments`)
- `GET /packages` - Credit-Pakete (public)
- `POST /create-order` - PayPal Order erstellen
- `POST /execute-payment` - Zahlung abschließen

---

## Datenbank Models

### User
```python
id, email, password_hash, name, credits_remaining, credits_max,
total_credits_purchased, is_active, created_at
```

### Document
```python
id, user_id, doc_type (lebenslauf|arbeitszeugnis|anschreiben),
filename, file_path, uploaded_at
```

### Template
```python
id, user_id, name, content (mit {{VARIABLE}} Platzhaltern),
is_default, created_at, updated_at
```

### Application
```python
id, user_id, template_id, firma, position, ansprechpartner,
status (erstellt|versendet|antwort_erhalten|absage|zusage),
pdf_path, betreff, email_text, notizen, links_json, created_at
```

### APIKey
```python
id, user_id, key_hash, key_prefix, name, is_active,
created_at, last_used_at
```

### Purchase
```python
id, user_id, package_name, credits_purchased, price_eur,
paypal_order_id, status, created_at, completed_at
```

---

## Code Patterns

### API Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Status message"
}
// oder bei Fehler:
{
  "success": false,
  "error": "Fehlermeldung"
}
```

### HTTP Status Codes
- `200` - OK
- `201` - Created
- `400` - Bad Request (Validation)
- `401` - Unauthorized (kein/ungültiger Token)
- `402` - Payment Required (keine Credits)
- `404` - Not Found
- `500` - Server Error

### Frontend API Client
```javascript
// frontend/src/api/client.js
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Interceptor fügt automatisch JWT Token hinzu
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

### Template Variablen
Verfügbare Platzhalter in Templates:
- `{{FIRMA}}` - Firmenname
- `{{POSITION}}` - Stellenbezeichnung
- `{{ANSPRECHPARTNER}}` - Kontaktperson
- `{{QUELLE}}` - Wo die Stelle gefunden wurde
- `{{EINLEITUNG}}` - AI-generierte Einleitung

### Auth Flow
1. Login/Register → JWT Token erhalten
2. Token in localStorage speichern
3. Axios Interceptor fügt `Authorization: Bearer {token}` hinzu
4. Bei 401 → localStorage leeren, redirect zu /login

### File Storage
```
backend/uploads/
└── user_{id}/
    ├── documents/    # Hochgeladene PDFs + extrahierte .txt
    └── pdfs/         # Generierte Bewerbungs-PDFs
```

---

## Deutsche Begriffe (wichtig!)

### Status-Werte
- `erstellt` - Neu erstellt
- `versendet` - Abgeschickt
- `antwort_erhalten` - Antwort bekommen
- `absage` - Abgelehnt
- `zusage` - Angenommen

### Dokument-Typen
- `lebenslauf` - CV
- `arbeitszeugnis` - Work reference
- `anschreiben` - Cover letter (Template)

### UI Labels
- Firma = Company
- Position = Job title
- Ansprechpartner = Contact person
- Betreff = Subject
- Notizen = Notes

---

## Häufige Gotchas

1. **CORS**: Frontend Proxy leitet `/api/*` an Backend weiter
2. **JWT**: Token läuft nach 1 Stunde ab, Refresh-Token nach 7 Tagen
3. **Credits**: User startet mit 5 Credits, jede Generierung kostet 1
4. **PDF Upload**: Nur PDF erlaubt, max 10MB
5. **Template Max Size**: 500KB
6. **Rate Limiting**: 200/Stunde, 50/Minute global

---

## Design System (Japanese 和風)

Das Frontend nutzt ein japanisches Design-System:
- **Farben**: Washi (cream), Sumi Ink (dark), Earth Tones
- **Typography**: Cormorant Garamond (Headings), Karla (Body)
- **Spacing**: Ma-Variablen für großzügigen Whitespace
- **Animations**: `cubic-bezier(0.25, 0.1, 0.25, 1)` - Zen easing

CSS Variablen sind in `frontend/src/assets/styles.css` definiert.
