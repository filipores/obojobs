# QA Check - Schnelle Validierung

Führe diese Quality Checks aus und berichte das Ergebnis:

## Backend
```bash
cd backend && source venv/bin/activate && pytest --tb=short -q
cd backend && source venv/bin/activate && ruff check . --select=E,F
cd backend && source venv/bin/activate && FLASK_APP=app.py flask db current 2>/dev/null | grep -q "(head)" && echo "DB_MIGRATIONS: UP_TO_DATE" || echo "DB_MIGRATIONS: PENDING"
```

## Frontend
```bash
cd frontend && npm test -- --watchAll=false
cd frontend && npm run lint
cd frontend && npm run build
```

## Ausgabe-Format (WICHTIG)

```
---QA_RESULT---
PYTEST: PASS|FAIL|SKIP
RUFF: PASS|FAIL|SKIP
DB_MIGRATIONS: UP_TO_DATE|PENDING
NPM_TEST: PASS|FAIL|SKIP
NPM_LINT: PASS|FAIL|SKIP
NPM_BUILD: PASS|FAIL|SKIP
SUMMARY: ALL_PASS|HAS_FAILURES
FAILURES: <komma-separierte Liste der fehlgeschlagenen Checks, oder "none">
---END_QA_RESULT---
```

Führe nur die Checks aus, keine Code-Änderungen!
