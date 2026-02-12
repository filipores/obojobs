# Backend Architecture

## Overview

Flask-based REST API with app factory pattern, blueprint-based routing, service layer for business logic, and SQLAlchemy ORM. All routes under `/api/`.

## Layer Diagram

```
Request
  |
  v
[Flask App]  (app.py - create_app())
  |
  +-- ProxyFix (trusts X-Forwarded-For from Caddy)
  +-- CORS (configurable origins)
  +-- Flask-Limiter (200/hour, 50/minute, fixed-window)
  +-- JWTManager (flask_jwt_extended)
  +-- Security Headers (after_request middleware, prod only)
  |
  v
[Middleware Decorators]  (middleware/)
  |  @jwt_required_custom   -> injects current_user into kwargs
  |  @api_key_required      -> X-API-Key header (Chrome extension)
  |  @admin_required        -> wraps jwt_required_custom + is_admin check
  |  @check_subscription_limit -> atomic limit check + counter increment
  |
  v
[Routes / Blueprints]  (routes/)  -- thin controllers
  |  Parse request, call service, return JSON
  |
  v
[Services]  (services/)  -- business logic
  |  BewerbungsGenerator, SkillExtractor, WebScraper, ...
  |
  v
[Models]  (models/)  -- SQLAlchemy ORM (15 models)
  |
  v
[Database]  SQLite (dev) / PostgreSQL (prod)
```

## App Factory (`backend/app.py`)

`create_app()` is the single entry point. It:

1. Creates Flask app with `ProxyFix` for reverse proxy
2. Loads config from `Config` object (`config.py`)
3. Initializes extensions: `db`, `migrate`, `CORS`, `JWTManager`
4. Registers JWT error handlers (all return German error messages)
5. Registers JWT token blacklist callback (`TokenBlacklist.is_token_blacklisted`)
6. Configures rate limiter with IP whitelist exemption
7. Initializes security headers middleware
8. Registers 17 blueprints with `/api/` prefix
9. Starts background scheduler (APScheduler)
10. Adds `/api/health` and `/api/version` endpoints (rate-limit exempt)

```python
# Entry points:
# Dev:  python app.py          -> runs init_database + seed_test_data
# Prod: wsgi.py via Gunicorn   -> runs init_database (no seed)
```

## Blueprint Registration

| Blueprint | URL Prefix | Module |
|-----------|-----------|--------|
| `auth_bp` | `/api/auth` | `routes/auth.py` |
| `demo_bp` | `/api/demo` | `routes/demo.py` |
| `documents_bp` | `/api/documents` | `routes/documents.py` |
| `templates_bp` | `/api/templates` | `routes/templates.py` |
| `applications_bp` | `/api/applications` | `routes/applications/` (sub-package) |
| `api_keys_bp` | `/api/keys` | `routes/api_keys.py` |
| `stats_bp` | `/api` | `routes/stats.py` |
| `subscriptions_bp` | `/api/subscriptions` | `routes/subscriptions.py` |
| `ats_bp` | `/api/ats` | `routes/ats.py` |
| `email_bp` | `/api/email` | `routes/email.py` |
| `webhooks_bp` | `/api/webhooks` | `routes/webhooks.py` |
| `skills_bp` | `/api` | `routes/skills.py` |
| `companies_bp` | `/api/companies` | `routes/companies.py` |
| `recommendations_bp` | `/api` | `routes/recommendations.py` |
| `salary_bp` | `/api/salary` | `routes/salary.py` |
| `legal_bp` | `/api/legal` | `routes/legal.py` |
| `admin_bp` | `/api/admin` | `routes/admin.py` |

The `applications` blueprint is a **sub-package** split into modules:
- `crud.py` - CRUD operations
- `generation.py` - Application generation (from URL, text, extension)
- `export.py` - PDF export
- `ats.py` - ATS analysis endpoints
- `interview.py` - Interview prep endpoints
- `requirements.py` - Job requirement analysis

## Middleware Layer (`backend/middleware/`)

### `@jwt_required_custom` (`jwt_required.py`)
Custom decorator that verifies JWT and **injects `current_user`** into kwargs:
```python
@jwt_required_custom
def my_route(current_user):  # <-- injected User model instance
    ...
```
- Calls `verify_jwt_in_request()` from flask_jwt_extended
- Looks up `User` by JWT identity (int user_id)
- Returns 401 if user not found or `is_active=False`

### `@api_key_required` (`api_key_required.py`)
For Chrome extension requests via `X-API-Key` header:
- Looks up `APIKey` by prefix (first 8 chars)
- Verifies full key hash via `api_key_obj.check_key()`
- Updates `last_used_at` timestamp
- Injects `current_user` into kwargs (same interface as JWT)

### `@admin_required` (`admin_required.py`)
Wraps `@jwt_required_custom` and checks `current_user.is_admin`:
```python
@admin_required
def admin_endpoint(current_user):  # current_user guaranteed to be admin
    ...
```

### `@check_subscription_limit` (`subscription_limit.py`)
**Atomic** limit check + counter increment to prevent TOCTOU races:
- Uses raw SQL `UPDATE ... WHERE count < limit` for atomicity
- Automatically decrements counter if wrapped function raises exception
- Plan limits: Free=3, Basic=20, Pro=unlimited
- Monthly counter resets on first day of each month

### Security Headers (`security_headers.py`)
`after_request` middleware (production only unless `SECURITY_HEADERS_ENABLED=true`):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` with `unsafe-inline` (Vue 3 scoped styles)
- `Permissions-Policy` (all features disabled)
- `Strict-Transport-Security` (only over HTTPS)

## Service Layer (`backend/services/`)

Services contain all business logic. Routes are thin controllers that parse requests and call services.

| Service | Purpose |
|---------|---------|
| `generator.py` | `BewerbungsGenerator` - 5-phase application pipeline |
| `qwen_client.py` | `QwenAPIClient` - LLM API calls (Together.xyz / Qwen) |
| `api_client.py` | Legacy Anthropic Claude API client |
| `web_scraper.py` | `WebScraper` - job posting scraping (BeautifulSoup) |
| `pdf_handler.py` | PDF creation (reportlab), text extraction (PyMuPDF/PyPDF2/OCR) |
| `skill_extractor.py` | `SkillExtractor` - CV skill extraction via AI |
| `profile_extractor.py` | `ProfileExtractor` - contact data extraction from CV |
| `contact_extractor.py` | `ContactExtractor` - contact info from job postings |
| `requirement_analyzer.py` | `RequirementAnalyzer` - job requirement extraction |
| `ats_service.py` | `ATSService` - ATS compatibility analysis |
| `ats_optimizer.py` | `ATSOptimizer` - ATS optimization suggestions |
| `interview_generator.py` | AI interview question generation |
| `interview_evaluator.py` | AI answer evaluation (STAR method) |
| `star_analyzer.py` | STAR method analysis |
| `job_recommender.py` | `JobRecommender` - job search + recommendations |
| `job_fit_calculator.py` | `JobFitCalculator` - skill-requirement matching score |
| `salary_coach.py` | Salary research + negotiation coaching |
| `company_researcher.py` | Company research via web scraping |
| `bundesagentur_client.py` | Bundesagentur fuer Arbeit API client |
| `auth_service.py` | User registration, login, Google OAuth |
| `email_service.py` | SMTP email sending |
| `email_verification_service.py` | Email verification token handling |
| `password_reset_service.py` | Password reset flow |
| `password_validator.py` | Password strength validation |
| `gmail_service.py` | Gmail API integration |
| `outlook_service.py` | Outlook/MSAL integration |
| `stripe_service.py` | Stripe checkout, portal, subscription management |
| `demo_generator.py` | Demo application generation (no auth) |
| `tracker.py` | Application status tracking |
| `scheduler.py` | APScheduler background jobs |

## Background Scheduler (`services/scheduler.py`)

APScheduler with 2 jobs:
- **Cleanup old recommendations**: daily at 3:00 AM (removes >30 day old records)
- **Auto-search jobs**: every 6 hours (finds jobs for users with skills)

Disabled in testing mode (`TESTING=true`). Registered via `atexit` for graceful shutdown.

## Configuration (`backend/config.py`)

Single `Config` class loaded from environment variables (`.env` in project root).

Key settings:
- `CLAUDE_MODEL`: `claude-3-5-haiku-20241022`
- `QWEN_MODEL`: `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` (via Together.xyz)
- `MAX_TOKENS`: 300 (extraction), `QWEN_ANSCHREIBEN_MAX_TOKENS`: 1200 (generation)
- `TEMPERATURE`: 0.7 / `QWEN_ANSCHREIBEN_TEMPERATURE`: 0.65
- `ALLOWED_EXTENSIONS`: `{"pdf"}` -- only PDFs allowed
- `MAX_CONTENT_LENGTH`: 10 MB
- `JWT_ACCESS_TOKEN_EXPIRES`: 1 hour, refresh: 7 days

Production secret validation: raises `ValueError` if default secrets are used with `FLASK_ENV=production`.

## Request Flow Example: Generate Application from URL

```
POST /api/applications/generate-from-url
  |
  @jwt_required_custom          -> verify JWT, inject current_user
  @check_subscription_limit     -> atomic: check limit + increment counter
  |
  Route: parse request JSON (url, company, title, tone, ...)
  |
  WebScraper.fetch_structured_job_posting(url)  -> scrape job page
  |
  BewerbungsGenerator(user_id)
    .prepare()                  -> load User + Documents from DB
    .generate_bewerbung(...)
      |
      Phase 1: Read job posting (URL scrape or user text)
      Phase 2: Extract details (position, contact, source) via AI
      Phase 3: Generate Anschreiben body via AI (Qwen)
      Phase 4: Build PDF (briefkopf + body -> reportlab)
      Phase 5: Generate email subject + body via AI
      |
      Save Application to DB (status="erstellt")
      Extract JobRequirements in background
  |
  JobFitCalculator.calculate_job_fit()  -> skill matching score
  |
  Return JSON: { success, application, pdf_path, usage }
```

## Rate Limiting

Flask-Limiter with in-memory storage (fixed-window strategy):
- Global: 200/hour, 50/minute
- Whitelisted IPs exempt (`RATE_LIMIT_WHITELIST`, default: `127.0.0.1`)
- Health/version endpoints exempt via `@limiter.exempt`
- Per-endpoint limits set via `app.limiter.limit()` in specific routes

## Error Handling Pattern

All error messages are in **German** (target audience: German job seekers):
```python
return jsonify({"error": "Ungültiger oder inaktiver Benutzer"}), 401
return jsonify({"success": False, "error": "URL ist erforderlich"}), 400
```

Standard response format:
- Success: `{"success": True, "data": ..., "message": "..."}`
- Error: `{"success": False, "error": "German error message"}` or `{"error": "..."}`

## File Storage

```
uploads/
  user_{id}/
    documents/     # lebenslauf.txt, lebenslauf.pdf, arbeitszeugnis.txt, ...
    pdfs/          # Anschreiben_FirmaName.pdf
```

PDFs are uploaded, text extracted via PyMuPDF/PyPDF2/OCR, stored as `.txt` alongside original `.pdf`.
