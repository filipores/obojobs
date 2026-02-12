# Testing Guide

## Overview

| Layer | Tool | Config | Threshold |
|-------|------|--------|-----------|
| Frontend unit | Vitest + jsdom | `frontend/vitest.config.js` | 70% statements/branches/lines |
| Frontend E2E | Playwright (Chromium) | `frontend/playwright.config.ts` | -- |
| Backend | Pytest + in-memory SQLite | `backend/pytest.ini` | 40% (CI) / 55% (local) |
| Linting (FE) | ESLint 9 | `frontend/eslint.config.js` | max 100 warnings |
| Linting (BE) | Ruff | `backend/pyproject.toml` | 0 errors |

## Commands

```bash
# Run everything
make test           # Frontend + Backend tests
make lint           # ESLint + Ruff
make lint-fix       # Auto-fix lint issues

# Frontend only
make test-frontend          # Vitest (single run)
make test-frontend-watch    # Vitest (watch mode)
make test-frontend-coverage # Vitest with coverage report

# Backend only
make test-backend   # Pytest -v

# Full CI pipeline locally
npm run ci:local
```

## Backend Testing

### Setup (`backend/tests/conftest.py`)

Environment set before app import:
```python
os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
```

### Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `app` | function | Flask app with in-memory SQLite, creates/drops all tables |
| `client` | function | Flask test client |
| `test_user` | function | User dict with id, email, full_name, password |
| `auth_token` | function | JWT access token (calls login endpoint) |
| `auth_headers` | function | `{"Authorization": "Bearer <token>"}` |

### Test Structure
```
backend/tests/
  conftest.py          # Shared fixtures
  test_auth.py         # Auth routes
  test_documents.py    # Document upload/CRUD
  test_applications.py # Application CRUD
  test_models.py       # Model unit tests
  test_services.py     # Service unit tests
  test_structural_*.py # Architecture enforcement tests
  ...                  # 25+ test files
```

### Running Individual Tests
```bash
# From project root, using venv Python:
backend/venv/bin/python -m pytest backend/tests/test_auth.py -v
backend/venv/bin/python -m pytest backend/tests/test_auth.py::test_register -v
backend/venv/bin/python -m pytest backend -v --cov=. --cov-report=term-missing
```

### Mocking External Services
AI services (Claude, Qwen) should be mocked in tests. They require API keys that are set to dummy values in conftest.

```python
from unittest.mock import patch, MagicMock

@patch('services.skill_extractor.Anthropic')
def test_skill_extraction(mock_anthropic, client, auth_headers):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='[{"skill_name": "Python", ...}]')]
    mock_anthropic.return_value.messages.create.return_value = mock_response
    # ... test code
```

### Structural Tests
Architecture enforcement tests that validate import rules:
- `test_structural_routes_no_models.py` -- routes must not import models directly
- `test_structural_services_only_ai.py` -- Anthropic/OpenAI only in services/
- `test_structural_models_no_services.py` -- models must not import services or routes

These tests parse Python AST and check import statements.

## Frontend Testing

### Vitest Setup
```
frontend/src/__tests__/
  *.test.js            # Unit test files
```

Tests use jsdom environment. Components tested with Vue Test Utils.

### Running Tests
```bash
cd frontend
npm run test           # Single run
npm run test:watch     # Watch mode
npm run test:coverage  # With coverage thresholds
```

### E2E Testing (Playwright)
```bash
cd frontend
npx playwright test              # Run all E2E tests
npx playwright test --headed     # With visible browser
npx playwright show-report       # View test report
```

Config: `frontend/playwright.config.ts` (Chromium only).

### Ralph (Custom UI Testing)
Custom bash-based testing agent in `ralph/` directory:
```bash
make ralph         # Run tests
make ralph-headed  # With visible browser
make ralph-status  # Show progress
make ralph-report  # Generate report
make ralph-reset   # Reset state
make ralph-split   # Split-screen mode (tmux)
```

## CI Pipeline (`.github/workflows/ci.yml`)

Runs on push to `main` and PRs to `main`.

### Backend Job
1. Setup Python 3.11
2. Install `requirements-dev.txt`
3. Run Ruff linter
4. Run Pytest with coverage (`--cov-fail-under=40`)
5. Upload coverage to Codecov
6. Upload test artifacts (JSON reports)

### Frontend Job
1. Setup Node.js 20
2. `npm ci`
3. Run ESLint (`--max-warnings=100`)
4. Run Vitest with coverage
5. Build frontend (`npm run build`)
6. Upload test artifacts

### CI Summary Job
- Runs after both jobs complete
- Creates `ci-summary.json` with results
- Posts PR comment with status table

## Pre-commit Hooks

Husky + lint-staged (configured in root `package.json`):
- **Frontend**: ESLint on staged `.js`/`.vue` files
- **Backend**: Ruff on staged `.py` files

Runs automatically on `git commit`. Skip with `--no-verify` (not recommended).

## Conventional Commits

Enforced via commitlint:
```
feat: add new feature
fix: fix a bug
docs: documentation changes
style: formatting, missing semi-colons
refactor: code refactoring
perf: performance improvements
test: adding tests
build: build system changes
ci: CI configuration
chore: maintenance tasks
revert: revert a commit
```

Semantic release uses commit types to auto-version on `main`.
