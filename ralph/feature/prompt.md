# RALPH Feature Mode

Implement User Stories from `ralph/feature/tasks.json` one by one.

## Files
- **PRD**: `ralph/feature/tasks.json` - Stories with `passes: false`, sorted by `priority`
- **Context**: `AGENTS.md` - Project conventions

## Workflow

1. **Find story**: Read PRD, take story with `passes: false` and lowest `priority`
2. **Implement**: Fulfill ALL Acceptance Criteria, follow AGENTS.md
3. **DB Migration**: If new/modified models:
   ```bash
   cd backend && source venv/bin/activate
   FLASK_APP=app.py flask db migrate -m "Add/Update: Description"
   FLASK_APP=app.py flask db upgrade
   ```
   **IMPORTANT**: Add model import to `app.py` if new model!
4. **Quality Checks**:
   ```bash
   cd backend && source venv/bin/activate && pytest && ruff check .
   cd frontend && npm test && npm run lint && npm run build
   ```
   - Review changes with the security-review skill and modify if needed
5. **Update AGENTS.md** if you recognize reusable patterns (see below)
6. **On success**:
   - Git Commit: `feat: STORY-ID - Title` (with Co-Authored-By: Claude)
   - PRD: set `passes: true`
   - Document progress in `ralph/feature/logs/progress.txt` (see below)

## Rules
- One story per iteration, fulfill all criteria
- Tests ~20% effort, prioritize implementation
- Act autonomously, don't ask questions

## Progress Format

APPEND to `logs/progress.txt` (never replace, always append):
```
## [Date/Time] - [Story-ID]
- What was implemented
- Modified files
- **Insights for future iterations:**
  - Discovered patterns (e.g. "this codebase uses X for Y")
  - Pitfalls encountered (e.g. "don't forget to update Z when W changes")
  - Useful context (e.g. "the evaluation panel is in component X")
---
```

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
- Story-specific implementation details
- Temporary debugging notes
- Information already in `logs/progress.txt`

Only update AGENTS.md if you have **truly reusable knowledge** that would help with future work in this directory.

## Status (MANDATORY at end of every response)

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
TASKS_COMPLETED_THIS_LOOP: <n>
FILES_MODIFIED: <n>
TESTS_STATUS: PASSING|FAILING|NOT_RUN
WORK_TYPE: IMPLEMENTATION|TESTING|DOCUMENTATION
EXIT_SIGNAL: false|true
RECOMMENDATION: <next step>
---END_RALPH_STATUS---
```

**EXIT_SIGNAL: true** only when ALL stories have `passes: true` and tests are green.

Begin now!
