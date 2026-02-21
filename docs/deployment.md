# Deployment

## Environments

| Environment | Frontend | Backend | Database | Proxy |
|-------------|----------|---------|----------|-------|
| **Dev** | Vite (port 3000) | Flask (port 5002) | SQLite (file) | Vite proxy |
| **Docker Dev** | Nginx (port 80) | Gunicorn (port 5002) | SQLite (volume) | -- |
| **Production** | Caddy serves static | Gunicorn (port 5002) | PostgreSQL 15 | Caddy (auto HTTPS) |

## Development Setup

```bash
# 1. Install dependencies
make install        # Frontend npm + Backend venv/pip

# 2. Configure environment
cp .env.example .env
# Edit .env with required keys (FIREWORKS_API_KEY at minimum)

# 3. Start dev servers
make dev            # Both frontend + backend in parallel
# OR individually:
make dev-frontend   # Vite on http://localhost:3000
make dev-backend    # Flask on http://localhost:5002
```

Frontend proxies `/api` requests to `http://127.0.0.1:5002` via Vite config.

### Required Environment Variables
- `FIREWORKS_API_KEY` -- required for AI features (Fireworks AI / Qwen + Kimi)
- `SECRET_KEY` -- Flask secret (default: dev value)
- `JWT_SECRET_KEY` -- JWT signing (default: same as SECRET_KEY)

### Optional Environment Variables
- `ANTHROPIC_API_KEY` -- for skill extraction, ATS, interview features
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` -- payments
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` -- Google OAuth
- `DATABASE_URL` -- defaults to SQLite
- `EMAIL_ENCRYPTION_KEY` -- for email account token encryption

## Docker Dev (`docker-compose.yml`)

```bash
make docker-build   # Build images
make docker-up      # Start containers
make docker-down    # Stop containers
make docker-logs    # Follow logs
```

Services:
- **backend**: Flask + Gunicorn, port 5002, SQLite in volume
- **frontend**: Nginx serving built Vue SPA, port 80

Volumes: `uploads` (user files), `database` (SQLite DB).

## Production (`docker-compose.prod.yml`)

### Architecture

```
Internet
  |
  v
[Caddy]  (auto HTTPS via Let's Encrypt)
  |
  +-- /api/*  --> [Backend: Gunicorn + Flask]  --> [PostgreSQL]
  |                                             --> [Redis]
  +-- /*      --> [Static files from /srv/frontend]
```

### Services

| Service | Image | Purpose |
|---------|-------|---------|
| `caddy` | `caddy:2-alpine` | Reverse proxy, auto HTTPS, static files, security headers |
| `frontend` | Custom (build-only) | Builds Vue SPA, copies to shared volume, exits |
| `backend` | Custom | Gunicorn + Flask API |
| `db` | `postgres:15-alpine` | PostgreSQL database |
| `redis` | `redis:7-alpine` | Rate limiting storage (shared across Gunicorn workers) |

### Deployment Commands

```bash
# Build and start
make docker-prod-build
make docker-prod-up

# Or directly:
docker compose -f docker-compose.prod.yml up -d --build

# Logs and management
make docker-prod-logs
make docker-prod-down
```

### Required Production Environment Variables

Set in `.env` at project root:

```bash
# Core
DOMAIN=yourdomain.com
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
DB_PASSWORD=<postgres-password>

# AI
FIREWORKS_API_KEY=<fireworks-api-key>
ANTHROPIC_API_KEY=<anthropic-api-key>

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
VITE_GOOGLE_CLIENT_ID=...

# Email encryption
EMAIL_ENCRYPTION_KEY=<fernet-key>

# Optional
REGISTRATION_ENABLED=true
APP_VERSION=1.0.0
COMPANY_NAME=obojobs
COMPANY_EMAIL=kontakt@obojobs.de
```

### Caddy Configuration (`Caddyfile`)

- Auto HTTPS via Let's Encrypt (domain from `$DOMAIN` env var)
- `/api/*` reverse proxied to `backend:5002`
- `/*` serves static files from `/srv/frontend` (built Vue SPA)
- SPA fallback: `try_files {path} /index.html`
- Aggressive caching for hashed assets (1 year, immutable)
- 7-day cache for images
- gzip + zstd compression
- Security headers (nosniff, DENY frame, strict referrer)
- www -> non-www redirect

### Health Checks

All services have Docker health checks:
- Backend: `curl -f http://localhost:5002/api/health`
- PostgreSQL: `pg_isready -U obojobs -d obojobs`
- Redis: `redis-cli ping`

### Production Security

- `FLASK_ENV=production` -- disables debug mode
- `FORCE_HTTPS=true` -- enables HSTS headers
- `SECURITY_HEADERS_ENABLED=true` -- enables CSP, X-Frame-Options, etc.
- Production secret validation: raises error if default secrets are used
- Rate limiting via Redis (shared across Gunicorn workers)

## Database Migrations

```bash
# Create new migration
make db-migrate m="add user phone field"

# Apply migrations
make db-upgrade

# Rollback last migration
make db-downgrade

# Reset database (DESTRUCTIVE)
make db-reset
```

Migrations managed by Flask-Migrate (Alembic) in `backend/migrations/`.

In production, migrations run via `flask db upgrade` in the Docker entrypoint.

## CI/CD

### GitHub Actions (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main, PRs | Run tests + linting |
| `release.yml` | Push to main | Semantic release (auto-version) |
| `deploy.yml` | Release created | Deploy to production |

### Semantic Release

Automated versioning from conventional commit messages on `main`:
- `feat:` -> minor version bump
- `fix:` -> patch version bump
- `BREAKING CHANGE:` -> major version bump

Configured in root `package.json` (semantic-release + commitlint).

## Backend Dependencies

System packages required (in Docker/production):
- `tesseract-ocr` + German language data (`tesseract-ocr-deu`) -- OCR for PDF text extraction
- `poppler-utils` -- PDF processing (pdftotext, pdfimages)
