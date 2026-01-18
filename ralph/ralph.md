# RALPH - Autonomous Development Agent Framework

RALPH (Rapid Automated Lean Feature-builder) is a framework for autonomous development agents that use Claude Code to perform various tasks in the software development process.

## Concept

Ralph orchestrates Claude Code sessions in different modes. Each mode has:
- A **Shell script** (`ralph.sh`) that runs the main loop
- A **Prompt file** (`prompt.md`) with instructions for Claude
- A **Config file** (`config.sh`) with configuration options
- A **Data file** (JSON) with items to process

Ralph calls Claude Code in a loop, analyzes responses, and decides whether to continue or stop.

## Mode Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     RALPH Ecosystem                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  feature/ ──▶ Implements User Stories from tasks.json             │
│      │                                                            │
│      ▼                                                            │
│  test/ ──▶ Tests Features with MCP Playwright (Browser)          │
│      │                                                            │
│      ├──▶ Bugs found? ──▶ debug/                                 │
│      │                                                            │
│      └──▶ Suggestions? ──▶ feature/ (new stories)                │
│                                                                   │
│  explore/ ──▶ Exploratory Testing of the entire app              │
│      │                                                            │
│      └──▶ Bugs + Suggestions ──▶ debug/ / feature/               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Feature Mode (`ralph/feature/`)
Implements User Stories from a PRD (Product Requirements Document).

**Files:**
- `tasks.json` - User Stories with `passes: false/true`
- `logs/progress.txt` - Progress documentation
- `prompt.md` - Implementation instructions

**Workflow:**
1. Read story with lowest `priority` and `passes: false`
2. Implement all Acceptance Criteria
3. Run Quality Checks (tests, linting, build)
4. Git commit and set `passes: true`

### Debug Mode (`ralph/debug/`)
Fixes bugs from a bug database.

**Files:**
- `tasks.json` - Bugs with `fixed: false/true`
- `prompt.md` - Debug instructions

**Workflow:**
1. Read bug with `fixed: false`
2. Analyze root cause
3. Implement minimal fix
4. Test and set `fixed: true`

### Test Mode (`ralph/test/`)
Tests features through exploratory UI tests with MCP Playwright.

**Files:**
- `tasks.json` - Features extracted from Git history
- `manual_tasks.json` - Optional: Manual feature list
- `prompt.md` - Test instructions

**Workflow:**
1. Extract features from Git commits
2. Start browser via MCP Playwright
3. Test each feature exploratively
4. Document bugs and suggestions

**Prerequisite:** MCP Playwright Server (`claude mcp add playwright -- npx @playwright/mcp@latest`)

### Explore Mode (`ralph/explore/`)
Exploratory testing of the entire application.

**Files:**
- `tasks.json` - Found bugs
- `sugg.json` - Feature suggestions
- `session.json` - Session state (visited pages, etc.)

**Workflow:**
1. Navigate through the app
2. Test interactions and edge cases
3. Document bugs and suggestions
4. Prioritize by severity

## Architecture

```
ralph/
├── ralph.md              # This documentation
├── setup-ubuntu.sh       # Setup script for Ubuntu
├── lib/                  # Shared Libraries
│   ├── circuit_breaker.sh    # Stuck Detection
│   ├── colors.sh             # Terminal colors
│   ├── context_builder.sh    # Token-optimized context
│   ├── date_utils.sh         # Date functions
│   ├── logger.sh             # Structured logging + status
│   └── monitor.sh            # Generic live monitor (all modes)
├── feature/              # Feature Mode
│   ├── ralph.sh              # Main script
│   ├── config.sh             # Configuration
│   ├── prompt.md             # Claude instructions
│   ├── tasks.json            # User Stories
│   ├── lib/
│   │   ├── rate_limiter.sh   # Rate Limiting
│   │   └── response_analyzer.sh
│   └── logs/                 # Runtime data
│       ├── ralph.log
│       ├── status.json
│       ├── progress.txt
│       └── .circuit_breaker_state
├── debug/                # Debug Mode
│   ├── ralph.sh
│   ├── config.sh
│   ├── prompt.md
│   └── tasks.json
├── test/                 # Test Mode
│   ├── ralph.sh
│   ├── config.sh
│   ├── prompt.md
│   ├── tasks.json
│   └── lib/
│       ├── commit_analyzer.sh
│       └── test_reporter.sh
└── explore/              # Explore Mode
    ├── ralph.sh
    ├── config.sh
    ├── prompt.md
    ├── tasks.json
    ├── sugg.json
    ├── session.json
    └── lib/
        └── explorer.sh
```

## Shared Libraries

### Circuit Breaker (`lib/circuit_breaker.sh`)
Detects and automatically stops infinite loops.

**States:**
| State | Meaning |
|-------|---------|
| `CLOSED` | Normal, work continues |
| `HALF_OPEN` | Monitoring, 2 loops without progress |
| `OPEN` | Stopped, manual intervention required |

**Triggers for OPEN:**
- 3+ loops without file changes (`CB_NO_PROGRESS_THRESHOLD`)
- 5+ loops with same error (`CB_SAME_ERROR_THRESHOLD`)
- Same story 5x without `passes: true`

### Rate Limiter (`feature/lib/rate_limiter.sh`)
Limits API calls to configurable number per hour.

### Logger (`lib/logger.sh`)
Structured logging with colors and status JSON for monitoring.

### Context Builder (`lib/context_builder.sh`)
Pre-calculates relevant files for a story/bug to save tokens.

### Monitor (`lib/monitor.sh`)
Generic live monitor for all Ralph modes.

**Usage:**
```bash
# Auto-detect active mode
./lib/monitor.sh

# Specific mode
./lib/monitor.sh feature
./lib/monitor.sh debug 3     # with 3s refresh

# All modes simultaneously
./lib/monitor.sh --all
```

**Unified Status JSON Format:**
All modes write `logs/status.json` in the same format:

```json
{
  "mode": "feature|debug|test|explore",
  "status": "running|complete|error|timeout|circuit_open|interrupted",
  "loop": 5,
  "current_task": "Story-ID / Bug-ID / Feature-Name",
  "progress": {
    "completed": 3,
    "total": 10
  },
  "started_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  // Mode-specific extras:
  "calls_made_this_hour": 25,    // Feature
  "model": "claude-opus-4",         // Debug
  "bugs_found": 3                // Test/Explore
}
```

## Status Reporting

Every Claude response MUST contain a status block:

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
TASKS_COMPLETED_THIS_LOOP: <n>
FILES_MODIFIED: <n>
TESTS_STATUS: PASSING|FAILING|NOT_RUN
WORK_TYPE: IMPLEMENTATION|TESTING|DOCUMENTATION|REFACTORING
EXIT_SIGNAL: false|true
RECOMMENDATION: <next step>
---END_RALPH_STATUS---
```

**EXIT_SIGNAL: true** cleanly ends the Ralph session.

## Configuration

Important variables in `config.sh`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CALLS_PER_HOUR` | 50 | Rate limit |
| `TIMEOUT_MINUTES` | 15 | Claude timeout |
| `CB_NO_PROGRESS_THRESHOLD` | 3 | Loops without progress |
| `CB_SAME_ERROR_THRESHOLD` | 5 | Same errors |
| `CLAUDE_MODEL` | claude-opus-4-5-20251101 | Claude model |
| `CLAUDE_ALLOWED_TOOLS` | Write,Edit,Read,... | Allowed tools |

## CLI Options

All Ralph modes support similar options:

```bash
./ralph.sh [OPTIONS]

Options:
  -h, --help          Show help
  -c, --calls NUM     Max API calls per hour
  -t, --timeout MIN   Claude timeout in minutes
  --status            Show current status
  --reset-circuit     Reset circuit breaker
  --circuit-status    Show circuit breaker status
```

## For Claude Agents

### Important Rules

1. **Status block is mandatory**: Every response MUST end with a status block
2. **One task per iteration**: Complete one story/bug fully
3. **Quality checks**: Tests, linting, build must be green
4. **Act autonomously**: Don't ask questions, make decisions independently
5. **Document**: Record progress in corresponding files
6. **Follow AGENTS.md**: Adhere to project conventions

### Exit Signals

Set `EXIT_SIGNAL: true` only when:
- All stories/bugs completed (`passes: true` / `fixed: true`)
- All tests green
- Build successful

### Handling Errors

1. On test failures: Implement fix, don't just skip
2. On build errors: Find root cause and resolve
3. On uncertainties: Note in `RECOMMENDATION` field

### Token Optimization

- Context Builder provides relevant files upfront
- Only read necessary files
- Keep status block compact

## Monitoring

```bash
# Live monitor for all modes (separate terminal)
./lib/monitor.sh              # Auto-detect active mode
./lib/monitor.sh feature      # Feature mode
./lib/monitor.sh debug        # Debug mode
./lib/monitor.sh test         # Test mode
./lib/monitor.sh explore      # Explore mode
./lib/monitor.sh --all        # All modes simultaneously

# Check status
./feature/ralph.sh --status
./debug/ralph.sh --status

# Follow logs
tail -f feature/logs/ralph.log
tail -f debug/logs/ralph.log

# Circuit breaker status
./feature/ralph.sh --circuit-status
```

## Troubleshooting

### Circuit Breaker Opened
```bash
./ralph.sh --circuit-status    # Check reason
tail -50 logs/ralph.log        # View logs
./ralph.sh --reset-circuit     # Reset
```

### Rate Limit Reached
Ralph automatically waits for reset. Alternatively:
- Increase `MAX_CALLS_PER_HOUR`
- Cancel and start later

### Claude Hangs/Timeout
- Increase `TIMEOUT_MINUTES`: `./ralph.sh --timeout 30`
- Simplify prompt

---

*This documentation is used by Ralph agents to understand the framework context.*
