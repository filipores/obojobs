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
        @keydown.enter="startDemo"
      />
      <button
        v-if="!loading"
        @click="startDemo"
        class="demo-submit-btn"
        :disabled="!canSubmit"
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

    <!-- CV Upload Drop Zone -->
    <div
      class="cv-drop-zone"
      :class="{ 'is-dragging': isDragging, 'has-file': selectedFile, 'is-loading': loading }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".pdf"
        class="file-input"
        @change="onFileSelect"
      />

      <div v-if="!selectedFile" class="drop-zone-content">
        <svg class="drop-zone-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p class="drop-zone-text">
          <strong>Lebenslauf ablegen</strong> oder <button type="button" @click="triggerFileSelect" class="drop-zone-link">Datei auswählen</button>
        </p>
      </div>

      <div v-else class="selected-file-info">
        <svg class="file-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span class="file-name">{{ selectedFile.name }}</span>
        <button type="button" @click="clearFile" class="clear-file-btn" aria-label="Datei entfernen">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="demo-error">
      <p>{{ error }}</p>
      <button @click="clearError" class="error-dismiss">Erneut versuchen</button>
    </div>

    <!-- Hint Text -->
    <p v-if="!loading && !error" class="demo-hint">
      Lebenslauf + Stellenanzeigen-URL — keine Anmeldung nötig
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'

const emit = defineEmits(['demo-started', 'demo-complete'])

const inputRef = ref(null)
const fileInput = ref(null)
const url = ref('')
const isFocused = ref(false)
const loading = ref(false)
const error = ref('')
const selectedFile = ref(null)
const isDragging = ref(false)

const isValidUrl = computed(() => {
  if (!url.value) return false
  try {
    const parsed = new URL(url.value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
})

const canSubmit = computed(() => isValidUrl.value && selectedFile.value)

function handleFileSelection(file) {
  if (!file) return
  if (file.type === 'application/pdf') {
    selectedFile.value = file
    error.value = ''
  } else {
    error.value = 'Bitte wähle eine PDF-Datei aus.'
  }
}

const triggerFileSelect = () => {
  fileInput.value?.click()
}

const onFileSelect = (event) => {
  handleFileSelection(event.target.files?.[0])
}

const onDragOver = () => {
  isDragging.value = true
}

const onDragLeave = () => {
  isDragging.value = false
}

const onDrop = (event) => {
  isDragging.value = false
  handleFileSelection(event.dataTransfer.files?.[0])
}

const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const startDemo = async () => {
  if (!canSubmit.value || loading.value) return

  loading.value = true
  error.value = ''
  emit('demo-started')

  try {
    const formData = new FormData()
    formData.append('url', url.value)
    formData.append('cv_file', selectedFile.value)

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
    if (err.response?.status === 429) {
      error.value = 'Demo-Limit erreicht. Bitte registriere dich für unbegrenzten Zugang.'
    } else {
      error.value = err.response?.data?.message || 'Fehler beim Verarbeiten der URL. Bitte versuche es erneut.'
    }
  } finally {
    loading.value = false
  }
}

const clearError = () => {
  error.value = ''
}

const reset = () => {
  loading.value = false
  error.value = ''
}

defineExpose({ reset })

onMounted(() => {
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

/* CV Drop Zone */
.cv-drop-zone {
  margin-top: var(--space-md);
  border: 2px dashed var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg);
  transition: all var(--transition-base);
  background: var(--color-washi);
  cursor: pointer;
}

.cv-drop-zone:hover,
.cv-drop-zone.is-dragging {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.cv-drop-zone.has-file {
  border-style: solid;
  border-color: var(--color-koke);
  background: rgba(122, 139, 110, 0.05);
}

.cv-drop-zone.is-loading {
  opacity: 0.6;
  pointer-events: none;
}

.file-input {
  display: none;
}

.drop-zone-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.drop-zone-icon {
  color: var(--color-stone);
  opacity: 0.6;
  flex-shrink: 0;
}

.drop-zone-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.drop-zone-text strong {
  color: var(--color-sumi);
}

.drop-zone-link {
  background: none;
  border: none;
  color: var(--color-ai);
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.selected-file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.file-icon {
  color: var(--color-koke);
  flex-shrink: 0;
}

.file-name {
  font-weight: 500;
  color: var(--color-sumi);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clear-file-btn {
  background: none;
  border: none;
  padding: var(--space-xs);
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.clear-file-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-error);
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

  .cv-drop-zone {
    padding: var(--space-sm) var(--space-md);
  }
}
</style>
