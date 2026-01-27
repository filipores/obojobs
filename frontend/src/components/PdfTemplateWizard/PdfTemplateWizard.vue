<template>
  <div class="pdf-template-wizard">
    <div class="wizard zen-card">
      <!-- Wizard Header -->
      <div class="wizard-header">
        <h2>PDF-Template erstellen</h2>
        <p class="wizard-subtitle">
          Laden Sie ein PDF hoch und lassen Sie die KI automatisch Variablen erkennen.
        </p>

        <!-- Progress Bar -->
        <div class="wizard-progress">
          <div class="progress-steps">
            <div
              v-for="stepNum in 3"
              :key="stepNum"
              class="progress-step"
              :class="{
                active: step === stepNum,
                completed: step > stepNum
              }"
            >
              <div class="step-circle">
                <svg v-if="step > stepNum" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span v-else>{{ stepNum }}</span>
              </div>
              <span class="step-label">{{ stepLabels[stepNum - 1] }}</span>
            </div>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${((step - 1) / 2) * 100}%` }"></div>
          </div>
        </div>
      </div>

      <!-- Wizard Content -->
      <div class="wizard-content">
        <!-- Step 1: Upload PDF -->
        <Transition name="step" mode="out-in">
          <div v-if="step === 1" key="step1" class="wizard-step">
            <PdfUploadStep @file-selected="handleFileSelected" />
          </div>

          <!-- Step 2: AI Analysis -->
          <div v-else-if="step === 2" key="step2" class="wizard-step">
            <div class="analysis-step">
              <!-- Loading State -->
              <div v-if="analyzing" class="analysis-loading">
                <div class="loading-content">
                  <div class="loading-animation">
                    <div class="pulse-ring"></div>
                    <div class="pulse-ring delay-1"></div>
                    <div class="pulse-ring delay-2"></div>
                    <div class="ai-icon">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                      </svg>
                    </div>
                  </div>
                  <h3>KI analysiert PDF...</h3>
                  <p>{{ analysisStatus }}</p>
                </div>
              </div>

              <!-- Analysis Result -->
              <div v-else class="analysis-result">
                <div class="result-layout">
                  <!-- PDF Preview -->
                  <div class="preview-column">
                    <PdfPreview
                      :pdf-file="selectedFile"
                      :highlights="suggestions"
                    />
                  </div>

                  <!-- Suggestions Summary -->
                  <div class="summary-column">
                    <div class="summary-card zen-card">
                      <div class="summary-header">
                        <div class="summary-icon">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="3"/>
                            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                          </svg>
                        </div>
                        <div>
                          <h4>Analyse abgeschlossen</h4>
                          <p>{{ suggestions.length }} Variablen erkannt</p>
                        </div>
                      </div>

                      <div class="suggestions-preview">
                        <div
                          v-for="suggestion in suggestions.slice(0, 5)"
                          :key="suggestion.id"
                          class="suggestion-preview-item"
                        >
                          <span class="var-badge" :class="getVariableClass(suggestion.variable_name)">
                            {{ suggestion.variable_name }}
                          </span>
                          <span class="var-text">"{{ truncateText(suggestion.suggested_text, 30) }}"</span>
                        </div>
                        <div v-if="suggestions.length > 5" class="more-suggestions">
                          +{{ suggestions.length - 5 }} weitere Variablen
                        </div>
                      </div>

                      <p class="summary-hint">
                        Im naechsten Schritt koennen Sie die erkannten Variablen ueberpruefen und anpassen.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Review Variables -->
          <div v-else-if="step === 3" key="step3" class="wizard-step">
            <div class="review-layout">
              <!-- PDF Preview -->
              <div class="preview-column">
                <PdfPreview
                  :pdf-file="selectedFile"
                  :highlights="acceptedSuggestions"
                />
              </div>

              <!-- Variable Review -->
              <div class="review-column">
                <VariableReviewStep
                  :suggestions="suggestions"
                  @accept="handleAcceptSuggestion"
                  @reject="handleRejectSuggestion"
                  @save="handleSave"
                />
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Wizard Navigation -->
      <div class="wizard-nav">
        <button
          v-if="step > 1 && !analyzing"
          class="zen-btn"
          @click="prevStep"
        >
          Zurueck
        </button>
        <button class="zen-btn" @click="handleCancel">
          Abbrechen
        </button>
        <div class="nav-spacer"></div>
        <button
          v-if="step === 1"
          class="zen-btn zen-btn-ai"
          :disabled="!selectedFile"
          @click="startAnalysis"
        >
          PDF analysieren
        </button>
        <button
          v-if="step === 2 && !analyzing"
          class="zen-btn zen-btn-ai"
          @click="nextStep"
        >
          Variablen ueberpruefen
        </button>
      </div>
    </div>

    <!-- Error Toast -->
    <Transition name="toast">
      <div v-if="errorMessage" class="error-toast">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>{{ errorMessage }}</span>
        <button class="toast-close" @click="errorMessage = ''">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/api/client'
import PdfUploadStep from './PdfUploadStep.vue'
import VariableReviewStep from './VariableReviewStep.vue'
import PdfPreview from './PdfPreview.vue'

const emit = defineEmits(['template-created', 'cancel'])

// Step state
const step = ref(1)
const stepLabels = ['PDF hochladen', 'KI-Analyse', 'Variablen pruefen']

// File state
const selectedFile = ref(null)

// Analysis state
const analyzing = ref(false)
const analysisStatus = ref('Starte Analyse...')
const suggestions = ref([])

// Error state
const errorMessage = ref('')

// Computed
const acceptedSuggestions = computed(() =>
  suggestions.value.filter(s => s.status === 'accepted')
)

// File selection
function handleFileSelected(file) {
  selectedFile.value = file
  if (!file) {
    suggestions.value = []
  }
}

// Navigation
function prevStep() {
  if (step.value > 1) {
    step.value--
  }
}

function nextStep() {
  if (step.value < 3) {
    step.value++
  }
}

// Start AI analysis
async function startAnalysis() {
  if (!selectedFile.value) return

  step.value = 2
  analyzing.value = true
  analysisStatus.value = 'Starte Analyse...'
  suggestions.value = []
  errorMessage.value = ''

  try {
    // Create FormData for file upload
    const formData = new FormData()
    formData.append('pdf', selectedFile.value)

    // Simulate analysis phases
    analysisStatus.value = 'PDF wird hochgeladen...'
    await delay(500)

    analysisStatus.value = 'Textinhalte werden extrahiert...'
    await delay(800)

    analysisStatus.value = 'KI analysiert Dokumentstruktur...'
    await delay(600)

    analysisStatus.value = 'Variablen werden identifiziert...'

    // Make API call
    const { data } = await api.post('/pdf-templates/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Process suggestions from API
    if (data.suggestions && Array.isArray(data.suggestions)) {
      suggestions.value = data.suggestions.map((s, index) => ({
        id: s.id || `suggestion_${index}`,
        variable_name: s.variable_name || s.variableName,
        suggested_text: s.suggested_text || s.suggestedText || s.text,
        reason: s.reason || s.explanation,
        position: s.position || null,
        status: 'pending'
      }))
    } else {
      suggestions.value = []
    }

    analysisStatus.value = 'Analyse abgeschlossen!'
    await delay(400)

  } catch (err) {
    console.error('Analysis error:', err)
    errorMessage.value = err.response?.data?.error || 'Fehler bei der PDF-Analyse. Bitte versuchen Sie es erneut.'

    // Fall back to step 1 on error
    step.value = 1
  } finally {
    analyzing.value = false
  }
}

// Suggestion actions
function handleAcceptSuggestion(suggestion) {
  const index = suggestions.value.findIndex(s => s.id === suggestion.id)
  if (index !== -1) {
    suggestions.value[index].status = 'accepted'
  }
}

function handleRejectSuggestion(suggestion) {
  const index = suggestions.value.findIndex(s => s.id === suggestion.id)
  if (index !== -1) {
    suggestions.value[index].status = 'rejected'
  }
}

// Save template
async function handleSave() {
  if (acceptedSuggestions.value.length === 0) {
    errorMessage.value = 'Bitte akzeptieren Sie mindestens eine Variable.'
    return
  }

  try {
    // Create FormData with file and accepted variables
    const formData = new FormData()
    formData.append('pdf', selectedFile.value)
    formData.append('variables', JSON.stringify(
      acceptedSuggestions.value.map(s => ({
        variable_name: s.variable_name,
        suggested_text: s.suggested_text,
        position: s.position
      }))
    ))
    formData.append('name', `PDF Template - ${selectedFile.value.name}`)

    const { data } = await api.post('/pdf-templates', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    emit('template-created', data.template)

  } catch (err) {
    console.error('Save error:', err)
    errorMessage.value = err.response?.data?.error || 'Fehler beim Speichern des Templates.'
  }
}

// Cancel wizard
function handleCancel() {
  emit('cancel')
}

// Helpers
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function getVariableClass(variableName) {
  const classMap = {
    'FIRMA': 'var-firma',
    'POSITION': 'var-position',
    'ANSPRECHPARTNER': 'var-ansprechpartner',
    'QUELLE': 'var-quelle',
    'EINLEITUNG': 'var-einleitung'
  }
  return classMap[variableName?.toUpperCase()] || 'var-default'
}

function truncateText(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.pdf-template-wizard {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.wizard {
  padding: var(--space-xl, 2rem);
}

/* Wizard Header */
.wizard-header {
  text-align: center;
  margin-bottom: var(--space-xl, 2rem);
}

.wizard-header h2 {
  font-size: 1.75rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-sm, 0.5rem);
}

.wizard-subtitle {
  color: var(--color-text-secondary, #4A4A4A);
  margin-bottom: var(--space-lg, 1.5rem);
}

/* Progress Bar */
.wizard-progress {
  max-width: 500px;
  margin: 0 auto;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-sm, 0.5rem);
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs, 0.25rem);
}

.step-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-stone, #9B958F);
  transition: all var(--transition-base, 350ms ease);
}

.progress-step.active .step-circle {
  background: var(--color-ai, #3D5A6C);
  color: var(--color-text-inverse, #FAF8F3);
}

.progress-step.completed .step-circle {
  background: var(--color-success, #7A8B6E);
  color: var(--color-text-inverse, #FAF8F3);
}

.step-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
  white-space: nowrap;
}

.progress-step.active .step-label {
  color: var(--color-ai, #3D5A6C);
  font-weight: 500;
}

.progress-bar {
  height: 4px;
  background: var(--color-sand, #D4C9BA);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-ai, #3D5A6C);
  border-radius: var(--radius-full, 9999px);
  transition: width var(--transition-smooth, 500ms ease);
}

/* Wizard Content */
.wizard-content {
  min-height: 400px;
  margin-bottom: var(--space-xl, 2rem);
}

.wizard-step {
  animation: fadeIn 300ms ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Analysis Step */
.analysis-step {
  min-height: 400px;
}

.analysis-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.loading-content {
  text-align: center;
}

.loading-animation {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto var(--space-lg, 1.5rem);
}

.pulse-ring {
  position: absolute;
  inset: 0;
  border: 2px solid var(--color-ai, #3D5A6C);
  border-radius: 50%;
  animation: pulse 2s ease-out infinite;
}

.pulse-ring.delay-1 {
  animation-delay: 0.5s;
}

.pulse-ring.delay-2 {
  animation-delay: 1s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.ai-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 48px;
  height: 48px;
  background: var(--color-ai, #3D5A6C);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-inverse, #FAF8F3);
}

.loading-content h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-sm, 0.5rem);
}

.loading-content p {
  color: var(--color-text-secondary, #4A4A4A);
}

/* Analysis Result / Review Layout */
.result-layout,
.review-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg, 1.5rem);
  min-height: 500px;
}

.preview-column {
  min-height: 400px;
}

.summary-column,
.review-column {
  display: flex;
  flex-direction: column;
}

/* Summary Card */
.summary-card {
  padding: var(--space-lg, 1.5rem);
  flex: 1;
}

.summary-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md, 1rem);
  margin-bottom: var(--space-lg, 1.5rem);
  padding-bottom: var(--space-md, 1rem);
  border-bottom: 1px solid var(--color-border-light, #E5DFD4);
}

.summary-icon {
  width: 48px;
  height: 48px;
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  border-radius: var(--radius-md, 0.5rem);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-success, #7A8B6E);
  flex-shrink: 0;
}

.summary-header h4 {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-xs, 0.25rem);
}

.summary-header p {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #4A4A4A);
  margin: 0;
}

/* Suggestions Preview */
.suggestions-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 0.5rem);
  margin-bottom: var(--space-lg, 1.5rem);
}

.suggestion-preview-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  padding: var(--space-sm, 0.5rem);
  background: var(--color-washi, #FAF8F3);
  border-radius: var(--radius-sm, 0.25rem);
}

.var-badge {
  display: inline-flex;
  padding: var(--space-xs, 0.25rem) var(--space-sm, 0.5rem);
  border-radius: var(--radius-sm, 0.25rem);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.var-firma {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
}

.var-position {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
}

.var-ansprechpartner {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
}

.var-quelle {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
}

.var-einleitung {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
}

.var-default {
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-stone, #9B958F);
}

.var-text {
  font-size: 0.8125rem;
  color: var(--color-text-secondary, #4A4A4A);
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-suggestions {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary, #6B6B6B);
  text-align: center;
  padding: var(--space-sm, 0.5rem);
}

.summary-hint {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #4A4A4A);
  line-height: var(--leading-relaxed, 1.85);
}

/* Wizard Navigation */
.wizard-nav {
  display: flex;
  gap: var(--space-md, 1rem);
  padding-top: var(--space-lg, 1.5rem);
  border-top: 1px solid var(--color-border-light, #E5DFD4);
}

.nav-spacer {
  flex: 1;
}

/* Error Toast */
.error-toast {
  position: fixed;
  bottom: var(--space-lg, 1.5rem);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  padding: var(--space-md, 1rem) var(--space-lg, 1.5rem);
  background: var(--color-error, #B87A6E);
  color: white;
  border-radius: var(--radius-md, 0.5rem);
  box-shadow: var(--shadow-elevated, 0 8px 32px rgba(44, 44, 44, 0.15));
  z-index: 1000;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  margin-left: var(--space-sm, 0.5rem);
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  transition: background 200ms ease;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Transitions */
.step-enter-active,
.step-leave-active {
  transition: all 300ms ease;
}

.step-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.step-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 300ms ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

/* Responsive */
@media (max-width: 968px) {
  .result-layout,
  .review-layout {
    grid-template-columns: 1fr;
  }

  .preview-column {
    order: 2;
  }

  .summary-column,
  .review-column {
    order: 1;
  }
}

@media (max-width: 768px) {
  .wizard {
    padding: var(--space-lg, 1.5rem);
  }

  .progress-steps {
    gap: var(--space-xs, 0.25rem);
  }

  .step-label {
    display: none;
  }

  .wizard-nav {
    flex-wrap: wrap;
  }
}
</style>
