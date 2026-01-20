<template>
  <div class="ats-optimizer">
    <!-- Manual Text Input Section -->
    <div v-if="!atsData && !loading" class="manual-input-section">
      <div class="input-toggle">
        <button
          :class="['toggle-btn', { active: inputMode === 'auto' }]"
          @click="inputMode = 'auto'"
        >
          Automatisch
        </button>
        <button
          :class="['toggle-btn', { active: inputMode === 'manual' }]"
          @click="inputMode = 'manual'"
        >
          Eigener Text
        </button>
      </div>

      <div v-if="inputMode === 'manual'" class="manual-text-form">
        <label class="form-label">Bewerbungstext zum Pruefen</label>
        <textarea
          v-model="manualCoverLetter"
          class="form-input form-textarea"
          placeholder="Fuege hier deinen Bewerbungstext ein, um ihn auf ATS-Kompatibilitaet zu pruefen..."
          rows="8"
        ></textarea>
        <p class="form-hint">
          Der Text wird mit den Anforderungen der Stellenanzeige abgeglichen.
        </p>
        <button
          @click="analyzeManualText"
          :disabled="!manualCoverLetter.trim()"
          class="zen-btn zen-btn-ai analyze-btn"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          ATS-Check starten
        </button>
      </div>

      <div v-else class="auto-mode-info">
        <p class="info-text">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Der generierte Bewerbungstext wird automatisch analysiert.
        </p>
        <button
          @click="loadATSScore"
          class="zen-btn zen-btn-ai analyze-btn"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          Bewerbung analysieren
        </button>
      </div>
    </div>

    <!-- Loading State - Skeleton -->
    <div v-if="loading" class="ats-loading-skeleton" aria-label="Analysiere ATS-Kompatibilitaet">
      <div class="skeleton-header">
        <div class="skeleton skeleton-title" style="width: 150px;"></div>
        <div class="skeleton skeleton-badge"></div>
      </div>
      <div class="skeleton-progress">
        <div class="skeleton skeleton-bar"></div>
        <div class="skeleton skeleton-score"></div>
      </div>
      <div class="skeleton-keywords">
        <div class="skeleton skeleton-subtitle" style="width: 140px;"></div>
        <div class="skeleton-tags">
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-tag"></div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error && !atsData" class="ats-error">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span>{{ error }}</span>
      <button v-if="inputMode === 'auto'" @click="inputMode = 'manual'" class="zen-btn zen-btn-sm switch-mode-btn">
        Manuell eingeben
      </button>
    </div>

    <!-- ATS Score Display -->
    <div v-else-if="atsData" class="ats-content">
      <!-- Score Header -->
      <div class="score-header">
        <div class="score-header-left">
          <button @click="resetAnalysis" class="back-btn" title="Neue Analyse">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>
          <h3>ATS-Kompatibilitaet</h3>
        </div>
        <div :class="['score-badge', scoreCategory]">
          {{ scoreLabel }}
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="score-progress">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :class="scoreCategory"
            :style="{ width: `${atsData.ats_score}%` }"
          ></div>
        </div>
        <div class="score-value">{{ atsData.ats_score }}%</div>
      </div>

      <!-- Found Keywords -->
      <div v-if="atsData.found_keywords && atsData.found_keywords.length > 0" class="keywords-section found">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Gefundene Keywords ({{ atsData.found_keywords.length }})
        </h4>
        <div class="keywords-list">
          <span v-for="keyword in atsData.found_keywords" :key="keyword" class="keyword-tag found">
            {{ keyword }}
            <span v-if="atsData.keyword_density && atsData.keyword_density[keyword]" class="keyword-count">
              {{ atsData.keyword_density[keyword] }}x
            </span>
          </span>
        </div>
      </div>

      <!-- Missing Keywords -->
      <div v-if="atsData.missing_keywords && atsData.missing_keywords.length > 0" class="keywords-section missing">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          Fehlende Keywords ({{ atsData.missing_keywords.length }})
        </h4>
        <p class="keywords-hint">Klicke auf ein Keyword für Integrationstipps</p>
        <div class="keywords-list">
          <button
            v-for="keyword in atsData.missing_keywords"
            :key="keyword"
            class="keyword-tag missing clickable"
            @click="toggleKeywordTooltip(keyword)"
            :aria-expanded="activeKeywordTooltip === keyword"
            :aria-label="`Tipp für ${keyword} anzeigen`"
          >
            {{ keyword }}
            <svg class="keyword-info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <div v-if="activeKeywordTooltip === keyword" class="keyword-tooltip" role="tooltip">
              <div class="keyword-tooltip-header">
                <span class="keyword-tooltip-title">💡 Tipp: {{ keyword }}</span>
                <button class="keyword-tooltip-close" @click.stop="closeAllTooltips" aria-label="Schließen">×</button>
              </div>
              <p class="keyword-tooltip-text">{{ getKeywordTip(keyword) }}</p>
            </div>
          </button>
        </div>
      </div>

      <!-- Keyword Suggestions -->
      <div v-if="atsData.keyword_suggestions && atsData.keyword_suggestions.length > 0" class="suggestions-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Einbau-Vorschlaege
        </h4>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in atsData.keyword_suggestions" :key="index" class="suggestion-item">
            <span class="suggestion-keyword">{{ suggestion.keyword }}</span>
            <p class="suggestion-text">{{ suggestion.suggestion }}</p>
          </li>
        </ul>
      </div>

      <!-- Format Issues -->
      <div v-if="atsData.format_issues && atsData.format_issues.length > 0" class="issues-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Format-Probleme
        </h4>
        <ul class="issues-list">
          <li v-for="(issue, index) in atsData.format_issues" :key="index" class="issue-item">
            {{ issue }}
          </li>
        </ul>
      </div>

      <!-- Optimize Button -->
      <div v-if="atsData.missing_keywords && atsData.missing_keywords.length > 0" class="optimize-section">
        <button
          @click="optimizeCoverLetter"
          :disabled="optimizing"
          class="zen-btn zen-btn-ai optimize-btn"
        >
          <svg v-if="!optimizing" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span v-if="optimizing">Optimiere...</span>
          <span v-else>Mit KI verbessern</span>
        </button>
      </div>

      <!-- Already Optimized -->
      <div v-else-if="!atsData.missing_keywords || atsData.missing_keywords.length === 0" class="optimized-notice">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <span>Bewerbung ist gut fuer ATS optimiert!</span>
      </div>
    </div>

    <!-- Comparison View -->
    <div v-if="showComparison && comparisonData" class="comparison-section">
      <div class="comparison-header">
        <h3>Vorher / Nachher Vergleich</h3>
        <button @click="closeComparison" class="close-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- Changes Made -->
      <div v-if="comparisonData.changes_made && comparisonData.changes_made.length > 0" class="changes-list">
        <h4>Vorgenommene Aenderungen:</h4>
        <ul>
          <li v-for="(change, index) in comparisonData.changes_made" :key="index">
            {{ change }}
          </li>
        </ul>
      </div>

      <!-- Side by Side -->
      <div class="comparison-grid">
        <div class="comparison-panel original">
          <div class="panel-header">
            <span class="panel-label">Original</span>
          </div>
          <div class="panel-content">
            <pre>{{ comparisonData.original_text }}</pre>
          </div>
        </div>
        <div class="comparison-panel optimized">
          <div class="panel-header">
            <span class="panel-label">Optimiert</span>
            <span class="panel-badge">NEU</span>
          </div>
          <div class="panel-content">
            <pre>{{ comparisonData.optimized_text }}</pre>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="comparison-actions">
        <button @click="revertToOriginal" class="zen-btn">
          Zurueck zum Original
        </button>
        <button @click="acceptOptimization" class="zen-btn zen-btn-ai">
          Optimierung uebernehmen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api/client'

const props = defineProps({
  applicationId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['optimized', 'score-loaded'])

const loading = ref(false)
const loadingText = ref('Analysiere ATS-Kompatibilitaet...')
const error = ref('')
const atsData = ref(null)
const optimizing = ref(false)
const showComparison = ref(false)
const comparisonData = ref(null)

// Manual text input mode
const inputMode = ref('auto')
const manualCoverLetter = ref('')

// Keyword tooltip state
const activeKeywordTooltip = ref(null)

// Generate integration tip for a keyword
const getKeywordTip = (keyword) => {
  const tips = [
    `Füge "${keyword}" natürlich in deine Berufserfahrung ein, z.B.: "Anwendung von ${keyword} in..."`,
    `Erwähne konkrete Projekte, in denen du ${keyword} eingesetzt hast.`,
    `Liste ${keyword} in einem separaten "Technische Fähigkeiten" Abschnitt auf.`,
    `Beschreibe eine Situation, in der du ${keyword} unter Beweis gestellt hast.`,
    `Verwende "${keyword}" im Kontext deiner bisherigen Tätigkeiten.`
  ]
  // Return a consistent tip based on keyword hash
  const index = keyword.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % tips.length
  return tips[index]
}

const toggleKeywordTooltip = (keyword) => {
  if (activeKeywordTooltip.value === keyword) {
    activeKeywordTooltip.value = null
  } else {
    activeKeywordTooltip.value = keyword
  }
}

const closeAllTooltips = () => {
  activeKeywordTooltip.value = null
}

const scoreCategory = computed(() => {
  if (!atsData.value) return ''
  const score = atsData.value.ats_score
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-medium'
  if (score >= 40) return 'score-low'
  return 'score-very-low'
})

const scoreLabel = computed(() => {
  if (!atsData.value) return ''
  const score = atsData.value.ats_score
  if (score >= 80) return 'Sehr gut'
  if (score >= 60) return 'Gut'
  if (score >= 40) return 'Mittel'
  return 'Niedrig'
})

const loadATSScore = async (customText = null) => {
  if (!props.applicationId) return

  loading.value = true
  loadingText.value = 'Analysiere ATS-Kompatibilitaet...'
  error.value = ''

  try {
    const payload = customText ? { cover_letter_text: customText } : {}
    const { data } = await api.post(`/applications/${props.applicationId}/ats-check`, payload)

    if (data.success) {
      atsData.value = data.data
      emit('score-loaded', data.data)
    } else {
      error.value = data.error || 'Fehler bei der ATS-Analyse'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Fehler bei der ATS-Analyse'
  } finally {
    loading.value = false
  }
}

const analyzeManualText = async () => {
  if (!manualCoverLetter.value.trim()) return
  await loadATSScore(manualCoverLetter.value)
}

const resetAnalysis = () => {
  atsData.value = null
  error.value = ''
}

const optimizeCoverLetter = async () => {
  if (!props.applicationId || optimizing.value) return

  optimizing.value = true
  error.value = ''

  try {
    const { data } = await api.post(`/applications/${props.applicationId}/ats-optimize`, {
      missing_keywords: atsData.value?.missing_keywords || []
    })

    if (data.success) {
      comparisonData.value = data.data
      showComparison.value = true
      emit('optimized', data.data)
    } else {
      error.value = data.error || 'Fehler bei der Optimierung'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Fehler bei der Optimierung'
  } finally {
    optimizing.value = false
  }
}

const closeComparison = () => {
  showComparison.value = false
}

const revertToOriginal = async () => {
  if (!comparisonData.value?.original_text) return

  try {
    // Update the application with original text
    await api.post(`/applications/${props.applicationId}/ats-optimize`, {
      cover_letter_text: comparisonData.value.original_text,
      missing_keywords: [] // Empty to skip re-optimization
    })

    showComparison.value = false
    comparisonData.value = null
    // Reload ATS score
    await loadATSScore()
  } catch (e) {
    error.value = e.response?.data?.error || 'Fehler beim Zuruecksetzen'
  }
}

const acceptOptimization = async () => {
  showComparison.value = false
  comparisonData.value = null
  // Reload ATS score to show updated results
  await loadATSScore()
}

// Watch for applicationId changes and reset state
watch(() => props.applicationId, () => {
  resetAnalysis()
  manualCoverLetter.value = ''
  inputMode.value = 'auto'
})

// Don't auto-load - let user choose mode first
onMounted(() => {
  // Component is ready, user can choose auto or manual mode
})

defineExpose({
  refresh: loadATSScore
})
</script>

<style scoped>
.ats-optimizer {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-lg);
  margin-top: var(--space-lg);
}

/* Loading Skeleton */
.ats-loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-md) 0;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skeleton-title {
  height: 1.25rem;
}

.skeleton-badge {
  width: 60px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-progress {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.skeleton-bar {
  flex: 1;
  height: 12px;
  border-radius: var(--radius-full);
}

.skeleton-score {
  width: 50px;
  height: 2rem;
}

.skeleton-keywords {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton-subtitle {
  height: 1rem;
}

.skeleton-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.skeleton-tag {
  width: 70px;
  height: 1.5rem;
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

/* Error State */
.ats-error {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: 0.875rem;
}

/* Score Header */
.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.score-header h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0;
}

.score-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.score-badge.score-high {
  background: var(--color-success-light);
  color: var(--color-success);
}

.score-badge.score-medium {
  background: rgba(196, 163, 90, 0.15);
  color: #8a7a2a;
}

.score-badge.score-low {
  background: rgba(201, 162, 39, 0.15);
  color: #8a6d17;
}

.score-badge.score-very-low {
  background: var(--color-error-light);
  color: var(--color-error);
}

/* Progress Bar */
.score-progress {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.progress-bar {
  flex: 1;
  height: 12px;
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.5s var(--ease-zen);
}

.progress-fill.score-high {
  background: var(--color-success);
}

.progress-fill.score-medium {
  background: #c9a227;
}

.progress-fill.score-low {
  background: #d4a017;
}

.progress-fill.score-very-low {
  background: var(--color-error);
}

.score-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-sumi);
  min-width: 60px;
  text-align: right;
}

/* Keywords Sections */
.keywords-section {
  margin-bottom: var(--space-lg);
}

.keywords-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--space-md) 0;
}

.keywords-section.found h4 {
  color: var(--color-success);
}

.keywords-section.missing h4 {
  color: var(--color-error);
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-weight: 500;
}

.keyword-tag.found {
  background: var(--color-success-light);
  color: var(--color-success);
}

.keyword-tag.missing {
  background: var(--color-error-light);
  color: var(--color-error);
}

/* Clickable missing keyword badges */
.keyword-tag.clickable {
  position: relative;
  cursor: pointer;
  border: none;
  font-family: inherit;
  transition: all var(--transition-base);
}

.keyword-tag.clickable:hover {
  background: rgba(180, 80, 80, 0.25);
  transform: translateY(-1px);
}

.keyword-tag.clickable:focus {
  outline: 2px solid var(--color-error);
  outline-offset: 2px;
}

.keyword-info-icon {
  opacity: 0.7;
  flex-shrink: 0;
  transition: opacity var(--transition-base);
}

.keyword-tag.clickable:hover .keyword-info-icon {
  opacity: 1;
}

/* Keywords hint */
.keywords-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-sm) 0;
}

/* Keyword tooltip */
.keyword-tooltip {
  position: absolute;
  bottom: calc(100% + 12px);
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  background: var(--color-sumi);
  color: var(--color-washi);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 100;
  animation: tooltipFadeIn 0.2s ease-out;
  text-align: left;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.keyword-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 8px solid transparent;
  border-top-color: var(--color-sumi);
}

.keyword-tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.keyword-tooltip-title {
  font-size: 0.8125rem;
  font-weight: 600;
}

.keyword-tooltip-close {
  background: none;
  border: none;
  color: var(--color-washi);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  opacity: 0.7;
  transition: opacity var(--transition-base);
}

.keyword-tooltip-close:hover {
  opacity: 1;
}

.keyword-tooltip-text {
  padding: var(--space-md);
  margin: 0;
  font-size: 0.8125rem;
  line-height: var(--leading-relaxed);
  color: var(--color-washi);
}

.keyword-count {
  font-size: 0.6875rem;
  padding: 1px 4px;
  background: rgba(255,255,255,0.5);
  border-radius: var(--radius-sm);
}

/* Suggestions Section */
.suggestions-section {
  margin-bottom: var(--space-lg);
}

.suggestions-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--space-md) 0;
  color: var(--color-ai);
}

.suggestions-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.suggestion-item {
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-ai);
}

.suggestion-keyword {
  display: inline-block;
  padding: 2px 8px;
  background: var(--color-ai);
  color: white;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: var(--space-xs);
}

.suggestion-text {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
}

/* Format Issues */
.issues-section {
  margin-bottom: var(--space-lg);
}

.issues-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--space-md) 0;
  color: var(--color-warning);
}

.issues-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.issue-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--color-warning-light);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  color: var(--color-sumi);
}

/* Optimize Section */
.optimize-section {
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.optimize-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

/* Optimized Notice */
.optimized-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-success-light);
  border-radius: var(--radius-md);
  color: var(--color-success);
  font-weight: 500;
}

/* Comparison Section */
.comparison-section {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 2px solid var(--color-ai);
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.comparison-header h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
  color: var(--color-ai);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  padding: var(--space-xs);
  transition: color var(--transition-base);
}

.close-btn:hover {
  color: var(--color-sumi);
}

/* Changes List */
.changes-list {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
}

.changes-list h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-ai);
}

.changes-list ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.changes-list li {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

/* Comparison Grid */
.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.comparison-panel {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-washi);
  border-bottom: 1px solid var(--color-border-light);
}

.panel-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-tertiary);
}

.comparison-panel.original .panel-label {
  color: var(--color-stone);
}

.comparison-panel.optimized .panel-label {
  color: var(--color-ai);
}

.panel-badge {
  font-size: 0.625rem;
  padding: 2px 6px;
  background: var(--color-ai);
  color: white;
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.panel-content {
  padding: var(--space-md);
  max-height: 400px;
  overflow-y: auto;
}

.panel-content pre {
  margin: 0;
  font-family: inherit;
  font-size: 0.8125rem;
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--color-sumi);
}

/* Comparison Actions */
.comparison-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: flex-end;
}

/* Responsive */
@media (max-width: 768px) {
  .comparison-grid {
    grid-template-columns: 1fr;
  }

  .comparison-actions {
    flex-direction: column;
  }

  .comparison-actions .zen-btn {
    width: 100%;
  }

  .score-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .manual-input-section {
    padding: var(--space-md);
  }
}

/* Manual Input Section */
.manual-input-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.input-toggle {
  display: flex;
  gap: var(--space-xs);
  background: var(--color-washi-aged);
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  width: fit-content;
}

.toggle-btn {
  padding: var(--space-sm) var(--space-md);
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-xs);
  transition: all var(--transition-base);
}

.toggle-btn:hover {
  color: var(--color-text-primary);
}

.toggle-btn.active {
  background: var(--color-washi);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

.manual-text-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.form-textarea {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-family: inherit;
  line-height: var(--leading-relaxed);
  resize: vertical;
  min-height: 160px;
  background: var(--color-washi);
  transition: border-color var(--transition-base);
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-ai);
}

.form-textarea::placeholder {
  color: var(--color-text-tertiary);
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

.analyze-btn {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.auto-mode-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.info-text {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.info-text svg {
  flex-shrink: 0;
  color: var(--color-ai);
}

/* Score Header Left */
.score-header-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  background: var(--color-washi);
  color: var(--color-stone);
  cursor: pointer;
  transition: all var(--transition-base);
}

.back-btn:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
  border-color: var(--color-border);
}

/* Switch Mode Button in Error */
.switch-mode-btn {
  margin-left: auto;
  flex-shrink: 0;
}

.ats-error {
  flex-wrap: wrap;
}
</style>
