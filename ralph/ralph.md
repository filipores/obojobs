# RALPH - Autonomous Development Agent Framework

RALPH (Rapid Automated Lean Feature-builder) ist ein Framework für autonome Entwicklungsagenten, die Claude Code nutzen um verschiedene Aufgaben im Software-Entwicklungsprozess auszuführen.

## Konzept

Ralph orchestriert Claude Code Sessions in verschiedenen Modi. Jeder Modus hat:
- Ein **Shell-Script** (`ralph.sh`) das die Hauptschleife ausführt
- Eine **Prompt-Datei** (`prompt.md`) mit Anweisungen für Claude
- Eine **Config-Datei** (`config.sh`) mit Konfigurationsoptionen
- Eine **Datendatei** (JSON) mit den zu bearbeitenden Items

Ralph ruft Claude Code in einer Schleife auf, analysiert die Responses und entscheidet ob fortgefahren oder gestoppt werden soll.

## Modi-Übersicht

```
┌──────────────────────────────────────────────────────────────────┐
│                     RALPH Ecosystem                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  feature/ ──▶ Implementiert User Stories aus prd.json            │
│      │                                                            │
│      ▼                                                            │
│  test/ ──▶ Testet Features mit MCP Playwright (Browser)          │
│      │                                                            │
│      ├──▶ Bugs gefunden? ──▶ debug/                              │
│      │                                                            │
│      └──▶ Suggestions? ──▶ feature/ (neue Stories)               │
│                                                                   │
│  explore/ ──▶ Exploratives Testen der gesamten App               │
│      │                                                            │
│      └──▶ Bugs + Suggestions ──▶ debug/ / feature/               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Feature Mode (`ralph/feature/`)
Implementiert User Stories aus einer PRD (Product Requirements Document).

**Dateien:**
- `prd.json` - User Stories mit `passes: false/true`
- `progress.txt` - Fortschrittsdokumentation
- `prompt.md` - Implementierungs-Anweisungen

**Workflow:**
1. Lies Story mit niedrigster `priority` und `passes: false`
2. Implementiere alle Acceptance Criteria
3. Führe Quality Checks aus (Tests, Linting, Build)
4. Git Commit und `passes: true` setzen

### Debug Mode (`ralph/debug/`)
Fixiert Bugs aus einer Bug-Datenbank.

**Dateien:**
- `bugs.json` - Bugs mit `fixed: false/true`
- `learnings.md` - Dokumentierte Erkenntnisse
- `prompt.md` - Debug-Anweisungen

**Workflow:**
1. Lies Bug mit `fixed: false`
2. Analysiere Root Cause
3. Implementiere minimalen Fix
4. Teste und setze `fixed: true`

### Test Mode (`ralph/test/`)
Testet Features durch explorative UI-Tests mit MCP Playwright.

**Dateien:**
- `features.json` - Aus Git-History extrahierte Features
- `manual_features.json` - Optional: Manuelle Feature-Liste
- `prompt.md` - Test-Anweisungen

**Workflow:**
1. Extrahiere Features aus Git-Commits
2. Starte Browser via MCP Playwright
3. Teste jedes Feature explorativ
4. Dokumentiere Bugs und Suggestions

**Voraussetzung:** MCP Playwright Server (`claude mcp add playwright -- npx @playwright/mcp@latest`)

### Explore Mode (`ralph/explore/`)
Exploratives Testen der gesamten Applikation.

**Dateien:**
- `bugs.json` - Gefundene Bugs
- `sugg.json` - Feature-Suggestions
- `session.json` - Session-State (besuchte Seiten, etc.)

**Workflow:**
1. Navigiere durch die App
2. Teste Interaktionen und Edge Cases
3. Dokumentiere Bugs und Suggestions
4. Priorisiere nach Severity

## Architektur

```
ralph/
├── ralph.md              # Diese Dokumentation
├── setup-ubuntu.sh       # Setup-Script für Ubuntu
├── lib/                  # Shared Libraries
│   ├── circuit_breaker.sh    # Stuck Detection
│   ├── context_builder.sh    # Token-optimierter Kontext
│   ├── date_utils.sh         # Datum-Funktionen
│   └── logger.sh             # Strukturiertes Logging
├── feature/              # Feature Mode
│   ├── ralph.sh              # Haupt-Script
│   ├── config.sh             # Konfiguration
│   ├── prompt.md             # Claude-Anweisungen
│   ├── prd.json              # User Stories
│   ├── progress.txt          # Fortschritt
│   ├── lib/
│   │   ├── rate_limiter.sh   # Rate Limiting
│   │   └── response_analyzer.sh
│   └── logs/
├── debug/                # Debug Mode
│   ├── ralph.sh
│   ├── config.sh
│   ├── prompt.md
│   ├── bugs.json
│   └── learnings.md
├── test/                 # Test Mode
│   ├── ralph.sh
│   ├── config.sh
│   ├── prompt.md
│   ├── features.json
│   └── lib/
│       ├── commit_analyzer.sh
│       └── test_reporter.sh
└── explore/              # Explore Mode
    ├── ralph.sh
    ├── config.sh
    ├── prompt.md
    ├── bugs.json
    ├── sugg.json
    ├── session.json
    └── lib/
        └── explorer.sh
```

## Shared Libraries

### Circuit Breaker (`lib/circuit_breaker.sh`)
Erkennt und stoppt Infinite Loops automatisch.

**Zustände:**
| Zustand | Bedeutung |
|---------|-----------|
| `CLOSED` | Normal, Arbeit wird fortgesetzt |
| `HALF_OPEN` | Monitoring, 2 Loops ohne Fortschritt |
| `OPEN` | Gestoppt, manuelle Intervention nötig |

**Trigger für OPEN:**
- 3+ Loops ohne Dateiänderungen (`CB_NO_PROGRESS_THRESHOLD`)
- 5+ Loops mit gleichem Fehler (`CB_SAME_ERROR_THRESHOLD`)
- Gleiche Story 5x ohne `passes: true`

### Rate Limiter (`feature/lib/rate_limiter.sh`)
Begrenzt API-Calls auf konfigurierbare Anzahl pro Stunde.

### Logger (`lib/logger.sh`)
Strukturiertes Logging mit Farben und Status-JSON für Monitoring.

### Context Builder (`lib/context_builder.sh`)
Berechnet relevante Dateien für eine Story/Bug vor, um Token zu sparen.

## Status Reporting

Jede Claude-Response MUSS einen Status-Block enthalten:

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
TASKS_COMPLETED_THIS_LOOP: <n>
FILES_MODIFIED: <n>
TESTS_STATUS: PASSING|FAILING|NOT_RUN
WORK_TYPE: IMPLEMENTATION|TESTING|DOCUMENTATION|REFACTORING
EXIT_SIGNAL: false|true
RECOMMENDATION: <nächster Schritt>
---END_RALPH_STATUS---
```

**EXIT_SIGNAL: true** beendet die Ralph-Session sauber.

## Konfiguration

Wichtige Variablen in `config.sh`:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `MAX_CALLS_PER_HOUR` | 50 | Rate Limit |
| `TIMEOUT_MINUTES` | 15 | Claude-Timeout |
| `CB_NO_PROGRESS_THRESHOLD` | 3 | Loops ohne Fortschritt |
| `CB_SAME_ERROR_THRESHOLD` | 5 | Gleiche Fehler |
| `CLAUDE_MODEL_IMPL` | claude-opus-4-5-20251101 | Claude Model |
| `CLAUDE_ALLOWED_TOOLS` | Write,Edit,Read,... | Erlaubte Tools |

## CLI Optionen

Alle Ralph-Modi unterstützen ähnliche Optionen:

```bash
./ralph.sh [OPTIONS]

Optionen:
  -h, --help          Hilfe anzeigen
  -c, --calls NUM     Max API-Calls pro Stunde
  -t, --timeout MIN   Claude Timeout in Minuten
  --status            Aktuellen Status anzeigen
  --reset-circuit     Circuit Breaker zurücksetzen
  --circuit-status    Circuit Breaker Status anzeigen
```

## Für Claude Agents

### Wichtige Regeln

1. **Status-Block ist Pflicht**: Jede Response MUSS mit einem Status-Block enden
2. **Eine Aufgabe pro Iteration**: Bearbeite eine Story/Bug vollständig
3. **Quality Checks**: Tests, Linting, Build müssen grün sein
4. **Autonom handeln**: Nicht nachfragen, eigenständig entscheiden
5. **Dokumentieren**: Progress in entsprechenden Dateien festhalten
6. **AGENTS.md beachten**: Projekt-Konventionen befolgen

### Exit Signals

Setze `EXIT_SIGNAL: true` nur wenn:
- Alle Stories/Bugs abgearbeitet (`passes: true` / `fixed: true`)
- Alle Tests grün
- Build erfolgreich

### Umgang mit Fehlern

1. Bei Test-Fehlern: Fix implementieren, nicht einfach überspringen
2. Bei Build-Fehlern: Root Cause finden und beheben
3. Bei Unklarheiten: Im `RECOMMENDATION` Feld notieren

### Token-Optimierung

- Context Builder liefert relevante Dateien vor
- Nur notwendige Dateien lesen
- Status-Block kompakt halten

## Monitoring

```bash
# Live-Monitor (separates Terminal)
./monitor.sh

# Status prüfen
./ralph.sh --status

# Logs verfolgen
tail -f logs/ralph.log

# Circuit Breaker Status
./ralph.sh --circuit-status
```

## Troubleshooting

### Circuit Breaker Opened
```bash
./ralph.sh --circuit-status    # Grund prüfen
tail -50 logs/ralph.log        # Logs ansehen
./ralph.sh --reset-circuit     # Zurücksetzen
```

### Rate Limit erreicht
Ralph wartet automatisch auf Reset. Alternativ:
- `MAX_CALLS_PER_HOUR` erhöhen
- Abbrechen und später starten

### Claude hängt/Timeout
- `TIMEOUT_MINUTES` erhöhen: `./ralph.sh --timeout 30`
- Prompt vereinfachen

---

*Diese Dokumentation wird von Ralph-Agenten genutzt um den Kontext des Frameworks zu verstehen.*
