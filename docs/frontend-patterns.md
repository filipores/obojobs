# Frontend Patterns

## Tech Stack

- **Vue 3** (Composition API only, `<script setup>`)
- **JavaScript** (NOT TypeScript -- one exception: `data/variableDescriptions.ts`)
- **Vite 5** (dev server port 3000, proxy `/api` to `localhost:5002`)
- **vue-router** (createWebHistory, lazy-loaded routes)
- **vue-i18n** (Composition API mode, `legacy: false`)
- **Axios** (API client with interceptors)
- **Custom CSS** ("Wafu Design" -- Japanese-inspired design system, no CSS framework)

## Project Structure

```
frontend/src/
  main.js              # App entry: createApp + plugins (router, i18n)
  App.vue              # Root: nav, sidebar, footer, theme toggle, toast
  api/client.js        # Axios instance + interceptors
  assets/styles.css    # Global design system (1500+ lines)
  components/          # 23+ reusable components + subdirs
  composables/         # 7 composable hooks
  pages/               # 26 route-level page components
  router/index.js      # Routes + auth guards
  stores/auth.js       # Auth state (reactive store)
  stores/demo.js       # Demo flow state (sessionStorage)
  i18n/                # vue-i18n setup + locales/de.json, en.json
  utils/               # Error translation helper
```

## Component Conventions

### SFC Pattern
All components follow `<template>` + `<script setup>` + `<style scoped>`:

```vue
<template>
  <div class="my-component">...</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/api/client'

const props = defineProps({ ... })
const emit = defineEmits([ ... ])

const loading = ref(false)
// ...
</script>

<style scoped>
.my-component { ... }
</style>
```

### Rules
- **Composition API only**: No Options API, no `export default`
- **`<script setup>`**: Always use, never `setup()` function
- **Scoped styles**: Always `<style scoped>` (exceptions: global styles in `styles.css`)
- **Inline SVG**: No icon library. All icons are inline `<svg>` elements
- **Path alias**: `@` maps to `frontend/src/` (configured in Vite)

## State Management

### Auth Store (`stores/auth.js`)
Reactive store using `reactive()` -- no Vuex/Pinia:

```javascript
import { reactive } from 'vue'

export const authStore = reactive({
  user: safeParseUser(),        // from localStorage
  token: localStorage.getItem('token'),

  async login(email, password) { ... },
  async register(email, password, full_name) { ... },
  async loginWithGoogle(credential) { ... },
  async fetchUser() { ... },
  async logout() { ... },
  isAuthenticated() { ... },    // JWT decode + expiry check
  clearAuthState() { ... }
})
```

- Token stored in `localStorage` as `token`
- User object stored in `localStorage` as `user` (JSON)
- `isAuthenticated()` decodes JWT payload to check expiration client-side
- Corrupted localStorage handled gracefully via `safeParseUser()`

### Demo Store (`stores/demo.js`)
Session-scoped state for demo-to-registration flow:

```javascript
export const demoStore = reactive({
  jobUrl: null,
  demoResult: null,
  postRegistrationFlow: false,
  // ... more fields
})
```

- Persisted in `sessionStorage` (survives refresh, clears on tab close)
- Manages the demo -> register -> CV upload -> regeneration flow

## API Client (`api/client.js`)

Axios instance with automatic auth and error handling:

```javascript
const api = axios.create({ baseURL: '/api' })

// Request interceptor: adds Bearer token from localStorage
// Response interceptor: handles 401, 403, 404, 500, 400/422
```

### Error Handling
- **401**: Clears auth state, redirects to `/login`, shows session expired toast
- **403**: Shows "forbidden" toast
- **404**: Shows "not found" toast
- **500+**: Shows "server error" toast
- **400/422**: Translates German error message via `translateError()`, shows toast
- Login requests are exempt from global 401 handling

### Silent Mode
Suppress automatic toast for custom error handling:
```javascript
api.silent.get('/path')    // no automatic toast
api.silent.post('/path', data)
```

## Routing (`router/index.js`)

### Route Meta
```javascript
{ path: '/dashboard', meta: { requiresAuth: true, titleKey: 'pages.dashboard' } }
{ path: '/login', meta: { public: true, titleKey: 'pages.login' } }
{ path: '/admin', meta: { requiresAuth: true, requiresAdmin: true } }
{ path: '/', meta: { public: true, landing: true } }
```

### Navigation Guards (beforeEach)
1. Landing page (`meta.landing`): redirects authenticated users to `/dashboard` (unless in demo flow)
2. Login/Register: redirects authenticated users to `/dashboard`
3. Public routes (`meta.public`): skip auth checks entirely
4. Protected routes (`meta.requiresAuth`): redirect to `/login` if not authenticated
5. Admin routes (`meta.requiresAdmin`): redirect to `/dashboard` if not admin

### Dynamic Page Title (afterEach)
Title set from `meta.titleKey` via i18n: `"Page Title | obo"`

### Lazy Loading
All route components use dynamic imports for code splitting:
```javascript
component: () => import('../pages/Dashboard.vue')
```

## Toast System

Global notification via `window.$toast()`:

```javascript
// Available anywhere:
window.$toast('Nachricht', 'success')  // success, error, warning, info
window.$toast('Fehler!', 'error')
```

- Component: `Toast.vue` with transition-group animation
- **Deduplication**: Same/similar messages within 2 seconds are suppressed
- Auto-dismiss after 3 seconds
- Accessible: ARIA live regions (`role="alert"` for errors, `role="status"` for info)
- Exposed via `defineExpose({ add, remove })`, mounted globally in `App.vue`

## Composables (`composables/`)

| Composable | Purpose |
|-----------|---------|
| `useConfirm` | Promise-based confirm dialog (renders `ConfirmModal` singleton) |
| `useSubscription` | Subscription plans, checkout, billing portal |
| `useStripe` | Stripe.js checkout redirect |
| `useJobRecommendations` | Job recommendations data |
| `useTemplateParser` | Template `{{VARIABLE}}` parsing |
| `useTemplatePreview` | Template preview rendering |
| `useLegalInfo` | Legal/Impressum data fetching |

### Confirm Dialog Pattern
```javascript
import { useConfirm } from '@/composables/useConfirm'
const { confirm } = useConfirm()

// Simple
const ok = await confirm('Wirklich loeschen?')

// With options
const result = await confirm({
  title: 'Loeschen',
  message: 'Dokument wirklich loeschen?',
  confirmText: 'Loeschen',
  type: 'danger',
  showCheckbox: true,
  checkboxLabel: 'Auch Skills loeschen'
})
// result = { confirmed: true, checkboxChecked: true }
```

## Design System ("Wafu Design" -- `styles.css`)

Japanese-inspired design tokens (1500+ lines CSS, no Tailwind/framework):

### Color System
```css
/* Washi Paper Tones */
--color-washi: #F7F5F0;
--color-washi-warm: #F2EDE3;

/* Sumi Ink */
--color-sumi: #2C2C2C;
--color-sumi-light: #4A4A4A;

/* Accent (Indigo) */
--color-ai: #3D5A6C;

/* Earth Tones */
--color-stone: #9B958F;
--color-clay: #B5A99A;

/* Seasonal Colors */
--color-sakura: #E8A8B8;   /* Spring */
--color-momiji: #D4695E;   /* Autumn */
--color-yuki: #A8C8DC;     /* Winter */

/* Semantic */
--color-success: #7A8B6E;  /* Moss green */
--color-error: #B87A6E;    /* Terracotta */
--color-warning: #C4A35A;
```

### Typography
- Display: `Cormorant Garamond` (serif)
- Body: `Karla` (sans-serif)
- Mono: `JetBrains Mono`

### Spacing (Ma)
```css
--space-ma-xs: 0.5rem;
--space-ma-sm: 1rem;
--space-ma: 2rem;      /* default breathing room */
--space-ma-lg: 3rem;
--space-ma-xl: 5rem;
```

### Dark Mode
CSS class `.dark-mode` on `#app`, toggled in `App.vue`, persisted in `localStorage` (`obojobs-theme`).

## i18n

- **Library**: vue-i18n (Composition API mode, `legacy: false`)
- **Default locale**: `de` (German), fallback: `de`
- **Locale files**: `i18n/locales/de.json`, `en.json`
- **Storage**: `localStorage` key `obojobs-locale`
- **Status**: Partially translated. Some UI strings still hardcoded in German
- **Helper**: `setLocale(locale)`, `getLocale()`, `getFullLocale()` (e.g. `de-DE`)

## Pages (26 route components)

| Page | Route | Auth |
|------|-------|------|
| Landing | `/` | public (redirects auth users) |
| Login | `/login` | public |
| Register | `/register` | public |
| EmailVerification | `/email-verification` | public |
| VerifyEmail | `/verify-email` | public |
| ForgotPassword | `/forgot-password` | public |
| ResetPassword | `/reset-password` | public |
| Impressum | `/impressum` | public |
| Datenschutz | `/datenschutz` | public |
| Dashboard | `/dashboard` | auth |
| Documents | `/documents` | auth |
| Applications | `/applications` | auth |
| NewApplication | `/new-application` | auth |
| Timeline | `/timeline` | auth |
| ATSView | `/ats` | auth |
| CompanyInsights | `/company-insights` | auth |
| Settings | `/settings` | auth |
| SubscriptionView | `/subscription` | auth |
| SubscriptionSuccess | `/subscription/success` | auth |
| InterviewPrep | `/applications/:id/interview` | auth |
| MockInterview | `/applications/:id/mock-interview` | auth |
| JobDashboard | `/job-dashboard` | auth |
| AdminDashboard | `/admin` | admin |
| AdminUsers | `/admin/users` | admin |
| AdminUserDetail | `/admin/users/:id` | admin |
| NotFound | `*` (catch-all) | -- |

## Key Components

| Component | Purpose |
|-----------|---------|
| `Toast.vue` | Global notifications (exposed via `window.$toast`) |
| `ConfirmModal.vue` | Promise-based confirm dialog (singleton) |
| `UsageIndicator.vue` | Monthly application usage display |
| `LanguageSwitcher.vue` | DE/EN locale toggle |
| `ScrollableTable.vue` | Reusable scrollable data table |
| `DateTimePicker.vue` | Date/time input component |
| `SkillsOverview.vue` | User skills display |
| `JobFitScore.vue` | Job-fit score visualization |
| `SalaryCoach.vue` | Salary coaching interface |
| `ATSOptimizer.vue` | ATS optimization UI |
| `InterviewTracker.vue` | Interview status tracking |
| `STARFeedback.vue` | STAR method feedback display |
| `WeeklyGoalWidget.vue` | Weekly application goal tracker |
| `CompanyResearch.vue` | Company research panel |
| `GapAnalysis.vue` | Skill gap analysis display |

### Component Subdirectories
- `components/application/` -- Application detail sub-components
- `components/Applications/` -- Applications list sub-components
- `components/NewApplication/` -- New application flow steps
- `components/landing/` -- Landing page sections
