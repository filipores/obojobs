<template>
  <div class="timeline-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Timeline</h1>
        <p class="page-subtitle">Chronologischer Verlauf Ihrer Bewerbungen</p>
      </section>

      <!-- Filter Section -->
      <section class="filter-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="filter-row">
          <div class="filter-group">
            <label class="filter-label">Zeitraum</label>
            <select v-model="daysFilter" @change="loadTimeline" class="form-select">
              <option value="7">Letzte 7 Tage</option>
              <option value="30">Letzte 30 Tage</option>
              <option value="90">Letzte 90 Tage</option>
              <option value="all">Alle</option>
            </select>
          </div>
          <div class="stats-summary">
            <span class="stat-item">
              <span class="stat-value">{{ applications.length }}</span>
              <span class="stat-label">Bewerbungen</span>
            </span>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-enso"></div>
        <p>Lade Timeline...</p>
      </div>

      <!-- Timeline View -->
      <section v-else-if="groupedApplications.length > 0" class="timeline-section">
        <!-- Timeline Axis -->
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
                <div class="timeline-item zen-card stagger-item">
            <!-- Timeline Item Header -->
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
            <div class="status-history">
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
                  <span class="history-time">{{ formatDateTime(event.timestamp) }}</span>
                </div>
              </div>
            </div>

            <!-- Timeline Item Meta -->
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
                {{ formatDate(app.datum) }}
              </span>
            </div>

            <!-- Actions -->
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

      <!-- Empty State -->
      <section v-else class="empty-state">
        <div class="empty-enso"></div>
        <h3>Keine Bewerbungen im Zeitraum</h3>
        <p>Im ausgewaehlten Zeitraum wurden keine Bewerbungen gefunden.</p>
        <button @click="daysFilter = 'all'; loadTimeline()" class="zen-btn">
          Alle anzeigen
        </button>
      </section>

      <!-- Detail Modal -->
      <Teleport to="body">
        <div v-if="selectedApp" class="modal-overlay" @click="closeDetails">
          <div class="modal zen-card animate-fade-up" @click.stop>
            <div class="modal-header">
              <div>
                <h2>{{ selectedApp.firma }}</h2>
                <p class="modal-subtitle">{{ selectedApp.position }}</p>
              </div>
              <button @click="closeDetails" class="modal-close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div class="modal-content">
              <!-- Status -->
              <div class="detail-group detail-group-highlight">
                <label class="detail-label">Status</label>
                <select v-model="selectedApp.status" @change="updateStatus(selectedApp)" class="form-select">
                  <option value="erstellt">Erstellt</option>
                  <option value="versendet">Versendet</option>
                  <option value="antwort_erhalten">Antwort erhalten</option>
                  <option value="interview">Interview</option>
                  <option value="absage">Absage</option>
                  <option value="zusage">Zusage</option>
                </select>
              </div>

              <!-- Info Grid -->
              <div class="info-grid">
                <div class="detail-group">
                  <label class="detail-label">Firma</label>
                  <p class="detail-value">{{ selectedApp.firma }}</p>
                </div>

                <div v-if="selectedApp.position" class="detail-group">
                  <label class="detail-label">Position</label>
                  <p class="detail-value">{{ selectedApp.position }}</p>
                </div>

                <div v-if="selectedApp.ansprechpartner" class="detail-group">
                  <label class="detail-label">Ansprechpartner</label>
                  <p class="detail-value">{{ selectedApp.ansprechpartner }}</p>
                </div>

                <div v-if="selectedApp.email" class="detail-group">
                  <label class="detail-label">Email</label>
                  <p class="detail-value">
                    <a :href="`mailto:${selectedApp.email}`" class="detail-link">{{ selectedApp.email }}</a>
                  </p>
                </div>

                <div v-if="selectedApp.quelle" class="detail-group">
                  <label class="detail-label">Quelle</label>
                  <p class="detail-value">
                    <a :href="selectedApp.quelle" target="_blank" class="detail-link">{{ getDomain(selectedApp.quelle) }}</a>
                  </p>
                </div>

                <div class="detail-group">
                  <label class="detail-label">Erstellt</label>
                  <p class="detail-value">{{ formatDateTime(selectedApp.datum) }}</p>
                </div>
              </div>

              <!-- Status History Timeline -->
              <div v-if="selectedApp.status_history && selectedApp.status_history.length > 0" class="detail-group">
                <label class="detail-label">Verlauf</label>
                <div class="status-history">
                  <div
                    v-for="(event, index) in selectedApp.status_history"
                    :key="index"
                    class="history-event"
                    :class="{ 'history-event-latest': index === selectedApp.status_history.length - 1 }"
                  >
                    <div class="history-marker">
                      <div class="history-dot"></div>
                      <div v-if="index < selectedApp.status_history.length - 1" class="history-line"></div>
                    </div>
                    <div class="history-content">
                      <span class="history-status">{{ getStatusLabel(event.status) }}</span>
                      <span class="history-time">{{ formatDateTime(event.timestamp) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Notes -->
              <div class="detail-group">
                <label class="detail-label">Notizen</label>
                <textarea
                  v-model="selectedApp.notizen"
                  @blur="updateNotes(selectedApp)"
                  placeholder="Notizen hinzufügen..."
                  rows="4"
                  class="form-textarea"
                ></textarea>
              </div>
            </div>

            <div class="modal-footer">
              <router-link
                :to="`/applications/${selectedApp.id}/interview`"
                class="zen-btn zen-btn-interview"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                Interview-Prep
              </router-link>
              <button @click="downloadPDF(selectedApp.id)" class="zen-btn">
                PDF herunterladen
              </button>
              <button @click="closeDetails" class="zen-btn">
                Schließen
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'
import { getFullLocale } from '../i18n'

const applications = ref([])
const loading = ref(false)
const daysFilter = ref('30')
const selectedApp = ref(null)

// Group applications by date/week
const groupedApplications = computed(() => {
  if (!applications.value.length) return []

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const lastWeekStart = new Date(today)
  lastWeekStart.setDate(lastWeekStart.getDate() - 7)

  const groupMap = new Map()

  applications.value.forEach(app => {
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
      // Group by month
      label = appDate.toLocaleDateString(getFullLocale(), { month: 'long', year: 'numeric' })
    }

    if (!groupMap.has(label)) {
      groupMap.set(label, { label, items: [], sortDate: appDate })
    }
    groupMap.get(label).items.push(app)
  })

  // Sort groups by date (newest first)
  const sortedGroups = Array.from(groupMap.values())
    .sort((a, b) => b.sortDate - a.sortDate)

  return sortedGroups
})

const loadTimeline = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/applications/timeline', {
      params: { days: daysFilter.value }
    })
    applications.value = data.data?.applications || []
  } catch (err) {
    console.error('Fehler beim Laden der Timeline:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatDateTime = (date) => {
  return new Date(date).toLocaleString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
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

const openDetails = (app) => {
  selectedApp.value = { ...app }
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
  } catch (_e) {
    alert('Fehler beim Aktualisieren des Status')
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
    alert('Fehler beim Speichern der Notizen')
  }
}

const downloadPDF = async (id) => {
  try {
    // Use authenticated request to fetch PDF blob
    const response = await api.get(`/applications/${id}/pdf`, {
      responseType: 'blob'
    })

    // Create download link from blob
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
    alert('Fehler beim PDF-Download')
  }
}

onMounted(() => {
  loadTimeline()
})
</script>

<style scoped>
.timeline-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

/* ========================================
   PAGE HEADER
   ======================================== */
.page-header {
  padding: var(--space-ma-lg) 0 var(--space-ma);
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

/* ========================================
   FILTER SECTION
   ======================================== */
.filter-section {
  margin-bottom: var(--space-ma);
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.stats-summary {
  display: flex;
  gap: var(--space-lg);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 1.5rem;
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
}

/* ========================================
   LOADING STATE
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
   TIMELINE AXIS - Global Timeline Line
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

/* Extend line below last item to connect to next group */
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

/* ========================================
   TIMELINE ITEM CONTENT
   ======================================== */
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
   STATUS BADGES
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
   STATUS HISTORY
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
   EMPTY STATE
   ======================================== */
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
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-summary {
    justify-content: flex-start;
  }

  .stat-item {
    align-items: flex-start;
  }

  .history-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }

  /* Timeline axis responsive */
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

/* ========================================
   MODAL
   ======================================== */
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(44, 44, 44, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.modal {
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-xl);
  border-bottom: 1px solid var(--color-border-light);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0 0 var(--space-xs) 0;
}

.modal-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  padding: var(--space-xs);
  transition: color var(--transition-base);
}

.modal-close:hover {
  color: var(--color-sumi);
}

.modal-content {
  padding: var(--space-xl);
}

.detail-group {
  margin-bottom: var(--space-lg);
}

.detail-group-highlight {
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-ai);
}

.detail-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.detail-value {
  margin: 0;
  color: var(--color-sumi);
  font-size: 1rem;
}

.detail-link {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.detail-link:hover {
  text-decoration: underline;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.modal-footer {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-washi);
}

/* Interview Prep Button */
.zen-btn-interview {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: rgba(138, 79, 125, 0.1);
  border-color: rgba(138, 79, 125, 0.3);
  color: #8a4f7d;
  text-decoration: none;
}

.zen-btn-interview:hover {
  background: rgba(138, 79, 125, 0.2);
  border-color: #8a4f7d;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }
}
</style>
