# RALPH Test Mode

RALPH Test Mode is an exploratory QA agent that uses MCP Playwright to test newly implemented features in the browser.

## Features

- **MCP Playwright Integration**: Browser automation directly from Claude Code
- **Commit-based Feature Detection**: Automatically extract features from Git history
- **Exploratory Tests**: Claude freely explores the UI looking for bugs
- **Structured Reports**: JSON output for further processing by Debug/Feature Ralph
- **Loop-based Execution**: Tests all features sequentially with Circuit Breaker

## Prerequisites

### 1. MCP Playwright Server

```bash
# Add MCP Playwright to Claude Code (official package)
claude mcp add playwright -- npx @playwright/mcp@latest

# Check if configured
claude mcp list
```

### 2. Frontend Server

The frontend server must be running:
```bash
cd frontend && npm run dev
```

## Quick Start

```bash
cd ralph/test

# Standard execution (tests all commits since main)
./ralph.sh

# With specific base branch
./ralph.sh --base develop

# Browser visible (not headless)
./ralph.sh --headed

# Check status
./ralph.sh --status

# Generate final report
./ralph.sh --report

# Reset and start fresh
./ralph.sh --reset
```

## File Structure

```
ralph/test/
├── ralph.sh              # Main script
├── config.sh             # Configuration
├── prompt.md             # Claude instructions
├── tasks.json            # Loaded features (generated)
├── manual_tasks.json     # Manual feature override (optional)
├── lib/
│   ├── commit_analyzer.sh    # Git analysis
│   └── test_reporter.sh      # Report generation
├── logs/
│   ├── status.json           # Current status
│   └── test_output_*.log     # Claude outputs
└── reports/
    ├── test_*.json           # Individual test results
    ├── final_report.json     # Overall report
    └── screenshots/          # Screenshots from tests
```

## Feature Sources

### Automatic (Default)

Features are extracted from Git history:
```bash
# All commits since main
./ralph.sh --base main

# All commits since develop
./ralph.sh --base develop
```

### Manual (Override)

Create `manual_tasks.json` for specific tests:

```json
{
  "features": [
    {
      "id": "MANUAL-001",
      "commit_hash": "abc1234",
      "message": "Dashboard redesigned",
      "scope": "frontend",
      "type": "feature",
      "changed_files": ["frontend/src/pages/Dashboard.vue"],
      "tested": false,
      "test_result": null
    }
  ]
}
```

Manual features have **priority** over automatically detected ones.

## Output Format

### Test Result (per Feature)

```json
{
  "feature_id": "COMMIT-0",
  "tested_at": "2025-01-14T10:00:00Z",
  "has_bugs": true,
  "bugs": [
    {
      "id": "BUG-001",
      "severity": "major",
      "title": "Button not responding",
      "description": "...",
      "steps_to_reproduce": ["..."],
      "affected_component": "Dashboard.vue"
    }
  ],
  "suggestions": [
    {
      "id": "SUG-001",
      "type": "ux",
      "title": "Loading indicator missing",
      "priority": "medium"
    }
  ]
}
```

### Final Report

The final report contains two special sections:

```json
{
  "for_debug_ralph": {
    "bugs_to_fix": [/* Critical and Major Bugs */]
  },
  "for_feature_ralph": {
    "features_to_add": [/* High-Priority Suggestions */]
  }
}
```

## Workflow Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    RALPH Ecosystem                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Feature Ralph ──▶ Implements features                     │
│        │                                                    │
│        ▼                                                    │
│  Test Ralph ──▶ Tests features with MCP Playwright         │
│        │                                                    │
│        ├──▶ Bugs found? ──▶ Debug Ralph                    │
│        │                                                    │
│        └──▶ Feature ideas? ──▶ Feature Ralph               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

All settings in `config.sh`:

| Variable | Default | Description |
|----------|---------|-------------|
| `COMMIT_RANGE_BASE` | main | Base branch for commit range |
| `FRONTEND_URL` | http://localhost:3000 | Frontend URL |
| `HEADLESS` | true | Browser in headless mode |
| `VIEWPORT_SIZE` | 1280x720 | Browser viewport |
| `MCP_CAPABILITIES` | testing | Playwright capabilities (testing, vision, pdf, tracing) |
| `TIMEOUT_MINUTES` | 10 | Claude timeout |
| `MAX_ITERATIONS` | 10 | Max number of test loops |
| `SAVE_TRACE` | false | Save Playwright trace |
| `SAVE_VIDEO` | false | Save video of session |

### MCP Playwright CLI Options

The MCP server supports many options:

```bash
# With test assertions
npx @playwright/mcp@latest --caps=testing

# With trace recording
npx @playwright/mcp@latest --save-trace --caps=tracing

# With specific browser
npx @playwright/mcp@latest --browser=firefox

# With device emulation
npx @playwright/mcp@latest --device="iPhone 15"

# Disable headless
npx @playwright/mcp@latest --headless=false
```

## MCP Playwright Tools

The official `@playwright/mcp` package (Microsoft) provides browser automation.
Docs: https://github.com/microsoft/playwright-mcp

### Important: Snapshot before Screenshot!

`browser_snapshot` provides structured accessibility data for LLM interaction.
`browser_take_screenshot` only for documentation/reports.

### Available Tools

**Navigation & Inspection:**
- `browser_navigate` - Open URL
- `browser_snapshot` - Accessibility snapshot (PREFERRED!)
- `browser_take_screenshot` - Save screenshot
- `browser_console_messages` - Get console errors
- `browser_network_requests` - Check API requests

**Interaction:**
- `browser_click` - Click element
- `browser_type` - Enter text
- `browser_fill_form` - Fill form
- `browser_select_option` - Select dropdown
- `browser_press_key` - Press key

**Test Assertions (--caps=testing):**
- `browser_verify_element_visible`
- `browser_verify_text_visible`
- `browser_verify_value`

**Control:**
- `browser_wait_for` - Wait for text/time
- `browser_resize` - Change viewport
- `browser_close` - Close browser

## Troubleshooting

### MCP Playwright Not Found

```bash
# Add again (official package)
claude mcp add playwright -- npx @playwright/mcp@latest

# Check if connected
claude mcp list
```

### Frontend Not Reachable

```bash
# Start frontend
cd frontend && npm run dev

# Or use different URL
./ralph.sh --url http://localhost:5173
```

### No Features Found

```bash
# Check if commits exist
git log --oneline main..HEAD

# Or define features manually
# Create manual_tasks.json
```

## Bug Categories

| Severity | Description | Action |
|----------|-------------|--------|
| **critical** | App crashes, data loss | Immediately to Debug Ralph |
| **major** | Feature doesn't work | To Debug Ralph |
| **minor** | Cosmetic errors | Backlog |
| **trivial** | Typos, small inconsistencies | Optional |

## Suggestion Types

| Type | Description |
|------|-------------|
| **ux** | User Experience improvements |
| **performance** | Performance optimizations |
| **accessibility** | Accessibility |
| **feature** | New feature ideas |
