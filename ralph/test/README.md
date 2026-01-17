# RALF Test Mode

RALF Test Mode ist ein explorativer QA-Agent, der MCP Playwright nutzt um neu implementierte Features im Browser zu testen.

## Features

- **MCP Playwright Integration**: Browser-Automation direkt aus Claude Code
- **Commit-basierte Feature-Erkennung**: Automatisch Features aus Git-History extrahieren
- **Explorative Tests**: Claude erkundet die UI frei und sucht nach Bugs
- **Strukturierte Reports**: JSON-Output für Weiterverarbeitung an Debug/Feature Ralph
- **Loop-basierte Ausführung**: Testet alle Features nacheinander mit Circuit Breaker

## Voraussetzungen

### 1. MCP Playwright Server

```bash
# MCP Playwright zu Claude Code hinzufügen (offizielles Paket)
claude mcp add playwright -- npx @playwright/mcp@latest

# Prüfen ob konfiguriert
claude mcp list
```

### 2. Frontend Server

Der Frontend-Server muss laufen:
```bash
cd frontend && npm run dev
```

## Quick Start

```bash
cd ralph/test

# Standard-Ausführung (testet alle Commits seit main)
./ralph.sh

# Mit spezifischem Base-Branch
./ralph.sh --base develop

# Browser sichtbar (nicht headless)
./ralph.sh --headed

# Status prüfen
./ralph.sh --status

# Finalen Report generieren
./ralph.sh --report

# Reset und neu starten
./ralph.sh --reset
```

## Dateistruktur

```
ralph/test/
├── ralph.sh              # Haupt-Script
├── config.sh             # Konfiguration
├── prompt.md             # Claude Anweisungen
├── features.json         # Geladene Features (generiert)
├── manual_features.json  # Manuelle Feature-Override (optional)
├── lib/
│   ├── commit_analyzer.sh    # Git-Analyse
│   └── test_reporter.sh      # Report-Generierung
├── logs/
│   ├── status.json           # Aktueller Status
│   └── test_output_*.log     # Claude Outputs
└── reports/
    ├── test_*.json           # Einzelne Test-Ergebnisse
    ├── final_report.json     # Gesamtreport
    └── screenshots/          # Screenshots von Tests
```

## Feature-Quellen

### Automatisch (Default)

Features werden aus der Git-History extrahiert:
```bash
# Alle Commits seit main
./ralph.sh --base main

# Alle Commits seit develop
./ralph.sh --base develop
```

### Manuell (Override)

Erstelle `manual_features.json` für spezifische Tests:

```json
{
  "features": [
    {
      "id": "MANUAL-001",
      "commit_hash": "abc1234",
      "message": "Dashboard neu gestaltet",
      "scope": "frontend",
      "type": "feature",
      "changed_files": ["frontend/src/pages/Dashboard.vue"],
      "tested": false,
      "test_result": null
    }
  ]
}
```

Manuelle Features haben **Priorität** über automatisch erkannte.

## Output Format

### Test-Ergebnis (pro Feature)

```json
{
  "feature_id": "COMMIT-0",
  "tested_at": "2025-01-14T10:00:00Z",
  "has_bugs": true,
  "bugs": [
    {
      "id": "BUG-001",
      "severity": "major",
      "title": "Button reagiert nicht",
      "description": "...",
      "steps_to_reproduce": ["..."],
      "affected_component": "Dashboard.vue"
    }
  ],
  "suggestions": [
    {
      "id": "SUG-001",
      "type": "ux",
      "title": "Loading-Indicator fehlt",
      "priority": "medium"
    }
  ]
}
```

### Final Report

Der finale Report enthält zwei spezielle Sektionen:

```json
{
  "for_debug_ralph": {
    "bugs_to_fix": [/* Critical und Major Bugs */]
  },
  "for_feature_ralph": {
    "features_to_add": [/* High-Priority Suggestions */]
  }
}
```

## Workflow Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    RALF Ecosystem                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Feature Ralph ──▶ Implementiert Features                   │
│        │                                                     │
│        ▼                                                     │
│  Test Ralph ──▶ Testet Features mit MCP Playwright          │
│        │                                                     │
│        ├──▶ Bugs gefunden? ──▶ Debug Ralph                  │
│        │                                                     │
│        └──▶ Feature-Ideen? ──▶ Feature Ralph                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Konfiguration

Alle Einstellungen in `config.sh`:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `COMMIT_RANGE_BASE` | main | Base-Branch für Commit-Range |
| `FRONTEND_URL` | http://localhost:3000 | Frontend URL |
| `HEADLESS` | true | Browser im Headless-Modus |
| `VIEWPORT_SIZE` | 1280x720 | Browser-Viewport |
| `MCP_CAPABILITIES` | testing | Playwright-Capabilities (testing, vision, pdf, tracing) |
| `TIMEOUT_MINUTES` | 10 | Claude Timeout |
| `MAX_TEST_ITERATIONS` | 10 | Max Anzahl Test-Loops |
| `SAVE_TRACE` | false | Playwright-Trace speichern |
| `SAVE_VIDEO` | false | Video der Session speichern |

### MCP Playwright CLI-Optionen

Der MCP Server unterstützt viele Optionen:

```bash
# Mit Test-Assertions
npx @playwright/mcp@latest --caps=testing

# Mit Trace-Recording
npx @playwright/mcp@latest --save-trace --caps=tracing

# Mit spezifischem Browser
npx @playwright/mcp@latest --browser=firefox

# Mit Device-Emulation
npx @playwright/mcp@latest --device="iPhone 15"

# Headless deaktivieren
npx @playwright/mcp@latest --headless=false
```

## MCP Playwright Tools

Das offizielle `@playwright/mcp` Paket (Microsoft) bietet Browser-Automation.
Docs: https://github.com/microsoft/playwright-mcp

### Wichtig: Snapshot vor Screenshot!

`browser_snapshot` liefert strukturierte Accessibility-Daten für LLM-Interaktion.
`browser_take_screenshot` nur für Dokumentation/Reports verwenden.

### Verfügbare Tools

**Navigation & Inspektion:**
- `browser_navigate` - URL aufrufen
- `browser_snapshot` - Accessibility-Snapshot (BEVORZUGT!)
- `browser_take_screenshot` - Screenshot speichern
- `browser_console_messages` - Console-Errors abrufen
- `browser_network_requests` - API-Requests prüfen

**Interaktion:**
- `browser_click` - Element klicken
- `browser_type` - Text eingeben
- `browser_fill_form` - Formular ausfüllen
- `browser_select_option` - Dropdown wählen
- `browser_press_key` - Taste drücken

**Test-Assertions (--caps=testing):**
- `browser_verify_element_visible`
- `browser_verify_text_visible`
- `browser_verify_value`

**Kontrolle:**
- `browser_wait_for` - Warten auf Text/Zeit
- `browser_resize` - Viewport ändern
- `browser_close` - Browser schließen

## Troubleshooting

### MCP Playwright nicht gefunden

```bash
# Neu hinzufügen (offizielles Paket)
claude mcp add playwright -- npx @playwright/mcp@latest

# Prüfen ob verbunden
claude mcp list
```

### Frontend nicht erreichbar

```bash
# Frontend starten
cd frontend && npm run dev

# Oder andere URL verwenden
./ralph.sh --url http://localhost:5173
```

### Keine Features gefunden

```bash
# Prüfe ob Commits vorhanden
git log --oneline main..HEAD

# Oder manuell Features definieren
# Erstelle manual_features.json
```

## Bug-Kategorien

| Severity | Beschreibung | Aktion |
|----------|--------------|--------|
| **critical** | App crasht, Datenverlust | Sofort an Debug Ralph |
| **major** | Feature funktioniert nicht | An Debug Ralph |
| **minor** | Kosmetische Fehler | Backlog |
| **trivial** | Typos, kleine Inkonsistenzen | Optional |

## Suggestion-Typen

| Type | Beschreibung |
|------|--------------|
| **ux** | User Experience Verbesserungen |
| **performance** | Performance-Optimierungen |
| **accessibility** | Barrierefreiheit |
| **feature** | Neue Feature-Ideen |
