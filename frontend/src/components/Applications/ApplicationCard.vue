<template>
  <div
    class="application-card zen-card stagger-item"
    role="listitem"
    data-testid="application-card"
    @click="$emit('open-details')"
  >
    <div class="card-header">
      <div class="card-title-group">
        <h3>{{ application.firma }}</h3>
        <p class="card-position">{{ application.position || t('applications.positionNotSpecified') }}</p>
      </div>
      <StatusBadge :status="application.status" />
    </div>

    <div class="card-meta">
      <span class="meta-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        {{ formatDate(application.datum) }}
      </span>
      <span v-if="application.job_fit_score !== null" class="meta-item">
        <span :class="['job-fit-badge', getJobFitClass(application.job_fit_score)]">
          {{ application.job_fit_score }}%
        </span>
      </span>
      <span v-if="application.quelle" class="meta-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        {{ getDomain(application.quelle) }}
      </span>
    </div>

    <div v-if="application.notizen" class="card-notes">
      {{ application.notizen.slice(0, 80) }}{{ application.notizen.length > 80 ? '...' : '' }}
    </div>

    <div class="card-actions" @click.stop>
      <button @click="$emit('download-pdf')" class="zen-btn zen-btn-sm">
        PDF
      </button>
      <button @click="$emit('open-details')" class="zen-btn zen-btn-ai zen-btn-sm">
        {{ t('applications.details') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import StatusBadge from './StatusBadge.vue'
import { getFullLocale } from '../../i18n'

const { t } = useI18n()

defineProps({
  application: { type: Object, required: true }
})

defineEmits(['open-details', 'download-pdf'])

const formatDate = (date) => {
  return new Date(date).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const getDomain = (url) => {
  try {
    const domain = new URL(url).hostname
    return domain.replace('www.', '')
  } catch {
    return url
  }
}

const getJobFitClass = (score) => {
  if (score >= 80) return 'job-fit-excellent'
  if (score >= 60) return 'job-fit-good'
  if (score >= 40) return 'job-fit-medium'
  return 'job-fit-low'
}
</script>

<style scoped>
.application-card {
  padding: var(--space-lg);
  cursor: pointer;
  transition: all var(--transition-base);
}

.application-card:hover {
  border-color: var(--color-ai);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.card-title-group {
  flex: 1;
  min-width: 0;
}

.card-title-group h3 {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-position {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-md);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.meta-item svg {
  color: var(--color-stone);
}

.card-notes {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.card-actions {
  display: flex;
  gap: var(--space-sm);
}

.job-fit-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.job-fit-excellent {
  background-color: var(--color-success-muted, #dcfce7);
  color: var(--color-success, #16a34a);
}

.job-fit-good {
  background-color: var(--color-ai-muted, #dbeafe);
  color: var(--color-ai, #2563eb);
}

.job-fit-medium {
  background-color: var(--color-warning-muted, #fef3c7);
  color: var(--color-warning, #d97706);
}

.job-fit-low {
  background-color: var(--color-error-muted, #fee2e2);
  color: var(--color-error, #dc2626);
}

@media (max-width: 480px) {
  .card-actions {
    flex-direction: column;
  }
}
</style>
