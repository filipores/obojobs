# obojobs

A full-stack AI-powered job application platform that generates personalized cover letters using Claude AI.

## What It Does

obojobs automates the tedious parts of job applications. Users upload their CV, paste a job posting URL, and the platform generates a tailored cover letter in seconds — matching the company's tone, highlighting relevant experience, and exporting as a professional PDF.

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | Vue.js 3, Vite, Vue Router |
| **Backend** | Python, Flask, SQLAlchemy, JWT Auth |
| **AI** | Anthropic Claude API |
| **Payments** | Stripe (subscriptions + webhooks) |
| **Database** | SQLite / PostgreSQL |
| **Testing** | Vitest, Pytest, Playwright (E2E) |
| **DevOps** | Docker, GitHub Actions, Semantic Release |

## Architecture Highlights

- **Clean separation** — Vue SPA frontend with Flask REST API backend
- **JWT + API Key auth** — Web app uses JWT tokens, Chrome extension uses API keys
- **Template engine** — Custom variable substitution system (`{{FIRMA}}`, `{{POSITION}}`, etc.)
- **PDF generation** — Server-side PDF rendering with customizable templates
- **Stripe integration** — Full subscription flow with webhook handling
- **Chrome extension** — Scrapes job postings directly from job boards

## Code Quality

- Comprehensive test suites (unit + E2E)
- ESLint + Ruff for consistent code style
- Pre-commit hooks with Husky
- Automated semantic versioning
- CI/CD pipeline with GitHub Actions

## Project Structure

```
obojobs/
├── frontend/           # Vue.js 3 SPA
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── composables/# Vue composition API hooks
│   │   ├── pages/      # Route views
│   │   └── api/        # Axios API client
│   └── tests/
├── backend/            # Flask REST API
│   ├── models/         # SQLAlchemy models
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic (AI, PDF, payments)
│   └── tests/
├── extension/          # Chrome extension
└── docker-compose.yml
```

## Run Locally

```bash
# Install dependencies
make install

# Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY

# Start dev servers
make dev
# Frontend: http://localhost:3000
# Backend: http://localhost:5001
```

## Contact

**Filip Ores**
[filip.ores@hotmail.com](mailto:filip.ores@hotmail.com)
