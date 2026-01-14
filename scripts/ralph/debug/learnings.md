# RALF Debug Mode - Learnings

Diese Datei enthält Erkenntnisse aus Debug-Sessions. Jeder Eintrag dokumentiert ein Problem, seine Ursache und was man daraus lernen kann.

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

