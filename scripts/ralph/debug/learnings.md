# RALF Debug Mode - Learnings

Diese Datei enthält Erkenntnisse aus Debug-Sessions. Jeder Eintrag dokumentiert ein Problem, seine Ursache und was man daraus lernen kann.

---

## [2026-01-17] - BUG-043: Keine 404-Seite für ungültige Routen

**Problem:** Bei ungültigen Routen (z.B. /nonexistent-page) wird nur eine leere main-Sektion angezeigt ohne Benutzerfeedback.

**Root Cause:**
- Vue Router hatte keine catch-all Route für 404-Fälle definiert
- NotFound.vue Komponente existierte nicht, obwohl in `affectedFiles` erwähnt
- Router-Konfiguration war unvollständig

**Fix:**
1. NotFound.vue Komponente erstellt in `frontend/src/pages/` (folgt Projekt-Konvention)
2. Catch-all Route hinzugefügt: `{ path: '/:pathMatch(.*)*', component: () => import('../pages/NotFound.vue'), meta: { title: 'Seite nicht gefunden' } }`
3. 404-Seite mit Zen-Design-Ästhetik, Zurück-Navigation und hilfreichen Links

**Lessons Learned:**
- **Route-Order wichtig:** Catch-all Route MUSS am Ende der Routes-Array stehen
- **Vue Router 4 Syntax:** `/:pathMatch(.*)` statt alter `:*` Syntax
- **Projekt-Struktur beachten:** Komponenten gehören in `pages/` nicht `views/` Ordner
- **Design-Konsistenz:** NotFound-Seite muss existierende Styling-Konventionen (zen-card, animate-fade-up) befolgen
- **User Experience:** 404-Seite sollte Wege zurück zur App bieten (Home, Zurück-Button, Navigation Links)

**Code-Konventionen:**
- Lazy Loading für alle Router-Komponenten verwenden
- Meta-Titles für SEO und Browser-Tab definieren
- Projektspezifische CSS-Klassen verwenden (.zen-card, .legal-page, etc.)

---

## [2026-01-17] - BUG-045: Bewerbungsgenerierung scheitert - Lebenslauf fehlt

**Problem:** Nach der Stellenanzeigen-Analyse schlägt die Bewerbungsgenerierung mit "Lebenslauf nicht gefunden" fehl, aber es gibt keinen klaren Weg zum Upload für den User.

**Root Cause:**
- Backend (generator.py:33) wirft korrekte Fehlermeldung "Lebenslauf nicht gefunden. Bitte lade deinen Lebenslauf hoch."
- Frontend zeigt nur generische Fehlermeldung ohne Handlungsanweisung
- Keine direkte Navigation zur /documents-Seite für den Upload

**Fix:**
```vue
// Frontend: Erkennung dokumentbezogener Fehler
const isDocumentMissingError = computed(() => {
  if (!error.value) return false
  const errorLower = error.value.toLowerCase()
  return errorLower.includes('lebenslauf') ||
         errorLower.includes('resume') ||
         errorLower.includes('cv') ||
         errorLower.includes('arbeitszeugnis')
})

// Enhanced Error UI mit Action Button
<div v-if="isDocumentMissingError" class="error-actions">
  <router-link to="/documents" class="zen-btn zen-btn-sm">
    Zu den Dokumenten
  </router-link>
</div>
```

**Learning:**
- Fehlermeldungen sollten immer mit einer klaren Handlungsanweisung kombiniert werden
- Backend-Errors können als Trigger für Frontend-Actions dienen (error pattern matching)
- UX-Verbesserung durch direkte Navigation zu Lösungsseiten

---

## [2026-01-17] - BUG-042: Stellenanzeige-URL-Fehlerbehandlung inkonsistent

**Problem:** Backend gab 500 Internal Server Error zurück, Frontend zeigte aber 403 Forbidden Fehlermeldung.

**Root Cause:** Inkonsistente Fehlerbehandlung zwischen Backend und Frontend:
- Backend behandelte nur 403/404/429 als Client-Fehler (400)
- Alle anderen Exceptions führten zu 500-Fehlern
- Frontend prüfte nur auf `e.response?.data?.error` ohne HTTP-Status zu beachten

**Fix:**
```python
# Backend: Erweiterte HTTP-Code-Liste
if any(code in error_message for code in ["403", "404", "429", "400", "401", "502", "503"]):
    return jsonify({"success": False, "error": error_message}), 400
```

```javascript
// Frontend: Explizite HTTP-Status-Prüfung
if (e.response?.status === 400 && e.response?.data?.error) {
  error.value = e.response.data.error  // Client errors from WebScraper
} else if (e.response?.status === 500 && e.response?.data?.error) {
  error.value = e.response.data.error  // Server errors with user-friendly messages
}
```

**Learning:** HTTP-Status-Codes müssen Backend und Frontend konsistent behandeln:
1. Client-Fehler (4xx) = Benutzer kann Problem beheben
2. Server-Fehler (5xx) = Technisches Problem, benutzerfreundliche Nachricht
3. Frontend sollte explizit HTTP-Status prüfen, nicht nur Fehlernachrichten
4. Server-Fehler sollten geloggt und mit benutzerfreundlichen Messages versehen werden

**Prevention:**
- Zentrale Fehlerbehandlung für API-Responses
- Konsistente HTTP-Status-Code-Konventionen dokumentieren
- Frontend-Wrapper für API-Calls mit einheitlicher Fehlerbehandlung

---

## [2026-01-17] - BUG-040: Mobile Navigation Schließen-Button ist nicht funktional

**Problem:** Der Close-Button der mobilen Navigation war nicht klickbar, da er von anderen DOM-Elementen überdeckt wurde.

**Root Cause:** Z-Index-Konflikt zwischen UI-Ebenen:
- Navigation Header: `z-index: var(--z-nav)` = `1000`
- Mobile Sidebar: `z-index: 999`
- Da die Navigation einen höheren z-index hatte, überdeckte sie die mobile Sidebar

**Fix:** Mobile Sidebar z-index von 999 auf 1001 erhöht
```css
.mobile-sidebar {
  z-index: 1001; /* war: 999 */
}
```

**Learning:** Bei overlapping UI-Elementen immer z-index-Hierarchie beachten:
1. Definiere klare z-index-Stufen (z.B. 100er-Schritte)
2. Nutze CSS Custom Properties für konsistente z-index-Werte
3. Bei Click-Problemen erst z-index-Konflikte prüfen
4. Mobile Overlays brauchen höhere z-index als Header/Navigation
5. Verwende Browser DevTools um z-index-Stacks zu analysieren

**Prevention:** Z-Index-Map in CSS-Variablen anlegen:
```css
:root {
  --z-base: 0;
  --z-nav: 1000;
  --z-modal: 1010;
  --z-sidebar: 1020;
  --z-toast: 1030;
}
```

---

## [2026-01-17] - BUG-036: Job-Analyse Dialog zeigt irrelevante Fehlermeldung nach Success-Flow

**Problem:** Fehlermeldungen von URL-Analyse blieben beim Wechsel zum manuellen Eingabemodus sichtbar und verwirrten Benutzer.

**Root Cause:** State Management Problem in Vue Component:
- `analyzeError` wurde nur beim erfolgreichen API-Call oder Modal-Schließen gelöscht
- Beim Klick auf "Stellentext manuell einfügen" wurde nur `showManualInput = true` gesetzt
- Error Message Display Logic prüfte nur `v-if="analyzeError"` ohne Mode-Kontext

**Fix:** Neue `switchToManualInput()` Methode erstellt:
```js
const switchToManualInput = () => {
  showManualInput.value = true
  analyzeError.value = '' // Clear error message when switching to manual input
}
```

**Learning:** Bei Modal-/Dialog-State-Management:
1. Jeder Modusswitch sollte relevante Error-States löschen
2. Error Messages sollten mode-spezifisch sein oder beim Kontext-Wechsel gelöscht werden
3. Inline Event-Handler (@click="variable = true") vermeiden für komplexere Logic
4. State-Clearing sollte proaktiv erfolgen, nicht nur reaktiv nach Fehlern
5. UX: Fehlermeldungen eines Flows sollten nicht in anderen Flows erscheinen

**Prevention:**
- Error-State bei jeder Benutzeraktion die den Kontext wechselt resetten
- Separate Error-States für verschiedene Modi verwenden
- Lifecycle-Methods für State-Clearing nutzen

---

## [2026-01-16] - BUG-018: Route /applications/:id/mock-interview zeigt leere Seite

**Problem:** Die Route `/applications/6/mock-interview` zeigte eine leere main-Section ohne Inhalte oder Fehlermeldungen, wenn eine ungültige Application-ID verwendet wurde.

**Root Cause:** Fehlende defensive Programmierung bei Route-Parameter-Validierung:
- `applicationId` wurde aus `route.params.id` ohne Validierung extrahiert
- Bei ungültigen IDs (nicht-numerisch, undefined) entstanden JavaScript-Fehler
- Keine Error-States für Benutzer-Feedback bei fehlgeschlagenen API-Calls
- Router-Links verwendeten ungeprüfte Template-Interpolation

**Fix:** Umfassende Error-Handling und Validation:
```js
// Application-ID Validation in onMounted
if (!applicationId.value || isNaN(parseInt(applicationId.value))) {
  error.value = 'Ungültige Bewerbungs-ID'
  loading.value = false
  return
}

// Error-State im Template
<section v-if="error" class="empty-state">
  <div class="empty-card zen-card">
    <h2>Fehler beim Laden</h2>
    <p>{{ error }}</p>
    <router-link to="/applications" class="zen-btn zen-btn-ai">
      Zurück zu Bewerbungen
    </router-link>
  </div>
</section>

// Defensive Router-Links
:to="applicationId ? `/applications/${applicationId}/interview` : '/applications'"
```

**Learning:**
1. **Route Parameter Validation**: Immer URL-Parameter validieren bevor sie verwendet werden
2. **Error State Design**: Jede SPA-Seite braucht Loading, Error und Empty States
3. **Template Safety**: Router-Links mit Template-Interpolation brauchen Safeguards
4. **User Experience**: Niemals leere Seiten - immer Feedback oder Redirect
5. **Defensive Programming**: Ungültige IDs sollten graceful behandelt werden, nicht zu JS-Fehlern führen

**Code Quality:** 71 Tests bestehen, build erfolgreich, robuste Error-Handling ohne Over-Engineering.

---

## [2026-01-17] - BUG-037: Job-Analyse API schlägt mit 400 Bad Request fehl

**Problem:** Die Job-Analyse API (`/api/recommendations/analyze` und `/api/recommendations/analyze-manual`) schlug mit 400 Bad Request fehl. Backend-Error zeigte "RequirementAnalyzer.analyze_requirements() got an unexpected keyword argument job_title".

**Root Cause:** Method Signature Mismatch zwischen JobRecommender und RequirementAnalyzer:
- `RequirementAnalyzer.analyze_requirements()` erwartet nur `job_text` und `retry_count` Parameter
- `JobRecommender` übergab zusätzlich `job_title` Parameter, der in der Method Signature nicht definiert war
- Dies führte zu einem TypeError der als 400 Bad Request an Frontend weitergegeben wurde

**Fix:** Entfernung des überflüssigen `job_title` Parameters:
```python
# Vorher (fehlerhaft)
requirements = self.requirement_analyzer.analyze_requirements(
    job_text=job_data.get("description", ""),
    job_title=job_data.get("title", ""),
)

# Nachher (korrekt)
requirements = self.requirement_analyzer.analyze_requirements(
    job_text=job_data.get("description", "")
)
```

**Affected Files:**
- `backend/services/job_recommender.py:145-148` (analyze_job_for_user)
- `backend/services/job_recommender.py:220-223` (analyze_manual_job_for_user)

**Learning:**
1. **API Method Signature Consistency**: Immer Method Signaturen zwischen Services prüfen
2. **Parameter Validation**: TypeError durch unerwartete Parameter führen zu verwirrenden 400-Fehlern
3. **Service Contract Testing**: Unit Tests sollten Service-Interfaces abdecken
4. **Documentation**: Method Signaturen ändern ohne entsprechende Caller-Updates ist gefährlich
5. **Error Propagation**: Backend TypeError werden als 400 Bad Request propagiert - irreführend für User

**Code Quality:** 288 Tests bestehen, Build erfolgreich, minimaler invasiver Fix.

---

## [2026-01-16] - BUG-032: Button-Style Inkonsistenz auf Settings-Seite

**Problem:** Die Buttons "Passwort ändern" und "Neuen Key generieren" auf der Settings-Seite verwendeten `zen-btn-filled` (solid style) statt `zen-btn` (outline style) wie andere primäre Action-Buttons in der App.

**Root Cause:** Inkonsistente Button-Style-Anwendung zwischen verschiedenen Seitenkategorien:
- **Authentication Pages** (Login, Register, ResetPassword): Verwenden `zen-btn-filled` für Submit-Buttons
- **Application Pages** (NewApplication, Applications, etc.): Verwenden `zen-btn` für primäre Actions
- **Settings Page**: Verwendete fälschlicherweise `zen-btn-filled` wie Authentication Pages

**Fix:** Button-Classes harmonisiert für Settings-Seite:
```js
// Vorher
<button class="zen-btn zen-btn-filled">Passwort ändern</button>
<button class="zen-btn zen-btn-filled">Neuen Key generieren</button>

// Nachher
<button class="zen-btn">Passwort ändern</button>
<button class="zen-btn">Neuen Key generieren</button>
```

**Learning:**
1. **Design System Consistency**: Button-Styles sollten nach Kontext gruppiert werden (Auth vs App vs Admin)
2. **CSS Architecture**: `.zen-btn` = outline (primary), `.zen-btn-filled` = solid (emphasis)
3. **Style Patterns**: Authentication = high emphasis (filled), Application = medium emphasis (outline)
4. **Visual Hierarchy**: Filled buttons signalisieren kritische/finale Actions, outline für reguläre Actions
5. **UX Consistency**: User erwartet gleiche Interaktionsmuster innerhalb derselben App-Sektion

**Code Quality:** 71 Tests bestehen, build erfolgreich, minimal invasive Änderung.

---

## [2026-01-16] - BUG-031: Keine sichtbare Validierungsmeldung bei leerem Login-Formular

**Problem:** Beim Klicken auf "Anmelden" ohne Eingaben erschienen keine sichtbaren Validierungsmeldungen. Nur der Fokus wurde auf das E-Mail-Feld gesetzt, aber keine roten Fehlertexte waren sichtbar.

**Root Cause:** Vue-Validation-Logic Timing-Problem:
- Validation existierte bereits via `emailError` und `passwordError` computed properties
- Fehlermeldungen werden nur angezeigt wenn entsprechende `touched` flags gesetzt sind
- `handleLogin()` führte Validation durch, aber setzte `touched` flags nie auf `true`
- Ohne `touched = true` bleiben Fehlermeldungen unsichtbar

**Fix:** Pre-Submit-Validation in `handleLogin()`:
```js
// Vor der Validation touched-Flags setzen
emailTouched.value = true
passwordTouched.value = true

// Dann Validation prüfen
if (emailError.value || passwordError.value) {
  return // Prevent submission
}
```

**Learning:**
1. **Vue Form Validation Pattern**: `touched` flags sind essentiell für UX - Fehler erst nach User-Interaction zeigen
2. **Validation Timing**: Bei Submit-Buttons immer touched-Flags explizit setzen um Fehler sichtbar zu machen
3. **Defensive UX**: Auch wenn Focus-Management funktioniert, braucht der User visuelle Fehlermeldungen
4. **Existing Logic Leverage**: Oft ist Validation-Logic schon da, nur die Trigger fehlen
5. **Two-Stage Validation**: Touched-Flags setzen → Validation prüfen → Submit verhindern wenn ungültig

**Code Quality:** Alle 71 Tests bestehen, npm run build erfolgreich, minimale Änderung ohne Over-Engineering.

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

## BUG-023: Error State vs Empty State korrekt unterscheiden

**Problem:** Applications-Seite zeigte "Noch keine Bewerbungen" auch bei API-Fehlern (422). User konnten nicht zwischen "keine Daten vorhanden" und "technischer Fehler" unterscheiden.

**Root Cause:** Keine Unterscheidung zwischen "keine Daten" und "API-Fehler":
- `loadApplications()` hatte keinen Error State - nur console.error() im catch-Block
- Template zeigte immer Empty State bei `applications.length === 0`
- User dachten bei API-Fehlern "ich habe keine Bewerbungen" statt "es gibt ein technisches Problem"
- Fehlende Retry-Option bei temporären API-Problemen

**Fix:** Comprehensive Error State Handling hinzugefügt:
1. `loadError` reactive State Variable in Applications.vue:706
2. `loadApplications()` setzt `loadError = true` bei catch + `applications = []` für klaren State
3. Template verwendet drei States: `v-if="loading"` → `v-else-if="loadError"` → `v-else-if="applications.length > 0"` → `v-else` (Empty)
4. Error State zeigt Retry-Button mit Reload-Funktionalität + klare Fehlermeldung
5. CSS-Styling für Error State mit Terra-Color-Scheme (warning-orange) und Retry-Icon

**Template Logic Pattern:**
```vue
<!-- Loading State -->
<div v-if="loading">Loading...</div>

<!-- Error State mit Retry -->
<div v-else-if="loadError" class="error-state">
  <div class="error-icon">⚠️ Icon</div>
  <h3>Fehler beim Laden der Bewerbungen</h3>
  <p>Es gab ein technisches Problem beim Laden. Bitte versuchen Sie es erneut.</p>
  <button @click="loadApplications()" class="zen-btn zen-btn-ai">
    🔄 Erneut versuchen
  </button>
</div>

<!-- Data Available -->
<section v-else-if="applications.length > 0">Show Data</section>

<!-- Empty State -->
<section v-else class="empty-state">
  <h3>Noch keine Bewerbungen</h3>
  <p>Generieren Sie Ihre erste Bewerbung...</p>
</section>
```

**Learning:**
1. **4-State-Pattern für Async Data**: Loading → Error → Data → Empty sind vier verschiedene UI-Zustände
2. **Error vs Empty Distinction**: Technische Fehler ≠ leere Datasets - brauchen verschiedene User-Experience
3. **Retry-UX**: Error State sollte IMMER Retry-Möglichkeit bieten für temporäre API-Probleme
4. **Clear Error-Messages**: "Fehler beim Laden der Bewerbungen" + "technisches Problem" ist klarer als generische Meldungen
5. **Error-State-Reset**: Bei erneutem Load-Versuch `loadError = false` setzen für korrekten State-Cycle
6. **Visual-Hierarchy**: Error State mit auffälliger Farbe (Terra-Orange) vs. Empty State mit subtilen Grau-Tönen
7. **Icon-Usage**: Warning-Icon für Error State vs. Circle-Icon für Empty State - semantische Unterscheidung

**Pattern für andere Pages**: Dashboard, Documents, Templates, etc. sollten dasselbe 4-State-Pattern verwenden.

**Betroffene Dateien:**
- `frontend/src/pages/Applications.vue:706` (loadError State)
- `frontend/src/pages/Applications.vue:165-183` (Error State Template)
- `frontend/src/pages/Applications.vue:1531-1558` (Error State CSS)

---

## [2026-01-16] - BUG-024: Aktions-Button 'Bewerbungen' fehlt in Mobile-Ansicht auf Company Insights

**Problem:** Der 'Bewerbungen' Button in der Company Insights Tabelle war in Mobile-Ansicht (< 480px) komplett unzugänglich. Die Aktions-Spalte wurde ausgeblendet und auch horizontales Scrollen machte sie nicht erreichbar.

**Root Cause:** Naive CSS Media Query Behandlung ohne Mobile-Alternative:
- **CSS Rule**: `@media (max-width: 480px) { .th-action, .td-action { display: none; } }`
- **Design-Gap**: Spalte wurde komplett versteckt ohne alternative Darstellung für Mobile
- **UX-Blackhole**: User hatten keine Möglichkeit, von Company-Insights zu spezifischen Bewerbungen zu navigieren
- **Responsive-Pattern-Missing**: Keine mobile Darstellung für komplexe Tabellen mit Action-Buttons

**Fix:** Mobile-Button-Integration in Firma-Zelle:
1. **HTML-Structure**: Button in Firma-Zelle mit flexbox-Layout hinzugefügt:
   ```html
   <div class="firma-cell">
     <span class="firma-name">{{ company.firma }}</span>
     <button class="zen-btn zen-btn-xs mobile-action-btn">Bewerbungen</button>
   </div>
   ```

2. **CSS Mobile-Pattern**:
   - Desktop: Action-Button bleibt in separater Spalte (rechts)
   - Mobile: Action-Button wird unter Firma-Name angezeigt
   - `mobile-action-btn` per default hidden, nur bei ≤480px mit `display: inline-flex !important`

3. **Responsive-Design**:
   - Action-Spalte bleibt Desktop-sichtbar für Tabellen-Konsistenz
   - Mobile-Button-Integration ohne Layout-Bruch
   - Gleiche Funktionalität über alle Breakpoints

**Learning:**
1. **No-Content-Loss-Principle**: Bei responsive Design darf KEIN Content oder Funktionalität komplett verschwinden
2. **Mobile-Action-Patterns**: Actions können in Mobile in Inhaltszellen integriert werden (z.B. unter Firma-Name)
3. **Progressive-Enhancement**: Desktop-Layout bleibt optimal, Mobile bekommt angepasste aber vollständige UX
4. **CSS-Override-Pattern**: `display: none` → `display: inline-flex !important` für gezieltes Mobile-Override
5. **Button-Size-Mobile**: `zen-btn-xs` für kompakte Mobile-Buttons in dichten Layouts
6. **Testing-Multiple-Viewports**: 480px, 375px, 768px sind kritische Mobile-Breakpoints für Navigation/Actions

**Code-Pattern für Tables-with-Actions:**
```css
/* Desktop: Separate Action Column */
.td-action { text-align: right; }

/* Mobile: Integrate Actions in Content Cells */
.mobile-action-btn { display: none; }

@media (max-width: 480px) {
  .th-action, .td-action { display: none; }      /* Hide action column */
  .mobile-action-btn { display: inline-flex !important; }  /* Show integrated button */
}
```

**Betroffene Dateien:** `frontend/src/pages/CompanyInsights.vue` (Mobile-Button-Integration + CSS-Responsive-Pattern)

---

## [2026-01-16] - BUG-025: KPI-Statistik-Karten zeigen permanente Skeleton-Loading statt Daten

**Problem:** Das Dashboard zeigte permanent Skeleton-Placeholder-Karten statt KPI-Statistiken. API gab 422-Fehler zurück, aber Error State wurde nicht korrekt angezeigt.

**Root Cause:** Template-Logic Bug in Error State Handling:
- **Template-Condition**: `v-else-if="!loadError"` für Loading State war zu permissiv
- **Logic-Gap**: Wenn `loadError = true` UND `stats = null`, wurde weder Loading noch Error State gezeigt
- **Result**: Permanent sichtbare Skeleton-Cards ohne Daten oder Error-Feedback
- **Missing CSS**: Error State Templates verwendeten CSS-Klassen die nicht definiert waren

**Fix:**
1. **Template-Logic Correction**: `v-else-if="!loadError"` → `v-else-if="!loadError && !stats"`
   - Loading State nur wenn KEIN Error UND KEINE Daten vorhanden
   - Error State wird bei `loadError = true` über `v-else` korrekt angezeigt

2. **Silent API Usage**: `api.get('/stats')` → `api.silent.get('/stats')`
   - Verhindert automatische Toast-Nachrichten bei API-Fehlern
   - Ermöglicht eigene Error State UI statt disruptive Toasts

3. **Complete Error State CSS**:
   - `.loading-error`, `.loading-error-icon`, `.loading-error-message`, `.loading-error-retry`
   - Grid-spanning Layout (`grid-column: 1 / -1`)
   - Zen-styled Retry-Button mit Hover-States

**Template-Logic-Pattern (3-State-System):**
```vue
<!-- Data Available -->
<div v-if="stats" class="stats-grid">Show Data</div>

<!-- Loading State: Kein Error UND keine Daten -->
<div v-else-if="!loadError && !stats" class="stats-grid">Skeleton Loading</div>

<!-- Error State: Bei loadError = true -->
<div v-else class="loading-error">
  <ErrorIcon />
  <p>Statistiken konnten nicht geladen werden</p>
  <button @click="retryLoadStats">Erneut versuchen</button>
</div>
```

**Learning:**
1. **3-State-Logic-Precision**: Data/Loading/Error States brauchen präzise Boolean-Logic - nicht nur `!error` sondern `!error && !data`
2. **Template-v-if-Chain**: Bei if/else-if/else-Ketten alle State-Kombinationen durchdenken (error+data, error+no-data, no-error+data, no-error+no-data)
3. **Silent-API-for-Background-Loads**: Dashboard/Stats-Loading sollte keine Toasts zeigen - nur User-Actions brauchen immediate Feedback
4. **CSS-Template-Sync**: Wenn Template CSS-Klassen verwendet, müssen diese definiert sein - nicht nur HTML ohne Styling
5. **Error-State-UX**: Retry-Button ist essentiell bei API-Error States - User braucht Möglichkeit zur Wiederholung
6. **Grid-Layout-Errors**: Error State in Grid-Layout braucht `grid-column: 1 / -1` um alle Spalten zu spannen

**Technical Implementation:**
- Loading State wird NUR bei `!loadError && !stats` gezeigt
- `api.silent.get()` verhindert Toast-Pollution bei System-Calls
- Error State hat vollständiges CSS für konsistente UX
- Retry-Button setzt `stats = null` vor erneutem API-Call für korrekten Loading-State

**Betroffene Dateien:** `frontend/src/pages/Dashboard.vue` (Template-Logic + Error-State-CSS + Silent-API)

---

## BUG-027: Feature-Liste des aktuellen Plans ist leer (16.01.2026)

**Problem:**
Subscription-Seite zeigte leere Feature-Liste, weil `subscription.plan_details.features` nicht reliable geladen wurde. User konnte nicht sehen, was in ihrem Plan enthalten ist.

**Root Cause:**
- Single-Point-of-Failure: Template verließ sich nur auf eine Datenquelle (`subscription?.plan_details?.features`)
- Keine Fallbacks bei API-Datenstructur-Änderungen oder Lade-Fehlern
- Hardcoded Features in Backend waren korrekt, aber Frontend-Access war fragil

**Fix:**
```vue
// Vorher: Direkte Binding ohne Fallback
<li v-for="feature in subscription?.plan_details?.features">

// Nachher: Multi-Layer-Fallback-System
<li v-for="feature in getCurrentPlanFeatures()">
```

**Learning:**
1. **Multi-Layer-Fallback-Strategy**: Bei kritischen UI-Elementen immer mehrere Datenquellen vorsehen
2. **Plan-Data-Redundancy**: Plan-Features sollten von mehreren Quellen (API-Response, availablePlans, hardcoded) abrufbar sein
3. **Graceful-Degradation**: Auch bei vollständigem API-Fail sollte Basic-Info (Plan-Features) anzeigbar bleiben
4. **Computed-Properties-for-Complex-Fallbacks**: Komplexe if/else-Logik gehört in Computed Properties, nicht ins Template

**Technical Implementation:**
- Computed Property `getCurrentPlanFeatures()` mit 4-stufigem Fallback
- Primär: `subscription.plan_details.features` (API-Response)
- Sekundär: `availablePlans.find().features` (Plan-Lookup)
- Tertiär: Hardcoded per Plan-Type (free/basic/pro)
- Quartär: Error-Message ("Keine Features verfügbar")

**Betroffene Dateien:** `frontend/src/pages/SubscriptionView.vue` (Template-Binding + Computed-Property)

---

## BUG-028: Keine Upgrade-Optionen oder Plan-Vergleich sichtbar (16.01.2026)

**Problem:**
Plan-Vergleichssektion wurde nicht angezeigt wenn `availablePlans` leer war (API-Fehler/Ladeprobleme). User konnten keine anderen Pläne sehen oder upgraden.

**Root Cause:**
- Fragile UI-Bedingung: `v-if="subscription && availablePlans.length > 0"`
- Single-Point-of-Failure: Komplette Sektion versteckt bei API-Problemen
- Keine Fallback-Strategie für kritische Business-Features (Plan-Verkauf)

**Fix:**
```vue
// Vorher: Fragile API-abhängige Bedingung
v-if="subscription && availablePlans.length > 0"

// Nachher: Robuste Bedingung + Fallback-System
v-if="subscription"
+ getAvailablePlans() computed property mit API + hardcoded Fallback
```

**Learning:**
1. **Business-Critical-UI-Never-Hide**: Revenue-generierenden Features (Plan-Verkauf) nie durch API-Fehler verstecken
2. **Dual-Source-Strategy**: Für Plan-Daten sowohl API als auch hardcoded Fallback vorhalten
3. **UI-Condition-Review**: `array.length > 0` Bedingungen sind fragil - besser mit Fallback-Daten arbeiten
4. **Always-Show-Core-Features**: Upgrade-Buttons und Plan-Vergleich sollten immer sichtbar sein

**Technical Implementation:**
- `getAvailablePlans()` computed property mit API-Daten + Hardcoded-Fallback
- Entfernte `availablePlans.length > 0` Bedingung aus Template
- Plan-Vergleich wird immer angezeigt (auch bei API-Fehlern)
- 3 komplette Plan-Definitionen als Fallback (free/basic/pro)

**Betroffene Dateien:** `frontend/src/pages/SubscriptionView.vue` (Template-Condition + Computed-Fallback)

---

## BUG-029: Stripe Checkout schlägt fehl - Plan nicht konfiguriert (16.01.2026)

**Problem:**
400 Bad Request "Plan nicht konfiguriert" beim Klick auf Upgrade-Buttons, weil STRIPE_PRICE_BASIC und STRIPE_PRICE_PRO Environment-Variablen nicht gesetzt waren.

**Root Cause:**
- Missing Environment-Variables: `config.STRIPE_PRICE_BASIC` und `config.STRIPE_PRICE_PRO` waren `None`
- Hard-Fail ohne Fallback: Code prüfte nur Existenz, keine Development-Alternative
- Cryptic Error-Message: "Plan nicht konfiguriert" gab keine Hilfestellung

**Fix:**
```python
# Vorher: Harter Fehler bei fehlenden Env-Vars
STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC")  # → None

# Nachher: Mock-IDs als Development-Fallback
STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC", "price_dev_basic_mock")

# + Benutzerfreundliche Fehlermeldung bei Mock-Usage
if price_id.startswith("price_dev_"):
    return jsonify({"error": "Stripe ist im Development-Modus nicht konfiguriert"})
```

**Learning:**
1. **Development-Fallbacks-for-External-APIs**: Immer Mock-/Test-Werte für externe Services vorhalten
2. **Environment-Config-Validation**: Kritische Config-Werte nicht ohne Fallback laden
3. **User-Friendly-Dev-Messages**: "Development-Modus" statt "nicht konfiguriert" - erklärt warum es nicht funktioniert
4. **503-vs-400-Error-Codes**: Service Unavailable (503) statt Bad Request (400) für Config-Probleme

**Technical Implementation:**
- Mock-Price-IDs (`price_dev_basic_mock`, `price_dev_pro_mock`) als config defaults
- Runtime-Check auf Mock-IDs mit benutzerfreundlicher 503-Fehlermeldung
- Klare Unterscheidung zwischen User-Fehler (400) und System-Setup-Problem (503)

**Betroffene Dateien:** `backend/config.py` + `backend/routes/subscriptions.py` (Environment-Fallbacks + Error-Handling)

---

## BUG-030: Fehlende Lebenslauf-Warnung vor ATS-Analyse (16.01.2026)

**Problem:**
User sahen erst NACH dem Klick eine generische Fehlermeldung 'Ungültige Eingabe', anstatt VOR dem Klick eine klare Warnung über den fehlenden Lebenslauf zu bekommen.

**Root Cause:**
- Unsichere Fallback-Logic: `hasResume = true` als Default + bei API-Fehler
- API-Error-Catch setzte automatisch `hasResume = true` (Zeile 726)
- Existierende Warnung-UI wurde durch falsche Variable ausgeblendet

**Fix:**
```javascript
// Vorher: Unsichere Defaults
const hasResume = ref(true) // Assume true until checked
catch { hasResume.value = true } // Optimistic fallback

// Nachher: Sicherheitsfokussierte Defaults
const hasResume = ref(false) // Assume false until confirmed (safe default)
catch { hasResume.value = false } // Pessimistic but safe fallback
```

**Learning:**
1. **Security-First-Defaults**: Bei Features mit Voraussetzungen (wie Resume-Upload) immer pessimistische Defaults wählen
2. **Show-Warning-over-False-Positive**: Lieber eine unnötige Warnung zeigen als kritische Info verstecken
3. **API-Error-Fallback-Strategy**: Bei Check-APIs sollten Fehler zu restriktivem Zustand führen, nicht zu permissivem
4. **Silent-API-for-Background-Checks**: `api.silent.get()` für Status-Checks um User-Toast-Spam zu vermeiden

**Technical Implementation:**
- Initial-State: `hasResume = false` (Warnung wird standardmäßig gezeigt)
- Error-Fallback: `hasResume = false` (bei API-Fehler bleibt Warnung)
- Silent-API: Verhindert Toast-Pollution bei Background-Checks
- Console-Logging: Ermöglicht Debugging ohne User-Störung

**Betroffene Dateien:** `frontend/src/pages/ATSView.vue` (Default-State + Error-Fallback-Logic)

---

## [2026-01-17] - BUG-033: Subscription-Seite rendert nicht - getAvailablePlans function fehlt

**Problem:** Die gesamte Subscription-Seite (/subscription) wurde nicht gerendert aufgrund eines JavaScript-Fehlers. Console zeigte "TypeError: getAvailablePlans is not a function" - die Seite blieb komplett leer.

**Root Cause:** Funktions-vs-Computed-Property Inkonsistenz:
- **Template**: Verwendete `getAvailablePlans()` als Funktionsaufruf (mit Klammern) in 10+ v-for Schleifen
- **Script**: Definierte `getAvailablePlans` als `computed` property, nicht als Funktion
- **Vue-Rule**: Computed properties werden im Template OHNE Klammern referenziert
- **JavaScript-Error**: `getAvailablePlans()` call auf computed property führt zu "not a function" TypeError
- **Page-Crash**: Ein einziger JavaScript-Fehler verhindert Rendering der gesamten Komponente

**Fix:**
1. **Template-Calls korrigiert**: Alle `getAvailablePlans()` → `getAvailablePlans` (Klammern entfernt)
2. **Script-Access korrigiert**: `getAvailablePlans.find()` → `getAvailablePlans.value.find()` in computed properties

**Specific Changes:**
```vue
// Template: 10 verschiedene v-for Statements
v-for="plan in getAvailablePlans()"  // ❌ Fehler
v-for="plan in getAvailablePlans"    // ✅ Korrekt

// Script: Computed property access
planFromAvailable = getAvailablePlans.find(plan => ...)      // ❌ Fehler
planFromAvailable = getAvailablePlans.value.find(plan => ...)  // ✅ Korrekt
```

**Learning:**
1. **Vue Computed Property Syntax**: Template verwendet `computedProperty`, Script verwendet `computedProperty.value`
2. **Function vs Computed Distinction**: Funktionen mit `()`, Computed Properties ohne `()`
3. **Error Cascade Effect**: Ein Template-Fehler kann gesamte Komponente zum Absturz bringen
4. **Consistent Pattern Enforcement**: Bei Refactoring (function→computed) ALLE Referenzen überprüfen
5. **Template-Script-Synchronization**: Template-Bindings müssen mit Script-Definitions konsistent sein

**Quality Assurance:**
- Build: ✅ erfolgreich (alle 166 Module kompiliert)
- Linting: ✅ ESLint clean für SubscriptionView.vue
- Tests: ✅ 71 Frontend + 288 Backend Tests bestehen
- Runtime: ✅ Subscription-Seite rendert korrekt mit Plan-Vergleichstabelle

**Pattern für ähnliche Fixes:**
- Bei `computed(() => {...})` Definition → Template ohne `()`
- Bei `function name() {...}` Definition → Template mit `()`
- Bei computed property access in script → immer `.value` verwenden

**Betroffene Dateien:** `frontend/src/pages/SubscriptionView.vue` (10+ Template-Calls + 1 Script-Access)

---

## [2026-01-17] - BUG-034: ATS-Seite zeigt nur Überschrift - Hauptfunktionalität fehlt

**Problem:** Bug-Report beschrieb, dass die ATS-Seite nur eine Überschrift und Beschreibungstext zeigte, aber kein Formular oder Interaktionselemente für die ATS-Analyse.

**Root Cause:** Veralteter Bug-Report - Feature war bereits vollständig implementiert:
- **ATSView.vue Analyse**: Datei enthielt bereits vollständige ATS-Funktionalität (1686 Zeilen)
- **Implementierte Features**: URL/Text-Input, Analyse-Button, Score-Visualisierung, Keyword-Kategorien, Verbesserungsvorschläge, Analyse-Historie
- **Router-Integration**: Route `/ats` korrekt definiert und in Navigation eingebunden
- **Related Fixes**: BUG-030 (Lebenslauf-Warnung) bereits implementiert als Teil der ATS-Funktionalität
- **Git-Historie**: Mehrere ATS-bezogene Commits zeigen kontinuierliche Feature-Entwicklung

**Fix:**
- Kein Code-Fix erforderlich - Feature war bereits vollständig implementiert
- Bug-Status in `bugs.json` von `fixed: false` auf `fixed: true` aktualisiert
- Bug-Report war vermutlich aus früher Entwicklungsphase und wurde nicht aktualisiert

**Learning:**
1. **Bug-Status-Verification**: Immer aktuellen Code-Stand prüfen bevor Fix-Implementierung - Bug könnte bereits behoben sein
2. **Feature-Completeness-Check**: Bei "Missing Feature" Bugs die entsprechende Vue-Komponente auf vollständige Implementierung prüfen
3. **Git-History-Analysis**: `git log --grep="FEATURE"` zeigt ob Feature bereits entwickelt wurde
4. **Code-vs-Report-Discrepancy**: Bug-Reports können durch parallele Entwicklung veralten ohne Status-Update
5. **Route-Integration-Verification**: Feature-Routes in `router/index.js` und Navigation-Links prüfen für vollständige Integration
6. **Related-Bug-Cross-Check**: Verwandte Bug-Fixes (z.B. BUG-030 für ATS-Lebenslauf-Check) zeigen Feature-Entwicklung an

**Quality Verification:**
- ✅ Route `/ats` korrekt in Router definiert
- ✅ Navigation-Links in App.vue und Mobile-Navigation vorhanden
- ✅ ATSView.vue enthält vollständige ATS-Analyse-Funktionalität (1686 Zeilen Code)
- ✅ Responsive Design und Error-Handling implementiert
- ✅ Integration mit Backend-API (`/ats/analyze`) vorhanden
- ✅ BUG-030 Fix (Lebenslauf-Warnung) bereits Teil der ATS-Implementierung

**Code Quality:** Keine Änderungen erforderlich - bestehendes Feature war bereits vollständig und korrekt implementiert.

---

## [2026-01-17] - BUG-035: Stellenanzeigen-Parser wirft 500-Serverfehler bei Job-Portal Requests

**Problem:** Beim Laden von StepStone-URLs gab das Backend 500 Internal Server Error zurück, obwohl der erwartete 403 Forbidden Error von Job-Portalen abgefangen werden sollte.

**Root Cause:** Mangelhafte Exception-Behandlung in HTTP-Request-Hierarchie:
- **WebScraper**: `response.raise_for_status()` wirft `requests.HTTPError` bei 403-Status-Codes
- **Exception-Handler**: Fing `HTTPError` als generische `requests.RequestException` ab
- **Re-Raise-Pattern**: Warf alle HTTP-Errors als generische `Exception` neu → verlor HTTP-Status-Context
- **Applications-Endpoint**: Behandelte alle `Exception`s als 500-Server-Errors → falsche HTTP-Semantik

**Flow-Problem:**
```
StepStone 403 → requests.HTTPError → WebScraper Exception → Applications 500 Error
```

**Fix:**
1. **WebScraper HTTP-Error-Handling (`services/web_scraper.py`)**:
   ```python
   # Vorher: Alle HTTP-Errors als generische Exception
   except requests.RequestException as e:
       raise Exception(f"Fehler beim Laden der URL: {str(e)}") from e

   # Nachher: Spezifische HTTP-Error-Behandlung
   except requests.HTTPError as e:
       if e.response.status_code == 403:
           raise Exception("Die Stellenanzeige ist nicht zugänglich (403 Forbidden). Job-Portale blockieren oft automatisierte Zugriffe. Versuchen Sie es mit manueller Eingabe.") from e
       elif e.response.status_code == 404:
           raise Exception("Stellenanzeige nicht gefunden (404). Bitte überprüfen Sie die URL.") from e
       elif e.response.status_code == 429:
           raise Exception("Zu viele Anfragen (429). Bitte warten Sie einen Moment und versuchen Sie es erneut.") from e
       else:
           raise Exception(f"HTTP-Fehler beim Laden der Stellenanzeige ({e.response.status_code}): {str(e)}") from e
   ```

2. **Applications-Endpoint Error-Mapping (`routes/applications.py`)**:
   ```python
   # Vorher: Alle Exceptions als 500
   except Exception as e:
       return jsonify({"success": False, "error": f"Fehler beim Laden der Stellenanzeige: {str(e)}"}), 500

   # Nachher: HTTP-Error-Detection für korrekten Status-Code
   except Exception as e:
       error_message = str(e)
       if any(code in error_message for code in ["403", "404", "429"]):
           return jsonify({"success": False, "error": error_message}), 400  # Client Error
       else:
           return jsonify({"success": False, "error": f"Fehler beim Laden der Stellenanzeige: {error_message}"}), 500
   ```

**Learning:**
1. **HTTP-Error-Semantik**: 403/404/429 sind Client-Errors (4xx), nicht Server-Errors (5xx) - API sollte HTTP-Status-Codes korrekt weiterleiten
2. **Exception-Context-Preservation**: Beim Re-Raising von HTTP-Errors Status-Code-Information nicht verlieren durch generische Exception-Wrapping
3. **Layered-Error-Handling**: Service-Layer (WebScraper) sollte benutzerfreundliche Messages erzeugen, API-Layer richtige HTTP-Codes setzen
4. **Expected-vs-Unexpected-Errors**: Job-Portal-Blocking (403) ist erwarteter Zustand, nicht interner Server-Fehler
5. **Error-Message-UX**: Spezifische, hilfreiche Fehlermeldungen ("Versuchen Sie manuelle Eingabe") statt technische HTTP-Details
6. **Pattern-Based-Error-Detection**: String-Matching auf Error-Messages als Fallback wenn Exception-Types verloren gehen

**Quality Verification:**
- ✅ 288 Backend-Tests bestehen (pytest)
- ✅ Ruff-Linting clean
- ✅ Frontend-Build erfolgreich
- ✅ HTTP-403-Errors werden nun als 400-Client-Errors behandelt (nicht 500)
- ✅ Benutzerfreundliche Error-Messages für Job-Portal-Blocking

**Technical Implementation:**
- WebScraper: Spezifische HTTP-Error-Handler für 403/404/429 mit deutschen UX-Nachrichten
- Applications-Endpoint: String-basierte Error-Classification für HTTP vs. System-Errors
- Beide Methoden (`fetch_structured_job_posting` + `scrape_html`) konsistent behandelt

---

## BUG-039 Fix: Gmail-Integration Konfigurationsprüfung

**Problem:** Gmail-Integration Button warf Backend-Fehler + doppelte Fehlermeldungen bei fehlender Konfiguration

**Root Cause:** OAuth-Services versuchten Initiierung ohne vorherige Konfigurationsprüfung:
- `GmailService.get_client_config()` warf `ValueError` bei fehlenden ENV-Vars
- Frontend-API-Interceptor zeigte zusätzliche Fehlermeldung neben Backend-Response
- Technische OAuth-Fehlermeldungen wurden ungefiltert an User weitergegeben

**Solution Approach:**
1. **Frontend-First-Validation**: Integration-Status via `/api/email/integration-status` prüfen
2. **Backend-Early-Return**: OAuth-Route prüft Konfiguration vor Service-Call
3. **UX-Enhancement**: Disabled-Button + Tooltip für nicht konfigurierte Services
4. **Single-Error-Message**: Keine doppelten Toast-Nachrichten mehr

**Key Learnings:**
1. **Pre-Flight-Config-Checks**: OAuth-Flows sollten ENV-Var-Verfügbarkeit prüfen bevor Client-Setup
2. **API-Design-Pattern**: Status-Endpoint (`/integration-status`) für Frontend-State-Management bei externen Dependencies
3. **Error-Message-Deduplication**: API-Interceptor sollte nicht zusätzliche Errors bei bereits behandelten Client-Errors zeigen
4. **Service-Configuration-Separation**: Konfiguration-Check von Service-Logic trennen für bessere Error-Handling
5. **Graceful-Degradation**: Features als "nicht konfiguriert" markieren statt Crashes bei fehlender Config

**Quality Verification:**
- ✅ Backend-Linting clean (ruff)
- ✅ Frontend-Build erfolgreich
- ✅ Frontend-Linting (nur warnings für andere Components)
- ✅ Gmail/Outlook-Buttons zeigen klaren Status
- ✅ Keine Backend-Fehler bei fehlender OAuth-Config

**Technical Implementation:**
- **Backend**: `/email/integration-status` Route mit ENV-Var-Check für Gmail/Outlook
- **Backend**: Early-Return in `gmail/auth-url` und `outlook/auth-url` mit deutschen Fehlermeldungen
- **Frontend**: Integration-Status-Loading in Settings-Page mit disabled-Button-Logic
- **Frontend**: Präventive Client-Side-Checks vor OAuth-Popup-Öffnung

**Prevented Issues:**
- Verwirrende technische OAuth-Errors für End-Users
- Doppelte Error-Toast-Nachrichten
- Backend-500-Errors bei normaler Feature-Unavailability
- Schlechte UX bei missing External-Service-Configuration

---

## BUG-041: Job-Analyse API-Fehlerbehandlung inkonsistent

**Problem:** Frontend zeigte bei Server-Fehlern (500) eigene Fehlermeldungen zusätzlich zu den automatischen Toast-Nachrichten des API-Clients. Dies führte zu verwirrenden oder doppelten Fehlermeldungen für User.

**Root Cause:** Inconsistente Fehlerbehandlung zwischen API-Client und Frontend-Komponenten:
- API-Client (`frontend/src/api/client.js`): Zeigt automatisch Toast für Server-Fehler (500+)
- JobRecommendations.vue: Zeigte zusätzlich eigene `analyzeError` Meldung
- User erlebte: Doppelte oder falsche Fehlermeldungen

**Solution:** Differenzierte Fehlerbehandlung in Frontend-Komponenten:
- Server-Fehler (500+): Keine eigene Fehlermeldung, API-Client Toast-Handling überlassen
- Client-Fehler (400/422): Spezifische Fehlermeldung aus response.data.error anzeigen
- Pattern: `if (error.response?.status >= 500) { analyzeError.value = '' }`

**Quality Assurance:**
- ✅ Frontend Tests passing
- ✅ Backend Tests passing (288 passed)
- ✅ Frontend Linting clean (nur warnings für andere Components)
- ✅ Backend Linting clean (ruff)
- ✅ ESLint-Error in MockInterview.vue behoben (unused `router` variable)

**Technical Implementation:**
- **Frontend**: Conditional error handling in `analyzeJob()` und `analyzeManualJob()`
- **Frontend**: Server-error distinction verhindert doppelte UI-Fehlermeldungen
- **API-Client**: Existing toast-logic für Server-errors bleibt unverändert
- **Pattern**: Status-Code-basierte Fehlerbehandlung zwischen API-Client und Component-Level

**Prevented Issues:**
- Verwirrende doppelte Fehlermeldungen bei API-Server-Fehlern
- False-positive 403-Meldungen bei tatsächlichen 500-Internal-Server-Errors
- Inconsistente UX zwischen API-Client-Toast und Component-Error-Display
- User-Confusion über tatsächliche Error-Ursache

---



---

## [2026-01-17] - BUG-038: Modal-Overlay blockiert Navigation während Job-Analyse geöffnet ist

**Problem:** Wenn das Job-Analyse Modal geöffnet war, konnten andere Links auf der Seite (z.B. 'Jetzt verifizieren') nicht mehr geklickt werden, da das Modal-Overlay alle Klicks abfing.

**Root Cause:** Unzuverlässiges `@click.self` Event-Handling im Modal-Overlay:
- **Template-Issue**: `@click.self="showAnalyzeModal = false"` funktionierte nicht robust bei komplexen DOM-Strukturen
- **Event-Propagation**: `@click.self` kann bei verschachtelten Elementen und CSS-Transformationen unvorhersagbar sein
- **Z-Index-Blocking**: Modal mit fullscreen overlay (inset: 0) und hohem z-index blockierte alle anderen Page-Interaktionen

**Fix:**
1. **Explizite Event-Handling-Funktion**: Ersetzt `@click.self` mit `@click="closeOnOverlayClick"`
2. **Target-Verification**: Neue Funktion prüft explizit `event.target === event.currentTarget`
3. **Robuste Overlay-Detection**: Direkter Vergleich verhindert false-positive Closes bei Klicks auf Modal-Content

**Implementation Details:**
```javascript
const closeOnOverlayClick = (event) => {
  // Only close if clicking on the overlay itself, not on the modal content
  if (event.target === event.currentTarget) {
    closeAnalyzeModal()
  }
}
```

**Learning:**
1. **@click.self Limitations**: `@click.self` ist nicht zuverlässig bei komplexen Layouts mit CSS-Transforms oder verschachtelten Strukturen
2. **Explicit Event Target Checking**: `event.target === event.currentTarget` ist robusterer Ansatz für Overlay-Click-Detection
3. **Modal UX**: Overlays sollten nur intended Bereiche blockieren, nicht die gesamte Page-Navigation
4. **Event Delegation**: Explizite Event-Handler-Funktionen sind wartbarer als Inline-Event-Bindings bei komplexer Logik
5. **Z-Index Best Practices**: Hohe z-index Values erfordern besondere Aufmerksamkeit bei Event-Handling

**Betroffene Dateien:**
- `frontend/src/components/JobRecommendations.vue` (Modal-Overlay Event-Handling)
