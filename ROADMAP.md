# obojobs - Vollständige Vision & Roadmap

## 📋 Projekt-Übersicht

**Ziel**: Multi-User Web-Anwendung zur automatisierten Bewerbungsgenerierung mit KI

**Kern-Idee**:
- User laden ihre Bewerbungsunterlagen (CV, Zeugnisse, Template) hoch
- Während dem Surfen auf Job-Websites können sie per Chrome Extension mit einem Klick eine personalisierte Bewerbung generieren lassen
- Claude AI analysiert die Stellenanzeige und erstellt ein maßgeschneidertes Anschreiben
- Fertige PDF-Bewerbung wird im Dashboard angezeigt und kann heruntergeladen werden

---

## ✅ Aktueller Stand (Minimal Version - Januar 2026)

### Was bereits funktioniert:

#### Backend (100% funktional)
- ✅ Flask API Server auf Port 5001
- ✅ SQLite Datenbank mit 6 Tabellen (users, documents, templates, applications, api_keys, purchases)
- ✅ JWT Authentication für Dashboard
- ✅ API Key Authentication für Chrome Extension
- ✅ User Management (Register, Login, Credits-System mit 5 Credits)
- ✅ Document Upload/Download (multipart/form-data)
- ✅ Template CRUD (Create, Read, Update, Delete)
- ✅ Application Management (Liste, Details, PDF Download)
- ✅ API Key Generation (einmalige Anzeige, gehashed storage)
- ✅ Stats Endpoint (Anzahl Bewerbungen, Credits)
- ✅ Per-User File Storage (uploads/user_<id>/)
- ✅ Credit-System (Dekrementierung bei Generierung)
- ✅ BewerbungsGenerator refactored für Multi-User
- ✅ Claude API Integration (3.5 Haiku)
- ✅ PDF Generation (ReportLab)
- ✅ Web Scraping (BeautifulSoup)
- ✅ PayPal Payment Integration (Sandbox & Production)
- ✅ Purchase Tracking & History
- ✅ Rate Limiting (Flask-Limiter)

#### Frontend (Vue 3 - Minimal aber funktional)
- ✅ Login/Register Pages
- ✅ Dashboard mit Stats-Anzeige
- ✅ Documents Page (Upload & Liste)
- ✅ Templates Page (CRUD & Default setzen)
- ✅ Applications Page (Liste)
- ✅ Settings Page (API Key Generation, Credits-Anzeige, Credits kaufen Button)
- ✅ Buy Credits Page (Pakete, Purchase History)
- ✅ Payment Success Page (PayPal Rückkehr-Handling)
- ✅ Vue Router mit Protected Routes
- ✅ Axios Client mit JWT Interceptors
- ✅ Auth Store (reactive state)
- ✅ Minimal CSS Styling

#### Chrome Extension (Aktualisiert)
- ✅ Settings Page für Server URL & API Key
- ✅ chrome.storage.sync für Konfiguration
- ✅ API Key Header in Requests
- ✅ Context Menu "Generate Application"
- ✅ Background Script mit API Calls
- ✅ Content Script für Text-Extraktion

#### Deployment
- ⚠️ Läuft nur lokal (keine Docker-Container)
- ⚠️ Development Server (nicht production-ready)

---

## 🎯 Vollständige Vision - Fehlende Features

### Phase 1: UI/UX Verbesserungen (Wichtig für Usability)

#### Frontend Polish
- [ ] **Besseres Design & Layout**
  - [ ] Modernes UI Framework (z.B. Tailwind CSS oder Vue Material)
  - [ ] Responsive Design (Mobile-friendly)
  - [ ] Dark Mode
  - [ ] Loading States & Spinners
  - [ ] Error Handling & User Feedback (Toast Notifications)
  - [ ] Form Validation (Client-side)

- [ ] **Dashboard Enhancements**
  - [ ] Charts/Graphs für Statistiken (z.B. Chart.js)
  - [ ] Timeline/Kalender-Ansicht für Bewerbungen
  - [ ] Quick Actions (Schnellzugriff auf häufige Aktionen)
  - [ ] Onboarding Tutorial für neue User

- [ ] **Document Management**
  - [ ] Drag & Drop Upload
  - [ ] File Preview (PDF Viewer im Browser)
  - [ ] Progress Bar beim Upload
  - [ ] Multiple File Upload
  - [ ] File Size & Type Validation

- [ ] **Template Editor**
  - [ ] Rich Text Editor (z.B. TipTap, Quill)
  - [ ] Live Preview beim Editieren
  - [ ] Platzhalter-Autocomplete ({{FIRMA}}, {{POSITION}}, etc.)
  - [ ] Template-Vorlagen (Vorgefertigte Templates zur Auswahl)
  - [ ] Versionierung (Template History)

- [ ] **Application Management**
  - [ ] Detailansicht mit allen Infos
  - [ ] PDF Viewer integriert
  - [ ] Inline-Editing (Status, Notizen ändern)
  - [ ] Filter & Suche (nach Firma, Status, Datum)
  - [ ] Sortierung (Datum, Firma, Status)
  - [ ] Pagination (bei vielen Bewerbungen)
  - [ ] Bulk Actions (Mehrere Bewerbungen löschen)
  - [ ] Export (CSV, Excel)

---

### Phase 2: Backend Funktionalität (Core Features)

- [ ] **CV PDF Upload & Text-Extraktion**
  - [ ] User kann CV als PDF hochladen
  - [ ] Backend extrahiert automatisch Text (PyPDF2)
  - [ ] Speichert als cv_summary.txt
  - [ ] User kann Summary manuell editieren

- [ ] **Vorgefertigtes Anschreiben Upload**
  - [ ] User lädt bestehendes Anschreiben (PDF/DOCX) hoch
  - [ ] Backend extrahiert Text
  - [ ] Erkennt automatisch Platzhalter-Kandidaten
  - [ ] Erstellt Default-Template daraus
  - [ ] User kann Template nachbearbeiten

- [ ] **Zeugnis-Management**
  - [ ] Upload mehrerer Zeugnisse
  - [ ] Automatische Text-Extraktion (falls PDF)
  - [ ] Summary-Generierung mit Claude AI
  - [ ] Auswahl: Welche Zeugnisse für welche Bewerbung?

- [x] **Verbesserte Bewerbungs-Generierung**
  - [x] Template-Auswahl bei Generierung (nicht nur Default)
  - [ ] Zeugnis-Auswahl bei Generierung
  - [ ] Anpassbare Generierungs-Parameter (Tonalität, Länge)
  - [x] Email-Text Generierung (nicht nur Anschreiben)
  - [x] Betreff-Generierung
  - [x] Automatische Link-Extraktion aus Job-Website

- [ ] **Status-Tracking & Workflow**
  - [ ] Status-Änderung: erstellt → versendet → antwort_erhalten → absage → zusage
  - [ ] Automatische Email-Versendung aus der App (optional)
  - [ ] Reminder-System (Follow-up nach X Tagen)
  - [ ] Notizen & Tags für Bewerbungen

- [ ] **Erweiterte API Features**
  - [x] Rate Limiting (Schutz vor Missbrauch)
  - [ ] API Key Rollen (Read-only, Full-access)
  - [ ] API Key Expiration (Auto-ablaufen nach X Tagen)
  - [ ] Webhook Support (Notifications bei Events)

---

### Phase 3: Extension Enhancements

- [ ] **Intelligentere Text-Extraktion**
  - [ ] Automatische Erkennung von Firmenname, Position, Ansprechpartner
  - [ ] Strukturierte Daten-Extraktion (JSON-LD, Schema.org)
  - [ ] Support für gängige Job-Portale (Indeed, LinkedIn, StepStone)
  - [ ] Fallback: Manuelle Input-Felder wenn Auto-Erkennung fehlschlägt

- [ ] **Extension UI Verbesserung**
  - [ ] Popup zeigt Credits & letzte Bewerbungen
  - [ ] Quick View: Generierte Bewerbung direkt in Extension
  - [ ] Settings: Template-Auswahl für schnelle Generierung
  - [ ] Keyboard Shortcuts

- [ ] **Offline Support**
  - [ ] Queue-System: Bewerbungen offline generieren → später syncen
  - [ ] Service Worker für Offline-Functionality

---

### Phase 4: Admin & Analytics

- [ ] **Admin Dashboard**
  - [ ] User-Verwaltung (Aktivieren/Deaktivieren)
  - [ ] Credit-Management (Credits hinzufügen/entfernen)
  - [ ] System-Statistiken (Total Users, Total Applications, API Usage)
  - [ ] Logs & Monitoring

- [ ] **User Analytics**
  - [ ] Erfolgsquote-Tracking (Absagen vs. Zusagen)
  - [ ] Zeittracking (Wie lange bis Antwort?)
  - [ ] Firmen-Statistiken (Welche Firmen antworten oft/selten?)
  - [ ] Template-Performance (Welches Template hat beste Quote?)

- [ ] **Reporting**
  - [ ] Monatliche Reports per Email
  - [ ] Export aller Daten (DSGVO-konform)
  - [ ] PDF-Report: "Meine Bewerbungsstatistik 2026"

---

### Phase 5: Deployment & Skalierung

- [ ] **Docker Containerization**
  - [ ] Dockerfile für Backend
  - [ ] Dockerfile für Frontend (nginx)
  - [ ] docker-compose.yml für Entwicklung
  - [ ] Production docker-compose mit Volumes

- [ ] **Production Server Setup**
  - [ ] Gunicorn statt Flask Dev Server
  - [ ] Nginx Reverse Proxy
  - [ ] SSL/TLS Zertifikate (Let's Encrypt)
  - [ ] Environment Variables Management
  - [ ] Logging & Error Tracking (Sentry)

- [ ] **Datenbank Migration**
  - [ ] SQLite → PostgreSQL für Production
  - [ ] Alembic Migrations
  - [ ] Backup-System (automatisch täglich)

- [ ] **CI/CD Pipeline**
  - [ ] GitHub Actions
  - [ ] Automated Tests
  - [ ] Automated Deployment
  - [ ] Version Tagging

- [ ] **Skalierung**
  - [ ] Redis für Caching
  - [ ] Celery für Background Tasks (PDF-Generierung async)
  - [ ] CDN für statische Files
  - [ ] Load Balancer bei hoher Last

---

### Phase 6: Premium Features (Monetarisierung)

- [x] **Credit-Pakete (Einmalzahlung)**
  - [x] Small Paket: 10 Credits für 1€
  - [x] Medium Paket: 50 Credits für 4€
  - [x] Large Paket: 100 Credits für 7€
  - [x] Neue User starten mit 5 Credits gratis

- [x] **Payment Integration**
  - [x] PayPal Integration (Sandbox & Production)
  - [x] Einmalzahlung (keine Subscriptions)
  - [x] Payment Order Creation & Execution
  - [x] Purchase History & Tracking

- [x] **Frontend Integration**
  - [x] Credits kaufen Page (/buy-credits)
  - [x] Payment Success Page (/payment/success)
  - [x] Settings mit "Credits kaufen" Button
  - [x] Purchase History Tabelle
  - [x] Total spent Anzeige

- [ ] **Zukünftige Premium Features**
  - [ ] Mehr Claude API Tokens (längere Anschreiben)
  - [ ] GPT-4 statt Claude Haiku (bessere Qualität)
  - [ ] Priority Support
  - [ ] Custom Branding (White-Label Extension)
  - [ ] Team Accounts (mehrere User, ein Subscription)

---

### Phase 7: Advanced Features (Optional)

- [ ] **Multi-Language Support**
  - [ ] Internationalisierung (i18n)
  - [ ] Übersetzungen (Deutsch, Englisch, Französisch, etc.)
  - [ ] Locale-spezifische Formate (Datum, Währung)

- [ ] **AI Improvements**
  - [ ] Fine-tuned Model für Bewerbungen
  - [ ] A/B Testing verschiedener Prompts
  - [ ] Feedback-Loop: User kann Generierung bewerten
  - [ ] Automatische Optimierung basierend auf Feedback

- [ ] **Integration mit Job-Portalen**
  - [ ] LinkedIn API: Jobs direkt importieren
  - [ ] Indeed API: Automatische Job-Suche
  - [ ] Xing API: Profil-Import

- [ ] **Mobile App**
  - [ ] React Native App (iOS & Android)
  - [ ] Push Notifications bei neuen Antworten
  - [ ] Mobile-optimiertes Dashboard

- [ ] **Collaboration Features**
  - [ ] Template-Sharing (Community Templates)
  - [ ] Bewertungs-System für Templates
  - [ ] Forum/Community für Tipps & Tricks

---

## 🚀 Priorisierte Next Steps (Nach Minimal Version)

### Kurzfristig (1-2 Wochen)
1. **Docker Setup** - Deployment ermöglichen
2. **UI Polish** - Tailwind CSS, Loading States, Error Handling
3. **PDF Text-Extraktion** - CV PDF Upload Support
4. **Template Editor** - Rich Text Editor

### Mittelfristig (1-2 Monate)
5. **Application Detail View** - Vollständige Bewerbungsansicht
6. **Extension Intelligence** - Auto-Erkennung von Firma/Position
7. **Status Workflow** - Tracking von versendet → Antwort
8. **Filter & Search** - Bewerbungen durchsuchen

### Langfristig (3-6 Monate)
9. **PostgreSQL Migration** - Production-ready DB
10. **Admin Dashboard** - User & System Management
11. **Analytics** - Erfolgsquote, Statistiken
12. ~~**Payment System**~~ - ✅ Bereits implementiert (PayPal)

---

## 📊 Feature-Komplexität Matrix

| Feature | Priorität | Komplexität | Geschätzter Aufwand |
|---------|-----------|-------------|---------------------|
| Docker Setup | Hoch | Niedrig | 1-2 Tage |
| Tailwind CSS Integration | Hoch | Niedrig | 1 Tag |
| PDF Text-Extraktion | Hoch | Mittel | 2-3 Tage |
| Rich Text Editor | Mittel | Mittel | 2-3 Tage |
| Application Detail View | Hoch | Niedrig | 1 Tag |
| Filter & Search | Mittel | Mittel | 3-4 Tage |
| PostgreSQL Migration | Mittel | Mittel | 2-3 Tage |
| Admin Dashboard | Niedrig | Hoch | 1-2 Wochen |
| ~~Payment Integration~~ | ✅ Fertig | ✅ Fertig | ✅ Implementiert |
| Mobile App | Niedrig | Sehr Hoch | 2-3 Monate |

---

## 🎨 Design-Philosophie

### Prinzipien:
1. **Simplicity First** - User soll in 3 Klicks eine Bewerbung generieren können
2. **Mobile-First** - Alles muss auf dem Smartphone nutzbar sein
3. **Performance** - Schnelle Response-Zeiten, keine unnötigen API-Calls
4. **Privacy** - User-Daten gehören dem User, keine Weitergabe an Dritte
5. **Transparency** - User sieht immer was die KI macht (Credits, API-Calls)

### UX Flow (Ideal):
```
1. Registrierung (30 Sekunden)
   ↓
2. CV Upload (1 Minute)
   ↓
3. Template erstellen/hochladen (2-3 Minuten)
   ↓
4. Extension installieren & konfigurieren (1 Minute)
   ↓
5. Auf Job-Website: Text markieren → Klick → Fertig! (10 Sekunden)
   ↓
6. PDF im Dashboard downloaden (5 Sekunden)
```

**Total: Erste Bewerbung in unter 10 Minuten!**

---

## 🔒 Sicherheits-Roadmap

### Jetzt (Minimal Version):
- ✅ Passwort-Hashing (bcrypt)
- ✅ JWT Signierung
- ✅ API Key Hashing
- ✅ User-Isolation (DB Queries)
- ✅ File-Access Control

### Bald:
- [x] Rate Limiting (Flask-Limiter)
- [ ] Input Validation (marshmallow schemas)
- [ ] SQL Injection Prevention (SQLAlchemy ORM nutzen wir schon)
- [ ] XSS Prevention (Frontend Sanitization)
- [ ] CSRF Tokens

### Später:
- [ ] 2FA (Two-Factor Authentication)
- [ ] Email Verification
- [ ] Password Reset Flow
- [ ] Account Deletion (DSGVO)
- [ ] Audit Logs (Wer hat wann was geändert?)
- [ ] Penetration Testing
- [ ] Security Headers (HSTS, CSP, etc.)

---

## 📈 Metriken für Erfolg

### User-Metriken:
- Registrierungen pro Woche
- Active Users (Daily/Weekly/Monthly)
- Durchschnittliche Credits pro User
- Retention Rate (Wie viele kommen wieder?)
- Conversion Rate (Free → Paid)

### System-Metriken:
- API Response Time (< 500ms für 95% der Requests)
- Uptime (> 99.9%)
- Error Rate (< 0.1%)
- Claude API Kosten pro Bewerbung
- Storage Usage (Dateigröße pro User)

### Business-Metriken:
- Monthly Recurring Revenue (MRR)
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)
- Churn Rate

---

## 🐛 Known Issues & Technical Debt

### Aktuell:
- ⚠️ Frontend hat minimales Styling (funktional, aber nicht schön)
- ⚠️ Keine Error Handling UI (Errors nur in Console)
- ⚠️ Keine Loading States (User weiß nicht ob etwas lädt)
- ⚠️ Extension zeigt keine Credits im Popup
- ⚠️ Keine PDF-Vorschau im Dashboard
- ⚠️ Favicon fehlt

### Technical Debt:
- ⚠️ Kein Testing (Unit Tests, Integration Tests)
- ⚠️ Keine API Dokumentation (Swagger/OpenAPI)
- ⚠️ Hardcoded Strings (sollten in Config/i18n)
- ⚠️ Keine Migration-Scripts (Alembic)
- ⚠️ Keine Logging-Strategie (nur prints)

---

## 💡 Ideen für die Zukunft

### Crazy Ideas (vielleicht irgendwann):
- **AI Interview-Vorbereitung**: KI simuliert Interview basierend auf Stellenanzeige
- **Salary Negotiation Coach**: KI hilft bei Gehaltsverhandlung
- **Auto-Apply**: KI bewirbt sich automatisch auf passende Jobs (mit User-Freigabe)
- **Career Path Analyzer**: KI analysiert CV und schlägt nächste Karriereschritte vor
- **Network Effect**: User können anonymisiert sehen "Andere die sich bei Google bewarben, bewarben sich auch bei..."
- **Gamification**: Achievements, Streaks ("10 Bewerbungen in 10 Tagen!")
- **AI Resume Optimizer**: KI verbessert CV basierend auf Job-Anforderungen

---

## 📝 Notizen für zukünftige Entwicklung

### Wichtig zu wissen:
- **Claude API Kosten**: ~$0.003 pro Bewerbung (Haiku), ~$0.05 mit Opus → Bei 1000 Usern mit je 10 Bewerbungen = $30-500/Monat
- **File Storage**: Durchschnittlich 5MB pro User (CV + Zeugnisse) → Bei 1000 Usern = 5GB
- **Database Size**: ~10KB pro Application → Bei 10.000 Applications = 100MB
- **Server**: Für 100-500 concurrent users: 2-4GB RAM, 2 CPU cores ausreichend

### Migration von alter CLI-Version:
- `bewerbungen.json` kann mit `migrations/migrate_json.py` importiert werden
- Alte Files in `dokumente/`, `anlagen/`, `output/` müssen manuell migriert werden
- User: migration@example.com (für alte Daten)

### Environment Variables (vollständig):
```bash
# Database
DATABASE_URL=sqlite:///mailer.db  # oder postgresql://...

# Security
SECRET_KEY=<random-secret-key-min-32-chars>
JWT_SECRET_KEY=<jwt-secret-key>

# AI
ANTHROPIC_API_KEY=<claude-api-key>

# File Upload
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=10485760  # 10MB

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Server
FLASK_ENV=production
DEBUG=False

# Credits
DEFAULT_CREDITS=5

# Payment (PayPal)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox  # oder 'live' für Production

# Email (für spätere Features)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## 🎯 Vision Statement

**"Wir machen Bewerbungen so einfach wie ein Tweet"**

Jeder sollte mit minimalem Aufwand professionelle, personalisierte Bewerbungen erstellen können. KI übernimmt das Schreiben, du übernimmst die Kontrolle. Keine Subscription-Fallen, keine versteckten Kosten, volle Transparenz.

---

**Letzte Aktualisierung**: 9. Januar 2026
**Aktueller Stand**: MVP + Payment System (PayPal) implementiert
**Nächster Meilenstein**: Docker Deployment + UI Polish
