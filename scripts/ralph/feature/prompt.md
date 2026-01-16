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
   - Änderungen mit dem security-review skill untersuchen und ggf. verändern
5. **AGENTS.md updaten** wenn du wiederverwertbare patterns erkennst (siehe unten): 
6. **Bei Erfolg**:
   - Git Commit: `feat: STORY-ID - Title` (mit Co-Authored-By: Claude)
   - PRD: `passes: true` setzen
   - Progress in `scripts/ralph/feature/progress.txt` dokumentieren (siehe unten)

## Regeln
- Eine Story pro Iteration, alle Criteria erfüllen
- Tests ~20% Aufwand, Implementation priorisieren
- Autonom handeln, nicht nachfragen

## Progess-Format

An progress.txt ANHÄNGEN (niemals ersetzen, immer anhängen):
```
## [Datum/Uhrzeit] - [Story-ID]
- Was wurde implementiert
- Geänderte Dateien
- **Erkenntnisse für zukünftige Iterationen:**
  - Entdeckte Muster (z.B. "diese Codebase verwendet X für Y")
  - Aufgetretene Stolperfallen (z.B. "nicht vergessen, Z zu aktualisieren wenn W geändert wird")
  - Nützlicher Kontext (z.B. "das Evaluierungs-Panel ist in Komponente X")
---
```

## AGENTS.md-Dateien aktualisieren

Vor dem Commit prüfen, ob bearbeitete Dateien Erkenntnisse haben, die es wert sind, in nahegelegenen AGENTS.md-Dateien festgehalten zu werden:

1. **Verzeichnisse mit bearbeiteten Dateien identifizieren** - Schauen, welche Verzeichnisse du geändert hast
2. **Nach vorhandenen AGENTS.md suchen** - Nach AGENTS.md in diesen Verzeichnissen oder übergeordneten Verzeichnissen suchen
3. **Wertvolle Erkenntnisse hinzufügen** - Wenn du etwas entdeckt hast, das zukünftige Entwickler/Agenten wissen sollten:
   - API-Muster oder Konventionen spezifisch für dieses Modul
   - Stolperfallen oder nicht-offensichtliche Anforderungen
   - Abhängigkeiten zwischen Dateien
   - Testansätze für diesen Bereich
   - Konfigurations- oder Umgebungsanforderungen

**NICHT hinzufügen:**
- Story-spezifische Implementierungsdetails
- Temporäre Debugging-Notizen
- Informationen, die bereits in progress.txt stehen

AGENTS.md nur aktualisieren, wenn du **wirklich wiederverwendbares Wissen** hast, das bei zukünftiger Arbeit in diesem Verzeichnis helfen würde.

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
