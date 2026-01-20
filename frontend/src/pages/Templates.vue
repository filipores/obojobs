<template>
  <div class="templates-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Templates</h1>
        <p class="page-subtitle">
          Erstellen Sie individuelle Anschreiben-Vorlagen mit KI-Unterstützung oder manuell.
        </p>
      </section>

      <!-- Warning Banner -->
      <div v-if="!hasLebenslauf" class="alert alert-warning animate-fade-up" style="animation-delay: 100ms;">
        <div class="alert-content">
          <strong>Lebenslauf fehlt</strong>
          <p>Ohne hochgeladenen Lebenslauf kann kein individualisiertes Anschreiben generiert werden.</p>
        </div>
        <router-link to="/documents" class="zen-btn zen-btn-sm">
          Lebenslauf hochladen
        </router-link>
      </div>

      <!-- Existing Templates -->
      <section v-if="templates.length > 0" class="templates-section animate-fade-up" style="animation-delay: 150ms;">
        <h2 class="section-title">Ihre Templates</h2>
        <div class="templates-grid">
          <div
            v-for="template in templates"
            :key="template.id"
            class="template-card zen-card stagger-item"
          >
            <div class="template-header">
              <div class="template-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </div>
              <div class="template-title-group">
                <h3>{{ template.name }}</h3>
                <span v-if="template.is_default" class="badge badge-success">Standard</span>
              </div>
            </div>

            <div class="template-preview">
              <p>{{ template.content.substring(0, 180) }}...</p>
            </div>

            <div class="template-meta">
              <span class="meta-item">{{ formatDate(template.created_at) }}</span>
              <span class="meta-divider"></span>
              <span class="meta-item">{{ template.content.length }} Zeichen</span>
            </div>

            <div class="template-actions">
              <button @click="editTemplate(template)" class="zen-btn zen-btn-sm">
                Bearbeiten
              </button>
              <button
                v-if="!template.is_default"
                @click="setDefault(template.id)"
                class="zen-btn zen-btn-sm"
              >
                Als Standard
              </button>
              <button @click="deleteTemplate(template.id)" class="zen-btn zen-btn-sm zen-btn-danger" aria-label="Template löschen" title="Template löschen">
                Löschen
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Empty State for No Templates -->
      <section v-if="templates.length === 0 && !showWizard && !showManualForm" class="empty-state-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="empty-state-card zen-card zen-card-featured">
          <div class="empty-state-content">
            <div class="empty-state-illustration">
              <svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Template document -->
                <rect x="20" y="10" width="60" height="80" rx="4" fill="var(--color-bg-elevated)" stroke="var(--color-ai)" stroke-width="2"/>
                <!-- Header area -->
                <rect x="28" y="18" width="44" height="12" rx="2" fill="var(--color-ai-subtle)"/>
                <!-- Content lines with variable placeholders -->
                <line x1="28" y1="40" x2="72" y2="40" stroke="var(--color-sand)" stroke-width="2" stroke-linecap="round"/>
                <rect x="28" y="48" width="20" height="6" rx="2" fill="var(--color-ai)" opacity="0.6"/>
                <line x1="52" y1="51" x2="72" y2="51" stroke="var(--color-sand)" stroke-width="2" stroke-linecap="round"/>
                <line x1="28" y1="62" x2="65" y2="62" stroke="var(--color-sand)" stroke-width="2" stroke-linecap="round"/>
                <rect x="28" y="70" width="16" height="6" rx="2" fill="var(--color-ai)" opacity="0.6"/>
                <line x1="48" y1="73" x2="72" y2="73" stroke="var(--color-sand)" stroke-width="2" stroke-linecap="round"/>
                <!-- Sparkle/AI indicator -->
                <circle cx="80" cy="20" r="12" fill="var(--color-ai)"/>
                <path d="M80 14v12M74 20h12" stroke="var(--color-washi)" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>Noch kein Template vorhanden</h3>
            <p>
              Erstellen Sie Ihr erstes Anschreiben-Template. Mit Platzhaltern wie <code v-pre>{{FIRMA}}</code> und <code v-pre>{{POSITION}}</code> werden Ihre Bewerbungen automatisch personalisiert.
            </p>
          </div>
        </div>
      </section>

      <!-- Ink Stroke Divider -->
      <div class="ink-stroke"></div>

      <!-- Create New Template -->
      <section v-if="!showWizard && !showManualForm" class="create-section animate-fade-up">
        <h2 class="section-title">Neues Template erstellen</h2>
        <div class="create-options">
          <div class="option-card zen-card" @click="startManual">
            <div class="option-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </div>
            <h3>Selbst schreiben</h3>
            <p>Erstellen Sie Ihr eigenes Template von Grund auf mit Platzhaltern</p>
            <span class="zen-btn zen-btn-ai zen-btn-sm">Jetzt erstellen</span>
          </div>

          <div
            class="option-card zen-card"
            :class="{ disabled: !hasLebenslauf }"
            @click="startWizard"
          >
            <div class="option-icon option-icon-ai">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
            </div>
            <h3>Mit KI erstellen</h3>
            <p>Beantworten Sie ein paar Fragen und lassen Sie Claude ein Template generieren</p>
            <span
              class="zen-btn zen-btn-ai zen-btn-sm"
              :class="{ disabled: !hasLebenslauf }"
            >
              {{ hasLebenslauf ? 'Wizard starten' : 'Lebenslauf erforderlich' }}
            </span>
          </div>
        </div>
      </section>

      <!-- AI Wizard -->
      <section v-if="showWizard" class="wizard-section animate-fade-up">
        <div class="wizard zen-card">
          <div class="wizard-header">
            <h2>Template mit KI erstellen</h2>
            <p class="wizard-subtitle">Beantworten Sie ein paar Fragen - Stichpunkte reichen.</p>

            <!-- Progress -->
            <div class="wizard-progress">
              <div class="wizard-progress-bar">
                <div class="wizard-progress-fill" :style="{ width: `${(wizardStep / 5) * 100}%` }"></div>
              </div>
              <span class="wizard-step-text">Schritt {{ wizardStep }} von 5</span>
            </div>
          </div>

          <!-- Wizard Steps -->
          <div class="wizard-content">
            <!-- Step 1: Arbeitssektor -->
            <div v-if="wizardStep === 1" class="wizard-question animate-fade-up">
              <div class="question-marker">01</div>
              <h3>In welchem Arbeitssektor möchten Sie sich bewerben?</h3>
              <p class="question-hint">z.B. "Software-Entwicklung", "Marketing", "Finanzen"</p>
              <input
                v-model="wizardData.sektor"
                type="text"
                placeholder="Software-Entwicklung"
                class="form-input"
                autofocus
              />
            </div>

            <!-- Step 2: Projekte -->
            <div v-if="wizardStep === 2" class="wizard-question animate-fade-up">
              <div class="question-marker">02</div>
              <h3>Welche Projekte oder Erfolge hatten Sie bei vorherigen Jobs?</h3>
              <p class="question-hint">2-3 Stichpunkte reichen!</p>
              <textarea
                v-model="wizardData.projekte"
                placeholder="- Web-App mit 10.000+ Nutzern entwickelt&#10;- API-Performance um 50% verbessert"
                rows="5"
                class="form-textarea"
              ></textarea>
            </div>

            <!-- Step 3: Leidenschaften -->
            <div v-if="wizardStep === 3" class="wizard-question animate-fade-up">
              <div class="question-marker">03</div>
              <h3>Was macht Ihnen in Ihrer Arbeit besonders Spaß?</h3>
              <p class="question-hint">Was treibt Sie an?</p>
              <textarea
                v-model="wizardData.leidenschaften"
                placeholder="- Benutzerfreundliche Software entwickeln&#10;- Im Team kreative Lösungen finden"
                rows="4"
                class="form-textarea"
              ></textarea>
            </div>

            <!-- Step 4: Hobbys -->
            <div v-if="wizardStep === 4" class="wizard-question animate-fade-up">
              <div class="question-marker">04</div>
              <h3>Haben Sie relevante Hobbys oder Interessen?</h3>
              <p class="question-hint">Optional - Nur wenn es zum Job passt!</p>
              <textarea
                v-model="wizardData.hobbys"
                placeholder="- Open-Source Projekte&#10;- Tech-Meetups organisieren"
                rows="3"
                class="form-textarea"
              ></textarea>
            </div>

            <!-- Step 5: Tonalität -->
            <div v-if="wizardStep === 5" class="wizard-question animate-fade-up">
              <div class="question-marker">05</div>
              <h3>Wie soll Ihr Anschreiben klingen?</h3>
              <p class="question-hint">Wählen Sie einen Stil</p>

              <div class="tone-grid">
                <label class="tone-card" :class="{ selected: wizardData.tonalitaet === 'formal' }">
                  <input type="radio" v-model="wizardData.tonalitaet" value="formal" />
                  <h4>Formal</h4>
                  <p>Professionell, höflich, klassisch</p>
                  <span class="tone-hint">Banken, Behörden, Konzerne</span>
                </label>

                <label class="tone-card" :class="{ selected: wizardData.tonalitaet === 'modern' }">
                  <input type="radio" v-model="wizardData.tonalitaet" value="modern" />
                  <h4>Modern</h4>
                  <p>Professionell aber locker</p>
                  <span class="tone-hint">Startups, Agenturen</span>
                </label>

                <label class="tone-card" :class="{ selected: wizardData.tonalitaet === 'kreativ' }">
                  <input type="radio" v-model="wizardData.tonalitaet" value="kreativ" />
                  <h4>Kreativ</h4>
                  <p>Persönlich, authentisch</p>
                  <span class="tone-hint">Kreativagenturen, Design</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Wizard Navigation -->
          <div class="wizard-nav">
            <button
              v-if="wizardStep > 1"
              @click="wizardStep--"
              class="zen-btn"
            >
              Zurück
            </button>
            <button @click="cancelWizard" class="zen-btn">
              Abbrechen
            </button>
            <div class="nav-spacer"></div>
            <button
              v-if="wizardStep < 5"
              @click="wizardStep++"
              :disabled="!isStepValid"
              class="zen-btn zen-btn-ai"
            >
              Weiter
            </button>
            <button
              v-if="wizardStep === 5"
              @click="generateWithAI"
              :disabled="generating || !wizardData.tonalitaet"
              class="zen-btn zen-btn-filled"
            >
              {{ generating ? 'Generiere...' : 'Template generieren' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Manual Form -->
      <section v-if="showManualForm" class="manual-section animate-fade-up">
        <div class="template-editor-layout">
          <!-- Editor Column -->
          <div class="manual-form zen-card">
            <div class="form-header">
              <div class="header-content">
                <h2>{{ editingTemplate ? 'Template bearbeiten' : 'Neues Template erstellen' }}</h2>
                <p class="form-subtitle">
                  Verwenden Sie Platzhalter wie <span v-pre>{{FIRMA}}, {{POSITION}}, {{ANSPRECHPARTNER}}</span>
                </p>
              </div>
              <!-- Auto-save status indicator -->
              <div v-if="editingTemplate" class="auto-save-indicator">
                <span v-if="autoSaveStatus === 'saving'" class="status-saving">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="40" stroke-dashoffset="10">
                      <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                    </circle>
                  </svg>
                  Speichern...
                </span>
                <span v-else-if="autoSaveStatus === 'saved'" class="status-saved">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Gespeichert
                </span>
                <span v-else-if="autoSaveStatus === 'error'" class="status-error">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                  </svg>
                  Fehler
                </span>
                <span v-else-if="hasUnsavedChanges" class="status-unsaved">
                  Ungespeicherte Änderungen
                </span>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Template-Name</label>
              <input
                v-model="form.name"
                type="text"
                placeholder="z.B. 'Standard Anschreiben'"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label class="form-label">Anschreiben-Text</label>
              <p class="editor-hint">
                Markiere Text und wähle eine Variable aus der Liste, oder ziehe Variablen per Drag & Drop in den Editor.
              </p>
              <TemplateEditor
                v-model="form.content"
                :suggestions="suggestions"
                placeholder="Sehr geehrte Damen und Herren,

mit großem Interesse habe ich Ihre Stellenausschreibung gelesen..."
                @suggestion-accepted="onSuggestionAccepted"
                @suggestion-rejected="onSuggestionRejected"
              />
            </div>

            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" v-model="form.is_default" />
                <span>Als Standard-Template setzen</span>
              </label>
            </div>

            <div class="form-actions">
              <button @click="cancelEdit" class="zen-btn">
                Abbrechen
              </button>
              <button
                @click="saveTemplate"
                :disabled="!form.name || !form.content"
                class="zen-btn zen-btn-filled"
              >
                {{ editingTemplate ? 'Aktualisieren' : 'Template erstellen' }}
              </button>
            </div>
          </div>

          <!-- Live Preview Column -->
          <div class="preview-panel zen-card">
            <div class="preview-header">
              <h3>Live-Vorschau</h3>
              <span class="preview-hint">Mit Beispieldaten</span>
            </div>
            <div class="preview-content">
              <div v-if="previewText" class="preview-text">{{ previewText }}</div>
              <div v-else class="preview-empty">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
                <p>Beginnen Sie mit dem Schreiben, um eine Vorschau zu sehen</p>
              </div>
            </div>
            <div class="preview-legend">
              <span class="legend-title">Beispieldaten:</span>
              <div class="legend-items">
                <span class="legend-item"><strong>Firma:</strong> {{ previewData.FIRMA }}</span>
                <span class="legend-item"><strong>Position:</strong> {{ previewData.POSITION }}</span>
                <span class="legend-item"><strong>Ansprechpartner:</strong> {{ previewData.ANSPRECHPARTNER }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Messages -->
      <div v-if="message" :class="['alert', `alert-${messageClass}`, 'animate-fade-up']" style="margin-top: var(--space-lg);">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import api from '../api/client'
import { TemplateEditor } from '../components/TemplateEditor'
import { confirm } from '../composables/useConfirm'

const templates = ref([])
const hasLebenslauf = ref(false)
const showWizard = ref(false)
const showManualForm = ref(false)
const editingTemplate = ref(null)
const generating = ref(false)
const message = ref('')
const messageClass = ref('')

const wizardStep = ref(1)
const wizardData = ref({
  sektor: '',
  projekte: '',
  leidenschaften: '',
  hobbys: '',
  tonalitaet: ''
})

const form = ref({
  name: '',
  content: '',
  is_default: false
})

const suggestions = ref([])

// Auto-save state
let autoSaveInterval = null
const lastSavedContent = ref('')
const autoSaveStatus = ref('') // '', 'saving', 'saved', 'error'
const hasUnsavedChanges = computed(() => {
  return showManualForm.value && editingTemplate.value &&
    (form.value.content !== lastSavedContent.value || form.value.name !== editingTemplate.value.name)
})

// Example data for live preview
const previewData = {
  FIRMA: 'Muster GmbH',
  POSITION: 'Software-Entwickler',
  ANSPRECHPARTNER: 'Frau Müller',
  QUELLE: 'LinkedIn',
  EINLEITUNG: 'Mit großem Interesse habe ich Ihre Stellenausschreibung auf LinkedIn entdeckt und möchte mich bei Ihnen als engagierter Software-Entwickler bewerben.'
}

// Computed preview text
const previewText = computed(() => {
  if (!form.value.content) return ''
  let text = form.value.content
  for (const [key, value] of Object.entries(previewData)) {
    text = text.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value)
  }
  return text
})

const isStepValid = computed(() => {
  switch (wizardStep.value) {
    case 1: return wizardData.value.sektor.trim().length > 0
    case 2: return wizardData.value.projekte.trim().length > 0
    case 3: return wizardData.value.leidenschaften.trim().length > 0
    case 4: return true // Optional
    case 5: return wizardData.value.tonalitaet !== ''
    default: return false
  }
})

// Auto-save function
const autoSave = async () => {
  if (!editingTemplate.value || !form.value.name || !form.value.content) return
  if (!hasUnsavedChanges.value) return

  try {
    autoSaveStatus.value = 'saving'
    await api.silent.put(`/templates/${editingTemplate.value.id}`, form.value)
    lastSavedContent.value = form.value.content
    autoSaveStatus.value = 'saved'
    // Reset status after 3 seconds
    setTimeout(() => {
      if (autoSaveStatus.value === 'saved') {
        autoSaveStatus.value = ''
      }
    }, 3000)
  } catch (_e) {
    autoSaveStatus.value = 'error'
  }
}

// Start auto-save interval when editing
const startAutoSave = () => {
  stopAutoSave()
  autoSaveInterval = setInterval(autoSave, 30000) // 30 seconds
}

const stopAutoSave = () => {
  if (autoSaveInterval) {
    clearInterval(autoSaveInterval)
    autoSaveInterval = null
  }
  autoSaveStatus.value = ''
}

// Watch for manual form opening to start/stop auto-save
watch(showManualForm, (newVal) => {
  if (newVal && editingTemplate.value) {
    lastSavedContent.value = form.value.content
    startAutoSave()
  } else {
    stopAutoSave()
  }
})

const startWizard = () => {
  if (!hasLebenslauf.value) return
  showWizard.value = true
  showManualForm.value = false
  wizardStep.value = 1
  wizardData.value = {
    sektor: '',
    projekte: '',
    leidenschaften: '',
    hobbys: '',
    tonalitaet: ''
  }
}

const startManual = () => {
  showManualForm.value = true
  showWizard.value = false
  editingTemplate.value = null
  form.value = { name: '', content: '', is_default: false }
}

const cancelWizard = () => {
  showWizard.value = false
}

const cancelEdit = () => {
  stopAutoSave()
  showManualForm.value = false
  editingTemplate.value = null
  form.value = { name: '', content: '', is_default: false }
  suggestions.value = []
}

const generateWithAI = async () => {
  generating.value = true
  message.value = ''

  try {
    const { data } = await api.post('/templates/generate', wizardData.value)

    form.value = {
      name: data.template.name,
      content: data.template.content,
      is_default: true
    }
    editingTemplate.value = data.template

    // Apply AI suggestions if available
    if (data.template.suggestions && data.template.suggestions.length > 0) {
      suggestions.value = data.template.suggestions
    } else {
      suggestions.value = []
    }

    showWizard.value = false
    showManualForm.value = true

    message.value = 'Template erfolgreich generiert! Sie können es jetzt anpassen.'
    messageClass.value = 'success'

    await loadTemplates()
  } catch (e) {
    message.value = e.response?.data?.error || 'Fehler beim Generieren des Templates'
    messageClass.value = 'error'
  } finally {
    generating.value = false
  }
}

const saveTemplate = async () => {
  try {
    if (editingTemplate.value) {
      await api.put(`/templates/${editingTemplate.value.id}`, form.value)
      message.value = 'Template aktualisiert!'
    } else {
      await api.post('/templates', form.value)
      message.value = 'Template erstellt!'
    }
    messageClass.value = 'success'
    cancelEdit()
    await loadTemplates()
  } catch (e) {
    message.value = e.response?.data?.error || 'Fehler beim Speichern'
    messageClass.value = 'error'
  }
}

const editTemplate = (template) => {
  editingTemplate.value = template
  form.value = {
    name: template.name,
    content: template.content,
    is_default: template.is_default
  }
  lastSavedContent.value = template.content
  suggestions.value = [] // Clear suggestions when editing existing template
  showManualForm.value = true
  showWizard.value = false
  startAutoSave()
}

const onSuggestionAccepted = (suggestionId) => {
  // Remove the accepted suggestion from the list
  suggestions.value = suggestions.value.filter(s => s.id !== suggestionId)
}

const onSuggestionRejected = (suggestionId) => {
  // Remove the rejected suggestion from the list
  suggestions.value = suggestions.value.filter(s => s.id !== suggestionId)
}

const deleteTemplate = async (id) => {
  const confirmed = await confirm({
    title: 'Template löschen',
    message: 'Möchten Sie dieses Template wirklich löschen?',
    confirmText: 'Löschen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/templates/${id}`)
    await loadTemplates()
    message.value = 'Template gelöscht!'
    messageClass.value = 'success'
  } catch (_e) {
    message.value = 'Fehler beim Löschen'
    messageClass.value = 'error'
  }
}

const setDefault = async (id) => {
  try {
    await api.put(`/templates/${id}/default`)
    await loadTemplates()
    message.value = 'Standard-Template gesetzt!'
    messageClass.value = 'success'
  } catch (_e) {
    message.value = 'Fehler'
    messageClass.value = 'error'
  }
}

const loadTemplates = async () => {
  try {
    const { data } = await api.silent.get('/templates')
    templates.value = data.templates
  } catch (err) {
    console.error('Fehler beim Laden:', err)
  }
}

const checkLebenslauf = async () => {
  try {
    const { data } = await api.silent.get('/documents')
    hasLebenslauf.value = data.documents.some(doc => doc.doc_type === 'lebenslauf')
  } catch (err) {
    console.error('Fehler beim Prüfen:', err)
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
  loadTemplates()
  checkLebenslauf()
})

onUnmounted(() => {
  stopAutoSave()
})
</script>

<style scoped>
.templates-page {
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
   SECTION STYLES
   ======================================== */
.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.templates-section {
  margin-bottom: var(--space-ma);
}

/* ========================================
   TEMPLATES GRID
   ======================================== */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--space-lg);
}

.template-card {
  padding: var(--space-lg);
}

.template-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.template-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.template-title-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.template-title-group h3 {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0;
}

.template-preview {
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
  min-height: 80px;
}

.template-preview p {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-md);
}

.meta-divider {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-sand);
}

.template-actions {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

/* ========================================
   CREATE SECTION
   ======================================== */
.create-section {
  margin-top: var(--space-ma);
}

.create-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.option-card {
  padding: var(--space-xl);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-base);
}

.option-card:hover:not(.disabled) {
  border-color: var(--color-ai);
  transform: translateY(-2px);
}

.option-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.option-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-md);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  color: var(--color-stone);
}

.option-icon-ai {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.option-card h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.option-card p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

/* ========================================
   WIZARD SECTION
   ======================================== */
.wizard-section {
  margin-top: var(--space-ma);
}

.wizard {
  padding: var(--space-xl);
}

.wizard-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.wizard-header h2 {
  font-size: 1.75rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.wizard-subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
}

.wizard-progress {
  max-width: 400px;
  margin: 0 auto;
}

.wizard-progress-bar {
  height: 6px;
  background: var(--color-sand);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--space-sm);
}

.wizard-progress-fill {
  height: 100%;
  background: var(--color-ai);
  transition: width var(--transition-smooth);
  border-radius: var(--radius-full);
}

.wizard-step-text {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.wizard-content {
  min-height: 280px;
  margin-bottom: var(--space-xl);
}

.wizard-question {
  max-width: 600px;
  margin: 0 auto;
}

.question-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-ai);
  color: var(--color-text-inverse);
  border-radius: 50%;
  font-weight: 500;
  font-size: 0.875rem;
  margin-bottom: var(--space-md);
}

.wizard-question h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.question-hint {
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
  margin-bottom: var(--space-lg);
}

/* ========================================
   TONE GRID
   ======================================== */
.tone-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.tone-card {
  background: var(--color-washi);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-base);
}

.tone-card:hover {
  border-color: var(--color-ai);
}

.tone-card.selected {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.tone-card input {
  display: none;
}

.tone-card h4 {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.tone-card p {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-sm);
}

.tone-hint {
  font-size: 0.75rem;
  color: var(--color-text-ghost);
}

/* ========================================
   WIZARD NAVIGATION
   ======================================== */
.wizard-nav {
  display: flex;
  gap: var(--space-md);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.nav-spacer {
  flex: 1;
}

/* ========================================
   MANUAL FORM
   ======================================== */
.manual-section {
  margin-top: var(--space-ma);
}

.template-editor-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  align-items: start;
}

.manual-form {
  padding: var(--space-xl);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-xl);
  gap: var(--space-md);
}

.header-content {
  text-align: left;
}

.form-header h2 {
  font-size: 1.75rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.form-subtitle {
  color: var(--color-text-secondary);
}

/* Auto-save indicator */
.auto-save-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  white-space: nowrap;
  flex-shrink: 0;
}

.auto-save-indicator span {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.status-saving {
  color: var(--color-ai);
}

.status-saved {
  color: var(--color-success);
}

.status-error {
  color: var(--color-error);
}

.status-unsaved {
  color: var(--color-text-tertiary);
  font-style: italic;
}

/* Preview Panel */
.preview-panel {
  padding: var(--space-lg);
  position: sticky;
  top: var(--space-lg);
  max-height: calc(100vh - 150px);
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.preview-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin: 0;
}

.preview-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: var(--space-md);
}

.preview-text {
  font-size: 0.9375rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-ghost);
}

.preview-empty svg {
  margin-bottom: var(--space-md);
  opacity: 0.5;
}

.preview-empty p {
  font-size: 0.875rem;
  margin: 0;
}

.preview-legend {
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.legend-title {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-xs);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.legend-item {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.legend-item strong {
  color: var(--color-text-primary);
}

.editor-hint {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-md);
  line-height: var(--leading-relaxed);
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
}

.form-checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-ai);
}

.form-checkbox span {
  font-weight: 500;
  color: var(--color-sumi);
}

.form-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: flex-end;
  margin-top: var(--space-lg);
}

/* ========================================
   EMPTY STATE
   ======================================== */
.empty-state-section {
  margin-bottom: var(--space-ma);
}

.empty-state-card {
  padding: var(--space-xl);
}

.empty-state-content {
  text-align: center;
  max-width: 480px;
  margin: 0 auto;
}

.empty-state-illustration {
  margin-bottom: var(--space-lg);
}

.empty-state-illustration svg {
  opacity: 0.9;
}

.empty-state-content h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-md);
}

.empty-state-content p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

.empty-state-content code {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-family: var(--font-mono, monospace);
}

/* ========================================
   BADGES
   ======================================== */
.badge-success {
  background: var(--color-koke);
  color: var(--color-washi);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 1200px) {
  .template-editor-layout {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
    max-height: none;
  }
}

@media (max-width: 968px) {
  .create-options {
    grid-template-columns: 1fr;
  }

  .tone-grid {
    grid-template-columns: 1fr;
  }

  .form-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .templates-grid {
    grid-template-columns: 1fr;
  }

  .wizard-nav {
    flex-wrap: wrap;
  }

  .form-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }
}
</style>
