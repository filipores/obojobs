<template>
  <div class="demo-generator">
    <!-- URL Input -->
    <div class="demo-input-wrapper" :class="{ 'demo-input-focused': isFocused, 'demo-input-loading': loading }">
      <svg class="demo-input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
      </svg>
      <input
        ref="inputRef"
        v-model="url"
        type="url"
        placeholder="Stellenanzeigen-URL einfügen..."
        class="demo-input"
        :disabled="loading"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @paste="onPaste"
        @keydown.enter="startDemo"
      />
      <button
        v-if="!loading"
        @click="startDemo"
        class="demo-submit-btn"
        :disabled="!isValidUrl"
        aria-label="Demo starten"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </button>
      <div v-else class="demo-loading">
        <div class="demo-spinner"></div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="demo-loading-state">
      <div class="loading-enso">
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
      </div>
      <p class="loading-text">{{ loadingText }}</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="demo-error">
      <p>{{ error }}</p>
      <button @click="clearError" class="error-dismiss">Erneut versuchen</button>
    </div>

    <!-- Hint Text -->
    <p v-if="!loading && !error" class="demo-hint">
      Probiere es aus - keine Anmeldung erforderlich
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'

const emit = defineEmits(['demo-started', 'demo-complete', 'request-cv'])

const inputRef = ref(null)
const url = ref('')
const isFocused = ref(false)
const loading = ref(false)
const error = ref('')
const loadingText = ref('Analysiere Stellenanzeige...')

// Validate URL
const isValidUrl = computed(() => {
  if (!url.value) return false
  try {
    const parsed = new URL(url.value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
})

// Handle paste - auto-start on paste
const onPaste = async () => {
  // Let the paste complete first
  await new Promise(resolve => setTimeout(resolve, 50))

  if (isValidUrl.value) {
    startDemo()
  }
}

// Start the demo - call API directly (no CV required)
const startDemo = async () => {
  if (!isValidUrl.value || loading.value) return

  loading.value = true
  error.value = ''
  emit('demo-started')

  const loadingTexts = [
    'Analysiere Stellenanzeige...',
    'Extrahiere Anforderungen...',
    'Erstelle Anschreiben...'
  ]
  let textIndex = 0
  const textInterval = setInterval(() => {
    textIndex = (textIndex + 1) % loadingTexts.length
    loadingText.value = loadingTexts[textIndex]
  }, 2500)

  try {
    const response = await api.post('/demo/generate', { url: url.value }, { suppressToast: true })

    if (response.data.success) {
      emit('demo-complete', {
        url: url.value,
        result: response.data
      })
    } else {
      error.value = response.data.message || 'Fehler beim Generieren des Anschreibens'
    }
  } catch (err) {
    if (err.response?.status === 429) {
      error.value = 'Demo-Limit erreicht. Bitte registriere dich für unbegrenzten Zugang.'
    } else {
      error.value = err.response?.data?.message || 'Fehler beim Verarbeiten der URL. Bitte versuche es erneut.'
    }
  } finally {
    clearInterval(textInterval)
    loading.value = false
  }
}

// Generate demo with CV file (called by parent after CV upload)
const generateWithCV = async (cvFile) => {
  if (!isValidUrl.value) return

  loading.value = true
  error.value = ''

  const textInterval = setInterval(() => {
    const texts = ['Lese deinen Lebenslauf...', 'Erstelle personalisiertes Anschreiben...']
    loadingText.value = texts[Math.floor(Math.random() * texts.length)]
  }, 2500)

  try {
    const formData = new FormData()
    formData.append('url', url.value)
    formData.append('cv_file', cvFile)

    const response = await api.post('/demo/generate', formData, { suppressToast: true })

    if (response.data.success) {
      emit('demo-complete', {
        url: url.value,
        result: response.data
      })
    } else {
      error.value = response.data.message || 'Fehler beim Generieren des Anschreibens'
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Fehler beim Verarbeiten der URL. Bitte versuche es erneut.'
  } finally {
    clearInterval(textInterval)
    loading.value = false
  }
}

// Reset the generator state
const reset = () => {
  loading.value = false
  error.value = ''
}

// Expose methods to parent
defineExpose({ generateWithCV, reset })

const clearError = () => {
  error.value = ''
  url.value = ''
  inputRef.value?.focus()
}

onMounted(() => {
  // Auto-focus the input on mount
  inputRef.value?.focus()
})
</script>

<style scoped>
.demo-generator {
  width: 100%;
}

.demo-input-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-bg-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-paper);
}

.demo-input-wrapper:hover {
  border-color: var(--color-stone);
}

.demo-input-focused {
  border-color: var(--color-ai);
  box-shadow: var(--shadow-lifted), 0 0 0 4px var(--color-ai-subtle);
}

.demo-input-loading {
  opacity: 0.8;
  pointer-events: none;
}

.demo-input-icon {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.demo-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1.0625rem;
  color: var(--color-text-primary);
  outline: none;
  font-family: inherit;
}

.demo-input::placeholder {
  color: var(--color-text-ghost);
}

.demo-submit-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  border: none;
  border-radius: var(--radius-lg);
  color: var(--color-text-inverse);
  cursor: pointer;
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.demo-submit-btn:hover:not(:disabled) {
  background: var(--color-ai-light);
  transform: translateX(2px);
}

.demo-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.demo-loading {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.demo-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-ai-subtle);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Loading State */
.demo-loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: var(--space-xl);
}

.loading-enso {
  width: 80px;
  height: 80px;
  margin-bottom: var(--space-md);
}

.enso-circle {
  width: 100%;
  height: 100%;
}

.enso-path {
  stroke: var(--color-ai);
  stroke-dasharray: 283;
  stroke-dashoffset: 283;
  animation: draw-enso 2s var(--ease-zen) forwards, pulse-opacity 2s ease-in-out infinite 2s;
}

@keyframes draw-enso {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes pulse-opacity {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.loading-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  animation: fade-in 0.3s ease-out;
}

/* Error State */
.demo-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
}

.demo-error p {
  font-size: 0.875rem;
  color: var(--color-error);
  margin: 0;
}

.error-dismiss {
  padding: var(--space-xs) var(--space-sm);
  background: transparent;
  border: 1px solid var(--color-error);
  border-radius: var(--radius-sm);
  color: var(--color-error);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.error-dismiss:hover {
  background: var(--color-error);
  color: var(--color-text-inverse);
}

/* Hint Text */
.demo-hint {
  text-align: center;
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-ghost);
}

/* Animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .demo-input-wrapper {
    padding: var(--space-sm) var(--space-md);
  }

  .demo-input {
    font-size: 1rem;
  }

  .demo-submit-btn {
    width: 40px;
    height: 40px;
  }
}
</style>
