# TODO - Bugs & Suggestions from Ralph Testing

**Generated:** 2026-01-24
**Test Sessions:** 2026-01-22 to 2026-01-24
**Sources:** Ralph Test (automated feature tests) + Ralph Explore (exploratory browser tests)

---

## Critical Bugs (P0)

### CORE-020-BUG-001: Success Modal has no Escape key handler
- **Severity:** Critical
- **Component:** `frontend/src/pages/NewApplication.vue:614-679`
- **Steps to reproduce:**
  1. Navigate to /new-application
  2. Complete the application generation flow successfully
  3. When the success modal appears, press the Escape key
- **Expected:** Modal should close when Escape key is pressed (standard accessibility pattern)
- **Actual:** Modal does not respond to Escape key. Other modals (ConfirmModal, JobRecommendations, SkillsOverview) all implement Escape key handling.

### EXPLORE-BUG-007: Privacy Policy link causes unexpected logout
- **Severity:** Critical
- **Component:** `frontend/src/router`, `frontend/src/middleware/auth`
- **Steps to reproduce:**
  1. Navigate to any page while logged in
  2. Click 'Datenschutz' in footer
  3. Observe redirect to login page
- **Expected:** Should navigate to privacy policy page while maintaining login session
- **Actual:** User is logged out and redirected to login page

---

## Major Bugs (P1)

### I18N-001-BUG-001: LanguageSwitcher nicht auf Login-Seite sichtbar
- **Severity:** Major
- **Component:** `frontend/src/pages/Login.vue`, `frontend/src/App.vue`
- **Steps to reproduce:**
  1. Navigiere zu /login (als nicht-authentifizierter User)
  2. Suche nach dem LanguageSwitcher in der Navbar
- **Expected:** LanguageSwitcher sollte in der Navbar auf der Login-Seite sichtbar sein
- **Actual:** LanguageSwitcher ist nur fuer authentifizierte User in App.vue eingebunden (v-if='authStore.isAuthenticated()')

### I18N-002-BUG-001: Nach Login wird die Sprache NICHT vom Backend synchronisiert
- **Severity:** Major
- **Component:** `frontend/src/store/auth.js:8-14`, `frontend/src/pages/Login.vue:251`
- **Steps to reproduce:**
  1. Setze im Backend die User-Sprache auf 'en' (direkt in DB oder via API)
  2. Loesche localStorage (obojobs-locale)
  3. Oeffne /login (Frontend zeigt Deutsch als Default)
  4. Logge dich ein
  5. Beobachte: Frontend bleibt auf Deutsch, obwohl User.language='en' ist
- **Expected:** Nach Login sollte die Spracheinstellung vom Backend (user.language) geladen und im Frontend angewendet werden
- **Actual:** authStore.login() speichert zwar user.language, aber vue-i18n locale wird NICHT aktualisiert

### I18N-002-BUG-002: Sprachwechsel VOR Login wird NICHT mit Backend synchronisiert
- **Severity:** Major
- **Component:** `frontend/src/store/auth.js:8-14`
- **Steps to reproduce:**
  1. Oeffne /login (nicht eingeloggt)
  2. LanguageSwitcher ist NICHT vorhanden (nur fuer authentifizierte User)
  3. Wechsle Sprache auf anderem Weg (z.B. localStorage manuell)
  4. Logge dich ein
  5. Beobachte Network: Kein PUT /api/auth/language Request
- **Expected:** Nach erfolgreichem Login sollte die aktuelle Frontend-Sprache mit PUT /api/auth/language ans Backend gesendet werden
- **Actual:** authStore.login() macht keinen Language-Sync Call

### CORE-016-BUG-001: Kein Link zur Subscription-Seite bei Limit-Fehler
- **Severity:** Major
- **Component:** `frontend/src/pages/NewApplication.vue:1259-1260`
- **Steps to reproduce:**
  1. Melde dich als Free-User an
  2. Generiere 3 Bewerbungen (Limit erreicht)
  3. Versuche eine 4. Bewerbung zu generieren
  4. Beobachte die Fehlermeldung
- **Expected:** Fehlermeldung sollte einen klickbaren Link zu /subscription enthalten
- **Actual:** Fehlermeldung zeigt nur Text ohne Link. User muss selbst den Weg zur Subscription-Seite finden.

### CORE-020-BUG-002: Success Modal lacks focus trap for keyboard users
- **Severity:** Major
- **Component:** `frontend/src/pages/NewApplication.vue:614-679`
- **Steps to reproduce:**
  1. Generate an application to trigger the success modal
  2. Press Tab repeatedly to navigate through focusable elements
- **Expected:** Focus should be trapped within the modal
- **Actual:** Focus can escape the modal and reach elements behind the backdrop

### CORE-020-BUG-003: Success Modal missing role='dialog' and aria-modal='true'
- **Severity:** Major
- **Component:** `frontend/src/pages/NewApplication.vue:616`
- **Expected:** Modal should have role='dialog' and aria-modal='true'
- **Actual:** Modal div lacks role and aria-modal attributes

### CORE-020-BUG-004: Collapsible description section not keyboard accessible
- **Severity:** Major
- **Component:** `frontend/src/pages/NewApplication.vue:369-394`
- **Expected:** Description toggle should be keyboard accessible with proper ARIA attributes
- **Actual:** The description header has @click handler but no keyboard event handler

### CORE-023-BUG-001: Contact data extraction truncates text to 3000 characters
- **Severity:** Major
- **Component:** `backend/services/contact_extractor.py:201`
- **Steps to reproduce:**
  1. Navigate to /new-application
  2. Click 'Stellentext manuell einfuegen'
  3. Paste a very long job posting text (>5000 characters)
  4. Click 'Stellentext analysieren'
- **Expected:** Contact data should be extracted from the entire job posting text
- **Actual:** The ContactExtractor.extract_contact_data() method truncates text to 3000 characters. Contact info at end of postings will be lost.

### EXPLORE-BUG-001: Insights page is completely empty
- **Severity:** Major
- **Component:** `frontend/src/pages/insights`
- **Steps to reproduce:**
  1. Navigate to logged-in dashboard
  2. Click on 'Insights' in navigation menu
- **Expected:** Page should display company insights, analytics, or relevant content
- **Actual:** Page is completely empty with no content between header and footer

### EXPLORE-BUG-002: Settings page is completely empty
- **Severity:** Major
- **Component:** `frontend/src/pages/settings`
- **Steps to reproduce:**
  1. Navigate to logged-in dashboard
  2. Click on 'Einstellungen' (Settings) in top-right navigation
- **Expected:** Page should display user settings, preferences, account options
- **Actual:** Page is completely empty with no content

### EXPLORE-BUG-003: New Application page is completely empty
- **Severity:** Major
- **Component:** `frontend/src/pages/applications/new`
- **Steps to reproduce:**
  1. Navigate to logged-in dashboard
  2. Click on 'Neu' (New) in navigation menu
- **Expected:** Page should display form or wizard for creating new job applications
- **Actual:** Page is completely empty with no content

---

## Minor Bugs (P2)

### CORE-015-BUG-001: Usage display format may be confusing
- **Severity:** Minor
- **Component:** `frontend/src/pages/NewApplication.vue:554`
- **Issue:** Display shows '2/3 Bewerbungen diesen Monat' which is ambiguous - users may think they've used 2 when actually 2 remain. The word 'verbleibend' (remaining) is missing.

### CORE-020-BUG-005: Some form labels not properly associated with inputs
- **Severity:** Minor
- **Component:** `frontend/src/pages/NewApplication.vue:316-366`
- **Issue:** Several labels (Standort, Anstellungsart, Ansprechpartner, Kontakt-Email, Gehalt) lack 'for' attribute

### CORE-020-BUG-006: Missing aria-label on modal close button
- **Severity:** Minor
- **Component:** `frontend/src/pages/NewApplication.vue:628-633`
- **Issue:** Modal close button has no aria-label, only an SVG icon

### CORE-023-BUG-002: No feedback to user about text length processing
- **Severity:** Minor
- **Component:** `frontend/src/pages/NewApplication.vue:216`
- **Issue:** No indication given to user that their text may be truncated for processing

### GOAL-002-BUG-001: Confetti may trigger on page load if goal already achieved
- **Severity:** Minor
- **Component:** `WeeklyGoalWidget.vue:188-197`
- **Issue:** Since previousAchieved is initialized as false, confetti triggers on page load for users who already completed their goal

### GOAL-002-BUG-002: Confetti animation may appear clipped on smaller cards
- **Severity:** Minor
- **Component:** `WeeklyGoalWidget.vue:497-506`
- **Issue:** Confetti falls only 200px which may not reach the bottom on taller card layouts

### SKEL-002-BUG-001: Skeleton stats count mismatch with actual stats
- **Severity:** Minor
- **Component:** `frontend/src/pages/InterviewPrep.vue:143-147`
- **Issue:** Skeleton shows only 3 stat placeholders while actual Stats section has 4

---

## Trivial Bugs (P3)

### SKEL-002-BUG-002: Skeleton filter count may not match dynamic filter tabs
- **Severity:** Trivial
- **Component:** `frontend/src/pages/InterviewPrep.vue:148-152`
- **Issue:** Skeleton shows 3 filter placeholders, but actual filter section can have up to 6 tabs

---

## High Priority Suggestions

### SUG-I18N-001: LanguageSwitcher auf Login-Seite hinzufuegen
- **Type:** Feature
- **Description:** Entweder: (A) LanguageSwitcher neben dem theme-toggle-float in Login.vue einbauen, oder (B) Eine separate mini-navbar fuer nicht-authentifizierte Seiten erstellen mit Theme Toggle + Language Switcher.

### SUG-I18N-002: Bidirektionale Sprachsynchronisation implementieren
- **Type:** Feature
- **Description:** In authStore.login() nach erfolgreichem Login: 1) User.language aus Response lesen, 2) Falls unterschiedlich zu localStorage: Backend-Sprache uebernehmen (fuer Multi-Device Konsistenz).

### SUG-CORE-016-001: isSubscriptionLimitError computed property hinzufuegen
- **Type:** UX
- **Description:** Analog zu isDocumentMissingError sollte es eine isSubscriptionLimitError computed property geben, die prueft ob error_code === 'SUBSCRIPTION_LIMIT_REACHED' und dann einen Link zu /subscription anzeigt.

### SUG-CORE-020-001: Add Escape key handler to success modal
- **Type:** Accessibility
- **Description:** Add keydown event listener that closes modal when Escape is pressed, following the pattern used in ConfirmModal.vue

### SUG-CORE-020-002: Implement focus trap for success modal
- **Type:** Accessibility
- **Description:** Use a focus trap library or manually implement focus trapping. On modal open, focus should move to the first focusable element.

### SUG-CORE-020-003: Add proper ARIA attributes to modal
- **Type:** Accessibility
- **Description:** Add role='dialog', aria-modal='true', aria-labelledby='modal-title' to modal div.

### SUG-GOAL-002-004: Store celebration shown state in localStorage
- **Type:** UX
- **Description:** Prevent repeat confetti triggers on page refresh by storing celebration state in localStorage

### SUG-CORE-023-001: Add smart contact extraction from end of text
- **Type:** Feature
- **Description:** Since contact information is often at the end of job postings, consider extracting last 1000 characters separately for contact data extraction, then merge with results from first 3000 characters.

### SUG-EXPLORE-001: Add loading states for empty pages
- **Type:** UX
- **Description:** Several pages appear empty, which creates confusion about whether content is loading or missing. Add loading spinners or skeleton screens.

### SUG-EXPLORE-004: Implement consistent modal behavior
- **Type:** UX
- **Description:** Modals should have predictable behavior - staying open until user action, proper close buttons, and escape key handling.

### SUG-EXPLORE-006: Add error boundary components
- **Type:** Feature
- **Description:** Implement React/Vue error boundaries to catch JavaScript errors and display user-friendly error messages instead of blank pages.

### SUG-EXPLORE-008: Review session management
- **Type:** Security
- **Description:** The unexpected logout when accessing privacy policy suggests session management issues. Review and strengthen session handling.

---

## Medium Priority Suggestions

### SUG-I18N-003: Konflikt-Handling bei unterschiedlichen Sprachen
- **Type:** UX
- **Description:** Falls localStorage-Sprache != Backend-Sprache beim Login: User fragen welche Sprache beibehalten werden soll.

### SUG-CORE-016-002: Pro-active Warnung vor Limit-Erreichen
- **Type:** UX
- **Description:** Wenn der User nur noch 1 Bewerbung uebrig hat (remaining === 1), sollte ein gelbes Banner erscheinen das vor dem bevorstehenden Limit warnt.

### SUG-CORE-016-003: Generate-Button deaktivieren wenn Limit erreicht
- **Type:** UX
- **Description:** Statt den Fehler erst nach Klick anzuzeigen, koennte der Generate-Button disabled werden wenn usage.remaining === 0.

### SUG-CORE-020-004: Make description toggle keyboard accessible
- **Type:** Accessibility
- **Description:** Add @keydown.enter and @keydown.space handlers to description header. Add tabindex='0', aria-expanded, aria-controls.

### SUG-CORE-020-005: Add for/id attributes to all form field pairs
- **Type:** Accessibility
- **Description:** Add unique id attributes to all input fields and corresponding 'for' attributes to their labels.

### SUG-CORE-023-002: Add character count indicator for manual text input
- **Type:** UX
- **Description:** Show a character counter on the textarea to give users visibility into text length.

### SUG-GOAL-001-002: Missing ARIA label on progress bar
- **Type:** Accessibility
- **Description:** The progress bar lacks aria-role='progressbar', aria-valuenow, aria-valuemin, and aria-valuemax attributes.

### SUG-GOAL-001-003: Goal edit validation feedback missing
- **Type:** UX
- **Description:** When user enters invalid goal value (<1 or >50), the save fails silently. Consider showing validation error message.

### SUG-GOAL-002-002: Consider adding a streak counter
- **Type:** UX
- **Description:** Add streak counter for consecutive weeks of goal achievement

### SUG-GOAL-002-003: Add aria-live announcement for goal achievement
- **Type:** Accessibility

### SUG-DASH-002-003: Consider showing multiple upcoming interviews
- **Type:** UX
- **Description:** Currently only the next interview is displayed. Users with multiple scheduled interviews might benefit from seeing '2 more scheduled' indicator.

### SUG-SKEL-002-003: Enhance skeleton ARIA labeling
- **Type:** Accessibility
- **Description:** Add aria-busy='true' and role='status' for better screen reader support during loading state.

### SUG-SKEL-002-004: Add reduced motion support for shimmer animation
- **Type:** Accessibility
- **Description:** The skeleton shimmer animation doesn't respect prefers-reduced-motion.

### SUG-EXPLORE-005: Add keyboard navigation support
- **Type:** Accessibility
- **Description:** Test and implement proper keyboard navigation throughout the application.

---

## Low Priority Suggestions

### SUG-CORE-014-001: Consider direct download instead of new tab for PDF
- **Type:** UX

### SUG-CORE-014-002: Add focus trap to success modal
- **Type:** Accessibility

### SUG-CORE-014-003: Add loading state during PDF download
- **Type:** UX

### SUG-CORE-015-002: Add visual progress indicator for usage
- **Type:** UX

### SUG-CORE-020-006: Add aria-label to modal close button
- **Type:** Accessibility

### SUG-DASH-001-001: Badge Text Inconsistency
- **Type:** UX
- **Description:** 'Gesendet' shows '+N heute' while others show '+N neu'. Consider consistent terminology.

### SUG-DASH-002-002: Missing ARIA live region for dynamic interview count
- **Type:** Accessibility

### SUG-DASH-003-001: Empty State koennte CTA zum Bewerbungen-Erstellen haben
- **Type:** UX

### SUG-GOAL-001-001: Progress bar could show overflow indicator
- **Type:** UX
- **Description:** When user exceeds weekly goal, show visual indicator for over-achievement.

### SUG-GOAL-001-004: Consider week boundary display
- **Type:** Feature
- **Description:** Show 'Diese Woche (20.01 - 26.01)' to help users understand the timeframe.

### SUG-EXPLORE-002: Improve dropdown interaction feedback
- **Type:** UX

### SUG-EXPLORE-003: Add breadcrumb navigation
- **Type:** Feature

### SUG-EXPLORE-007: Improve empty state messaging
- **Type:** UX

---

## Summary

| Category | Count |
|----------|-------|
| Critical Bugs | 2 |
| Major Bugs | 11 |
| Minor Bugs | 7 |
| Trivial Bugs | 1 |
| **Total Bugs** | **21** |
| High Priority Suggestions | 12 |
| Medium Priority Suggestions | 14 |
| Low Priority Suggestions | 10 |
| **Total Suggestions** | **36** |
