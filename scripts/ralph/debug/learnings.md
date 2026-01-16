# RALF Debug Mode - Learnings

Diese Datei enthält Erkenntnisse aus Debug-Sessions. Jeder Eintrag dokumentiert ein Problem, seine Ursache und was man daraus lernen kann.

---

## [2026-01-16] - BUG-020: Navigation zeigt eingeloggten Zustand trotz ungültigem Token

**Problem:** Die Navigation zeigte vollen eingeloggten Zustand (Dashboard-Links, Abmelden-Button) obwohl der Token in localStorage ungültig/abgelaufen war.

**Root Cause:** Schwache Token-Validierung in `authStore.isAuthenticated()`:
```js
// Vorher - nur Existenz-Check
isAuthenticated() {
  return !!this.token
}
```

**Fix:** Verbesserte `isAuthenticated()` mit echter JWT-Validierung:
- Strukturelle JWT-Prüfung (3 Teile)
- Payload-Dekodierung mit `window.atob()`
- Expiration-Check basierend auf `exp` claim
- Automatische State-Bereinigung bei ungültigen Tokens
- Neue `clearAuthState()` Hilfsmethode

**Learning:**
1. **Frontend JWT Validation**: Client-seitige Token-Validierung ist kritisch für UX - nicht nur auf API-Responses verlassen
2. **JWT Structure**: `token.split('.')` + `atob()` ermöglicht einfache Browser-basierte Token-Inspektion
3. **Expiry Math**: `exp` claim ist in Sekunden, `Date.now()` in Millisekunden - `exp * 1000 < Date.now()`
4. **Error Handling**: Try-catch um Token-Parsing, da ungültige Tokens JSON.parse() zum Crash bringen
5. **State Consistency**: Bei Token-Invalidierung immer User + Token + localStorage bereinigen

**Code Quality:** Alle Tests bestehen, ESLint clean (nur existing warnings bleiben).

---

## [2026-01-16] - BUG-021: Backend gibt 422 statt 401 für ungültige Tokens

**Problem:** Flask-JWT-Extended gab 422 Unprocessable Entity zurück statt 401 Unauthorized für ungültige JWT-Tokens wie "invalid-token" oder malformierte Tokens.

**Root Cause:** Flask-JWT-Extended Library Problem:
- JWT-Parsing-Fehler werden VOR Custom Error Handlers abgefangen
- Die Library gibt direkte 422 Responses zurück für Token-Strukturfehler
- Standard-Error-Handler wie `@jwt.invalid_token_loader` greifen nur bei bereits geparsten Tokens
- Fehler wie "Not enough segments", "Invalid header string" werden nicht abgefangen

**Fix:** Middleware-Lösung mit `@app.after_request`:
```python
@app.after_request
def after_request(response):
    # Intercepte 422 JSON-Responses
    if response.status_code == 422 and 'application/json' in response.content_type:
        try:
            response_data = json.loads(response.data.decode('utf-8'))
            error_msg = response_data.get('msg', '')

            # JWT-Fehler-Patterns erkennen
            jwt_error_patterns = ['Not enough segments', 'Invalid header string', ...]
            for pattern in jwt_error_patterns:
                if pattern in error_msg:
                    # Neuen 401 Response erstellen
                    return Response(json.dumps({"error": "Ungültiger Token"}), status=401)
        except:
            pass
    return response
```

**Learning:**
1. **Flask-JWT-Extended Limitation**: Standard Error Handlers reichen nicht für Parsing-Fehler
2. **Middleware Pattern**: `@app.after_request` ist mächtiger als Error Handlers für Library-interne Fehler
3. **Response Interception**: JSON Response Data kann nach Library-Verarbeitung noch modifiziert werden
4. **Error Pattern Matching**: Liste häufiger JWT-Fehler hilft bei umfassendem Error Handling
5. **Status Code Consistency**: 401 für alle Authentication-Fehler verbessert API-Konsistenz

**Testing:** Validiert mit curl:
- `Authorization: Bearer invalid-token` → 401 ✅
- `Authorization: Bearer not.enough.segments` → 401 ✅
- Kein Authorization Header → 401 ✅ (bleibt unverändert)

**Code Quality:** 288 Tests bestehen, Ruff checks clean, Frontend Build erfolgreich.

---

## [2026-01-16] - BUG-026: Fehlende 'Konto löschen' Funktion (DSGVO-Compliance)

**Problem:** Die Settings-Seite hatte zwar bereits eine "Gefahrenzone" mit einem "Konto löschen" Button, aber die Implementierung war nur ein Platzhalter der User zum Support-Kontakt verwies.

**Root Cause:** DSGVO-Compliance Lücke:
- Frontend zeigte nur Toast mit "Bitte Support kontaktieren" statt echte Löschung
- Kein Backend-Endpoint `/auth/delete-account` vorhanden
- "Recht auf Löschung" nach DSGVO war nicht implementiert

**Fix:**
- Backend: Neuer `DELETE /auth/delete-account` Endpoint mit JWT-Schutz
- Löscht User und alle zugehörigen Daten via CASCADE (documents, applications, API keys, etc.)
- Spezielle Behandlung für TokenBlacklist wegen Foreign Key Constraints
- Frontend: Echte API-Integration mit Toast & Redirect nach erfolgreicher Löschung
- Umfassende Tests mit 8 verschiedenen Testfällen

**Learning:**
- **Foreign Key Constraints bei User Deletion**: TokenBlacklist hatte FK zu User ohne CASCADE. Solution: Zuerst alle TokenBlacklist Entries löschen, dann User löschen
- **GDPR Logging**: Account-Löschungen müssen für Compliance geloggt werden
- **User Model CASCADE**: Gut designte User-Relationships mit `cascade="all, delete-orphan"` machten Cleanup automatisch
- **Test Coverage**: Account-Deletion braucht viele Edge Cases (404, DB-Errors, Related Data, etc.)

**Code Quality:** Alle 288 Backend Tests + Frontend Tests bestehen, Linting clean.

---

## [2026-01-14] - BUG-001: Interview-Fragen werden auf InterviewPrep-Seite nicht angezeigt

**Problem:** Die InterviewPrep-Seite zeigte "Keine Interview-Fragen vorhanden", obwohl die API erfolgreich Fragen zurückgab (200 OK).

**Root Cause:** Datenpfad-Mismatch zwischen Frontend und Backend:
- Backend-API-Struktur: `{ success: true, data: { all_questions: [...], questions: {grouped} } }`
- Frontend las: `data.questions` (existiert nicht auf top-level - wurde mit leerem Array defaulted)
- Korrekt wäre: `data.data.all_questions` für das Array

**Fix:**
- `loadQuestions`: `data.questions || []` → `data.data?.all_questions || []`
- `regenerateQuestions`: `data.questions || []` → `data.data?.questions || []`

**Learning:**
1. Bei API-Responses immer die Backend-Struktur verifizieren (AGENTS.md beschreibt Standard-Format)
2. Optional Chaining (`?.`) nutzen um Crashes bei fehlenden Pfaden zu vermeiden
3. Unterschiedliche Endpoints können unterschiedliche Response-Strukturen haben (GET vs POST)

**Betroffene Dateien:** `frontend/src/pages/InterviewPrep.vue`

---

## [2026-01-14] - BUG-002: API-Fehler 415 beim Generieren von Interview-Fragen

**Problem:** Beim Klicken auf "Fragen generieren" erschien ein Alert mit HTTP 415 UNSUPPORTED MEDIA TYPE Fehler.

**Root Cause:** POST-Request ohne Body an Backend-Endpoint:
- Frontend: `api.post('/generate-questions')` ohne Body-Parameter
- Backend: `request.json or {}` - Flask erwartet Content-Type: application/json
- Axios setzt Content-Type Header nur, wenn ein Body übergeben wird
- Ohne Body → kein Content-Type Header → Flask gibt 415 zurück

**Fix:**
- `api.post(`/applications/${applicationId.value}/generate-questions`)`
- → `api.post(`/applications/${applicationId.value}/generate-questions`, {})`
- Leeres Objekt `{}` erzwingt Content-Type: application/json Header

**Learning:**
1. Bei POST-Requests immer einen Body mitschicken, auch wenn leer (`{}`)
2. Flask's `request.json` erfordert Content-Type: application/json Header
3. 415 UNSUPPORTED MEDIA TYPE = Content-Type Header fehlt oder ist falsch
4. Axios setzt Content-Type automatisch, aber nur bei vorhandenem Body

**Betroffene Dateien:** `frontend/src/pages/InterviewPrep.vue`

---

## [2026-01-16] - BUG-017: Interview-Fragen können nicht generiert werden - Stellenbeschreibung fehlt

**Problem:** Bei manuell eingegebenen Stellenbeschreibungen konnten keine Interview-Fragen generiert werden. Fehlermeldung: "Keine Stellenbeschreibung vorhanden".

**Root Cause:** Datenflussproblem in der manuellen Stelleneingabe:
- `NewApplication.vue`: Bei manueller Eingabe wurde `editableData.description` befüllt
- Frontend sendete an `/generate-from-text` nur `job_text`, `company`, `title` - NICHT die verarbeitete `description`
- Backend speicherte nur temp file mit ursprünglichem `job_text`, nicht die strukturierte Beschreibung
- `InterviewPrep.vue` suchte Stellenbeschreibung in `app.notizen`, fand aber nur "[Draft - Job-Fit Analyse]" Text

**Fix:**
1. **Frontend:** `NewApplication.vue` sendet zusätzlich `description: editableData.value.description`
2. **Backend:** `applications.py` nimmt `description` Parameter und speichert in `latest.notizen`

**Learning:**
1. **Datenfluss tracken:** Bei manuellen Eingaben mehrere Processing-Schritte verfolgen (Eingabe → Analyse → Speicherung → Abruf)
2. **Strukturierte vs. rohe Daten:** Unterscheidung zwischen ursprünglichem Text (`job_text`) und verarbeiteter Beschreibung (`description`)
3. **Datenvertrag:** Verschiedene Endpoints nutzen verschiedene Datenquellen (URL-based vs. manual-based)
4. **Cross-Feature Dependencies:** Interview-Prep hängt von korrekt gespeicherten Application-Daten ab

**Betroffene Dateien:**
- `frontend/src/pages/NewApplication.vue` (Zeile 942-946)
- `backend/routes/applications.py` (Zeile 409, 453-459)

---

## [2026-01-16] - BUG-016: Firmen-Recherche zeigt korrupte/unlesbare Zeichen

**Problem:** Bei der Firmen-Recherche wurden korrupte Zeichen angezeigt (`\x03�S\x11\x15�...`) in der "Über das Unternehmen" Sektion.

**Root Cause:** Encoding-Problem beim Web-Scraping in `CompanyResearcher` Service:
- Direktes Setzen von `response.encoding = response.apparent_encoding`
- `apparent_encoding` kann None sein oder falsch detektiert werden (z.B. 'ascii' bei deutschen Umlauten)
- BeautifulSoup bekommt dadurch falsches Encoding und produziert korrupte Zeichen

**Fix:**
- Defensive Encoding-Behandlung in `company_researcher.py`
- Prüfung: Ist `apparent_encoding` gültig und nicht 'ascii'/'none'?
- UTF-8 als sicherer Fallback wenn `apparent_encoding` problematisch ist
- Anwendung auf alle HTTP-Requests: Homepage, About-Page, Job-Posting

**Learning:**
1. `response.apparent_encoding` nie blind vertrauen - kann None oder 'ascii' zurückgeben
2. Bei deutschem Content immer UTF-8 als Fallback verwenden
3. Encoding-Probleme zeigen sich als `\x03` etc. - klarer Indikator für falsches Encoding
4. Alle HTTP-Request-Stellen im Service konsistent behandeln

**Betroffene Dateien:** `backend/services/company_researcher.py`

---

## [2026-01-14] - BUG-003: Modal-State wird nicht zurückgesetzt beim erneuten Öffnen

**Problem:** Wenn das Analyse-Modal geschlossen und erneut geöffnet wurde, blieben die vorherige URL-Eingabe und Fehlermeldung erhalten.

**Root Cause:** Die Buttons zum Öffnen des Modals setzten direkt `showAnalyzeModal = true`, ohne den State vorher zurückzusetzen. Die State-Reset-Logik war nur in der `closeAnalyzeModal` Funktion vorhanden.

**Fix:**
- Neue Funktion `openAnalyzeModal()` erstellt, die alle State-Variablen zurücksetzt (analyzeUrl, analyzeResult, analyzeError, showManualInput, manualJobText, manualCompany, manualTitle) bevor das Modal geöffnet wird
- Beide Buttons ("Job analysieren" und "Erste Stelle analysieren") verwenden jetzt `openAnalyzeModal()` statt direktes `showAnalyzeModal = true`

**Learning:**
1. Modal-State sollte immer beim Öffnen zurückgesetzt werden, nicht nur beim Schließen
2. Statt direktes State-Setzen (`showModal = true`) immer eine Funktion verwenden, die die nötige Initialisierung durchführt
3. Single Responsibility: Eine `openModal` Funktion für das Öffnen, eine `closeModal` Funktion für das Schließen
4. Bei mehreren Triggern für dasselbe Modal (z.B. Header-Button + Empty-State-Button) ist eine zentrale Open-Funktion besonders wichtig

**Betroffene Dateien:** `frontend/src/components/JobRecommendations.vue`

---

## [2026-01-14] - BUG-004: GapAnalysis-Komponente wird nicht angezeigt bei fehlenden JobRequirements

**Problem:** Die GapAnalysis-Sektion wurde komplett ausgeblendet, wenn keine JobRequirements analysiert waren, statt einen hilfreichen Hinweis anzuzeigen.

**Root Cause:** Die `v-if` Bedingung in `Applications.vue:293` pruefte:
```vue
v-if="jobFitData && (jobFitData.missing_skills?.length > 0 || jobFitData.partial_matches?.length > 0)"
```
Wenn keine Daten vorhanden waren oder der API-Call fehlschlug, wurde die gesamte Sektion ausgeblendet.

**Fix:**
- Sektion wird jetzt immer angezeigt mit drei States:
  1. **Loading State**: Spinner während jobFitLoading=true
  2. **GapAnalysis-Komponente**: Wenn jobFitData vorhanden (Komponente handhabt selbst "keine Luecken")
  3. **Empty State**: Informativer Hinweis wenn keine Analyse verfuegbar

**Learning:**
1. UI-Sektionen sollten nicht komplett verschwinden - immer einen informativen Zustand zeigen
2. "Leere Zustände" (Empty States) sind wichtig fuer UX - sie erklaeren warum etwas fehlt
3. Loading, Data und Empty State sind drei Standard-Zustände die jede async-Sektion braucht
4. Komponenten koennen oft bereits Empty/Success States handeln - die Eltern-Komponente muss nur die Komponente rendern

**Betroffene Dateien:** `frontend/src/pages/Applications.vue`

---

## [2026-01-14] - BUG-005: Mehrere identische Toast-Fehlermeldungen erscheinen gleichzeitig

**Problem:** Beim Öffnen einer Bewerbung ohne Bewerbungstext erschienen zwei identische Toast-Meldungen "Kein Bewerbungstext vorhanden" gleichzeitig.

**Root Cause:** Die Toast-Komponente hatte keine Deduplizierungs-Logik. Bei schnell aufeinanderfolgenden Aufrufen (z.B. durch API-Interceptor und lokale Fehlerbehandlung) wurden identische Meldungen mehrfach angezeigt.

**Fix:**
- Deduplizierungs-Logik im Toast-Service implementiert
- `recentMessages` Map speichert Timestamps der letzten Anzeige pro Nachricht
- Identische Nachrichten innerhalb von 500ms werden ignoriert
- Memory-Leak-Prävention durch periodische Bereinigung alter Einträge

**Learning:**
1. Globale Services wie Toast/Notification sollten Duplikate automatisch verhindern
2. Ein kurzes Zeitfenster (500ms) ist ausreichend, um Race-Conditions abzufangen
3. Bei Maps für Caching/Tracking immer an Memory-Leaks denken (periodische Bereinigung)
4. Die Deduplizierung sollte im Service selbst sein, nicht in jedem Aufrufer

**Betroffene Dateien:** `frontend/src/components/Toast.vue`

---

## [2026-01-15] - BUG-001: Details-Link führt zu nicht existierender Route - leere Seite

**Problem:** In der Timeline-Seite führte der "Details"-Button zu einer leeren Seite mit Vue Router Warnung: 'No match found for location with path /applications/:id'

**Root Cause:** Route-System-Inkonsistenz:
- `Timeline.vue:100` nutzte `router-link :to="/applications/${app.id}"`
- Diese Route `/applications/:id` existiert nicht im Router (`frontend/src/router/index.js`)
- Nur `/applications` (Übersicht) und speziell `/applications/:id/interview`, `/applications/:id/mock-interview` existieren
- `Applications.vue` nutzt Modal-basierte Detail-Ansicht statt Routing

**Fix:**
- Router-Link ersetzt durch Button mit `@click="openDetails(app)"`
- Modal-System von `Applications.vue` übernommen und angepasst für `Timeline.vue`
- Modal-Funktionen hinzugefügt: `openDetails`, `closeDetails`, `updateStatus`, `updateNotes`
- Vollständiges Detail-Modal mit Status-Änderung, Notizen, Status-Verlauf und Aktionen

**Learning:**
1. Bei Routing-Problemen immer Router-Konfiguration vs. tatsächliche Links prüfen
2. Konsistenz zwischen Seiten: Wenn eine Seite Modals nutzt, sollten ähnliche Features das gleiche System verwenden
3. Modal-basierte Detail-Ansicht ist oft flexibler als separate Routen für einfache Inhalte
4. Beim Kopieren von Modal-Systemen: State-Variablen, Funktionen UND CSS-Styles übernehmen
5. Timeline-typische Funktionen (Status-Historie) passen gut in Detail-Modals

**Betroffene Dateien:** `frontend/src/pages/Timeline.vue`, `frontend/src/router/index.js` (analysiert)

---

## [2026-01-15] - BUG-011: Login-Fehlermeldung wird nicht angezeigt bei falschen Credentials

**Problem:** Bei falschem Login (401) wurde keine Fehlermeldung angezeigt - der Benutzer sah nur das leere Formular, ohne Hinweis was schiefgelaufen ist.

**Root Cause:** Interceptor-Konkurrenz zwischen globalem Error-Handler und Login-Komponente:
- `frontend/src/api/client.js:26-33` - Globaler Response-Interceptor fängt ALLE 401-Fehler ab
- Bei 401 wird automatisch zur Login-Seite weitergeleitet mit Toast "Sitzung abgelaufen"
- Das passiert BEVOR die Login-Komponente (`Login.vue:191-192`) den Fehler verarbeiten kann
- `authStore.login` nutzte `api.post` statt `api.silent.post` → Interceptor fing Fehler ab

**Fix:**
- `authStore.login` geändert von `api.post` zu `api.silent.post` (Zeile 9 in `auth.js`)
- `api.silent.post` unterdrückt automatische Toast-Nachrichten durch `suppressToast: true`
- Erlaubt der Login-Komponente, 401-Fehler selbst zu behandeln und lokalisierte Fehlermeldung zu zeigen

**Learning:**
1. **Interceptor-Scope beachten**: Globale Interceptor sollten authentifizierte Bereiche schützen, aber Login/Register-Flows ausschließen
2. **Silent API für Auth verwenden**: Login, Register, Password-Reset sollten `api.silent` nutzen für eigene Fehlerbehandlung
3. **Fehler-Ownership**: Wer den Request macht, sollte auch die Fehlerbehandlung kontrollieren können
4. **Interceptor-Design**: Globale Interceptor für "Session expired" vs. lokale Handler für "Invalid credentials"
5. **Testing**: Bei Auth-Flows immer falsche Credentials testen um Fehlerbehandlung zu verifizieren

**Betroffene Dateien:** `frontend/src/store/auth.js` (Fix), `frontend/src/api/client.js` (Analyse)

---

## [2026-01-15] - BUG-002: Backend-Fehlermeldungen teilweise auf Englisch

**Problem:** Bug-Report beschrieb englische Fehlermeldung "User with this email already exists" bei Registrierung mit existierender E-Mail, erwartet wurde deutsche Meldung.

**Root Cause:** Bug war bereits in vorherigem Commit behoben:
- Git-Historie zeigt: `"User with this email already exists"` → `"Ein Benutzer mit dieser E-Mail existiert bereits"`
- `backend/services/auth_service.py:40` enthält bereits die deutsche Übersetzung
- Der Bug-Report in `bugs.json` war veraltet und reflektierte nicht den aktuellen Code-Stand

**Fix:**
- Keine Code-Änderung nötig - Bug bereits behoben
- `bugs.json` aktualisiert: `fixed: true` mit Vermerk "bereits in vorherigem Commit behoben"

**Learning:**
1. **Bug-Status-Verification**: Immer aktuellen Code überprüfen bevor Fix implementiert wird
2. **Git-Historie-Analyse**: `git log -p` kann zeigen wann/wie Bugs bereits behoben wurden
3. **State-Management in Bug-Tracking**: Bug-Listen können veralten wenn Fixes parallel durchgeführt werden
4. **Grep für String-Suche**: `grep` hilft englische vs. deutsche Strings in Codebase zu finden
5. **Test-Coverage**: Alle Tests (280 Backend, 63 Frontend) bestätigen dass bestehende Übersetzungen funktionieren

**Betroffene Dateien:** `backend/services/auth_service.py` (bereits gefixt), `scripts/ralph/debug/bugs.json` (Status aktualisiert)

---

## [2026-01-15] - BUG-003: Fehlermeldungen werden nicht lokalisiert (Englisch statt Deutsch)

**Problem:** Bei E-Mail-Verifizierung mit ungültigem Token wurde eine englische Fehlermeldung "Invalid verification token" angezeigt statt der erwarteten deutschen Meldung.

**Root Cause:** Frontend-Backend String-Mismatch in Fehlerbehandlung:
- **Backend** (`EmailVerificationService.py:80,86`): Sendet bereits deutsche Nachrichten:
  - "Ungültiger Bestätigungstoken"
  - "Bestätigungstoken ist abgelaufen"
  - "E-Mail ist bereits bestätigt"
- **Frontend** (`VerifyEmail.vue:175-184`): Erwartete veraltete englische Schlüssel:
  - `if (errorCode === 'Ungültiger Token')` statt `'Ungültiger Bestätigungstoken'`
  - `if (errorCode === 'Token abgelaufen')` statt `'Bestätigungstoken ist abgelaufen'`

**Fix:**
- Frontend-Fehlerbehandlung aktualisiert um die korrekten deutschen Backend-Strings zu matchen
- Mapping korrigiert: Backend-Message → erwartete Frontend-Condition

**Learning:**
1. **String-Kongruenz**: Frontend-Fehlerbehandlung muss exakte Backend-Messages verwenden
2. **Evolution-Drift**: Backend-Messages können sich ändern ohne dass Frontend entsprechend aktualisiert wird
3. **Konsistenz-Checks**: Bei Lokalisierung beide Seiten der API überprüfen (Request/Response)
4. **Error-Code-Standards**: Erwägen strukturierte Error-Codes statt Free-Text für robustere Handhabung
5. **Backend-Message-Traceability**: Backend-Service-Layer definiert die authoritative Message-Quelle

**Betroffene Dateien:** `frontend/src/pages/VerifyEmail.vue` (Fix), `backend/services/email_verification_service.py` (Analyse)

---

## [2026-01-15] - BUG-004: Englischer Toast bei ungültigem Reset-Token zusätzlich zur deutschen Fehlerkarte

**Problem:** Bei ungültigem Reset-Token erschienen beide eine deutsche Fehlerkarte UND ein englischer Toast gleichzeitig, was eine verwirrende doppelte Fehlermeldung verursachte.

**Root Cause:** API-Interceptor-Duplikation in Error-Handling:
- **Component-Level**: `ResetPassword.vue:312-321` behandelt Reset-Fehler mit eigenen deutschen Fehlerkarten für ungültige/abgelaufene Tokens
- **API-Interceptor**: `client.js:39-45` zeigt automatisch Toast für alle 400/422-Errors
- **Double-Display**: Beide Systeme führten zu redundanter Fehlermeldung mit unterschiedlichen Sprachen

**Fix:**
- Verwendung von `api.silent.post` statt `api.post` in `ResetPassword.vue:303`
- `api.silent` setzt `suppressToast: true` Config-Parameter
- Unterdrückt automatische Interceptor-Toasts und ermöglicht Component-eigene Fehlerbehandlung

**Learning:**
1. **Silent API für eigene Error-Handling**: Wenn Komponenten spezielle Fehlerbehandlung haben, `api.silent` verwenden
2. **Error-Ownership-Prinzip**: Eine Fehlerquelle → eine Fehlermeldung → ein zuständiges System
3. **API-Interceptor-Scope**: Globale Interceptor für Standard-Cases, Component-Override für Custom-UX
4. **Konsistente Error-UX**: Spezielle Flows (Auth, Password-Reset) brauchen oft eigene Error-Cards statt generische Toasts
5. **Duplikations-Vermeidung**: Bei mehrschichtiger Error-Architektur (Interceptor + Component) immer Suppression-Mechanismus vorsehen

**Betroffene Dateien:** `frontend/src/pages/ResetPassword.vue` (Fix), `frontend/src/api/client.js` (Analyse)

---

## [2026-01-15] - BUG-005: Englische technische Fehlermeldungen werden Endnutzern angezeigt

**Problem:** Bei OAuth-Verbindungsversuchen (Gmail/Outlook) in den Einstellungen erschienen technische englische Fehlermeldungen wie "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set" zusätzlich zu deutschen Meldungen.

**Root Cause:** Fehlende Übersetzungen für OAuth-Konfigurationsfehler:
- **Backend** (`gmail_service.py:32-34`, `outlook_service.py:27-30`): Wirft technische englische `ValueError` für fehlende Environment-Variablen
- **Frontend API-Interceptor** (`client.js:41-42`): Übersetzt Fehlermeldungen via `translateError()`
- **Translation-Gap**: `errorTranslations.js` hatte keine Mappings für OAuth-Konfigurationsfehler
- **Resultat**: Technische englische Meldungen erreichten Endnutzer unübersetzt

**Fix:**
Übersetzungen für OAuth-Konfigurationsfehler zu `errorTranslations.js` hinzugefügt:
- `"GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set"` → `"Gmail-Integration ist derzeit nicht konfiguriert."`
- `"MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET must be set"` → `"Outlook-Integration ist derzeit nicht konfiguriert."`
- `"GOOGLE_REDIRECT_URI must be set"` → `"Gmail-Integration ist derzeit nicht konfiguriert."`
- `"MICROSOFT_REDIRECT_URI must be set"` → `"Outlook-Integration ist derzeit nicht konfiguriert."`

**Learning:**
1. **Translation-Coverage**: Auch technische Backend-Exceptions brauchen benutzerfreundliche Übersetzungen
2. **Error-Translation-Pipeline**: Backend → API-Response → Frontend-Interceptor → Translation-Mapping → User-Toast
3. **Configuration-Errors**: Fehlende Umgebungsvariablen sollten benutzerfreundlich kommuniziert werden ("Service nicht konfiguriert" statt technische Details)
4. **Error-Message-Audit**: Bei neuen Backend-Services prüfen welche Error-Messages an Frontend gehen könnten
5. **Defensive-Translation**: `translateError()` fällt auf Original-Message zurück, daher werden ungemappte Nachrichten 1:1 weitergegeben

**Betroffene Dateien:** `frontend/src/utils/errorTranslations.js` (Fix), `backend/services/gmail_service.py` + `backend/services/outlook_service.py` (Analyse)

---

## [2026-01-15] - BUG-006: Coverage dependency not installed

**Problem:** Vitest Coverage-Tests konnten nicht ausgeführt werden mit Fehlermeldung "MISSING DEPENDENCY - Cannot find dependency '@vitest/coverage-v8'", obwohl diese im suggested Fix empfohlen wurde.

**Root Cause:** Bug war bereits behoben (Phantom-Bug):
- **package.json Analysis**: `@vitest/coverage-v8: ^1.6.1` war bereits in devDependencies installiert (Zeile 23)
- **node_modules Check**: Dependency physisch installiert im Dateisystem
- **Test Execution**: `npm run test:coverage` und `npx vitest run --coverage` funktionieren beide fehlerfrei
- **Coverage Report**: Generiert erfolgreich 63 passing tests mit vollständigem Coverage-Report

**Fix:**
- Kein Code-Fix nötig - Dependencies waren bereits installiert und funktionsfähig
- `bugs.json` aktualisiert: `fixed: true` mit Vermerk "Bug war bereits behoben - Dependencies waren installiert und Coverage-Tests funktionieren problemlos"

**Learning:**
1. **State-Verification**: Immer aktuellen Setup-Status prüfen bevor Fix-Implementierung
2. **Dependency-Troubleshooting**: Bei "Missing Dependency" Fehlern: 1) package.json prüfen 2) node_modules Existenz prüfen 3) tatsächliche Ausführung testen
3. **Bug-Report-Timing**: Bug-Reports können veralten wenn Dependencies durch andere Prozesse (npm install, package updates) bereits behoben wurden
4. **Testing-Pipeline**: `npm test`, `npm run test:coverage`, `npm run build`, `npm run lint` sind wichtige Verification-Steps
5. **Phantom-Bug-Detection**: Bei scheinbar einfachen Dependency-Issues immer den Ist-Status verifizieren bevor Änderungen vorgenommen werden

**Betroffene Dateien:** `frontend/package.json` (Analyse), `frontend/vitest.config.js` (Analyse), `scripts/ralph/debug/bugs.json` (Status aktualisiert)

---

## [2026-01-15] - BUG-007: Alte Fehlermeldung bleibt nach manuellem Fallback sichtbar

**Problem:** Wenn URL-Scraping fehlschlug und der User den manuellen Fallback nutzte, blieb die ursprüngliche Fehlermeldung (z.B. "403 Forbidden") im Preview-Bereich sichtbar, auch nachdem der manuelle Flow erfolgreich abgeschlossen war.

**Root Cause:** State-Reset-Inkonsistenz im `analyzeManualText()` Flow:
- **Error State Persistence**: `error.value` Variable wurde bei erfolgreichem manuellen Fallback nicht zurückgesetzt
- **Flow-Sequence**: URL-Scraping → Fehler (`error.value = "403 Forbidden"`) → Fallback → Success (`showManualFallback = false`, Toast angezeigt) → **aber** `error.value` bleibt bestehen
- **Template Rendering**: `v-if="error && previewData"` (Zeile 414-421) zeigt weiterhin alte Fehlermeldung an, da beide Conditions erfüllt sind

**Fix:**
- `error.value = ''` in `analyzeManualText()` bei erfolgreichem Abschluss hinzugefügt (nach Zeile 850)
- Kommentar `// Clear any previous error from URL loading` für Klarheit
- Erfolgreicher manueller Flow setzt jetzt sowohl `showManualFallback = false` als auch `error.value = ''`

**Learning:**
1. **State-Reset-Consistency**: Alle relevanten State-Variablen müssen bei Success-Flows zurückgesetzt werden, nicht nur UI-States
2. **Cross-Flow-State-Management**: Wenn verschiedene Flows (URL + Manual) denselben UI-Bereich beeinflussen, müssen alle State-Variablen koordiniert werden
3. **Template-Condition-Analysis**: `v-if` mit mehreren Bedingungen kann zu "stuck state" führen wenn nur eine Bedingung zurückgesetzt wird
4. **Error-State-Ownership**: Wer einen Error-State setzt, sollte auch für dessen Reset verantwortlich sein
5. **Success-Flow-Cleanup**: Success-Toast allein bedeutet nicht dass alle Error-States automatisch verschwinden

**Betroffene Dateien:** `frontend/src/pages/NewApplication.vue` (Zeile 851 hinzugefügt)

---

## [2026-01-15] - BUG-008: Inkonsistente Umlaute in Fehlermeldung (Anforderungsanalyse)

**Problem:** In der Fehlermeldung der Anforderungsanalyse wurden gemischte Schreibweisen von Umlauten verwendet - ASCII-Umlaute ("moeglich", "koennen") und echte deutsche Umlaute ("möglich") in derselben Sektion.

**Root Cause:** Inkonsistente String-Literale in der Requirements-Error-Box:
- **Überschrift**: `"Anforderungsanalyse nicht moeglich"` (Zeile 358) - ASCII-Umlaut-Schreibweise
- **Hint-Text**: `"Sie koennen trotzdem eine Bewerbung generieren, aber der Job-Fit Score ist nicht verfuegbar."` (Zeile 360) - ASCII-Umlaut-Schreibweise
- **Erwartung**: Konsistente deutsche Umlaute (ö, ü, ä) in der gesamten UI

**Fix:**
- `"moeglich"` → `"möglich"` in der Überschrift
- `"koennen"` → `"können"` im Hint-Text
- `"verfuegbar"` → `"verfügbar"` im Hint-Text
- Alle Strings in der Error-Box verwenden jetzt einheitlich echte deutsche Umlaute

**Learning:**
1. **String-Consistency**: Deutsche UI sollte durchgängig echte Umlaute (ö,ü,ä) verwenden, nicht ASCII-Ersatz (oe,ue,ae)
2. **Localization-Standards**: UTF-8 Encoding erlaubt native deutsche Zeichen - ASCII-Umlaute sind nur für Legacy-Systeme nötig
3. **Section-Coherence**: Alle Strings innerhalb einer UI-Sektion sollten den gleichen Schreibstil verwenden
4. **Code-Review-Focus**: Bei deutschen Texten auf einheitliche Umlaut-Schreibweise achten
5. **Template-Literal-Audit**: Hardcodierte deutsche Strings sollten regelmäßig auf Konsistenz geprüft werden

**Betroffene Dateien:** `frontend/src/pages/NewApplication.vue` (Zeilen 358, 360)

---

## [2026-01-15] - BUG-010: Keine Fehlermeldung bei Duplikat-Skill

**Problem:** Beim Hinzufügen eines bereits existierenden Skills wurde keine Fehlermeldung angezeigt - das Modal blieb stumm offen, obwohl der Server einen 409 CONFLICT Error zurückgab.

**Root Cause:** Fehlende Error-Handling-Logik für Duplikat-Validierung:
- **Backend**: Skills-API (`POST /users/me/skills`) gibt korrekt 409 CONFLICT zurück bei Duplikat-Skills
- **Frontend**: `SkillsOverview.vue:280-281` loggte Fehler nur in Console, zeigte keine User-Feedback
- **UX-Blackhole**: User bekam kein Feedback warum das Modal offen blieb und der Skill nicht hinzugefügt wurde
- **Error-Response**: `error.response?.status === 409` war verfügbar, aber nicht behandelt

**Fix:**
- Error-Handling in `saveSkill()` catch-Block erweitert (Zeilen 283-293)
- **409 CONFLICT**: Spezifische deutsche Fehlermeldung "Skill existiert bereits" via Toast
- **Andere Fehler**: Generische Fehlermeldung "Fehler beim Speichern des Skills" via Toast
- **Conditional Toast**: `if (window.$toast)` check für robuste Implementierung

**Learning:**
1. **Specific Error Codes**: HTTP Status Codes nutzen für spezifische User-Feedback (409 = Duplikat, 422 = Validation, etc.)
2. **Silent Failures vermeiden**: Jeder API-Error sollte User-sichtbares Feedback auslösen, nie nur Console-Logging
3. **Context-Aware Messages**: "Skill existiert bereits" ist klarer als generisches "Fehler beim Speichern"
4. **Modal-Error-UX**: Bei Modals sollten Fehler das Modal offen lassen mit Fehlermeldung, nicht automatisch schließen
5. **Toast-Availability**: `window.$toast` check für Fälle wo Toast-System noch nicht geladen ist

**Betroffene Dateien:** `frontend/src/components/SkillsOverview.vue` (Zeilen 283-293)

---

## [2026-01-15] - BUG-009: Keine Client-seitige URL-Validierung vor Submit

**Problem:** Ungültige URLs ohne http/https Prefix konnten abgeschickt werden - der Button "Stellenanzeige laden" war aktiv und klickbar, auch bei offensichtlich ungültigen URLs. Fehler wurde erst nach Server-Request angezeigt (400 Bad Request).

**Root Cause:** Unvollständige Button-Disable-Logic:
- **URL-Validation**: `urlValidation.computed()` prüfte korrekt auf gültiges Format (http/https-Prefix, valide Domain)
- **Button-Logic**: `frontend/src/pages/NewApplication.vue:61` - Button disabled nur bei `urlValidation.isValid === false`
- **Logic-Gap**: Button war AKTIV bei `urlValidation.isValid === null` (leere URL oder noch keine Validation)
- **Resultat**: Ungültige URLs ohne Prefix führten zu unnötigen Server-Requests und schlechter UX

**Fix:**
- Button-Disable-Condition geändert von `:disabled="!url || loading || urlValidation.isValid === false"`
- zu `:disabled="!url || loading || urlValidation.isValid !== true"`
- Button ist jetzt nur aktiv wenn URL-Validierung EXPLIZIT erfolgreich ist (`isValid === true`)

**Learning:**
1. **Explicit Success Validation**: Bei tri-state Logic (true/false/null) nur auf explicit `=== true` prüfen, nicht nur `!== false`
2. **User-Feedback-Flow**: Ungültige URLs sollten sofort visuell blockiert werden, nicht erst nach Server-Request
3. **Validation-State-Machine**: `null` (unvalidiert), `false` (ungültig), `true` (gültig) - UI sollte nur bei `true` aktiviert sein
4. **URL-Pattern-Validation**: Basic patterns (http/https-Prefix, Domain mit Punkt) verhindern die meisten User-Errors vor API-Call
5. **Progressive Enhancement**: URL-Input mit real-time validation + Button-state = bessere UX als Server-only validation

**Betroffene Dateien:** `frontend/src/pages/NewApplication.vue` (Zeile 61)

---

## [2026-01-16] - BUG-019: 401-Handler erkennt viele JWT-Fehlermeldungen nicht

**Problem:** JWT-Fehler wurden nicht korrekt als Authentication-Fehler erkannt. User wurde nicht ausgeloggt und zu Login weitergeleitet, sondern blieb "eingeloggt" mit "Ungültige Eingabe" Toast-Meldungen.

**Root Cause:** Doppeltes Problem in JWT-Error-Recognition:
1. **Backend**: Flask-JWT-Extended gibt standardmäßig 422 (Unprocessable Entity) für JWT-Fehler zurück, nicht 401 (Unauthorized)
2. **Frontend**: Error-Detection in `api/client.js:32` prüfte nur `error.response?.data?.msg?.includes('token')`
   - Viele JWT-Fehler enthalten nicht das Wort "token": "Not enough segments", "Signature verification failed", "Invalid header", etc.
   - Diese Fehler wurden als normale Validation-Errors (422) behandelt statt als Auth-Errors

**Fix:**
1. **Backend** (`app.py`): Custom JWT Error-Handler hinzugefügt:
   - `@jwt.invalid_token_loader` → 401 mit "Ungültiger Token"
   - `@jwt.expired_token_loader` → 401 mit "Token ist abgelaufen"
   - `@jwt.unauthorized_loader` → 401 mit "Token fehlt"
   - Alle JWT-Fehler geben jetzt konsistent 401 zurück

2. **Frontend** (`client.js`): Erweiterte JWT-Error-Detection:
   - `isJWTErrorMessage()` Helper-Function mit Pattern-Matching
   - Erkennt alle gängigen JWT-Fehler: "token", "Not enough segments", "Signature verification failed", "jwt", "Bearer", etc.
   - Bessere Boolean-Logic: `isJWTError = status === 401 || (status === 422 && isJWTErrorMessage(msg))`

**Learning:**
1. **JWT-Error-Standards**: Flask-JWT-Extended gibt defaultmäßig 422 zurück - Custom Error-Handler nötig für konsistente 401-Response
2. **Pattern-Based Error-Detection**: Nicht nur auf spezifische Keywords verlassen, sondern Pattern-Arrays für robuste Error-Recognition
3. **Error-Classification**: JWT-Errors haben viele Formen ("segments", "signature", "header") - alle müssen als Auth-Fehler behandelt werden
4. **Auth-Error-UX**: Konsistenter Flow: JWT-Error → Logout → Redirect zu Login → Toast "Sitzung abgelaufen"
5. **Backend-Frontend-Consistency**: Error-Handler auf Backend-Seite sollten HTTP-Status-Standards befolgen für erwartbare Frontend-Behandlung
6. **Comprehensive Error-Patterns**: Error-Detection sollte aktuell UND zukünftig mögliche Error-Messages abdecken

**Betroffene Dateien:**
- `backend/app.py` (JWT Error-Handler hinzugefügt)
- `frontend/src/api/client.js` (isJWTErrorMessage() Helper + erweiterte Detection)

---

## [2026-01-16] - BUG-012: Kein Hamburger-Menü auf Mobile - Navigation nicht zugänglich

**Problem:** Auf Mobile (375x667 Viewport) waren wichtige Navigation-Links nicht zugänglich. Nur "Insights" (Icon) und "Neu" (Button) waren sichtbar, während Dashboard, Dokumente, Templates, Bewerbungen, Timeline, ATS komplett versteckt waren.

**Root Cause:** Incomplete Mobile Navigation-Design:
- **CSS Media Query**: `@media (max-width: 768px)` versteckte nur `.nav-text` (display: none)
- **Missing Hamburger Menu**: Kein Button vorhanden um versteckte Links zugänglich zu machen
- **Partial Implementation**: Nur Company Insights hatte `.nav-icon-mobile` Icon als Fallback
- **Bottom Navigation Gap**: Bottom-Nav hatte nur 5 von 9 Links (fehlten Dokumente, Templates, Insights)
- **UX-Blackhole**: Benutzer konnten zentrale Features nicht erreichen ohne Desktop-Ansicht

**Fix:**
✅ **Hamburger-Menu Button** hinzugefügt (nur Mobile ≤768px sichtbar)
✅ **Mobile Sidebar** mit slide-in Animation implementiert
✅ **Vollständige Navigation** - alle 9 Hauptbereiche zugänglich:
   - Dashboard, Dokumente, Templates, Bewerbungen
   - Timeline, ATS, Company-Insights
   - Abo-Einstellungen, Account-Einstellungen, Abmelden
✅ **Accessibility Features**:
   - Escape-Taste schließt Sidebar
   - Router-Wechsel schließt Sidebar automatisch
   - Body-Scroll deaktiviert bei offener Sidebar
   - Aria-labels für Screen-Reader
✅ **Japanese Design System Integration**:
   - Zen-styled Sidebar mit Enso-Branding
   - Washi-Paper Farbschema
   - Smooth Transitions mit natürlicher Easing
   - Backdrop-Blur-Overlay

**Learning:**
1. **Mobile-First Navigation**: Responsive Design muss sicherstellen dass ALLE Funktionen auf Mobile erreichbar sind, nicht nur Desktop-Features verstecken
2. **Progressive Disclosure**: Hamburger-Menu ist Standard-Pattern für Mobile Navigation wenn Top-Level-Links zu viele sind
3. **Accessibility-Complete**: Keyboard-Navigation (Escape), automatisches Schließen und Aria-Labels sind essentiell
4. **State-Management**: Sidebar-State benötigt Body-Scroll-Management und Route-Change-Listeners für gute UX
5. **Design-System-Consistency**: Mobile-Komponenten sollten das gleiche Design-Language wie Desktop verwenden
6. **Testing-Viewports**: Mobile-Tests bei verschiedenen Breakpoints (375px, 480px, 768px) zeigen Layout-Probleme auf

**Betroffene Dateien:** `frontend/src/App.vue` (383 neue Zeilen: Hamburger-Button, Sidebar-Component, Mobile-CSS)

---

## [2026-01-16] - BUG-013: Einstellungen und Abmelden auf Mobile nicht zugänglich

**Problem:** Auf sehr kleinen Mobile-Viewports (375x667) waren Settings-Icon und Logout-Button in der Top-Navigation nicht erreichbar oder zu klein/überlappend dargestellt.

**Root Cause:** Unoptimiertes Responsive Layout bei extremen Mobile-Sizes:
- **Layout-Overflow**: Bei 375px Viewport-Breite hatten alle Navigation-Elemente (Brand, Hamburger, Subscription-Display, Theme-Toggle, Settings, Logout) zu wenig Platz
- **CSS Media Queries**: Nur bis max-width: 480px definiert, aber keine spezifische Behandlung für ≤375px
- **Nav-Actions-Spacing**: Bei kleinen Screens waren Gaps zu groß und Icons möglicherweise überlappend
- **Alternative Access**: Mobile Sidebar hatte bereits Settings/Logout, aber diese waren evtl. nicht für User sichtbar bei Navigation-Overflow

**Fix:**
1. **Responsive Optimization**: Neue Media Query für ≤375px hinzugefügt
2. **Tighter Spacing**: Nav-actions gap von space-sm auf 2px reduziert bei sehr kleinen Screens
3. **Icon-Size Reduction**: Nav-icons von 36px auf 32px verkleinert bei ≤375px
4. **Subscription-Display Optimization**: min-width: 0 und kleinere Schrift für besseres Flex-Verhalten
5. **Layout-Protection**: flex-shrink: 0 und min-width: fit-content für nav-actions um Overflow zu verhindern

**Learning:**
1. **Extreme Mobile Testing**: Standard Mobile (480px) ist nicht genug - auch 375px und 320px testen für moderne Smartphones
2. **Nav-Element-Priority**: Bei Platz-Konflikt haben Settings/Logout höhere Priorität als große Subscription-Display
3. **Flex-Layout-Robustness**: min-width: 0 und flex-shrink Controls verhindern unerwartetes Layout-Verhalten bei kleinen Screens
4. **Alternative-Access-Paths**: Mobile Sidebar als Backup-Navigation ist wichtig wenn Top-Nav überfüllt wird
5. **Progressive Space-Reduction**: Bei verschiedenen Breakpoints schrittweise Gap/Padding/Icon-Sizes reduzieren statt alles auf einmal zu verstecken
6. **Layout-Testing**: Visual Testing bei verschiedenen Viewport-Größen deckt solche Probleme vor Production auf

**Betroffene Dateien:** `frontend/src/App.vue` (Responsive CSS für ≤375px hinzugefügt, nav-actions Layout-Protection)

---

## [2026-01-16] - BUG-014: Enter-Taste sendet Formular auf /new-application nicht ab

**Problem:** Die Enter-Taste im URL-Eingabefeld auf der /new-application Seite löste nicht das Laden der Stellenanzeige aus. User mussten manuell auf den "Stellenanzeige laden" Button klicken.

**Root Cause:** Fehlende Keyboard-Event-Behandlung im URL-Input:
- **URL-Input-Field**: Hatte kein `@keydown.enter` Event-Handler (Zeile 21-32)
- **Form-Structure**: Kein `<form>` Element um Standard-Submit-Verhalten zu ermöglichen
- **Button-Only-Activation**: "Stellenanzeige laden" wurde nur durch Click ausgelöst, nicht durch Enter
- **A11Y-Gap**: Keine Tastatur-Zugänglichkeit für häufig verwendete Primär-Action

**Fix:**
1. **Event-Handler hinzugefügt**: `@keydown.enter="onUrlEnterPressed"` zum URL-Input
2. **Validation-Logic**: `onUrlEnterPressed()` prüft URL-Validierung, Loading-State und Preview-Status
3. **Progressive Enhancement**: Enter-Taste aktiviert nur bei gültiger URL (`urlValidation.isValid === true`)
4. **Prevent-Default**: `event.preventDefault()` verhindert unerwünschtes Form-Submit-Verhalten

**Learning:**
1. **Keyboard-A11Y**: Primäre Actions sollten sowohl mit Maus als auch Tastatur ausführbar sein
2. **Enter-Key-Convention**: User erwarten Enter-Taste bei Input-Feldern für Formular-Submission
3. **Validation-Before-Action**: Enter-Key-Handler sollte dieselbe Validation wie Button-Click verwenden
4. **State-Awareness**: Event-Handler müssen Loading/Generating-States respektieren um Race-Conditions zu vermeiden
5. **UX-Consistency**: Keyboard- und Mouse-Interaktionen sollten identische Validation/Feedback haben

**Code-Implementation:**
```javascript
// Handle Enter key press in URL input
const onUrlEnterPressed = (event) => {
  // Only proceed if URL is valid and not already loading
  if (url.value && urlValidation.value.isValid === true && !loading.value && !generating.value && !previewData.value) {
    event.preventDefault()
    loadPreview()
  }
}
```

**Betroffene Dateien:** `frontend/src/pages/NewApplication.vue` (Zeile 32: Event-Handler + Zeile 720-726: Handler-Function)

---

## [2026-01-16] - BUG-015: Escape-Taste schließt Modals nicht

**Problem:** Modals in der Anwendung konnten nicht mit der Escape-Taste geschlossen werden. User mussten das X-Icon klicken oder außerhalb des Modals klicken.

**Root Cause:** Fehlende Keyboard-Event-Handler für Modal-Komponenten:
- **SkillsOverview.vue**: "Skill hinzufügen/bearbeiten" Modal hatte keinen Escape-Key-Handler
- **JobRecommendations.vue**: "Job analysieren" Modal hatte keinen Escape-Key-Handler
- **Standard-Accessibility**: Escape-Taste ist Standard-Erwartung für Modal-Navigation
- **Event-Listener-Management**: Keine dynamische Registrierung/Deregistrierung von keydown-Events

**Fix:**
1. **Event-Handler implementiert**: `handleEscapeKey(event)` function für beide Komponenten
2. **Dynamic Listener Management**: `watch()` für Modal-State mit addEventListener/removeEventListener
3. **Conditional Logic**: Handler prüft sowohl Escape-Key als auch Modal-State vor Aktion
4. **Vue Composition API**: Import von `watch` hinzugefügt für reaktive Event-Listener

**Implementation Details:**
```javascript
// Escape key handler for modal
const handleEscapeKey = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    closeModal()
  }
}

// Watch for modal state changes to add/remove escape key listener
watch(showModal, (isModalOpen) => {
  if (isModalOpen) {
    document.addEventListener('keydown', handleEscapeKey)
  } else {
    document.removeEventListener('keydown', handleEscapeKey)
  }
})
```

**Learning:**
1. **Modal-A11Y-Standards**: Escape-Taste ist Essential für barrierefreie Modal-Navigation
2. **Event-Listener-Lifecycle**: Event-Listener müssen mit Component-State synchronisiert sein - bei Modal-Open hinzufügen, bei Close entfernen
3. **Memory-Leak-Prevention**: removeEventListener ist wichtig um Event-Handler nicht zu akkumulieren
4. **Conditional-Event-Handling**: Handler sollten sowohl Key-Type als auch Application-State prüfen
5. **Vue-Watch-Pattern**: `watch()` ist ideal für Event-Listener-Management basierend auf reaktiven State-Änderungen
6. **Cross-Component-Consistency**: Alle Modals in der App sollten dasselbe Keyboard-Verhalten haben

**Betroffene Dateien:**
- `frontend/src/components/SkillsOverview.vue` (Escape-Handler für Skill-Modal)
- `frontend/src/components/JobRecommendations.vue` (Escape-Handler für Job-Analyse-Modal)

---

## [2026-01-16] - BUG-022: Error-Toast 'Ungültige Eingabe' erscheint bei jedem Seitenwechsel

**Problem:** Beim Navigieren zu Bewerbungen/Templates/Dokumente erschien kurzzeitig ein störender Error-Toast "✗ Ungültige Eingabe", auch wenn die Seiten korrekt geladen wurden und leere States anzeigten.

**Root Cause:** Zu aggressive automatische Toast-Nachrichten im API Client:
- **Load-Funktionen**: `loadApplications()`, `loadDocuments()`, `loadTemplates()` verwenden normale `api.get()` calls
- **API-Interceptor**: `client.js:68-75` fängt ALLE 422-Fehler ab und zeigt automatisch Toast-Nachrichten
- **Backend-Response**: Bei leeren Datasets (keine Bewerbungen/Templates/Dokumente) gibt Backend 422 zurück
- **False-Positive**: Leere States sind kein "Ungültige Eingabe" Error, sondern normaler Zustand
- **UX-Problem**: User werden mit unnötigen Error-Toasts bei legitimem "no data found" Zustand belästigt

**Fix:**
1. **Silent API-Calls**: Load-Funktionen verwenden nun `api.silent.get()` statt `api.get()`
   - `loadApplications()` → `api.silent.get('/applications', ...)`
   - `loadDocuments()` → `api.silent.get('/documents')`
   - `loadTemplates()` → `api.silent.get('/templates')`
   - `checkLebenslauf()` → `api.silent.get('/documents')`
2. **Suppressierte Toasts**: `api.silent` setzt `suppressToast: true` Config-Parameter
3. **Selective Error-Handling**: Nur User-Actions (Form-Submits, Button-Clicks) zeigen automatische Error-Toasts

**Learning:**
1. **Silent System Operations**: Load-/Init-Funktionen sollten silent sein - nur User-Actions brauchen Feedback
2. **API-Error-Classification**: Unterscheidung zwischen "System-Requests" (silent) und "User-Actions" (mit Toast)
3. **Empty-State vs Error-State**: Leere Datasets sind nicht dasselbe wie Validation-Fehler
4. **UX-Noise-Reduction**: Automatische Error-Handler müssen zwischen verschiedenen Fehler-Kontexten unterscheiden
5. **API-Client-Architecture**: `api.silent` Pattern ermöglicht selective Toast-Suppression ohne globale Interceptor-Änderungen
6. **Error-Handling-Scope**: Global-Interceptor für User-facing Errors, Component-Level für System-Errors

**API-Pattern-Changes:**
- **System/Load Calls**: `api.silent.get()`, `api.silent.post()` für automatische Background-Operationen
- **User Actions**: `api.get()`, `api.post()` für Formular-Submits und Button-Actions
- **Granular Control**: Components können bei Bedarf weiterhin eigene Error-Handling haben

**Betroffene Dateien:**
- `frontend/src/pages/Applications.vue:839` (loadApplications mit api.silent)
- `frontend/src/pages/Documents.vue:442` (loadDocuments mit api.silent)
- `frontend/src/pages/Templates.vue:503` (loadTemplates mit api.silent)
- `frontend/src/pages/Templates.vue:512` (checkLebenslauf mit api.silent)

---

