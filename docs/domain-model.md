# Domain Model (15 SQLAlchemy Models)

## Entity Relationship Diagram

```
User (1) ──< Document (N)
  |  |  |  |  |  |  |
  |  |  |  |  |  |  └──< JobRecommendation (N)
  |  |  |  |  |  └──< UserSkill (N) ──> Document (source)
  |  |  |  |  └──< EmailAccount (N)
  |  |  |  └──< APIKey (N)
  |  |  └──< TokenBlacklist (N)   [via backref]
  |  └──< ATSAnalysis (N)         [via backref]
  |  └──1 SalaryCoachData          [via backref, uselist=False]
  └──1 Subscription                [uselist=False]
  └──< Template (N) ──< Application (N)
  └──< Application (N)
         |  |
         |  └──< JobRequirement (N)
         └──< InterviewQuestion (N)

WebhookEvent (standalone - no FK to User)
```

All relationships from User use `cascade="all, delete-orphan"` -- deleting a User cascades to all owned records.

## Model Details

### User (`users`)

Central auth + profile model. Hub for all user-owned data.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `email` | String(255) | unique, indexed, NOT NULL |
| `password_hash` | String(255) | nullable (OAuth users) |
| `full_name` | String(255) | |
| `display_name` | String(100) | Optional UI name |
| `is_active` | Boolean | Default True |
| `is_admin` | Boolean | Default False |
| `email_verified` | Boolean | Default False |
| `email_verification_token` | String(255) | |
| `email_verification_sent_at` | DateTime | |
| `password_reset_token` | String(255) | |
| `password_reset_sent_at` | DateTime | |
| `failed_login_attempts` | Integer | Default 0, for account lockout |
| `locked_until` | DateTime | Account lockout timestamp |
| `stripe_customer_id` | String(255) | unique, indexed |
| `google_id` | String(255) | unique, indexed (Google OAuth) |
| `language` | String(5) | Default "de" |
| `applications_this_month` | Integer | Monthly usage counter |
| `month_reset_at` | DateTime | Monthly counter reset timestamp |
| `weekly_goal` | Integer | Default 5 |
| `phone` | String(50) | Contact for PDFs |
| `address` | String(255) | Contact for PDFs |
| `city` | String(100) | Contact for PDFs |
| `postal_code` | String(20) | Contact for PDFs |
| `website` | String(255) | Contact for PDFs |
| `created_at` | DateTime | |

**Relationships**: documents, templates, applications, api_keys, email_accounts, subscription (1:1), skills, job_recommendations, ats_analyses (backref), salary_coach_data (backref, 1:1), blacklisted_tokens (backref)

**Methods**:
- `set_password(password)` / `check_password(password)` - werkzeug password hashing
- `to_dict()` - includes nested subscription

---

### Application (`applications`)

Core entity: a generated job application with full lifecycle tracking.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `template_id` | FK -> templates | optional |
| `datum` | DateTime | Default utcnow |
| `firma` | String(255) | Company name, NOT NULL |
| `position` | String(255) | Job title |
| `ansprechpartner` | Text | Contact person salutation |
| `email` | String(255) | Contact email |
| `quelle` | String(255) | Source portal |
| `status` | String(50) | Default "erstellt" |
| `pdf_path` | String(500) | Path to generated PDF |
| `betreff` | Text | Email subject line |
| `email_text` | Text | Email body text |
| `einleitung` | Text | AI-generated cover letter body |
| `notizen` | Text | User notes / structured description |
| `links_json` | Text | JSON: email_links, application_links |
| `sent_at` | DateTime | When sent |
| `sent_via` | String(50) | "gmail" or "outlook" |
| `status_history` | Text | JSON array of {status, timestamp} |
| `interview_date` | DateTime | Scheduled interview |
| `interview_feedback` | Text | User's feedback |
| `interview_result` | String(50) | scheduled/completed/passed/rejected/offer_received |
| `job_fit_score` | Integer | 0-100, calculated after generation |

**Status lifecycle** (German): `erstellt` -> `versendet` -> `antwort_erhalten` -> `absage` | `zusage`

**Relationships**: user, template, requirements (JobRequirement), interview_questions

**Methods**:
- `get_status_history()` / `add_status_change(status)` - JSON-backed status log
- `to_dict()` - full serialization

---

### Document (`documents`)

Uploaded user documents (PDFs). Text extracted and stored as `.txt`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `doc_type` | String(50) | "lebenslauf", "anschreiben", "arbeitszeugnis" |
| `file_path` | String(500) | Path to extracted .txt, NOT NULL |
| `pdf_path` | String(500) | Path to original .pdf |
| `original_filename` | String(255) | Original upload name |
| `uploaded_at` | DateTime | |

One document per type per user (upsert pattern in route).

---

### Template (`templates`)

Cover letter templates with `{{VARIABLE}}` placeholders.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `name` | String(255) | NOT NULL |
| `content` | Text | Template with `{{FIRMA}}`, `{{POSITION}}`, etc. |
| `is_default` | Boolean | Default False |
| `is_pdf_template` | Boolean | Default False |
| `pdf_path` | String(500) | Path to PDF template file |
| `variable_positions` | JSON | Positions for PDF variable overlay |
| `created_at` | DateTime | |
| `updated_at` | DateTime | Auto-update |

**Template variables**: `{{FIRMA}}`, `{{POSITION}}`, `{{ANSPRECHPARTNER}}`, `{{QUELLE}}`, `{{EINLEITUNG}}`

---

### Subscription (`subscriptions`)

Stripe subscription data. 1:1 with User.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | unique, NOT NULL |
| `stripe_customer_id` | String(255) | indexed |
| `stripe_subscription_id` | String(255) | unique, indexed |
| `plan` | Enum(SubscriptionPlan) | free/basic/pro, default free |
| `status` | Enum(SubscriptionStatus) | active/canceled/past_due/trialing |
| `current_period_start` | DateTime | |
| `current_period_end` | DateTime | |
| `cancel_at_period_end` | Boolean | Default False |
| `canceled_at` | DateTime | |
| `trial_end` | DateTime | |
| `created_at` | DateTime | |

**Enums**:
- `SubscriptionPlan`: free, basic, pro
- `SubscriptionStatus`: active, canceled, past_due, trialing

---

### APIKey (`api_keys`)

Chrome extension authentication keys.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `key_hash` | String(255) | Werkzeug password hash, NOT NULL |
| `key_prefix` | String(10) | First 8 chars for display, indexed |
| `name` | String(255) | User-given name |
| `is_active` | Boolean | Default True |
| `created_at` | DateTime | |
| `last_used_at` | DateTime | Updated on each use |

**Key format**: `mlr_` + `secrets.token_urlsafe(32)` (e.g. `mlr_abc123...`)
Keys are hashed with werkzeug; only prefix stored in plaintext.

**Methods**: `generate_key()`, `set_key(key)`, `check_key(key)`

---

### TokenBlacklist (`token_blacklist`)

JWT revocation. Tokens added on logout.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `jti` | String(36) | JWT ID, unique, indexed |
| `token_type` | String(10) | "access" or "refresh" |
| `user_id` | FK -> users | NOT NULL |
| `created_at` | DateTime | |
| `expires_at` | DateTime | NOT NULL |

**Class methods**: `is_token_blacklisted(jti)`, `add_token(...)`, `cleanup_expired()`

---

### ATSAnalysis (`ats_analyses`)

ATS (Applicant Tracking System) scan results. Cached by job text hash.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `job_url` | String(2048) | indexed |
| `job_text_hash` | String(64) | SHA-256, indexed (duplicate detection) |
| `title` | String(255) | |
| `score` | Integer | NOT NULL (0-100) |
| `result_json` | Text | Full analysis result as JSON |
| `created_at` | DateTime | indexed |

**Methods**: `hash_job_text(text)` (SHA-256), `to_dict()`, `to_summary_dict()`

---

### EmailAccount (`email_accounts`)

Connected Gmail/Outlook accounts for sending applications via email.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `provider` | String(50) | "gmail" or "outlook" |
| `email` | String(255) | NOT NULL |
| `access_token_encrypted` | Text | Fernet-encrypted |
| `refresh_token_encrypted` | Text | Fernet-encrypted |
| `token_expires_at` | DateTime | |
| `created_at` | DateTime | |

**Encryption**: Fernet symmetric encryption via `EMAIL_ENCRYPTION_KEY` env var.
**Methods**: `set_access_token()`, `get_access_token()`, `set_refresh_token()`, `get_refresh_token()`, `is_token_expired()`

---

### UserSkill (`user_skills`)

Skills auto-extracted from CV uploads via AI.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `skill_name` | String(255) | NOT NULL |
| `skill_category` | String(50) | NOT NULL |
| `experience_years` | Float | nullable |
| `source_document_id` | FK -> documents | nullable |
| `created_at` | DateTime | |
| `updated_at` | DateTime | Auto-update |

**Valid categories**: `technical`, `soft_skills`, `languages`, `tools`, `certifications`

---

### JobRequirement (`job_requirements`)

Requirements extracted from job postings via AI. Linked to Application.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `application_id` | FK -> applications | indexed, NOT NULL |
| `requirement_text` | Text | NOT NULL |
| `requirement_type` | String(20) | NOT NULL: `must_have` or `nice_to_have` |
| `skill_category` | String(50) | nullable |
| `created_at` | DateTime | |

Used by `JobFitCalculator` to match UserSkills against requirements.

---

### InterviewQuestion (`interview_questions`)

AI-generated interview prep questions per application.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `application_id` | FK -> applications | indexed, NOT NULL |
| `question_text` | Text | NOT NULL |
| `question_type` | String(30) | NOT NULL |
| `difficulty` | String(20) | Default "medium" |
| `sample_answer` | Text | nullable |
| `created_at` | DateTime | |

**Question types**: `behavioral`, `technical`, `situational`, `company_specific`, `salary_negotiation`
**Difficulty levels**: `easy`, `medium`, `hard`

---

### JobRecommendation (`job_recommendations`)

Job recommendations based on user skills, with fit scores.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | indexed, NOT NULL |
| `job_data_json` | Text | Full job data as JSON |
| `fit_score` | Integer | 0-100, NOT NULL |
| `fit_category` | String(50) | `sehr_gut`, `gut`, `mittel` |
| `source` | String(100) | Job board name |
| `job_url` | String(500) | indexed |
| `job_title` | String(255) | |
| `company_name` | String(255) | |
| `location` | String(255) | |
| `recommended_at` | DateTime | |
| `dismissed` | Boolean | Default False |
| `applied` | Boolean | Default False |
| `application_id` | FK -> applications | nullable |

**Factory method**: `from_job_data(user_id, job_data, fit_score, fit_category)`
Auto-cleaned after 30 days by background scheduler.

---

### SalaryCoachData (`salary_coach_data`)

Salary research + negotiation data. 1:1 per user (unique user_id).

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `user_id` | FK -> users | unique, indexed, NOT NULL |
| `position` | String(255) | |
| `region` | String(255) | |
| `experience_years` | Integer | |
| `target_salary` | Integer | |
| `current_salary` | Integer | |
| `industry` | String(255) | |
| `research_json` | Text | AI research result |
| `strategy_json` | Text | AI negotiation strategy |
| `created_at` | DateTime | |
| `updated_at` | DateTime | Auto-update |

---

### WebhookEvent (`webhook_events`)

Stripe webhook idempotency tracking. Standalone (no User FK).

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `stripe_event_id` | String(255) | unique, indexed, NOT NULL |
| `event_type` | String(100) | NOT NULL |
| `processed_at` | DateTime | |
| `status` | String(20) | "success" or "failed" |
| `error_message` | Text | |

## Naming Conventions

- **Table names**: lowercase plural English (`users`, `applications`, `documents`)
- **Column names**: German for domain fields (`firma`, `position`, `ansprechpartner`, `betreff`, `einleitung`, `notizen`, `quelle`, `datum`)
- **Status values**: German (`erstellt`, `versendet`, `absage`, `zusage`, `antwort_erhalten`)
- **Enum values**: English (`free`, `basic`, `pro`, `active`, `canceled`)
- **Categories**: English (`technical`, `soft_skills`, `must_have`, `nice_to_have`)

## Common Patterns

- All models have `to_dict()` for JSON serialization
- JSON fields stored as `Text` with manual `json.loads()`/`json.dumps()` (not `db.JSON`)
- Timestamps use `datetime.utcnow` (no timezone-aware datetimes)
- Cascade deletes from User to all owned models
- Validation via class methods (`validate_type()`, `validate_category()`)
- Sensitive data encrypted (EmailAccount tokens: Fernet, APIKey keys: werkzeug hash)
