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
          Skill hinzufugen
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
      <p>Laden Sie einen Lebenslauf hoch, um Skills automatisch zu extrahieren, oder fugen Sie Skills manuell hinzu.</p>
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

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editingSkill" class="modal-overlay" @click.self="closeModal">
      <div class="modal zen-card">
        <div class="modal-header">
          <h3>{{ editingSkill ? 'Skill bearbeiten' : 'Skill hinzufugen' }}</h3>
          <button @click="closeModal" class="modal-close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveSkill" class="modal-form">
          <div class="form-group">
            <label for="skill-name">Skill Name *</label>
            <input
              id="skill-name"
              v-model="formData.skill_name"
              type="text"
              required
              minlength="2"
              placeholder="z.B. Python, Projektmanagement"
              :class="{ 'input-error': skillNameError }"
              @input="validateSkillName"
            />
            <span v-if="skillNameError" class="field-error" role="alert">{{ skillNameError }}</span>
          </div>
          <div class="form-group">
            <label for="skill-category">Kategorie *</label>
            <select id="skill-category" v-model="formData.skill_category" required>
              <option value="">Kategorie wahlen...</option>
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
              {{ saving ? 'Speichert...' : (editingSkill ? 'Aktualisieren' : 'Hinzufugen') }}
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
const editingSkill = ref(null)
const cvDocumentId = ref(null)

const formData = ref({
  skill_name: '',
  skill_category: '',
  experience_years: null
})

const skillNameError = ref('')

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

const skillsByCategory = computed(() => {
  const grouped = {}
  for (const skill of skills.value) {
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
  } catch (error) {
    console.error('Failed to load skills:', error)
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
  } catch (error) {
    console.error('Failed to load documents:', error)
  }
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
  } catch (error) {
    console.error('Failed to extract skills:', error)
  } finally {
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
      window.$toast('Skill geloscht', 'success')
    }
  } catch (error) {
    console.error('Failed to delete skill:', error)
  }
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
      window.$toast(editingSkill.value ? 'Skill aktualisiert' : 'Skill hinzugefugt', 'success')
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save skill:', error)

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
  editingSkill.value = null
  formData.value = {
    skill_name: '',
    skill_category: '',
    experience_years: null
  }
  skillNameError.value = ''
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
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
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
