<template>
  <div
    :class="[
      'job-card',
      `job-card--${job.status}`,
    ]"
  >
    <!-- Shared card header -->
    <div class="card-header">
      <div class="skeleton-line skeleton-tag" v-if="job.status === 'extracting'" />
      <span v-else-if="job.status === 'error'" class="error-label">Fehler</span>
      <span
        v-else-if="job.quickData?.portal"
        :class="['portal-tag', portalClass]"
      >
        {{ job.quickData.portal }}
      </span>
      <span v-else />
      <button
        v-if="job.status !== 'generating'"
        class="remove-btn"
        aria-label="Entfernen"
        @click="emit('remove')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <!-- EXTRACTING STATE -->
    <template v-if="job.status === 'extracting'">
      <div class="skeleton-line skeleton-title" />
      <div class="skeleton-line skeleton-subtitle" />
      <p class="extracting-text">Stellenanzeige wird gelesen...</p>
      <p class="extracting-url">{{ displayUrl }}</p>
    </template>

    <!-- EXTRACTED STATE -->
    <template v-else-if="job.status === 'extracted'">
      <h3 class="card-company">{{ job.quickData?.company }}</h3>
      <p class="card-position">{{ job.quickData?.title }}</p>
      <div class="card-actions-row">
        <select
          class="tone-select"
          :value="job.tone"
          @change="emit('update:tone', $event.target.value)"
        >
          <option value="modern">Modern (Empfohlen)</option>
          <option value="formal">Formal</option>
          <option value="kreativ">Kreativ</option>
        </select>
        <button class="zen-btn zen-btn-ai" @click="emit('generate')">
          Bewerbung generieren
        </button>
      </div>
    </template>

    <!-- GENERATING STATE -->
    <template v-else-if="job.status === 'generating'">
      <h3 class="card-company">{{ job.quickData?.company }}</h3>
      <p class="card-position">{{ job.quickData?.title }}</p>
      <div class="generating-indicator">
        <span class="generating-spinner" />
        <span class="generating-text">{{ progressMessage || 'Anschreiben wird generiert...' }}</span>
      </div>
    </template>

    <!-- COMPLETED STATE -->
    <template v-else-if="job.status === 'completed'">
      <h3 class="card-title-completed">
        {{ job.quickData?.title }} bei {{ job.quickData?.company }}
      </h3>
      <p class="card-preview">{{ einleitungPreview }}</p>
      <div class="card-action-buttons">
        <button class="zen-btn zen-btn-ai" @click="emit('download-pdf')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          PDF herunterladen
        </button>
        <button class="zen-btn zen-btn-secondary" @click="emit('download-email')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          E-Mail-Entwurf
        </button>
        <button class="zen-btn zen-btn-ghost" @click="emit('view-application')">
          Ansehen
        </button>
      </div>
    </template>

    <!-- ERROR STATE -->
    <template v-else-if="job.status === 'error'">
      <p class="error-message">{{ job.error }}</p>
      <div class="card-action-buttons">
        <button class="zen-btn zen-btn-ai" @click="emit('retry')">
          Erneut versuchen
        </button>
        <button class="zen-btn zen-btn-ghost" @click="emit('remove')">
          Entfernen
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  job: {
    type: Object,
    required: true
    // Shape: { id, url, status, quickData, editableData, tone, generatedApp, error }
    // status: 'extracting' | 'extracted' | 'generating' | 'completed' | 'error'
  },
  progressMessage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'generate',
  'remove',
  'retry',
  'download-pdf',
  'download-email',
  'view-application',
  'update:tone'
])

const displayUrl = computed(() => {
  try {
    return new URL(props.job.url).hostname
  } catch {
    return props.job.url
  }
})

const einleitungPreview = computed(() => {
  const text = props.job.generatedApp?.einleitung || ''
  if (text.length <= 150) return text
  return text.substring(0, 150) + '...'
})

const portalClass = computed(() => {
  const portal = props.job.quickData?.portal_id || props.job.quickData?.portal || ''
  const key = portal.toLowerCase()
  if (key.includes('stepstone')) return 'portal-stepstone'
  if (key.includes('indeed')) return 'portal-indeed'
  if (key.includes('xing')) return 'portal-xing'
  if (key.includes('arbeitsagentur')) return 'portal-arbeitsagentur'
  return 'portal-generic'
})
</script>

<style scoped>
/* Animations */
@keyframes card-pulse {
  0%, 100% { box-shadow: 0 0 0 0 hsla(217, 91%, 60%, 0); }
  50% { box-shadow: 0 0 0 3px hsla(217, 91%, 60%, 0.25); }
}

@keyframes card-enter {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Card base */
.job-card {
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  animation: card-enter 0.3s ease-out;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}

.job-card--generating {
  animation: card-pulse 2s ease-in-out infinite;
}

.job-card--completed {
  border-left: 3px solid var(--color-koke, #7a8b6e);
}

.job-card--error {
  border-left: 3px solid #b45050;
}

/* Card header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

/* Remove button */
.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: var(--transition-base);
  flex-shrink: 0;
  margin-left: auto;
}

.remove-btn:hover {
  background: var(--color-washi-aged, rgba(0, 0, 0, 0.05));
  color: var(--color-sumi);
}

/* Portal tags */
.portal-tag {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.portal-tag.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-tag.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-tag.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-tag.portal-arbeitsagentur {
  background: rgba(0, 68, 103, 0.15);
  color: #004467;
}

.portal-tag.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

/* Skeleton shimmer (extracting state) */
.skeleton-line {
  height: 16px;
  background: linear-gradient(90deg, var(--color-washi-aged) 25%, var(--color-washi-warm) 50%, var(--color-washi-aged) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton-tag {
  width: 80px;
  height: 22px;
}

.skeleton-title {
  width: 60%;
  height: 20px;
  margin-bottom: var(--space-xs);
}

.skeleton-subtitle {
  width: 40%;
  height: 16px;
  margin-bottom: var(--space-md);
}

.extracting-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: var(--space-sm) 0 var(--space-xs);
}

.extracting-url {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: 0;
  word-break: break-all;
}

/* Extracted / generating state */
.card-company {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs);
}

.card-position {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-md);
}

.card-actions-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.tone-select {
  appearance: none;
  background: var(--color-washi);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-xs) var(--space-lg) var(--space-xs) var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-sumi);
  cursor: pointer;
  transition: var(--transition-base);
  background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%23666' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-sm) center;
}

.tone-select:hover {
  border-color: var(--color-ai, hsl(217, 91%, 60%));
}

.tone-select:focus {
  outline: none;
  border-color: var(--color-ai, hsl(217, 91%, 60%));
  box-shadow: 0 0 0 2px hsla(217, 91%, 60%, 0.15);
}

/* Generating state */
.generating-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.generating-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border-light);
  border-top-color: var(--color-ai, hsl(217, 91%, 60%));
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.generating-text {
  font-size: 0.875rem;
  color: var(--color-ai, hsl(217, 91%, 60%));
  font-weight: 500;
}

/* Completed state */
.card-title-completed {
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin: 0 0 var(--space-sm);
}

.card-preview {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0 0 var(--space-md);
}

.card-action-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.card-action-buttons .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

/* Error state */
.error-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #b45050;
}

.error-message {
  font-size: 0.875rem;
  color: #b45050;
  line-height: 1.5;
  margin: 0 0 var(--space-md);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .card-action-buttons {
    flex-direction: column;
    align-items: stretch;
  }

  .card-action-buttons .zen-btn {
    justify-content: center;
    width: 100%;
  }

  .card-actions-row {
    flex-direction: column;
    align-items: stretch;
  }

  .tone-select {
    width: 100%;
  }

  .skeleton-title {
    width: 80%;
  }

  .skeleton-subtitle {
    width: 55%;
  }
}
</style>
