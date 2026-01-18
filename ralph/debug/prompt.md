# RALPH Debug Mode

Fix bugs from `ralph/debug/tasks.json` systematically.

## Files
- **Bugs**: `ralph/debug/tasks.json` - Bugs with `fixed: false`
- **Context**: `AGENTS.md` - Project conventions

## Workflow per Bug

1. **Understand bug**: Read `stepsToReproduce`, `rootCause`, `affectedFiles`, `suggestedFix`
2. **Analyze code**: Verify root cause in affected files
3. **Implement fix**: Minimal change, follow conventions from AGENTS.md
4. **Quality Checks**:
   ```bash
   cd backend && source venv/bin/activate && pytest && ruff check .
   cd frontend && npm test && npm run lint && npm run build
   ```
5. **Update AGENTS.md** if you recognize reusable patterns (see below)
6. **On success**:
   - Git Commit: `fix: BUG-ID - Title` (with Co-Authored-By: Claude)
   - tasks.json: set `fixed: true`

## Rules
- One bug per iteration, understand root cause
- Minimally invasive fixes, tests must be green
- Act autonomously

## Updating AGENTS.md Files

Before committing, check if edited files have insights worth capturing in nearby AGENTS.md files:

1. **Identify directories with edited files** - See which directories you modified
2. **Look for existing AGENTS.md** - Search for AGENTS.md in these directories or parent directories
3. **Add valuable insights** - If you discovered something that future developers/agents should know:
   - API patterns or conventions specific to this module
   - Pitfalls or non-obvious requirements
   - Dependencies between files
   - Testing approaches for this area
   - Configuration or environment requirements

**DO NOT add:**
- Bug-specific implementation details
- Temporary debugging notes
- One-off fixes without reuse value

Only update AGENTS.md if you have **truly reusable knowledge** that would help with future work in this directory.

## Status (MANDATORY at end of every response)

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
BUG_ID: <bug_id>
FIX_SUCCESSFUL: true|false
TESTS_STATUS: PASSING|FAILING|NOT_RUN
FILES_MODIFIED: <n>
EXIT_SIGNAL: false|true
RECOMMENDATION: <next step>
---END_RALPH_STATUS---
```

**EXIT_SIGNAL: true** only when ALL bugs have `fixed: true` and tests are green.

Begin with the next open bug!
