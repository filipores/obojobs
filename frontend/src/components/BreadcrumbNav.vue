<template>
  <nav v-if="breadcrumbs.length > 1" class="breadcrumb-nav" aria-label="Breadcrumb">
    <ol class="breadcrumb-list">
      <li v-for="(crumb, index) in breadcrumbs" :key="crumb.path" class="breadcrumb-item">
        <router-link
          v-if="index < breadcrumbs.length - 1"
          :to="crumb.path"
          class="breadcrumb-link"
        >
          {{ crumb.label }}
        </router-link>
        <span v-else class="breadcrumb-current" aria-current="page">{{ crumb.label }}</span>
        <svg v-if="index < breadcrumbs.length - 1" class="breadcrumb-separator" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </li>
    </ol>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()

function resolveBreadcrumbLabel(bc) {
  if (typeof bc.label === 'function') return bc.label(route)
  if (bc.labelKey) return t(bc.labelKey)
  return bc.label
}

const breadcrumbs = computed(() => {
  const crumbs = [{ path: '/dashboard', label: 'Dashboard' }]

  if (route.meta?.breadcrumbs) {
    for (const bc of route.meta.breadcrumbs) {
      crumbs.push({
        path: bc.path || route.path,
        label: resolveBreadcrumbLabel(bc)
      })
    }
  } else if (route.meta?.titleKey && route.path !== '/dashboard') {
    crumbs.push({
      path: route.path,
      label: t(route.meta.titleKey)
    })
  }

  return crumbs
})
</script>

<style scoped>
.breadcrumb-nav {
  padding: var(--space-sm) 0;
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  list-style: none;
  padding: 0;
  margin: 0;
  flex-wrap: wrap;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.breadcrumb-link {
  color: var(--color-text-tertiary);
  text-decoration: none;
  font-size: 0.8125rem;
  transition: color var(--transition-base);
}

.breadcrumb-link:hover {
  color: var(--color-ai);
}

.breadcrumb-current {
  color: var(--color-text-primary);
  font-size: 0.8125rem;
  font-weight: 500;
}

.breadcrumb-separator {
  color: var(--color-text-ghost);
  flex-shrink: 0;
}
</style>
