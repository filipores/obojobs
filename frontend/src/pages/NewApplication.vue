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
          <!-- URL Input -->
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
                :disabled="generating"
              />
            </div>
            <p class="form-hint">Kopiere die URL der Stellenanzeige und füge sie hier ein</p>
          </div>

          <!-- Template Selection -->
          <div class="form-group">
            <label class="form-label">Anschreiben-Template</label>
            <select v-model="selectedTemplateId" class="form-select" :disabled="generating || loadingTemplates">
              <option :value="null">Standard-Template verwenden</option>
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}{{ template.is_default ? ' (Standard)' : '' }}
              </option>
            </select>
          </div>

          <!-- Info Box -->
          <div class="info-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <div class="info-content">
              <strong>So funktioniert's:</strong>
              <ul>
                <li>Die Stellenanzeige wird automatisch analysiert</li>
                <li>Firma und Position werden extrahiert</li>
                <li>Ein personalisiertes Anschreiben wird generiert</li>
              </ul>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="form-actions">
            <button
              @click="generateApplication"
              :disabled="!url || generating"
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
            <p class="credits-info">
              Du hast noch <strong>{{ credits }}</strong> Credits
            </p>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()

const url = ref('')
const selectedTemplateId = ref(null)
const templates = ref([])
const loadingTemplates = ref(false)
const generating = ref(false)
const error = ref('')
const credits = ref(0)
const generatedApp = ref(null)

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

const loadCredits = async () => {
  try {
    const { data } = await api.get('/stats')
    credits.value = data.credits_remaining || 0
  } catch (e) {
    console.error('Fehler beim Laden der Credits:', e)
  }
}

const generateApplication = async () => {
  if (!url.value) return

  error.value = ''
  generating.value = true

  try {
    const { data } = await api.post('/applications/generate-from-url', {
      url: url.value,
      template_id: selectedTemplateId.value
    })

    if (data.success) {
      generatedApp.value = data.application
      credits.value = data.credits_remaining
      url.value = ''

      if (window.$toast) {
        window.$toast('Bewerbung erfolgreich generiert!', 'success')
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
    }
  } catch (e) {
    if (e.response?.status === 402) {
      error.value = 'Keine Credits mehr vorhanden. Bitte kaufe weitere Credits.'
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
  loadCredits()
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

.credits-info {
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.credits-info strong {
  color: var(--color-ai);
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
  .form-card {
    padding: var(--space-lg);
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
}
</style>
