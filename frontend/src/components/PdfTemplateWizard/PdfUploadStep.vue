<template>
  <div class="pdf-upload-step">
    <div class="upload-header">
      <div class="step-marker">01</div>
      <h3>PDF-Vorlage hochladen</h3>
      <p class="upload-hint">
        {{ t('components.pdfUpload.uploadDescription') }}
      </p>
    </div>

    <!-- Drop Zone -->
    <div
      class="drop-zone"
      :class="{
        'drag-over': isDragOver,
        'has-file': selectedFile,
        'has-error': errorMessage
      }"
      @dragenter.prevent="handleDragEnter"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="openFileDialog"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,application/pdf"
        class="file-input-hidden"
        @change="handleFileChange"
      />

      <!-- Empty State -->
      <div v-if="!selectedFile" class="drop-zone-content">
        <div class="drop-zone-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
          </svg>
        </div>
        <p class="drop-zone-text">
          <strong>Klicken</strong> oder <strong>PDF hierher ziehen</strong>
        </p>
        <p class="drop-zone-hint">
          Nur PDF-Dateien, max. 10 MB
        </p>
      </div>

      <!-- File Selected State -->
      <div v-else class="drop-zone-content file-selected">
        <div class="file-info">
          <div class="file-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="file-details">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
          </div>
          <button
            type="button"
            class="file-remove"
            @click.stop="removeFile"
            title="Datei entfernen"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <p class="change-file-hint">Klicken, um eine andere Datei auszuwaehlen</p>
      </div>
    </div>

    <!-- Error Message -->
    <Transition name="fade">
      <div v-if="errorMessage" class="upload-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>{{ errorMessage }}</span>
      </div>
    </Transition>

    <!-- File Requirements -->
    <div class="upload-requirements">
      <h4>Anforderungen:</h4>
      <ul>
        <li>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          PDF-Format (.pdf)
        </li>
        <li>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ t('components.pdfUpload.maxSize') }}
        </li>
        <li>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Textbasiertes PDF (keine Scans)
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits(['file-selected'])

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragOver = ref(false)
const errorMessage = ref('')

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

function openFileDialog() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (file) {
    validateAndSelectFile(file)
  }
  // Reset input so same file can be selected again
  event.target.value = ''
}

function handleDragEnter(event) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragOver(event) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(event) {
  event.preventDefault()
  // Only set to false if leaving the drop zone entirely
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragOver.value = false
  }
}

function handleDrop(event) {
  event.preventDefault()
  isDragOver.value = false

  const file = event.dataTransfer?.files?.[0]
  if (file) {
    validateAndSelectFile(file)
  }
}

function validateAndSelectFile(file) {
  errorMessage.value = ''

  // Check file type
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    errorMessage.value = 'Bitte waehlen Sie eine PDF-Datei aus.'
    return
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    errorMessage.value = `${t('components.pdfUpload.fileTooLarge')} ${formatFileSize(MAX_FILE_SIZE)}.`
    return
  }

  // Check if file is empty
  if (file.size === 0) {
    errorMessage.value = 'Die Datei ist leer. Bitte waehlen Sie eine gueltige PDF-Datei.'
    return
  }

  selectedFile.value = file
  emit('file-selected', file)
}

function removeFile() {
  selectedFile.value = null
  errorMessage.value = ''
  emit('file-selected', null)
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.pdf-upload-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg, 1.5rem);
}

.upload-header {
  text-align: center;
}

.step-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-ai, #3D5A6C);
  color: var(--color-text-inverse, #FAF8F3);
  border-radius: 50%;
  font-weight: 500;
  font-size: 0.875rem;
  margin-bottom: var(--space-md, 1rem);
}

.upload-header h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-sm, 0.5rem);
}

.upload-hint {
  color: var(--color-text-secondary, #4A4A4A);
  font-size: 0.9375rem;
  max-width: 400px;
  margin: 0 auto;
  line-height: var(--leading-relaxed, 1.85);
}

/* Drop Zone */
.drop-zone {
  position: relative;
  border: 2px dashed var(--color-border, #D4C9BA);
  border-radius: var(--radius-lg, 0.75rem);
  padding: var(--space-xl, 2rem);
  background: var(--color-washi, #FAF8F3);
  cursor: pointer;
  transition: all var(--transition-base, 350ms ease);
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-zone:hover {
  border-color: var(--color-ai, #3D5A6C);
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.04));
}

.drop-zone.drag-over {
  border-color: var(--color-ai, #3D5A6C);
  border-style: solid;
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.08));
  transform: scale(1.01);
}

.drop-zone.has-file {
  border-style: solid;
  border-color: var(--color-success, #7A8B6E);
  background: var(--color-success-light, rgba(122, 139, 110, 0.08));
}

.drop-zone.has-error {
  border-color: var(--color-error, #B87A6E);
}

.file-input-hidden {
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

.drop-zone-content {
  text-align: center;
}

.drop-zone-icon {
  color: var(--color-stone, #9B958F);
  margin-bottom: var(--space-md, 1rem);
  transition: color var(--transition-subtle, 200ms ease);
}

.drop-zone:hover .drop-zone-icon,
.drop-zone.drag-over .drop-zone-icon {
  color: var(--color-ai, #3D5A6C);
}

.drop-zone-text {
  font-size: 1rem;
  color: var(--color-text-primary, #2C2C2C);
  margin-bottom: var(--space-xs, 0.25rem);
}

.drop-zone-text strong {
  color: var(--color-ai, #3D5A6C);
}

.drop-zone-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary, #6B6B6B);
}

/* File Selected State */
.file-selected {
  width: 100%;
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--space-md, 1rem);
  padding: var(--space-md, 1rem);
  background: var(--color-washi-cream, #FAF8F3);
  border-radius: var(--radius-md, 0.5rem);
  border: 1px solid var(--color-success, #7A8B6E);
}

.file-icon {
  color: var(--color-success, #7A8B6E);
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs, 0.25rem);
  text-align: left;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary, #6B6B6B);
}

.file-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--color-border, #D4C9BA);
  border-radius: 50%;
  color: var(--color-text-tertiary, #6B6B6B);
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
  flex-shrink: 0;
}

.file-remove:hover {
  background: var(--color-error-light, rgba(184, 122, 110, 0.15));
  border-color: var(--color-error, #B87A6E);
  color: var(--color-error, #B87A6E);
}

.change-file-hint {
  margin-top: var(--space-sm, 0.5rem);
  font-size: 0.8125rem;
  color: var(--color-text-ghost, #8A8A8A);
}

/* Error Message */
.upload-error {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  padding: var(--space-md, 1rem);
  background: var(--color-error-light, rgba(184, 122, 110, 0.1));
  border: 1px solid var(--color-error, #B87A6E);
  border-radius: var(--radius-md, 0.5rem);
  color: var(--color-error, #B87A6E);
  font-size: 0.875rem;
}

/* Requirements */
.upload-requirements {
  padding: var(--space-lg, 1.5rem);
  background: var(--color-washi-warm, #F2EDE3);
  border-radius: var(--radius-md, 0.5rem);
}

.upload-requirements h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-md, 1rem);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.upload-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 0.5rem);
}

.upload-requirements li {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  font-size: 0.9375rem;
  color: var(--color-text-secondary, #4A4A4A);
}

.upload-requirements li svg {
  color: var(--color-success, #7A8B6E);
  flex-shrink: 0;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
