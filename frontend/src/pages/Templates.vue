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
        <div class="manual-form zen-card">
          <div class="form-header">
            <h2>{{ editingTemplate ? 'Template bearbeiten' : 'Neues Template erstellen' }}</h2>
            <p class="form-subtitle">
              Verwenden Sie Platzhalter wie {{FIRMA}}, {{POSITION}}, {{ANSPRECHPARTNER}}
            </p>
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
              Markiere Text und wähle eine Variable aus der Liste, um dynamische Platzhalter einzufügen.
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
      </section>

      <!-- Messages -->
      <div v-if="message" :class="['alert', `alert-${messageClass}`, 'animate-fade-up']" style="margin-top: var(--space-lg);">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
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
  suggestions.value = [] // Clear suggestions when editing existing template
  showManualForm.value = true
  showWizard.value = false
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
    const { data } = await api.get('/templates')
    templates.value = data.templates
  } catch (err) {
    console.error('Fehler beim Laden:', err)
  }
}

const checkLebenslauf = async () => {
  try {
    const { data } = await api.get('/documents')
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

.manual-form {
  padding: var(--space-xl);
}

.form-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.form-header h2 {
  font-size: 1.75rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.form-subtitle {
  color: var(--color-text-secondary);
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
   BADGES
   ======================================== */
.badge-success {
  background: var(--color-koke);
  color: var(--color-washi);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 968px) {
  .create-options {
    grid-template-columns: 1fr;
  }

  .tone-grid {
    grid-template-columns: 1fr;
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
