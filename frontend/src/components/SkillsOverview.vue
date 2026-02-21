<template>
  <div class="skills-overview">
    <div class="skills-header">
      <h3>Ihre Skills</h3>
      <div class="header-actions">
        <button @click="showAddModal = true" class="zen-btn zen-btn-sm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Skill hinzufügen
        </button>
        <button @click="showBulkModal = true" class="zen-btn zen-btn-sm" title="Mehrere Skills auf einmal hinzufügen">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          Bulk-Import
        </button>
        <button v-if="cvDocumentId" @click="reextractSkills" :disabled="extracting" class="zen-btn zen-btn-ai zen-btn-sm">
          <svg v-if="!extracting" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"/>
            <path d="M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          <span v-else class="spinner"></span>
          {{ extracting ? 'Extrahiere...' : 'Neu extrahieren' }}
        </button>
      </div>
    </div>

    <!-- Category Filter -->
    <div v-if="skills.length > 0" class="category-filter">
      <button
        class="filter-btn"
        :class="{ active: categoryFilter === '' }"
        @click="categoryFilter = ''"
      >
        Alle
        <span class="filter-count">{{ skills.length }}</span>
      </button>
      <button
        v-for="(count, cat) in categoryCounts"
        :key="cat"
        class="filter-btn"
        :class="{ active: categoryFilter === cat }"
        @click="categoryFilter = cat"
      >
        {{ getCategoryLabel(cat) }}
        <span class="filter-count">{{ count }}</span>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !loadError" class="skills-loading" role="status" aria-label="Skills werden geladen">
      <div class="skeleton" style="height: 200px;" aria-hidden="true"></div>
      <span class="sr-only">Skills werden geladen...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="loading-error" role="alert">
      <svg class="loading-error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <p class="loading-error-message">Skills konnten nicht geladen werden</p>
      <button @click="retryLoad" class="loading-error-retry">
        Erneut versuchen
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="!skills.length" class="skills-empty">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <h4>Noch keine Skills</h4>
      <p>Laden Sie einen Lebenslauf hoch, um Skills automatisch zu extrahieren, oder fügen Sie Skills manuell hinzu.</p>
      <router-link to="/documents" class="zen-btn zen-btn-ai">
        Lebenslauf hochladen
      </router-link>
    </div>

    <!-- Skills by Category -->
    <div v-else class="skills-categories">
      <div v-for="(categorySkills, category) in skillsByCategory" :key="category" class="skill-category">
        <h4 class="category-title">
          <span class="category-icon">{{ getCategoryIcon(category) }}</span>
          {{ getCategoryLabel(category) }}
          <span class="category-count">{{ categorySkills.length }}</span>
        </h4>
        <div class="skills-list">
          <div v-for="skill in categorySkills" :key="skill.id" class="skill-item">
            <div class="skill-info">
              <span class="skill-name">{{ skill.skill_name }}</span>
              <span v-if="skill.experience_years" class="skill-years">
                {{ skill.experience_years }} {{ skill.experience_years === 1 ? 'Jahr' : 'Jahre' }}
              </span>
            </div>
            <div class="skill-actions">
              <button @click="editSkill(skill)" class="icon-btn" title="Bearbeiten">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button @click="deleteSkill(skill)" class="icon-btn icon-btn-danger" title="Skill löschen" aria-label="Skill löschen">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Total Count -->
    <div v-if="skills.length" class="skills-total">
      Gesamt: {{ skills.length }} Skills
    </div>

    <!-- Bulk Import Modal -->
    <div v-if="showBulkModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal zen-card" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h3>Bulk-Import</h3>
          <button @click="closeModal" class="modal-close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveBulkSkills" class="modal-form">
          <div class="form-group">
            <label for="bulk-skills">Skills (Komma, Semikolon oder Zeilenumbruch getrennt) *</label>
            <textarea
              id="bulk-skills"
              v-model="bulkFormData.skills_text"
              rows="4"
              required
              placeholder="Python, JavaScript, React&#10;oder&#10;Python&#10;JavaScript&#10;React"
            ></textarea>
            <span class="field-hint">Jeder Skill muss mindestens 2 Zeichen haben</span>
          </div>
          <div class="form-group">
            <label for="bulk-category">Kategorie für alle *</label>
            <select id="bulk-category" v-model="bulkFormData.skill_category" required>
              <option value="">Kategorie wählen...</option>
              <option value="technical">Technisch</option>
              <option value="soft_skills">Soft Skills</option>
              <option value="languages">Sprachen</option>
              <option value="tools">Tools</option>
              <option value="certifications">Zertifikate</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModal" class="zen-btn">Abbrechen</button>
            <button type="submit" class="zen-btn zen-btn-ai" :disabled="saving || !bulkFormData.skills_text || !bulkFormData.skill_category">
              {{ saving ? 'Importiere...' : 'Importieren' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editingSkill" class="modal-overlay" @click.self="closeModal">
      <div class="modal zen-card" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h3>{{ editingSkill ? 'Skill bearbeiten' : 'Skill hinzufügen' }}</h3>
          <button @click="closeModal" class="modal-close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveSkill" class="modal-form">
          <div class="form-group autocomplete-container">
            <label for="skill-name">Skill Name *</label>
            <input
              id="skill-name"
              v-model="formData.skill_name"
              type="text"
              required
              minlength="2"
              placeholder="z.B. Python, Projektmanagement"
              :class="{ 'input-error': skillNameError }"
              autocomplete="off"
              @input="validateSkillName(); searchSkills(formData.skill_name)"
              @focus="searchSkills(formData.skill_name)"
              @blur="setTimeout(() => showAutocomplete = false, 200)"
            />
            <ul v-if="showAutocomplete && autocompleteResults.length" class="autocomplete-list">
              <li
                v-for="suggestion in autocompleteResults"
                :key="suggestion"
                @mousedown.prevent="selectAutocomplete(suggestion)"
              >
                {{ suggestion }}
              </li>
            </ul>
            <span v-if="skillNameError" class="field-error" role="alert">{{ skillNameError }}</span>
          </div>
          <div class="form-group">
            <label for="skill-category">Kategorie *</label>
            <select id="skill-category" v-model="formData.skill_category" required>
              <option value="">Kategorie wählen...</option>
              <option value="technical">Technisch</option>
              <option value="soft_skills">Soft Skills</option>
              <option value="languages">Sprachen</option>
              <option value="tools">Tools</option>
              <option value="certifications">Zertifikate</option>
            </select>
          </div>
          <div class="form-group">
            <label for="experience-years">Erfahrungsjahre</label>
            <input
              id="experience-years"
              v-model.number="formData.experience_years"
              type="number"
              min="0"
              step="0.5"
              placeholder="Optional"
            />
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModal" class="zen-btn">Abbrechen</button>
            <button type="submit" class="zen-btn zen-btn-ai" :disabled="saving">
              {{ saving ? 'Speichert...' : (editingSkill ? 'Aktualisieren' : 'Hinzufügen') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api/client'
import { confirm } from '../composables/useConfirm'

const skills = ref([])
const loading = ref(true)
const loadError = ref(false)
const extracting = ref(false)
const saving = ref(false)
const showAddModal = ref(false)
const showBulkModal = ref(false)
const editingSkill = ref(null)
const cvDocumentId = ref(null)
const categoryFilter = ref('') // empty = all categories

const formData = ref({
  skill_name: '',
  skill_category: '',
  experience_years: null
})

const bulkFormData = ref({
  skills_text: '',
  skill_category: ''
})

const skillNameError = ref('')

// Common skill suggestions for autocomplete
const commonSkills = [
  // Technical
  'JavaScript', 'TypeScript', 'Python', 'Java', 'C#', 'C++', 'Go', 'Rust', 'PHP', 'Ruby',
  'React', 'Vue.js', 'Angular', 'Node.js', 'Express', 'Django', 'Flask', 'Spring Boot',
  'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'Azure',
  'Git', 'Linux', 'REST API', 'GraphQL', 'HTML', 'CSS', 'SASS', 'TailwindCSS',
  // Soft Skills
  'Teamarbeit', 'Kommunikation', 'Projektmanagement', 'Problemloesung', 'Zeitmanagement',
  'Fuehrungskompetenz', 'Kreativitaet', 'Analytisches Denken', 'Flexibilitaet',
  // Languages
  'Deutsch', 'Englisch', 'Franzoesisch', 'Spanisch', 'Italienisch', 'Chinesisch',
  // Tools
  'Jira', 'Confluence', 'Slack', 'Microsoft Office', 'Excel', 'PowerPoint', 'Figma', 'Photoshop'
]

const autocompleteResults = ref([])
const showAutocomplete = ref(false)

const validateSkillName = () => {
  const name = formData.value.skill_name.trim()

  // Check empty
  if (!name) {
    skillNameError.value = 'Skill-Name ist erforderlich'
    return false
  }

  // Check minimum length
  if (name.length < 2) {
    skillNameError.value = 'Skill-Name muss mindestens 2 Zeichen haben'
    return false
  }

  // Check for duplicate (case-insensitive)
  const normalizedName = name.toLowerCase()
  const isDuplicate = skills.value.some(
    s => s.skill_name.toLowerCase() === normalizedName &&
         (!editingSkill.value || s.id !== editingSkill.value.id)
  )
  if (isDuplicate) {
    skillNameError.value = 'Dieser Skill existiert bereits'
    return false
  }

  skillNameError.value = ''
  return true
}

// Filter skills by selected category
const filteredSkills = computed(() => {
  if (!categoryFilter.value) return skills.value
  return skills.value.filter(s => s.skill_category === categoryFilter.value)
})

const skillsByCategory = computed(() => {
  const grouped = {}
  for (const skill of filteredSkills.value) {
    const cat = skill.skill_category
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(skill)
  }
  // Sort categories
  const order = ['technical', 'tools', 'languages', 'soft_skills', 'certifications']
  const sorted = {}
  for (const cat of order) {
    if (grouped[cat]) sorted[cat] = grouped[cat]
  }
  return sorted
})

// Count skills per category for filter badges
const categoryCounts = computed(() => {
  const counts = {}
  for (const skill of skills.value) {
    const cat = skill.skill_category
    counts[cat] = (counts[cat] || 0) + 1
  }
  return counts
})

const getCategoryLabel = (category) => {
  const labels = {
    technical: 'Technische Skills',
    soft_skills: 'Soft Skills',
    languages: 'Sprachen',
    tools: 'Tools',
    certifications: 'Zertifikate'
  }
  return labels[category] || category
}

const getCategoryIcon = (category) => {
  const icons = {
    technical: '< >',
    soft_skills: '...',
    languages: 'Aa',
    tools: '#',
    certifications: '*'
  }
  return icons[category] || '-'
}

const loadSkills = async () => {
  loadError.value = false
  try {
    const { data } = await api.get('/users/me/skills')
    skills.value = data.skills || []
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

const retryLoad = () => {
  loading.value = true
  loadSkills()
  loadDocuments()
}

const loadDocuments = async () => {
  try {
    const { data } = await api.get('/documents')
    const cv = data.documents?.find(d => d.doc_type === 'lebenslauf')
    if (cv) cvDocumentId.value = cv.id
  } catch { /* ignore */ }
}

const reextractSkills = async () => {
  if (!cvDocumentId.value || extracting.value) return

  extracting.value = true
  try {
    const { data } = await api.post(`/documents/${cvDocumentId.value}/extract-skills`)
    if (window.$toast) {
      window.$toast(data.message || 'Skills extrahiert', 'success')
    }
    await loadSkills()
  } catch { /* ignore */ } finally {
    extracting.value = false
  }
}

const editSkill = (skill) => {
  editingSkill.value = skill
  formData.value = {
    skill_name: skill.skill_name,
    skill_category: skill.skill_category,
    experience_years: skill.experience_years
  }
}

const deleteSkill = async (skill) => {
  const confirmed = await confirm({
    title: 'Skill löschen',
    message: `Möchten Sie den Skill "${skill.skill_name}" wirklich löschen?`,
    confirmText: 'Löschen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/users/me/skills/${skill.id}`)
    skills.value = skills.value.filter(s => s.id !== skill.id)
    if (window.$toast) {
      window.$toast('Skill gelöscht', 'success')
    }
  } catch { /* ignore */ }
}

const saveSkill = async () => {
  if (saving.value) return

  // Validate before saving
  if (!validateSkillName()) {
    return
  }

  saving.value = true
  try {
    if (editingSkill.value) {
      // Update existing
      const { data } = await api.put(`/users/me/skills/${editingSkill.value.id}`, formData.value)
      const idx = skills.value.findIndex(s => s.id === editingSkill.value.id)
      if (idx >= 0) skills.value[idx] = data.skill
    } else {
      // Add new
      const { data } = await api.post('/users/me/skills', formData.value)
      skills.value.push(data.skill)
    }

    if (window.$toast) {
      window.$toast(editingSkill.value ? 'Skill aktualisiert' : 'Skill hinzugefügt', 'success')
    }
    closeModal()
  } catch (error) {

    // Handle duplicate skill error (409 CONFLICT)
    if (error.response?.status === 409) {
      if (window.$toast) {
        window.$toast('Skill existiert bereits', 'error')
      }
    } else {
      // Generic error for other cases
      if (window.$toast) {
        window.$toast('Fehler beim Speichern des Skills', 'error')
      }
    }
  } finally {
    saving.value = false
  }
}

const closeModal = () => {
  showAddModal.value = false
  showBulkModal.value = false
  editingSkill.value = null
  formData.value = {
    skill_name: '',
    skill_category: '',
    experience_years: null
  }
  bulkFormData.value = {
    skills_text: '',
    skill_category: ''
  }
  skillNameError.value = ''
  showAutocomplete.value = false
  autocompleteResults.value = []
}

// Autocomplete search
const searchSkills = (query) => {
  if (!query || query.length < 2) {
    autocompleteResults.value = []
    showAutocomplete.value = false
    return
  }

  const normalizedQuery = query.toLowerCase()
  const existingSkillNames = skills.value.map(s => s.skill_name.toLowerCase())

  autocompleteResults.value = commonSkills
    .filter(s =>
      s.toLowerCase().includes(normalizedQuery) &&
      !existingSkillNames.includes(s.toLowerCase())
    )
    .slice(0, 5)

  showAutocomplete.value = autocompleteResults.value.length > 0
}

const selectAutocomplete = (skillName) => {
  formData.value.skill_name = skillName
  showAutocomplete.value = false
  autocompleteResults.value = []
  validateSkillName()
}

// Bulk import skills
const saveBulkSkills = async () => {
  if (saving.value) return

  const text = bulkFormData.value.skills_text.trim()
  const category = bulkFormData.value.skill_category

  if (!text || !category) return

  // Parse comma-separated skills
  const skillNames = text
    .split(/[,;\n]/)
    .map(s => s.trim())
    .filter(s => s.length >= 2)

  if (skillNames.length === 0) return

  saving.value = true
  let successCount = 0
  let errorCount = 0

  for (const skillName of skillNames) {
    // Check if skill already exists
    const exists = skills.value.some(
      s => s.skill_name.toLowerCase() === skillName.toLowerCase()
    )
    if (exists) {
      errorCount++
      continue
    }

    try {
      const { data } = await api.post('/users/me/skills', {
        skill_name: skillName,
        skill_category: category,
        experience_years: null
      })
      skills.value.push(data.skill)
      successCount++
    } catch (_e) {
      errorCount++
    }
  }

  saving.value = false

  if (window.$toast) {
    if (successCount > 0) {
      window.$toast(`${successCount} Skills hinzugefügt`, 'success')
    }
    if (errorCount > 0) {
      window.$toast(`${errorCount} Skills übersprungen (bereits vorhanden)`, 'warning')
    }
  }

  closeModal()
}

// Escape key handler for modal
const handleEscapeKey = (event) => {
  if (event.key === 'Escape' && (showAddModal.value || editingSkill.value)) {
    closeModal()
  }
}

// Watch for modal state changes to add/remove escape key listener
watch(() => showAddModal.value || editingSkill.value, (isModalOpen) => {
  if (isModalOpen) {
    document.addEventListener('keydown', handleEscapeKey)
  } else {
    document.removeEventListener('keydown', handleEscapeKey)
  }
})

onMounted(() => {
  loadSkills()
  loadDocuments()
})
</script>

<style scoped>
.skills-overview {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-lg);
}

.skills-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
  gap: var(--space-md);
}

.skills-header h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

/* Category Filter */
.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.filter-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.filter-btn.active {
  background: var(--color-ai-subtle);
  border-color: var(--color-ai);
  color: var(--color-ai);
  font-weight: 500;
}

.filter-count {
  font-size: 0.6875rem;
  padding: 2px 6px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-full);
}

.filter-btn.active .filter-count {
  background: var(--color-ai);
  color: white;
}

.skills-loading,
.skills-empty {
  text-align: center;
  padding: var(--space-xl);
}

.empty-icon {
  color: var(--color-text-ghost);
  margin-bottom: var(--space-md);
}

.skills-empty h4 {
  font-size: 1.125rem;
  margin-bottom: var(--space-sm);
}

.skills-empty p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.skills-categories {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.skill-category {
  border-bottom: 1px solid var(--color-border-light);
  padding-bottom: var(--space-md);
}

.skill-category:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.category-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin-bottom: var(--space-md);
}

.category-icon {
  font-family: monospace;
  font-size: 0.75rem;
  padding: var(--space-xs);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-sm);
  min-width: 28px;
  text-align: center;
}

.category-count {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.skill-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.skill-item:hover {
  border-color: var(--color-ai);
}

.skill-info {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
}

.skill-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.skill-years {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.skill-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition-base);
}

.skill-item:hover .skill-actions {
  opacity: 1;
}

.icon-btn {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.icon-btn:hover {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.icon-btn-danger:hover {
  background: var(--color-error-subtle);
  color: var(--color-error);
}

.skills-total {
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-align: right;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.modal {
  width: 100%;
  max-width: 400px;
  margin: var(--space-md);
  padding: var(--space-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.modal-header h3 {
  font-size: 1.125rem;
  margin: 0;
}

.modal-close {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.modal-close:hover {
  background: var(--color-bg-secondary);
  color: var(--color-sumi);
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.form-group input,
.form-group select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  transition: border-color var(--transition-base);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-ai);
}

.form-group input.input-error {
  border-color: var(--color-error);
}

.form-group input.input-error:focus {
  border-color: var(--color-error);
}

.form-group textarea {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color var(--transition-base);
}

.form-group textarea:focus {
  outline: none;
  border-color: var(--color-ai);
}

.field-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* Autocomplete */
.autocomplete-container {
  position: relative;
}

.autocomplete-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lifted);
  z-index: 10;
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0 0;
  max-height: 200px;
  overflow-y: auto;
}

.autocomplete-list li {
  padding: var(--space-sm) var(--space-md);
  cursor: pointer;
  transition: background var(--transition-base);
}

.autocomplete-list li:hover {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.field-error {
  font-size: 0.8125rem;
  color: var(--color-error);
  margin-top: var(--space-xs);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .skills-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
  }

  .skill-actions {
    opacity: 1;
  }
}
</style>
