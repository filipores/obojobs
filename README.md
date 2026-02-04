# obojobs

An AI-powered job application automation platform that generates personalized cover letters and optimizes CVs using Claude AI.

## Overview

obojobs streamlines the job application process by automatically generating tailored cover letters and optimizing resumes for specific job postings. The platform uses Anthropic's Claude API to create compelling, personalized application materials that help job seekers stand out.

## Key Features

- **AI-Generated Cover Letters** - Create personalized, compelling cover letters tailored to specific job postings
- **CV Optimization** - Analyze and optimize your resume for each application
- **Template System** - Customizable templates with variable substitution (`{{FIRMA}}`, `{{POSITION}}`, etc.)
- **Chrome Extension** - Scrape job postings directly from job boards
- **Document Management** - Upload and manage your CVs, certificates, and other documents
- **PDF Generation** - Export professional application documents as PDFs
- **Subscription Plans** - Free, Basic, and Pro tiers with Stripe integration

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue.js 3, Vite, Vue Router, Axios |
| Backend | Python 3.11+, Flask, SQLAlchemy |
| Database | SQLite (development) / PostgreSQL (production) |
| AI | Anthropic Claude API (Claude 3.5 Haiku) |
| Payments | Stripe |
| Testing | Vitest (frontend), Pytest (backend), Playwright (E2E) |
| Linting | ESLint (frontend), Ruff (backend) |
| Deployment | Docker, Gunicorn, Nginx |

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker** (optional, for containerized deployment)
- **Anthropic API Key** (required for AI features)
- **Stripe API Keys** (optional, for payment features)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/obojobs.git
cd obojobs
```

### 2. Install dependencies

```bash
make install
```

This installs both frontend (npm) and backend (pip) dependencies.

### 3. Configure environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and set:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Security (change in production)
SECRET_KEY=your-secret-key-minimum-32-characters
JWT_SECRET_KEY=your-jwt-secret-key

# Optional
DATABASE_URL=postgresql://user:pass@localhost/obojobs
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### 4. Start development servers

```bash
make dev
```

This starts both servers:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5001

### Development Test Credentials

In development mode, a test user is automatically created:
- **Email**: `test@example.com`
- **Password**: `Test1234!`

## Development

### Available Commands

Run `make help` to see all available commands:

```bash
# Development
make install        # Install all dependencies
make dev            # Start frontend + backend
make dev-frontend   # Start only frontend (Vite)
make dev-backend    # Start only backend (Flask)

# Build & Test
make build          # Build frontend for production
make test           # Run all tests
make test-frontend  # Frontend tests (Vitest)
make test-backend   # Backend tests (Pytest)
make lint           # Linting (frontend + backend)
make lint-fix       # Lint and auto-fix

# Database
make db-migrate m="message"  # Create new migration
make db-upgrade              # Apply migrations
make db-downgrade            # Rollback last migration
make db-reset                # Reset database

# Docker
make docker-build   # Build Docker images
make docker-up      # Start containers
make docker-down    # Stop containers

# Utilities
make logs           # View backend logs
make clean          # Delete build artifacts
```

### Project Structure

```
obojobs/
├── frontend/               # Vue.js 3 application
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── composables/    # Vue composables
│   │   ├── api/            # API client (Axios)
│   │   └── assets/         # Styles and static files
│   └── package.json
├── backend/                # Flask API
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic
│   ├── middleware/         # Auth, rate limiting
│   └── requirements.txt
├── extension/              # Chrome extension
├── docker-compose.yml
└── Makefile
```

## Testing

### Backend (Python)

```bash
# Run all tests
make test-backend

# Or directly with pytest
cd backend && source venv/bin/activate && pytest -v

# With coverage
pytest --cov=backend
```

### Frontend (Vue.js)

```bash
# Run all tests
make test-frontend

# Watch mode
cd frontend && npm run test:watch

# With coverage
cd frontend && npm run test:coverage
```

### End-to-End (Playwright)

```bash
cd frontend && npm run test:e2e

# With UI
npm run test:e2e:ui
```

## Docker Deployment

### Build and run with Docker Compose

```bash
# Build images
make docker-build

# Start containers
make docker-up

# View logs
make docker-logs

# Stop containers
make docker-down
```

### Production Configuration

For production, ensure these environment variables are set:

```env
DEBUG=False
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@host/dbname
CORS_ORIGINS=https://yourdomain.com
FORCE_HTTPS=true
```

## API Documentation

### Authentication

The API uses JWT tokens for web authentication and API keys for the Chrome extension:

- **Web App**: JWT tokens (1h access, 7d refresh)
- **Extension**: API key via `X-API-Key` header

### Response Format

All API endpoints return a consistent JSON format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional status message"
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error description"
}
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Code style and conventions
- Submitting pull requests
- Reporting bugs
- Requesting features

### Development Guidelines

- **Language**: The UI and database use German terminology
- **API Format**: Follow the standard response format
- **Testing**: Write tests for new features
- **Linting**: Run `make lint` before committing

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Built with Vue.js, Flask, and Claude AI
