<template>
  <div class="documents-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Dokumente</h1>
        <p class="page-subtitle">
          Laden Sie Ihre Bewerbungsunterlagen hoch. Der Text wird automatisch extrahiert.
        </p>
      </section>

      <!-- Progress Section -->
      <section class="progress-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="progress-card zen-card">
          <div class="progress-info">
            <span class="progress-label">Fortschritt</span>
            <span class="progress-count">{{ uploadedCount }} / {{ requiredCount }} Pflichtdokumente</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Documents Grid -->
      <section class="documents-section">
        <div class="documents-grid">
          <!-- Lebenslauf -->
          <div class="document-card zen-card stagger-item" :class="{ 'is-complete': documents.lebenslauf }">
            <div class="document-header">
              <div class="document-icon" :class="{ 'icon-complete': documents.lebenslauf }">
                <svg v-if="documents.lebenslauf" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <div class="document-title-group">
                <h3>Lebenslauf</h3>
                <span class="badge badge-required">Pflichtfeld</span>
              </div>
            </div>

            <p class="document-description">Ihr aktueller Lebenslauf als PDF-Datei</p>

            <!-- Upload Area -->
            <div
              class="upload-zone"
              :class="{
                'has-file': files.lebenslauf,
                'is-uploading': uploading.lebenslauf,
                'is-complete': documents.lebenslauf
              }"
              @dragover.prevent="handleDragOver($event, 'lebenslauf')"
              @dragleave.prevent="handleDragLeave"
              @drop.prevent="handleDrop($event, 'lebenslauf')"
            >
              <input
                type="file"
                accept=".pdf"
                @change="handleFile($event, 'lebenslauf')"
                :id="'upload-lebenslauf'"
                class="file-input"
              />

              <div v-if="!documents.lebenslauf" class="upload-content">
                <div class="upload-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <label :for="'upload-lebenslauf'" class="upload-label">
                  <span v-if="!files.lebenslauf" class="upload-text">
                    <strong>PDF auswählen</strong> oder hierher ziehen
                  </span>
                  <span v-else class="upload-filename">
                    {{ files.lebenslauf.name }}
                  </span>
                </label>
                <button
                  @click="upload('lebenslauf')"
                  :disabled="!files.lebenslauf || uploading.lebenslauf"
                  class="zen-btn zen-btn-ai zen-btn-sm"
                >
                  {{ uploading.lebenslauf ? 'Wird hochgeladen...' : 'Hochladen' }}
                </button>
              </div>

              <div v-else class="uploaded-status">
                <div class="uploaded-info">
                  <p class="uploaded-filename">{{ documents.lebenslauf.original_filename }}</p>
                  <p class="uploaded-date">{{ formatDate(documents.lebenslauf.uploaded_at) }}</p>
                </div>
                <button @click="deleteDoc(documents.lebenslauf.id)" class="zen-btn zen-btn-sm">
                  Löschen
                </button>
              </div>
            </div>

            <!-- Messages -->
            <div v-if="messages.lebenslauf" :class="['alert', `alert-${messageClass.lebenslauf}`]">
              {{ messages.lebenslauf }}
            </div>
          </div>

          <!-- Anschreiben -->
          <div class="document-card zen-card stagger-item" :class="{ 'is-complete': documents.anschreiben }">
            <div class="document-header">
              <div class="document-icon" :class="{ 'icon-complete': documents.anschreiben }">
                <svg v-if="documents.anschreiben" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
              </div>
              <div class="document-title-group">
                <h3>Anschreiben</h3>
                <span class="badge badge-optional">Optional</span>
              </div>
            </div>

            <p class="document-description">Vorgefertigtes Anschreiben als Vorlage</p>

            <div
              class="upload-zone"
              :class="{
                'has-file': files.anschreiben,
                'is-uploading': uploading.anschreiben,
                'is-complete': documents.anschreiben
              }"
              @dragover.prevent="handleDragOver($event, 'anschreiben')"
              @dragleave.prevent="handleDragLeave"
              @drop.prevent="handleDrop($event, 'anschreiben')"
            >
              <input
                type="file"
                accept=".pdf"
                @change="handleFile($event, 'anschreiben')"
                :id="'upload-anschreiben'"
                class="file-input"
              />

              <div v-if="!documents.anschreiben" class="upload-content">
                <div class="upload-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <label :for="'upload-anschreiben'" class="upload-label">
                  <span v-if="!files.anschreiben" class="upload-text">
                    <strong>PDF auswählen</strong> oder hierher ziehen
                  </span>
                  <span v-else class="upload-filename">
                    {{ files.anschreiben.name }}
                  </span>
                </label>
                <button
                  @click="upload('anschreiben')"
                  :disabled="!files.anschreiben || uploading.anschreiben"
                  class="zen-btn zen-btn-ai zen-btn-sm"
                >
                  {{ uploading.anschreiben ? 'Wird hochgeladen...' : 'Hochladen' }}
                </button>
              </div>

              <div v-else class="uploaded-status">
                <div class="uploaded-info">
                  <p class="uploaded-filename">{{ documents.anschreiben.original_filename }}</p>
                  <p class="uploaded-date">{{ formatDate(documents.anschreiben.uploaded_at) }}</p>
                </div>
                <button @click="deleteDoc(documents.anschreiben.id)" class="zen-btn zen-btn-sm">
                  Löschen
                </button>
              </div>
            </div>

            <div v-if="messages.anschreiben" :class="['alert', `alert-${messageClass.anschreiben}`]">
              {{ messages.anschreiben }}
            </div>
          </div>

          <!-- Arbeitszeugnis -->
          <div class="document-card zen-card stagger-item" :class="{ 'is-complete': documents.arbeitszeugnis }">
            <div class="document-header">
              <div class="document-icon" :class="{ 'icon-complete': documents.arbeitszeugnis }">
                <svg v-if="documents.arbeitszeugnis" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M9 11l3 3L22 4"/>
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
              </div>
              <div class="document-title-group">
                <h3>Arbeitszeugnis</h3>
                <span class="badge badge-required">Pflichtfeld</span>
              </div>
            </div>

            <p class="document-description">Ihr aktuellstes Arbeitszeugnis</p>

            <div
              class="upload-zone"
              :class="{
                'has-file': files.arbeitszeugnis,
                'is-uploading': uploading.arbeitszeugnis,
                'is-complete': documents.arbeitszeugnis
              }"
              @dragover.prevent="handleDragOver($event, 'arbeitszeugnis')"
              @dragleave.prevent="handleDragLeave"
              @drop.prevent="handleDrop($event, 'arbeitszeugnis')"
            >
              <input
                type="file"
                accept=".pdf"
                @change="handleFile($event, 'arbeitszeugnis')"
                :id="'upload-arbeitszeugnis'"
                class="file-input"
              />

              <div v-if="!documents.arbeitszeugnis" class="upload-content">
                <div class="upload-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <label :for="'upload-arbeitszeugnis'" class="upload-label">
                  <span v-if="!files.arbeitszeugnis" class="upload-text">
                    <strong>PDF auswählen</strong> oder hierher ziehen
                  </span>
                  <span v-else class="upload-filename">
                    {{ files.arbeitszeugnis.name }}
                  </span>
                </label>
                <button
                  @click="upload('arbeitszeugnis')"
                  :disabled="!files.arbeitszeugnis || uploading.arbeitszeugnis"
                  class="zen-btn zen-btn-ai zen-btn-sm"
                >
                  {{ uploading.arbeitszeugnis ? 'Wird hochgeladen...' : 'Hochladen' }}
                </button>
              </div>

              <div v-else class="uploaded-status">
                <div class="uploaded-info">
                  <p class="uploaded-filename">{{ documents.arbeitszeugnis.original_filename }}</p>
                  <p class="uploaded-date">{{ formatDate(documents.arbeitszeugnis.uploaded_at) }}</p>
                </div>
                <button @click="deleteDoc(documents.arbeitszeugnis.id)" class="zen-btn zen-btn-sm">
                  Löschen
                </button>
              </div>
            </div>

            <div v-if="messages.arbeitszeugnis" :class="['alert', `alert-${messageClass.arbeitszeugnis}`]">
              {{ messages.arbeitszeugnis }}
            </div>
          </div>
        </div>
      </section>

      <!-- Success Banner -->
      <section v-if="isComplete" class="success-section animate-fade-up">
        <div class="success-banner zen-card zen-card-featured">
          <div class="success-content">
            <h3>Alle Pflicht-Dokumente hochgeladen</h3>
            <p>Sie können jetzt Templates erstellen und Bewerbungen generieren.</p>
          </div>
          <router-link to="/templates" class="zen-btn zen-btn-filled">
            Zu den Templates
          </router-link>
        </div>
      </section>

      <!-- Skills Section -->
      <section class="skills-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="ink-stroke"></div>
        <h2 class="section-title">Extrahierte Skills</h2>
        <SkillsOverview />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api/client'
import SkillsOverview from '../components/SkillsOverview.vue'

const documents = ref({
  lebenslauf: null,
  anschreiben: null,
  arbeitszeugnis: null
})

const files = ref({
  lebenslauf: null,
  anschreiben: null,
  arbeitszeugnis: null
})

const uploading = ref({
  lebenslauf: false,
  anschreiben: false,
  arbeitszeugnis: false
})

const messages = ref({
  lebenslauf: '',
  anschreiben: '',
  arbeitszeugnis: ''
})

const messageClass = ref({
  lebenslauf: '',
  anschreiben: '',
  arbeitszeugnis: ''
})

const dragActive = ref(null)

const isComplete = computed(() => {
  return documents.value.lebenslauf && documents.value.arbeitszeugnis
})

const uploadedCount = computed(() => {
  let count = 0
  if (documents.value.lebenslauf) count++
  if (documents.value.arbeitszeugnis) count++
  return count
})

const requiredCount = 2

const uploadProgress = computed(() => {
  return (uploadedCount.value / requiredCount) * 100
})

const handleFile = (e, docType) => {
  files.value[docType] = e.target.files[0]
  messages.value[docType] = ''
}

const handleDragOver = (e, docType) => {
  dragActive.value = docType
}

const handleDragLeave = () => {
  dragActive.value = null
}

const handleDrop = (e, docType) => {
  dragActive.value = null
  const droppedFiles = e.dataTransfer.files
  if (droppedFiles.length > 0 && droppedFiles[0].type === 'application/pdf') {
    files.value[docType] = droppedFiles[0]
    messages.value[docType] = ''
  }
}

const upload = async (docType) => {
  if (!files.value[docType]) return

  const formData = new FormData()
  formData.append('file', files.value[docType])
  formData.append('doc_type', docType)

  uploading.value[docType] = true
  messages.value[docType] = ''

  try {
    const { data } = await api.post('/documents', formData)
    messages.value[docType] = data.message || 'Upload erfolgreich!'
    messageClass.value[docType] = 'success'
    files.value[docType] = null

    // Reset file input
    const input = document.getElementById(`upload-${docType}`)
    if (input) input.value = ''

    await loadDocuments()
  } catch (e) {
    messages.value[docType] = e.response?.data?.error || 'Upload fehlgeschlagen'
    messageClass.value[docType] = 'error'
  } finally {
    uploading.value[docType] = false
  }
}

const deleteDoc = async (id) => {
  if (!confirm('Möchten Sie dieses Dokument wirklich löschen?')) return

  try {
    await api.delete(`/documents/${id}`)
    await loadDocuments()
  } catch (e) {
    alert('Fehler beim Löschen: ' + (e.response?.data?.error || 'Unbekannter Fehler'))
  }
}

const loadDocuments = async () => {
  try {
    const { data } = await api.get('/documents')

    // Reset
    documents.value = {
      lebenslauf: null,
      anschreiben: null,
      arbeitszeugnis: null
    }

    // Map documents by type
    data.documents.forEach(doc => {
      if (doc.doc_type in documents.value) {
        documents.value[doc.doc_type] = doc
      }
    })
  } catch (e) {
    console.error('Fehler beim Laden der Dokumente:', e)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.documents-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

/* ========================================
   PAGE HEADER
   ======================================== */
.page-header {
  padding: var(--space-ma-lg) 0 var(--space-ma);
}

.page-header h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
}

.page-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin-bottom: 0;
}

/* ========================================
   PROGRESS SECTION
   ======================================== */
.progress-section {
  margin-bottom: var(--space-ma);
}

.progress-card {
  padding: var(--space-lg) var(--space-xl);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.progress-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.progress-count {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--color-ai);
  font-weight: 500;
}

.progress-bar {
  height: 6px;
  background: var(--color-sand);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-ai);
  transition: width var(--transition-smooth);
  border-radius: var(--radius-full);
}

/* ========================================
   DOCUMENTS SECTION
   ======================================== */
.documents-section {
  margin-top: var(--space-ma);
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

/* ========================================
   DOCUMENT CARD
   ======================================== */
.document-card {
  padding: var(--space-lg);
  transition: all var(--transition-base);
}

.document-card.is-complete {
  border-color: var(--color-koke);
}

.document-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.document-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  color: var(--color-stone);
  flex-shrink: 0;
  transition: all var(--transition-base);
}

.document-icon.icon-complete {
  background: var(--color-koke);
  color: var(--color-washi);
}

.document-title-group h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
}

.document-description {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

/* ========================================
   BADGES
   ======================================== */
.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.badge-required {
  background: var(--color-terra);
  color: var(--color-washi);
  opacity: 0.9;
}

.badge-optional {
  background: var(--color-sand);
  color: var(--color-sumi-light);
}

/* ========================================
   UPLOAD ZONE
   ======================================== */
.upload-zone {
  border: 2px dashed var(--color-sand);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  transition: all var(--transition-base);
  background: var(--color-washi);
}

.upload-zone:hover {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.upload-zone.has-file {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.upload-zone.is-uploading {
  opacity: 0.6;
  pointer-events: none;
}

.upload-zone.is-complete {
  border-style: solid;
  border-color: var(--color-koke);
  background: rgba(122, 139, 110, 0.05);
}

.file-input {
  display: none;
}

.upload-content {
  text-align: center;
}

.upload-icon {
  color: var(--color-stone);
  margin-bottom: var(--space-md);
  opacity: 0.6;
}

.upload-label {
  display: block;
  margin-bottom: var(--space-md);
  cursor: pointer;
}

.upload-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.upload-text strong {
  color: var(--color-ai);
  font-weight: 500;
}

.upload-filename {
  display: inline-block;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  color: var(--color-sumi);
  font-weight: 500;
}

/* ========================================
   UPLOADED STATUS
   ======================================== */
.uploaded-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.uploaded-info {
  flex: 1;
  min-width: 0;
}

.uploaded-filename {
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uploaded-date {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

/* ========================================
   SUCCESS SECTION
   ======================================== */
.success-section {
  margin-top: var(--space-ma-lg);
}

.success-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-xl);
}

.success-content h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
}

.success-content p {
  font-size: 0.9375rem;
  opacity: 0.8;
  margin-bottom: 0;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 1024px) {
  .documents-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .documents-grid {
    grid-template-columns: 1fr;
  }

  .success-banner {
    flex-direction: column;
    text-align: center;
    gap: var(--space-lg);
  }

  .uploaded-status {
    flex-direction: column;
    text-align: center;
  }

  .uploaded-info {
    text-align: center;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .progress-info {
    flex-direction: column;
    gap: var(--space-sm);
    align-items: flex-start;
  }
}

/* ========================================
   SKILLS SECTION
   ======================================== */
.skills-section {
  margin-top: var(--space-ma);
}

.skills-section .ink-stroke {
  margin-bottom: var(--space-ma);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-lg);
}
</style>
