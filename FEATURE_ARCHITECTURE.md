# Obojobs Feature Architecture Guide

> Code-focused implementation guide for extending the obojobs codebase.
> Generated with Feature Architect skill.

---

## Codebase Architecture Overview

### Tech Stack
```
Frontend:  Vue 3 + Vite + vue-i18n
Backend:   Flask 3.0 + SQLAlchemy + JWT
AI:        Anthropic Claude (claude-3-5-haiku)
Payments:  Stripe (subscriptions + webhooks)
Database:  SQLite (dev) / PostgreSQL (prod)
```

### Directory Structure
```
obojobs/
├── backend/
│   ├── app.py                 # Flask app factory
│   ├── config.py              # Environment config
│   ├── models/                # SQLAlchemy models (18 files)
│   ├── routes/                # API blueprints (18 files)
│   ├── services/              # Business logic (28 files)
│   ├── middleware/            # Auth, rate limiting
│   └── i18n/                  # Backend translations
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # Route components (22 files)
│   │   ├── components/        # Reusable UI (19 files)
│   │   ├── api/client.js      # Axios wrapper
│   │   ├── store/auth.js      # Pinia auth store
│   │   ├── router/index.js    # Vue Router
│   │   ├── i18n/              # vue-i18n setup
│   │   └── assets/styles.css  # Zen design system
│   └── package.json
│
└── extension/                  # Chrome extension (Manifest V3)
```

### Established Patterns

#### Backend Patterns

**1. Route Definition**
```python
# backend/routes/{feature}.py
from flask import Blueprint, request, jsonify
from middleware.jwt_required import jwt_required
from services.{feature}_service import {Feature}Service

{feature}_bp = Blueprint('{feature}', __name__)

@{feature}_bp.route('/', methods=['GET'])
@jwt_required
def get_{feature}s(current_user):
    service = {Feature}Service()
    result = service.get_all(current_user.id)
    return jsonify(result), 200

@{feature}_bp.route('/', methods=['POST'])
@jwt_required
def create_{feature}(current_user):
    data = request.get_json()
    service = {Feature}Service()
    result = service.create(current_user.id, data)
    return jsonify(result), 201
```

**2. Service Layer**
```python
# backend/services/{feature}_service.py
from models.{feature} import {Feature}
from models import db

class {Feature}Service:
    def get_all(self, user_id):
        return {Feature}.query.filter_by(user_id=user_id).all()

    def create(self, user_id, data):
        item = {Feature}(user_id=user_id, **data)
        db.session.add(item)
        db.session.commit()
        return item.to_dict()

    def get_by_id(self, user_id, item_id):
        return {Feature}.query.filter_by(
            id=item_id,
            user_id=user_id
        ).first_or_404()
```

**3. Model Definition**
```python
# backend/models/{feature}.py
from models import db
from datetime import datetime
import uuid

class {Feature}(db.Model):
    __tablename__ = '{feature}s'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    # ... fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            # ... fields
            'created_at': self.created_at.isoformat()
        }
```

**4. Blueprint Registration**
```python
# backend/app.py - register new blueprint
from routes.{feature} import {feature}_bp
app.register_blueprint({feature}_bp, url_prefix='/api/{feature}')
```

#### Frontend Patterns

**1. Page Component**
```vue
<!-- frontend/src/pages/{Feature}.vue -->
<template>
  <div class="page-container">
    <header class="page-header">
      <h1>{{ $t('{feature}.title') }}</h1>
    </header>

    <div v-if="loading" class="skeleton-container">
      <!-- Skeleton loaders -->
    </div>

    <div v-else-if="error" class="error-state">
      {{ error }}
    </div>

    <div v-else class="content">
      <!-- Main content -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

const loading = ref(true)
const error = ref(null)
const data = ref([])

onMounted(async () => {
  try {
    const response = await api.get('/{feature}')
    data.value = response.data
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})
</script>
```

**2. API Client Usage**
```javascript
// frontend/src/api/client.js is pre-configured with:
// - Base URL from VITE_API_URL
// - JWT token injection
// - 401 → refresh token flow
// - Response interceptors

import api from '@/api/client'

// GET
const response = await api.get('/endpoint')

// POST
const response = await api.post('/endpoint', { data })

// PATCH
const response = await api.patch('/endpoint/id', { data })

// DELETE
await api.delete('/endpoint/id')
```

**3. Route Registration**
```javascript
// frontend/src/router/index.js
{
  path: '/{feature}',
  name: '{Feature}',
  component: () => import('@/pages/{Feature}.vue'),
  meta: { requiresAuth: true }
}
```

**4. i18n Translations**
```json
// frontend/src/i18n/locales/de.json
{
  "{feature}": {
    "title": "German Title",
    "description": "German description"
  }
}

// frontend/src/i18n/locales/en.json
{
  "{feature}": {
    "title": "English Title",
    "description": "English description"
  }
}
```

---

## Priority Feature Implementations

### Feature 1: Quick-Start Onboarding (Skip CV)

**Problem**: Users must upload CV before seeing any value. High drop-off.

**Solution**: Allow first application without CV, show comparison after.

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/OnboardingChecklist.vue` | Progress checklist widget |
| `frontend/src/components/CoverLetterComparison.vue` | Before/after CV comparison |
| `backend/services/quick_generator.py` | CV-optional generation logic |

#### Files to Modify

| File | Change |
|------|--------|
| `backend/routes/applications.py` | Make CV optional in generate endpoint |
| `backend/services/generator.py` | Add `has_cv` conditional logic |
| `frontend/src/pages/NewApplication.vue` | Add skip-CV flow |
| `frontend/src/pages/Dashboard.vue` | Add OnboardingChecklist |
| `backend/models/user.py` | Add `onboarding_completed` field |

#### Implementation: Backend Changes

```python
# backend/routes/applications.py - Modify generate endpoint

@applications_bp.route('/generate', methods=['POST'])
@jwt_required
def generate_application(current_user):
    data = request.get_json()

    # Check if user has CV
    has_cv = Document.query.filter_by(
        user_id=current_user.id,
        doc_type='lebenslauf'
    ).first() is not None

    generator = BewerbungsGenerator()

    if has_cv:
        # Full personalized generation
        result = generator.generate_full(current_user.id, data)
    else:
        # Basic generation without CV
        result = generator.generate_basic(data)
        result['needs_cv_upgrade'] = True
        result['cv_benefits'] = [
            'Personalized skills matching',
            'Experience-based intro',
            'ATS optimization'
        ]

    return jsonify(result), 200
```

```python
# backend/services/generator.py - Add basic generation

class BewerbungsGenerator:
    def generate_basic(self, data):
        """Generate cover letter without CV - uses job posting only"""
        job_url = data.get('job_url')
        job_text = data.get('job_text', '')

        # Extract job details
        if job_url:
            job_details = self.scraper.extract_job_details(job_url)
        else:
            job_details = self._parse_job_text(job_text)

        # Generate with limited context
        prompt = f"""
        Generate a professional cover letter introduction for:
        Company: {job_details.get('firma', 'the company')}
        Position: {job_details.get('position', 'the position')}

        Write 2-3 sentences expressing interest and enthusiasm.
        Keep it generic but professional since we don't have CV details.
        Write in German.
        """

        intro = self.api_client.generate(prompt)

        return {
            'firma': job_details.get('firma'),
            'position': job_details.get('position'),
            'einleitung': intro,
            'is_basic': True
        }
```

#### Implementation: Frontend Changes

```vue
<!-- frontend/src/components/OnboardingChecklist.vue -->
<template>
  <div class="onboarding-checklist zen-card" v-if="!allComplete">
    <h3>{{ $t('onboarding.getStarted') }}</h3>
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>
    <ul class="checklist">
      <li v-for="item in items" :key="item.key" :class="{ completed: item.done }">
        <span class="check-icon">{{ item.done ? '✓' : '○' }}</span>
        <span class="label">{{ $t(`onboarding.${item.key}`) }}</span>
        <button v-if="!item.done" @click="item.action" class="btn-small">
          {{ $t('common.start') }}
        </button>
      </li>
    </ul>
    <button @click="dismiss" class="btn-ghost">{{ $t('common.dismiss') }}</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const props = defineProps({
  hasApplication: Boolean,
  hasCv: Boolean,
  hasCertificate: Boolean,
  hasWeeklyGoal: Boolean
})

const items = computed(() => [
  { key: 'firstApp', done: props.hasApplication, action: () => router.push('/new-application') },
  { key: 'uploadCv', done: props.hasCv, action: () => router.push('/documents') },
  { key: 'uploadCert', done: props.hasCertificate, action: () => router.push('/documents') },
  { key: 'setGoal', done: props.hasWeeklyGoal, action: () => router.push('/settings') }
])

const progressPercent = computed(() => {
  const done = items.value.filter(i => i.done).length
  return (done / items.value.length) * 100
})

const allComplete = computed(() => items.value.every(i => i.done))
</script>
```

#### Build Sequence

1. **Backend: Quick generator** (~2h)
   - Add `generate_basic()` to generator.py
   - Modify route to check for CV
   - Test: Generate works without CV

2. **Backend: User model** (~30m)
   - Add migration for `onboarding_completed`
   - Test: Migration runs

3. **Frontend: Checklist component** (~2h)
   - Create OnboardingChecklist.vue
   - Add i18n strings
   - Test: Component renders

4. **Frontend: Dashboard integration** (~1h)
   - Add checklist to Dashboard.vue
   - Wire up user state
   - Test: Checklist shows/hides correctly

5. **Frontend: New Application flow** (~2h)
   - Modify to work without CV
   - Add upgrade prompt after generation
   - Test: Full flow works

---

### Feature 2: Next Action Widget

**Problem**: Dashboard doesn't guide users on what to do next.

**Solution**: Smart widget showing highest-priority action.

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/NextActionWidget.vue` | Smart action display |
| `backend/routes/dashboard.py` | Dashboard-specific endpoints |
| `backend/services/next_action_service.py` | Action priority logic |

#### Implementation: Backend

```python
# backend/services/next_action_service.py
from datetime import datetime, timedelta
from models.application import Application

class NextActionService:
    PRIORITY_ORDER = [
        'interview_tomorrow',
        'interview_upcoming',
        'follow_up_needed',
        'weekly_goal_behind',
        'new_recommendation',
        'create_application'
    ]

    def get_next_action(self, user_id):
        # Check for interview tomorrow
        tomorrow = datetime.utcnow() + timedelta(days=1)
        interview = Application.query.filter(
            Application.user_id == user_id,
            Application.interview_date <= tomorrow,
            Application.interview_date >= datetime.utcnow(),
            Application.interview_result == None
        ).first()

        if interview:
            return {
                'type': 'interview_tomorrow',
                'priority': 1,
                'title': f'Interview with {interview.firma}',
                'subtitle': f'Tomorrow at {interview.interview_date.strftime("%H:%M")}',
                'action': 'prepare',
                'action_url': f'/interview-prep/{interview.id}',
                'data': {'application_id': interview.id}
            }

        # Check for follow-ups needed (sent 7+ days ago, no response)
        week_ago = datetime.utcnow() - timedelta(days=7)
        needs_followup = Application.query.filter(
            Application.user_id == user_id,
            Application.status == 'versendet',
            Application.sent_at <= week_ago
        ).first()

        if needs_followup:
            return {
                'type': 'follow_up_needed',
                'priority': 2,
                'title': f'Follow up with {needs_followup.firma}',
                'subtitle': f'Sent {(datetime.utcnow() - needs_followup.sent_at).days} days ago',
                'action': 'follow_up',
                'action_url': f'/applications/{needs_followup.id}',
                'data': {'application_id': needs_followup.id}
            }

        # Check weekly goal progress
        user = User.query.get(user_id)
        apps_this_week = self._count_apps_this_week(user_id)
        if apps_this_week < user.weekly_goal * 0.5:  # Less than 50% through week
            return {
                'type': 'weekly_goal_behind',
                'priority': 3,
                'title': 'You\'re behind on your weekly goal',
                'subtitle': f'{apps_this_week}/{user.weekly_goal} applications',
                'action': 'create',
                'action_url': '/new-application',
                'data': {'current': apps_this_week, 'goal': user.weekly_goal}
            }

        # Default: create new application
        return {
            'type': 'create_application',
            'priority': 10,
            'title': 'Create a new application',
            'subtitle': 'Keep the momentum going',
            'action': 'create',
            'action_url': '/new-application',
            'data': {}
        }
```

```python
# backend/routes/dashboard.py
from flask import Blueprint, jsonify
from middleware.jwt_required import jwt_required
from services.next_action_service import NextActionService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/next-action', methods=['GET'])
@jwt_required
def get_next_action(current_user):
    service = NextActionService()
    action = service.get_next_action(current_user.id)
    return jsonify(action), 200
```

#### Implementation: Frontend

```vue
<!-- frontend/src/components/NextActionWidget.vue -->
<template>
  <div class="next-action-widget zen-card prominent" @click="handleAction">
    <div class="action-icon" :class="action.type">
      <component :is="iconComponent" />
    </div>
    <div class="action-content">
      <h3>{{ action.title }}</h3>
      <p>{{ action.subtitle }}</p>
    </div>
    <div class="action-arrow">→</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'

const router = useRouter()
const action = ref({
  type: 'loading',
  title: 'Loading...',
  subtitle: '',
  action_url: '#'
})

const iconComponent = computed(() => {
  const icons = {
    'interview_tomorrow': 'CalendarIcon',
    'follow_up_needed': 'MailIcon',
    'weekly_goal_behind': 'TargetIcon',
    'create_application': 'PlusIcon'
  }
  return icons[action.value.type] || 'PlusIcon'
})

onMounted(async () => {
  const response = await api.get('/dashboard/next-action')
  action.value = response.data
})

const handleAction = () => {
  router.push(action.value.action_url)
}
</script>

<style scoped>
.next-action-widget {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  background: linear-gradient(135deg, var(--color-washi), var(--color-washi-dark));
  border-left: 4px solid var(--color-indigo);
}

.next-action-widget:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-indigo);
  color: white;
}

.action-content {
  flex: 1;
}

.action-content h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--color-sumi);
}

.action-content p {
  margin: 0.25rem 0 0;
  color: var(--color-stone);
  font-size: 0.9rem;
}

.action-arrow {
  font-size: 1.5rem;
  color: var(--color-stone);
}
</style>
```

#### Build Sequence

1. **Backend: Service** (~1.5h)
   - Create next_action_service.py
   - Implement priority logic
   - Test: Returns correct action types

2. **Backend: Route** (~30m)
   - Create dashboard.py blueprint
   - Register in app.py
   - Test: Endpoint works

3. **Frontend: Widget** (~1.5h)
   - Create NextActionWidget.vue
   - Style with Zen design
   - Test: Renders, clickable

4. **Frontend: Integration** (~30m)
   - Add to Dashboard.vue
   - Position prominently
   - Test: Full flow works

---

### Feature 3: Empty States

**Problem**: Empty pages confuse new users.

**Solution**: Helpful empty states with clear CTAs.

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/EmptyState.vue` | Reusable empty state |

#### Implementation

```vue
<!-- frontend/src/components/EmptyState.vue -->
<template>
  <div class="empty-state">
    <div class="empty-icon">
      <slot name="icon">
        <svg><!-- default icon --></svg>
      </slot>
    </div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <button v-if="actionLabel" @click="$emit('action')" class="btn-primary">
      {{ actionLabel }}
    </button>
    <p v-if="hint" class="hint">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  actionLabel: { type: String, default: '' },
  hint: { type: String, default: '' }
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 1.5rem;
  opacity: 0.6;
}

.empty-state h3 {
  margin: 0 0 0.5rem;
  color: var(--color-sumi);
}

.empty-state p {
  margin: 0 0 1.5rem;
  color: var(--color-stone);
}

.hint {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: var(--color-stone);
}
</style>
```

#### Pages to Update

| Page | Empty State Content |
|------|---------------------|
| Applications.vue | "No applications yet" + Create button |
| Templates.vue | "Using default template" + Create custom |
| Documents.vue | "Upload documents for better results" |
| Timeline.vue | "No activity yet" + Create first app |
| InterviewPrep.vue | "No interviews scheduled" |

---

### Feature 4: Celebration Moments

**Problem**: No positive reinforcement for milestones.

**Solution**: Confetti and toasts for achievements.

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/composables/useCelebration.js` | Celebration logic |
| `frontend/src/components/CelebrationToast.vue` | Custom celebration toast |

#### Implementation

```javascript
// frontend/src/composables/useCelebration.js
import confetti from 'canvas-confetti'

export function useCelebration() {
  const celebrate = (type = 'default') => {
    const configs = {
      default: {
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      },
      big: {
        particleCount: 200,
        spread: 100,
        origin: { y: 0.6 },
        colors: ['#6366F1', '#22C55E', '#F59E0B']
      },
      subtle: {
        particleCount: 30,
        spread: 50,
        origin: { y: 0.8 },
        gravity: 0.8
      }
    }

    confetti(configs[type] || configs.default)
  }

  const celebrateMilestone = (milestone) => {
    const milestones = {
      'first_application': { type: 'big', message: 'Your first application!' },
      'first_response': { type: 'big', message: 'You got a response!' },
      'first_interview': { type: 'big', message: 'Interview scheduled!' },
      'offer_received': { type: 'big', message: 'Congratulations on the offer!' },
      'weekly_goal': { type: 'subtle', message: 'Weekly goal achieved!' }
    }

    const config = milestones[milestone]
    if (config) {
      celebrate(config.type)
      return config.message
    }
  }

  return { celebrate, celebrateMilestone }
}
```

```bash
# Install confetti library
cd frontend && npm install canvas-confetti
```

---

## Database Migrations Needed

```python
# backend/migrations/versions/xxx_add_onboarding_fields.py

def upgrade():
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('onboarding_dismissed', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('first_app_celebrated', sa.Boolean(), default=False))

def downgrade():
    op.drop_column('users', 'onboarding_completed')
    op.drop_column('users', 'onboarding_dismissed')
    op.drop_column('users', 'first_app_celebrated')
```

---

## Implementation Priority

| # | Feature | Effort | Impact | Files Changed |
|---|---------|--------|--------|---------------|
| 1 | Empty States | 3h | High | 6 pages + 1 component |
| 2 | Next Action Widget | 4h | High | 2 backend + 2 frontend |
| 3 | Quick-Start (Skip CV) | 6h | Critical | 4 backend + 3 frontend |
| 4 | Celebration Moments | 2h | Medium | 1 composable + integration |
| 5 | Onboarding Checklist | 3h | High | 1 component + dashboard |

**Recommended Order**: 1 → 2 → 3 → 5 → 4

Start with Empty States (quick win, immediate UX improvement), then Next Action Widget (guides users), then tackle the larger Quick-Start feature.

---

## Testing Checklist

### For Each Feature
- [ ] Unit tests for new services
- [ ] API tests for new endpoints
- [ ] Component tests for new Vue components
- [ ] Manual test: Happy path works
- [ ] Manual test: Edge cases handled
- [ ] Manual test: Mobile responsive
- [ ] i18n: German translations added
- [ ] i18n: English translations added

### Integration Tests
- [ ] New user flow: Register → Skip CV → Generate → Upgrade prompt
- [ ] Returning user flow: Dashboard → Next Action → Complete action
- [ ] Milestone flow: Create app → First response → Celebration

---

## Code Quality Checklist

Before merging each feature:
- [ ] Follows existing patterns (see Architecture Patterns above)
- [ ] No console.log statements
- [ ] Error handling for API calls
- [ ] Loading states for async operations
- [ ] No hardcoded strings (use i18n)
- [ ] Responsive on mobile
- [ ] Accessible (keyboard nav, screen readers)
