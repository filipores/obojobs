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
          :style="{ '--status-color': option.color }"
          :aria-pressed="selectedResult === option.value"
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
      <DateTimePicker
        v-model="interviewDate"
        placeholder="Datum und Uhrzeit waehlen"
        aria-label="Interview-Termin"
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
import DateTimePicker from './DateTimePicker.vue'

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

onMounted(() => {
  // DateTimePicker handles ISO strings directly
  if (props.initialDate) {
    interviewDate.value = props.initialDate
  }
})

watch(() => props.initialResult, (newVal) => {
  selectedResult.value = newVal
})

watch(() => props.initialDate, (newVal) => {
  // DateTimePicker handles ISO strings directly
  interviewDate.value = newVal || ''
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

    // DateTimePicker already provides ISO string
    payload.interview_date = interviewDate.value || null

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
  border-color: var(--status-color, var(--color-ai));
  color: var(--color-sumi);
}

.status-option.active:hover {
  opacity: 0.9;
  color: #fff;
}

.status-option.active {
  border-color: var(--status-color, var(--color-ai));
  background: var(--status-color, var(--color-ai));
  color: #fff;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.status-option.active .status-icon {
  background: rgba(255, 255, 255, 0.9) !important;
}

.status-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
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
}
</style>
