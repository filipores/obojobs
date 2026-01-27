# Template Component Bugs

**Tested on:** 2026-01-26
**Tested by:** Automated Playwright Testing
**Component:** Template Editor (`/templates` page)
**Files affected:**
- `frontend/src/pages/Templates.vue`
- `frontend/src/components/TemplateEditor/TemplateEditor.vue`
- `frontend/src/composables/useTemplateParser.js`

---

## Critical Bugs

### BUG-001: Variable Label Text Duplication on Insert

**Severity:** CRITICAL
**Status:** Open
**Reproducible:** Yes (100%)

**Description:**
When inserting a variable via the VariablePanel button click, the variable chip is inserted correctly, BUT the variable's label text is also added as plain text immediately after the chip.

**Steps to Reproduce:**
1. Go to `/templates`
2. Click "Selbst schreiben" to create a new template
3. Type some text in the editor, e.g., "Sehr geehrte Damen und Herren bei "
4. Click on the "Firma" variable button in the panel

**Expected Result:**
Editor shows: `Sehr geehrte Damen und Herren bei [Firma chip]`

**Actual Result:**
Editor shows: `Sehr geehrte Damen und Herren bei [Firma chip]Firma`

The label "Firma" appears twice - once as the chip and once as plain text.

**Root Cause (suspected):**
In `TemplateEditor.vue`, the `handleInsertVariable()` function at line 457-527 creates and inserts the chip correctly, but when `setContent()` is called with `getPlainTextFromEditor()`, the serialization/parsing logic appears to duplicate the label text.

---

### BUG-002: Live Preview Shows Concatenated Values

**Severity:** CRITICAL
**Status:** Open
**Reproducible:** Yes (100%)

**Description:**
The live preview panel displays both the replaced variable value AND the original label text concatenated together, without any space.

**Steps to Reproduce:**
1. Create or edit a template with variables
2. Observe the live preview panel

**Expected Result:**
Preview shows: `Sehr geehrte Damen und Herren bei Muster GmbH`

**Actual Result:**
Preview shows: `Sehr geehrte Damen und Herren bei Muster GmbHFirma`

**Impact:**
Users cannot accurately preview how their template will look when rendered.

---

### BUG-003: Auto-Save Persists Corrupted Data

**Severity:** CRITICAL
**Status:** Open
**Reproducible:** Yes

**Description:**
The auto-save feature (triggered every 30 seconds during editing) saves the corrupted content to the backend database, permanently damaging template data.

**Steps to Reproduce:**
1. Open an existing template for editing
2. Insert a variable using the panel
3. Wait for auto-save (or observe "Gespeichert" indicator)
4. Cancel editing and view the template card

**Expected Result:**
Template content remains intact

**Actual Result:**
Template content is permanently corrupted with duplicated label text

**Impact:**
User data loss - templates become unusable and display incorrect content.

---

### BUG-004: Existing Templates Show Severe Data Corruption

**Severity:** CRITICAL
**Status:** Open (data corruption already occurred)

**Description:**
At least one existing template in the database shows severe corruption with variable labels duplicated multiple times and merged with surrounding text.

**Evidence from testing:**
- Template preview shows: `{{ANSPRECHPARTNER}}Ansprechpartner`
- Editor content shows: `FirmaFirmaFirmaFirmaschaft` (label duplicated 4+ times, merged with "schaft")
- Editor content shows: `PositionPositionPositionrfahren` (label duplicated 3+ times, merged with "rfahren")

**Impact:**
Existing user data is corrupted and templates may be unusable.

---

## High Priority Bugs

### BUG-005: Variable Removal Leaves Label Text Behind

**Severity:** HIGH
**Status:** Open
**Reproducible:** Yes

**Description:**
When removing a variable by clicking the "X" button on a variable chip, the chip is removed but its label text remains in the content as plain text.

**Steps to Reproduce:**
1. Open a template with variables
2. Click the "Variable entfernen" (X) button on a variable chip
3. Observe the editor content

**Expected Result:**
Variable chip and its placeholder are completely removed

**Actual Result:**
Variable chip is removed, but the label text (e.g., "Einleitung") remains as plain text

---

### BUG-006: Strange Characters in AI-Generated Templates

**Severity:** MEDIUM
**Status:** Open

**Description:**
Some AI-generated templates contain unusual characters like sparkle emoji (`✨`) embedded in the text content, which appears to be artifacts from the AI generation process.

**Evidence:**
- Template content shows: `YOOtheme entdeckt✨die Stellenausschreibung`
- Template content shows: `YOOtheme✨YOOthemeFirma`

**Impact:**
Templates may display unprofessionally with random emoji characters.

---

## Working Features (Verified)

The following template features were tested and work correctly:

- Template list display
- Template card preview (shows first 180 characters)
- "Als Standard" (set as default) functionality
- Delete confirmation dialog
- KI Wizard navigation and validation
- Character count display
- Template name input
- Checkbox for "Als Standard-Template setzen"

---

## Recommended Fixes

### Priority 1: Fix Variable Insertion Logic
**File:** `frontend/src/components/TemplateEditor/TemplateEditor.vue`

The `handleInsertVariable()` function needs to be reviewed. The issue appears to be in how the content is serialized after inserting a chip. The `getPlainTextFromEditor()` function may be including both the chip's data-type attribute AND any text content.

### Priority 2: Fix Template Parser/Serializer
**File:** `frontend/src/composables/useTemplateParser.js`

Review the `parseTemplate` and `serializeTemplate` functions to ensure proper handling of variable boundaries without duplicating label text.

### Priority 3: Disable Auto-Save Until Fixed
Consider temporarily disabling auto-save to prevent further data corruption while the bugs are being fixed.

### Priority 4: Data Migration
Create a migration script to fix corrupted templates in the database by removing duplicated label text patterns.

---

## Test Environment

- **Browser:** Chromium (Playwright)
- **Frontend:** Vite dev server on localhost:3000
- **Backend:** Flask on localhost:5001
- **Test Account:** test@example.com

---
---

# New Application Component Bugs

**Tested on:** 2026-01-26
**Tested by:** Automated Playwright Testing
**Component:** New Application (`/new-application` page)
**Files affected:**
- `frontend/src/pages/NewApplication.vue`

---

## Medium Priority Bugs

### BUG-007: URL Validation State Lost After Reset

**Severity:** MEDIUM
**Status:** Open
**Reproducible:** Yes (100%)

**Description:**
After clicking the "Neu laden" (reset) button, the URL validation icon and message disappear even though the URL is still present in the input field.

**Steps to Reproduce:**
1. Go to `/new-application`
2. Enter a valid URL (e.g., `https://www.stepstone.de/jobs/test-123`)
3. Wait for validation - green checkmark and "URL ist gültig" message appear
4. Load the job preview (or use manual text input)
5. Click "Neu laden" button to reset

**Expected Result:**
- URL remains in input field ✓
- Validation icon and message should persist (URL is still valid)

**Actual Result:**
- URL remains in input field ✓
- Validation icon and "URL ist gültig" message disappear
- User must modify URL to trigger re-validation

**Impact:**
Minor UX issue - confusing state where URL appears unvalidated despite being valid.

---

### BUG-008: "Ohne Score fortfahren" Button Does Not Dismiss Error Section

**Severity:** LOW
**Status:** Open
**Reproducible:** Yes

**Description:**
When the Job-Fit analysis fails and the user clicks "Ohne Score fortfahren" (continue without score), the button becomes active but the error section with all options remains fully visible.

**Steps to Reproduce:**
1. Go to `/new-application`
2. Load a job preview (via URL or manual text input)
3. Wait for Job-Fit analysis to fail (shows error section)
4. Click "Ohne Score fortfahren" button

**Expected Result:**
- Error section should collapse or show a success indicator
- User should clearly see they've acknowledged the error and can proceed

**Actual Result:**
- Button shows as "active" state
- Entire error section remains visible with both buttons
- No clear visual feedback that the action was acknowledged

**Impact:**
Confusing UX - user doesn't get clear feedback that their choice was registered.

---

## Working Features (Verified)

The following New Application features were tested and work correctly:

- URL input with real-time validation
- URL format validation with clear error messages
- Portal detection badges (StepStone, Indeed, XING, Sonstige)
- "Stellenanzeige laden" button disabled for invalid URLs
- Manual text input fallback ("Keinen Link? Text hier eingeben...")
- Location auto-detection from job description text
- Preview form with all editable fields (Firma, Position, Standort, etc.)
- Stellenbeschreibung collapsible section
- Template dropdown selection with multiple options
- Template variable info display
- Application quota counter ("Noch X von Y Bewerbungen diesen Monat")
- "Neu laden" button resets form correctly (except validation state bug)
- Error notifications display correctly
- "Erneut versuchen" button for Job-Fit retry

---

## Notes

### Job-Fit Analysis
The Job-Fit analysis endpoint (`/api/applications/analyze-job-fit`) returns a 500 error in the development environment. This may be expected behavior due to:
- Missing API keys for AI analysis
- Backend service not fully configured
- External service dependency

This should be verified against production environment to determine if it's a real bug.

### Portal Badge in Preview Header
When using manual text input, the preview header correctly shows "Manuell eingegeben" badge. Portal detection works correctly when a URL is entered (tested with StepStone URL showing "StepStone" badge).

---

## Recommended Fixes

### Priority 1: Fix Validation State Persistence
**File:** `frontend/src/pages/NewApplication.vue`

The `handleReset()` function should preserve the URL validation state, or alternatively re-trigger validation after reset if the URL field is not empty.

### Priority 2: Improve "Ohne Score fortfahren" UX
**File:** `frontend/src/pages/NewApplication.vue`

When "Ohne Score fortfahren" is clicked:
- Hide or collapse the error section
- Show a small indicator that proceeding without score is active
- Or simply hide the error section and show the generate button more prominently
