<template>
  <div class="new-application-page">
    <div class="container">
      <section class="page-header animate-fade-up">
        <h1>Neue Bewerbung</h1>
        <p class="page-subtitle">Generiere ein Anschreiben aus einer Stellenanzeigen-URL</p>
      </section>

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

      <section v-if="usage" class="usage-section animate-fade-up" style="animation-delay: 150ms;">
        <UsageIndicator
          :used="usage.used"
          :limit="usage.limit"
          :unlimited="usage.unlimited"
          :plan="usage.plan"
        />
      </section>

      <section class="form-section animate-fade-up" :class="{ 'form-section--anticipation': !checkingResume && !hasResume }" style="animation-delay: 100ms;">
        <JobUrlInput
          v-model="url"
          @submit="addJob"
        />
      </section>

      <section v-if="jobs.length > 0" class="jobs-section">
        <div class="jobs-header">
          <div class="jobs-counter">
            <span class="jobs-count">{{ jobs.length }} {{ jobs.length === 1 ? 'Bewerbung' : 'Bewerbungen' }}</span>
            <span v-if="generatingCount > 0" class="status-badge status-badge--generating">
              {{ generatingCount }} in Arbeit
            </span>
            <span v-if="completedJobs.length > 0" class="status-badge status-badge--completed">
              {{ completedJobs.length }} fertig
            </span>
          </div>
          <div class="jobs-header-actions">
            <label class="auto-generate-toggle">
              <input type="checkbox" v-model="autoGenerate" />
              <span>Auto-Generierung</span>
            </label>
          </div>
        </div>
        <div v-if="extractedJobs.length >= 2 || completedJobs.length >= 2" class="batch-actions">
          <button
            v-if="extractedJobs.length >= 2"
            class="zen-btn zen-btn-ai"
            @click="generateAllJobs"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Alle generieren ({{ extractedJobs.length }})
          </button>
          <button
            v-if="completedJobs.length >= 2"
            class="zen-btn zen-btn-secondary"
            @click="downloadAllPDFs"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Alle PDFs herunterladen ({{ completedJobs.length }})
          </button>
        </div>
        <TransitionGroup name="job-list" tag="div" class="jobs-list">
          <JobCard
            v-for="job in jobs"
            :key="job.id"
            :job="job"
            :progress-message="job.progressMessage"
            @generate="generateJob(job.id)"
            @remove="removeJob(job.id)"
            @retry="retryJob(job.id)"
            @download-pdf="downloadJobPDF(job.id)"
            @download-email="downloadJobEmail(job.id)"
            @view-application="viewJobApplication(job.id)"
            @update:tone="job.tone = $event"
            @update:model="job.model = $event"
          />
        </TransitionGroup>
      </section>

      <section v-if="jobs.length === 0" class="info-section animate-fade-up" style="animation-delay: 200ms;">
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import { authStore } from '../stores/auth'
import UsageIndicator from '../components/UsageIndicator.vue'
import EnsoCircle from '../components/application/EnsoCircle.vue'
import JobUrlInput from '../components/NewApplication/JobUrlInput.vue'
import JobCard from '../components/NewApplication/JobCard.vue'

const router = useRouter()

const checkingSkills = ref(true)
const hasSkills = ref(true)
const checkingResume = ref(true)
const hasResume = ref(true)
const profileIncomplete = ref(false)

const url = ref('')
const usage = ref(null)

const jobs = ref([])
let nextJobId = 0

const JOBS_STORAGE_KEY = 'obo_jobs_pipeline'
const progressTimers = new Map()

const autoGenerate = ref(JSON.parse(localStorage.getItem('obo_auto_generate') ?? 'false'))
watch(autoGenerate, (value) => localStorage.setItem('obo_auto_generate', JSON.stringify(value)))

const extractedJobs = computed(() => jobs.value.filter(j => j.status === 'extracted'))
const completedJobs = computed(() => jobs.value.filter(j => j.status === 'completed'))
const generatingCount = computed(() => jobs.value.filter(j => j.status === 'generating').length)

function normalizeUrl(url) {
  try {
    const parsed = new URL(url)
    return (parsed.origin + parsed.pathname).replace(/\/$/, '')
  } catch {
    return url
  }
}

function saveJobsToStorage() {
  const serializable = jobs.value.map(j => ({
    id: j.id,
    url: j.url,
    status: j.status,
    quickData: j.quickData,
    editableData: j.editableData,
    tone: j.tone,
    model: j.model,
    generatedApp: j.generatedApp,
    error: j.error,
    progressMessage: null,
    thinkingText: null,
    streamedContent: null
  }))
  sessionStorage.setItem(JOBS_STORAGE_KEY, JSON.stringify(serializable))
}

function loadJobsFromStorage() {
  try {
    const raw = sessionStorage.getItem(JOBS_STORAGE_KEY)
    if (!raw) return
    const loaded = JSON.parse(raw)
    if (!Array.isArray(loaded) || loaded.length === 0) return

    for (const j of loaded) {
      if (j.status === 'extracting' || j.status === 'generating') {
        j.status = 'error'
        j.error = 'Sitzung unterbrochen. Bitte erneut versuchen.'
      }
      j.progressMessage = null
    }

    jobs.value = loaded
    nextJobId = Math.max(...loaded.map(j => j.id)) + 1
  } catch {
    // Ignore corrupt storage
  }
}

watch(jobs, saveJobsToStorage, { deep: true })

function setProgressMessageAfterDelay(jobId, message, delayMs) {
  return setTimeout(() => {
    const job = findJob(jobId)
    if (job?.status === 'generating') {
      job.progressMessage = message
    }
  }, delayMs)
}

function startProgressTimers(jobId) {
  const timers = [
    setProgressMessageAfterDelay(jobId, 'Anschreiben wird formuliert...', 3000),
    setProgressMessageAfterDelay(jobId, 'Feinschliff und Optimierung...', 8000)
  ]
  progressTimers.set(jobId, timers)
}

function clearProgressTimers(jobId) {
  const timers = progressTimers.get(jobId)
  if (timers) {
    timers.forEach(t => clearTimeout(t))
    progressTimers.delete(jobId)
  }
}

function extractApiError(e, fallbackMessage) {
  return e.response?.data?.error || fallbackMessage
}

function isAtUsageLimit() {
  if (!usage.value || usage.value.unlimited) return false
  return usage.value.used >= usage.value.limit
}

function findJob(jobId) {
  return jobs.value.find(j => j.id === jobId)
}

async function addJob(submittedUrl) {
  if (!submittedUrl) return
  if (isAtUsageLimit()) {
    if (window.$toast) {
      window.$toast('Bewerbungslimit erreicht. Bitte Abo upgraden.', 'warning')
    }
    return
  }

  const normalizedInput = normalizeUrl(submittedUrl)
  if (jobs.value.some(j => normalizeUrl(j.url) === normalizedInput)) {
    if (window.$toast) {
      window.$toast('Diese URL ist bereits in der Pipeline.', 'warning')
    }
    return
  }

  const jobId = nextJobId++
  const job = {
    id: jobId,
    url: submittedUrl,
    status: 'extracting',
    quickData: null,
    editableData: null,
    tone: 'modern',
    model: 'qwen',
    generatedApp: null,
    error: null,
    progressMessage: null,
    thinkingText: '',
    streamedContent: ''
  }

  jobs.value.unshift(job)
  url.value = ''
  await extractJob(jobId)

  if (autoGenerate.value && job.status === 'extracted') {
    generateJob(jobId)
  }
}

async function extractJob(jobId) {
  const job = findJob(jobId)
  if (!job) return

  try {
    const { data } = await api.post('/applications/quick-extract', {
      url: job.url
    })

    if (data.success) {
      job.quickData = data.data
      job.editableData = {
        company: data.data.company || '',
        title: data.data.title || '',
        location: '',
        employment_type: '',
        contact_person: '',
        contact_email: '',
        salary: '',
        description: data.data.description || ''
      }
      job.status = 'extracted'

      if (window.$toast) {
        window.$toast('Stellenanzeige erkannt!', 'success')
      }
    } else {
      job.error = data.error || 'Stellenanzeige konnte nicht gelesen werden'
      job.status = 'error'
    }
  } catch (e) {
    job.error = extractApiError(e, 'Fehler beim Laden der Stellenanzeige. Bitte versuche es erneut.')
    job.status = 'error'
  }
}

function getPayloadForJob(job) {
  return {
    url: job.url,
    tone: job.tone,
    model: job.model,
    company: job.editableData.company,
    title: job.editableData.title,
    contact_person: job.editableData.contact_person,
    contact_email: job.editableData.contact_email,
    location: job.editableData.location,
    description: job.editableData.description
  }
}

function handleGenerationSuccess(job, data) {
  job.generatedApp = data.application
  job.status = 'completed'

  loadUsage()

  if (window.$toast) {
    window.$toast('Bewerbung erfolgreich generiert!', 'success')
    if (data.profile_warning?.incomplete) {
      setTimeout(() => {
        window.$toast('Profil unvollständig — ergänze fehlende Angaben in den Einstellungen.', 'warning')
      }, 1500)
    }
  }
}

async function generateJobWithSSE(job) {
  job.thinkingText = ''
  job.streamedContent = ''
  const token = localStorage.getItem('token')
  const payload = getPayloadForJob(job)

  const response = await fetch('/api/applications/generate-from-url-stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    const errorData = await response.json()
    const err = new Error(errorData.error || 'Unbekannter Fehler')
    err.isServerError = true
    throw err
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) throw new Error('Stream ended without result')

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop()

    for (const chunk of chunks) {
      if (!chunk.startsWith('data: ')) continue

      let event
      try { event = JSON.parse(chunk.slice(6)) } catch { continue }

      if (event.type === 'complete') return event
      if (event.type === 'error') {
        const err = new Error(event.error)
        err.isServerError = true
        throw err
      }
      if (event.type === 'thinking') {
        job.thinkingText += event.text
        continue
      }
      if (event.type === 'thinking_done') {
        job.progressMessage = 'Anschreiben wird finalisiert...'
        continue
      }
      if (event.type === 'content') {
        if (!job.streamedContent) job.streamedContent = ''
        job.streamedContent += event.text
        job.progressMessage = 'Anschreiben wird geschrieben...'
        continue
      }
      if (event.step && event.message) {
        job.progressMessage = `${event.step}/${event.total_steps}: ${event.message}`
      }
    }
  }
}

async function generateJobFallback(job) {
  const payload = getPayloadForJob(job)
  startProgressTimers(job.id)

  try {
    const { data } = await api.post('/applications/generate-from-url', payload)
    if (!data.success) {
      throw new Error(data.error || 'Unbekannter Fehler')
    }
    return data
  } finally {
    clearProgressTimers(job.id)
  }
}

async function generateJob(jobId) {
  const job = findJob(jobId)
  if (!job?.editableData) return

  if (isAtUsageLimit()) {
    job.error = 'Bewerbungslimit erreicht. Bitte Abo upgraden.'
    job.status = 'error'
    return
  }

  job.status = 'generating'
  job.error = null
  job.progressMessage = 'Stellenanzeige wird analysiert...'

  try {
    const data = await generateJobWithSSE(job)
    job.progressMessage = null
    handleGenerationSuccess(job, data)
  } catch (sseError) {
    // Server-reported errors (validation, generation failures) should not trigger fallback
    if (sseError.isServerError) {
      job.progressMessage = null
      job.error = sseError.message
      job.status = 'error'
      return
    }

    // Network/stream failures: fall back to the non-streaming endpoint
    try {
      job.progressMessage = 'Stellenanzeige wird analysiert...'
      const data = await generateJobFallback(job)
      job.progressMessage = null
      handleGenerationSuccess(job, data)
    } catch (fallbackError) {
      clearProgressTimers(jobId)
      job.progressMessage = null
      job.error = extractApiError(fallbackError, 'Fehler bei der Generierung. Bitte versuche es erneut.')
      job.status = 'error'
    }
  }
}

function removeJob(jobId) {
  jobs.value = jobs.value.filter(j => j.id !== jobId)
}

function retryJob(jobId) {
  const job = findJob(jobId)
  if (!job) return

  job.error = null
  job.status = 'extracting'
  job.quickData = null
  job.editableData = null
  job.generatedApp = null

  extractJob(jobId)
}

function downloadBlob(blobData, mimeType, filename) {
  const blob = new Blob([blobData], { type: mimeType })
  const objectUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(objectUrl)
}

async function downloadJobPDF(jobId) {
  const job = findJob(jobId)
  if (!job?.generatedApp?.id) return

  try {
    const response = await api.get(`/applications/${job.generatedApp.id}/pdf`, {
      responseType: 'blob'
    })
    const disposition = response.headers['content-disposition']
    const match = disposition?.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/)
    const filename = match
      ? decodeURIComponent(match[1])
      : `Anschreiben_${job.generatedApp.firma || job.generatedApp.id}.pdf`
    downloadBlob(response.data, 'application/pdf', filename)
  } catch (_err) {
    if (window.$toast) {
      window.$toast('Fehler beim Herunterladen des PDF', 'error')
    }
  }
}

function resolveTemplateVars(text, app) {
  if (!text) return ''
  return text
    .replace(/\{\{FIRMA\}\}/g, app.firma || '')
    .replace(/\{\{POSITION\}\}/g, app.position || '')
    .replace(/\{\{ANSPRECHPARTNER\}\}/g, app.ansprechpartner || '')
    .replace(/\{\{QUELLE\}\}/g, app.quelle || '')
}

function downloadJobEmail(jobId) {
  const job = findJob(jobId)
  if (!job?.generatedApp) return

  const app = job.generatedApp
  const to = app.email || ''
  const subject = resolveTemplateVars(app.betreff || '', app)
  const body = resolveTemplateVars(app.email_text || '', app)

  const params = new URLSearchParams()
  if (subject) params.set('subject', subject)
  if (body) params.set('body', body)

  const query = params.toString()
  window.location.href = `mailto:${encodeURIComponent(to)}${query ? '?' + query : ''}`
}

function viewJobApplication(jobId) {
  const job = findJob(jobId)
  if (!job?.generatedApp?.id) return
  router.push('/applications')
}

function generateAllJobs() {
  extractedJobs.value.forEach(j => generateJob(j.id))
}

async function downloadAllPDFs() {
  for (const job of completedJobs.value) {
    await downloadJobPDF(job.id)
    await new Promise(r => setTimeout(r, 500))
  }
}

async function loadUsage() {
  try {
    const { data } = await api.get('/stats')
    usage.value = data.usage
  } catch (e) {
    console.error('Fehler beim Laden der Nutzung:', e)
  }
}

async function checkUserSkills() {
  checkingSkills.value = true
  try {
    const { data } = await api.get('/users/me/skills')
    hasSkills.value = (data.skills || []).length > 0
  } catch {
    hasSkills.value = true
  } finally {
    checkingSkills.value = false
  }
}

async function checkUserResume() {
  checkingResume.value = true
  try {
    const { data } = await api.get('/documents')
    hasResume.value = (data.documents || []).some(doc => doc.doc_type === 'lebenslauf')
  } catch {
    hasResume.value = true
  } finally {
    checkingResume.value = false
  }
}

function checkProfileCompleteness() {
  const user = authStore.user
  if (!user) return
  const requiredFields = ['full_name', 'phone', 'address', 'city', 'postal_code']
  profileIncomplete.value = requiredFields.some(f => !user[f])
}

function dismissProfileWarning() {
  profileIncomplete.value = false
}

onMounted(() => {
  loadJobsFromStorage()
  loadUsage()
  checkUserSkills()
  checkUserResume()
  checkProfileCompleteness()
})

onBeforeUnmount(() => {
  progressTimers.forEach((timers) => timers.forEach(t => clearTimeout(t)))
  progressTimers.clear()
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
  margin-bottom: var(--space-xl);
}

.usage-section {
  margin-bottom: var(--space-lg);
}

.jobs-section {
  max-width: 640px;
  margin-bottom: var(--space-xl);
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.job-list-enter-active {
  transition: all 0.3s ease-out;
}

.job-list-leave-active {
  transition: all 0.2s ease-in;
}

.job-list-enter-from {
  opacity: 0;
  transform: translateY(-12px);
}

.job-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.job-list-move {
  transition: transform 0.3s ease;
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

/* Jobs header with counter + actions */
.jobs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.jobs-counter {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.jobs-count {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-sumi);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-sm);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.5;
}

.status-badge--generating {
  background: hsla(217, 91%, 60%, 0.12);
  color: var(--color-ai, hsl(217, 91%, 60%));
}

.status-badge--completed {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke, #7a8b6e);
}

.jobs-header-actions {
  display: flex;
  align-items: center;
}

.auto-generate-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
}

.auto-generate-toggle input[type="checkbox"] {
  accent-color: var(--color-ai, hsl(217, 91%, 60%));
  width: 15px;
  height: 15px;
  cursor: pointer;
}

/* Batch action buttons */
.batch-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.batch-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
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

  .jobs-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .batch-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .batch-actions .zen-btn {
    justify-content: center;
    width: 100%;
  }
}
</style>
