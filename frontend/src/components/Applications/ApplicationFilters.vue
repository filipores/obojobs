<template>
  <div>
    <!-- Status Filter Tabs -->
    <section class="status-tabs-section animate-fade-up" style="animation-delay: 125ms;">
      <div class="status-tabs" role="tablist" :aria-label="t('applications.statusFilterLabel')">
        <button
          v-for="status in statusOptions"
          :key="status.value"
          :class="['status-tab', { 'status-tab-active': filterStatus === status.value }]"
          @click="$emit('update:filterStatus', status.value)"
          role="tab"
          :aria-selected="filterStatus === status.value"
          :aria-controls="'applications-list'"
        >
          <span class="status-tab-label">{{ status.label }}</span>
          <span class="status-tab-count">{{ status.count }}</span>
        </button>
      </div>
    </section>

    <!-- Filter Section -->
    <section class="filter-section animate-fade-up" style="animation-delay: 150ms;">
      <div class="filter-row">
        <div class="search-group">
          <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            :value="searchInput"
            @input="$emit('update:searchInput', $event.target.value)"
            type="text"
            :placeholder="t('applications.searchPlaceholder')"
            class="form-input search-input"
          />
        </div>
        <div class="filter-group sort-group">
          <select :value="sortBy" @change="$emit('update:sortBy', $event.target.value)" class="form-select">
            <option value="datum_desc">{{ t('applications.sortDateDesc') }}</option>
            <option value="datum_asc">{{ t('applications.sortDateAsc') }}</option>
            <option value="firma_asc">{{ t('applications.sortCompanyAsc') }}</option>
            <option value="firma_desc">{{ t('applications.sortCompanyDesc') }}</option>
            <option value="status">{{ t('applications.sortStatus') }}</option>
          </select>
        </div>
        <div class="view-toggle" role="group" :aria-label="t('applications.switchView')">
          <button
            :class="['view-toggle-btn', { active: viewMode === 'grid' }]"
            @click="$emit('update:viewMode', 'grid')"
            :aria-pressed="viewMode === 'grid'"
            :title="t('applications.gridView')"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
            </svg>
          </button>
          <button
            :class="['view-toggle-btn', { active: viewMode === 'table' }]"
            @click="$emit('update:viewMode', 'table')"
            :aria-pressed="viewMode === 'table'"
            :title="t('applications.tableView')"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
        </div>
      </div>

      <div v-if="searchQuery || filterStatus || filterFirma" class="active-filters">
        <span v-if="searchQuery" class="filter-tag">
          "{{ searchQuery }}"
          <button @click="$emit('clear-search')" class="filter-tag-close">&times;</button>
        </span>
        <span v-if="filterStatus" class="filter-tag">
          {{ getStatusLabel(filterStatus) }}
          <button @click="$emit('update:filterStatus', '')" class="filter-tag-close">&times;</button>
        </span>
        <span v-if="filterFirma" class="filter-tag filter-tag-firma">
          {{ t('applications.companyLabel') }}: {{ filterFirma }}
          <button @click="$emit('clear-filters')" class="filter-tag-close">&times;</button>
        </span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({
  statusOptions: { type: Array, required: true },
  filterStatus: { type: String, default: '' },
  searchInput: { type: String, default: '' },
  searchQuery: { type: String, default: '' },
  sortBy: { type: String, default: 'datum_desc' },
  viewMode: { type: String, default: 'grid' },
  filterFirma: { type: String, default: '' }
})

defineEmits([
  'update:filterStatus',
  'update:searchInput',
  'update:sortBy',
  'update:viewMode',
  'clear-search',
  'clear-filters'
])

const getStatusLabel = (status) => {
  const labels = {
    'erstellt': t('applications.statusCreated'),
    'versendet': t('applications.statusSent'),
    'antwort_erhalten': t('applications.statusResponse'),
    'absage': t('applications.statusRejection'),
    'zusage': t('applications.statusAcceptance')
  }
  return labels[status] || status
}
</script>

<style scoped>
.status-tabs-section {
  margin-bottom: var(--space-md);
}

.status-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.status-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.status-tab:hover {
  background: var(--color-washi-aged);
  border-color: var(--color-stone);
  color: var(--color-sumi);
}

.status-tab:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}

.status-tab-active {
  background: var(--color-ai);
  border-color: var(--color-ai);
  color: var(--color-washi);
}

.status-tab-active:hover {
  background: var(--color-ai-dark, #2d4a5a);
  border-color: var(--color-ai-dark, #2d4a5a);
  color: var(--color-washi);
}

.status-tab-label {
  white-space: nowrap;
}

.status-tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-xs);
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
}

.status-tab-active .status-tab-count {
  background: rgba(255, 255, 255, 0.25);
}

.filter-section {
  margin-bottom: var(--space-ma);
}

.filter-row {
  display: flex;
  gap: var(--space-md);
}

.search-group {
  flex: 1;
  position: relative;
}

.search-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-stone);
  pointer-events: none;
}

.search-input {
  padding-left: calc(var(--space-md) + 26px);
}

.filter-group {
  min-width: 200px;
}

.sort-group {
  min-width: 220px;
}

.active-filters {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
}

.filter-tag-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
}

.filter-tag-close:hover {
  opacity: 1;
}

.filter-tag-firma {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.view-toggle {
  display: flex;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 38px;
  background: transparent;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  transition: all var(--transition-base);
}

.view-toggle-btn:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

.view-toggle-btn.active {
  background: var(--color-ai);
  color: var(--color-washi);
}

.view-toggle-btn:first-child {
  border-right: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
  }

  .filter-group {
    min-width: 100%;
  }

  .status-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: var(--space-sm);
    -webkit-overflow-scrolling: touch;
  }

  .status-tab {
    flex-shrink: 0;
  }

  .view-toggle {
    display: none;
  }
}
</style>
