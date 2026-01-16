<template>
  <div class="salary-coach">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state zen-card">
      <div class="loading-spinner"></div>
      <p>Lade gespeicherte Daten...</p>
    </div>

    <!-- Input Section -->
    <div v-else class="input-section zen-card">
      <h3 class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 1v22"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
        Gehaltsverhandlungs-Coach
      </h3>

      <div class="input-grid">
        <div class="input-group">
          <label for="position">Position</label>
          <input
            id="position"
            v-model="formData.position"
            type="text"
            placeholder="z.B. Software Engineer"
            class="zen-input"
          />
        </div>

        <div class="input-group">
          <label for="region">Region</label>
          <input
            id="region"
            v-model="formData.region"
            type="text"
            placeholder="z.B. Muenchen"
            class="zen-input"
          />
        </div>

        <div class="input-group">
          <label for="experience">Berufserfahrung (Jahre)</label>
          <input
            id="experience"
            v-model.number="formData.experienceYears"
            type="number"
            min="0"
            max="50"
            class="zen-input"
          />
        </div>

        <div class="input-group">
          <label for="targetSalary">Wunschgehalt (EUR)</label>
          <input
            id="targetSalary"
            v-model.number="formData.targetSalary"
            type="number"
            min="0"
            step="1000"
            placeholder="z.B. 65000"
            class="zen-input"
          />
        </div>

        <div class="input-group">
          <label for="currentSalary">Aktuelles Gehalt (optional)</label>
          <input
            id="currentSalary"
            v-model.number="formData.currentSalary"
            type="number"
            min="0"
            step="1000"
            placeholder="z.B. 55000"
            class="zen-input"
          />
        </div>

        <div class="input-group">
          <label for="industry">Branche (optional)</label>
          <input
            id="industry"
            v-model="formData.industry"
            type="text"
            placeholder="z.B. Software, Finance"
            class="zen-input"
          />
        </div>
      </div>

      <div class="action-buttons">
        <button
          @click="researchSalary"
          :disabled="isResearching || !formData.position"
          class="zen-btn"
        >
          <span v-if="isResearching" class="loading-spinner-sm"></span>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
          {{ isResearching ? 'Recherchiere...' : 'Gehalt recherchieren' }}
        </button>

        <button
          @click="getStrategy"
          :disabled="isGenerating || !formData.targetSalary"
          class="zen-btn zen-btn-ai"
        >
          <span v-if="isGenerating" class="loading-spinner-sm"></span>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
          </svg>
          {{ isGenerating ? 'Generiere Strategie...' : 'Verhandlungsstrategie' }}
        </button>
      </div>

      <!-- Autosave indicator -->
      <div v-if="lastSavedAt || isSaving" class="autosave-indicator">
        <svg v-if="isSaving" class="saving-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
          <polyline points="17 21 17 13 7 13 7 21"/>
          <polyline points="7 3 7 8 15 8"/>
        </svg>
        <span v-if="isSaving">Speichere...</span>
        <span v-else>Automatisch gespeichert</span>
      </div>
    </div>

    <!-- Salary Research Results -->
    <div v-if="!isLoading && salaryResearch" class="research-section zen-card animate-fade-up">
      <h3 class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="20" x2="12" y2="10"/>
          <line x1="18" y1="20" x2="18" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="16"/>
        </svg>
        Marktrecherche: {{ salaryResearch.position }}
      </h3>

      <div class="salary-range">
        <div class="range-bar">
          <div class="range-track">
            <div class="range-fill" :style="{ width: '100%' }"></div>
            <div class="range-marker median" :style="{ left: medianPosition + '%' }">
              <span class="marker-label">Median</span>
              <span class="marker-value">{{ formatCurrency(salaryResearch.median_salary) }}</span>
            </div>
          </div>
          <div class="range-labels">
            <span class="range-min">{{ formatCurrency(salaryResearch.min_salary) }}</span>
            <span class="range-max">{{ formatCurrency(salaryResearch.max_salary) }}</span>
          </div>
        </div>
      </div>

      <div class="research-details">
        <div v-if="salaryResearch.factors?.length" class="detail-group">
          <h4>Einflussfaktoren</h4>
          <ul class="factor-list">
            <li v-for="(factor, idx) in salaryResearch.factors" :key="idx">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {{ factor }}
            </li>
          </ul>
        </div>

        <div v-if="salaryResearch.data_sources?.length" class="detail-group">
          <h4>Datenquellen</h4>
          <div class="source-badges">
            <span v-for="(source, idx) in salaryResearch.data_sources" :key="idx" class="source-badge">
              {{ source }}
            </span>
          </div>
        </div>

        <div v-if="salaryResearch.notes" class="detail-group">
          <h4>Hinweise</h4>
          <p class="notes-text">{{ salaryResearch.notes }}</p>
        </div>
      </div>
    </div>

    <!-- Negotiation Strategy -->
    <div v-if="!isLoading && strategy" class="strategy-section animate-fade-up">
      <!-- Recommended Range Card -->
      <div class="range-card zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          Empfohlene Verhandlungsspanne
        </h3>
        <div class="recommended-range">
          <div class="range-value min">
            <span class="label">Untergrenze</span>
            <span class="value">{{ formatCurrency(strategy.recommended_range.min) }}</span>
          </div>
          <div class="range-arrow">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </div>
          <div class="range-value max">
            <span class="label">Obergrenze</span>
            <span class="value">{{ formatCurrency(strategy.recommended_range.max) }}</span>
          </div>
        </div>
      </div>

      <!-- Opening Statement -->
      <div class="opening-card zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Eroeffnungsstatement
        </h3>
        <blockquote class="opening-quote">
          "{{ strategy.opening_statement }}"
        </blockquote>
      </div>

      <!-- Tips by Category -->
      <div class="tips-section zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          Verhandlungstipps
        </h3>

        <!-- Category Filter -->
        <div class="category-tabs">
          <button
            v-for="cat in tipCategories"
            :key="cat.key"
            :class="['category-tab', { active: activeCategory === cat.key }]"
            @click="activeCategory = cat.key"
          >
            {{ cat.label }} ({{ getTipsForCategory(cat.key).length }})
          </button>
        </div>

        <!-- Tips List -->
        <div class="tips-list">
          <div
            v-for="tip in filteredTips"
            :key="tip.title"
            class="tip-card"
            :class="['priority-' + tip.priority]"
          >
            <div class="tip-header">
              <span :class="['priority-badge', 'priority-' + tip.priority]">
                {{ tip.priority === 'high' ? 'Wichtig' : tip.priority === 'medium' ? 'Mittel' : 'Info' }}
              </span>
              <h4>{{ tip.title }}</h4>
            </div>
            <p class="tip-description">{{ tip.description }}</p>
            <div v-if="tip.example_script" class="tip-script">
              <span class="script-label">Beispiel-Formulierung:</span>
              <p>"{{ tip.example_script }}"</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Counter Arguments -->
      <div class="arguments-section zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          Ihre Argumente
        </h3>
        <ul class="arguments-list">
          <li v-for="(arg, idx) in strategy.counter_arguments" :key="idx">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ arg }}
          </li>
        </ul>
      </div>

      <!-- Fallback Positions -->
      <div class="fallback-section zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          Fallback-Positionen
        </h3>
        <p class="fallback-intro">Falls das Grundgehalt nicht verhandelbar ist:</p>
        <ul class="fallback-list">
          <li v-for="(fallback, idx) in strategy.fallback_positions" :key="idx">
            <span class="fallback-number">{{ idx + 1 }}</span>
            {{ fallback }}
          </li>
        </ul>
      </div>

      <!-- Common Objections -->
      <div v-if="strategy.common_objections?.length" class="objections-section zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Typische Einwaende und Antworten
        </h3>
        <div class="objections-list">
          <div v-for="(obj, idx) in strategy.common_objections" :key="idx" class="objection-item">
            <div class="objection">
              <span class="objection-label">Einwand:</span>
              <p>"{{ obj.objection }}"</p>
            </div>
            <div class="response">
              <span class="response-label">Ihre Antwort:</span>
              <p>"{{ obj.response }}"</p>
            </div>
          </div>
        </div>
      </div>

      <!-- German Culture Notes -->
      <div v-if="strategy.german_culture_notes?.length" class="culture-section zen-card">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
            <line x1="4" y1="22" x2="4" y2="15"/>
          </svg>
          Kulturelle Hinweise (Deutschland)
        </h3>
        <ul class="culture-list">
          <li v-for="(note, idx) in strategy.german_culture_notes" :key="idx">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            {{ note }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!isLoading && !salaryResearch && !strategy && !isResearching && !isGenerating" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 1v22"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
      </div>
      <p>Geben Sie Ihre Daten ein und klicken Sie auf "Gehalt recherchieren" oder "Verhandlungsstrategie".</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, watch, onMounted } from 'vue'
import api from '../api/client'

const props = defineProps({
  initialPosition: {
    type: String,
    default: ''
  },
  initialCompany: {
    type: String,
    default: ''
  }
})

const formData = ref({
  position: props.initialPosition || '',
  region: 'Deutschland',
  experienceYears: 3,
  targetSalary: null,
  currentSalary: null,
  industry: ''
})

const isResearching = ref(false)
const isGenerating = ref(false)
const isLoading = ref(true)
const isSaving = ref(false)
const salaryResearch = ref(null)
const strategy = ref(null)
const activeCategory = ref('all')
const hasLoadedData = ref(false)
const lastSavedAt = ref(null)

const tipCategories = [
  { key: 'all', label: 'Alle' },
  { key: 'preparation', label: 'Vorbereitung' },
  { key: 'opening', label: 'Eroeffnung' },
  { key: 'counter', label: 'Gegenargumente' },
  { key: 'closing', label: 'Abschluss' },
  { key: 'timing', label: 'Timing' }
]

const medianPosition = computed(() => {
  if (!salaryResearch.value) return 50
  const { min_salary, max_salary, median_salary } = salaryResearch.value
  const range = max_salary - min_salary
  if (range === 0) return 50
  return ((median_salary - min_salary) / range) * 100
})

const filteredTips = computed(() => {
  if (!strategy.value?.tips) return []
  if (activeCategory.value === 'all') return strategy.value.tips
  return strategy.value.tips.filter(t => t.category === activeCategory.value)
})

const getTipsForCategory = (category) => {
  if (!strategy.value?.tips) return []
  if (category === 'all') return strategy.value.tips
  return strategy.value.tips.filter(t => t.category === category)
}

const formatCurrency = (value) => {
  if (!value) return '0 EUR'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

// Load saved data from backend
const loadSavedData = async () => {
  try {
    const { data } = await api.get('/salary/data')
    if (data.success && data.data) {
      // Only apply saved data if no initialPosition is provided
      if (!props.initialPosition) {
        formData.value = {
          position: data.data.formData.position || '',
          region: data.data.formData.region || 'Deutschland',
          experienceYears: data.data.formData.experienceYears || 3,
          targetSalary: data.data.formData.targetSalary || null,
          currentSalary: data.data.formData.currentSalary || null,
          industry: data.data.formData.industry || ''
        }
      }
      salaryResearch.value = data.data.research
      strategy.value = data.data.strategy
      lastSavedAt.value = data.data.updatedAt
      hasLoadedData.value = true
    }
  } catch (err) {
    console.error('Error loading saved data:', err)
  } finally {
    isLoading.value = false
  }
}

// Save data to backend (debounced)
let saveTimeout = null
const saveData = async () => {
  if (isSaving.value) return

  // Clear any pending save
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }

  // Debounce to avoid too many saves
  saveTimeout = setTimeout(async () => {
    isSaving.value = true
    try {
      await api.post('/salary/data', {
        formData: {
          position: formData.value.position,
          region: formData.value.region,
          experienceYears: formData.value.experienceYears,
          targetSalary: formData.value.targetSalary,
          currentSalary: formData.value.currentSalary,
          industry: formData.value.industry
        },
        research: salaryResearch.value,
        strategy: strategy.value
      })
      lastSavedAt.value = new Date().toISOString()
    } catch (err) {
      console.error('Error saving data:', err)
    } finally {
      isSaving.value = false
    }
  }, 1000)
}

const researchSalary = async () => {
  if (!formData.value.position) return

  isResearching.value = true
  try {
    const { data } = await api.post('/salary/research', {
      position: formData.value.position,
      region: formData.value.region,
      experience_years: formData.value.experienceYears,
      industry: formData.value.industry || undefined
    })

    if (data.success) {
      salaryResearch.value = data.research

      // Auto-fill target salary if not set
      if (!formData.value.targetSalary && data.research.median_salary) {
        formData.value.targetSalary = data.research.median_salary
      }

      // Save after successful research
      saveData()
    }
  } catch (err) {
    console.error('Salary research error:', err)
    alert(err.response?.data?.error || 'Fehler bei der Gehaltsrecherche')
  } finally {
    isResearching.value = false
  }
}

const getStrategy = async () => {
  if (!formData.value.targetSalary) return

  isGenerating.value = true
  try {
    const { data } = await api.post('/salary/negotiation-tips', {
      target_salary: formData.value.targetSalary,
      current_salary: formData.value.currentSalary || undefined,
      position: formData.value.position,
      experience_years: formData.value.experienceYears,
      company_name: props.initialCompany || undefined
    })

    if (data.success) {
      strategy.value = data.strategy
      activeCategory.value = 'all'

      // Save after successful strategy generation
      saveData()
    }
  } catch (err) {
    console.error('Strategy generation error:', err)
    alert(err.response?.data?.error || 'Fehler bei der Strategieentwicklung')
  } finally {
    isGenerating.value = false
  }
}

// Watch for prop changes
watch(() => props.initialPosition, (newVal) => {
  if (newVal) {
    formData.value.position = newVal
  }
})

onMounted(async () => {
  // Load saved data first
  await loadSavedData()

  // Override with props if provided
  if (props.initialPosition) {
    formData.value.position = props.initialPosition
  }
})
</script>

<style scoped>
.salary-coach {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* ========================================
   LOADING STATE
   ======================================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-ma-xl);
  text-align: center;
}

.loading-state p {
  margin: 0;
  color: var(--color-text-ghost);
  font-size: 0.9375rem;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-washi-aged);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ========================================
   AUTOSAVE INDICATOR
   ======================================== */
.autosave-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
  font-size: 0.75rem;
  color: var(--color-text-ghost);
}

.autosave-indicator svg {
  color: var(--color-koke);
}

.autosave-indicator .saving-icon {
  animation: spin 1s linear infinite;
  color: var(--color-ai);
}

/* ========================================
   INPUT SECTION
   ======================================== */
.input-section {
  padding: var(--space-lg);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: var(--space-lg);
  color: var(--color-sumi);
}

.section-title svg {
  color: var(--color-ai);
}

.input-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.input-group label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.zen-input {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.9375rem;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background: var(--color-washi);
  color: var(--color-sumi);
  transition: all 0.2s var(--ease-zen);
}

.zen-input:focus {
  outline: none;
  border-color: var(--color-ai);
  box-shadow: 0 0 0 3px rgba(61, 90, 108, 0.1);
}

.zen-input::placeholder {
  color: var(--color-text-ghost);
}

.action-buttons {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

/* ========================================
   SALARY RESEARCH
   ======================================== */
.research-section {
  padding: var(--space-lg);
}

.salary-range {
  margin-bottom: var(--space-lg);
}

.range-bar {
  padding: var(--space-lg) 0;
}

.range-track {
  position: relative;
  height: 12px;
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  overflow: visible;
}

.range-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-ai-light), var(--color-ai));
  border-radius: var(--radius-full);
}

.range-marker {
  position: absolute;
  top: -8px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
}

.range-marker::before {
  content: '';
  width: 24px;
  height: 24px;
  background: var(--color-ai);
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.marker-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-top: var(--space-sm);
}

.marker-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-ai);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.research-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.detail-group h4 {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.factor-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.factor-list li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.factor-list svg {
  flex-shrink: 0;
  color: var(--color-koke);
  margin-top: 3px;
}

.source-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.source-badge {
  padding: var(--space-xs) var(--space-sm);
  background: rgba(61, 90, 108, 0.1);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--color-ai);
}

.notes-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* ========================================
   STRATEGY SECTION
   ======================================== */
.strategy-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.strategy-section .zen-card {
  padding: var(--space-lg);
}

/* Recommended Range */
.recommended-range {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  padding: var(--space-lg) 0;
}

.range-value {
  text-align: center;
}

.range-value .label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.range-value .value {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-sumi);
}

.range-value.max .value {
  color: var(--color-koke);
}

.range-arrow {
  color: var(--color-sand);
}

/* Opening Statement */
.opening-quote {
  margin: 0;
  padding: var(--space-lg);
  background: var(--color-washi);
  border-left: 4px solid var(--color-ai);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  font-size: 1rem;
  font-style: italic;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-lg);
}

.category-tab {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s var(--ease-zen);
}

.category-tab:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

.category-tab.active {
  background: var(--color-ai);
  color: white;
  border-color: var(--color-ai);
}

/* Tips List */
.tips-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.tip-card {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-sand);
}

.tip-card.priority-high {
  border-left-color: var(--color-ai);
  background: rgba(61, 90, 108, 0.05);
}

.tip-card.priority-medium {
  border-left-color: var(--color-terra);
}

.tip-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.priority-badge {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.priority-badge.priority-high {
  background: rgba(61, 90, 108, 0.15);
  color: var(--color-ai);
}

.priority-badge.priority-medium {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.priority-badge.priority-low {
  background: rgba(155, 149, 143, 0.15);
  color: var(--color-stone);
}

.tip-header h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin: 0;
}

.tip-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-sm);
}

.tip-script {
  padding: var(--space-sm);
  background: white;
  border-radius: var(--radius-sm);
  margin-top: var(--space-sm);
}

.script-label {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.tip-script p {
  margin: 0;
  font-size: 0.8125rem;
  font-style: italic;
  color: var(--color-ai);
}

/* Arguments List */
.arguments-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.arguments-list li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.arguments-list svg {
  flex-shrink: 0;
  color: var(--color-koke);
  margin-top: 3px;
}

/* Fallback Positions */
.fallback-intro {
  font-size: 0.875rem;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-md);
}

.fallback-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.fallback-list li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.fallback-number {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Objections */
.objections-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.objection-item {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
}

.objection,
.response {
  margin-bottom: var(--space-sm);
}

.objection:last-child,
.response:last-child {
  margin-bottom: 0;
}

.objection-label,
.response-label {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  margin-bottom: var(--space-xs);
}

.objection-label {
  color: var(--color-terra);
}

.response-label {
  color: var(--color-koke);
}

.objection p,
.response p {
  margin: 0;
  font-size: 0.875rem;
  font-style: italic;
  color: var(--color-text-secondary);
}

/* Culture Notes */
.culture-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.culture-list li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.culture-list svg {
  flex-shrink: 0;
  color: var(--color-ai);
  margin-top: 2px;
}

/* ========================================
   EMPTY STATE
   ======================================== */
.empty-state {
  text-align: center;
  padding: var(--space-ma-xl) var(--space-lg);
}

.empty-icon {
  margin-bottom: var(--space-lg);
  opacity: 0.3;
}

.empty-icon svg {
  color: var(--color-stone);
}

.empty-state p {
  font-size: 0.9375rem;
  color: var(--color-text-ghost);
  max-width: 400px;
  margin: 0 auto;
}

/* ========================================
   LOADING SPINNER
   ======================================== */
.loading-spinner-sm {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: var(--space-xs);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .input-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .zen-btn {
    width: 100%;
    justify-content: center;
  }

  .recommended-range {
    flex-direction: column;
    gap: var(--space-md);
  }

  .range-arrow {
    transform: rotate(90deg);
  }

  .category-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
  }

  .category-tab {
    flex-shrink: 0;
  }
}
</style>
