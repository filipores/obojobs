<template>
  <div class="new-application-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Neue Bewerbung</h1>
        <p class="page-subtitle">Generiere ein Anschreiben aus einer Stellenanzeigen-URL</p>
      </section>

      <!-- Zero-State: CV Invitation - transforms CV-missing from blocker to invitation -->
      <section v-if="!checkingResume && !hasResume" class="cv-invitation-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="cv-invitation-card zen-card">
          <div class="cv-invitation-enso">
            <EnsoCircle state="breathing" size="lg" color="var(--color-ai)" :duration="5000" />
          </div>
          <h2 class="cv-invitation-title">Dein Lebenslauf bringt dein Anschreiben zum Leben</h2>
          <p class="cv-invitation-text">
            Lade deinen Lebenslauf hoch und wir erstellen personalisierte Bewerbungen,
            die deine Erfahrungen und Fähigkeiten perfekt zur Geltung bringen.
          </p>
          <router-link to="/documents?from=new-application&upload=lebenslauf" class="zen-btn zen-btn-ai zen-btn-lg cv-invitation-cta">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Lebenslauf hochladen
          </router-link>
          <span class="cv-invitation-hint">PDF-Format, max. 10 MB</span>
        </div>
      </section>

      <!-- Skills Missing Warning Banner - vor dem Formular -->
      <section v-if="!checkingSkills && !hasSkills && hasResume" class="skills-warning-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="skills-warning zen-card">
          <div class="warning-icon-box">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <div class="warning-text-content">
            <h3>Skills für Job-Fit-Analyse benötigt</h3>
            <p>
              Um den <strong>Job-Fit Score</strong> zu berechnen, werden deine Skills mit den Anforderungen der Stellenanzeige verglichen.
              Du kannst trotzdem eine Bewerbung generieren, aber der Job-Fit Score ist ohne Skills nicht verfügbar.
            </p>
            <div class="warning-actions">
              <router-link to="/documents#skills" class="zen-btn zen-btn-ai">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
                Skills extrahieren
              </router-link>
              <span class="warning-hint">Skills werden aus deinem bereits hochgeladenen Lebenslauf extrahiert</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Profile Incomplete Warning Banner -->
      <section v-if="profileIncomplete && hasResume" class="profile-warning-section animate-fade-up" style="animation-delay: 120ms;">
        <div class="profile-warning zen-card">
          <div class="warning-icon-box profile-warning-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div class="warning-text-content">
            <h3>Profil unvollst&auml;ndig</h3>
            <p>
              Erg&auml;nze fehlende Angaben in den <strong>Einstellungen</strong> f&uuml;r professionellere Bewerbungen.
              Du kannst trotzdem Bewerbungen generieren.
            </p>
            <div class="warning-actions">
              <router-link to="/settings" class="zen-btn zen-btn-secondary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                Zu den Einstellungen
              </router-link>
              <button class="zen-btn zen-btn-ghost profile-dismiss-btn" @click="dismissProfileWarning">Verstanden</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Usage Indicator - Show prominently before form -->
      <section v-if="usage" class="usage-section animate-fade-up" style="animation-delay: 150ms;">
        <UsageIndicator
          :used="usage.used"
          :limit="usage.limit"
          :unlimited="usage.unlimited"
          :plan="usage.plan"
        />
      </section>

      <!-- Form Section - subtly faded when no CV (anticipation) -->
      <section class="form-section animate-fade-up" :class="{ 'form-section--anticipation': !checkingResume && !hasResume }" style="animation-delay: 100ms;">
        <JobUrlInput
          v-model="url"
          :loading="loading"
          :generating="generating"
          :error="error"
          :quick-confirm-data="quickConfirmData"
          :preview-data="previewData"
          :show-manual-fallback="showManualFallback"
          :analyzing-manual-text="analyzingManualText"
          :recognition-complete="recognitionComplete"
          :recognized-company="recognizedCompany"
          :url-touched="urlTouched"
          @url-input="onUrlInput"
          @url-paste="onUrlPaste"
          @url-enter="loadPreview"
          @show-manual-fallback="showManualFallback = true"
          @analyze-manual-text="analyzeManualText"
          @reset-manual-fallback="resetManualFallback"
        />
      </section>

      <!-- Minimal Confirmation Section (quick flow) -->
      <QuickExtract
        v-if="quickConfirmData && !showFullPreview"
        :quick-confirm-data="quickConfirmData"
        :selected-template-id="selectedTemplateId"
        :templates="templates"
        :loading-templates="loadingTemplates"
        :generating="generating"
        :loading="loading"
        :can-generate="canGenerate"
        :usage="usage"
        :error="error"
        @generate="generateApplication"
        @load-full-preview="loadFullPreview"
        @reset="resetPreview"
        @update:selected-template-id="selectedTemplateId = $event"
      />

      <!-- Preview Section (shown after loading full details) -->
      <JobPreview
        v-if="previewData && showFullPreview"
        :preview-data="previewData"
        :editable-data="editableData"
        :selected-template-id="selectedTemplateId"
        :templates="templates"
        :loading-templates="loadingTemplates"
        :generating="generating"
        :can-generate="canGenerate"
        :is-at-usage-limit="isAtUsageLimit"
        :usage="usage"
        :error="error"
        @reset="resetPreview"
        @generate="generateApplication"
        @update:editable-data="editableData = $event"
        @update:selected-template-id="selectedTemplateId = $event"
      />

      <!-- Info Box (show when no quick confirm or preview) -->
      <section v-if="!quickConfirmData && !previewData" class="info-section animate-fade-up" style="animation-delay: 200ms;">
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

      <!-- Crafting Overlay - Cinematic generation experience -->
      <CraftingOverlay
        :is-active="showCraftingOverlay"
        :company-name="editableData.company"
        :job-title="editableData.title"
        :job-description="editableData.description"
        :contact-person="editableData.contact_person"
        @complete="onCraftingComplete"
      />

      <!-- Premium Reveal Success Modal -->
      <GenerationResult
        :generated-app="generatedApp"
        :reveal-phase="revealPhase"
        :enso-state="ensoState"
        @close="closeModal"
        @download-pdf="downloadPDF"
        @go-to-applications="goToApplications"
        @send-email="sendEmail"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import { authStore } from '../stores/auth'
import UsageIndicator from '../components/UsageIndicator.vue'
import EnsoCircle from '../components/application/EnsoCircle.vue'
import CraftingOverlay from '../components/application/CraftingOverlay.vue'
import JobUrlInput from '../components/NewApplication/JobUrlInput.vue'
import QuickExtract from '../components/NewApplication/QuickExtract.vue'
import JobPreview from '../components/NewApplication/JobPreview.vue'
import GenerationResult from '../components/NewApplication/GenerationResult.vue'

const router = useRouter()

const handleKeydown = (e) => {
  if (e.key === 'Escape' && generatedApp.value) {
    closeModal()
  }
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (pasteDebounceTimeout) {
    clearTimeout(pasteDebounceTimeout)
  }
})

const checkingSkills = ref(true)
const hasSkills = ref(true)
const checkingResume = ref(true)
const hasResume = ref(true)
const profileIncomplete = ref(false)
const profileWarningDismissed = ref(false)

const url = ref('')
const urlTouched = ref(false)
const selectedTemplateId = ref(null)
const templates = ref([])
const loadingTemplates = ref(false)
const loading = ref(false)
const generating = ref(false)
const error = ref('')
const usage = ref(null)
const generatedApp = ref(null)
const showCraftingOverlay = ref(false)

const revealPhase = ref(0)
const ensoState = ref('broken')

const quickConfirmData = ref(null)
const showFullPreview = ref(false)

const recognitionComplete = ref(false)
const recognizedCompany = ref('')
let pasteDebounceTimeout = null

const defaultEditableData = () => ({
  company: '',
  title: '',
  location: '',
  employment_type: '',
  contact_person: '',
  contact_email: '',
  salary: '',
  description: ''
})

const extractApiError = (e, fallbackMessage) => {
  return e.response?.data?.error || fallbackMessage
}

const previewData = ref(null)
const editableData = ref(defaultEditableData())

const showManualFallback = ref(false)
const manualJobText = ref('')
const manualCompany = ref('')
const manualTitle = ref('')
const manualTextError = ref('')
const analyzingManualText = ref(false)
const isManualEntry = ref(false)

const isAtUsageLimit = computed(() => {
  if (!usage.value || usage.value.unlimited) return false
  return usage.value.used >= usage.value.limit
})

const canGenerate = computed(() => {
  return editableData.value.company && editableData.value.title && !isAtUsageLimit.value
})

let urlInputTimeout = null
const onUrlInput = () => {
  urlTouched.value = true

  if (urlInputTimeout) clearTimeout(urlInputTimeout)

  if (previewData.value && url.value !== previewData.value.url) {
    previewData.value = null
    editableData.value = defaultEditableData()
  }
}

const urlValidation = computed(() => {
  const urlValue = url.value.trim()
  if (!urlValue) return { isValid: null, message: '' }
  if (!urlValue.match(/^https?:\/\//i)) {
    return { isValid: false, message: 'URL muss mit http:// oder https:// beginnen' }
  }
  try {
    const parsedUrl = new URL(urlValue)
    if (!parsedUrl.hostname.includes('.')) return { isValid: false, message: 'Ungültige Domain' }
    if (parsedUrl.hostname.endsWith('.')) return { isValid: false, message: 'Domain darf nicht mit einem Punkt enden' }
    return { isValid: true, message: '' }
  } catch {
    return { isValid: false, message: 'Ungültiges URL-Format' }
  }
})

const onUrlPaste = () => {
  urlTouched.value = true

  if (pasteDebounceTimeout) {
    clearTimeout(pasteDebounceTimeout)
  }

  setTimeout(() => {
    if (url.value && urlValidation.value.isValid === true && !loading.value && !generating.value && !quickConfirmData.value && !previewData.value) {
      pasteDebounceTimeout = setTimeout(() => {
        loadPreviewWithAnimation()
      }, 500)
    }
  }, 0)
}

const loadPreviewWithAnimation = async () => {
  recognitionComplete.value = false
  recognizedCompany.value = ''

  await loadPreview()

  if (quickConfirmData.value) {
    recognizedCompany.value = quickConfirmData.value.company || ''
    recognitionComplete.value = true

    await new Promise(resolve => setTimeout(resolve, 800))
  }
}

const loadPreview = async () => {
  if (!url.value) return

  error.value = ''
  loading.value = true
  quickConfirmData.value = null
  showFullPreview.value = false
  previewData.value = null

  try {
    const { data } = await api.post('/applications/quick-extract', {
      url: url.value
    })

    if (data.success) {
      quickConfirmData.value = data.data

      editableData.value = {
        ...defaultEditableData(),
        company: data.data.company || '',
        title: data.data.title || '',
      }

      loading.value = false

      if (window.$toast) {
        window.$toast('Stellenanzeige erkannt!', 'success')
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
      loading.value = false
    }
  } catch (e) {
    error.value = extractApiError(e, 'Fehler beim Laden der Stellenanzeige. Bitte versuche es erneut.')
    loading.value = false
  }
}

const loadFullPreview = async () => {
  if (!url.value) return

  error.value = ''
  loading.value = true

  try {
    const { data } = await api.post('/applications/preview-job', {
      url: url.value
    })

    if (data.success) {
      previewData.value = data.data
      showFullPreview.value = true

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

      loading.value = false

      if (window.$toast) {
        window.$toast('Details geladen!', 'success')
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
      loading.value = false
    }
  } catch (e) {
    error.value = extractApiError(e, 'Fehler beim Laden der Details. Bitte versuche es erneut.')
    loading.value = false
  }
}

const resetPreview = () => {
  quickConfirmData.value = null
  showFullPreview.value = false
  previewData.value = null
  editableData.value = defaultEditableData()
  error.value = ''
  isManualEntry.value = false
  showManualFallback.value = false
  manualJobText.value = ''
  manualCompany.value = ''
  manualTitle.value = ''
  urlTouched.value = false
  recognitionComplete.value = false
  recognizedCompany.value = ''
  if (pasteDebounceTimeout) {
    clearTimeout(pasteDebounceTimeout)
    pasteDebounceTimeout = null
  }
}

const resetManualFallback = () => {
  showManualFallback.value = false
  manualJobText.value = ''
  manualCompany.value = ''
  manualTitle.value = ''
  manualTextError.value = ''
}

const analyzeManualText = async ({ jobText, company, title }) => {
  if (jobText.trim().length < 100) return

  analyzingManualText.value = true
  manualTextError.value = ''

  try {
    const { data } = await api.post('/applications/analyze-manual-text', {
      job_text: jobText,
      company,
      title
    })

    if (data.success) {
      previewData.value = data.data
      isManualEntry.value = true

      editableData.value = {
        company: data.data.company || company || '',
        title: data.data.title || title || '',
        location: data.data.location || '',
        employment_type: data.data.employment_type || '',
        contact_person: data.data.contact_person || '',
        contact_email: data.data.contact_email || '',
        salary: data.data.salary || '',
        description: data.data.description || jobText
      }

      showFullPreview.value = true
      showManualFallback.value = false
      analyzingManualText.value = false
      error.value = ''

      if (window.$toast) {
        window.$toast('Stellentext analysiert!', 'success')
      }
    } else {
      manualTextError.value = data.error || 'Analyse fehlgeschlagen'
      analyzingManualText.value = false
    }
  } catch (e) {
    manualTextError.value = e.response?.data?.error || 'Fehler bei der Analyse'
    analyzingManualText.value = false
  }
}

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

const loadUsage = async () => {
  try {
    const { data } = await api.get('/stats')
    usage.value = data.usage
  } catch (e) {
    console.error('Fehler beim Laden der Nutzung:', e)
  }
}

const onCraftingComplete = () => {
  showCraftingOverlay.value = false
}

const generateApplication = async () => {
  if (!canGenerate.value) return

  error.value = ''
  generating.value = true
  showCraftingOverlay.value = true

  try {
    let response

    if (isManualEntry.value) {
      response = await api.post('/applications/generate-from-text', {
        job_text: editableData.value.description,
        company: editableData.value.company,
        title: editableData.value.title,
        template_id: selectedTemplateId.value,
        description: editableData.value.description
      })
    } else {
      response = await api.post('/applications/generate-from-url', {
        url: url.value,
        template_id: selectedTemplateId.value,
        company: editableData.value.company,
        title: editableData.value.title,
        contact_person: editableData.value.contact_person,
        contact_email: editableData.value.contact_email,
        location: editableData.value.location,
        description: editableData.value.description
      })
    }

    const { data } = response

    if (data.success) {
      generatedApp.value = data.application
      showCraftingOverlay.value = false
      startPremiumReveal()
      await loadUsage()
      url.value = ''
      resetPreview()

      if (window.$toast) {
        window.$toast('Bewerbung erfolgreich generiert!', 'success')
        if (data.profile_warning?.incomplete) {
          setTimeout(() => {
            window.$toast('Profil unvollständig — ergänze fehlende Angaben in den Einstellungen.', 'warning')
          }, 1500)
        }
      }
    } else {
      showCraftingOverlay.value = false
      error.value = data.error || 'Unbekannter Fehler'
    }
  } catch (e) {
    showCraftingOverlay.value = false
    error.value = extractApiError(e, 'Fehler bei der Generierung. Bitte versuche es erneut.')
  } finally {
    generating.value = false
  }
}

const downloadPDF = async () => {
  if (!generatedApp.value?.id) return

  try {
    const response = await api.get(`/applications/${generatedApp.value.id}/pdf`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const pdfUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = pdfUrl
    link.download = `bewerbung_${generatedApp.value.id}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(pdfUrl)
  } catch (err) {
    console.error('PDF download error:', err)
    error.value = 'Fehler beim Herunterladen des PDF'
  }
}

const goToApplications = () => {
  router.push('/applications')
}

const sendEmail = () => {
  const id = generatedApp.value?.id
  if (!id) return
  closeModal()
  router.push({ path: '/applications', query: { open: String(id), action: 'email' } })
}

const closeModal = () => {
  generatedApp.value = null
  revealPhase.value = 0
  ensoState.value = 'broken'
}

const startPremiumReveal = async () => {
  revealPhase.value = 0
  ensoState.value = 'broken'

  await nextTick()

  revealPhase.value = 1

  setTimeout(() => {
    ensoState.value = 'complete'
  }, 300)

  setTimeout(() => {
    revealPhase.value = 2
  }, 900)

  setTimeout(() => {
    revealPhase.value = 3
  }, 1400)
}

const checkUserSkills = async () => {
  checkingSkills.value = true
  try {
    const { data } = await api.get('/users/me/skills')
    const userSkills = data.skills || []
    hasSkills.value = userSkills.length > 0
  } catch {
    hasSkills.value = true
  } finally {
    checkingSkills.value = false
  }
}

const checkUserResume = async () => {
  checkingResume.value = true
  try {
    const { data } = await api.get('/documents')
    const documents = data.documents || []
    hasResume.value = documents.some(doc => doc.doc_type === 'lebenslauf')
  } catch {
    hasResume.value = true
  } finally {
    checkingResume.value = false
  }
}

const checkProfileCompleteness = () => {
  const user = authStore.user
  if (!user) return
  const requiredFields = ['full_name', 'phone', 'address', 'city', 'postal_code']
  const missing = requiredFields.filter(f => !user[f])
  profileIncomplete.value = missing.length > 0 && !profileWarningDismissed.value
}

const dismissProfileWarning = () => {
  profileWarningDismissed.value = true
  profileIncomplete.value = false
}

onMounted(() => {
  loadTemplates()
  loadUsage()
  checkUserSkills()
  checkUserResume()
  checkProfileCompleteness()
  document.addEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.new-application-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

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

.cv-invitation-section {
  max-width: 520px;
  margin-bottom: var(--space-xl);
}

.cv-invitation-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-2xl) var(--space-xl);
  background: linear-gradient(180deg, var(--color-washi) 0%, var(--color-washi-warm) 100%);
  border: 1px solid var(--color-border-light);
}

.cv-invitation-enso {
  margin-bottom: var(--space-xl);
}

.cv-invitation-title {
  font-size: 1.5rem;
  font-weight: 400;
  letter-spacing: -0.01em;
  color: var(--color-sumi);
  margin: 0 0 var(--space-md) 0;
  line-height: var(--leading-snug);
}

.cv-invitation-text {
  font-size: 1rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-xl) 0;
  max-width: 380px;
}

.cv-invitation-cta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  margin-bottom: var(--space-md);
}

.cv-invitation-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.form-section--anticipation {
  opacity: 0.5;
  pointer-events: none;
  position: relative;
}

.form-section--anticipation::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, transparent 0%, var(--color-washi) 80%);
  pointer-events: none;
}

.skills-warning-section {
  max-width: 640px;
  margin-bottom: var(--space-lg);
}

.skills-warning {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-xl);
  border: 2px solid var(--color-ai);
  background: var(--color-ai-subtle);
}

.warning-icon-box {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  border-radius: var(--radius-md);
  color: white;
}

.warning-text-content h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-sumi);
}

.warning-text-content p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-lg) 0;
}

.warning-text-content p strong {
  color: var(--color-ai);
}

.warning-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.warning-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
}

.warning-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  font-style: italic;
}

.profile-warning-section {
  max-width: 640px;
  margin-bottom: var(--space-lg);
}

.profile-warning {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-xl);
  border: 2px solid var(--color-warning, #e6a817);
  background: color-mix(in srgb, var(--color-warning, #e6a817) 8%, var(--color-washi));
}

.profile-warning-icon {
  background: var(--color-warning, #e6a817);
}

.profile-dismiss-btn {
  font-size: 0.875rem;
}

.form-section {
  max-width: 640px;
}

.usage-section {
  margin-bottom: var(--space-lg);
}

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

.zen-btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  min-width: 240px;
}

@media (max-width: 768px) {
  .cv-invitation-card {
    padding: var(--space-xl) var(--space-lg);
  }

  .cv-invitation-title {
    font-size: 1.25rem;
  }

  .cv-invitation-text {
    font-size: 0.9375rem;
  }

  .skills-warning {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .warning-text-content {
    text-align: center;
  }

  .warning-actions {
    flex-direction: column;
    align-items: center;
  }

  .profile-warning {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .zen-btn-lg {
    width: 100%;
  }
}
</style>
