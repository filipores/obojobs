# RALF Debug Mode

Fixe Bugs aus `ralph/debug/bugs.json` systematisch.

## Dateien
- **Bugs**: `ralph/debug/bugs.json` - Bugs mit `fixed: false`
- **Kontext**: `AGENTS.md` - Projekt-Konventionen
- **Learnings**: `ralph/debug/learnings.md` - Erkenntnisse dokumentieren

## Workflow pro Bug

1. **Bug verstehen**: Lies `stepsToReproduce`, `rootCause`, `affectedFiles`, `suggestedFix`
2. **Code analysieren**: Verifiziere Root Cause in betroffenen Dateien
3. **Fix implementieren**: Minimale Änderung, Konventionen aus AGENTS.md befolgen
4. **Quality Checks**:
   ```bash
   cd backend && source venv/bin/activate && pytest && ruff check .
   cd frontend && npm test && npm run lint && npm run build
   ```
5. **Bei Erfolg**:
   - Git Commit: `fix: BUG-ID - Title` (mit Co-Authored-By: Claude)
   - bugs.json: `fixed: true` setzen
   - Learnings in `learnings.md` dokumentieren

## Regeln
- Ein Bug pro Iteration, Root Cause verstehen
- Minimal invasive Fixes, Tests müssen grün sein
- Autonom handeln

## Status (PFLICHT am Ende jeder Antwort)

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
BUG_ID: <bug_id>
FIX_SUCCESSFUL: true|false
TESTS_STATUS: PASSING|FAILING|NOT_RUN
FILES_MODIFIED: <n>
EXIT_SIGNAL: false|true
RECOMMENDATION: <nächster Schritt>
---END_RALPH_STATUS---
```

**EXIT_SIGNAL: true** nur wenn ALLE Bugs `fixed: true` und Tests grün.

Beginne mit dem nächsten offenen Bug!
