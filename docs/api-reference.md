# API Reference

All endpoints under `/api/`. Authentication via JWT Bearer token unless noted.

## Authentication

### Auth Methods
- **JWT**: `Authorization: Bearer <token>` header (most endpoints)
- **API Key**: `X-API-Key: mlr_...` header (Chrome extension endpoints)
- **None**: Public endpoints (demo, legal, health)

### Decorators
- `@jwt_required_custom` -- verifies JWT, injects `current_user`
- `@api_key_required` -- verifies API key, injects `current_user`
- `@admin_required` -- JWT + `is_admin` check
- `@check_subscription_limit` -- JWT + atomic limit check/increment

---

## Auth (`/api/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | -- | Register new user (email, password, full_name) |
| POST | `/login` | -- | Login (email, password) -> access_token, user |
| POST | `/google` | -- | Google OAuth login (credential) |
| POST | `/refresh` | JWT | Refresh access token |
| GET | `/me` | JWT | Get current user profile |
| POST | `/logout` | JWT | Logout (blacklists token) |
| PUT | `/language` | JWT | Update language preference |
| PUT | `/profile` | JWT | Update user profile fields |
| PUT | `/change-password` | JWT | Change password |
| DELETE | `/delete-account` | JWT | Delete user account |
| GET | `/password-requirements` | -- | Get password requirements |
| POST | `/validate-password` | -- | Validate password strength |
| POST | `/send-verification` | JWT | Send email verification |
| POST | `/resend-verification` | -- | Resend verification email |
| POST | `/verify-email` | -- | Verify email with token |
| POST | `/forgot-password` | -- | Request password reset |
| POST | `/reset-password` | -- | Reset password with token |

Rate limits: email verification 3/hour, password reset 3/hour.

---

## Applications (`/api/applications`)

### CRUD

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | JWT | List user's applications |
| GET | `/timeline` | JWT | Get applications as timeline events |
| GET | `/<id>` | JWT | Get single application |
| PUT | `/<id>` | JWT | Update application (status, notes, etc.) |
| DELETE | `/<id>` | JWT | Delete application |

### Generation

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/generate` | API Key + Sub | Generate from extension (company, text, url) |
| POST | `/generate-from-url` | JWT + Sub | Generate from URL (web app) |
| POST | `/generate-from-text` | JWT + Sub | Generate from pasted text |
| POST | `/preview-job` | JWT | Preview job data from URL before generating |
| POST | `/quick-extract` | JWT | Quick extract job data from URL |
| POST | `/analyze-manual-text` | JWT | Analyze manually pasted job text |

"Sub" = `@check_subscription_limit` (checks monthly limit + increments atomically).

### Export

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/<id>/pdf` | JWT | Download generated PDF |
| GET | `/<id>/email-draft` | JWT | Get email draft (subject + body) |
| GET | `/export` | JWT | Export applications as CSV/JSON |

### ATS

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/<id>/ats-check` | JWT | Run ATS compatibility check |
| POST | `/<id>/ats-optimize` | JWT | Get ATS optimization suggestions |

### Interview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/<id>/generate-questions` | JWT | Generate interview questions |
| GET | `/<id>/interview-questions` | JWT | Get generated questions |
| POST | `/interview/evaluate-answer` | JWT | Evaluate a practice answer |
| POST | `/interview/summary` | JWT | Get interview prep summary |
| POST | `/interview/analyze-star` | JWT | STAR method analysis |
| GET | `/interview/star-components` | JWT | Get STAR component definitions |
| PUT | `/<id>/interview-result` | JWT | Update interview result |
| GET | `/interview-stats` | JWT | Get interview statistics |

### Requirements / Job Fit

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/<id>/requirements` | JWT | Get extracted job requirements |
| POST | `/<id>/analyze-requirements` | JWT | Analyze requirements from job posting |
| GET | `/<id>/job-fit` | JWT | Get job-fit score |
| POST | `/analyze-job-fit` | JWT | Analyze job fit ad-hoc |

---

## Documents (`/api/documents`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | JWT | List user's documents |
| POST | `/` | JWT | Upload PDF (multipart: file + doc_type) |
| GET | `/<id>` | JWT | Download document (extracted text) |
| DELETE | `/<id>` | JWT | Delete document (?delete_skills=true) |

`doc_type` values: `lebenslauf`, `anschreiben`, `arbeitszeugnis`. One per type per user (upsert).

Upload triggers: PDF text extraction -> skill extraction (for CV) -> profile extraction (for CV).

---

## Skills (`/api/users/me/skills`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me/skills` | JWT | List user's skills (filterable by category) |
| POST | `/users/me/skills` | JWT | Add manual skill |
| PUT | `/users/me/skills/<id>` | JWT | Update skill |
| DELETE | `/users/me/skills/<id>` | JWT | Delete skill |
| POST | `/documents/<id>/extract-skills` | JWT | Re-extract skills from document |

---

## ATS (`/api/ats`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/analyze` | JWT | Run ATS analysis (URL or text + CV) |
| GET | `/history` | JWT | List past ATS analyses |
| GET | `/history/<id>` | JWT | Get specific analysis |
| DELETE | `/history/<id>` | JWT | Delete analysis |

---

## Subscriptions (`/api/subscriptions`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/status` | JWT | Get subscription status + usage |
| GET | `/plans` | JWT | List available plans + prices |
| GET | `/current` | JWT | Get current subscription details |
| POST | `/create-checkout` | JWT | Create Stripe checkout session |
| POST | `/portal` | JWT | Create Stripe billing portal URL |
| POST | `/change-plan` | JWT | Change subscription plan |

---

## Webhooks (`/api/webhooks`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/stripe` | Stripe signature | Handle Stripe webhook events |

Idempotent: uses `WebhookEvent` table to track processed events.

---

## API Keys (`/api/keys`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | JWT | List user's API keys |
| POST | `/` | JWT | Create new API key (returns full key once) |
| DELETE | `/<id>` | JWT | Revoke API key |

---

## Email (`/api/email`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/integration-status` | JWT | Check email integration status |
| GET | `/accounts` | JWT | List connected email accounts |
| DELETE | `/accounts/<id>` | JWT | Disconnect email account |
| GET | `/gmail/auth-url` | JWT | Get Gmail OAuth URL |
| GET | `/gmail/callback` | JWT | Gmail OAuth callback |
| GET | `/outlook/auth-url` | JWT | Get Outlook OAuth URL |
| GET | `/outlook/callback` | JWT | Outlook OAuth callback |
| POST | `/send` | JWT | Send application via email |

---

## Companies (`/api/companies`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/<name>/research` | JWT | Get company research data |
| GET | `/<name>/cache-status` | JWT | Check if research is cached |

---

## Salary (`/api/salary`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/research` | JWT | Run salary research |
| POST | `/negotiation-tips` | JWT | Get negotiation strategy |
| GET | `/data` | JWT | Get saved salary data |
| POST | `/data` | JWT | Save salary form data |
| DELETE | `/data` | JWT | Delete salary data |

---

## Recommendations (`/api/recommendations`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | JWT | List job recommendations |
| POST | `/analyze` | JWT | Analyze job fit from URL |
| POST | `/analyze-manual` | JWT | Analyze job fit from text |
| POST | `/search` | JWT | Search for jobs |
| GET | `/<id>` | JWT | Get single recommendation |
| POST | `/<id>/dismiss` | JWT | Dismiss recommendation |
| POST | `/<id>/apply` | JWT | Mark as applied |
| DELETE | `/<id>` | JWT | Delete recommendation |
| POST | `/save` | JWT | Save external job as recommendation |
| GET | `/stats` | JWT | Get recommendation statistics |

---

## Stats (`/api/stats`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/stats` | JWT | Basic dashboard stats |
| GET | `/stats/extended` | JWT | Extended statistics (charts, trends) |
| GET | `/stats/companies` | JWT | Company application stats |
| GET | `/stats/weekly-goal` | JWT | Get weekly goal + progress |
| PUT | `/stats/weekly-goal` | JWT | Update weekly goal target |

---

## Demo (`/api/demo`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/generate` | -- | Generate demo cover letter (anonymous) |

---

## Templates (`/api/templates`) -- DEPRECATED

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/list-simple` | -- | Returns empty list (extension compat) |

---

## Admin (`/api/admin`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/stats` | Admin | Platform-wide statistics |
| GET | `/users` | Admin | List all users (paginated, searchable) |
| GET | `/users/<id>` | Admin | Get user detail |
| PATCH | `/users/<id>` | Admin | Update user (activate/deactivate, admin) |
| GET | `/users/<id>/applications` | Admin | List user's applications |

---

## Legal (`/api/legal`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/info` | -- | Get Impressum/legal info |

---

## Utility Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | -- | Health check (rate-limit exempt) |
| GET | `/api/version` | -- | App version + commit (rate-limit exempt) |

---

## Rate Limiting

- **Global**: 200/hour, 50/minute (Flask-Limiter, in-memory, fixed-window)
- **Email verification**: 3/hour
- **Password reset**: 3/hour
- **Whitelisted IPs**: Exempt via `RATE_LIMIT_WHITELIST` env var (default: `127.0.0.1`)
- **Health/version**: Exempt via `@limiter.exempt`

## Response Format

```json
// Success
{ "success": true, "data": { ... }, "message": "..." }

// Error
{ "success": false, "error": "German error message" }
// or
{ "error": "German error message" }
```

## Error Codes

| HTTP | Meaning |
|------|---------|
| 400 | Validation error / bad request |
| 401 | Missing/invalid/expired token |
| 403 | Subscription limit reached / forbidden |
| 404 | Resource not found |
| 422 | JWT decode error |
| 429 | Rate limit exceeded |
| 500 | Server error |

Special error code: `SUBSCRIPTION_LIMIT_REACHED` (in 403 response body `error_code` field).
