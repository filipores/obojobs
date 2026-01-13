# RALF Feature Mode

RALF (Rapid Automated Lean Feature-builder) ist ein autonomer Entwicklungsagent, der User Stories aus einer PRD (Product Requirements Document) automatisch implementiert.

## Features

- **Rate Limiting**: Begrenzt API-Calls auf 50/Stunde (konfigurierbar)
- **Circuit Breaker**: Erkennt und stoppt Infinite Loops automatisch
- **Timeout Protection**: Verhindert hängende Claude-Sessions (default: 15 Min)
- **Status Reporting**: Strukturierte Statusberichte von Claude
- **Live Monitoring**: Echtzeit-Dashboard im Terminal
- **Structured Logging**: Umfassendes Logging für Debugging

## Quick Start

```bash
# RALF starten
cd scripts/ralph/feature
./ralph.sh

# Mit Live-Monitor (separates Terminal)
./monitor.sh

# Status prüfen
./ralph.sh --status

# Circuit Breaker zurücksetzen
./ralph.sh --reset-circuit
```

## Konfiguration

Alle Einstellungen in `config.sh`:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `MAX_CALLS_PER_HOUR` | 50 | Maximale API-Calls pro Stunde |
| `TIMEOUT_MINUTES` | 15 | Claude-Ausführungs-Timeout |
| `CB_NO_PROGRESS_THRESHOLD` | 3 | Loops ohne Fortschritt bis Circuit öffnet |
| `CB_SAME_ERROR_THRESHOLD` | 5 | Gleicher Fehler bis Circuit öffnet |

## Dateistruktur

```
scripts/ralph/feature/
├── ralph.sh           # Haupt-Script
├── monitor.sh         # Live-Monitor
├── config.sh          # Konfiguration
├── prompt.md          # Anweisungen für Claude
├── prd.json           # User Stories
├── progress.txt       # Fortschrittsdokumentation
├── lib/
│   ├── date_utils.sh      # Datum-Funktionen
│   ├── logger.sh          # Logging-Funktionen
│   ├── rate_limiter.sh    # Rate Limiting
│   ├── circuit_breaker.sh # Stuck Detection
│   └── response_analyzer.sh # Output-Analyse
└── logs/
    ├── ralph.log          # Ausführungslog
    ├── status.json        # Aktueller Status
    ├── history.json       # Letzte 50 Iterationen
    └── claude_output_*.log # Claude-Outputs
```

## PRD Format

Die `prd.json` enthält User Stories im Format:

```json
{
  "project": "obojobs",
  "branchName": "ralph/feature-name",
  "description": "Feature-Beschreibung",
  "userStories": [
    {
      "id": "FEATURE-001",
      "title": "Story Titel",
      "description": "Was implementiert werden soll",
      "acceptanceCriteria": [
        "Kriterium 1",
        "Kriterium 2"
      ],
      "priority": 1,
      "passes": false,
      "notes": "Zusätzliche Hinweise"
    }
  ]
}
```

## Status Reporting (RALPH_STATUS)

Claude gibt am Ende jeder Antwort einen Status-Block aus:

```
---RALPH_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: <number>
FILES_MODIFIED: <number>
TESTS_STATUS: PASSING | FAILING | NOT_RUN
WORK_TYPE: IMPLEMENTATION | TESTING | DOCUMENTATION | REFACTORING
EXIT_SIGNAL: false | true
RECOMMENDATION: <one line summary>
---END_RALPH_STATUS---
```

## Circuit Breaker

Der Circuit Breaker hat drei Zustände:

| Zustand | Bedeutung |
|---------|-----------|
| **CLOSED** | Normal, Arbeit wird fortgesetzt |
| **HALF_OPEN** | Monitoring, 2 Loops ohne Fortschritt |
| **OPEN** | Gestoppt, manuelle Intervention nötig |

Der Circuit öffnet wenn:
- 3+ Loops ohne Dateiänderungen
- 5+ Loops mit gleichem Fehler
- Gleiche Story 5x ohne `passes: true`

## Troubleshooting

### RALF stoppt mit "Circuit Breaker Open"

```bash
# Status prüfen
./ralph.sh --circuit-status

# Logs ansehen
tail -50 logs/ralph.log

# Letzten Claude-Output prüfen
ls -lt logs/claude_output_*.log | head -1 | xargs cat

# Circuit zurücksetzen
./ralph.sh --reset-circuit
```

### Rate Limit erreicht

RALF wartet automatisch auf den nächsten Stunden-Reset. Du kannst:
- Warten (automatisch fortsetzen)
- Abbrechen und später starten
- `MAX_CALLS_PER_HOUR` in config.sh erhöhen

### Claude hängt/Timeout

- Timeout in config.sh erhöhen: `TIMEOUT_MINUTES=30`
- Via CLI: `./ralph.sh --timeout 30`

### Story nicht als "passes" markiert

Claude muss:
1. Alle Tests grün haben
2. `passes: true` in prd.json setzen
3. `EXIT_SIGNAL: true` im Status-Block

Prüfe ob alle Acceptance Criteria erfüllt sind.

## Monitoring

### Live-Monitor (empfohlen)

```bash
# In separatem Terminal
./monitor.sh

# Mit anderem Refresh-Interval (default: 5s)
./monitor.sh 10
```

### Einfache Alternative

```bash
# Status in Echtzeit beobachten
watch -n 5 'cat logs/status.json | jq .'

# Logs verfolgen
tail -f logs/ralph.log
```

## CLI Optionen

```
./ralph.sh [OPTIONS]

Optionen:
  -h, --help          Hilfe anzeigen
  -c, --calls NUM     Max API-Calls pro Stunde
  -t, --timeout MIN   Claude Timeout in Minuten
  -v, --verbose       Detaillierte Ausgabe
  --status            Aktuellen Status anzeigen
  --reset-circuit     Circuit Breaker zurücksetzen
  --circuit-status    Circuit Breaker Status anzeigen
```

## Tipps für effektive Nutzung

1. **PRD klar formulieren**: Je klarer die Acceptance Criteria, desto besser das Ergebnis
2. **Monitor nutzen**: Live-Überwachung hilft bei der Fehlersuche
3. **Logs prüfen**: Bei Problemen immer `logs/ralph.log` und Claude-Outputs checken
4. **Kleine Stories**: Lieber viele kleine Stories als wenige große
5. **Tests wichtig**: RALF setzt `passes: true` nur bei grünen Tests
