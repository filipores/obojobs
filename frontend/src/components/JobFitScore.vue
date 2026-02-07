<template>
  <div class="job-fit-score">
    <!-- Loading State -->
    <div v-if="loading" class="job-fit-loading" role="status" aria-live="polite">
      <div class="loading-spinner" aria-hidden="true"></div>
      <span>Analysiere Job-Fit...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="errorState.message" class="job-fit-error" :class="{ 'error-temporary': errorState.isTemporary }">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div class="error-content">
        <span class="error-message">{{ errorState.message }}</span>
        <p v-if="errorState.hint" class="error-hint">{{ errorState.hint }}</p>
        <div class="error-actions">
          <!-- Retry Button for temporary errors -->
          <button
            v-if="errorState.isTemporary"
            @click="loadJobFitScore"
            class="zen-btn zen-btn-sm retry-btn"
            :disabled="loading"
            aria-label="Erneut versuchen - Job-Fit Score neu laden"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M8 16H3v5"/>
            </svg>
            Erneut versuchen
          </button>
          <!-- Contact link for persistent errors -->
          <a
            v-if="errorState.showContactLink"
            href="mailto:kontakt@obojobs.de"
            class="contact-link"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            Support kontaktieren
          </a>
        </div>
      </div>
    </div>

    <!-- No Skills Warning -->
    <div v-else-if="!hasUserSkills" class="job-fit-no-skills">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      <div>
        <strong>Keine Skills gefunden</strong>
        <p>Laden Sie einen Lebenslauf hoch oder fügen Sie Skills manuell hinzu, um den Job-Fit Score zu berechnen.</p>
        <router-link to="/documents#skills" class="zen-btn zen-btn-sm">
          Skills hinzufügen
        </router-link>
      </div>
    </div>

    <!-- Score Display -->
    <div v-else-if="jobFitData" class="job-fit-content">
      <!-- Score Header -->
      <div class="score-header">
        <h3>Job-Fit Score</h3>
        <div :class="['score-badge', `score-${jobFitData.score_category}`]">
          {{ jobFitData.score_label }}
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="score-progress">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :class="`fill-${jobFitData.score_category}`"
            :style="{ width: `${jobFitData.overall_score}%` }"
          ></div>
        </div>
        <div class="score-value">{{ jobFitData.overall_score }}%</div>
      </div>

      <!-- Score Breakdown -->
      <div class="score-breakdown">
        <div class="breakdown-item">
          <span class="breakdown-label">Must-Have Anforderungen</span>
          <span class="breakdown-value">
            {{ jobFitData.summary.matched_must_have }}/{{ jobFitData.summary.total_must_have }}
            <span class="breakdown-percent">({{ jobFitData.must_have_score }}%)</span>
          </span>
        </div>
        <div class="breakdown-item">
          <span class="breakdown-label">Nice-to-Have Anforderungen</span>
          <span class="breakdown-value">
            {{ jobFitData.summary.matched_nice_to_have }}/{{ jobFitData.summary.total_nice_to_have }}
            <span class="breakdown-percent">({{ jobFitData.nice_to_have_score }}%)</span>
          </span>
        </div>
      </div>

      <!-- Low Score Warning -->
      <div v-if="jobFitData.overall_score < 40" class="low-score-warning">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <div>
          <strong>Niedriger Job-Fit Score</strong>
          <p>Diese Stelle passt moeglicherweise nicht zu Ihrem Profil. Ueberlegen Sie, ob sich eine Bewerbung lohnt.</p>
        </div>
      </div>

      <!-- Skills Lists -->
      <div class="skills-sections">
        <!-- Matched Skills -->
        <div v-if="jobFitData.matched_skills.length > 0" class="skills-section matched">
          <h4>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Erfuellte Anforderungen
          </h4>
          <ul class="skills-list">
            <li v-for="(skill, index) in jobFitData.matched_skills" :key="'matched-' + index" class="skill-item matched">
              <span class="skill-text">{{ skill.requirement_text }}</span>
              <span class="skill-match">{{ skill.user_skill_name }}</span>
            </li>
          </ul>
        </div>

        <!-- Partial Matches -->
        <div v-if="jobFitData.partial_matches.length > 0" class="skills-section partial">
          <h4>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
            Teilweise erfuellt
          </h4>
          <ul class="skills-list">
            <li v-for="(skill, index) in jobFitData.partial_matches" :key="'partial-' + index" class="skill-item partial">
              <span class="skill-text">{{ skill.requirement_text }}</span>
              <span class="skill-reason">{{ skill.match_reason }}</span>
            </li>
          </ul>
        </div>

        <!-- Missing Skills -->
        <div v-if="jobFitData.missing_skills.length > 0" class="skills-section missing">
          <h4>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            Fehlende Skills
          </h4>
          <ul class="skills-list">
            <li v-for="(skill, index) in jobFitData.missing_skills" :key="'missing-' + index" class="skill-item missing">
              <span class="skill-text">{{ skill.requirement_text }}</span>
              <span v-if="skill.requirement_type === 'must_have'" class="skill-type must-have">Must-Have</span>
              <span v-else class="skill-type nice-to-have">Nice-to-Have</span>
            </li>
          </ul>

          <!-- Skill Recommendations -->
          <div class="skill-recommendations">
            <p class="recommendations-hint">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              Tipp: Erwaehnen Sie relevante Erfahrungen oder Lernbereitschaft in Ihrer Bewerbung.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '../api/client'

const props = defineProps({
  applicationId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['score-loaded'])

const loading = ref(false)
const errorState = ref({
  message: '',
  hint: '',
  isTemporary: false,
  showContactLink: false
})
const jobFitData = ref(null)
const hasUserSkills = ref(true)

/**
 * Parse HTTP error and return user-friendly error state
 */
const parseErrorResponse = (e) => {
  const status = e.response?.status
  const serverError = e.response?.data?.error

  // 5xx Server errors - temporary, can retry
  if (status >= 500) {
    return {
      message: 'Voruebergehender Serverfehler',
      hint: 'Der Server ist momentan nicht erreichbar. Bitte versuchen Sie es in einigen Minuten erneut.',
      isTemporary: true,
      showContactLink: false
    }
  }

  // 404 - No requirements found (not really an error)
  if (status === 404) {
    return {
      message: 'Keine Anforderungen fuer diese Stelle gefunden',
      hint: 'Die Stellenanzeige enthaelt keine analysierbaren Anforderungen.',
      isTemporary: false,
      showContactLink: false
    }
  }

  // 429 - Rate limit exceeded
  if (status === 429) {
    return {
      message: 'Zu viele Anfragen',
      hint: 'Bitte warten Sie einen Moment und versuchen Sie es dann erneut.',
      isTemporary: true,
      showContactLink: false
    }
  }

  // 401/403 - Auth errors (handled by global interceptor usually)
  if (status === 401 || status === 403) {
    return {
      message: 'Zugriff verweigert',
      hint: 'Bitte melden Sie sich erneut an.',
      isTemporary: false,
      showContactLink: false
    }
  }

  // 400 - Bad request (client error)
  if (status === 400) {
    return {
      message: serverError || 'Ungueltige Anfrage',
      hint: 'Die Anfrage konnte nicht verarbeitet werden.',
      isTemporary: false,
      showContactLink: true
    }
  }

  // Network error (no response)
  if (!e.response) {
    return {
      message: 'Netzwerkfehler',
      hint: 'Bitte pruefen Sie Ihre Internetverbindung und versuchen Sie es erneut.',
      isTemporary: true,
      showContactLink: false
    }
  }

  // Other/unknown errors
  return {
    message: serverError || 'Fehler beim Laden des Job-Fit Scores',
    hint: 'Falls das Problem weiterhin besteht, kontaktieren Sie bitte den Support.',
    isTemporary: false,
    showContactLink: true
  }
}

const loadJobFitScore = async () => {
  if (!props.applicationId) return

  loading.value = true
  errorState.value = { message: '', hint: '', isTemporary: false, showContactLink: false }

  try {
    // First check if user has skills
    const skillsResponse = await api.get('/users/me/skills')
    const userSkills = skillsResponse.data.skills || []

    if (userSkills.length === 0) {
      hasUserSkills.value = false
      loading.value = false
      return
    }

    hasUserSkills.value = true

    // Load job-fit score
    const { data } = await api.get(`/applications/${props.applicationId}/job-fit`)

    if (data.success) {
      jobFitData.value = data.job_fit
      emit('score-loaded', data.job_fit)
    } else {
      errorState.value = {
        message: data.error || 'Fehler beim Laden des Job-Fit Scores',
        hint: '',
        isTemporary: false,
        showContactLink: true
      }
    }
  } catch (e) {
    errorState.value = parseErrorResponse(e)
  } finally {
    loading.value = false
  }
}

watch(() => props.applicationId, (newId) => {
  if (newId) {
    loadJobFitScore()
  }
}, { immediate: true })

onMounted(() => {
  if (props.applicationId) {
    loadJobFitScore()
  }
})

defineExpose({
  refresh: loadJobFitScore
})
</script>

<style scoped>
.job-fit-score {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-lg);
  margin-top: var(--space-lg);
}

/* Loading State */
.job-fit-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-xl);
  color: var(--color-text-secondary);
}

.loading-spinner {
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

/* Error State */
.job-fit-error {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: 0.875rem;
}

.job-fit-error.error-temporary {
  background: var(--color-warning-light);
  color: #8a6d17;
  border: 1px solid rgba(201, 162, 39, 0.3);
}

.job-fit-error svg {
  flex-shrink: 0;
  margin-top: 2px;
}

.job-fit-error .error-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.job-fit-error .error-message {
  font-weight: 500;
}

.job-fit-error .error-hint {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
  font-weight: normal;
}

.job-fit-error.error-temporary .error-hint {
  color: var(--color-text-secondary);
}

.job-fit-error .error-actions {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-top: var(--space-xs);
}

.job-fit-error .retry-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: transparent;
  border: 1px solid currentColor;
  color: inherit;
  font-size: 0.8125rem;
  padding: var(--space-xs) var(--space-sm);
}

.job-fit-error .retry-btn:hover {
  background: rgba(201, 162, 39, 0.15);
}

.job-fit-error .retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.job-fit-error .contact-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ai);
  text-decoration: none;
  font-size: 0.8125rem;
  font-weight: 500;
}

.job-fit-error .contact-link:hover {
  text-decoration: underline;
}

/* No Skills State */
.job-fit-no-skills {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-warning-light);
  border-radius: var(--radius-md);
}

.job-fit-no-skills svg {
  flex-shrink: 0;
  color: var(--color-warning);
}

.job-fit-no-skills strong {
  display: block;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.job-fit-no-skills p {
  margin: 0 0 var(--space-sm) 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
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

.score-badge.score-sehr_gut {
  background: var(--color-success-light);
  color: var(--color-success);
}

.score-badge.score-gut {
  background: rgba(196, 163, 90, 0.15);
  color: #8a7a2a;
}

.score-badge.score-mittel {
  background: rgba(201, 162, 39, 0.15);
  color: #8a6d17;
}

.score-badge.score-niedrig {
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

.progress-fill.fill-sehr_gut {
  background: var(--color-success);
}

.progress-fill.fill-gut {
  background: #c9a227;
}

.progress-fill.fill-mittel {
  background: #d4a017;
}

.progress-fill.fill-niedrig {
  background: var(--color-error);
}

.score-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-sumi);
  min-width: 60px;
  text-align: right;
}

/* Score Breakdown */
.score-breakdown {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.breakdown-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.breakdown-value {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.breakdown-percent {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* Low Score Warning */
.low-score-warning {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-error);
  margin-bottom: var(--space-lg);
}

.low-score-warning svg {
  flex-shrink: 0;
  color: var(--color-error);
}

.low-score-warning strong {
  display: block;
  color: var(--color-error);
  margin-bottom: var(--space-xs);
  font-size: 0.875rem;
}

.low-score-warning p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

/* Skills Sections */
.skills-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.skills-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--space-md) 0;
}

.skills-section.matched h4 {
  color: var(--color-success);
}

.skills-section.partial h4 {
  color: #8a7a2a;
}

.skills-section.missing h4 {
  color: var(--color-error);
}

.skills-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skill-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
}

.skill-item.matched {
  border-left-color: var(--color-success);
}

.skill-item.partial {
  border-left-color: #c9a227;
}

.skill-item.missing {
  border-left-color: var(--color-error);
}

.skill-text {
  flex: 1;
  font-size: 0.875rem;
  color: var(--color-sumi);
}

.skill-match {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: var(--color-success-light);
  color: var(--color-success);
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.skill-reason {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-style: italic;
}

.skill-type {
  font-size: 0.6875rem;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  font-weight: 600;
}

.skill-type.must-have {
  background: var(--color-error-light);
  color: var(--color-error);
}

.skill-type.nice-to-have {
  background: var(--color-warning-light);
  color: #8a6d17;
}

/* Skill Recommendations */
.skill-recommendations {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.recommendations-hint {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.recommendations-hint svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-ai);
}

/* Responsive */
@media (max-width: 640px) {
  .score-breakdown {
    grid-template-columns: 1fr;
  }

  .skill-item {
    flex-direction: column;
    gap: var(--space-xs);
  }

  .score-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }
}
</style>
