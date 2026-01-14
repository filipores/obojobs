<template>
  <div class="interview-tracker">
    <!-- Interview Status Section -->
    <div class="tracker-section">
      <label class="tracker-label">Interview-Status</label>
      <div class="status-options">
        <button
          v-for="option in resultOptions"
          :key="option.value"
          :class="['status-option', { active: selectedResult === option.value }]"
          @click="selectResult(option.value)"
        >
          <span class="status-icon" :style="{ background: option.color }"></span>
          <span>{{ option.label }}</span>
        </button>
      </div>
    </div>

    <!-- Interview Date Section -->
    <div v-if="selectedResult" class="tracker-section">
      <label class="tracker-label">Interview-Termin</label>
      <input
        v-model="interviewDate"
        type="datetime-local"
        class="form-input date-input"
        @change="updateInterviewData"
      />
    </div>

    <!-- Interview Feedback Section -->
    <div v-if="selectedResult && ['completed', 'passed', 'rejected', 'offer_received'].includes(selectedResult)" class="tracker-section">
      <label class="tracker-label">Eigenes Feedback</label>
      <textarea
        v-model="interviewFeedback"
        placeholder="Wie lief das Interview? Was war gut, was koennte besser sein?"
        rows="4"
        class="form-textarea"
        @blur="updateInterviewData"
      ></textarea>
      <p class="feedback-hint">Diese Notizen sind nur fuer Sie sichtbar und helfen bei der Analyse.</p>
    </div>

    <!-- Save Status -->
    <div v-if="saveStatus" :class="['save-status', saveStatus.type]">
      {{ saveStatus.message }}
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
  },
  initialDate: {
    type: String,
    default: null
  },
  initialResult: {
    type: String,
    default: null
  },
  initialFeedback: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['updated'])

const selectedResult = ref(props.initialResult || null)
const interviewDate = ref('')
const interviewFeedback = ref(props.initialFeedback || '')
const saveStatus = ref(null)

const resultOptions = [
  { value: 'scheduled', label: 'Geplant', color: 'var(--color-ai)' },
  { value: 'completed', label: 'Durchgefuehrt', color: 'var(--color-terra)' },
  { value: 'passed', label: 'Bestanden', color: 'var(--color-koke)' },
  { value: 'rejected', label: 'Absage', color: '#b45050' },
  { value: 'offer_received', label: 'Angebot erhalten', color: '#4a9d4a' }
]

const formatDateForInput = (isoString) => {
  if (!isoString) return ''
  // Convert ISO string to local datetime-local format
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

onMounted(() => {
  if (props.initialDate) {
    interviewDate.value = formatDateForInput(props.initialDate)
  }
})

watch(() => props.initialResult, (newVal) => {
  selectedResult.value = newVal
})

watch(() => props.initialDate, (newVal) => {
  interviewDate.value = formatDateForInput(newVal)
})

watch(() => props.initialFeedback, (newVal) => {
  interviewFeedback.value = newVal || ''
})

const selectResult = async (result) => {
  selectedResult.value = result
  await updateInterviewData()
}

const updateInterviewData = async () => {
  try {
    saveStatus.value = { type: 'saving', message: 'Speichern...' }

    const payload = {
      interview_result: selectedResult.value,
      interview_feedback: interviewFeedback.value || null
    }

    // Only include date if set
    if (interviewDate.value) {
      payload.interview_date = new Date(interviewDate.value).toISOString()
    } else {
      payload.interview_date = null
    }

    const { data } = await api.put(`/applications/${props.applicationId}/interview-result`, payload)

    if (data.success) {
      saveStatus.value = { type: 'success', message: 'Gespeichert!' }
      emit('updated', data.application)

      // Clear success message after 2 seconds
      setTimeout(() => {
        if (saveStatus.value?.type === 'success') {
          saveStatus.value = null
        }
      }, 2000)
    }
  } catch (err) {
    console.error('Fehler beim Speichern:', err)
    saveStatus.value = {
      type: 'error',
      message: err.response?.data?.error || 'Fehler beim Speichern'
    }
  }
}
</script>

<style scoped>
.interview-tracker {
  background: var(--color-washi);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}

.tracker-section {
  margin-bottom: var(--space-lg);
}

.tracker-section:last-of-type {
  margin-bottom: 0;
}

.tracker-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

/* Status Options */
.status-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.status-option {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.status-option:hover {
  border-color: var(--color-ai);
  color: var(--color-sumi);
}

.status-option.active {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  font-weight: 500;
}

.status-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Date Input */
.date-input {
  max-width: 280px;
}

/* Feedback */
.feedback-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
  margin-bottom: 0;
}

/* Save Status */
.save-status {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  margin-top: var(--space-md);
}

.save-status.saving {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.save-status.success {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.save-status.error {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

@media (max-width: 480px) {
  .status-options {
    flex-direction: column;
  }

  .status-option {
    width: 100%;
    justify-content: flex-start;
  }

  .date-input {
    max-width: 100%;
  }
}
</style>
