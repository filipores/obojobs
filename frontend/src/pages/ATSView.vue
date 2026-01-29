<template>
  <div class="ats-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>ATS-Analyse</h1>
        <p class="page-subtitle">Prüfe wie gut dein Lebenslauf zur Stellenanzeige passt</p>
      </section>

      <!-- Resume Missing Warning -->
      <section v-if="!checkingResume && !hasResume" class="resume-warning-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="resume-warning zen-card">
          <div class="warning-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="12" y1="9" x2="12.01" y2="9"/>
            </svg>
          </div>
          <div class="warning-content">
            <h3>Lebenslauf erforderlich</h3>
            <p>
              Um die ATS-Analyse durchzuführen, benötigen wir deinen Lebenslauf.
              Die Analyse vergleicht dein Profil mit den Anforderungen der Stellenanzeige.
            </p>
            <button @click="goToDocuments" class="zen-btn zen-btn-ai">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Lebenslauf hochladen
            </button>
          </div>
        </div>
      </section>

      <!-- Form Section -->
      <section v-if="!checkingResume && hasResume" class="form-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="form-card zen-card">
          <!-- Input Mode Toggle -->
          <div class="input-toggle">
            <button
              :class="['toggle-btn', { active: inputMode === 'url' }]"
              @click="inputMode = 'url'"
              :disabled="analyzing"
            >
              URL
            </button>
            <button
              :class="['toggle-btn', { active: inputMode === 'text' }]"
              @click="inputMode = 'text'"
              :disabled="analyzing"
            >
              Text
            </button>
          </div>

          <!-- URL Input -->
          <div v-if="inputMode === 'url'" class="form-group">
            <label class="form-label">Stellenanzeigen-URL</label>
            <div class="url-input-wrapper">
              <svg class="url-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              <input
                v-model="jobUrl"
                type="url"
                placeholder="https://example.com/jobs/stellenanzeige"
                class="form-input url-input"
                :disabled="analyzing"
              />
            </div>
            <p class="form-hint">Kopiere die URL der Stellenanzeige und füge sie hier ein</p>
          </div>

          <!-- Text Input -->
          <div v-else class="form-group">
            <label class="form-label">Stellenbeschreibung</label>
            <textarea
              v-model="jobText"
              placeholder="Füge hier die Stellenbeschreibung ein..."
              class="form-input form-textarea"
              :disabled="analyzing"
              rows="8"
            ></textarea>
            <p class="form-hint">Kopiere den Text der Stellenanzeige hierher</p>
          </div>

          <!-- ATS Explanation Box -->
          <div class="info-box ats-explanation">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <div class="info-content">
              <strong>
                Was ist ein ATS-Score?
                <span class="ats-tooltip-trigger" tabindex="0" role="button" aria-describedby="ats-tooltip">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  <span id="ats-tooltip" class="ats-tooltip" role="tooltip">
                    <strong>ATS = Applicant Tracking System</strong><br/>
                    Ein Software-System, das Unternehmen nutzen, um Bewerbungen automatisch zu filtern.
                    Der Score zeigt, wie gut dein Lebenslauf zu den Anforderungen passt.
                  </span>
                </span>
              </strong>
              <ul>
                <li>Die Stellenanzeige wird mit deinem Lebenslauf verglichen</li>
                <li>Du erhältst einen Score von 0-100</li>
                <li>Fehlende Keywords werden identifiziert</li>
                <li>Verbesserungsvorschläge helfen dir weiter</li>
              </ul>
            </div>
          </div>

          <!-- Score Legend -->
          <div class="score-legend">
            <h4 class="legend-title">Score-Bewertung</h4>
            <div class="legend-items">
              <div class="legend-item">
                <span class="legend-color score-high"></span>
                <span class="legend-range">75-100</span>
                <span class="legend-label">Sehr gut</span>
              </div>
              <div class="legend-item">
                <span class="legend-color score-medium"></span>
                <span class="legend-range">50-74</span>
                <span class="legend-label">Gut</span>
              </div>
              <div class="legend-item">
                <span class="legend-color score-low"></span>
                <span class="legend-range">0-49</span>
                <span class="legend-label">Optimierbar</span>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="form-actions">
            <button
              @click="analyzeCV"
              :disabled="!canAnalyze || analyzing"
              class="zen-btn zen-btn-ai zen-btn-lg"
            >
              <span v-if="analyzing" class="btn-loading">
                <span class="loading-spinner"></span>
                Analysiere...
              </span>
              <span v-else>
                Analysieren
              </span>
            </button>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="error-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>{{ error }}</span>
          </div>
        </div>
      </section>

      <!-- History Section -->
      <section v-if="hasResume && history.length > 0" class="history-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="history-card zen-card">
          <h3 class="history-title">Letzte Analysen</h3>
          <ul class="history-list">
            <li
              v-for="item in history"
              :key="item.id"
              class="history-item"
            >
              <div class="history-content" @click="loadHistoryItem(item)">
                <div class="history-info">
                  <span class="history-url" :title="item.title || item.job_url || 'Manuelle Eingabe'">
                    {{ formatHistoryTitle(item) }}
                  </span>
                  <span class="history-date">{{ formatDate(item.created_at) }}</span>
                </div>
                <div class="history-stats">
                  <span :class="['history-score', getScoreClass(item.score)]">{{ item.score }}</span>
                  <span class="history-keywords">
                    <span class="matched">{{ item.matched_count }}</span>
                    /
                    <span class="missing">{{ item.missing_count }}</span>
                  </span>
                </div>
              </div>
              <button
                class="history-delete-btn"
                @click.stop="confirmDeleteAnalysis(item)"
                title="Analyse löschen"
                aria-label="Analyse löschen"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </li>
          </ul>
        </div>
      </section>

      <!-- Results Section -->
      <section v-if="hasResume && result" class="results-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="results-card zen-card">
          <h2 class="results-title">Analyse-Ergebnis</h2>

          <!-- Score Display -->
          <div class="score-display">
            <div class="score-ring-container" :class="scoreClass">
              <svg class="score-ring" viewBox="0 0 120 120">
                <!-- Background circle -->
                <circle
                  class="ring-background"
                  cx="60"
                  cy="60"
                  r="52"
                  fill="none"
                  stroke-width="8"
                />
                <!-- Progress circle -->
                <circle
                  class="ring-progress"
                  cx="60"
                  cy="60"
                  r="52"
                  fill="none"
                  stroke-width="8"
                  stroke-linecap="round"
                  :stroke-dasharray="circumference"
                  :stroke-dashoffset="progressOffset"
                />
              </svg>
              <div class="score-ring-content">
                <span class="score-value">{{ result.score }}</span>
                <span class="score-label">Score</span>
              </div>
            </div>
            <p class="score-description">{{ scoreDescription }}</p>
          </div>

          <!-- Categories -->
          <div v-if="result.categories" class="categories-section">
            <h3 class="section-title">Keywords nach Kategorie</h3>
            <p class="categories-hint">💡 Klicke auf fehlende Keywords für Integrationstipps</p>

            <div class="categories-grid">
              <!-- Hard Skills -->
              <div v-if="hasCategory('hard_skills')" class="category-card">
                <h4 class="category-title">
                  <span class="category-icon">&#128187;</span>
                  Hard Skills
                </h4>
                <div class="keyword-lists">
                  <div v-if="result.categories.hard_skills.matched?.length" class="keyword-list matched">
                    <span class="list-label">Gefunden:</span>
                    <span v-for="kw in result.categories.hard_skills.matched" :key="kw" class="keyword-tag matched">
                      {{ kw }}
                    </span>
                  </div>
                  <div v-if="result.categories.hard_skills.missing?.length" class="keyword-list missing">
                    <span class="list-label">Fehlt:</span>
                    <button
                      v-for="kw in result.categories.hard_skills.missing"
                      :key="kw"
                      class="keyword-tag missing clickable"
                      @click="toggleKeywordTooltip(kw, 'hard_skills')"
                      :aria-expanded="activeKeywordTooltip === kw"
                      :aria-label="`Tipp für ${kw} anzeigen`"
                    >
                      {{ kw }}
                      <svg class="keyword-info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      <div v-if="activeKeywordTooltip === kw" class="keyword-tooltip" role="tooltip">
                        <div class="keyword-tooltip-header">
                          <span class="keyword-tooltip-title">💡 Tipp: {{ kw }}</span>
                          <button class="keyword-tooltip-close" @click.stop="closeAllTooltips" aria-label="Schließen">×</button>
                        </div>
                        <p class="keyword-tooltip-text">{{ getKeywordTip(kw, 'hard_skills') }}</p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Soft Skills -->
              <div v-if="hasCategory('soft_skills')" class="category-card">
                <h4 class="category-title">
                  <span class="category-icon">&#129309;</span>
                  Soft Skills
                </h4>
                <div class="keyword-lists">
                  <div v-if="result.categories.soft_skills.matched?.length" class="keyword-list matched">
                    <span class="list-label">Gefunden:</span>
                    <span v-for="kw in result.categories.soft_skills.matched" :key="kw" class="keyword-tag matched">
                      {{ kw }}
                    </span>
                  </div>
                  <div v-if="result.categories.soft_skills.missing?.length" class="keyword-list missing">
                    <span class="list-label">Fehlt:</span>
                    <button
                      v-for="kw in result.categories.soft_skills.missing"
                      :key="kw"
                      class="keyword-tag missing clickable"
                      @click="toggleKeywordTooltip(kw, 'soft_skills')"
                      :aria-expanded="activeKeywordTooltip === kw"
                      :aria-label="`Tipp für ${kw} anzeigen`"
                    >
                      {{ kw }}
                      <svg class="keyword-info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      <div v-if="activeKeywordTooltip === kw" class="keyword-tooltip" role="tooltip">
                        <div class="keyword-tooltip-header">
                          <span class="keyword-tooltip-title">💡 Tipp: {{ kw }}</span>
                          <button class="keyword-tooltip-close" @click.stop="closeAllTooltips" aria-label="Schließen">×</button>
                        </div>
                        <p class="keyword-tooltip-text">{{ getKeywordTip(kw, 'soft_skills') }}</p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Qualifications -->
              <div v-if="hasCategory('qualifications')" class="category-card">
                <h4 class="category-title">
                  <span class="category-icon">&#127891;</span>
                  Qualifikationen
                </h4>
                <div class="keyword-lists">
                  <div v-if="result.categories.qualifications.matched?.length" class="keyword-list matched">
                    <span class="list-label">Gefunden:</span>
                    <span v-for="kw in result.categories.qualifications.matched" :key="kw" class="keyword-tag matched">
                      {{ kw }}
                    </span>
                  </div>
                  <div v-if="result.categories.qualifications.missing?.length" class="keyword-list missing">
                    <span class="list-label">Fehlt:</span>
                    <button
                      v-for="kw in result.categories.qualifications.missing"
                      :key="kw"
                      class="keyword-tag missing clickable"
                      @click="toggleKeywordTooltip(kw, 'qualifications')"
                      :aria-expanded="activeKeywordTooltip === kw"
                      :aria-label="`Tipp für ${kw} anzeigen`"
                    >
                      {{ kw }}
                      <svg class="keyword-info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      <div v-if="activeKeywordTooltip === kw" class="keyword-tooltip" role="tooltip">
                        <div class="keyword-tooltip-header">
                          <span class="keyword-tooltip-title">💡 Tipp: {{ kw }}</span>
                          <button class="keyword-tooltip-close" @click.stop="closeAllTooltips" aria-label="Schließen">×</button>
                        </div>
                        <p class="keyword-tooltip-text">{{ getKeywordTip(kw, 'qualifications') }}</p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Experience -->
              <div v-if="hasCategory('experience')" class="category-card">
                <h4 class="category-title">
                  <span class="category-icon">&#128188;</span>
                  Erfahrung
                </h4>
                <div class="keyword-lists">
                  <div v-if="result.categories.experience.matched?.length" class="keyword-list matched">
                    <span class="list-label">Gefunden:</span>
                    <span v-for="kw in result.categories.experience.matched" :key="kw" class="keyword-tag matched">
                      {{ kw }}
                    </span>
                  </div>
                  <div v-if="result.categories.experience.missing?.length" class="keyword-list missing">
                    <span class="list-label">Fehlt:</span>
                    <button
                      v-for="kw in result.categories.experience.missing"
                      :key="kw"
                      class="keyword-tag missing clickable"
                      @click="toggleKeywordTooltip(kw, 'experience')"
                      :aria-expanded="activeKeywordTooltip === kw"
                      :aria-label="`Tipp für ${kw} anzeigen`"
                    >
                      {{ kw }}
                      <svg class="keyword-info-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      <div v-if="activeKeywordTooltip === kw" class="keyword-tooltip" role="tooltip">
                        <div class="keyword-tooltip-header">
                          <span class="keyword-tooltip-title">💡 Tipp: {{ kw }}</span>
                          <button class="keyword-tooltip-close" @click.stop="closeAllTooltips" aria-label="Schließen">×</button>
                        </div>
                        <p class="keyword-tooltip-text">{{ getKeywordTip(kw, 'experience') }}</p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Suggestions -->
          <div v-if="result.suggestions?.length" class="suggestions-section">
            <h3 class="section-title">Verbesserungsvorschläge</h3>
            <ul class="suggestions-list">
              <li
                v-for="(suggestion, index) in result.suggestions"
                :key="index"
                :class="['suggestion-item', getSuggestionPriority(suggestion)]"
              >
                <span class="suggestion-priority">{{ getPriorityLabel(suggestion) }}</span>
                <span class="suggestion-content">{{ getSuggestionContent(suggestion) }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import { confirm } from '../composables/useConfirm'
import { getFullLocale } from '../i18n'

const router = useRouter()

const inputMode = ref('url')
const jobUrl = ref('')
const jobText = ref('')
const analyzing = ref(false)
const error = ref('')
const result = ref(null)
const history = ref([])
const loadingHistory = ref(false)
const hasResume = ref(false) // Assume false until confirmed (safe default)
const checkingResume = ref(true)

// Keyword tooltip state
const activeKeywordTooltip = ref(null)

// Generate integration tip for a keyword
const getKeywordTip = (keyword, category = null) => {
  const tips = {
    hard_skills: [
      `Füge "${keyword}" in deine Berufserfahrung ein, z.B.: "Anwendung von ${keyword} in..."`,
      `Erwähne konkrete Projekte, in denen du ${keyword} eingesetzt hast.`,
      `Liste ${keyword} in einem separaten "Technische Fähigkeiten" Abschnitt auf.`
    ],
    soft_skills: [
      `Beschreibe eine Situation, in der du ${keyword} unter Beweis gestellt hast.`,
      `Verwende Formulierungen wie "Durch ${keyword} konnte ich..." in deinen Erfolgen.`,
      `Integriere ${keyword} in die Beschreibung deiner Teamarbeit.`
    ],
    qualifications: [
      `Stelle sicher, dass ${keyword} in deinem Bildungsabschnitt erwähnt wird.`,
      `Falls du ${keyword} besitzt, hebe es prominent hervor.`,
      `Erwäge relevante Zertifikate oder Weiterbildungen zu ${keyword}.`
    ],
    experience: [
      `Quantifiziere deine Erfahrung mit ${keyword}, z.B. "3+ Jahre ${keyword}".`,
      `Beschreibe konkrete Aufgaben und Verantwortlichkeiten mit ${keyword}.`,
      `Zeige Progression und Entwicklung in ${keyword} auf.`
    ],
    default: [
      `Füge "${keyword}" natürlich in deine Berufserfahrung oder Fähigkeiten ein.`,
      `Verwende "${keyword}" im Kontext deiner bisherigen Tätigkeiten.`,
      `Beschreibe konkrete Beispiele, wo du "${keyword}" angewandt hast.`
    ]
  }

  const categoryTips = tips[category] || tips.default
  // Return a random tip from the category
  return categoryTips[Math.floor(Math.random() * categoryTips.length)]
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

const canAnalyze = computed(() => {
  if (inputMode.value === 'url') {
    return jobUrl.value.trim().length > 0
  }
  return jobText.value.trim().length > 0
})

const scoreClass = computed(() => {
  if (!result.value) return ''
  const score = result.value.score
  if (score >= 75) return 'score-high'
  if (score >= 50) return 'score-medium'
  return 'score-low'
})

const scoreDescription = computed(() => {
  if (!result.value) return ''
  const score = result.value.score
  if (score >= 75) return 'Sehr gute Übereinstimmung! Dein Lebenslauf passt gut zur Stelle.'
  if (score >= 50) return 'Gute Basis vorhanden. Mit einigen Anpassungen kannst du deinen Score verbessern.'
  return 'Es gibt einige wichtige Keywords die fehlen. Optimiere deinen Lebenslauf für diese Stelle.'
})

// Progress ring calculations
const circumference = computed(() => 2 * Math.PI * 52) // 2πr where r=52

const progressOffset = computed(() => {
  if (!result.value) return circumference.value
  const score = result.value.score
  return circumference.value - (score / 100) * circumference.value
})

const hasCategory = (category) => {
  return result.value?.categories?.[category] &&
    (result.value.categories[category].matched?.length > 0 ||
     result.value.categories[category].missing?.length > 0)
}

const getSuggestionPriority = (suggestion) => {
  if (typeof suggestion === 'object' && suggestion.priority) {
    return `priority-${suggestion.priority}`
  }
  return 'priority-medium'
}

const getPriorityLabel = (suggestion) => {
  if (typeof suggestion === 'object' && suggestion.priority) {
    const labels = { high: 'Wichtig', medium: 'Empfohlen', low: 'Optional' }
    return labels[suggestion.priority] || 'Empfohlen'
  }
  return 'Empfohlen'
}

const getSuggestionContent = (suggestion) => {
  if (typeof suggestion === 'object' && suggestion.content) {
    return suggestion.content
  }
  return suggestion
}

const analyzeCV = async () => {
  error.value = ''
  result.value = null
  analyzing.value = true

  try {
    const payload = {}
    if (inputMode.value === 'url') {
      payload.job_url = jobUrl.value
    } else {
      payload.job_text = jobText.value
    }

    const { data } = await api.post('/ats/analyze', payload)

    if (data.success) {
      result.value = data.data
      if (window.$toast) {
        window.$toast('Analyse abgeschlossen!', 'success')
      }
      // Refresh history after successful analysis
      fetchHistory()
    } else {
      error.value = data.error || 'Unbekannter Fehler'
    }
  } catch (e) {
    if (e.response?.status === 400) {
      error.value = e.response.data?.error || 'Bitte lade zuerst einen Lebenslauf hoch.'
    } else if (e.response?.status === 429) {
      error.value = 'Rate Limit erreicht. Bitte warte einen Moment.'
    } else if (e.response?.data?.error) {
      error.value = e.response.data.error
    } else {
      error.value = 'Fehler bei der Analyse. Bitte versuche es erneut.'
    }
  } finally {
    analyzing.value = false
  }
}

const fetchHistory = async () => {
  loadingHistory.value = true
  try {
    const { data } = await api.get('/ats/history')
    if (data.success) {
      history.value = data.data.analyses || []
    }
  } catch (e) {
    // Silently fail - history is not critical
    console.error('Failed to fetch history:', e)
  } finally {
    loadingHistory.value = false
  }
}

const loadHistoryItem = async (item) => {
  error.value = ''
  analyzing.value = true

  try {
    const { data } = await api.get(`/ats/history/${item.id}`)
    if (data.success && data.data.result) {
      result.value = data.data.result
      result.value.job_url = data.data.job_url
      if (window.$toast) {
        window.$toast('Analyse geladen', 'success')
      }
    } else {
      error.value = 'Konnte Analyse nicht laden'
    }
  } catch {
    error.value = 'Fehler beim Laden der Analyse'
  } finally {
    analyzing.value = false
  }
}

const confirmDeleteAnalysis = async (item) => {
  const confirmed = await confirm({
    title: 'Analyse löschen',
    message: 'Möchten Sie diese Analyse wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.',
    confirmText: 'Löschen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (confirmed) {
    deleteAnalysis(item)
  }
}

const deleteAnalysis = async (item) => {
  try {
    const { data } = await api.delete(`/ats/history/${item.id}`)
    if (data.success) {
      // Remove from local history array
      history.value = history.value.filter(h => h.id !== item.id)
      if (window.$toast) {
        window.$toast('Analyse gelöscht', 'success')
      }
    }
  } catch {
    if (window.$toast) {
      window.$toast('Fehler beim Löschen der Analyse', 'error')
    }
  }
}

const formatHistoryTitle = (item) => {
  // Prefer title if available
  if (item.title) {
    return item.title.length > 40 ? item.title.slice(0, 40) + '...' : item.title
  }
  // Fallback to URL hostname or default
  if (item.job_url) {
    try {
      const hostname = new URL(item.job_url).hostname.replace('www.', '')
      return hostname.length > 25 ? hostname.slice(0, 25) + '...' : hostname
    } catch {
      return item.job_url.slice(0, 25) + '...'
    }
  }
  return 'Manuelle Eingabe'
}

const formatDate = (isoDate) => {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  return date.toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getScoreClass = (score) => {
  if (score >= 75) return 'score-high'
  if (score >= 50) return 'score-medium'
  return 'score-low'
}

const checkResumeStatus = async () => {
  checkingResume.value = true
  try {
    const { data } = await api.silent.get('/documents')
    const docs = data.documents || []
    hasResume.value = docs.some(doc => doc.doc_type === 'lebenslauf')
  } catch (err) {
    // Safe fallback: assume no resume (show warning rather than false security)
    hasResume.value = false
    console.log('Resume check failed, showing warning to be safe:', err.message)
  } finally {
    checkingResume.value = false
  }
}

const goToDocuments = () => {
  router.push('/documents')
}

onMounted(() => {
  checkResumeStatus()
  fetchHistory()
})
</script>

<style scoped>
.ats-page {
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
   FORM SECTION
   ======================================== */
.form-section {
  max-width: 640px;
}

.form-card {
  padding: var(--space-xl);
}

.input-toggle {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-lg);
  background: var(--color-washi-aged);
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  width: fit-content;
}

.toggle-btn {
  padding: var(--space-sm) var(--space-lg);
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-xs);
  transition: all var(--transition-base);
}

.toggle-btn:hover:not(:disabled) {
  color: var(--color-text-primary);
}

.toggle-btn.active {
  background: var(--color-washi);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

.toggle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.url-input-wrapper {
  position: relative;
}

.url-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-stone);
  pointer-events: none;
}

.url-input {
  padding-left: calc(var(--space-md) + 28px);
}

.form-textarea {
  resize: vertical;
  min-height: 160px;
  font-family: inherit;
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* ========================================
   INFO BOX
   ======================================== */
.info-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-ai);
  margin-bottom: var(--space-lg);
}

.info-box svg {
  flex-shrink: 0;
  color: var(--color-ai);
}

.info-content {
  font-size: 0.875rem;
  color: var(--color-sumi-light);
}

.info-content strong {
  display: block;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.info-content ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.info-content li {
  margin-bottom: var(--space-xs);
}

/* ========================================
   FORM ACTIONS
   ======================================== */
.form-actions {
  text-align: center;
}

.zen-btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  min-width: 200px;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   ERROR BOX
   ======================================== */
.error-box {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(180, 80, 80, 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid #b45050;
  margin-top: var(--space-lg);
  color: #b45050;
  font-size: 0.875rem;
}

.error-box svg {
  flex-shrink: 0;
}

/* ========================================
   RESULTS SECTION
   ======================================== */
.results-section {
  margin-top: var(--space-ma);
}

.results-card {
  padding: var(--space-xl);
}

.results-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-xl);
  text-align: center;
}

/* ========================================
   SCORE DISPLAY - Progress Ring
   ======================================== */
.score-display {
  text-align: center;
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid var(--color-border-light);
}

.score-ring-container {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 0 auto var(--space-lg);
}

.score-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-background {
  stroke: var(--color-washi-aged);
}

.ring-progress {
  transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Score colors */
.score-ring-container.score-high .ring-progress {
  stroke: var(--color-koke);
}

.score-ring-container.score-medium .ring-progress {
  stroke: #c9a227;
}

.score-ring-container.score-low .ring-progress {
  stroke: #b45050;
}

.score-ring-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 600;
  line-height: 1;
}

.score-high .score-value,
.score-ring-container.score-high .score-value {
  color: var(--color-koke);
}

.score-medium .score-value,
.score-ring-container.score-medium .score-value {
  color: #c9a227;
}

.score-low .score-value,
.score-ring-container.score-low .score-value {
  color: #b45050;
}

.score-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.score-description {
  font-size: 1rem;
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0 auto;
}

/* ========================================
   CATEGORIES SECTION
   ======================================== */
.categories-section {
  margin-bottom: var(--space-xl);
}

.section-title {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.categories-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-lg) 0;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}

.category-card {
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}

.category-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.category-icon {
  font-size: 1.25rem;
}

.keyword-lists {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
}

.list-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  margin-right: var(--space-xs);
}

.keyword-tag {
  font-size: 0.8125rem;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-xs);
}

.keyword-tag.matched {
  background: rgba(122, 139, 110, 0.2);
  color: var(--color-koke);
}

.keyword-tag.missing {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

/* Clickable missing keyword badges */
.keyword-tag.clickable {
  position: relative;
  cursor: pointer;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-family: inherit;
  transition: all var(--transition-base);
}

.keyword-tag.clickable:hover {
  background: rgba(180, 80, 80, 0.25);
  transform: translateY(-1px);
}

.keyword-tag.clickable:focus {
  outline: 2px solid #b45050;
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

/* Tooltip position adjustments for edge cases */
@media (max-width: 768px) {
  .keyword-tooltip {
    width: 240px;
    left: 0;
    transform: translateX(0);
  }

  .keyword-tooltip::after {
    left: 20px;
  }
}

/* ========================================
   SUGGESTIONS SECTION
   ======================================== */
.suggestions-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-xl);
}

.suggestions-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.suggestion-item {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: var(--color-washi-warm);
  align-items: flex-start;
}

.suggestion-priority {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-xs);
  flex-shrink: 0;
}

.suggestion-item.priority-high .suggestion-priority {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.suggestion-item.priority-medium .suggestion-priority {
  background: rgba(201, 162, 39, 0.15);
  color: #c9a227;
}

.suggestion-item.priority-low .suggestion-priority {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.suggestion-content {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* ========================================
   HISTORY SECTION
   ======================================== */
.history-section {
  margin-top: var(--space-lg);
  max-width: 640px;
}

.history-card {
  padding: var(--space-lg);
}

.history-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
  color: var(--color-text-secondary);
}

.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-washi-warm);
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
  gap: var(--space-sm);
}

.history-item:hover {
  background: var(--color-washi-aged);
}

.history-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.history-content:hover {
  transform: translateX(4px);
}

.history-delete-btn {
  background: none;
  border: none;
  padding: var(--space-xs);
  cursor: pointer;
  color: var(--color-text-tertiary);
  opacity: 0.5;
  transition: all var(--transition-base);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-delete-btn:hover {
  opacity: 1;
  color: var(--color-error);
  background: rgba(220, 53, 69, 0.1);
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.history-url {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-date {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.history-stats {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-shrink: 0;
}

.history-score {
  font-size: 1rem;
  font-weight: 600;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-xs);
  min-width: 40px;
  text-align: center;
}

.history-score.score-high {
  background: rgba(122, 139, 110, 0.2);
  color: var(--color-koke);
}

.history-score.score-medium {
  background: rgba(201, 162, 39, 0.15);
  color: #c9a227;
}

.history-score.score-low {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.history-keywords {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.history-keywords .matched {
  color: var(--color-koke);
}

.history-keywords .missing {
  color: #b45050;
}

/* ========================================
   RESUME WARNING
   ======================================== */
.resume-warning-section {
  max-width: 640px;
}

.resume-warning {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-xl);
  border: 2px dashed var(--color-terra);
  background: rgba(184, 122, 94, 0.08);
}

.warning-icon {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-terra);
  border-radius: var(--radius-md);
  color: var(--color-washi);
}

.warning-content h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.warning-content p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-lg);
}

.warning-content .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
}

/* ========================================
   ATS TOOLTIP
   ======================================== */
.ats-tooltip-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin-left: var(--space-xs);
  cursor: help;
  color: var(--color-ai);
  vertical-align: middle;
}

.ats-tooltip {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 8px);
  transform: translateX(-50%);
  width: 280px;
  padding: var(--space-md);
  background: var(--color-sumi);
  color: var(--color-washi);
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  font-weight: 400;
  line-height: var(--leading-relaxed);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  visibility: hidden;
  transition: all var(--transition-base);
  z-index: 100;
  pointer-events: none;
}

.ats-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: var(--color-sumi);
}

.ats-tooltip strong {
  display: block;
  margin-bottom: var(--space-xs);
  color: var(--color-washi);
}

.ats-tooltip-trigger:hover .ats-tooltip,
.ats-tooltip-trigger:focus .ats-tooltip {
  opacity: 1;
  visibility: visible;
}

/* ========================================
   SCORE LEGEND
   ======================================== */
.score-legend {
  margin-top: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
}

.legend-title {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-sm);
}

.legend-items {
  display: flex;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-xs);
}

.legend-color.score-high {
  background: var(--color-koke);
}

.legend-color.score-medium {
  background: #c9a227;
}

.legend-color.score-low {
  background: #b45050;
}

.legend-range {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-sumi);
  min-width: 45px;
}

.legend-label {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .form-card,
  .results-card,
  .history-card {
    padding: var(--space-lg);
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .score-ring-container {
    width: 120px;
    height: 120px;
  }

  .score-value {
    font-size: 2rem;
  }

  .suggestion-item {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .history-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .history-stats {
    width: 100%;
    justify-content: space-between;
  }

  .resume-warning {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .warning-content {
    text-align: center;
  }

  .legend-items {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .ats-tooltip {
    left: 0;
    transform: translateX(-10%);
    width: 240px;
  }

  .ats-tooltip::after {
    left: 20%;
  }
}
</style>
