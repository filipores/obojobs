# obojobs (obo) - AI-Powered Job Application Platform

German-language SaaS: Upload CV, paste job URL, AI generates personalized cover letter (Anschreiben) as PDF + email-ready content. "Bewerbungen, die sich selbst schreiben."

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vue 3 (Composition API, `<script setup>`), JavaScript (NOT TypeScript), Vite 5 |
| **Backend** | Python 3.11, Flask 3.1, Flask-SQLAlchemy |
| **Database** | SQLite (dev), PostgreSQL 15 (prod) |
| **AI** | Qwen (Together.xyz) for generation, Claude (Anthropic) for analysis |
| **Auth** | JWT (Flask-JWT-Extended), Google OAuth |
| **Payments** | Stripe (checkout, portal, webhooks) |
| **Styling** | Custom CSS "Wafu Design" (Japanese-inspired), no CSS framework |
| **Deploy** | Docker Compose, Caddy (reverse proxy), Gunicorn |

## Quick Start

```bash
make install        # Install all deps (frontend npm + backend venv/pip)
make dev            # Start frontend (port 3000) + backend (port 5002)
make test           # Run all tests (Vitest + Pytest)
make lint           # Run all linters (ESLint + Ruff)
```

## Detailed Documentation (docs/)

| Document | Contents |
|----------|----------|
| **[docs/architecture.md](docs/architecture.md)** | Backend layers, app factory, blueprints, middleware, service layer, config, request flow |
| **[docs/domain-model.md](docs/domain-model.md)** | 15 SQLAlchemy models with all columns, relationships, enums, naming conventions |
| **[docs/ai-features.md](docs/ai-features.md)** | Qwen + Claude providers, 5-phase pipeline, prompt constraints, token limits |
| **[docs/frontend-patterns.md](docs/frontend-patterns.md)** | Vue conventions, stores, API client, routing, composables, design system |
| **[docs/api-reference.md](docs/api-reference.md)** | All REST endpoints, auth methods, rate limiting, response format |
| **[docs/testing-guide.md](docs/testing-guide.md)** | Pytest/Vitest setup, fixtures, CI pipeline, pre-commit hooks |
| **[docs/deployment.md](docs/deployment.md)** | Dev/Docker/Prod setup, env vars, Caddy config, migrations |

## Key Conventions

- **German-first**: UI, DB fields (`firma`, `position`, `ansprechpartner`, `betreff`, `einleitung`), status values (`erstellt`, `versendet`, `absage`, `zusage`), error messages
- **Service layer**: Business logic in `services/`, routes are thin controllers
- **Auth decorators**: `@jwt_required_custom` injects `current_user` into kwargs
- **Composition API only**: `<script setup>`, `reactive()` stores (no Vuex/Pinia), `<style scoped>`
- **Conventional commits**: Enforced via commitlint + semantic-release on main
- **No TypeScript**: JavaScript only (one exception: `data/variableDescriptions.ts`)

## Core Business Flow

1. Upload CV (PDF) -> skills auto-extracted via AI
2. Paste job URL -> web scraper extracts job details
3. AI generates personalized Anschreiben (Qwen via Together.xyz)
4. PDF generated + email subject/body
5. Track lifecycle: erstellt -> versendet -> antwort_erhalten -> absage/zusage

## Subscription Tiers

| Plan | Limit | Price |
|------|-------|-------|
| Free | 3/month | 0 EUR |
| Basic | 20/month | 9.99 EUR/month |
| Pro | Unlimited | 19.99 EUR/month |

## Project Structure

```
obojobs/
├── frontend/src/          # Vue 3 SPA (26 pages, 23+ components, 7 composables)
├── backend/
│   ├── app.py             # Flask app factory
│   ├── models/            # 15 SQLAlchemy models
│   ├── routes/            # 17 Flask Blueprints (/api/*)
│   ├── services/          # 31 service files (business logic)
│   └── middleware/        # Auth, security, subscription limits
├── extension/             # Chrome extension (Manifest V3)
├── docs/                  # Detailed documentation (see table above)
├── docker-compose.prod.yml
├── Caddyfile
└── Makefile               # Central task runner
```
