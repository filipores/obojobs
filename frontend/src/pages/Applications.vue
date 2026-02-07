<template>
  <div class="applications-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <div class="page-header-content">
          <div>
            <h1>{{ t('applications.title') }}</h1>
            <p class="page-subtitle">{{ t('applications.subtitle') }}</p>
          </div>
          <div class="export-section">
            <label class="export-filter-toggle" v-if="hasActiveFilters">
              <input type="checkbox" v-model="exportFilteredOnly" />
              <span>{{ t('applications.filteredOnly', { count: filteredApplications.length }) }}</span>
            </label>
            <div class="export-buttons">
              <button
                @click="exportApplications('csv')"
                class="zen-btn zen-btn-sm"
                :disabled="isExportDisabled"
                :title="exportDisabledReason"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                CSV
              </button>
              <button
                @click="exportApplications('pdf')"
                class="zen-btn zen-btn-sm"
                :disabled="isExportDisabled"
                :title="exportDisabledReason"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                PDF
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Stats Section -->
      <section class="stats-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ totalApplications }}</span>
            <span class="stat-label">{{ t('applications.total') }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.erstellt }}</span>
            <span class="stat-label">{{ t('applications.created') }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.versendet }}</span>
            <span class="stat-label">{{ t('applications.sent') }}</span>
          </div>
        </div>
      </section>

      <!-- Filters -->
      <ApplicationFilters
        :status-options="statusOptions"
        :filter-status="filterStatus"
        :search-input="searchInput"
        :search-query="searchQuery"
        :sort-by="sortBy"
        :view-mode="viewMode"
        :filter-firma="filterFirma"
        @update:filter-status="filterStatus = $event"
        @update:search-input="searchInput = $event"
        @update:sort-by="sortBy = $event"
        @update:view-mode="viewMode = $event"
        @clear-search="searchInput = ''; searchQuery = ''"
        @clear-filters="clearFilters"
      />

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Loading State - Skeleton -->
      <div v-if="loading" class="loading-skeleton" :aria-label="t('applications.loadingApplications')" data-testid="loading-state">
        <div class="skeleton-grid">
          <div v-for="i in 6" :key="i" class="skeleton-card zen-card">
            <div class="skeleton-card-header">
              <div class="skeleton-title-group">
                <div class="skeleton skeleton-company"></div>
                <div class="skeleton skeleton-position"></div>
              </div>
              <div class="skeleton skeleton-status"></div>
            </div>
            <div class="skeleton-card-meta">
              <div class="skeleton skeleton-date"></div>
              <div class="skeleton skeleton-source"></div>
            </div>
            <div class="skeleton skeleton-notes"></div>
            <div class="skeleton-card-actions">
              <div class="skeleton skeleton-btn-sm"></div>
              <div class="skeleton skeleton-btn-sm"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="error-state" data-testid="error-state">
        <div class="error-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <h3>{{ t('applications.loadErrorTitle') }}</h3>
        <p>{{ t('applications.loadErrorMessage') }}</p>
        <button @click="loadApplications()" class="zen-btn zen-btn-ai">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
          </svg>
          {{ t('applications.retryLoad') }}
        </button>
      </div>

      <!-- Applications List -->
      <section v-else-if="filteredApplications.length > 0" id="applications-list" class="applications-section" aria-live="polite">
        <ApplicationList
          :applications="filteredApplications"
          :view-mode="viewMode"
          :sort-by="sortBy"
          :current-page="currentPage"
          :total-pages="totalPages"
          :total-applications="totalApplications"
          @open-details="openDetails"
          @download-pdf="downloadPDF"
          @toggle-sort="toggleTableSort"
          @go-to-page="goToPage"
        />
      </section>

      <!-- Empty State -->
      <section v-else id="applications-list" class="empty-state" data-testid="empty-state" aria-live="polite">
        <div class="empty-enso" aria-hidden="true"></div>
        <h3>{{ searchQuery || filterStatus || filterFirma ? t('applications.noResults') : t('applications.noApplicationsYet') }}</h3>
        <p v-if="searchQuery || filterStatus || filterFirma">
          {{ t('applications.noApplicationsFound') }}
        </p>
        <p v-else>
          {{ t('applications.createFirst') }}
        </p>
        <router-link v-if="!(searchQuery || filterStatus || filterFirma)" to="/new-application" class="zen-btn zen-btn-ai" data-testid="new-application-btn">
          {{ t('applications.createNew') }}
        </router-link>
        <button v-if="searchQuery || filterStatus || filterFirma" @click="clearFilters" class="zen-btn" data-testid="clear-filters-btn">
          {{ t('applications.resetFilters') }}
        </button>
      </section>

      <!-- Detail Modal -->
      <ApplicationDetail
        :selected-app="selectedApp"
        :job-fit-data="jobFitData"
        :job-fit-loading="jobFitLoading"
        @close="closeDetails"
        @update-status="updateStatus"
        @update-notes="updateNotes"
        @download-pdf="downloadPDF"
        @download-email-draft="downloadEmailDraft"
        @delete="deleteApp"
        @interview-updated="onInterviewUpdated"
        @ats-optimized="onATSOptimized"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import { confirm } from '../composables/useConfirm'
import { useI18n } from 'vue-i18n'
import ApplicationFilters from '../components/Applications/ApplicationFilters.vue'
import ApplicationList from '../components/Applications/ApplicationList.vue'
import ApplicationDetail from '../components/Applications/ApplicationDetail.vue'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

const applications = ref([])
const selectedApp = ref(null)
const loading = ref(false)
const loadError = ref(false)
const searchInput = ref('')
const searchQuery = ref('')
let searchTimeout = null
const filterStatus = ref('')
const filterFirma = ref('')
const sortBy = ref('datum_desc')
const exportFilteredOnly = ref(false)
const viewMode = ref(localStorage.getItem('applications_view_mode') || 'grid')

const currentPage = ref(1)
const totalPages = ref(1)
const totalApplications = ref(0)
const perPage = ref(15)

const jobFitData = ref(null)
const jobFitLoading = ref(false)

const stats = computed(() => {
  return {
    erstellt: applications.value.filter(a => a.status === 'erstellt').length,
    versendet: applications.value.filter(a => a.status === 'versendet').length
  }
})

const statusOptions = computed(() => {
  const counts = {
    '': applications.value.length,
    'erstellt': applications.value.filter(a => a.status === 'erstellt').length,
    'versendet': applications.value.filter(a => a.status === 'versendet').length,
    'antwort_erhalten': applications.value.filter(a => a.status === 'antwort_erhalten').length,
    'absage': applications.value.filter(a => a.status === 'absage').length,
    'zusage': applications.value.filter(a => a.status === 'zusage').length
  }
  return [
    { value: '', label: t('applications.statusAll'), count: counts[''] },
    { value: 'erstellt', label: t('applications.statusCreated'), count: counts['erstellt'] },
    { value: 'versendet', label: t('applications.statusSent'), count: counts['versendet'] },
    { value: 'antwort_erhalten', label: t('applications.statusResponse'), count: counts['antwort_erhalten'] },
    { value: 'absage', label: t('applications.statusRejection'), count: counts['absage'] },
    { value: 'zusage', label: t('applications.statusAcceptance'), count: counts['zusage'] }
  ]
})

const filteredApplications = computed(() => {
  let filtered = applications.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(app =>
      app.firma.toLowerCase().includes(query) ||
      (app.position && app.position.toLowerCase().includes(query))
    )
  }

  if (filterStatus.value) {
    filtered = filtered.filter(app => app.status === filterStatus.value)
  }

  if (filterFirma.value) {
    filtered = filtered.filter(app => app.firma === filterFirma.value)
  }

  return [...filtered].sort((a, b) => {
    switch (sortBy.value) {
      case 'datum_desc':
        return new Date(b.datum) - new Date(a.datum)
      case 'datum_asc':
        return new Date(a.datum) - new Date(b.datum)
      case 'firma_asc':
        return a.firma.localeCompare(b.firma, 'de')
      case 'firma_desc':
        return b.firma.localeCompare(a.firma, 'de')
      case 'status': {
        const statusOrder = ['zusage', 'antwort_erhalten', 'versendet', 'erstellt', 'absage']
        return statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status)
      }
      default:
        return new Date(b.datum) - new Date(a.datum)
    }
  })
})

const hasActiveFilters = computed(() => {
  return !!(searchQuery.value || filterStatus.value || filterFirma.value)
})

const isExportDisabled = computed(() => {
  if (applications.value.length === 0) return true
  if (exportFilteredOnly.value && filteredApplications.value.length === 0) return true
  return false
})

const exportDisabledReason = computed(() => {
  if (applications.value.length === 0) {
    return t('applications.exportNoApplications')
  }
  if (exportFilteredOnly.value && filteredApplications.value.length === 0) {
    return t('applications.exportNoFilteredResults')
  }
  return ''
})

const loadApplications = async (page = 1) => {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await api.silent.get('/applications', {
      params: {
        page,
        per_page: perPage.value
      }
    })
    applications.value = data.applications || []
    currentPage.value = data.page || 1
    totalPages.value = data.pages || 1
    totalApplications.value = data.total || 0
    loadError.value = false
  } catch (err) {
    console.error('Fehler beim Laden:', err)
    loadError.value = true
    applications.value = []
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    loadApplications(page)
  }
}

const downloadPDF = async (id) => {
  try {
    const response = await api.get(`/applications/${id}/pdf`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bewerbung_${id}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.pdfDownloadError'), 'error') }
  }
}

const openDetails = (app) => {
  selectedApp.value = { ...app }
  loadJobFitData(app.id)
}

const loadJobFitData = async (appId) => {
  jobFitData.value = null
  jobFitLoading.value = true
  try {
    const { data } = await api.get(`/applications/${appId}/job-fit?include_recommendations=true`)
    if (data.success) {
      jobFitData.value = data.job_fit
    }
  } catch {
    // Silently fail - job fit data is optional
  } finally {
    jobFitLoading.value = false
  }
}

const closeDetails = () => {
  selectedApp.value = null
}

const updateStatus = async (app) => {
  try {
    await api.put(`/applications/${app.id}`, {
      status: app.status
    })
    const index = applications.value.findIndex(a => a.id === app.id)
    if (index !== -1) {
      applications.value[index].status = app.status
    }
    if (selectedApp.value) {
      selectedApp.value.status = app.status
    }
    if (window.$toast) {
      window.$toast(t('applications.statusChangedSuccess'), 'success')
    }
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.statusChangeError'), 'error') }
  }
}

const updateNotes = async (app) => {
  try {
    await api.put(`/applications/${app.id}`, {
      notizen: app.notizen
    })
    const index = applications.value.findIndex(a => a.id === app.id)
    if (index !== -1) {
      applications.value[index].notizen = app.notizen
    }
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.noteSaveError'), 'error') }
  }
}

const deleteApp = async (id) => {
  const confirmed = await confirm({
    title: t('applications.deleteConfirmTitle'),
    message: t('applications.deleteConfirmMessage'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/applications/${id}`)
    if (selectedApp.value && selectedApp.value.id === id) {
      selectedApp.value = null
    }
    const pageToLoad = applications.value.length === 1 && currentPage.value > 1
      ? currentPage.value - 1
      : currentPage.value
    loadApplications(pageToLoad)
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.deleteError'), 'error') }
  }
}

const clearFilters = () => {
  searchInput.value = ''
  searchQuery.value = ''
  filterStatus.value = ''
  filterFirma.value = ''
  if (route.query.firma) {
    router.replace({ path: '/applications' })
  }
}

const toggleTableSort = (field) => {
  if (field === 'firma') {
    sortBy.value = sortBy.value === 'firma_asc' ? 'firma_desc' : 'firma_asc'
  } else if (field === 'datum') {
    sortBy.value = sortBy.value === 'datum_desc' ? 'datum_asc' : 'datum_desc'
  } else if (field === 'status') {
    sortBy.value = 'status'
  }
}

const onATSOptimized = (data) => {
  if (selectedApp.value && data.optimized_text) {
    selectedApp.value.email_text = data.optimized_text
  }
}

const onInterviewUpdated = (updatedApp) => {
  if (selectedApp.value) {
    selectedApp.value.interview_date = updatedApp.interview_date
    selectedApp.value.interview_result = updatedApp.interview_result
    selectedApp.value.interview_feedback = updatedApp.interview_feedback
  }
  const index = applications.value.findIndex(a => a.id === updatedApp.id)
  if (index !== -1) {
    applications.value[index] = { ...applications.value[index], ...updatedApp }
  }
}

const exportApplications = async (format) => {
  try {
    const params = new URLSearchParams({ format })

    if (exportFilteredOnly.value && hasActiveFilters.value) {
      if (searchQuery.value) params.append('search', searchQuery.value)
      if (filterStatus.value) params.append('status', filterStatus.value)
      if (filterFirma.value) params.append('firma', filterFirma.value)
    }

    const response = await api.get(`/applications/export?${params}`, {
      responseType: 'blob'
    })
    const blob = new Blob([response.data], {
      type: format === 'pdf' ? 'application/pdf' : 'text/csv'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const today = new Date().toISOString().split('T')[0]
    const suffix = exportFilteredOnly.value && hasActiveFilters.value ? '_gefiltert' : ''
    link.download = `bewerbungen${suffix}_${today}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.exportError'), 'error') }
  }
}

const downloadEmailDraft = async (app) => {
  try {
    const response = await api.get(`/applications/${app.id}/email-draft`, {
      responseType: 'blob'
    })
    const blob = new Blob([response.data], { type: 'message/rfc822' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const firma = app.firma || 'Bewerbung'
    link.download = `Bewerbung_${firma}.eml`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    if (window.$toast) {
      window.$toast(t('applications.emlDownloaded'), 'success', 6000)
    }
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.emailDraftError'), 'error') }
  }
}

const handleEscapeKey = (event) => {
  if (event.key === 'Escape') {
    if (selectedApp.value) {
      closeDetails()
    }
  }
}

onMounted(() => {
  if (route.query.firma) {
    filterFirma.value = route.query.firma
  }
  loadApplications()
  document.addEventListener('keydown', handleEscapeKey)
})

onUnmounted(() => {
  if (searchTimeout) clearTimeout(searchTimeout)
  document.removeEventListener('keydown', handleEscapeKey)
})

watch(() => route.query.firma, (newFirma) => {
  filterFirma.value = newFirma || ''
})

watch(searchInput, (newVal) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    searchQuery.value = newVal
  }, 300)
})

watch(hasActiveFilters, (isActive) => {
  if (!isActive) {
    exportFilteredOnly.value = false
  }
})

watch(viewMode, (newMode) => {
  localStorage.setItem('applications_view_mode', newMode)
})
</script>

<style scoped>
.applications-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

.page-header {
  padding: var(--space-ma-lg) 0 var(--space-ma);
}

.page-header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
}

.page-header h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
}

.page-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0;
}

.export-buttons {
  display: flex;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.export-buttons .zen-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.export-buttons .zen-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats-section {
  margin-bottom: var(--space-lg);
}

.stats-grid {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 500;
  color: var(--color-ai);
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-top: var(--space-xs);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-sand);
}

.loading-skeleton {
  padding: var(--space-ma) 0;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-lg);
}

.skeleton-card {
  padding: var(--space-lg);
}

.skeleton-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.skeleton-title-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-company {
  width: 60%;
  height: 1.25rem;
}

.skeleton-position {
  width: 40%;
  height: 1rem;
}

.skeleton-status {
  width: 70px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-card-meta {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-md);
}

.skeleton-date {
  width: 90px;
  height: 1rem;
}

.skeleton-source {
  width: 80px;
  height: 1rem;
}

.skeleton-notes {
  width: 100%;
  height: 60px;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.skeleton-card-actions {
  display: flex;
  gap: var(--space-sm);
}

.skeleton-btn-sm {
  width: 60px;
  height: 2rem;
  border-radius: var(--radius-md);
}

.skeleton {
  background: linear-gradient(90deg, var(--color-washi-aged) 25%, var(--color-washi-warm) 50%, var(--color-washi-aged) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.8s ease infinite;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.applications-section {
  margin-top: var(--space-ma);
}

.error-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.error-icon {
  color: var(--color-terra);
  margin: 0 auto var(--space-lg);
}

.error-state h3 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.error-state p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

.error-state .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.empty-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.empty-enso {
  width: 100px;
  height: 100px;
  margin: 0 auto var(--space-lg);
  border: 2px solid var(--color-sand);
  border-width: 2px 3px 2px 2.5px;
  border-radius: 50%;
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.empty-state p {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-lg);
}

@media (max-width: 768px) {
  .page-header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .export-buttons {
    justify-content: flex-start;
  }

  .skeleton-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }
}
</style>
