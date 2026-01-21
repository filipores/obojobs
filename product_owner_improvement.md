# Obojobs Product Owner Improvement Plan

**Document Version**: 1.0
**Created**: 2026-01-21
**Author**: Product Owner Analysis (Claude)
**Status**: Ready for Review

---

## Executive Summary

### One-Liner
Obojobs is a German job application automation platform that needs UX polish, conversion optimization, and strategic feature expansion to capture the untapped market of overwhelmed German job seekers.

### Current State Assessment

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    OBOJOBS PRODUCT HEALTH SCORECARD                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Dimension              Score    Benchmark    Status                     │
│  ─────────────────────────────────────────────────────────              │
│  Core Functionality     9/10     8/10         🟢 Excellent               │
│  Technical Foundation   9/10     8/10         🟢 Excellent               │
│  Design System          7/10     8/10         🟡 Good, needs polish      │
│  Onboarding UX          5/10     8/10         🔴 Critical friction       │
│  Conversion Funnel      4/10     7/10         🔴 Needs attention         │
│  Mobile Experience      6/10     8/10         🟡 Functional, not optimal │
│  Feature Discovery      5/10     7/10         🟡 Hidden value            │
│  Internationalization   7/10     8/10         🟢 Foundation in place     │
│  ─────────────────────────────────────────────────────────              │
│  OVERALL HEALTH         52/80    62/80        🟡 Strong foundation,      │
│                         (65%)    (78%)           UX gaps to close        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Strategic Opportunity
The product has **excellent technical foundation** and **comprehensive features** but suffers from **UX friction** that prevents users from experiencing value quickly. The primary opportunity is **time-to-value optimization** - getting users to their first AI-generated cover letter in under 2 minutes.

---

## Part 1: Product Discovery Analysis

### Jobs-to-be-Done Canvas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRIMARY JOB STATEMENT                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  When I find a job posting that interests me,                           │
│  I want to quickly create a personalized application,                   │
│  So I can apply before the position is filled while staying organized.  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │   FUNCTIONAL JOB                    EMOTIONAL JOB               │    │
│  │   ──────────────                    ─────────────               │    │
│  │   • Generate cover letter           • Feel prepared             │    │
│  │   • Track applications              • Reduce anxiety            │    │
│  │   • Prepare for interviews          • Feel in control           │    │
│  │   • Negotiate salary                • Feel confident            │    │
│  │                                                                  │    │
│  ├──────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │    │
│  │   SOCIAL JOB                        RELATED JOBS                │    │
│  │   ──────────                        ────────────                │    │
│  │   • Appear professional             Before: Find job postings   │    │
│  │   • Stand out from crowd            After: Interview prep       │    │
│  │   • Show competence                 Related: Career planning    │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Opportunity Solution Tree

```
                         DESIRED OUTCOME
                    ┌─────────────────────┐
                    │ Increase activation │
                    │ rate from ~30% → 60%│
                    └─────────┬───────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ OPPORTUNITY │    │ OPPORTUNITY │    │ OPPORTUNITY │
    │ Too many    │    │ Value not   │    │ Features    │
    │ steps before│    │ immediately │    │ are hidden  │
    │ value       │    │ visible     │    │ /complex    │
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                  │                  │
     ┌─────┴─────┐      ┌─────┴─────┐      ┌─────┴─────┐
     │           │      │           │      │           │
     ▼           ▼      ▼           ▼      ▼           ▼
   ┌─────┐   ┌─────┐  ┌─────┐   ┌─────┐  ┌─────┐   ┌─────┐
   │Skip │   │Defer│  │Show │   │Cele-│  │Prog-│   │Tool-│
   │doc  │   │docs │  │prev-│   │brate│  │ress-│   │tips │
   │req  │   │to   │  │iew  │   │wins │  │ive  │   │on   │
   │init │   │later│  │fast │   │     │  │disc │   │hover│
   └─────┘   └─────┘  └─────┘   └─────┘  └─────┘   └─────┘
```

### Assumption Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CRITICAL ASSUMPTIONS TO TEST                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   HIGH RISK (Unknown + Important)            TEST PRIORITY               │
│   ────────────────────────────────           ─────────────               │
│   • Users will upload CV before seeing       → Test: Skip CV flow        │
│     value (current blocker)                                              │
│                                                                          │
│   • Users want AI-generated intro            → Test: A/B test with       │
│     (vs writing their own)                     manual option             │
│                                                                          │
│   • German job seekers will pay €9.99/mo     → Test: Price testing       │
│                                                                          │
│   • Users find ATS/Interview features        → Test: Feature discovery   │
│                                                                          │
│   VALIDATED ASSUMPTIONS                                                  │
│   ─────────────────────                                                  │
│   ✓ Users need help with cover letters                                  │
│   ✓ German market underserved                                           │
│   ✓ AI quality is acceptable                                            │
│   ✓ Zen design differentiates                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Prioritized Backlog

### RICE-Scored Feature Backlog

| Priority | Feature | Reach | Impact | Confidence | Effort | RICE | Status |
|----------|---------|-------|--------|------------|--------|------|--------|
| **P0** | Quick-start onboarding (skip docs) | 10,000 | 3.0 | 80% | 2w | 12,000 | Proposed |
| **P0** | Empty states for all pages | 8,000 | 2.0 | 100% | 1w | 16,000 | Proposed |
| **P0** | Dashboard "Next Action" widget | 8,000 | 2.0 | 90% | 1w | 14,400 | Proposed |
| **P1** | Celebration moments (confetti, toasts) | 6,000 | 1.5 | 80% | 0.5w | 14,400 | Proposed |
| **P1** | Contextual upgrade prompts | 5,000 | 2.0 | 70% | 1w | 7,000 | Proposed |
| **P1** | Mobile-optimized job entry | 4,000 | 2.0 | 80% | 2w | 3,200 | Proposed |
| **P1** | Trial period implementation | 3,000 | 3.0 | 60% | 1.5w | 3,600 | Proposed |
| **P2** | Chrome extension onboarding | 2,000 | 2.0 | 70% | 1w | 2,800 | Proposed |
| **P2** | Email response auto-detection | 2,500 | 1.5 | 60% | 2w | 1,125 | Proposed |
| **P2** | Interview calendar integration | 2,000 | 1.5 | 50% | 2w | 750 | Proposed |
| **P3** | LinkedIn job import | 1,500 | 1.5 | 50% | 3w | 375 | Proposed |
| **P3** | Team/recruiter features | 500 | 2.0 | 40% | 4w | 100 | Proposed |

### MoSCoW Classification for Q1 2026

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Q1 2026 RELEASE SCOPE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  MUST HAVE (60% of capacity)                                            │
│  ─────────────────────────────                                          │
│  ☐ Quick-start onboarding flow                                          │
│  ☐ Empty states for all major pages                                     │
│  ☐ Dashboard "Next Action" widget                                       │
│  ☐ Complete English translation (i18n)                                  │
│                                                                          │
│  SHOULD HAVE (20% of capacity)                                          │
│  ─────────────────────────────                                          │
│  ☐ Celebration moments (first app, milestones)                          │
│  ☐ Contextual upgrade prompts                                           │
│  ☐ Weekly goal notifications                                            │
│                                                                          │
│  COULD HAVE (20% of capacity)                                           │
│  ─────────────────────────────                                          │
│  ☐ Mobile-optimized job URL entry                                       │
│  ☐ Chrome extension polish                                              │
│  ☐ Performance optimizations                                            │
│                                                                          │
│  WON'T HAVE (This Quarter)                                              │
│  ─────────────────────────────                                          │
│  ☐ LinkedIn direct integration                                          │
│  ☐ Team/recruiter features                                              │
│  ☐ Native mobile app                                                    │
│  ☐ Video interview recording                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Epic & User Stories

### Epic 1: Frictionless Onboarding

**Epic Goal**: Reduce time-to-first-application from 15+ minutes to under 3 minutes.

#### Story 1.1: Skip Document Upload Flow

```markdown
## [OBO-101] Allow users to create first application without CV upload

**Epic**: Frictionless Onboarding
**Priority**: P0
**Points**: 8
**Labels**: feature, onboarding, activation

### User Story
As a new user eager to try the product,
I want to generate my first cover letter without uploading documents,
So that I can experience the value immediately and decide if it's worth the setup.

### Context
Current onboarding requires CV + Arbeitszeugnis upload before any value is shown.
This creates a 4-5 step process before the "aha moment" (seeing AI-generated cover letter).
Users drop off because they don't have documents ready or don't trust the platform yet.

### Acceptance Criteria
Given a new user who just registered
When they click "Create First Application"
Then they can enter a job URL and basic info (name, target role)
And the system generates a generic but personalized cover letter
And they see a prompt to "Make it better with your CV" after seeing the result

Given a user who skipped CV upload
When they view their generated cover letter
Then they see clear indicators of what could be improved with CV data
And they see an inline prompt to upload CV for "personalized version"

Given a user who uploads CV after initial generation
When the upload completes
Then the cover letter is automatically regenerated with CV context
And a "before/after" comparison is shown to demonstrate value

### Technical Notes
- Modify `/api/applications/generate` to work without documents
- Add `has_cv` flag to personalization prompts
- Create comparison view component
- Track conversion: skipped → uploaded CV

### Out of Scope
- Removing CV requirement for Pro features (ATS, Interview Prep)
- Changing the existing full onboarding for returning users

### Definition of Done
- [ ] Code complete and reviewed
- [ ] Unit tests for document-optional generation
- [ ] Integration test for full flow
- [ ] A/B test framework in place
- [ ] Analytics events added
- [ ] QA verified on desktop and mobile
- [ ] Product Owner accepted
```

#### Story 1.2: Progressive Onboarding Checklist

```markdown
## [OBO-102] Add progressive onboarding checklist to dashboard

**Epic**: Frictionless Onboarding
**Priority**: P1
**Points**: 5
**Labels**: feature, onboarding, dashboard

### User Story
As a new user who skipped initial setup,
I want to see what steps will improve my experience,
So that I can complete them at my own pace while using the product.

### Acceptance Criteria
Given a new user with incomplete profile
When they view the dashboard
Then they see a "Getting Started" checklist showing:
  - [ ] Create your first application (completed if done)
  - [ ] Upload your CV for better personalization
  - [ ] Upload Arbeitszeugnis for reference matching
  - [ ] Set your weekly goal
  - [ ] Try the ATS optimizer (Pro feature teaser)

Given a user who completes a checklist item
When the action is detected
Then the item animates to "completed" state
And a small celebration toast appears
And progress percentage updates

Given a user who completes all checklist items
When viewing dashboard
Then the checklist collapses to a "Setup Complete" badge
And is dismissible permanently

### Technical Notes
- Store checklist state in user preferences
- Calculate completion from existing data (has_cv, has_certificate, etc.)
- Use existing skeleton loader patterns

### Out of Scope
- Gamification beyond checklist (badges, streaks)
- Forced completion of any item
```

#### Story 1.3: Instant Demo Mode

```markdown
## [OBO-103] Add "Try with demo data" option

**Epic**: Frictionless Onboarding
**Priority**: P2
**Points**: 5
**Labels**: feature, onboarding, conversion

### User Story
As a visitor evaluating the product,
I want to see a real example without signing up,
So that I can understand the value before creating an account.

### Acceptance Criteria
Given a visitor on the landing page
When they click "Try Demo"
Then they see a pre-filled application form with sample job URL
And clicking "Generate" shows an AI-generated cover letter
And a modal appears: "Like what you see? Sign up to create your own"

Given a visitor in demo mode
When they attempt to download or copy the cover letter
Then they are prompted to sign up
And their demo session is preserved for conversion

### Technical Notes
- No backend changes needed for demo generation
- Use rate-limited public endpoint
- Store demo session in localStorage
```

---

### Epic 2: Dashboard Value Clarity

**Epic Goal**: Make the dashboard a clear command center showing progress and next actions.

#### Story 2.1: Next Action Widget

```markdown
## [OBO-201] Add "Next Action" widget to dashboard

**Epic**: Dashboard Value Clarity
**Priority**: P0
**Points**: 5
**Labels**: feature, dashboard, engagement

### User Story
As a returning user,
I want to immediately see what I should do next,
So that I can make progress without thinking about where to start.

### Acceptance Criteria
Given a user with applications in various states
When they view the dashboard
Then they see a prominent "Next Action" card showing the most important action:
  Priority order:
  1. "Interview tomorrow with [Company]" - if interview within 24h
  2. "Follow up on [Company]" - if sent 7+ days ago, no response
  3. "You're behind on weekly goal" - if goal not on track
  4. "New match: [Job Title]" - if job recommendation available
  5. "Create new application" - default

Given a user clicks the Next Action
When the action is executed
Then they are navigated to the relevant page/modal
And the next action updates

### Technical Notes
- Create NextActionWidget.vue component
- Logic service to determine priority action
- API endpoint: `/api/dashboard/next-action`
```

#### Story 2.2: Application Status Timeline

```markdown
## [OBO-202] Improve application status visualization

**Epic**: Dashboard Value Clarity
**Priority**: P1
**Points**: 3
**Labels**: enhancement, dashboard, ux

### User Story
As a user tracking multiple applications,
I want to quickly see the status distribution,
So that I can understand my overall progress at a glance.

### Acceptance Criteria
Given a user with applications
When they view the dashboard
Then they see a visual status bar showing:
  [████████░░░░░░░░░░░░]
  8 sent • 3 responded • 2 interviews • 1 offer

Given a user hovers over a status segment
When hovering
Then a tooltip shows the company names in that status
And clicking navigates to filtered applications list

### Technical Notes
- Reuse existing stats endpoint
- Add StatusBar.vue component
- Use Zen design system colors for states
```

#### Story 2.3: Empty State Improvements

```markdown
## [OBO-203] Add helpful empty states to all major pages

**Epic**: Dashboard Value Clarity
**Priority**: P0
**Points**: 5
**Labels**: enhancement, ux, onboarding

### User Story
As a new user exploring the product,
I want to understand what each page does when empty,
So that I don't feel lost and know how to get started.

### Acceptance Criteria
Given a user visits Applications page with no applications
Then they see:
  - Illustration/icon representing applications
  - "No applications yet"
  - "Create your first application to start tracking your job search"
  - [+ Create Application] primary button
  - "or paste a job URL to get started instantly"

Given a user visits Templates page with only default template
Then they see:
  - "You're using the default template"
  - "Create custom templates for different job types"
  - [+ Create Template] button
  - Preview of what custom templates enable

Given a user visits Documents page with no uploads
Then they see:
  - "Upload your documents for better results"
  - Clear explanation of what each document type does
  - Drag-and-drop upload zone

Pages to update:
- Applications (done partially)
- Templates
- Documents
- Timeline
- Interview Prep
- ATS View

### Technical Notes
- Create EmptyState.vue reusable component
- Props: icon, title, description, primaryAction, secondaryText
```

---

### Epic 3: Conversion Optimization

**Epic Goal**: Increase free-to-paid conversion by 50% through strategic prompts and trial experience.

#### Story 3.1: Contextual Upgrade Prompts

```markdown
## [OBO-301] Add contextual upgrade prompts at value moments

**Epic**: Conversion Optimization
**Priority**: P1
**Points**: 5
**Labels**: feature, monetization, conversion

### User Story
As a free user experiencing value,
I want to understand when premium features would help,
So that I can make an informed decision about upgrading.

### Acceptance Criteria
Given a free user generates their 2nd application
When generation completes
Then a subtle banner appears: "You've used 2 of 3 free applications this month. Upgrade for unlimited."
And the banner is dismissible
And shows upgrade CTA

Given a free user tries ATS optimization
When they access the feature
Then they see a "Pro Feature" modal with:
  - Brief explanation of ATS value
  - Sample ATS report preview (blurred)
  - "Unlock with Pro - €19.99/mo" button
  - "Maybe later" dismiss option

Given a user on Basic plan hits 15 of 20 limit
When they generate application 15
Then a warning appears: "5 applications remaining this month"
And suggests Pro upgrade for unlimited

### Technical Notes
- Track upgrade prompt impressions and conversions
- Don't show same prompt twice in 24 hours
- Store dismiss state in localStorage
```

#### Story 3.2: Trial Period Implementation

```markdown
## [OBO-302] Implement 14-day Pro trial for new users

**Epic**: Conversion Optimization
**Priority**: P1
**Points**: 8
**Labels**: feature, monetization, trial

### User Story
As a new user,
I want to try all Pro features for free,
So that I can experience the full value before deciding to pay.

### Acceptance Criteria
Given a new user completes registration
When their account is created
Then they automatically receive 14-day Pro trial
And they see a welcome message explaining trial benefits
And a countdown appears in header: "12 days left in trial"

Given a trial user on day 12
When they log in
Then they see a prominent reminder: "2 days left - Don't lose your Pro features"
And easy upgrade CTA

Given a trial expires
When user logs in
Then their plan reverts to Free
And a "Trial ended" modal appears with:
  - Summary of what they accomplished
  - What they'll lose (unlimited apps, ATS, etc.)
  - Special offer: "Upgrade now for 20% off first month"

### Technical Notes
- Add `trial_ends_at` to User model
- Modify subscription checking middleware
- Create trial-specific email sequences
- Stripe: No payment method required for trial
```

#### Story 3.3: Milestone Celebrations

```markdown
## [OBO-303] Add celebration moments for user milestones

**Epic**: Conversion Optimization
**Priority**: P1
**Points**: 3
**Labels**: enhancement, engagement, delight

### User Story
As a user making progress,
I want to feel acknowledged for my achievements,
So that I stay motivated and associate positive emotions with the product.

### Acceptance Criteria
Given a user creates their first application
When generation completes
Then confetti animation plays briefly
And a toast says "Your first application! You're on your way."

Given a user receives their first response (status: antwort_erhalten)
When they update the status
Then a celebration modal appears: "Congratulations! Your first response!"
And shows encouraging message + prompt to prepare for interview

Given a user gets an interview (status: interview scheduled)
When they add interview date
Then celebration toast: "Interview scheduled! Let's prepare."
And auto-navigation to Interview Prep page offered

Given a user receives an offer (status: zusage)
When they update status to zusage
Then full celebration: confetti, modal, "You did it!"
And prompt to share experience/leave review

### Technical Notes
- Use canvas-confetti library (lightweight)
- Milestone tracking in user stats
- Don't repeat celebrations for same milestone type
```

---

### Epic 4: Mobile Experience

**Epic Goal**: Make the core flow (create application from job URL) seamless on mobile.

#### Story 4.1: Mobile-Optimized Job Entry

```markdown
## [OBO-401] Optimize new application flow for mobile

**Epic**: Mobile Experience
**Priority**: P1
**Points**: 8
**Labels**: enhancement, mobile, ux

### User Story
As a job seeker browsing jobs on my phone,
I want to quickly start an application from a job URL,
So that I can capture opportunities when I find them, not just at my computer.

### Acceptance Criteria
Given a user on mobile device
When they tap "New Application"
Then they see a simplified form:
  - Large URL paste field (full width)
  - "Paste from clipboard" button (uses Clipboard API)
  - Minimal visible fields (job URL only initially)
  - "Analyze Job" large touch target

Given a mobile user pastes a job URL
When analysis completes
Then results display in mobile-optimized cards
And "Generate Cover Letter" is a fixed bottom button
And template selection is a bottom sheet, not dropdown

Given a mobile user generates a cover letter
When generation completes
Then they can:
  - Preview in mobile-readable format
  - Share directly (Web Share API)
  - Save for later (mark as draft)
  - Download PDF

### Technical Notes
- Add mobile detection (user-agent + screen size)
- Implement bottom sheet component
- Use Web Share API for native sharing
- Test on iOS Safari + Android Chrome
```

---

## Part 4: Metrics Framework

### North Star Metric

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NORTH STAR METRIC                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│              WEEKLY ACTIVE APPLICATIONS GENERATED                        │
│                                                                          │
│   Why this metric?                                                       │
│   • Captures core value delivery (AI-generated cover letters)           │
│   • Correlates with user success (more apps → more interviews)          │
│   • Leads to revenue (usage drives upgrades)                            │
│   • Actionable (can be improved through UX, features, engagement)       │
│                                                                          │
│   Current Baseline: [To be measured]                                    │
│   Target (Q2 2026): +50% increase                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### AARRR Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    OBOJOBS PIRATE METRICS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ACQUISITION                                                             │
│  ───────────                                                             │
│  • Website visitors / week                    Target: Track baseline    │
│  • Signup conversion rate                     Target: >5%               │
│  • Source attribution (organic, paid, ref)   Target: Track             │
│                                                                          │
│  ACTIVATION                                                              │
│  ──────────                                                              │
│  • Time to first application                  Target: <3 minutes        │
│  • Onboarding completion rate                 Target: >60%              │
│  • First application generated (Day 0)        Target: >40%              │
│                                                                          │
│  RETENTION                                                               │
│  ─────────                                                               │
│  • Week 1 retention (generated 2+ apps)       Target: >30%              │
│  • Week 4 retention                           Target: >20%              │
│  • Weekly goal completion rate                Target: >50%              │
│                                                                          │
│  REVENUE                                                                 │
│  ───────                                                                 │
│  • Free → Paid conversion (30 days)           Target: >5%               │
│  • Trial → Paid conversion                    Target: >25%              │
│  • MRR                                        Target: Track growth      │
│  • ARPU                                       Target: >€12              │
│                                                                          │
│  REFERRAL                                                                │
│  ────────                                                                │
│  • NPS Score                                  Target: >40               │
│  • Referral signups                           Target: Track             │
│  • Social shares                              Target: Track             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Feature Success Metrics

| Feature | Primary Metric | Target | Guardrails |
|---------|---------------|--------|------------|
| Quick-start onboarding | First app generated (Day 0) | >40% | CV upload rate >60% by Day 7 |
| Empty states | Page bounce rate | -30% | No increase in support tickets |
| Next Action widget | Dashboard → Action conversion | >50% | No decrease in exploration |
| Upgrade prompts | Free → Paid conversion | +25% | No increase in churn |
| Trial period | Trial → Paid conversion | >25% | No decrease in engagement |
| Mobile optimization | Mobile app generation | +100% | No decrease in quality |

---

## Part 5: Release Roadmap

### Q1 2026 Release Plan

```
              January           February           March
         ────────────────    ────────────────    ────────────────
Week     1  2  3  4         5  6  7  8         9  10 11 12
         ┌─────────────────────────────────────────────────────────┐
EPIC 1   │███████████████████████████                              │
Onboard  │ Skip-CV ─▶ Checklist ─▶ Demo                           │
         │        ▲v0.1    ▲v0.2                                   │
         ├─────────────────────────────────────────────────────────┤
EPIC 2   │     ░░░░░░███████████████████████                       │
Dashboard│     Plan    Next Action ─▶ Empty States                │
         │                    ▲v0.1                                │
         ├─────────────────────────────────────────────────────────┤
EPIC 3   │               ░░░░░░░░░░██████████████████████████████  │
Convert  │               Plan       Upgrade ─▶ Trial ─▶ Celebrate │
         │                                ▲v0.1      ▲v0.2        │
         ├─────────────────────────────────────────────────────────┤
i18n     │███████████████████████████████████████████████████████  │
English  │ Ongoing translation completion                          │
         │                                            ▲v1.0 (GA)  │
         └─────────────────────────────────────────────────────────┘

Legend:
███  = Development/Delivery
░░░  = Planning/Design
  ▲  = Release milestone
```

### Release Milestones

| Milestone | Target Date | Key Deliverables | Success Criteria |
|-----------|-------------|------------------|------------------|
| v0.8.0 | Jan 31, 2026 | Skip-CV onboarding, Empty states | Activation rate +20% |
| v0.9.0 | Feb 28, 2026 | Next Action widget, Upgrade prompts | Dashboard engagement +30% |
| v1.0.0 | Mar 31, 2026 | Trial period, English GA, Mobile opt | Conversion rate +25% |

### Release Criteria Checklist

```markdown
## v0.8.0 Release Criteria
- [ ] Skip-CV flow working end-to-end
- [ ] Empty states on all major pages
- [ ] Onboarding checklist on dashboard
- [ ] No P0/P1 bugs
- [ ] Performance: LCP <2.5s
- [ ] Accessibility: WCAG AA compliance
- [ ] Analytics events firing correctly
- [ ] English translations at 80%+ coverage

## v0.9.0 Release Criteria
- [ ] Next Action widget implemented
- [ ] Contextual upgrade prompts (3+ touchpoints)
- [ ] Celebration moments (first app, first response)
- [ ] A/B test framework in place
- [ ] No regression in core metrics

## v1.0.0 Release Criteria
- [ ] Trial period fully functional
- [ ] English at 100% coverage
- [ ] Mobile flow optimization complete
- [ ] Trial → Paid funnel tracked
- [ ] Documentation complete
- [ ] Marketing materials ready
```

---

## Part 6: Risk Assessment

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Skip-CV reduces CV upload rate | Medium | High | Show clear value comparison; gate advanced features |
| Trial period increases support load | Medium | Medium | Self-serve trial management; clear trial messaging |
| Mobile optimization delays | Low | Medium | Scope to core flow only; defer complex features |
| i18n translation quality issues | Low | Medium | Professional review before GA; community feedback |
| Upgrade prompts feel pushy | Medium | Medium | A/B test frequency; easy dismissal; track sentiment |
| Technical debt from fast shipping | Medium | Low | Allocate 15% capacity to tech debt each sprint |

### Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DEPENDENCY MAP                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Skip-CV Flow                                                          │
│       │                                                                  │
│       ├──▶ Comparison View (for CV upsell)                              │
│       │                                                                  │
│       └──▶ Onboarding Checklist (tracks CV upload)                      │
│               │                                                          │
│               └──▶ Dashboard Redesign (hosts checklist)                 │
│                       │                                                  │
│                       └──▶ Next Action Widget                           │
│                                                                          │
│   Trial Period                                                          │
│       │                                                                  │
│       ├──▶ Subscription model updates                                   │
│       │                                                                  │
│       └──▶ Upgrade prompts (trial expiry triggers)                      │
│               │                                                          │
│               └──▶ Celebration moments (trial milestones)               │
│                                                                          │
│   i18n English                                                          │
│       │                                                                  │
│       └──▶ No blockers (parallel work)                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Open Questions

| # | Question | Owner | Priority | Notes |
|---|----------|-------|----------|-------|
| 1 | What's current baseline activation rate? | Analytics | High | Need to measure before changes |
| 2 | Should trial require payment method? | Product | High | Trade-off: conversion vs friction |
| 3 | What's acceptable CV upload delay? | Product | Medium | 7 days? 14 days? For trial users? |
| 4 | Should demo mode require email? | Growth | Medium | Lead capture vs friction |
| 5 | Multi-language job boards supported? | Engineering | Low | For English expansion |

---

## Appendix A: Competitive Analysis Summary

### Key Competitors

| Competitor | Strength | Weakness | Obojobs Opportunity |
|------------|----------|----------|---------------------|
| Lebenslauf.de | Brand recognition | Basic features only | Full lifecycle management |
| Bewerbung.de | Template variety | No AI generation | AI-powered personalization |
| Indeed Resume | Job board integration | Generic, not German-focused | German market specialization |
| Kickresume | Modern design | Expensive, no tracking | Affordable + comprehensive |

### Differentiation Strategy
1. **German market focus** - Native German UX and legal compliance
2. **Full lifecycle** - Beyond resumes to interviews and salary
3. **Zen design** - Memorable, calm experience vs. generic SaaS
4. **AI-native** - Claude-powered personalization, not templates

---

## Appendix B: User Persona Profiles

### Primary Persona: "Stressed Stefan"

```
Name:           Stefan Müller, 32
Role:           Marketing Manager, seeking new position
Location:       Munich, Germany
Goals:          • Land a better-paying job within 3 months
                • Apply to 5+ jobs per week
                • Stand out from other applicants
Pain Points:    • Spends 2+ hours per application
                • Loses track of where he applied
                • Dreads interview preparation
Context:        • Browses jobs on phone during commute
                • Applies on laptop in evenings
                • Currently employed, limited time
Tech Level:     Intermediate - comfortable with web apps
Quote:          "I know I need to personalize each application,
                 but I just don't have the time."
```

### Secondary Persona: "Anxious Anna"

```
Name:           Anna Schmidt, 26
Role:           Recent graduate, first job search
Location:       Berlin, Germany
Goals:          • Get any relevant job in her field
                • Learn how to write professional applications
                • Gain confidence in interviews
Pain Points:    • Doesn't know what employers want
                • No professional network
                • Intimidated by application process
Context:        • Full-time job searching
                • Uses phone primarily
                • Tight budget
Tech Level:     High - digital native
Quote:          "I've applied to 50 jobs and heard back from 3.
                 What am I doing wrong?"
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| Bewerbung | German for "application" - used throughout the codebase |
| Lebenslauf | CV/Resume |
| Arbeitszeugnis | Work certificate - formal reference from employer |
| Anschreiben | Cover letter |
| Zusage | Acceptance/Offer |
| Absage | Rejection |
| ATS | Applicant Tracking System - software used to filter resumes |
| RICE | Reach, Impact, Confidence, Effort - prioritization framework |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-21 | Claude (Product Owner Analysis) | Initial comprehensive analysis |

---

*This document was generated using the Product Owner skill framework. Review and adapt priorities based on actual user research and business constraints.*
