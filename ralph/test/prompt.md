# RALF Test Mode

Teste Features durch explorative UI-Tests mit MCP Playwright.

## Test-Setup: Dokumente und Login

**WICHTIG:** Vor dem Testen der Kernfunktionalität (CORE-* Features) muss das Test-Setup durchgeführt werden:

### Test-Dokumente (aus config.sh)
- **Lebenslauf:** `~/cv-ger.pdf`
- **Arbeitszeugnis:** `~/Filip Zeugnis.pdf`

### Setup-Ablauf (Feature SETUP-001)
1. Registriere neuen Test-User ODER logge bestehenden User ein
2. Navigiere zu `/documents`
3. Lade Lebenslauf hoch via `browser_file_upload` mit dem Pfad oben
4. Warte auf Upload-Bestätigung
5. Lade Arbeitszeugnis hoch
6. Warte auf Upload-Bestätigung
7. Erstelle mindestens ein Template unter `/templates`
8. Verifiziere: Beide Dokumente und Template sind vorhanden

### File Upload mit MCP Playwright
```
browser_file_upload mit paths: ["/Users/filipores/Documents/Bewerbungsunterlagen/Batch/cv-ger.pdf"]
```

Nach dem Setup können die CORE-* Features getestet werden.

## MCP Playwright Tools (Wichtigste)

| Kategorie | Tool | Beschreibung |
|-----------|------|--------------|
| **Navigation** | `browser_navigate` | URL aufrufen |
| | `browser_snapshot` | **BEVORZUGT!** Accessibility-Snapshot |
| | `browser_take_screenshot` | Screenshot (nur für Dokumentation) |
| **Interaktion** | `browser_click` | Element klicken (ref aus Snapshot) |
| | `browser_type` | Text eingeben |
| | `browser_fill_form` | Formular füllen |
| **Debugging** | `browser_console_messages` | **WICHTIG:** JS-Errors prüfen! |
| | `browser_network_requests` | API-Fehler (4xx, 5xx) prüfen |
| **Assertions** | `browser_verify_text_visible` | Text sichtbar? |
| **Kontrolle** | `browser_resize` | Viewport ändern (375x667 = Mobile) |
| | `browser_wait_for` | Auf Text/Zeit warten |

## Workflow

1. `browser_navigate` zur relevanten Seite
2. `browser_snapshot` für Struktur (NICHT Screenshot!)
3. `browser_console_messages` → Initiale Errors?
4. Interaktionen durchführen (click, type, fill_form)
5. Nach Aktionen: `browser_snapshot` + `browser_console_messages`
6. Bei Bugs: `browser_take_screenshot` als Beweis
7. `browser_resize` auf 375x667 für Mobile-Test

## Output (PFLICHT)

```json
---RALPH_TEST_RESULT---
{
  "feature_id": "COMMIT-X",
  "tested_at": "ISO-Timestamp",
  "has_bugs": true|false,
  "bugs": [{
    "id": "BUG-001",
    "severity": "critical|major|minor|trivial",
    "title": "Beschreibung",
    "steps_to_reproduce": ["Schritt 1", "Schritt 2"],
    "expected": "Erwartet",
    "actual": "Tatsächlich",
    "affected_component": "Component.vue"
  }],
  "suggestions": [{
    "id": "SUG-001",
    "type": "ux|performance|accessibility|feature",
    "title": "Beschreibung",
    "priority": "high|medium|low"
  }]
}
---END_RALPH_TEST_RESULT---
```

## Status (PFLICHT am Ende)

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
FEATURE_TESTED: <feature_id>
BUGS_FOUND: <n>
SUGGESTIONS_FOUND: <n>
SCREENSHOTS_TAKEN: <n>
EXIT_SIGNAL: false|true
RECOMMENDATION: <nächster Schritt>
---END_RALPH_STATUS---
```

Teste das übergebene Feature gründlich!
