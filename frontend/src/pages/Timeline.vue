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
      <section v-else-if="applications.length > 0" class="timeline-section">
        <div class="timeline-container">
          <div
            v-for="app in applications"
            :key="app.id"
            class="timeline-item zen-card stagger-item"
          >
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
              <router-link :to="`/applications`" class="zen-btn zen-btn-sm">
                Details
              </router-link>
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const applications = ref([])
const loading = ref(false)
const daysFilter = ref('30')

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
  return new Date(date).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatDateTime = (date) => {
  return new Date(date).toLocaleString('de-DE', {
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
   TIMELINE CONTAINER
   ======================================== */
.timeline-section {
  margin-top: var(--space-ma);
}

.timeline-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.timeline-item {
  padding: var(--space-lg);
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
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .timeline-item-header {
    flex-direction: column;
  }
}
</style>
