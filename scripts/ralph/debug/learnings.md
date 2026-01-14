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

