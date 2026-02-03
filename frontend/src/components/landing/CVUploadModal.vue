<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="visible"
        class="cv-modal-overlay"
        @click="handleOverlayClick"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cv-modal-title"
      >
        <div class="cv-modal zen-card animate-fade-up" @click.stop>
          <div class="cv-modal-header">
            <div class="cv-modal-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <h2 id="cv-modal-title">Personalisiere dein Anschreiben</h2>
            <p class="cv-modal-subtitle">Lade deinen Lebenslauf hoch fur ein individuelles Anschreiben</p>
          </div>

          <!-- Drop Zone -->
          <div
            class="cv-drop-zone"
            :class="{
              'is-dragging': isDragging,
              'has-file': selectedFile,
              'has-error': error
            }"
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
              <div class="drop-zone-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <p class="drop-zone-text">
                <strong>PDF hier ablegen</strong> oder
                <button type="button" @click="triggerFileSelect" class="drop-zone-link">Datei auswahlen</button>
              </p>
              <span class="drop-zone-hint">Nur PDF-Dateien, max. 10 MB</span>
            </div>

            <div v-else class="selected-file-info">
              <div class="file-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <span class="file-name">{{ selectedFile.name }}</span>
              <button type="button" @click="clearFile" class="clear-file-btn" aria-label="Datei entfernen">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="cv-modal-error">
            {{ error }}
          </div>

          <!-- Actions -->
          <div class="cv-modal-actions">
            <button
              @click="handleSubmit"
              :disabled="!selectedFile"
              class="zen-btn zen-btn-ai zen-btn-lg cv-submit-btn"
            >
              <span>Weiter</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </button>
          </div>

          <!-- Info Text -->
          <p class="cv-modal-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
            Dein Lebenslauf wird nur fur diese Demo verwendet
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'submit'])

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const error = ref('')

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

const triggerFileSelect = () => {
  fileInput.value?.click()
}

const validateFile = (file) => {
  if (!file) {
    return 'Bitte wahle eine Datei aus.'
  }
  if (file.type !== 'application/pdf') {
    return 'Bitte wahle eine PDF-Datei aus.'
  }
  if (file.size > MAX_FILE_SIZE) {
    return 'Die Datei ist zu gross. Maximal 10 MB erlaubt.'
  }
  return null
}

const onFileSelect = (event) => {
  const file = event.target.files?.[0]
  const validationError = validateFile(file)

  if (validationError) {
    error.value = validationError
    selectedFile.value = null
  } else {
    selectedFile.value = file
    error.value = ''
  }
}

const onDragOver = () => {
  isDragging.value = true
}

const onDragLeave = () => {
  isDragging.value = false
}

const onDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  const validationError = validateFile(file)

  if (validationError) {
    error.value = validationError
    selectedFile.value = null
  } else {
    selectedFile.value = file
    error.value = ''
  }
}

const clearFile = () => {
  selectedFile.value = null
  error.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const handleSubmit = () => {
  if (selectedFile.value) {
    emit('submit', selectedFile.value)
  }
}

const handleOverlayClick = () => {
  // Don't allow closing by clicking overlay - CV is required
  // But we could emit a close event if needed
}

const handleKeydown = (_e) => {
  if (!props.visible) return
  // Don't close on Escape - CV is required
}

watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    // Reset state when modal opens
    selectedFile.value = null
    error.value = ''
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.cv-modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(44, 44, 44, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.cv-modal {
  width: 100%;
  max-width: 480px;
  padding: var(--space-xl);
  text-align: center;
}

.cv-modal-header {
  margin-bottom: var(--space-xl);
}

.cv-modal-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-md);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-lg);
  color: var(--color-ai);
}

.cv-modal-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-sumi);
}

.cv-modal-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: var(--leading-relaxed);
}

/* Drop Zone */
.cv-drop-zone {
  border: 2px dashed var(--color-sand);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  transition: all var(--transition-base);
  background: var(--color-washi);
  cursor: pointer;
  margin-bottom: var(--space-lg);
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

.cv-drop-zone.has-error {
  border-color: var(--color-error);
  background: var(--color-error-light);
}

.file-input {
  display: none;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.drop-zone-icon {
  color: var(--color-stone);
  opacity: 0.6;
}

.drop-zone-text {
  font-size: 1rem;
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
  padding: 0;
}

.drop-zone-link:hover {
  color: var(--color-ai-light);
}

.drop-zone-hint {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
}

.selected-file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.file-icon {
  color: var(--color-koke);
}

.file-name {
  font-weight: 500;
  color: var(--color-sumi);
  max-width: 250px;
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
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-file-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-error);
}

/* Error */
.cv-modal-error {
  padding: var(--space-md);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: 0.875rem;
  margin-bottom: var(--space-lg);
}

/* Actions */
.cv-modal-actions {
  margin-bottom: var(--space-lg);
}

.cv-submit-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.cv-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Info Text */
.cv-modal-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
  margin: 0;
}

.cv-modal-info svg {
  flex-shrink: 0;
  opacity: 0.6;
}

/* Transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-active .cv-modal,
.modal-fade-leave-active .cv-modal {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .cv-modal,
.modal-fade-leave-to .cv-modal {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

/* Responsive */
@media (max-width: 480px) {
  .cv-modal {
    padding: var(--space-lg);
    margin: var(--space-md);
  }

  .cv-modal-header h2 {
    font-size: 1.25rem;
  }

  .cv-drop-zone {
    padding: var(--space-lg);
  }

  .file-name {
    max-width: 180px;
  }
}
</style>
