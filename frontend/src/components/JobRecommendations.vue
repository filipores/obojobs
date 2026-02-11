<template>
  <div class="job-recommendations">
    <div class="recommendations-header">
      <div class="header-content">
        <h2>Job-Empfehlungen</h2>
        <p class="subtitle">Basierend auf Ihrem Profil und Ihren Skills</p>
      </div>
      <div class="header-actions">
        <router-link to="/job-dashboard" class="zen-btn zen-btn-sm zen-btn-ghost">
          Alle Vorschläge
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
        <button @click="openAnalyzeModal" class="zen-btn zen-btn-ai">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
          Job analysieren
        </button>
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="stats" class="stats-row">
      <div class="stat-item">
        <span class="stat-value">{{ stats.active }}</span>
        <span class="stat-label">Aktiv</span>
      </div>
      <div class="stat-item stat-sehr-gut">
        <span class="stat-value">{{ stats.by_score?.sehr_gut || 0 }}</span>
        <span class="stat-label">Sehr gut (80%+)</span>
      </div>
      <div class="stat-item stat-gut">
        <span class="stat-value">{{ stats.by_score?.gut || 0 }}</span>
        <span class="stat-label">Gut (60-79%)</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.applied }}</span>
        <span class="stat-label">Beworben</span>
      </div>
    </div>

    <!-- Loading State - Skeleton -->
    <div v-if="loading" class="loading-skeleton" aria-label="Lade Empfehlungen">
      <div v-for="i in 3" :key="i" class="skeleton-card zen-card">
        <div class="skeleton-card-header">
          <div class="skeleton skeleton-badge"></div>
          <div class="skeleton-job-info">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text-short"></div>
          </div>
        </div>
        <div class="skeleton-card-body">
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-text-short"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="recommendations.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/>
          <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
      </div>
      <h3>Keine Empfehlungen vorhanden</h3>
      <p>
        Analysieren Sie Stellenanzeigen, um personalisierte Job-Empfehlungen
        basierend auf Ihrem Profil zu erhalten.
      </p>
      <button @click="openAnalyzeModal" class="zen-btn zen-btn-ai">
        Erste Stelle analysieren
      </button>
    </div>

    <!-- Recommendations List (Top 3) -->
    <div v-else class="recommendations-list">
      <div
        v-for="rec in recommendations.slice(0, 3)"
        :key="rec.id"
        class="recommendation-card zen-card"
        :class="[`score-${rec.fit_category}`]"
      >
        <div class="card-header">
          <div class="score-badge" :class="rec.fit_category">
            {{ rec.fit_score }}%
          </div>
          <div class="job-info">
            <h3 class="job-title">{{ rec.job_title || 'Unbekannte Position' }}</h3>
            <p class="company-name">{{ rec.company_name || 'Unbekanntes Unternehmen' }}</p>
            <p v-if="rec.location" class="location">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              {{ rec.location }}
            </p>
          </div>
          <div class="card-actions">
            <button
              v-if="rec.job_url"
              @click="openJobUrl(rec.job_url)"
              class="action-btn"
              title="Stellenanzeige öffnen"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </button>
            <button
              @click="dismissRecommendation(rec.id)"
              class="action-btn action-dismiss"
              title="Ausblenden"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="card-body">
          <div v-if="rec.source" class="source-tag">
            {{ getSourceLabel(rec.source) }}
          </div>
          <p class="recommended-at">
            Empfohlen am {{ formatDate(rec.recommended_at) }}
          </p>
        </div>

        <div class="card-footer">
          <router-link
            :to="`/new-application?url=${encodeURIComponent(rec.job_url)}`"
            class="zen-btn zen-btn-sm"
            @click="markAsApplied(rec.id)"
          >
            Bewerbung starten
          </router-link>
        </div>
      </div>

      <!-- View All Link -->
      <div v-if="recommendations.length > 3" class="view-all-link">
        <router-link to="/job-dashboard" class="zen-btn zen-btn-ghost">
          Alle {{ recommendations.length }} Vorschläge ansehen
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
      </div>
    </div>

    <!-- Analyze Modal -->
    <div v-if="showAnalyzeModal" class="modal-overlay" @click="closeOnOverlayClick">
      <div class="modal zen-card" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h3>Stellenanzeige analysieren</h3>
          <button @click="showAnalyzeModal = false" class="modal-close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- URL Input Mode -->
          <div v-if="!showManualInput">
            <p class="modal-description">
              Geben Sie die URL einer Stellenanzeige ein, um Ihren Job-Fit Score zu berechnen.
            </p>

            <div class="form-group">
              <label for="job-url">Stellenanzeige URL</label>
              <input
                id="job-url"
                v-model="analyzeUrl"
                type="url"
                placeholder="https://www.indeed.de/viewjob?..."
                class="form-input"
                :disabled="analyzing"
              />
            </div>

            <div v-if="analyzeError && !showManualInput" class="error-message error-with-action">
              <span>{{ analyzeError }}</span>
              <template v-if="isNoSkillsError">
                <p class="error-hint">
                  Fügen Sie Skills zu Ihrem Profil hinzu, um den Job-Fit Score zu berechnen.
                </p>
                <router-link to="/documents#skills" class="fallback-link" @click="closeAnalyzeModal">
                  Skills hinzufügen →
                </router-link>
              </template>
              <template v-else>
                <p class="error-hint">
                  Einige Portale blockieren automatisches Laden.
                </p>
                <button @click="switchToManualInput" class="fallback-link">
                  Stellentext manuell einfügen
                </button>
              </template>
            </div>
          </div>

          <!-- Manual Input Mode -->
          <div v-else class="manual-input-section">
            <div class="manual-input-header">
              <h4>Stellentext manuell einfügen</h4>
              <button @click="showManualInput = false" class="back-link">
                ← Zurück zur URL-Eingabe
              </button>
            </div>

            <div class="form-group">
              <label>Firmenname</label>
              <input
                v-model="manualCompany"
                type="text"
                class="form-input"
                placeholder="z.B. Beispiel GmbH"
                :disabled="analyzing"
              />
            </div>

            <div class="form-group">
              <label>Position (optional)</label>
              <input
                v-model="manualTitle"
                type="text"
                class="form-input"
                placeholder="z.B. Software Entwickler (m/w/d)"
                :disabled="analyzing"
              />
            </div>

            <div class="form-group">
              <label>Stellentext</label>
              <textarea
                v-model="manualJobText"
                class="form-input form-textarea"
                rows="8"
                placeholder="Fügen Sie hier den vollständigen Text der Stellenanzeige ein..."
                :disabled="analyzing"
              ></textarea>
              <p class="form-hint">Mindestens 100 Zeichen</p>
            </div>

            <div v-if="analyzeError" class="error-message" :class="{ 'error-with-action': isNoSkillsError }">
              <span>{{ analyzeError }}</span>
              <template v-if="isNoSkillsError">
                <p class="error-hint">
                  Fügen Sie Skills zu Ihrem Profil hinzu, um den Job-Fit Score zu berechnen.
                </p>
                <router-link to="/documents#skills" class="fallback-link" @click="closeAnalyzeModal">
                  Skills hinzufügen →
                </router-link>
              </template>
            </div>
          </div>

          <div v-if="analyzeResult" class="analyze-result">
            <div class="result-score" :class="analyzeResult.fit_category">
              <span class="score-value">{{ analyzeResult.fit_score }}%</span>
              <span class="score-label">{{ getScoreLabel(analyzeResult.fit_category) }}</span>
            </div>

            <div v-if="analyzeResult.job_data" class="result-details">
              <h4>{{ analyzeResult.job_data.title || 'Position' }}</h4>
              <p>{{ analyzeResult.job_data.company || 'Unternehmen' }}</p>
            </div>

            <div v-if="analyzeResult.matched_skills?.length" class="skills-section matched">
              <h5>Erfüllte Anforderungen ({{ analyzeResult.matched_skills.length }})</h5>
              <ul>
                <li v-for="skill in analyzeResult.matched_skills.slice(0, 5)" :key="skill.requirement">
                  {{ skill.requirement }}
                </li>
              </ul>
            </div>

            <div v-if="analyzeResult.missing_skills?.length" class="skills-section missing">
              <h5>Fehlende Anforderungen ({{ analyzeResult.missing_skills.length }})</h5>
              <ul>
                <li v-for="skill in analyzeResult.missing_skills.slice(0, 5)" :key="skill.requirement">
                  {{ skill.requirement }}
                </li>
              </ul>
            </div>

            <div v-if="analyzeResult.saved" class="save-status success">
              Job wurde als Empfehlung gespeichert
            </div>
            <div v-else-if="analyzeResult.message" class="save-status info">
              {{ analyzeResult.message }}
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAnalyzeModal" class="zen-btn zen-btn-ghost">
            Schließen
          </button>
          <button
            v-if="!showManualInput"
            @click="analyzeJob"
            class="zen-btn zen-btn-ai"
            :disabled="!analyzeUrl || analyzing"
          >
            <span v-if="analyzing">Analysiere...</span>
            <span v-else>Analysieren</span>
          </button>
          <button
            v-else
            @click="analyzeManualJob"
            class="zen-btn zen-btn-ai"
            :disabled="manualJobText.length < 100 || analyzing"
          >
            <span v-if="analyzing">Analysiere...</span>
            <span v-else>Stellentext analysieren</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api/client'
import { getFullLocale } from '../i18n'

const recommendations = ref([])
const stats = ref(null)
const loading = ref(true)
const showAnalyzeModal = ref(false)
const analyzeUrl = ref('')
const analyzing = ref(false)
const analyzeResult = ref(null)
const analyzeError = ref('')

// Manual input state
const showManualInput = ref(false)
const manualJobText = ref('')
const manualCompany = ref('')
const manualTitle = ref('')

// Check if error is "no skills" error
const isNoSkillsError = computed(() => {
  return analyzeError.value.toLowerCase().includes('keine skills')
})

const loadRecommendations = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/recommendations')
    recommendations.value = data.recommendations || []
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const { data } = await api.get('/recommendations/stats')
    stats.value = data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

// Shared error handler for analyze requests.
// Server errors (500+) are already shown by the API client toast,
// so we only surface client errors (400/422) in the component UI.
const handleAnalyzeError = (error) => {
  if (error.response?.status >= 500) {
    analyzeError.value = ''
  } else {
    analyzeError.value = error.response?.data?.error || 'Analyse fehlgeschlagen'
  }
}

const handleAnalyzeSuccess = async (data) => {
  analyzeResult.value = data
  if (data.saved) {
    await loadRecommendations()
    await loadStats()
  }
}

const analyzeJob = async () => {
  if (!analyzeUrl.value) return

  analyzing.value = true
  analyzeError.value = ''
  analyzeResult.value = null

  try {
    const { data } = await api.post('/recommendations/analyze', {
      job_url: analyzeUrl.value
    })
    await handleAnalyzeSuccess(data)
  } catch (error) {
    handleAnalyzeError(error)
  } finally {
    analyzing.value = false
  }
}

const analyzeManualJob = async () => {
  if (manualJobText.value.length < 100) return

  analyzing.value = true
  analyzeError.value = ''
  analyzeResult.value = null

  try {
    const { data } = await api.post('/recommendations/analyze-manual', {
      job_text: manualJobText.value,
      company: manualCompany.value,
      title: manualTitle.value
    })
    await handleAnalyzeSuccess(data)
  } catch (error) {
    handleAnalyzeError(error)
  } finally {
    analyzing.value = false
  }
}

const resetModalState = () => {
  analyzeUrl.value = ''
  analyzeResult.value = null
  analyzeError.value = ''
  showManualInput.value = false
  manualJobText.value = ''
  manualCompany.value = ''
  manualTitle.value = ''
}

const openAnalyzeModal = () => {
  resetModalState()
  showAnalyzeModal.value = true
}

const switchToManualInput = () => {
  showManualInput.value = true
  analyzeError.value = ''
}

const closeAnalyzeModal = () => {
  showAnalyzeModal.value = false
  resetModalState()
}

const closeOnOverlayClick = (event) => {
  // Only close if clicking on the overlay itself, not on the modal content
  if (event.target === event.currentTarget) {
    closeAnalyzeModal()
  }
}

// Escape key handler for modal
const handleEscapeKey = (event) => {
  if (event.key === 'Escape' && showAnalyzeModal.value) {
    closeAnalyzeModal()
  }
}

// Watch for modal state changes to add/remove escape key listener
watch(showAnalyzeModal, (isModalOpen) => {
  if (isModalOpen) {
    document.addEventListener('keydown', handleEscapeKey)
  } else {
    document.removeEventListener('keydown', handleEscapeKey)
  }
})

const dismissRecommendation = async (id) => {
  try {
    await api.post(`/recommendations/${id}/dismiss`)
    recommendations.value = recommendations.value.filter(r => r.id !== id)
    await loadStats()
  } catch (error) {
    console.error('Failed to dismiss:', error)
  }
}

const markAsApplied = async (id) => {
  try {
    await api.post(`/recommendations/${id}/apply`)
  } catch (error) {
    console.error('Failed to mark as applied:', error)
  }
}

const openJobUrl = (url) => {
  window.open(url, '_blank')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const SOURCE_LABELS = {
  indeed: 'Indeed',
  stepstone: 'StepStone',
  xing: 'XING',
  arbeitsagentur: 'Arbeitsagentur',
  generic: 'Web',
}

const SCORE_LABELS = {
  sehr_gut: 'Sehr gut',
  gut: 'Gut',
  mittel: 'Mittel',
  niedrig: 'Niedrig',
}

const getSourceLabel = (source) => SOURCE_LABELS[source] || source

const getScoreLabel = (category) => SCORE_LABELS[category] || category

onMounted(() => {
  loadRecommendations()
  loadStats()
})
</script>

<style scoped>
.job-recommendations {
  padding: var(--space-lg);
}

.recommendations-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-lg);
}

.header-content h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

/* Stats Row */
.stats-row {
  display: flex;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-sumi);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-sehr-gut .stat-value {
  color: var(--color-success);
}

.stat-gut .stat-value {
  color: var(--color-warning);
}

/* Loading Skeleton */
.loading-skeleton {
  display: grid;
  gap: var(--space-md);
}

.skeleton-card {
  padding: var(--space-lg);
}

.skeleton-card-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.skeleton-badge {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.skeleton-job-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-title {
  height: 1.25rem;
  width: 70%;
}

.skeleton-text {
  height: 1rem;
  width: 50%;
}

.skeleton-text-short {
  height: 0.875rem;
  width: 30%;
}

.skeleton-card-body {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.skeleton-tag {
  height: 1.5rem;
  width: 60px;
  border-radius: var(--radius-sm);
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

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--space-xl);
}

.empty-icon {
  margin-bottom: var(--space-md);
  color: var(--color-text-ghost);
}

.empty-state h3 {
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.empty-state p {
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0 auto var(--space-lg);
}

/* Recommendations List */
.recommendations-list {
  display: grid;
  gap: var(--space-md);
}

.recommendation-card {
  padding: var(--space-lg);
  transition: all var(--transition-base);
}

.recommendation-card:hover {
  box-shadow: var(--shadow-lifted);
}

.card-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.score-badge {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  color: white;
}

.score-badge.sehr_gut {
  background: var(--color-success);
}

.score-badge.gut {
  background: var(--color-warning);
}

.score-badge.mittel {
  background: var(--color-orange, #f57c00);
}

.score-badge.niedrig {
  background: var(--color-error);
}

.job-info {
  flex: 1;
  min-width: 0;
}

.job-title {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
}

.company-name {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.location {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.card-actions {
  display: flex;
  gap: var(--space-xs);
}

.action-btn {
  padding: var(--space-sm);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.action-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.action-dismiss:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

.card-body {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.source-tag {
  font-size: 0.75rem;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-sm);
}

.recommended-at {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  margin: 0;
}

.card-footer {
  margin-top: var(--space-md);
}

.view-all-link {
  display: flex;
  justify-content: center;
  margin-top: var(--space-lg);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-md);
}

.modal {
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.modal-header h3 {
  margin: 0;
}

.modal-close {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.modal-close:hover {
  color: var(--color-sumi);
  background: var(--color-bg-subtle);
}

.modal-body {
  padding: var(--space-lg);
}

.modal-description {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-xs);
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 1rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-ai);
}

.error-message {
  padding: var(--space-sm) var(--space-md);
  background: var(--color-error-subtle, #ffebee);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.analyze-result {
  margin-top: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-bg-subtle);
  border-radius: var(--radius-md);
}

.result-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  margin-bottom: var(--space-md);
  border-radius: var(--radius-md);
  color: white;
}

.result-score.sehr_gut {
  background: var(--color-success);
}

.result-score.gut {
  background: var(--color-warning);
}

.result-score.mittel {
  background: var(--color-orange, #f57c00);
}

.result-score.niedrig {
  background: var(--color-error);
}

.score-value {
  font-size: 2rem;
  font-weight: 600;
}

.score-label {
  font-size: 0.875rem;
  opacity: 0.9;
}

.result-details {
  margin-bottom: var(--space-md);
}

.result-details h4 {
  margin-bottom: var(--space-xs);
}

.result-details p {
  color: var(--color-text-secondary);
  margin: 0;
}

.skills-section {
  margin-top: var(--space-md);
}

.skills-section h5 {
  font-size: 0.875rem;
  margin-bottom: var(--space-sm);
}

.skills-section.matched h5 {
  color: var(--color-success);
}

.skills-section.missing h5 {
  color: var(--color-error);
}

.skills-section ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.skills-section li {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.save-status {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}

.save-status.success {
  background: var(--color-success-subtle, #e8f5e9);
  color: var(--color-success);
}

.save-status.info {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

/* Error with action */
.error-with-action {
  flex-direction: column;
  align-items: flex-start;
}

.error-hint {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: var(--space-xs) 0;
}

.fallback-link {
  background: transparent;
  border: none;
  color: var(--color-ai);
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  font-size: 0.875rem;
}

.fallback-link:hover {
  color: var(--color-ai-light);
}

/* Manual input section */
.manual-input-section {
  padding-top: var(--space-md);
}

.manual-input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.manual-input-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}

.back-link {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 0.875rem;
}

.back-link:hover {
  color: var(--color-ai);
}

.form-textarea {
  resize: vertical;
  min-height: 150px;
}

.form-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* Responsive */
@media (max-width: 768px) {
  .recommendations-header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .stats-row {
    flex-wrap: wrap;
    justify-content: center;
  }

  .card-header {
    flex-wrap: wrap;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
