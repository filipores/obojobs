<template>
  <div class="new-application-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Neue Bewerbung</h1>
        <p class="page-subtitle">Generiere ein Anschreiben aus einer Stellenanzeigen-URL</p>
      </section>

      <!-- Form Section -->
      <section class="form-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="form-card zen-card">
          <!-- URL Input with Portal Detection -->
          <div class="form-group">
            <label class="form-label">Stellenanzeigen-URL</label>
            <div class="url-input-wrapper">
              <svg class="url-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              <input
                v-model="url"
                type="url"
                placeholder="https://example.com/jobs/stellenanzeige"
                class="form-input url-input"
                :disabled="loading || generating"
                @input="onUrlInput"
              />
              <!-- Portal Badge -->
              <span v-if="detectedPortal" :class="['portal-badge', `portal-${detectedPortal.id}`]">
                {{ detectedPortal.name }}
              </span>
            </div>
            <p class="form-hint">Kopiere die URL der Stellenanzeige und füge sie hier ein</p>
          </div>

          <!-- Preview Button (only show if no preview yet) -->
          <div v-if="!previewData" class="form-actions preview-actions">
            <button
              @click="loadPreview"
              :disabled="!url || loading"
              class="zen-btn zen-btn-lg"
            >
              <span v-if="loading" class="btn-loading">
                <span class="loading-spinner"></span>
                Lade Stellenanzeige...
              </span>
              <span v-else>
                Stellenanzeige laden
              </span>
            </button>
          </div>

          <!-- Error Message -->
          <div v-if="error && !previewData" class="error-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>{{ error }}</span>
          </div>
        </div>
      </section>

      <!-- Preview Section (shown after loading) -->
      <section v-if="previewData" class="preview-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="preview-card zen-card">
          <div class="preview-header">
            <div class="preview-title-row">
              <h2>Stellenanzeige Preview</h2>
              <span :class="['portal-tag', `portal-${previewData.portal_id}`]">
                {{ previewData.portal }}
              </span>
            </div>
            <button @click="resetPreview" class="reset-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M8 16H3v5"/>
              </svg>
              Neu laden
            </button>
          </div>

          <!-- Missing Fields Warning -->
          <div v-if="previewData.missing_fields?.length > 0" class="warning-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <div>
              <strong>Fehlende Daten</strong>
              <p>Folgende wichtige Felder konnten nicht automatisch erkannt werden: {{ previewData.missing_fields.join(', ') }}</p>
            </div>
          </div>

          <!-- Editable Preview Form -->
          <div class="preview-form">
            <!-- Core Fields Row -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label required">Firma</label>
                <input
                  v-model="editableData.company"
                  type="text"
                  class="form-input"
                  :class="{ 'field-warning': !editableData.company }"
                  placeholder="Firmenname eingeben"
                />
              </div>
              <div class="form-group">
                <label class="form-label required">Position</label>
                <input
                  v-model="editableData.title"
                  type="text"
                  class="form-input"
                  :class="{ 'field-warning': !editableData.title }"
                  placeholder="Stellentitel eingeben"
                />
              </div>
            </div>

            <!-- Location and Employment Type Row -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Standort</label>
                <input
                  v-model="editableData.location"
                  type="text"
                  class="form-input"
                  placeholder="z.B. Berlin, Hamburg"
                />
              </div>
              <div class="form-group">
                <label class="form-label">Anstellungsart</label>
                <input
                  v-model="editableData.employment_type"
                  type="text"
                  class="form-input"
                  placeholder="z.B. Vollzeit, Teilzeit"
                />
              </div>
            </div>

            <!-- Contact Fields Row -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Ansprechpartner</label>
                <input
                  v-model="editableData.contact_person"
                  type="text"
                  class="form-input"
                  placeholder="Name des Ansprechpartners"
                />
              </div>
              <div class="form-group">
                <label class="form-label">Kontakt-Email</label>
                <input
                  v-model="editableData.contact_email"
                  type="email"
                  class="form-input"
                  placeholder="email@firma.de"
                />
              </div>
            </div>

            <!-- Salary (if available) -->
            <div v-if="editableData.salary || previewData.salary" class="form-group">
              <label class="form-label">Gehalt</label>
              <input
                v-model="editableData.salary"
                type="text"
                class="form-input"
                placeholder="Gehaltsangabe"
              />
            </div>

            <!-- Description (collapsible) -->
            <div class="form-group description-group">
              <div class="description-header" @click="showDescription = !showDescription">
                <label class="form-label">Stellenbeschreibung</label>
                <button type="button" class="toggle-btn">
                  <svg
                    :class="['toggle-icon', { rotated: showDescription }]"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>
              <div v-show="showDescription" class="description-content">
                <textarea
                  v-model="editableData.description"
                  class="form-textarea"
                  rows="8"
                  placeholder="Stellenbeschreibung..."
                ></textarea>
              </div>
            </div>

            <!-- Template Variables Info -->
            <div class="template-variables-info">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              <div>
                <strong>Template-Variablen werden automatisch befüllt:</strong>
                <span class="variable-list">
                  <code
                    v-for="(value, key) in templateVariables"
                    :key="key"
                    :title="value || 'nicht verfügbar'"
                    :class="{ missing: !value }"
                  >{{ getVariableDisplay(key) }}</code>
                </span>
              </div>
            </div>
          </div>

          <!-- Job-Fit Score -->
          <JobFitScore
            v-if="tempApplicationId"
            :application-id="tempApplicationId"
            @score-loaded="onJobFitScoreLoaded"
          />

          <!-- Template Selection -->
          <div class="form-group template-selection">
            <label class="form-label">Anschreiben-Template</label>
            <select v-model="selectedTemplateId" class="form-select" :disabled="generating || loadingTemplates">
              <option :value="null">Standard-Template verwenden</option>
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}{{ template.is_default ? ' (Standard)' : '' }}
              </option>
            </select>
          </div>

          <!-- Low Score Warning on Generate Button -->
          <div v-if="showLowScoreWarning" class="low-score-generate-warning">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span>Der Job-Fit Score ist niedrig ({{ jobFitScore?.overall_score }}%). Moeglicherweise passt diese Stelle nicht optimal zu Ihrem Profil.</span>
          </div>

          <!-- Generate Button -->
          <div class="form-actions">
            <button
              @click="generateApplication"
              :disabled="!canGenerate || generating"
              class="zen-btn zen-btn-ai zen-btn-lg"
            >
              <span v-if="generating" class="btn-loading">
                <span class="loading-spinner"></span>
                Generiere Bewerbung...
              </span>
              <span v-else>
                Bewerbung generieren
              </span>
            </button>
            <p class="usage-info">
              <span v-if="usage?.unlimited">Unbegrenzte Bewerbungen ({{ getPlanLabel() }})</span>
              <span v-else>{{ usage?.remaining || 0 }}/{{ usage?.limit || 3 }} Bewerbungen diesen Monat</span>
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="error && previewData" class="error-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>{{ error }}</span>
          </div>
        </div>
      </section>

      <!-- Info Box (show when no preview) -->
      <section v-if="!previewData" class="info-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="info-box zen-card">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <div class="info-content">
            <strong>So funktioniert's:</strong>
            <ul>
              <li>Füge eine Stellenanzeigen-URL ein</li>
              <li>Die Daten werden automatisch extrahiert (Firma, Position, Kontakt...)</li>
              <li>Prüfe und bearbeite die Daten vor der Generierung</li>
              <li>Ein personalisiertes Anschreiben wird erstellt</li>
            </ul>
            <div class="supported-portals">
              <strong>Unterstützte Job-Portale:</strong>
              <div class="portal-list">
                <span class="portal-item portal-stepstone">StepStone</span>
                <span class="portal-item portal-indeed">Indeed</span>
                <span class="portal-item portal-xing">XING</span>
                <span class="portal-item portal-generic">+ Weitere</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Success Modal -->
      <Teleport to="body">
        <div v-if="generatedApp" class="modal-overlay" @click="closeModal">
          <div class="modal zen-card animate-fade-up" @click.stop>
            <div class="modal-header success-header">
              <div class="success-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <div>
                <h2>Bewerbung erstellt!</h2>
                <p class="modal-subtitle">{{ generatedApp.firma }}</p>
              </div>
              <button @click="closeModal" class="modal-close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div class="modal-content">
              <!-- Info Grid -->
              <div class="info-grid">
                <div class="detail-group">
                  <label class="detail-label">Firma</label>
                  <p class="detail-value">{{ generatedApp.firma }}</p>
                </div>

                <div class="detail-group">
                  <label class="detail-label">Position</label>
                  <p class="detail-value">{{ generatedApp.position || 'Nicht angegeben' }}</p>
                </div>

                <div v-if="generatedApp.ansprechpartner" class="detail-group">
                  <label class="detail-label">Ansprechpartner</label>
                  <p class="detail-value">{{ generatedApp.ansprechpartner }}</p>
                </div>

                <div v-if="generatedApp.email" class="detail-group">
                  <label class="detail-label">Email</label>
                  <p class="detail-value">
                    <a :href="`mailto:${generatedApp.email}`" class="detail-link">{{ generatedApp.email }}</a>
                  </p>
                </div>
              </div>

              <!-- Betreff -->
              <div v-if="generatedApp.betreff" class="detail-group">
                <label class="detail-label">Betreff</label>
                <p class="detail-value detail-value-block">{{ generatedApp.betreff }}</p>
              </div>
            </div>

            <div class="modal-footer">
              <button @click="downloadPDF" class="zen-btn zen-btn-ai">
                PDF herunterladen
              </button>
              <button @click="goToApplications" class="zen-btn">
                Alle Bewerbungen
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
import { useRouter } from 'vue-router'
import api from '../api/client'
import JobFitScore from '../components/JobFitScore.vue'

const router = useRouter()

// State
const url = ref('')
const selectedTemplateId = ref(null)
const templates = ref([])
const loadingTemplates = ref(false)
const loading = ref(false)
const generating = ref(false)
const error = ref('')
const usage = ref(null)
const generatedApp = ref(null)

// Preview state
const previewData = ref(null)
const editableData = ref({
  company: '',
  title: '',
  location: '',
  employment_type: '',
  contact_person: '',
  contact_email: '',
  salary: '',
  description: ''
})
const showDescription = ref(false)

// Job-Fit Score state
const tempApplicationId = ref(null)
const jobFitScore = ref(null)
const showLowScoreWarning = ref(false)

// Portal detection (real-time based on URL)
const detectedPortal = computed(() => {
  if (!url.value) return null

  const urlLower = url.value.toLowerCase()

  if (urlLower.includes('stepstone.de')) {
    return { id: 'stepstone', name: 'StepStone' }
  }
  if (urlLower.includes('indeed.com') || urlLower.includes('indeed.de')) {
    return { id: 'indeed', name: 'Indeed' }
  }
  if (urlLower.includes('xing.com')) {
    return { id: 'xing', name: 'XING' }
  }
  if (urlLower.includes('arbeitsagentur.de')) {
    return { id: 'arbeitsagentur', name: 'Arbeitsagentur' }
  }

  // Generic if it looks like a URL
  if (url.value.startsWith('http')) {
    return { id: 'generic', name: 'Sonstige' }
  }

  return null
})

// Template variables computed from editable data
const templateVariables = computed(() => ({
  FIRMA: editableData.value.company,
  POSITION: editableData.value.title,
  ANSPRECHPARTNER: editableData.value.contact_person,
  STANDORT: editableData.value.location,
  QUELLE: previewData.value?.portal || ''
}))

// Can generate check
const canGenerate = computed(() => {
  return editableData.value.company && editableData.value.title
})

// Helper to display template variable name with double braces
const getVariableDisplay = (key) => {
  return `{{${key}}}`
}

// Debounce URL input
let urlInputTimeout = null
const onUrlInput = () => {
  // Clear any existing timeout
  if (urlInputTimeout) clearTimeout(urlInputTimeout)

  // Reset preview when URL changes significantly
  if (previewData.value && url.value !== previewData.value.url) {
    previewData.value = null
    editableData.value = {
      company: '',
      title: '',
      location: '',
      employment_type: '',
      contact_person: '',
      contact_email: '',
      salary: '',
      description: ''
    }
  }
}

// Load preview data from URL
const loadPreview = async () => {
  if (!url.value) return

  error.value = ''
  loading.value = true
  tempApplicationId.value = null
  jobFitScore.value = null
  showLowScoreWarning.value = false

  try {
    const { data } = await api.post('/applications/preview-job', {
      url: url.value
    })

    if (data.success) {
      previewData.value = data.data

      // Populate editable data from preview
      editableData.value = {
        company: data.data.company || '',
        title: data.data.title || '',
        location: data.data.location || '',
        employment_type: data.data.employment_type || '',
        contact_person: data.data.contact_person || '',
        contact_email: data.data.contact_email || '',
        salary: data.data.salary || '',
        description: data.data.description || ''
      }

      // Create temporary application for job-fit analysis
      if (data.data.description) {
        try {
          const analyzeResponse = await api.post('/applications/analyze-job-fit', {
            url: url.value,
            description: data.data.description,
            company: data.data.company,
            title: data.data.title
          })
          if (analyzeResponse.data.success) {
            tempApplicationId.value = analyzeResponse.data.application_id
          }
        } catch (analyzeError) {
          console.log('Job-Fit Analyse nicht verfuegbar:', analyzeError.message)
        }
      }

      if (window.$toast) {
        window.$toast('Stellenanzeige geladen!', 'success')
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
    }
  } catch (e) {
    if (e.response?.data?.error) {
      error.value = e.response.data.error
    } else {
      error.value = 'Fehler beim Laden der Stellenanzeige. Bitte versuche es erneut.'
    }
  } finally {
    loading.value = false
  }
}

// Handle job-fit score loaded event
const onJobFitScoreLoaded = (score) => {
  jobFitScore.value = score
  showLowScoreWarning.value = score.overall_score < 40
}

// Reset preview and start fresh
const resetPreview = () => {
  previewData.value = null
  editableData.value = {
    company: '',
    title: '',
    location: '',
    employment_type: '',
    contact_person: '',
    contact_email: '',
    salary: '',
    description: ''
  }
  error.value = ''
}

// Load templates
const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const { data } = await api.get('/templates')
    templates.value = data.templates || []
  } catch (e) {
    console.error('Fehler beim Laden der Templates:', e)
  } finally {
    loadingTemplates.value = false
  }
}

// Load usage
const loadUsage = async () => {
  try {
    const { data } = await api.get('/stats')
    usage.value = data.usage
  } catch (e) {
    console.error('Fehler beim Laden der Nutzung:', e)
  }
}

const getPlanLabel = () => {
  const plan = usage.value?.plan || 'free'
  return plan.charAt(0).toUpperCase() + plan.slice(1)
}

// Generate application
const generateApplication = async () => {
  if (!canGenerate.value) return

  error.value = ''
  generating.value = true

  try {
    const { data } = await api.post('/applications/generate-from-url', {
      url: url.value,
      template_id: selectedTemplateId.value
    })

    if (data.success) {
      generatedApp.value = data.application
      // Reload usage after generation
      await loadUsage()
      // Reset form
      url.value = ''
      previewData.value = null
      editableData.value = {
        company: '',
        title: '',
        location: '',
        employment_type: '',
        contact_person: '',
        contact_email: '',
        salary: '',
        description: ''
      }

      if (window.$toast) {
        window.$toast('Bewerbung erfolgreich generiert!', 'success')
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
    }
  } catch (e) {
    if (e.response?.status === 403 && e.response?.data?.error_code === 'SUBSCRIPTION_LIMIT_REACHED') {
      error.value = e.response.data.error
    } else if (e.response?.data?.error) {
      error.value = e.response.data.error
    } else {
      error.value = 'Fehler bei der Generierung. Bitte versuche es erneut.'
    }
  } finally {
    generating.value = false
  }
}

const downloadPDF = () => {
  if (generatedApp.value?.id) {
    window.open(`/api/applications/${generatedApp.value.id}/pdf`, '_blank')
  }
}

const goToApplications = () => {
  router.push('/applications')
}

const closeModal = () => {
  generatedApp.value = null
}

onMounted(() => {
  loadTemplates()
  loadUsage()
})
</script>

<style scoped>
.new-application-page {
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

.form-label.required::after {
  content: ' *';
  color: #b45050;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
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
  padding-right: 100px;
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* ========================================
   PORTAL BADGE
   ======================================== */
.portal-badge {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.portal-badge.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-badge.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-badge.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-badge.portal-arbeitsagentur {
  background: rgba(0, 68, 103, 0.15);
  color: #004467;
}

.portal-badge.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

/* ========================================
   PREVIEW SECTION
   ======================================== */
.preview-section {
  max-width: 800px;
}

.preview-card {
  padding: var(--space-xl);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.preview-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.preview-title-row h2 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.portal-tag {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.portal-tag.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-tag.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-tag.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-tag.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.reset-btn:hover {
  background: var(--color-washi-warm);
  color: var(--color-text-primary);
}

/* ========================================
   WARNING BOX
   ======================================== */
.warning-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(201, 162, 39, 0.1);
  border: 1px solid rgba(201, 162, 39, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.warning-box svg {
  flex-shrink: 0;
  color: #c9a227;
}

.warning-box strong {
  display: block;
  color: #8a6d17;
  margin-bottom: var(--space-xs);
  font-size: 0.875rem;
}

.warning-box p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

/* ========================================
   PREVIEW FORM
   ======================================== */
.preview-form {
  margin-bottom: var(--space-lg);
}

.field-warning {
  border-color: rgba(201, 162, 39, 0.5);
  background: rgba(201, 162, 39, 0.05);
}

/* Description Toggle */
.description-group {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.description-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.description-header .form-label {
  margin-bottom: 0;
  cursor: pointer;
}

.toggle-btn {
  background: none;
  border: none;
  padding: var(--space-xs);
  cursor: pointer;
  color: var(--color-text-tertiary);
}

.toggle-icon {
  transition: transform var(--transition-base);
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.description-content {
  margin-top: var(--space-md);
}

/* ========================================
   TEMPLATE VARIABLES INFO
   ======================================== */
.template-variables-info {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  margin-top: var(--space-lg);
}

.template-variables-info svg {
  flex-shrink: 0;
  color: var(--color-ai);
  margin-top: 2px;
}

.template-variables-info strong {
  display: block;
  font-size: 0.8125rem;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.variable-list code {
  padding: 2px var(--space-xs);
  background: var(--color-washi);
  border-radius: var(--radius-xs);
  font-size: 0.75rem;
  color: var(--color-ai);
}

.variable-list code.missing {
  color: var(--color-text-tertiary);
  opacity: 0.6;
}

/* ========================================
   TEMPLATE SELECTION
   ======================================== */
.template-selection {
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

/* ========================================
   INFO SECTION
   ======================================== */
.info-section {
  max-width: 640px;
}

.info-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
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
  margin: 0 0 var(--space-lg) 0;
  padding-left: var(--space-lg);
}

.info-content li {
  margin-bottom: var(--space-xs);
}

.supported-portals {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.portal-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.portal-item {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.portal-item.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-item.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-item.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-item.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

/* ========================================
   FORM ACTIONS
   ======================================== */
.form-actions {
  text-align: center;
}

.preview-actions {
  margin-top: var(--space-lg);
}

.zen-btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  min-width: 240px;
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

.usage-info {
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

/* ========================================
   LOW SCORE WARNING
   ======================================== */
.low-score-generate-warning {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(201, 162, 39, 0.1);
  border: 1px solid rgba(201, 162, 39, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.low-score-generate-warning svg {
  flex-shrink: 0;
  color: #c9a227;
  margin-top: 2px;
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
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-xl);
  border-bottom: 1px solid var(--color-border-light);
}

.success-header {
  background: rgba(122, 139, 110, 0.1);
}

.success-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-koke);
  color: white;
  border-radius: 50%;
  flex-shrink: 0;
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
  margin-left: auto;
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

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.detail-group {
  margin-bottom: var(--space-md);
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
}

.detail-link {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.detail-link:hover {
  text-decoration: underline;
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
  .form-card,
  .preview-card {
    padding: var(--space-lg);
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }

  .zen-btn-lg {
    width: 100%;
  }

  .url-input {
    padding-right: var(--space-md);
  }

  .portal-badge {
    position: static;
    transform: none;
    display: inline-block;
    margin-top: var(--space-sm);
  }

  .url-input-wrapper {
    display: flex;
    flex-direction: column;
  }
}
</style>
