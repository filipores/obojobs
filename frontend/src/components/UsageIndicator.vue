<template>
  <div class="usage-indicator" :class="statusClass">
    <div class="usage-header">
      <div class="usage-label">
        <svg v-if="isAtLimit" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <svg v-else-if="isNearLimit" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span v-if="isAtLimit">Keine Credits mehr</span>
        <span v-else-if="isNearLimit">Wenige Credits übrig</span>
        <span v-else>Verfügbar</span>
      </div>
      <div class="usage-count">
        <strong>{{ limit }}</strong> Credits
      </div>
    </div>

    <div v-if="isAtLimit" class="usage-cta">
      <p>Kaufe einen Karriere-Pass für mehr Bewerbungen</p>
      <router-link to="/subscription" class="zen-btn zen-btn-sm zen-btn-ai">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
        Credits kaufen
      </router-link>
    </div>
    <div v-else-if="isNearLimit" class="usage-hint">
      <router-link to="/subscription">Mehr Credits kaufen</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  used: {
    type: Number,
    default: 0
  },
  limit: {
    type: Number,
    default: 3
  },
  unlimited: {
    type: Boolean,
    default: false
  },
  plan: {
    type: String,
    default: 'free'
  }
})

const isNearLimit = computed(() => props.limit > 0 && props.limit <= 3)

const isAtLimit = computed(() => props.limit <= 0)

const statusClass = computed(() => {
  if (isAtLimit.value) return 'status-limit'
  if (isNearLimit.value) return 'status-warning'
  return 'status-normal'
})
</script>

<style scoped>
.usage-indicator {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg);
}

.usage-indicator.status-warning {
  background: var(--color-warning-light);
  border-color: var(--color-warning);
}

.usage-indicator.status-limit {
  background: var(--color-error-light);
  border-color: var(--color-error);
}

.usage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
}

.usage-label {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.status-warning .usage-label {
  color: var(--color-warning);
}

.status-limit .usage-label {
  color: var(--color-error);
}

.usage-label svg {
  flex-shrink: 0;
}

.usage-count {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.usage-count strong {
  color: var(--color-text-primary);
}

.usage-cta {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-error);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  text-align: center;
}

.usage-cta p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-error);
}

.usage-hint {
  margin-top: var(--space-sm);
  font-size: 0.75rem;
  text-align: right;
}

.usage-hint a {
  color: var(--color-warning);
  text-decoration: none;
}

.usage-hint a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .usage-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }

  .usage-cta {
    flex-direction: column;
  }
}
</style>
