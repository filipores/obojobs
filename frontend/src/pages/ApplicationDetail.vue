<template>
  <div class="application-detail-page">
    <div class="container">
      <!-- Back link -->
      <router-link to="/applications" class="back-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        {{ t('applicationDetail.backToApplications') }}
      </router-link>

      <!-- Loading Skeleton -->
      <div v-if="loading" class="detail-skeleton">
        <div class="skeleton-header">
          <div>
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-subtitle"></div>
          </div>
          <div class="skeleton skeleton-badge"></div>
        </div>
        <div class="skeleton-tabs">
          <div class="skeleton skeleton-tab" v-for="i in 3" :key="i"></div>
        </div>
        <div class="skeleton skeleton-card-lg"></div>
        <div class="skeleton skeleton-card-md"></div>
      </div>

      <!-- Content -->
      <template v-else-if="application">
        <!-- Header -->
        <section class="detail-header animate-fade-up">
          <div class="detail-header-content">
            <div class="detail-header-info">
              <h1>{{ application.firma }}</h1>
              <p class="detail-position">{{ application.position || t('applicationDetail.positionNotSpecified') }}</p>
            </div>
            <div class="header-actions">
              <StatusBadge :status="application.status" />
              <button @click="downloadPDF" class="zen-btn zen-btn-sm">PDF</button>
            </div>
          </div>
        </section>

        <!-- Tabs -->
        <nav class="detail-tabs animate-fade-up" style="animation-delay: 50ms;">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="detail-tab"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>

        <!-- Tab Content -->
        <section class="tab-content animate-fade-up" style="animation-delay: 100ms;">
          <!-- Overview Tab -->
          <div v-if="activeTab === 'overview'" class="tab-overview">
            <!-- Status Change -->
            <div class="detail-card zen-card">
              <h3>{{ t('applicationDetail.status') }}</h3>
              <div class="status-select-wrapper">
                <select v-model="application.status" @change="updateStatus" class="form-select">
                  <option value="erstellt">{{ t('applications.statusCreated') }}</option>
                  <option value="versendet">{{ t('applications.statusSent') }}</option>
                  <option value="antwort_erhalten">{{ t('applications.statusResponseReceived') }}</option>
                  <option value="interview">Interview</option>
                  <option value="absage">{{ t('applications.statusRejection') }}</option>
                  <option value="zusage">{{ t('applications.statusAcceptance') }}</option>
                </select>
              </div>
            </div>

            <!-- Info Grid -->
            <div class="detail-card zen-card">
              <h3>{{ t('applicationDetail.details') }}</h3>
              <div class="info-grid">
                <div class="info-item">
                  <label>{{ t('applications.companyLabel') }}</label>
                  <p>{{ application.firma }}</p>
                </div>
                <div v-if="application.position" class="info-item">
                  <label>{{ t('applications.position') }}</label>
                  <p>{{ application.position }}</p>
                </div>
                <div v-if="application.ansprechpartner" class="info-item">
                  <label>{{ t('applications.contactPerson') }}</label>
                  <p>{{ application.ansprechpartner }}</p>
                </div>
                <div v-if="application.email" class="info-item">
                  <label>{{ t('applications.email') }}</label>
                  <a :href="`mailto:${application.email}`">{{ application.email }}</a>
                </div>
                <div v-if="application.quelle || application.job_url" class="info-item">
                  <label>{{ t('applicationDetail.source') }}</label>
                  <a v-if="application.job_url" :href="application.job_url" target="_blank" rel="noopener noreferrer">{{ application.quelle || getDomain(application.job_url) }}</a>
                  <p v-else>{{ application.quelle }}</p>
                </div>
                <div class="info-item">
                  <label>{{ t('applicationDetail.created') }}</label>
                  <p>{{ formatDate(application.datum) }}</p>
                </div>
              </div>
            </div>

            <!-- Sent Info -->
            <div v-if="application.sent_at" class="detail-card zen-card detail-card-sent">
              <h3>{{ t('applicationDetail.sentLabel') }}</h3>
              <div class="sent-info">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 2L11 13"/>
                  <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
                </svg>
                <span>{{ formatDateTime(application.sent_at) }}</span>
              </div>
            </div>

            <!-- Betreff -->
            <div v-if="application.betreff" class="detail-card zen-card">
              <h3>{{ t('applicationDetail.subject') }}</h3>
              <p class="betreff-text">{{ application.betreff }}</p>
            </div>

            <!-- Notes -->
            <div class="detail-card zen-card">
              <h3>{{ t('applicationDetail.notes') }}</h3>
              <textarea
                v-model="application.notizen"
                @blur="updateNotes"
                :placeholder="t('applicationDetail.notesPlaceholder')"
                rows="4"
                class="form-textarea"
              ></textarea>
            </div>

            <!-- Job Fit Score -->
            <div v-if="jobFitData" class="detail-card zen-card">
              <h3>{{ t('applicationDetail.jobFitScore') }}</h3>
              <div class="fit-score-display">
                <div class="fit-score-value" :class="getFitCategory(jobFitData.score)">
                  {{ jobFitData.score }}%
                </div>
                <div v-if="jobFitData.recommendations?.length" class="fit-recommendations">
                  <h4>{{ t('applicationDetail.recommendations') }}</h4>
                  <ul>
                    <li v-for="rec in jobFitData.recommendations" :key="rec">{{ rec }}</li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- Gap Analysis -->
            <div v-if="jobFitData" class="detail-card zen-card">
              <h3>{{ t('applicationDetail.skillGaps') }}</h3>
              <GapAnalysis
                :recommendations="jobFitData.learning_recommendations || []"
                :missing-skills="jobFitData.missing_skills || []"
                :partial-matches="jobFitData.partial_matches || []"
                :loading="false"
              />
            </div>

            <!-- Actions -->
            <div class="detail-card zen-card detail-card-actions">
              <div class="email-split-btn">
                <button @click="openInEmailClient" class="zen-btn zen-btn-sm zen-btn-ai">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                  {{ t('applicationDetail.openInEmailClient') }}
                </button>
                <div class="email-dropdown-wrapper">
                  <button @click="emailDropdownOpen = !emailDropdownOpen" class="zen-btn zen-btn-sm zen-btn-ai email-dropdown-toggle" :aria-label="t('applicationDetail.moreEmailOptions')">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                  <div v-if="emailDropdownOpen" class="email-dropdown" @click="emailDropdownOpen = false">
                    <button @click="downloadEmailDraft" class="email-dropdown-item">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                      </svg>
                      {{ t('applicationDetail.downloadEml') }}
                    </button>
                  </div>
                </div>
              </div>
              <button @click="confirmDelete" class="zen-btn zen-btn-sm zen-btn-danger">
                {{ t('common.delete') }}
              </button>
            </div>
          </div>

          <!-- ATS Tab -->
          <div v-if="activeTab === 'ats'" class="tab-ats">
            <div class="detail-card zen-card">
              <h3>{{ t('applicationDetail.atsOptimization') }}</h3>
              <p class="tab-description">{{ t('applicationDetail.atsDescription') }}</p>
              <ATSOptimizer
                v-if="application.id"
                :application-id="application.id"
                @optimized="onATSOptimized"
              />
            </div>
          </div>

          <!-- Interview Tab -->
          <div v-if="activeTab === 'interview'" class="tab-interview">
            <!-- Interview Tracker -->
            <div class="detail-card zen-card">
              <h3>{{ t('applicationDetail.interviewTracking') }}</h3>
              <InterviewTracker
                :application-id="application.id"
                :initial-date="application.interview_date"
                :initial-result="application.interview_result"
                :initial-feedback="application.interview_feedback"
                @updated="onInterviewUpdated"
              />
            </div>

            <!-- Interview Actions -->
            <div class="detail-card zen-card">
              <h3>{{ t('applicationDetail.interviewPrep') }}</h3>
              <p class="tab-description">{{ t('applicationDetail.interviewDescription') }}</p>

              <!-- Interview Date -->
              <div v-if="application.interview_date" class="interview-date-info">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                <span>{{ formatDate(application.interview_date) }}</span>
              </div>

              <div class="interview-actions">
                <router-link
                  :to="`/applications/${application.id}/interview`"
                  class="zen-btn zen-btn-ai"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                  {{ t('applicationDetail.startInterviewPrep') }}
                </router-link>
                <router-link
                  :to="`/applications/${application.id}/mock-interview`"
                  class="zen-btn"
                >
                  {{ t('applicationDetail.mockInterview') }}
                </router-link>
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api/client'
import { confirm } from '../composables/useConfirm'
import { getFullLocale } from '../i18n'
import StatusBadge from '../components/Applications/StatusBadge.vue'
import ATSOptimizer from '../components/ATSOptimizer.vue'
import GapAnalysis from '../components/GapAnalysis.vue'
import InterviewTracker from '../components/InterviewTracker.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const application = ref(null)
const loading = ref(true)
const activeTab = ref('overview')
const jobFitData = ref(null)
const emailDropdownOpen = ref(false)

const tabs = computed(() => [
  { id: 'overview', label: t('applicationDetail.tabOverview') },
  { id: 'ats', label: t('applicationDetail.tabATS') },
  { id: 'interview', label: t('applicationDetail.tabInterview') }
])

// --- Data loading ---

const loadApplication = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/applications/${route.params.id}`)
    application.value = data.application || data
  } catch (err) {
    console.error('Fehler beim Laden:', err)
    router.push('/applications')
  } finally {
    loading.value = false
  }
}

const loadJobFitData = async () => {
  try {
    const { data } = await api.silent.get(`/applications/${route.params.id}/job-fit?include_recommendations=true`)
    if (data.success) {
      jobFitData.value = data.job_fit
    }
  } catch {
    // Optional data - silently fail
  }
}

// --- Helpers ---

const formatDate = (date) => {
  if (!date) return '\u2013'
  return new Date(date).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatDateTime = (date) => {
  if (!date) return '\u2013'
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
    return new URL(url).hostname.replace('www.', '')
  } catch {
    return url
  }
}

const getFitCategory = (score) => {
  if (score >= 80) return 'fit-excellent'
  if (score >= 60) return 'fit-good'
  if (score >= 40) return 'fit-medium'
  return 'fit-low'
}

function triggerBlobDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// --- Actions ---

const updateStatus = async () => {
  try {
    await api.put(`/applications/${application.value.id}`, {
      status: application.value.status
    })
    if (window.$toast) {
      window.$toast(t('applications.statusChangedSuccess'), 'success')
    }
  } catch {
    if (window.$toast) {
      window.$toast(t('applications.statusChangeError'), 'error')
    }
  }
}

const updateNotes = async () => {
  try {
    await api.put(`/applications/${application.value.id}`, {
      notizen: application.value.notizen
    })
  } catch {
    if (window.$toast) {
      window.$toast(t('applications.noteSaveError'), 'error')
    }
  }
}

const downloadPDF = async () => {
  try {
    const response = await api.get(`/applications/${application.value.id}/pdf`, {
      responseType: 'blob'
    })
    const disposition = response.headers['content-disposition']
    const match = disposition?.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/)
    const filename = match ? decodeURIComponent(match[1]) : `Anschreiben_${application.value.id}.pdf`
    triggerBlobDownload(new Blob([response.data], { type: 'application/pdf' }), filename)
  } catch {
    if (window.$toast) {
      window.$toast(t('applications.pdfDownloadError'), 'error')
    }
  }
}

const resolveTemplateVars = (text, app) => {
  if (!text) return ''
  return text
    .replace(/\{\{FIRMA\}\}/g, app.firma || '')
    .replace(/\{\{POSITION\}\}/g, app.position || '')
    .replace(/\{\{ANSPRECHPARTNER\}\}/g, app.ansprechpartner || '')
    .replace(/\{\{QUELLE\}\}/g, app.quelle || '')
}

const openInEmailClient = () => {
  const app = application.value
  if (!app) return

  const to = app.email || ''
  const subject = resolveTemplateVars(app.betreff || '', app)
  const body = resolveTemplateVars(app.email_text || '', app)

  const params = new URLSearchParams()
  if (subject) params.set('subject', subject)
  if (body) params.set('body', body)

  const query = params.toString()
  window.location.href = `mailto:${encodeURIComponent(to)}${query ? '?' + query : ''}`
}

const downloadEmailDraft = async () => {
  try {
    const response = await api.get(`/applications/${application.value.id}/email-draft`, {
      responseType: 'blob'
    })
    const firma = application.value.firma || 'Bewerbung'
    triggerBlobDownload(new Blob([response.data], { type: 'message/rfc822' }), `Bewerbung_${firma}.eml`)
    if (window.$toast) {
      window.$toast(t('applications.emlDownloaded'), 'success', 6000)
    }
  } catch {
    if (window.$toast) {
      window.$toast(t('applications.emailDraftError'), 'error')
    }
  }
}

const confirmDelete = async () => {
  const confirmed = await confirm({
    title: t('applications.deleteConfirmTitle'),
    message: t('applications.deleteConfirmMessage'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/applications/${application.value.id}`)
    if (window.$toast) {
      window.$toast(t('applicationDetail.deleted'), 'success')
    }
    router.push('/applications')
  } catch {
    if (window.$toast) {
      window.$toast(t('applications.deleteError'), 'error')
    }
  }
}

const onATSOptimized = (data) => {
  if (application.value && data.optimized_text) {
    application.value.email_text = data.optimized_text
  }
}

const onInterviewUpdated = (updatedApp) => {
  if (application.value) {
    application.value.interview_date = updatedApp.interview_date
    application.value.interview_result = updatedApp.interview_result
    application.value.interview_feedback = updatedApp.interview_feedback
  }
}

// --- Lifecycle ---

const closeDropdown = (e) => {
  if (!e.target.closest('.email-split-btn')) {
    emailDropdownOpen.value = false
  }
}

onMounted(() => {
  loadApplication()
  loadJobFitData()
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})
</script>

<style scoped>
.application-detail-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

/* Back link */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-text-tertiary);
  text-decoration: none;
  font-size: 0.875rem;
  padding: var(--space-lg) 0;
  transition: color var(--transition-base);
}

.back-link:hover {
  color: var(--color-ai);
}

/* Header */
.detail-header {
  padding: var(--space-lg) 0 var(--space-ma);
}

.detail-header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
}

.detail-header-info {
  min-width: 0;
  flex: 1;
}

.detail-header h1 {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-xs);
  word-break: break-word;
}

.detail-position {
  color: var(--color-text-secondary);
  font-size: 1.125rem;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-shrink: 0;
}

/* Tabs */
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-ma);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.detail-tabs::-webkit-scrollbar {
  display: none;
}

.detail-tab {
  padding: var(--space-md) var(--space-lg);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
}

.detail-tab:hover {
  color: var(--color-text-primary);
}

.detail-tab.active {
  color: var(--color-ai);
  border-bottom-color: var(--color-ai);
}

/* Tab content */
.tab-content {
  padding-bottom: var(--space-ma);
}

.tab-description {
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-lg);
}

/* Cards */
.detail-card {
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.detail-card h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-md);
  color: var(--color-sumi);
}

.detail-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  align-items: center;
}

.detail-card-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.detail-card-sent {
  border-left: 3px solid var(--color-koke);
}

.sent-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-koke);
  font-weight: 500;
}

.betreff-text {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
  margin: 0;
  color: var(--color-sumi);
}

/* Status select */
.status-select-wrapper {
  max-width: 280px;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.info-item label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.info-item p {
  font-size: 1rem;
  color: var(--color-sumi);
  margin: 0;
}

.info-item a {
  font-size: 1rem;
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.info-item a:hover {
  text-decoration: underline;
}

/* Job Fit Score */
.fit-score-display {
  display: flex;
  align-items: flex-start;
  gap: var(--space-lg);
}

.fit-score-value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 600;
  line-height: 1;
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.fit-excellent {
  background-color: var(--color-success-muted, #dcfce7);
  color: var(--color-success, #16a34a);
}

.fit-good {
  background-color: var(--color-ai-muted, #dbeafe);
  color: var(--color-ai, #2563eb);
}

.fit-medium {
  background-color: var(--color-warning-muted, #fef3c7);
  color: var(--color-warning, #d97706);
}

.fit-low {
  background-color: var(--color-error-muted, #fee2e2);
  color: var(--color-error, #dc2626);
}

.fit-recommendations {
  flex: 1;
}

.fit-recommendations h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.fit-recommendations ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.fit-recommendations li {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-xs);
}

/* Interview Tab */
.interview-date-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  color: var(--color-ai);
  font-weight: 500;
}

.interview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.interview-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

/* Loading Skeleton */
.detail-skeleton {
  padding: var(--space-ma) 0;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-ma);
}

.skeleton-title {
  width: 260px;
  height: 2rem;
  margin-bottom: var(--space-sm);
}

.skeleton-subtitle {
  width: 180px;
  height: 1.125rem;
}

.skeleton-badge {
  width: 80px;
  height: 1.75rem;
  border-radius: var(--radius-sm);
}

.skeleton-tabs {
  display: flex;
  gap: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
  padding-bottom: var(--space-md);
  margin-bottom: var(--space-ma);
}

.skeleton-tab {
  width: 80px;
  height: 1.125rem;
}

.skeleton-card-lg {
  width: 100%;
  height: 200px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.skeleton-card-md {
  width: 100%;
  height: 140px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
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

/* Email split button */
.email-split-btn {
  display: inline-flex;
  position: relative;
}

.email-split-btn > .zen-btn {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.email-dropdown-wrapper {
  position: relative;
}

.email-dropdown-toggle {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  padding-left: var(--space-sm);
  padding-right: var(--space-sm);
  min-width: unset;
}

.email-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--space-xs);
  background: var(--color-bg-elevated, #fff);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  min-width: 220px;
  overflow: hidden;
}

.email-dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: none;
  border: none;
  color: var(--color-sumi);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background var(--transition-base);
  white-space: nowrap;
}

.email-dropdown-item:hover {
  background: var(--color-washi);
}

/* Responsive */
@media (max-width: 768px) {
  .detail-header-content {
    flex-direction: column;
    gap: var(--space-md);
  }

  .header-actions {
    justify-content: flex-start;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .fit-score-display {
    flex-direction: column;
  }

  .detail-card-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .detail-card-actions .zen-btn {
    justify-content: center;
  }

  .interview-actions {
    flex-direction: column;
  }

  .interview-actions .zen-btn {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .detail-header h1 {
    font-size: 1.5rem;
  }

  .detail-tab {
    padding: var(--space-sm) var(--space-md);
    font-size: 0.875rem;
  }
}
</style>
