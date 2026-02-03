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
              v-for="stepNum in 2"
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
            <div class="progress-fill" :style="{ width: `${(step - 1) * 100}%` }"></div>
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

          <!-- Step 2: AI Analysis + Quick Review -->
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
                  <!-- Upload Progress Bar -->
                  <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                    </div>
                    <span class="progress-text">{{ uploadProgress }}%</span>
                  </div>
                </div>
              </div>

              <!-- Quick Review (default after analysis) -->
              <div v-else-if="!showDetailedReview" class="quick-review-wrapper">
                <QuickReview
                  :suggestions="suggestions"
                  @confirm="handleQuickConfirm"
                  @adjust="handleShowDetailedReview"
                />
              </div>

              <!-- Detailed Review (when user clicks "Nein, anpassen") -->
              <div v-else class="review-layout">
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
          </div>
        </Transition>
      </div>

      <!-- Wizard Navigation -->
      <div class="wizard-nav">
        <button
          v-if="step > 1 && !analyzing && showDetailedReview"
          class="zen-btn"
          @click="handleBackToQuickReview"
        >
          Zurueck
        </button>
        <button
          v-else-if="step > 1 && !analyzing"
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
import QuickReview from './QuickReview.vue'

const emit = defineEmits(['template-created', 'cancel'])

// Step state
const step = ref(1)
const stepLabels = ['PDF hochladen', 'Variablen pruefen']

// Quick review state
const showDetailedReview = ref(false)

// File state
const selectedFile = ref(null)

// Analysis state
const analyzing = ref(false)
const analysisStatus = ref('Starte Analyse...')
const uploadProgress = ref(0)
const suggestions = ref([])

// Error state
const errorMessage = ref('')

// Template state (from upload)
const templateId = ref(null)
const templateData = ref(null)

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
    showDetailedReview.value = false
  }
}

function handleBackToQuickReview() {
  showDetailedReview.value = false
}

function handleShowDetailedReview() {
  showDetailedReview.value = true
}

// Quick confirm - accept all and save
async function handleQuickConfirm() {
  // Accept all suggestions
  suggestions.value.forEach(s => {
    s.status = 'accepted'
  })
  // Then save
  await handleSave()
}

// Start AI analysis
async function startAnalysis() {
  if (!selectedFile.value) return

  step.value = 2
  analyzing.value = true
  analysisStatus.value = 'Starte Analyse...'
  uploadProgress.value = 0
  suggestions.value = []
  errorMessage.value = ''

  try {
    // Step 1: Upload PDF to create template
    const uploadFormData = new FormData()
    uploadFormData.append('file', selectedFile.value)
    uploadFormData.append('name', selectedFile.value.name.replace(/\.pdf$/i, ''))

    analysisStatus.value = 'PDF wird hochgeladen...'

    const uploadResponse = await api.post('/templates/upload-pdf', uploadFormData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      }
    })

    // Store template ID for later
    templateId.value = uploadResponse.data.template.id
    templateData.value = uploadResponse.data.template

    analysisStatus.value = 'Textinhalte wurden extrahiert...'
    await delay(500)

    // Step 2: Analyze variables using AI
    analysisStatus.value = 'KI analysiert Dokumentstruktur...'

    const analyzeResponse = await api.post(`/templates/${templateId.value}/analyze-variables`)

    analysisStatus.value = 'Variablen werden identifiziert...'
    await delay(400)

    // Process suggestions from API
    if (analyzeResponse.data.suggestions && Array.isArray(analyzeResponse.data.suggestions)) {
      suggestions.value = analyzeResponse.data.suggestions.map((s, index) => ({
        id: s.id || `suggestion_${index}`,
        variable_name: s.variable_name || s.variableName || s.variable,
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

    // Stay on step 2 to show QuickReview
    // showDetailedReview is false by default, so QuickReview will be shown

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

  if (!templateId.value) {
    errorMessage.value = 'Kein Template vorhanden. Bitte starten Sie die Analyse erneut.'
    return
  }

  try {
    // Save variable positions to the existing template
    const variablePositions = acceptedSuggestions.value.map(s => ({
      variable_name: s.variable_name,
      suggested_text: s.suggested_text,
      position: s.position
    }))

    const { data } = await api.put(`/templates/${templateId.value}/variable-positions`, {
      variable_positions: variablePositions
    })

    emit('template-created', data.template || templateData.value)

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
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
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

/* Upload Progress */
.upload-progress {
  margin-top: var(--space-lg, 1.5rem);
  max-width: 300px;
  margin-left: auto;
  margin-right: auto;
}

.progress-bar {
  height: 8px;
  background: var(--color-border, #D4C9BA);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-ai, #3D5A6C);
  border-radius: var(--radius-full, 9999px);
  transition: width 150ms ease;
}

.progress-text {
  display: block;
  margin-top: var(--space-sm, 0.5rem);
  font-size: 0.875rem;
  color: var(--color-text-secondary, #4A4A4A);
  font-weight: 500;
}

/* Review Layout */
.review-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg, 1.5rem);
  min-height: 500px;
}

.preview-column {
  min-height: 400px;
}

.review-column {
  display: flex;
  flex-direction: column;
}

/* Quick Review Wrapper */
.quick-review-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
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
  z-index: var(--z-toast);
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
  .review-layout {
    grid-template-columns: 1fr;
  }

  .preview-column {
    order: 2;
  }

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
