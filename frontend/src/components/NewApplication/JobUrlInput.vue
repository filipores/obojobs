<template>
  <div class="form-card zen-card">
    <!-- URL Input with Portal Detection -->
    <div class="form-group">
      <label class="form-label">Stellenanzeigen-URL</label>
      <div class="url-input-wrapper">
        <svg class="url-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        <input
          v-model="localUrl"
          type="url"
          placeholder="https://example.com/jobs/stellenanzeige"
          class="form-input url-input"
          :class="{
            'url-valid': showUrlValidation && urlValidation.isValid === true,
            'url-invalid': showUrlValidation && urlValidation.isValid === false
          }"
          :disabled="loading || generating"
          @input="onUrlInput"
          @paste="onUrlPaste"
          @keydown.enter="onUrlEnterPressed"
        />
        <!-- Validation Icon -->
        <span v-if="showUrlValidation && urlValidation.isValid === true" class="url-validation-icon url-validation-valid">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </span>
        <span v-else-if="showUrlValidation && urlValidation.isValid === false" class="url-validation-icon url-validation-invalid" :title="urlValidation.message">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </span>
        <!-- Portal Badge -->
        <span v-if="detectedPortal && urlValidation.isValid !== false" :class="['portal-badge', `portal-${detectedPortal.id}`]">
          {{ detectedPortal.name }}
        </span>
      </div>
      <!-- Validation Error Message -->
      <p v-if="showUrlValidation && urlValidation.isValid === false" class="url-validation-message">
        {{ urlValidation.message }}
      </p>
      <p v-else class="form-hint">Kopiere die URL der Stellenanzeige und füge sie hier ein</p>
      <!-- ARIA Live Region for Screenreaders -->
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ urlValidationAnnouncement }}
      </div>
    </div>

    <!-- Enso Recognition Animation (shown during paste detection) -->
    <div v-if="loading && !quickConfirmData && !previewData" class="enso-recognition-container">
      <div class="enso-recognition" :class="{ 'enso-complete': recognitionComplete }">
        <svg class="enso-circle" viewBox="0 0 100 100">
          <circle
            class="enso-path"
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke-width="3"
            stroke-linecap="round"
          />
        </svg>
        <div v-if="recognitionComplete && recognizedCompany" class="enso-company-name">
          {{ recognizedCompany }}
        </div>
        <div v-else class="enso-status">
          Erkenne Stellenanzeige...
        </div>
      </div>
    </div>

    <!-- Error State with Broken Enso - Graceful Fallback -->
    <div v-if="error && !previewData && !showManualFallback" class="scrape-error-state">
      <div class="scrape-error-enso">
        <EnsoCircle state="broken" size="lg" color="var(--color-stone)" :duration="3000" />
      </div>
      <p class="scrape-error-message">Diese Seite spricht nicht mit uns.</p>
      <p class="scrape-error-reassurance">Kein Problem.</p>
      <button @click="$emit('show-manual-fallback')" class="zen-btn zen-btn-ai scrape-error-action">
        Stellentext selbst einfügen
      </button>
    </div>

    <!-- Manual Text Fallback Section - Expanding Flow -->
    <ManualTextInput
      v-if="showManualFallback && !previewData"
      :analyzing-manual-text="analyzingManualText"
      @analyze="$emit('analyze-manual-text', $event)"
      @close="$emit('reset-manual-fallback')"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EnsoCircle from '../application/EnsoCircle.vue'
import ManualTextInput from './ManualTextInput.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  generating: { type: Boolean, default: false },
  error: { type: String, default: '' },
  quickConfirmData: { type: Object, default: null },
  previewData: { type: Object, default: null },
  showManualFallback: { type: Boolean, default: false },
  analyzingManualText: { type: Boolean, default: false },
  recognitionComplete: { type: Boolean, default: false },
  recognizedCompany: { type: String, default: '' },
  urlTouched: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update:modelValue',
  'url-input',
  'url-paste',
  'url-enter',
  'show-manual-fallback',
  'analyze-manual-text',
  'reset-manual-fallback'
])

const localUrl = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const urlValidation = computed(() => {
  const urlValue = props.modelValue.trim()

  if (!urlValue) {
    return { isValid: null, message: '' }
  }

  if (!urlValue.match(/^https?:\/\//i)) {
    return { isValid: false, message: 'URL muss mit http:// oder https:// beginnen' }
  }

  try {
    const parsedUrl = new URL(urlValue)

    if (!parsedUrl.hostname.includes('.')) {
      return { isValid: false, message: 'Ungültige Domain (z.B. example.com)' }
    }

    if (parsedUrl.hostname.endsWith('.')) {
      return { isValid: false, message: 'Domain darf nicht mit einem Punkt enden' }
    }

    return { isValid: true, message: '' }
  } catch {
    return { isValid: false, message: 'Ungültiges URL-Format' }
  }
})

const showUrlValidation = computed(() => {
  return props.urlTouched && props.modelValue.trim().length > 0
})

const urlValidationAnnouncement = computed(() => {
  if (!showUrlValidation.value) return ''
  if (urlValidation.value.isValid === true) {
    return 'URL ist gültig'
  }
  if (urlValidation.value.isValid === false) {
    return `URL ungültig: ${urlValidation.value.message}`
  }
  return ''
})

const detectedPortal = computed(() => {
  if (!props.modelValue) return null

  const urlLower = props.modelValue.toLowerCase()

  if (urlLower.includes('stepstone.de')) {
    return { id: 'stepstone', name: 'StepStone' }
  }
  if (urlLower.includes('indeed.com') || urlLower.includes('indeed.de')) {
    return { id: 'indeed', name: 'Indeed' }
  }
  if (urlLower.includes('xing.com')) {
    return { id: 'xing', name: 'XING' }
  }
  if (urlLower.includes('arbeitsagentur.de')) {
    return { id: 'arbeitsagentur', name: 'Arbeitsagentur' }
  }

  if (props.modelValue.startsWith('http')) {
    return { id: 'generic', name: 'Sonstige' }
  }

  return null
})

const onUrlInput = () => {
  emit('url-input')
}

const onUrlPaste = () => {
  emit('url-paste')
}

const onUrlEnterPressed = (event) => {
  if (props.modelValue && urlValidation.value.isValid === true && !props.loading && !props.generating && !props.previewData) {
    event.preventDefault()
    emit('url-enter')
  }
}
</script>

<style scoped>
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
  padding-right: 130px;
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.url-input.url-valid {
  border-color: var(--color-koke);
  box-shadow: 0 0 0 3px rgba(122, 139, 110, 0.15);
}

.url-input.url-invalid {
  border-color: #b45050;
  box-shadow: 0 0 0 3px rgba(180, 80, 80, 0.15);
}

.url-validation-icon {
  position: absolute;
  right: 100px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.url-validation-valid {
  color: var(--color-koke);
  background: rgba(122, 139, 110, 0.15);
}

.url-validation-invalid {
  color: #b45050;
  background: rgba(180, 80, 80, 0.15);
  cursor: help;
}

.url-validation-message {
  font-size: 0.8125rem;
  color: #b45050;
  margin-top: var(--space-xs);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.portal-badge {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.portal-badge.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-badge.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-badge.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-badge.portal-arbeitsagentur {
  background: rgba(0, 68, 103, 0.15);
  color: #004467;
}

.portal-badge.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

.enso-recognition-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-xl) 0;
  margin-top: var(--space-lg);
}

.enso-recognition {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.enso-circle {
  position: absolute;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.enso-path {
  stroke: var(--color-ai);
  stroke-dasharray: 283;
  stroke-dashoffset: 283;
  animation: enso-draw 1.5s ease-in-out forwards, enso-pulse 2s ease-in-out 1.5s infinite;
  opacity: 0.8;
}

.enso-complete .enso-path {
  stroke-dashoffset: 0;
  animation: enso-complete-glow 0.6s ease-out forwards;
}

.enso-status {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-align: center;
  margin-top: var(--space-sm);
  animation: enso-status-fade 1.5s ease-in-out infinite;
}

.enso-company-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-ai);
  text-align: center;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  animation: enso-materialize 0.6s ease-out forwards;
  opacity: 0;
  transform: scale(0.8);
}

@keyframes enso-draw {
  0% {
    stroke-dashoffset: 283;
    opacity: 0.3;
  }
  50% {
    opacity: 0.8;
  }
  100% {
    stroke-dashoffset: 20;
    opacity: 0.8;
  }
}

@keyframes enso-pulse {
  0%, 100% {
    stroke-dashoffset: 20;
    opacity: 0.6;
  }
  50% {
    stroke-dashoffset: 40;
    opacity: 1;
  }
}

@keyframes enso-complete-glow {
  0% {
    stroke: var(--color-ai);
    filter: none;
  }
  50% {
    stroke: var(--color-koke);
    filter: drop-shadow(0 0 8px var(--color-koke));
  }
  100% {
    stroke: var(--color-koke);
    filter: none;
    opacity: 1;
  }
}

@keyframes enso-status-fade {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

@keyframes enso-materialize {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.scrape-error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-2xl) var(--space-lg);
  margin-top: var(--space-lg);
  animation: scrape-error-fade-in 0.6s var(--ease-zen) forwards;
}

.scrape-error-enso {
  margin-bottom: var(--space-xl);
  opacity: 0;
  animation: scrape-error-enso-appear 0.8s var(--ease-zen) 0.2s forwards;
}

.scrape-error-message {
  font-size: 1.25rem;
  font-weight: 400;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
  opacity: 0;
  animation: scrape-error-text-appear 0.6s var(--ease-zen) 0.5s forwards;
}

.scrape-error-reassurance {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-xl) 0;
  font-style: italic;
  opacity: 0;
  animation: scrape-error-text-appear 0.6s var(--ease-zen) 0.7s forwards;
}

.scrape-error-action {
  opacity: 0;
  animation: scrape-error-action-appear 0.5s var(--ease-zen) 1s forwards;
}

@keyframes scrape-error-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scrape-error-enso-appear {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes scrape-error-text-appear {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scrape-error-action-appear {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .url-input {
    padding-right: var(--space-md);
  }

  .url-input.url-valid,
  .url-input.url-invalid {
    padding-right: 50px;
  }

  .url-validation-icon {
    right: var(--space-md);
  }

  .portal-badge {
    position: static;
    transform: none;
    display: inline-block;
    margin-top: var(--space-sm);
  }

  .url-input-wrapper {
    display: flex;
    flex-direction: column;
  }
}
</style>
