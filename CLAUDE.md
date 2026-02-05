# obojobs (obo) - AI-Powered Job Application Platform

## What is this?

German-language SaaS platform that automates job applications. Users upload their CV, paste a job posting URL, and the platform generates a personalized cover letter (Anschreiben) using Claude AI, exports it as PDF, and provides email-ready content. Tagline: "Bewerbungen, die sich selbst schreiben."

**Target market**: German-speaking job seekers. German is the primary language; English is a secondary locale.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vue 3 (Composition API, `<script setup>`), JavaScript, Vite 5 |
| **Backend** | Python 3.11, Flask 3.1, Flask-SQLAlchemy |
| **Database** | SQLite (dev), PostgreSQL 15 (prod) |
| **AI** | Anthropic Claude API (claude-3-5-haiku model) |
| **Auth** | JWT (Flask-JWT-Extended), Google OAuth |
| **Payments** | Stripe (checkout, portal, webhooks) |
| **PDF** | PyPDF2, PyMuPDF, reportlab, pytesseract (OCR) |
| **Styling** | Custom CSS design system ("Wafu Design" - Japanese-inspired), no CSS framework |
| **Testing** | Vitest + Playwright (frontend), Pytest (backend) |
| **Linting** | ESLint 9 (frontend), Ruff (backend) |
| **CI/CD** | GitHub Actions, semantic-release |
| **Deploy** | Docker Compose, Caddy (reverse proxy), Gunicorn |

**Important**: This project uses **JavaScript, NOT TypeScript**. Only one .ts file exists (`data/variableDescriptions.ts`).

## Project Structure

```
obojobs/
├── frontend/                 # Vue 3 SPA
│   ├── src/
│   │   ├── main.js           # App entry, mounts plugins (router, i18n)
│   │   ├── App.vue           # Root component (nav, sidebar, footer, theme)
│   │   ├── api/client.js     # Axios instance, interceptors, auth header
│   │   ├── assets/styles.css # Global design system (1500+ lines)
│   │   ├── components/       # 23+ reusable components + subdirs
│   │   ├── composables/      # Vue composable hooks (5 files)
│   │   ├── pages/            # 23 route-level page components
│   │   ├── router/index.js   # Route definitions + auth guards
│   │   ├── store/auth.js     # Reactive auth state (no Vuex/Pinia)
│   │   ├── stores/demo.js    # Demo flow state (sessionStorage)
│   │   ├── i18n/             # vue-i18n setup, locales/de.json + en.json
│   │   └── utils/            # Error translation helper
│   ├── e2e/                  # Playwright E2E tests
│   └── src/__tests__/        # Vitest unit tests
├── backend/
│   ├── app.py                # Flask app factory (create_app)
│   ├── config.py             # Config from env vars
│   ├── wsgi.py               # Gunicorn entry point
│   ├── models/               # 14 SQLAlchemy models
│   ├── routes/               # 15 Flask Blueprints (/api/*)
│   ├── services/             # 30 service files (business logic)
│   ├── middleware/            # Auth, security headers, subscription limits
│   ├── migrations/           # Alembic DB migrations
│   ├── i18n/                 # Backend i18n (de/en JSON)
│   ├── tests/                # 25 Pytest test files
│   └── uploads/              # User file storage
├── extension/                # Chrome extension (Manifest V3)
├── ralph/                    # Custom AI testing/automation agent (bash)
├── scripts/                  # CI helper scripts
├── docker-compose.yml        # Dev Docker setup
├── docker-compose.prod.yml   # Prod Docker setup (Caddy + PostgreSQL)
├── Caddyfile                 # Reverse proxy config
├── Makefile                  # Central task runner (German help text)
└── package.json              # Root-level DevOps tools only (husky, commitlint, semantic-release)
```

## Development Setup

```bash
make install        # Install all deps (frontend npm + backend venv/pip)
make dev            # Start both frontend + backend in parallel
make dev-frontend   # Vite dev server on port 3000
make dev-backend    # Flask dev server on port 5001
```

Frontend proxies `/api` requests to `http://127.0.0.1:5001` via Vite config.

**Environment files**: Copy `.env.example` in root and `backend/` and `frontend/` directories. Key vars:
- `ANTHROPIC_API_KEY` (required for AI features)
- `SECRET_KEY`, `JWT_SECRET_KEY` (auth)
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` (payments)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (OAuth)
- `DATABASE_URL` (defaults to SQLite)

## Key Commands

```bash
make test           # Run all tests (Vitest + Pytest)
make lint           # Run all linters (ESLint + Ruff)
make lint-fix       # Auto-fix lint issues
make db-migrate m="description"  # Create new migration
make db-upgrade     # Apply migrations
make db-reset       # Reset database
make docker-build   # Build Docker images
make docker-up      # Start Docker containers
npm run ci:local    # Run full CI pipeline locally
```

## Architecture Patterns

### Backend

- **App Factory**: `create_app()` in `app.py`
- **Blueprints**: Each domain area is a separate Blueprint under `routes/`
- **Service Layer**: Business logic lives in `services/`, routes are thin controllers
- **Decorator Auth**: `@jwt_required_custom` injects `current_user` into route kwargs
- **API Key Auth**: `@api_key_required` for Chrome extension (X-API-Key header)
- **Subscription Middleware**: `@subscription_limit` checks monthly application limits

### Frontend

- **Composition API only**: All components use `<script setup>`, no Options API
- **Reactive stores**: `reactive()` objects instead of Vuex/Pinia
- **SFC pattern**: `<template>` + `<script setup>` + `<style scoped>`
- **Lazy-loaded routes**: `() => import(...)` for code splitting
- **Global toast**: `window.$toast()` for notifications
- **Inline SVG**: No icon library, all icons are inline SVG
- **Path alias**: `@` maps to `frontend/src/`

## Domain Model (14 Models)

| Model | Purpose |
|-------|---------|
| **User** | Core user, auth, Stripe, Google OAuth, language pref, usage tracking |
| **Document** | Uploaded CVs and work references (PDFs) |
| **Template** | Cover letter templates with `{{VARIABLE}}` placeholders |
| **Application** | Generated applications with full lifecycle tracking |
| **Subscription** | Stripe subscription (free/basic/pro plans) |
| **APIKey** | Chrome extension auth keys (`mlr_` prefix) |
| **TokenBlacklist** | JWT revocation |
| **ATSAnalysis** | ATS compatibility scan results |
| **EmailAccount** | Connected Gmail/Outlook accounts (encrypted tokens) |
| **UserSkill** | Skills extracted from CV (technical, soft, languages, tools, certs) |
| **JobRequirement** | Requirements extracted from job postings (must-have, nice-to-have) |
| **InterviewQuestion** | AI-generated interview prep questions |
| **JobRecommendation** | Job recommendations with fit scores |
| **SalaryCoachData** | Salary research and negotiation data |

## Core Business Flow

1. **Upload CV** (PDF) -> skills auto-extracted
2. **Paste job URL** or text -> web scraper extracts job details
3. **Claude AI generates** personalized cover letter intro
4. **Template variables** substituted: `{{FIRMA}}`, `{{POSITION}}`, `{{ANSPRECHPARTNER}}`, `{{QUELLE}}`, `{{EINLEITUNG}}`
5. **PDF generated** + email subject/body text
6. **Track application** lifecycle: erstellt -> versendet -> antwort_erhalten -> absage/zusage

## Subscription Tiers

| Plan | Limit | Price |
|------|-------|-------|
| Free | 3 applications/month | 0 EUR |
| Basic | 20 applications/month | 9.99 EUR/month |
| Pro | Unlimited | 19.99 EUR/month |

## AI-Powered Features

All AI calls use Anthropic Claude API (`claude-3-5-haiku-20241022`):
- Cover letter generation (BewerbungsGenerator - 5-phase pipeline)
- ATS analysis and optimization
- Interview question generation + answer evaluation
- STAR method analysis
- Skill extraction from CVs
- Salary research + negotiation coaching
- Job recommendation scoring
- Requirement analysis from job postings
- Company research

## External Integrations

- **Anthropic Claude API** - All AI features
- **Stripe** - Subscription payments (checkout, portal, webhooks)
- **Google OAuth** - Social login
- **Gmail API** - Send applications via email
- **Outlook/MSAL** - Send applications via email
- **Web scraping** (BeautifulSoup) - Job posting and company research

## Important Conventions

- **German-first**: UI defaults to German, DB field names are German (firma, position, ansprechpartner, betreff, einleitung, notizen), status values are German (erstellt, versendet, absage, zusage)
- **i18n partial**: vue-i18n is set up but some strings are still hardcoded in German
- **Error messages**: Backend returns German error messages, frontend has EN->DE translation layer
- **Conventional commits**: Enforced via commitlint (feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert)
- **Semantic release**: Automated versioning from commit messages on main branch
- **Pre-commit hooks**: Husky + lint-staged runs ESLint (frontend) and Ruff (backend)
- **No TypeScript**: Project is JavaScript-only (except one data file)
- **CSS design system**: Custom "Wafu Design" with Japanese-inspired tokens (washi, sumi, ai colors), no Tailwind/CSS framework
- **Dark mode**: CSS class `.dark-mode` on root, persisted in localStorage (`obojobs-theme`)
- **Locale**: Stored in localStorage (`obojobs-locale`), default "de"

## Testing

- **Frontend unit**: Vitest with jsdom, coverage thresholds (70% statements/branches/lines)
- **Frontend E2E**: Playwright (Chromium), config at `frontend/playwright.config.ts`
- **Backend**: Pytest with in-memory SQLite, coverage threshold 40% (CI) / 55% (local)
- **CI max warnings**: ESLint allows max 100 warnings

## API Structure

All routes under `/api/`. Key blueprints:
- `/api/auth` - Registration, login, OAuth, email verification, password reset
- `/api/applications` - Core CRUD + generation + ATS + interview features (largest route file)
- `/api/documents` - Document upload/management
- `/api/templates` - Template CRUD + PDF template wizard
- `/api/subscriptions` - Stripe checkout and portal
- `/api/webhooks` - Stripe webhook handling
- `/api/keys` - API key management for Chrome extension
- `/api/ats` - ATS analysis
- `/api/email` - Gmail/Outlook OAuth and email sending
- `/api/companies` - Company research
- `/api/salary` - Salary coaching
- `/api/demo` - Demo generation (anonymous)

## Rate Limiting

- Global: 200/hour, 50/minute (Flask-Limiter, in-memory)
- Email verification: 3/hour
- Password reset: 3/hour
- Whitelisted IPs exempt via `RATE_LIMIT_WHITELIST`

## Deployment

- **Dev**: Vite (port 3000) + Flask (port 5001), SQLite, Vite proxy for `/api`
- **Prod**: Docker Compose with Caddy (auto HTTPS) -> Nginx (Vue SPA) + Gunicorn (Flask) + PostgreSQL
- **Backend deps**: tesseract-ocr (German), poppler-utils (PDF processing)
