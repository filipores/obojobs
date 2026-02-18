<template>
  <Teleport to="body">
    <div v-if="selectedApp" class="modal-overlay" @click="$emit('close')">
      <div class="modal zen-card animate-fade-up" @click.stop>
        <div class="modal-header">
          <div>
            <h2>{{ selectedApp.firma }}</h2>
            <p class="modal-subtitle">{{ selectedApp.position }}</p>
          </div>
          <button @click="$emit('close')" class="modal-close">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-content">
          <!-- Status -->
          <div class="detail-group detail-group-highlight">
            <label class="detail-label">{{ t('applications.status') }}</label>
            <select :value="selectedApp.status" @change="$emit('update-status', { ...selectedApp, status: $event.target.value })" class="form-select">
              <option value="erstellt">{{ t('applications.statusCreated') }}</option>
              <option value="versendet">{{ t('applications.statusSent') }}</option>
              <option value="antwort_erhalten">{{ t('applications.statusResponseReceived') }}</option>
              <option value="absage">{{ t('applications.statusRejection') }}</option>
              <option value="zusage">{{ t('applications.statusAcceptance') }}</option>
            </select>
          </div>

          <!-- Info Grid -->
          <div class="info-grid">
            <div class="detail-group">
              <label class="detail-label">{{ t('applications.companyLabel') }}</label>
              <p class="detail-value">{{ selectedApp.firma }}</p>
            </div>

            <div v-if="selectedApp.position" class="detail-group">
              <label class="detail-label">{{ t('applications.position') }}</label>
              <p class="detail-value">{{ selectedApp.position }}</p>
            </div>

            <div v-if="selectedApp.ansprechpartner" class="detail-group">
              <label class="detail-label">{{ t('applications.contactPerson') }}</label>
              <p class="detail-value">{{ selectedApp.ansprechpartner }}</p>
            </div>

            <div v-if="selectedApp.email" class="detail-group">
              <label class="detail-label">{{ t('applications.email') }}</label>
              <p class="detail-value">
                <a :href="`mailto:${selectedApp.email}`" class="detail-link">{{ selectedApp.email }}</a>
              </p>
            </div>

            <div v-if="selectedApp.quelle || selectedApp.job_url" class="detail-group">
              <label class="detail-label">{{ t('applications.source') }}</label>
              <p class="detail-value">
                <a v-if="selectedApp.job_url" :href="selectedApp.job_url" target="_blank" class="detail-link">{{ selectedApp.quelle || getDomain(selectedApp.job_url) }}</a>
                <span v-else>{{ selectedApp.quelle }}</span>
              </p>
            </div>

            <div class="detail-group">
              <label class="detail-label">{{ t('applications.date') }}</label>
              <p class="detail-value">{{ formatDateTime(selectedApp.datum) }}</p>
            </div>
          </div>

          <!-- Sent Info -->
          <div v-if="selectedApp.sent_at" class="detail-group detail-group-sent">
            <label class="detail-label">{{ t('applications.sentLabel') }}</label>
            <p class="detail-value">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sent-icon">
                <path d="M22 2L11 13"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
              </svg>
              {{ formatDateTime(selectedApp.sent_at) }} via {{ getSentViaLabel(selectedApp.sent_via) }}
            </p>
          </div>

          <!-- Betreff -->
          <div v-if="selectedApp.betreff" class="detail-group">
            <label class="detail-label">{{ t('applications.subject') }}</label>
            <p class="detail-value detail-value-block">{{ selectedApp.betreff }}</p>
          </div>

          <!-- Notes -->
          <div class="detail-group">
            <label class="detail-label">{{ t('applications.notes') }}</label>
            <textarea
              :value="selectedApp.notizen"
              @input="$emit('update-notes', { ...selectedApp, notizen: $event.target.value })"
              @blur="$emit('update-notes', { ...selectedApp, notizen: $event.target.value })"
              :placeholder="t('applications.notesPlaceholder')"
              rows="4"
              class="form-textarea"
            ></textarea>
          </div>

          <!-- Interview Tracking Section -->
          <div class="detail-group">
            <label class="detail-label">{{ t('applications.interviewTracking') }}</label>
            <InterviewTracker
              :application-id="selectedApp.id"
              :initial-date="selectedApp.interview_date"
              :initial-result="selectedApp.interview_result"
              :initial-feedback="selectedApp.interview_feedback"
              @updated="$emit('interview-updated', $event)"
            />
          </div>

          <!-- ATS Optimizer Section -->
          <div class="detail-group">
            <label class="detail-label">{{ t('applications.atsOptimization') }}</label>
            <ATSOptimizer
              v-if="selectedApp.id"
              :application-id="selectedApp.id"
              @optimized="$emit('ats-optimized', $event)"
            />
          </div>

          <!-- Gap Analysis / Learning Recommendations Section -->
          <div class="detail-group">
            <label class="detail-label">{{ t('applications.skillGapsAndRecommendations') }}</label>
            <div v-if="jobFitLoading" class="gap-loading-state">
              <div class="loading-spinner"></div>
              <span>{{ t('applications.loadingSkillAnalysis') }}</span>
            </div>
            <GapAnalysis
              v-else-if="jobFitData"
              :recommendations="jobFitData.learning_recommendations || []"
              :missing-skills="jobFitData.missing_skills || []"
              :partial-matches="jobFitData.partial_matches || []"
              :loading="false"
            />
            <div v-else class="gap-empty-state">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <div>
                <strong>{{ t('applications.noSkillAnalysis') }}</strong>
                <p>{{ t('applications.analyzeRequirementsFirst') }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <router-link
            :to="`/applications/${selectedApp.id}/interview`"
            class="zen-btn zen-btn-interview"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            {{ t('applications.interviewPrep') }}
          </router-link>
          <div class="email-split-btn">
            <button @click="openInEmailClient" class="zen-btn zen-btn-ai">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              {{ t('applications.openInEmailClient') }}
            </button>
            <div class="email-dropdown-wrapper">
              <button @click.stop="emlDropdownOpen = !emlDropdownOpen" class="zen-btn zen-btn-ai email-dropdown-toggle">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
              <div v-if="emlDropdownOpen" class="email-dropdown" @click="emlDropdownOpen = false">
                <button @click="$emit('download-email-draft', selectedApp)" class="email-dropdown-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  {{ t('applications.downloadEml') }}
                </button>
              </div>
            </div>
          </div>
          <button @click="$emit('download-pdf', selectedApp.id)" class="zen-btn">
            {{ t('applications.downloadPdf') }}
          </button>
          <button @click="$emit('delete', selectedApp.id)" class="zen-btn zen-btn-danger" :aria-label="t('applications.deleteApplication')" :title="t('applications.deleteApplication')">
            {{ t('common.delete') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import ATSOptimizer from '../ATSOptimizer.vue'
import GapAnalysis from '../GapAnalysis.vue'
import InterviewTracker from '../InterviewTracker.vue'
import { getFullLocale } from '../../i18n'

const { t } = useI18n()
const emlDropdownOpen = ref(false)

const props = defineProps({
  selectedApp: { type: Object, default: null },
  jobFitData: { type: Object, default: null },
  jobFitLoading: { type: Boolean, default: false }
})

defineEmits([
  'close',
  'update-status',
  'update-notes',
  'download-pdf',
  'download-email-draft',
  'delete',
  'interview-updated',
  'ats-optimized'
])

const resolveTemplateVars = (text, app) => {
  if (!text) return ''
  return text
    .replace(/\{\{FIRMA\}\}/g, app.firma || '')
    .replace(/\{\{POSITION\}\}/g, app.position || '')
    .replace(/\{\{ANSPRECHPARTNER\}\}/g, app.ansprechpartner || '')
    .replace(/\{\{QUELLE\}\}/g, app.quelle || '')
}

const openInEmailClient = () => {
  const app = props.selectedApp
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

const closeDropdown = (e) => {
  if (!e.target.closest('.email-split-btn')) {
    emlDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

const formatDateTime = (date) => {
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

const getSentViaLabel = (provider) => {
  const labels = {
    'gmail': 'Gmail',
    'outlook': 'Outlook'
  }
  return labels[provider] || provider
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(44, 44, 44, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
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

.detail-group-sent {
  padding: var(--space-md);
  background: rgba(122, 139, 110, 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-koke);
}

.detail-group-sent .detail-value {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-koke);
  font-weight: 500;
}

.sent-icon {
  flex-shrink: 0;
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
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-washi);
}

.modal-footer .zen-btn,
.modal-footer .zen-btn-interview {
  flex: 1 1 auto;
  min-width: 140px;
  white-space: nowrap;
}

.modal-footer .zen-btn-danger {
  flex: 0 1 auto;
}

.modal-footer .zen-btn svg {
  margin-right: var(--space-xs);
  vertical-align: middle;
}

/* Email split button */
.email-split-btn {
  display: inline-flex;
  position: relative;
  flex: 1 1 auto;
  min-width: 140px;
}

.email-split-btn > .zen-btn {
  flex: 1;
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

.zen-btn-interview {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: rgba(138, 79, 125, 0.1);
  border-color: rgba(138, 79, 125, 0.3);
  color: #8a4f7d;
  text-decoration: none;
}

.zen-btn-interview:hover {
  background: rgba(138, 79, 125, 0.2);
  border-color: #8a4f7d;
}

.gap-loading-state {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-secondary);
}

.gap-loading-state .loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.gap-empty-state {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-washi-aged);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.gap-empty-state svg {
  flex-shrink: 0;
  color: var(--color-ai);
  opacity: 0.7;
}

.gap-empty-state strong {
  display: block;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
  font-size: 0.9375rem;
}

.gap-empty-state p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }
}
</style>
