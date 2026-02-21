# AI Features

## AI Providers

The platform uses **two AI providers** for different tasks:

### 1. Qwen (Together.xyz) -- Primary for Generation

- **Client**: `QwenAPIClient` (`services/qwen_client.py`)
- **Library**: `openai` Python SDK (OpenAI-compatible API)
- **Model**: `qwen/qwen3-235b-a22b-2507` via OpenRouter
- **Base URL**: `https://openrouter.ai/api/v1`
- **Env var**: `OPENROUTER_API_KEY`
- **Used for**: Cover letter generation, detail extraction, email/subject generation

### 2. Anthropic Claude -- Secondary for Analysis

- **Client**: `ClaudeAPIClient` (`services/api_client.py`) + direct `Anthropic` SDK usage
- **Library**: `anthropic` Python SDK
- **Model**: `claude-3-5-haiku-20241022`
- **Env var**: `ANTHROPIC_API_KEY`
- **Used for**: Skill extraction, ATS analysis, interview generation, requirement analysis, salary coaching, and 8 other analysis services

### Service-to-Provider Mapping

| Service | Provider | Purpose |
|---------|----------|---------|
| `qwen_client.py` (QwenAPIClient) | Qwen | Cover letter + email generation |
| `generator.py` (BewerbungsGenerator) | Qwen (via QwenAPIClient) | Full application pipeline |
| `demo_generator.py` | Qwen (via QwenAPIClient) | Demo generation (no auth) |
| `api_client.py` (ClaudeAPIClient) | Claude | Legacy: detail extraction, intro generation |
| `skill_extractor.py` | Claude | CV skill extraction |
| `profile_extractor.py` | Claude | CV profile data extraction |
| `contact_extractor.py` | Claude | Job posting contact extraction |
| `requirement_analyzer.py` | Claude | Job requirement extraction |
| `ats_service.py` | Claude | ATS compatibility analysis |
| `ats_optimizer.py` | Claude | ATS optimization suggestions |
| `interview_generator.py` | Claude | Interview question generation |
| `interview_evaluator.py` | Claude | Answer evaluation (STAR method) |
| `star_analyzer.py` | Claude | STAR method analysis |
| `job_fit_calculator.py` | Claude | Skill-requirement matching |
| `salary_coach.py` | Claude | Salary research + negotiation |
| `company_researcher.py` | Web scraping | Company research (no AI) |

## Core Pipeline: BewerbungsGenerator

The 5-phase application generation pipeline in `services/generator.py`:

```
Phase 1: Read Job Posting
  |  URL -> WebScraper.fetch_structured_job_posting()
  |  OR: user-provided text from preview step
  v
Phase 2: Extract Details (via QwenAPIClient)
  |  Input:  job posting text + company name
  |  Output: position, ansprechpartner, quelle, email
  |  Method: extract_bewerbung_details()
  |  Temp: 0.3, max_tokens: 500
  v
Phase 3: Generate Anschreiben (via QwenAPIClient)
  |  Input:  CV, job text, extracted details, skills, tone
  |  Output: full cover letter body (greeting to closing)
  |  Method: generate_anschreiben()
  |  Temp: 0.65, max_tokens: 1200
  |  Includes: forbidden phrase detection + retry
  v
Phase 4: Create PDF (reportlab)
  |  Briefkopf (header) built programmatically from user profile
  |  + AI-generated body -> PDF via create_anschreiben_pdf()
  v
Phase 5: Generate Email (via QwenAPIClient)
  |  Subject: generate_betreff() -- template-based, no AI call
  |  Body: generate_email_text() -- template-based, no AI call
  |  (Both are deterministic string templates, not AI-generated)
  v
Save Application to DB + Extract JobRequirements in background
```

## Prompt Engineering Constraints

### Factual Accuracy (KRITISCHE REGEL)
All generation prompts enforce strict factual accuracy:
- ONLY mention skills/tools/experience that appear in the CV
- NEVER invent qualifications (explicit forbidden examples in prompts)
- If job requires skills not in CV: honestly state willingness to learn
- "Better an honest gap than an invented qualification"

### Forbidden Phrases
Maintained in `QwenAPIClient.FORBIDDEN_PHRASES` list (~20 phrases):
- Generic openers: "Hiermit bewerbe ich mich", "mit grossem Interesse"
- AI-typical: "hat meine Aufmerksamkeit geweckt", "genau die Mischung aus"
- Cliches: "hochmotiviert", "in einem dynamischen Umfeld", "meine Leidenschaft fuer"

Post-generation check via `_find_forbidden_phrases()`. If violations found, a correction prompt is appended and the model retries (up to 3 attempts).

### Forbidden Characters
- En-dash, em-dash, hyphens as punctuation are forbidden
- Post-processed: replaced with commas via `_postprocess_anschreiben()`

### Tone Configuration
Three tones supported (passed to generation):
- **modern** (default): "Locker aber respektvoll. 'Bei euch' statt 'bei Ihnen'"
- **formal**: "Formell und professionell. Siezen (Sie)."
- **kreativ**: "Persoenlich und kreativ. Storytelling-Elemente erlaubt."

## API Call Pattern

All AI services follow the same retry pattern:

```python
for attempt in range(retry_count):  # default: 3
    try:
        response = self.client.messages.create(...)
        return parse_response(response)
    except Exception as e:
        if attempt < retry_count - 1:
            logger.warning("... (Versuch %d/%d): %s", attempt + 1, retry_count, e)
            time.sleep(2)  # RETRY_DELAY_SECONDS
        else:
            # either raise or return defaults
```

## Token Limits & Temperatures

| Operation | max_tokens | temperature | Provider |
|-----------|-----------|-------------|----------|
| Detail extraction | 500 | 0.3 | Qwen |
| Key info extraction | 400 | 0.3 | Qwen |
| Einleitung (intro) | 300 | 0.7 | Qwen |
| Anschreiben (full) | 1200 | 0.65 | Qwen |
| Skill extraction | 2000 | 0.2 | Claude |
| ATS analysis | varies | 0.3 | Claude |
| Interview generation | varies | 0.7 | Claude |

## Input Truncation

All prompts truncate inputs to prevent token overflow:
- CV text: max 2000-2500 chars in generation prompts, 4000 chars in skill extraction
- Job posting text: max 2000 chars
- Zeugnis (work reference): max 1000 chars
- Job description for compact extraction: max 500 chars

## Skill Extraction Pipeline

Triggered automatically on CV upload (`documents.py` route):

```
Upload PDF
  -> extract_text_from_pdf() (PyMuPDF/PyPDF2/OCR)
  -> SkillExtractor.extract_skills_from_cv()
     -> Claude API: "Extrahiere alle Skills als JSON-Array"
     -> Parse JSON response
     -> Validate categories (with fuzzy mapping)
     -> Save to UserSkill table
  -> ProfileExtractor.extract_profile_from_cv()
     -> Claude API: extract name, phone, address, etc.
     -> Only fill empty User fields (never overwrite)
```

**Valid skill categories**: `technical`, `soft_skills`, `languages`, `tools`, `certifications`
Category fuzzy mapping: `"programming"` -> `"technical"`, `"sprachen"` -> `"languages"`, etc.

## ATS Analysis

Two-step process:
1. `ATSService.analyze()` -- keyword matching between CV and job posting
2. `ATSOptimizer.optimize()` -- suggestions for improving match score

Results cached in `ATSAnalysis` model (keyed by `job_text_hash` SHA-256).

## Interview Preparation

1. `InterviewGenerator.generate_questions()` -- generates questions per application
   - Types: behavioral, technical, situational, company_specific, salary_negotiation
   - Difficulty: easy, medium, hard
2. `InterviewEvaluator.evaluate_answer()` -- evaluates user's practice answers
3. `StarAnalyzer.analyze()` -- STAR method feedback on answers

## Job Fit Calculation

`JobFitCalculator.calculate_job_fit(user_id, application_id)`:
- Matches `UserSkill` records against `JobRequirement` records
- Produces overall score (0-100) stored in `Application.job_fit_score`
- Uses Claude for semantic matching (not just exact string match)

## Demo Mode

`DemoGenerator` (`services/demo_generator.py`):
- Uses QwenAPIClient (same as production)
- No authentication required
- Generates sample cover letter from hardcoded/demo data
- Endpoint: `POST /api/demo/generate`

## Background AI Jobs

Via APScheduler (`services/scheduler.py`):
- `auto_search_jobs`: every 6 hours, uses `JobRecommender` to find jobs
- `JobRecommender` uses `BundesagenturClient` (Bundesagentur fuer Arbeit API) for job search
- Results scored via `JobFitCalculator` and saved as `JobRecommendation`
