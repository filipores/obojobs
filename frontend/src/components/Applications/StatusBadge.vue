<template>
  <span :class="['status-badge', `status-${status}`, { 'status-badge-sm': size === 'sm' }]">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  status: { type: String, required: true },
  size: { type: String, default: 'default' }
})

const label = computed(() => {
  const labels = {
    'erstellt': t('applications.statusCreated'),
    'versendet': t('applications.statusSent'),
    'antwort_erhalten': t('applications.statusResponse'),
    'absage': t('applications.statusRejection'),
    'zusage': t('applications.statusAcceptance')
  }
  return labels[props.status] || props.status
})
</script>

<style scoped>
.status-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  white-space: nowrap;
}

.status-badge-sm {
  font-size: 0.625rem;
  padding: 2px var(--space-sm);
}

.status-erstellt {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.status-versendet {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.status-antwort_erhalten {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.status-absage {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.status-zusage {
  background: var(--color-koke);
  color: var(--color-washi);
}
</style>
