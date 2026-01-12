<template>
  <div class="applications-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Bewerbungen</h1>
        <p class="page-subtitle">Verwalten und verfolgen Sie alle Ihre Bewerbungen</p>
      </section>

      <!-- Stats Section -->
      <section class="stats-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ applications.length }}</span>
            <span class="stat-label">Gesamt</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.erstellt }}</span>
            <span class="stat-label">Erstellt</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.versendet }}</span>
            <span class="stat-label">Versendet</span>
          </div>
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
              v-model="searchQuery"
              type="text"
              placeholder="Suche nach Firma oder Position..."
              class="form-input search-input"
            />
          </div>
          <div class="filter-group">
            <select v-model="filterStatus" class="form-select">
              <option value="">Alle Status</option>
              <option value="erstellt">Erstellt</option>
              <option value="versendet">Versendet</option>
              <option value="antwort_erhalten">Antwort erhalten</option>
              <option value="absage">Absage</option>
              <option value="zusage">Zusage</option>
            </select>
          </div>
        </div>

        <div v-if="searchQuery || filterStatus" class="active-filters">
          <span v-if="searchQuery" class="filter-tag">
            "{{ searchQuery }}"
            <button @click="searchQuery = ''" class="filter-tag-close">&times;</button>
          </span>
          <span v-if="filterStatus" class="filter-tag">
            {{ getStatusLabel(filterStatus) }}
            <button @click="filterStatus = ''" class="filter-tag-close">&times;</button>
          </span>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-enso"></div>
        <p>Lade Bewerbungen...</p>
      </div>

      <!-- Applications Grid -->
      <section v-else-if="filteredApplications.length > 0" class="applications-section">
        <div class="applications-grid">
          <div
            v-for="app in filteredApplications"
            :key="app.id"
            class="application-card zen-card stagger-item"
            @click="openDetails(app)"
          >
            <div class="card-header">
              <div class="card-title-group">
                <h3>{{ app.firma }}</h3>
                <p class="card-position">{{ app.position || 'Position nicht angegeben' }}</p>
              </div>
              <span :class="['status-badge', `status-${app.status}`]">
                {{ getStatusLabel(app.status) }}
              </span>
            </div>

            <div class="card-meta">
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ formatDate(app.datum) }}
              </span>
              <span v-if="app.quelle" class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                {{ getDomain(app.quelle) }}
              </span>
            </div>

            <div v-if="app.notizen" class="card-notes">
              {{ app.notizen.slice(0, 80) }}{{ app.notizen.length > 80 ? '...' : '' }}
            </div>

            <div class="card-actions" @click.stop>
              <button @click="downloadPDF(app.id)" class="zen-btn zen-btn-sm">
                PDF
              </button>
              <button @click="openDetails(app)" class="zen-btn zen-btn-ai zen-btn-sm">
                Details
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Empty State -->
      <section v-else class="empty-state">
        <div class="empty-enso"></div>
        <h3>{{ searchQuery || filterStatus ? 'Keine Ergebnisse' : 'Noch keine Bewerbungen' }}</h3>
        <p v-if="searchQuery || filterStatus">
          Keine Bewerbungen gefunden. Versuchen Sie andere Suchbegriffe.
        </p>
        <p v-else>
          Generieren Sie Ihre erste Bewerbung über die Chrome Extension.
        </p>
        <button v-if="searchQuery || filterStatus" @click="clearFilters" class="zen-btn">
          Filter zurücksetzen
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
                  <label class="detail-label">Datum</label>
                  <p class="detail-value">{{ formatDateTime(selectedApp.datum) }}</p>
                </div>
              </div>

              <!-- Betreff -->
              <div v-if="selectedApp.betreff" class="detail-group">
                <label class="detail-label">Betreff</label>
                <p class="detail-value detail-value-block">{{ selectedApp.betreff }}</p>
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
              <button @click="downloadPDF(selectedApp.id)" class="zen-btn zen-btn-ai">
                PDF herunterladen
              </button>
              <button @click="deleteApp(selectedApp.id)" class="zen-btn zen-btn-danger">
                Bewerbung löschen
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api/client'

const applications = ref([])
const selectedApp = ref(null)
const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')

const stats = computed(() => {
  return {
    erstellt: applications.value.filter(a => a.status === 'erstellt').length,
    versendet: applications.value.filter(a => a.status === 'versendet').length
  }
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

  return filtered.sort((a, b) => new Date(b.datum) - new Date(a.datum))
})

const loadApplications = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/applications')
    applications.value = data.applications || []
  } catch (err) {
    console.error('Fehler beim Laden:', err)
  } finally {
    loading.value = false
  }
}

const downloadPDF = async (id) => {
  try {
    window.open(`/api/applications/${id}/pdf`, '_blank')
  } catch (_e) {
    alert('Fehler beim PDF-Download')
  }
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
    alert('Fehler beim Aktualisieren')
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

const deleteApp = async (id) => {
  if (!confirm('Bewerbung wirklich löschen?')) return

  try {
    await api.delete(`/applications/${id}`)
    applications.value = applications.value.filter(a => a.id !== id)
    if (selectedApp.value && selectedApp.value.id === id) {
      selectedApp.value = null
    }
  } catch (_e) {
    alert('Fehler beim Löschen')
  }
}

const clearFilters = () => {
  searchQuery.value = ''
  filterStatus.value = ''
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
    'antwort_erhalten': 'Antwort',
    'absage': 'Absage',
    'zusage': 'Zusage'
  }
  return labels[status] || status
}

onMounted(loadApplications)
</script>

<style scoped>
.applications-page {
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
   STATS SECTION
   ======================================== */
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

/* ========================================
   FILTER SECTION
   ======================================== */
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
   APPLICATIONS GRID
   ======================================== */
.applications-section {
  margin-top: var(--space-ma);
}

.applications-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-lg);
}

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

.status-absage {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.status-zusage {
  background: var(--color-koke);
  color: var(--color-washi);
}

/* ========================================
   CARD META
   ======================================== */
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
   MODAL
   ======================================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(44, 44, 44, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
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

.detail-value-block {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
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

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
  }

  .filter-group {
    min-width: 100%;
  }

  .applications-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    flex-wrap: wrap;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .card-actions {
    flex-direction: column;
  }
}
</style>
