# RALPH Test Mode

Test features through exploratory UI tests with MCP Playwright.

## Files
- **Features**: `ralph/test/tasks.json` - Features to test
- **Context**: `AGENTS.md` - Project conventions

## Test Setup: Documents and Login

**IMPORTANT:** Before testing core functionality (CORE-* features), the test setup must be completed:

### Test Documents (from config.sh)
- **Resume:** `~/cv-ger.pdf`
- **Reference Letter:** `~/Filip Zeugnis.pdf`

### Setup Flow (Feature SETUP-001)
1. Register new test user OR log in existing user
2. Navigate to `/documents`
3. Upload resume via `browser_file_upload` with the path above
4. Wait for upload confirmation
5. Upload reference letter
6. Wait for upload confirmation
7. Create at least one template under `/templates`
8. Verify: Both documents and template are present

### File Upload with MCP Playwright
```
browser_file_upload with paths: ["/Users/filipores/Documents/Bewerbungsunterlagen/Batch/cv-ger.pdf"]
```

After setup, the CORE-* features can be tested.

## MCP Playwright Tools (Most Important)

| Category | Tool | Description |
|----------|------|-------------|
| **Navigation** | `browser_navigate` | Open URL |
| | `browser_snapshot` | **PREFERRED!** Accessibility snapshot |
| | `browser_take_screenshot` | Screenshot (only for documentation) |
| **Interaction** | `browser_click` | Click element (ref from snapshot) |
| | `browser_type` | Enter text |
| | `browser_fill_form` | Fill form |
| **Debugging** | `browser_console_messages` | **IMPORTANT:** Check JS errors! |
| | `browser_network_requests` | Check API errors (4xx, 5xx) |
| **Assertions** | `browser_verify_text_visible` | Text visible? |
| **Control** | `browser_resize` | Change viewport (375x667 = Mobile) |
| | `browser_wait_for` | Wait for text/time |

## Workflow

1. `browser_navigate` to relevant page
2. `browser_snapshot` for structure (NOT screenshot!)
3. `browser_console_messages` → Initial errors?
4. Perform interactions (click, type, fill_form)
5. After actions: `browser_snapshot` + `browser_console_messages`
6. On bugs: `browser_take_screenshot` as evidence
7. `browser_resize` to 375x667 for mobile test

## Output (MANDATORY)

```json
---RALPH_TEST_RESULT---
{
  "feature_id": "COMMIT-X",
  "tested_at": "ISO-Timestamp",
  "has_bugs": true|false,
  "bugs": [{
    "id": "BUG-001",
    "severity": "critical|major|minor|trivial",
    "title": "Description",
    "steps_to_reproduce": ["Step 1", "Step 2"],
    "expected": "Expected",
    "actual": "Actual",
    "affected_component": "Component.vue"
  }],
  "suggestions": [{
    "id": "SUG-001",
    "type": "ux|performance|accessibility|feature",
    "title": "Description",
    "priority": "high|medium|low"
  }]
}
---END_RALPH_TEST_RESULT---
```

## Updating AGENTS.md Files

If you discover reusable knowledge while testing, add it to the corresponding AGENTS.md:

1. **Identify directories** - Which areas of the app did you test?
2. **Look for existing AGENTS.md** - In these directories or parent directories
3. **Add valuable insights**:
   - UI patterns that should be tested
   - Critical user flows
   - Known edge cases
   - Performance aspects of certain features

**DO NOT add:**
- Test session-specific details
- Temporary bug descriptions (belong in tasks.json)
- One-off observations without reuse value

Only update AGENTS.md if you have **truly reusable knowledge**.

## Status (MANDATORY at end)

```
---RALPH_STATUS---
STATUS: IN_PROGRESS|COMPLETE|BLOCKED
FEATURE_TESTED: <feature_id>
BUGS_FOUND: <n>
SUGGESTIONS_FOUND: <n>
SCREENSHOTS_TAKEN: <n>
EXIT_SIGNAL: false|true
RECOMMENDATION: <next step>
---END_RALPH_STATUS---
```

Test the provided feature thoroughly!
