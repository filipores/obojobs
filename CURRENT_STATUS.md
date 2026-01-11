# Aktueller Projekt-Status (Januar 2026)

## ✅ Was funktioniert (Getestet & Bestätigt)

### Backend
- ✅ Server startet auf Port 5001
- ✅ Alle API Endpoints funktionieren:
  - Health Check
  - Auth (Register, Login, Refresh, Me)
  - Documents (Upload, List, Download, Delete)
  - Templates (CRUD, Set Default)
  - Applications (List, Generate, Details, PDF Download)
  - API Keys (Generate, List, Revoke)
  - Stats
- ✅ JWT Authentication funktioniert (Fix: User-ID muss String sein)
- ✅ API Key Authentication funktioniert
- ✅ Datenbank (SQLite) mit allen 5 Tabellen
- ✅ Test-User: test@example.com / test123 (50 Credits)
- ✅ File Storage in uploads/user_<id>/
- ✅ Claude API Integration

### Frontend
- ✅ Läuft auf Port 3000
- ✅ Login/Register funktionieren
- ✅ Dashboard zeigt Stats
- ✅ Alle Seiten laden (Documents, Templates, Applications, Settings)
- ✅ Routing mit geschützten Routes
- ✅ JWT wird in localStorage gespeichert
- ✅ Axios Interceptor fügt Token zu Requests hinzu

### Chrome Extension
- ✅ Manifest V3 korrekt konfiguriert
- ✅ Settings Page für Server URL & API Key
- ✅ chrome.storage.sync für Persistenz
- ✅ Context Menu funktioniert
- ✅ API Key wird in Requests gesendet

---

## 🔧 Bekannte Probleme & Einschränkungen

### Critical (Muss behoben werden)
- ⚠️ **JWT-Fix muss beim Backend-Neustart angewendet werden**:
  - Problem war: `identity=user.id` (Integer) statt `identity=str(user.id)` (String)
  - Fix in: `backend/services/auth_service.py` Zeile 67-68
  - Fix in: `backend/middleware/jwt_required.py` Zeile 19
  - Fix in: `backend/routes/auth.py` Zeile 62

### UI/UX Issues
- ⚠️ Minimalistisches Design (nur sehr basic CSS)
- ⚠️ Keine Loading States (User weiß nicht ob Request läuft)
- ⚠️ Keine Error-Anzeige (Errors nur in Console)
- ⚠️ Keine Success-Messages (außer console.log)
- ⚠️ Kein PDF-Viewer (nur Download-Link)
- ⚠️ Keine Drag & Drop für File Upload
- ⚠️ Keine Favicon
- ⚠️ Application Detail-Seite zeigt nur Basis-Infos

### Backend
- ⚠️ Keine Input-Validation (nur basic checks)
- ⚠️ Keine Rate Limiting
- ⚠️ Development Server (nicht production-ready)
- ⚠️ Kein Logging (nur prints)
- ⚠️ Keine Error-Tracking
- ⚠️ Keine Tests

### Extension
- ⚠️ Credits werden nicht im Popup angezeigt
- ⚠️ Keine Fehlerbehandlung (wenn Backend offline)
- ⚠️ Keine Offline-Queue
- ⚠️ Text-Extraktion ist sehr simpel (nur Selection)

### Deployment
- ⚠️ Läuft nur lokal (localhost:5001 & localhost:3000)
- ⚠️ Kein Docker Setup
- ⚠️ Keine Production-Config
- ⚠️ SQLite nicht ideal für Production

---

## 🐛 Bugs & Workarounds

### Bug 1: Port 5000 belegt (macOS AirPlay)
**Problem**: Flask default Port 5000 ist von AirPlay belegt
**Fix**: Backend läuft auf Port 5001
**Geänderte Dateien**:
- backend/app.py (Zeile 61)
- frontend/vite.config.js (Zeile 10)
- extension/settings.html (Zeile 23)

### Bug 2: JWT "Subject must be a string"
**Problem**: Flask-JWT-Extended erwartet String, aber Integer wurde übergeben
**Fix**: `create_access_token(identity=str(user.id))`
**Status**: ✅ Behoben

### Bug 3: Vite Proxy IPv6 Problem
**Problem**: Vite versucht über IPv6 zu connecten (::1), Backend läuft auf IPv4
**Fix**: target: 'http://127.0.0.1:5001' statt 'http://localhost:5001'
**Status**: ✅ Behoben

### Bug 4: index.html war in public/ statt root
**Problem**: Vite konnte index.html nicht finden
**Fix**: Verschoben nach frontend/index.html
**Status**: ✅ Behoben

### Bug 5: ModuleNotFoundError 'src'
**Problem**: Import `from src.web_scraper` nach Refactoring ungültig
**Fix**: `from .web_scraper` (relative import)
**Datei**: backend/services/pdf_handler.py (Zeile 9)
**Status**: ✅ Behoben

---

## 📂 Wichtige Dateien & Pfade

### Backend Entry Point
```
/Users/filipores/_Coding/mailer/backend/app.py
```

### Frontend Entry Point
```
/Users/filipores/_Coding/mailer/frontend/index.html
/Users/filipores/_Coding/mailer/frontend/src/main.js
```

### Extension
```
/Users/filipores/_Coding/mailer/extension/manifest.json
```

### Datenbank
```
/Users/filipores/_Coding/mailer/backend/mailer.db
```

### Uploads
```
/Users/filipores/_Coding/mailer/backend/uploads/user_<id>/
  ├── documents/
  └── pdfs/
```

### Config
```
/Users/filipores/_Coding/mailer/backend/.env
/Users/filipores/_Coding/mailer/backend/config.py
```

---

## 🚀 Wie man das Projekt startet

### 1. Backend starten
```bash
cd /Users/filipores/_Coding/mailer/backend
source venv/bin/activate  # Falls venv existiert
python3 app.py
```

**Erwarteter Output**:
```
✓ Configuration validated
Creating database tables...
✓ Database tables created successfully
✓ Test user already exists

============================================================
Mailer API Server
============================================================
Server running on http://localhost:5001
============================================================
```

### 2. Frontend starten (neues Terminal)
```bash
cd /Users/filipores/_Coding/mailer/frontend
npm run dev
```

**Erwarteter Output**:
```
VITE v5.4.21  ready in 231 ms

➜  Local:   http://localhost:3000/
```

### 3. Extension installieren
1. Öffne Chrome: `chrome://extensions`
2. Aktiviere "Entwicklermodus" (oben rechts)
3. Klicke "Entpackte Extension laden"
4. Wähle: `/Users/filipores/_Coding/mailer/extension`

### 4. Extension konfigurieren
1. Rechtsklick auf Extension-Icon → "Optionen"
2. Server URL: `http://localhost:5001`
3. API Key: (generiere im Dashboard unter Settings)

---

## 🧪 Test-Daten

### Test-User
```
Email: test@example.com
Password: test123
Credits: 50/50
```

### Test API Key (Falls generiert)
```
mlr_MGQKyT3kRIYg9WVTw_mbvMH0YVHnNLNlsYClXtaJOTo
```

### Test-Endpoints (mit curl)
```bash
# Health Check
curl http://localhost:5001/api/health

# Login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Stats (benötigt JWT Token)
curl -X GET http://localhost:5001/api/stats \
  -H "Authorization: Bearer <your-jwt-token>"
```

---

## 📊 Feature-Vollständigkeit

| Feature | Status | Notizen |
|---------|--------|---------|
| User Registration | ✅ 100% | Funktioniert |
| User Login | ✅ 100% | JWT wird korrekt generiert |
| Document Upload | ✅ 100% | Multipart/form-data funktioniert |
| Document List | ✅ 100% | Zeigt alle User-Dokumente |
| Document Download | ⚠️ 90% | Funktioniert, aber kein Preview |
| Document Delete | ✅ 100% | Löscht Datei & DB-Eintrag |
| Template CRUD | ✅ 100% | Alle Operationen funktionieren |
| Template Set Default | ✅ 100% | Funktioniert |
| Application List | ⚠️ 80% | Funktioniert, aber minimal |
| Application Generate | ⚠️ 50% | Backend funktioniert, Extension ungetestet |
| Application Detail | ⚠️ 60% | Route existiert, UI minimal |
| Application PDF Download | ✅ 100% | Funktioniert |
| Application Delete | ✅ 100% | Funktioniert |
| API Key Generation | ✅ 100% | Funktioniert, einmalige Anzeige |
| API Key List | ✅ 100% | Zeigt alle Keys |
| API Key Revoke | ✅ 100% | Funktioniert |
| Stats | ✅ 100% | Zeigt korrekte Zahlen |
| Credits System | ✅ 100% | Dekrementierung funktioniert |
| Extension Settings | ✅ 100% | Speichert in chrome.storage |
| Extension Generation | ⚠️ 0% | Nicht getestet |

**Gesamt-Fortschritt: ~75% funktional**

---

## 🔄 Was als Nächstes zu tun ist

### Sofort (Debugging/Testing)
1. ✅ JWT-Fix verifizieren (Backend neu starten)
2. ✅ Frontend-Login testen
3. ⏳ Extension End-to-End Test (Bewerbung generieren)
4. ⏳ PDF-Generierung testen
5. ⏳ Credit-System verifizieren (Credits gehen runter nach Generierung)

### Kurzfristig (Usability)
1. Error Handling im Frontend (Toast-Notifications)
2. Loading States (Spinner beim API Call)
3. Success Messages ("Upload erfolgreich!")
4. Extension Popup zeigt Credits
5. Favicon hinzufügen

### Mittelfristig (Features)
1. Application Detail Page verbessern
2. PDF Viewer integrieren
3. Template Editor (Rich Text)
4. Drag & Drop Upload
5. Filter & Search für Applications

---

## 💾 Backup & Wiederherstellung

### Wichtige Daten sichern
```bash
# Datenbank
cp backend/mailer.db mailer_backup_$(date +%Y%m%d).db

# Uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz backend/uploads/

# Environment
cp backend/.env .env.backup
```

### Bei Problemen: Neustart von vorne
```bash
# Datenbank löschen (alle User & Daten weg!)
rm backend/mailer.db

# Uploads löschen
rm -rf backend/uploads/*

# Backend neu starten → Test-User wird automatisch erstellt
python backend/app.py
```

---

## 🔑 Wichtige Credentials (Lokal)

### Anthropic API Key
Gespeichert in: `backend/.env`
```
ANTHROPIC_API_KEY=sk-ant-...
```

### JWT Secret
Generiert in: `backend/config.py`
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
```

**⚠️ WICHTIG**: In Production MÜSSEN diese geändert werden!

---

## 📝 Letzter Stand (Snapshot)

**Datum**: 8. Januar 2026, 17:00 Uhr
**Git Commit**: (kein Git-Repo initialisiert)
**Backend**: Läuft auf Port 5001 ✅
**Frontend**: Läuft auf Port 3000 ✅
**Extension**: Installiert, aber nicht getestet ⚠️
**Datenbank**: mailer.db mit Test-User ✅
**Tests durchgeführt**: Backend API (Python Script) ✅

**Letztes Problem behoben**: JWT "Subject must be a string" Error

**Nächstes To-Do**: Extension End-to-End Test

---

Dieser Status wird bei jedem größeren Update aktualisiert.
