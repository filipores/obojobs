# RALPH Feature Mode

RALPH (Rapid Automated Lean Feature-builder) is an autonomous development agent that automatically implements User Stories from a PRD (Product Requirements Document).

## Features

- **Rate Limiting**: Limits API calls to 50/hour (configurable)
- **Circuit Breaker**: Detects and automatically stops infinite loops
- **Timeout Protection**: Prevents hanging Claude sessions (default: 15 min)
- **Status Reporting**: Structured status reports from Claude
- **Live Monitoring**: Real-time dashboard in terminal
- **Structured Logging**: Comprehensive logging for debugging

## Quick Start

```bash
# Start RALPH
cd ralph/feature
./ralph.sh

# With live monitor (separate terminal)
./monitor.sh

# Check status
./ralph.sh --status

# Reset circuit breaker
./ralph.sh --reset-circuit
```

## Configuration

All settings in `config.sh`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CALLS_PER_HOUR` | 50 | Maximum API calls per hour |
| `TIMEOUT_MINUTES` | 15 | Claude execution timeout |
| `CB_NO_PROGRESS_THRESHOLD` | 3 | Loops without progress until circuit opens |
| `CB_SAME_ERROR_THRESHOLD` | 5 | Same error until circuit opens |

## File Structure

```
ralph/feature/
├── ralph.sh           # Main script
├── monitor.sh         # Live monitor
├── config.sh          # Configuration
├── prompt.md          # Instructions for Claude
├── tasks.json         # User Stories
├── progress.txt       # Progress documentation
├── lib/
│   ├── date_utils.sh      # Date functions
│   ├── logger.sh          # Logging functions
│   ├── rate_limiter.sh    # Rate Limiting
│   ├── circuit_breaker.sh # Stuck Detection
│   └── response_analyzer.sh # Output analysis
└── logs/
    ├── ralph.log          # Execution log
    ├── status.json        # Current status
    ├── history.json       # Last 50 iterations
    └── claude_output_*.log # Claude outputs
```

## PRD Format

The `tasks.json` contains User Stories in format:

```json
{
  "project": "obojobs",
  "branchName": "ralph/feature-name",
  "description": "Feature description",
  "userStories": [
    {
      "id": "FEATURE-001",
      "title": "Story Title",
      "description": "What should be implemented",
      "acceptanceCriteria": [
        "Criterion 1",
        "Criterion 2"
      ],
      "priority": 1,
      "passes": false,
      "notes": "Additional notes"
    }
  ]
}
```

## Status Reporting (RALPH_STATUS)

Claude outputs a status block at the end of each response:

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

The Circuit Breaker has three states:

| State | Meaning |
|-------|---------|
| **CLOSED** | Normal, work continues |
| **HALF_OPEN** | Monitoring, 2 loops without progress |
| **OPEN** | Stopped, manual intervention required |

The circuit opens when:
- 3+ loops without file changes
- 5+ loops with same error
- Same story 5x without `passes: true`

## Troubleshooting

### RALPH stops with "Circuit Breaker Open"

```bash
# Check status
./ralph.sh --circuit-status

# View logs
tail -50 logs/ralph.log

# Check last Claude output
ls -lt logs/claude_output_*.log | head -1 | xargs cat

# Reset circuit
./ralph.sh --reset-circuit
```

### Rate Limit Reached

RALPH automatically waits for the next hour reset. You can:
- Wait (continues automatically)
- Cancel and start later
- Increase `MAX_CALLS_PER_HOUR` in config.sh

### Claude Hangs/Timeout

- Increase timeout in config.sh: `TIMEOUT_MINUTES=30`
- Via CLI: `./ralph.sh --timeout 30`

### Story Not Marked as "passes"

Claude must:
1. Have all tests green
2. Set `passes: true` in tasks.json
3. Have `EXIT_SIGNAL: true` in status block

Check if all Acceptance Criteria are fulfilled.

## Monitoring

### Live Monitor (recommended)

```bash
# In separate terminal
./monitor.sh

# With different refresh interval (default: 5s)
./monitor.sh 10
```

### Simple Alternative

```bash
# Watch status in real-time
watch -n 5 'cat logs/status.json | jq .'

# Follow logs
tail -f logs/ralph.log
```

## CLI Options

```
./ralph.sh [OPTIONS]

Options:
  -h, --help          Show help
  -c, --calls NUM     Max API calls per hour
  -t, --timeout MIN   Claude timeout in minutes
  -v, --verbose       Detailed output
  --status            Show current status
  --reset-circuit     Reset circuit breaker
  --circuit-status    Show circuit breaker status
```

## Tips for Effective Use

1. **Formulate PRD clearly**: The clearer the Acceptance Criteria, the better the result
2. **Use monitor**: Live monitoring helps with troubleshooting
3. **Check logs**: Always check `logs/ralph.log` and Claude outputs on problems
4. **Small stories**: Many small stories are better than few large ones
5. **Tests important**: RALPH only sets `passes: true` with green tests
