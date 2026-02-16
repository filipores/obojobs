<template>
  <div>
    <!-- Grid View -->
    <div v-if="viewMode === 'grid'" class="applications-grid" role="list" data-testid="applications-grid">
      <ApplicationCard
        v-for="app in applications"
        :key="app.id"
        :application="app"
        @open-details="$emit('open-details', app)"
        @download-pdf="$emit('download-pdf', app.id)"
      />
    </div>

    <!-- Table View -->
    <ScrollableTable v-else class="applications-table-wrapper" data-testid="applications-table">
      <table class="applications-table">
        <thead>
          <tr>
            <th
              @click="$emit('toggle-sort', 'firma')"
              @keydown="handleSortKeydown($event, 'firma')"
              class="sortable-header"
              tabindex="0"
              role="columnheader"
              aria-sort="none"
            >
              {{ t('applications.tableCompany') }}
              <span v-if="sortBy.startsWith('firma')" class="sort-indicator">
                {{ sortBy === 'firma_asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th>{{ t('applications.tablePosition') }}</th>
            <th
              @click="$emit('toggle-sort', 'datum')"
              @keydown="handleSortKeydown($event, 'datum')"
              class="sortable-header"
              tabindex="0"
              role="columnheader"
              aria-sort="none"
            >
              {{ t('applications.tableDate') }}
              <span v-if="sortBy.startsWith('datum')" class="sort-indicator">
                {{ sortBy === 'datum_asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th
              @click="$emit('toggle-sort', 'status')"
              @keydown="handleSortKeydown($event, 'status')"
              class="sortable-header"
              tabindex="0"
              role="columnheader"
              aria-sort="none"
            >
              {{ t('applications.tableStatus') }}
              <span v-if="sortBy === 'status'" class="sort-indicator">&#x25CF;</span>
            </th>
            <th>{{ t('applications.tableJobFit') }}</th>
            <th>{{ t('applications.tableSource') }}</th>
            <th class="actions-header">{{ t('applications.tableActions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="app in applications"
            :key="app.id"
            class="table-row"
            @click="$emit('open-details', app)"
          >
            <td class="cell-firma">{{ app.firma }}</td>
            <td class="cell-position">{{ app.position || '–' }}</td>
            <td class="cell-datum">{{ formatDate(app.datum) }}</td>
            <td class="cell-status">
              <StatusBadge :status="app.status" size="sm" />
            </td>
            <td class="cell-job-fit">
              <span v-if="app.job_fit_score !== null" :class="['job-fit-badge', getJobFitClass(app.job_fit_score)]">
                {{ app.job_fit_score }}%
              </span>
              <span v-else class="text-muted">–</span>
            </td>
            <td class="cell-quelle">
              <a v-if="app.job_url" :href="app.job_url" target="_blank" @click.stop class="table-link">
                {{ app.quelle || getDomain(app.job_url) }}
              </a>
              <span v-else-if="app.quelle">{{ app.quelle }}</span>
              <span v-else class="text-muted">–</span>
            </td>
            <td class="cell-actions" @click.stop>
              <button @click="$emit('download-pdf', app.id)" class="zen-btn zen-btn-sm" :title="t('applications.downloadPdf')">
                PDF
              </button>
              <button @click="$emit('open-details', app)" class="zen-btn zen-btn-ai zen-btn-sm" :title="t('applications.showDetails')">
                {{ t('applications.details') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </ScrollableTable>

    <!-- Pagination -->
    <nav v-if="totalPages > 1" class="pagination" :aria-label="t('applications.paginationNav')">
      <button
        class="pagination-btn"
        :disabled="currentPage === 1"
        @click="$emit('go-to-page', currentPage - 1)"
        :aria-label="t('applications.previousPage')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>

      <div class="pagination-pages">
        <button
          v-if="currentPage > 2"
          class="pagination-btn pagination-page"
          @click="$emit('go-to-page', 1)"
        >
          1
        </button>
        <span v-if="currentPage > 3" class="pagination-ellipsis">...</span>

        <button
          v-for="page in visiblePages"
          :key="page"
          class="pagination-btn pagination-page"
          :class="{ 'pagination-page-active': page === currentPage }"
          @click="$emit('go-to-page', page)"
          :aria-current="page === currentPage ? 'page' : undefined"
        >
          {{ page }}
        </button>

        <span v-if="currentPage < totalPages - 2" class="pagination-ellipsis">...</span>
        <button
          v-if="currentPage < totalPages - 1"
          class="pagination-btn pagination-page"
          @click="$emit('go-to-page', totalPages)"
        >
          {{ totalPages }}
        </button>
      </div>

      <button
        class="pagination-btn"
        :disabled="currentPage === totalPages"
        @click="$emit('go-to-page', currentPage + 1)"
        :aria-label="t('applications.nextPage')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </nav>

    <p v-if="totalPages > 1" class="pagination-info">
      {{ t('applications.paginationInfo', { current: currentPage, total: totalPages, count: totalApplications }) }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ScrollableTable from '../ScrollableTable.vue'
import ApplicationCard from './ApplicationCard.vue'
import StatusBadge from './StatusBadge.vue'
import { getFullLocale } from '../../i18n'

const { t } = useI18n()

const props = defineProps({
  applications: { type: Array, required: true },
  viewMode: { type: String, default: 'grid' },
  sortBy: { type: String, default: 'datum_desc' },
  currentPage: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  totalApplications: { type: Number, default: 0 }
})

const emit = defineEmits(['open-details', 'download-pdf', 'toggle-sort', 'go-to-page'])

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, props.currentPage - 1)
  const end = Math.min(props.totalPages, props.currentPage + 1)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const formatDate = (date) => {
  return new Date(date).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const getDomain = (url) => {
  try {
    return new URL(url).hostname.replace('www.', '')
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

const handleSortKeydown = (event, field) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    emit('toggle-sort', field)
  }
}
</script>

<style scoped>
.applications-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-lg);
}

.applications-table-wrapper {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.applications-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.applications-table thead {
  background: var(--color-washi-aged);
  border-bottom: 1px solid var(--color-border);
}

.applications-table th {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  white-space: nowrap;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: color var(--transition-base);
}

.sortable-header:hover {
  color: var(--color-ai);
}

.sort-indicator {
  margin-left: var(--space-xs);
  color: var(--color-ai);
}

.actions-header {
  text-align: right;
}

.applications-table tbody tr {
  border-bottom: 1px solid var(--color-border-light);
  transition: background var(--transition-base);
  cursor: pointer;
}

.applications-table tbody tr:last-child {
  border-bottom: none;
}

.applications-table tbody tr:hover {
  background: var(--color-ai-subtle);
}

.applications-table td {
  padding: var(--space-md) var(--space-lg);
  vertical-align: middle;
}

.cell-firma {
  font-weight: 500;
  color: var(--color-sumi);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-position {
  color: var(--color-text-secondary);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-datum {
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.cell-status {
  white-space: nowrap;
}

.cell-job-fit {
  white-space: nowrap;
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

.cell-quelle {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-link {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.table-link:hover {
  text-decoration: underline;
}

.text-muted {
  color: var(--color-text-ghost);
}

.cell-actions {
  text-align: right;
  white-space: nowrap;
}

.cell-actions .zen-btn {
  margin-left: var(--space-xs);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-ma);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.pagination-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 40px;
  padding: var(--space-sm);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.pagination-btn:hover:not(:disabled) {
  background: var(--color-ai-subtle);
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination-pages {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.pagination-page {
  font-weight: 500;
  font-size: 0.875rem;
}

.pagination-page-active {
  background: var(--color-ai);
  border-color: var(--color-ai);
  color: var(--color-washi);
}

.pagination-page-active:hover:not(:disabled) {
  background: var(--color-ai);
  color: var(--color-washi);
}

.pagination-ellipsis {
  padding: 0 var(--space-xs);
  color: var(--color-text-tertiary);
}

.pagination-info {
  text-align: center;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-md);
}

@media (max-width: 1024px) {
  .applications-table {
    min-width: 700px;
  }
}

@media (max-width: 768px) {
  .applications-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .pagination {
    gap: var(--space-xs);
  }

  .pagination-btn {
    min-width: 36px;
    height: 36px;
  }

  .pagination-page {
    font-size: 0.8125rem;
  }
}
</style>
