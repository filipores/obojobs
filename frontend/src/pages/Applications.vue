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

      <!-- View Tabs -->
      <section class="view-tabs-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="view-tabs">
          <button
            class="view-tab"
            :class="{ active: activeTab === 'liste' }"
            @click="switchToListe"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            Liste
          </button>
          <button
            class="view-tab"
            :class="{ active: activeTab === 'timeline' }"
            @click="switchToTimeline"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Timeline
          </button>
        </div>
      </section>

      <!-- Liste Tab Content -->
      <template v-if="activeTab === 'liste'">

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

      </template>

      <!-- Timeline Tab Content -->
      <template v-else>

        <!-- Days filter -->
        <div class="timeline-filter animate-fade-up" style="animation-delay: 200ms;">
          <div class="timeline-filter-row">
            <div class="timeline-filter-group">
              <label class="filter-label">Zeitraum</label>
              <select v-model="daysFilter" @change="loadTimeline" class="form-select form-select-sm">
                <option value="7">Letzte 7 Tage</option>
                <option value="30">Letzte 30 Tage</option>
                <option value="90">Letzte 90 Tage</option>
                <option value="all">Alle</option>
              </select>
            </div>
            <div class="timeline-stats-summary">
              <span class="timeline-stat-count">{{ timelineApps.length }}</span>
              <span class="timeline-stat-label">Bewerbungen</span>
            </div>
          </div>
        </div>

        <!-- Ink Stroke -->
        <div class="ink-stroke"></div>

        <!-- Timeline loading -->
        <div v-if="timelineLoading" class="loading-state">
          <div class="loading-enso"></div>
          <p>Lade Timeline...</p>
        </div>

        <!-- Timeline grouped view -->
        <section v-else-if="groupedApplications.length > 0" class="timeline-section">
          <div class="timeline-axis">
            <div
              v-for="(group, groupIndex) in groupedApplications"
              :key="group.label"
              class="timeline-group"
            >
              <!-- Date Group Header -->
              <div class="timeline-group-header">
                <div class="timeline-axis-marker">
                  <div class="axis-dot"></div>
                </div>
                <div class="timeline-group-label">{{ group.label }}</div>
              </div>

              <!-- Applications in Group -->
              <div class="timeline-group-items">
                <div
                  v-for="(app, appIndex) in group.items"
                  :key="app.id"
                  class="timeline-item-wrapper"
                  :class="{
                    'timeline-item-latest': groupIndex === 0 && appIndex === 0,
                    'timeline-item-last-in-group': appIndex === group.items.length - 1 && groupIndex < groupedApplications.length - 1
                  }"
                >
                  <!-- Vertical Line Connector -->
                  <div class="timeline-axis-line">
                    <div class="axis-line"></div>
                  </div>

                  <!-- Timeline Card -->
                  <div class="timeline-item zen-card">
                    <div class="timeline-item-header">
                      <div class="timeline-company">
                        <h3>{{ app.firma }}</h3>
                        <p class="timeline-position">{{ app.position || 'Position nicht angegeben' }}</p>
                      </div>
                      <span :class="['status-badge', `status-${app.status}`]">
                        {{ getStatusLabel(app.status) }}
                      </span>
                    </div>

                    <!-- Status History Timeline -->
                    <div v-if="app.status_history && app.status_history.length > 0" class="status-history">
                      <div
                        v-for="(event, index) in app.status_history"
                        :key="index"
                        class="history-event"
                        :class="{ 'history-event-latest': index === app.status_history.length - 1 }"
                      >
                        <div class="history-marker">
                          <div class="history-dot"></div>
                          <div v-if="index < app.status_history.length - 1" class="history-line"></div>
                        </div>
                        <div class="history-content">
                          <span class="history-status">{{ getStatusLabel(event.status) }}</span>
                          <span class="history-time">{{ formatTimelineDateTime(event.timestamp) }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="timeline-item-meta">
                      <span v-if="app.quelle" class="meta-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                        </svg>
                        {{ getDomain(app.quelle) }}
                      </span>
                      <span class="meta-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                          <line x1="16" y1="2" x2="16" y2="6"/>
                          <line x1="8" y1="2" x2="8" y2="6"/>
                          <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                        {{ formatTimelineDate(app.datum) }}
                      </span>
                    </div>

                    <div class="timeline-actions">
                      <button @click="openDetails(app)" class="zen-btn zen-btn-sm">
                        Details
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Timeline empty -->
        <section v-else class="empty-state">
          <div class="empty-enso" aria-hidden="true"></div>
          <h3>Keine Bewerbungen im Zeitraum</h3>
          <p>Im ausgewaehlten Zeitraum wurden keine Bewerbungen gefunden.</p>
          <button @click="daysFilter = 'all'; loadTimeline()" class="zen-btn">
            Alle anzeigen
          </button>
        </section>

      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import { useI18n } from 'vue-i18n'
import { getFullLocale } from '../i18n'
import ApplicationFilters from '../components/Applications/ApplicationFilters.vue'
import ApplicationList from '../components/Applications/ApplicationList.vue'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

const applications = ref([])
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

const activeTab = ref('liste')
const timelineLoading = ref(false)
const timelineApps = ref([])
const daysFilter = ref('30')

const currentPage = ref(1)
const totalPages = ref(1)
const totalApplications = ref(0)
const perPage = ref(15)

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
  return applications.value.length === 0 ||
    (exportFilteredOnly.value && filteredApplications.value.length === 0)
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

// Timeline: group applications by date
const groupedApplications = computed(() => {
  if (!timelineApps.value.length) return []

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const lastWeekStart = new Date(today)
  lastWeekStart.setDate(lastWeekStart.getDate() - 7)

  const groupMap = new Map()

  timelineApps.value.forEach(app => {
    const appDate = new Date(app.datum)
    const appDateOnly = new Date(appDate.getFullYear(), appDate.getMonth(), appDate.getDate())

    let label
    if (appDateOnly.getTime() === today.getTime()) {
      label = 'Heute'
    } else if (appDateOnly.getTime() === yesterday.getTime()) {
      label = 'Gestern'
    } else if (appDateOnly >= lastWeekStart) {
      label = 'Diese Woche'
    } else {
      label = appDate.toLocaleDateString(getFullLocale(), { month: 'long', year: 'numeric' })
    }

    if (!groupMap.has(label)) {
      groupMap.set(label, { label, items: [], sortDate: appDate })
    }
    groupMap.get(label).items.push(app)
  })

  return Array.from(groupMap.values()).sort((a, b) => b.sortDate - a.sortDate)
})

const switchToTimeline = async () => {
  activeTab.value = 'timeline'
  router.replace({ path: '/applications', query: { ...route.query, view: 'timeline' } })
  if (timelineApps.value.length === 0) await loadTimeline()
}

const switchToListe = () => {
  activeTab.value = 'liste'
  const query = { ...route.query }
  delete query.view
  router.replace({ path: '/applications', query })
}

const loadTimeline = async () => {
  timelineLoading.value = true
  try {
    const { data } = await api.get('/applications/timeline', {
      params: { days: daysFilter.value }
    })
    timelineApps.value = data.data?.applications || []
  } catch (err) {
    console.error('Fehler beim Laden der Timeline:', err)
  } finally {
    timelineLoading.value = false
  }
}

const getStatusLabel = (status) => {
  const labels = {
    'erstellt': 'Erstellt',
    'versendet': 'Versendet',
    'antwort_erhalten': 'Antwort erhalten',
    'interview': 'Interview',
    'absage': 'Absage',
    'zusage': 'Zusage'
  }
  return labels[status] || status
}

const getDomain = (url) => {
  try {
    return new URL(url).hostname.replace('www.', '')
  } catch {
    return url
  }
}

const formatTimelineDate = (date) => {
  return new Date(date).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatTimelineDateTime = (date) => {
  return new Date(date).toLocaleString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

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
    const disposition = response.headers['content-disposition']
    const match = disposition?.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/)
    link.download = match ? decodeURIComponent(match[1]) : `Anschreiben_${id}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (_e) {
    if (window.$toast) { window.$toast(t('applications.pdfDownloadError'), 'error') }
  }
}

const openDetails = (app) => {
  router.push(`/applications/${app.id}`)
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

onMounted(() => {
  if (route.query.firma) {
    filterFirma.value = route.query.firma
  }
  if (route.query.view === 'timeline') {
    switchToTimeline()
  }
  loadApplications()
})

onUnmounted(() => {
  if (searchTimeout) clearTimeout(searchTimeout)
})

watch(() => route.query.firma, (newFirma) => {
  filterFirma.value = newFirma || ''
})

watch(() => route.query.view, (newView) => {
  if (newView === 'timeline' && activeTab.value !== 'timeline') {
    switchToTimeline()
  } else if (!newView && activeTab.value !== 'liste') {
    activeTab.value = 'liste'
  }
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

/* ========================================
   VIEW TABS
   ======================================== */
.view-tabs-section {
  margin-bottom: var(--space-md);
}

.view-tabs {
  display: inline-flex;
  background: var(--color-bg-elevated, var(--color-washi));
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 2px;
  gap: 2px;
}

.view-tab {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
}

.view-tab:hover {
  color: var(--color-text-primary);
}

.view-tab.active {
  background: var(--color-ai);
  color: var(--color-text-inverse, #fff);
}

/* ========================================
   TIMELINE FILTER
   ======================================== */
.timeline-filter {
  margin-bottom: var(--space-md);
}

.timeline-filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}

.timeline-filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.timeline-filter .filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.timeline-stats-summary {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
}

.timeline-stat-count {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-ai);
  line-height: 1;
}

.timeline-stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

/* ========================================
   TIMELINE LOADING
   ======================================== */
.loading-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.loading-enso {
  width: 60px;
  height: 60px;
  margin: 0 auto var(--space-lg);
  border: 2px solid var(--color-sand);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  color: var(--color-text-tertiary);
}

/* ========================================
   TIMELINE AXIS
   ======================================== */
.timeline-section {
  margin-top: var(--space-ma);
}

.timeline-axis {
  position: relative;
  padding-left: var(--space-xl);
}

.timeline-group {
  position: relative;
}

.timeline-group-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
  position: relative;
}

.timeline-axis-marker {
  position: absolute;
  left: calc(-1 * var(--space-xl));
  width: var(--space-xl);
  display: flex;
  align-items: center;
  justify-content: center;
}

.axis-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-ai);
  border: 3px solid var(--color-washi);
  box-shadow: 0 0 0 2px var(--color-ai);
  z-index: 2;
  position: relative;
}

.timeline-group-label {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-ai);
  background: var(--color-washi);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

.timeline-group-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.timeline-item-wrapper {
  position: relative;
  display: flex;
  gap: 0;
}

.timeline-axis-line {
  position: absolute;
  left: calc(-1 * var(--space-xl));
  top: 0;
  bottom: 0;
  width: var(--space-xl);
  display: flex;
  justify-content: center;
}

.axis-line {
  width: 2px;
  height: 100%;
  background: linear-gradient(
    to bottom,
    var(--color-sand) 0%,
    var(--color-stone) 50%,
    var(--color-sand) 100%
  );
}

.timeline-item-last-in-group .axis-line {
  height: calc(100% + var(--space-lg));
}

/* Latest item highlighting */
.timeline-item-latest .timeline-item {
  border-left: 3px solid var(--color-ai);
  box-shadow: var(--shadow-lifted), 0 0 0 1px var(--color-ai-subtle);
}

.timeline-item-latest .axis-line {
  background: linear-gradient(
    to bottom,
    var(--color-ai) 0%,
    var(--color-ai-light) 30%,
    var(--color-sand) 100%
  );
  width: 3px;
}

/* ========================================
   TIMELINE CARDS
   ======================================== */
.timeline-item {
  flex: 1;
  padding: var(--space-lg);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.timeline-item:hover {
  transform: translateX(4px);
}

.timeline-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.timeline-company h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
}

.timeline-position {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

/* ========================================
   STATUS BADGES (Timeline)
   ======================================== */
.status-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  white-space: nowrap;
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

.status-interview {
  background: rgba(61, 90, 108, 0.15);
  color: var(--color-ai);
}

.status-absage {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.status-zusage {
  background: var(--color-koke);
  color: var(--color-washi);
}

/* ========================================
   STATUS HISTORY (Timeline)
   ======================================== */
.status-history {
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-md);
}

.history-event {
  display: flex;
  gap: var(--space-md);
}

.history-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
}

.history-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-stone);
  flex-shrink: 0;
}

.history-event-latest .history-dot {
  background: var(--color-ai);
  box-shadow: 0 0 0 4px var(--color-ai-subtle);
}

.history-line {
  width: 2px;
  flex: 1;
  min-height: 24px;
  background: var(--color-sand);
}

.history-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-md);
}

.history-status {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.history-time {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

/* ========================================
   TIMELINE META
   ======================================== */
.timeline-item-meta {
  display: flex;
  gap: var(--space-lg);
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

/* ========================================
   TIMELINE ACTIONS
   ======================================== */
.timeline-actions {
  display: flex;
  gap: var(--space-sm);
}

/* ========================================
   RESPONSIVE
   ======================================== */
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

  .timeline-filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .timeline-filter-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .timeline-stats-summary {
    justify-content: flex-start;
  }

  .timeline-axis {
    padding-left: var(--space-lg);
  }

  .timeline-axis-marker {
    left: calc(-1 * var(--space-lg));
    width: var(--space-lg);
  }

  .timeline-axis-line {
    left: calc(-1 * var(--space-lg));
    width: var(--space-lg);
  }

  .axis-dot {
    width: 10px;
    height: 10px;
    border-width: 2px;
  }

  .history-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .timeline-item-header {
    flex-direction: column;
  }

  .timeline-axis {
    padding-left: var(--space-md);
  }

  .timeline-axis-marker {
    left: calc(-1 * var(--space-md));
    width: var(--space-md);
  }

  .timeline-axis-line {
    left: calc(-1 * var(--space-md));
    width: var(--space-md);
  }

  .axis-dot {
    width: 8px;
    height: 8px;
  }

  .timeline-group-label {
    font-size: 0.75rem;
    padding: var(--space-xs);
  }
}
</style>
