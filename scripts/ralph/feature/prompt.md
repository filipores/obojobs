# RALF Feature Mode

Implementiere User Stories aus `scripts/ralph/feature/prd.json` eine nach der anderen.

## Dateien
- **PRD**: `scripts/ralph/feature/prd.json` - Stories mit `passes: false`, sortiert nach `priority`
- **Kontext**: `AGENTS.md` - Projekt-Konventionen

## Workflow

1. **Story finden**: Lies PRD, nimm Story mit `passes: false` und niedrigster `priority`
2. **Implementieren**: Erfülle ALLE Acceptance Criteria, befolge AGENTS.md
3. **DB-Migration**: Falls neue/geänderte Models:
   ```bash
   cd backend && source venv/bin/activate
   FLASK_APP=app.py flask db migrate -m "Add/Update: Beschreibung"
   FLASK_APP=app.py flask db upgrade
   ```
   **WICHTIG**: Model-Import in `app.py` hinzufügen falls neues Model!
4. **Quality Checks**:
   ```bash
   cd backend && source venv/bin/activate && pytest && ruff check .
   cd frontend && npm test && npm run lint && npm run build
   ```
5. **Bei Erfolg**:
   - Änderungen mit dem security-review skill untersuchen und ggf. verändern
   - Git Commit: `feat: STORY-ID - Title` (mit Co-Authored-By: Claude)
   - PRD: `passes: true` setzen
   - Progress in `scripts/ralph/feature/progress.txt` dokumentieren

## Regeln
- Eine Story pro Iteration, alle Criteria erfüllen
- Tests ~20% Aufwand, Implementation priorisieren
- Autonom handeln, nicht nachfragen

## Status (PFLICHT am Ende jeder Antwort)

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
TASKS_COMPLETED_THIS_LOOP: <n>
FILES_MODIFIED: <n>
TESTS_STATUS: PASSING|FAILING|NOT_RUN
WORK_TYPE: IMPLEMENTATION|TESTING|DOCUMENTATION
EXIT_SIGNAL: false|true
RECOMMENDATION: <nächster Schritt>
---END_RALPH_STATUS---
```

**EXIT_SIGNAL: true** nur wenn ALLE Stories `passes: true` und Tests grün.

Beginne jetzt!
