<template>
  <div class="interview-prep-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <div class="page-header-content">
          <router-link to="/applications" class="back-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            {{ t('interviewPrep.backToApplications') }}
          </router-link>
          <div class="header-main">
            <div>
              <h1>Interview-Vorbereitung</h1>
              <p class="page-subtitle" v-if="application">
                {{ application.firma }} - {{ application.position || 'Position nicht angegeben' }}
              </p>
            </div>
            <div class="header-actions">
              <button
                @click="regenerateQuestions"
                :disabled="isGenerating"
                class="zen-btn"
              >
                <svg v-if="!isGenerating" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
                <span v-if="isGenerating" class="loading-spinner-sm"></span>
                {{ isGenerating ? 'Generiere...' : 'Alle Fragen neu generieren' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Company Research Section -->
      <section v-if="application && application.firma" class="company-research-section animate-fade-up" style="animation-delay: 50ms;">
        <div class="section-toggle" @click="showCompanyResearch = !showCompanyResearch">
          <h2>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            Firmen-Recherche
          </h2>
          <button class="toggle-btn" :class="{ expanded: showCompanyResearch }">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
        <transition name="expand">
          <div v-if="showCompanyResearch" class="research-wrapper">
            <CompanyResearch
              :company-name="application.firma"
              :job-url="application.quelle || ''"
              :auto-load="true"
            />
          </div>
        </transition>
      </section>

      <!-- Salary Coach Section -->
      <section v-if="application" class="salary-coach-section animate-fade-up" style="animation-delay: 75ms;">
        <div class="section-toggle" @click="showSalaryCoach = !showSalaryCoach">
          <h2>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1v22"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            Gehaltsverhandlungs-Coach
          </h2>
          <button class="toggle-btn" :class="{ expanded: showSalaryCoach }">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
        <transition name="expand">
          <div v-if="showSalaryCoach" class="salary-wrapper">
            <SalaryCoach
              :initial-position="application.position || ''"
              :initial-company="application.firma || ''"
            />
          </div>
        </transition>
      </section>

      <!-- Stats Section -->
      <section v-if="!loading && questions.length > 0" class="stats-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ questions.length }}</span>
            <span class="stat-label">Fragen</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ categoryCounts.behavioral || 0 }}</span>
            <span class="stat-label">Verhaltens</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ categoryCounts.technical || 0 }}</span>
            <span class="stat-label">Technisch</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ categoryCounts.situational || 0 }}</span>
            <span class="stat-label">Situativ</span>
          </div>
        </div>
      </section>

      <!-- Filter Tabs -->
      <section v-if="!loading && questions.length > 0" class="filter-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="filter-tabs">
          <button
            :class="['filter-tab', { active: activeFilter === 'all' }]"
            @click="activeFilter = 'all'"
          >
            Alle ({{ questions.length }})
          </button>
          <button
            v-for="category in categories"
            :key="category.key"
            :class="['filter-tab', { active: activeFilter === category.key }]"
            @click="activeFilter = category.key"
          >
            <span class="category-icon">{{ category.icon }}</span>
            {{ category.label }} ({{ categoryCounts[category.key] || 0 }})
          </button>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Loading State - Skeleton -->
      <!-- SKEL-002-BUG-001: Changed from 3 to 4 skeletons to match actual stats count -->
      <div v-if="loading" class="loading-skeleton" aria-label="Lade Interview-Fragen">
        <div class="skeleton-stats">
          <div class="skeleton skeleton-stat"></div>
          <div class="skeleton skeleton-stat"></div>
          <div class="skeleton skeleton-stat"></div>
          <div class="skeleton skeleton-stat"></div>
        </div>
        <!-- SKEL-002-BUG-002: Increased to 4 filters (1 "All" + 3 categories) to better match dynamic tabs -->
        <div class="skeleton-filters">
          <div class="skeleton skeleton-filter"></div>
          <div class="skeleton skeleton-filter"></div>
          <div class="skeleton skeleton-filter"></div>
          <div class="skeleton skeleton-filter"></div>
        </div>
        <div class="skeleton-questions">
          <div v-for="i in 4" :key="i" class="skeleton-question zen-card">
            <div class="skeleton-question-header">
              <div class="skeleton-badges">
                <div class="skeleton skeleton-badge"></div>
                <div class="skeleton skeleton-badge-sm"></div>
              </div>
              <div class="skeleton skeleton-question-text"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Generating State -->
      <div v-else-if="isGenerating && questions.length === 0" class="loading-state">
        <div class="loading-enso"></div>
        <p>Generiere Interview-Fragen mit KI...</p>
        <p class="loading-hint">Dies kann einen Moment dauern</p>
      </div>

      <!-- Questions List -->
      <section v-else-if="filteredQuestions.length > 0" class="questions-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="questions-list">
          <div
            v-for="(question, index) in filteredQuestions"
            :key="question.id"
            class="question-card zen-card"
            :style="{ animationDelay: `${index * 50}ms` }"
          >
            <div class="question-header" @click="toggleQuestion(question.id)">
              <div class="question-info">
                <div class="question-badges">
                  <span :class="['category-badge', `category-${question.question_type}`]">
                    {{ getCategoryLabel(question.question_type) }}
                  </span>
                  <span :class="['difficulty-badge', `difficulty-${question.difficulty}`]">
                    {{ getDifficultyLabel(question.difficulty) }}
                  </span>
                </div>
                <h3 class="question-text">{{ question.question_text }}</h3>
              </div>
              <div class="question-actions">
                <button
                  @click.stop="goToMockInterview(question)"
                  class="zen-btn zen-btn-sm zen-btn-ai"
                  title="Antwort ueben"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  Ueben
                </button>
                <button class="expand-btn" :class="{ expanded: expandedQuestions.has(question.id) }">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>
            </div>

            <transition name="expand">
              <div v-if="expandedQuestions.has(question.id)" class="question-answer">
                <div class="answer-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                  <span>Beispiel-Antwort</span>
                </div>
                <p class="answer-text">{{ question.sample_answer || t('interviewPrep.noSampleAnswer') }}</p>

                <div v-if="question.question_type === 'behavioral'" class="star-hint">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                  <span>{{ t('interviewPrep.starTip') }}</span>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </section>

      <!-- Empty State -->
      <section v-else class="empty-state">
        <div class="empty-enso"></div>
        <h3>Keine Interview-Fragen vorhanden</h3>
        <p>
          Generieren Sie Interview-Fragen basierend auf der Stellenausschreibung.
        </p>
        <button @click="regenerateQuestions" :disabled="isGenerating" class="zen-btn zen-btn-ai">
          <svg v-if="!isGenerating" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span v-if="isGenerating" class="loading-spinner-sm"></span>
          {{ isGenerating ? 'Generiere...' : 'Fragen generieren' }}
        </button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api/client'
import CompanyResearch from '../components/CompanyResearch.vue'
import SalaryCoach from '../components/SalaryCoach.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const applicationId = computed(() => route.params.id)
const application = ref(null)
const questions = ref([])
const loading = ref(true)
const isGenerating = ref(false)
const activeFilter = ref('all')
const expandedQuestions = ref(new Set())
const showCompanyResearch = ref(true)
const showSalaryCoach = ref(false)

const categories = [
  { key: 'behavioral', label: 'Verhaltens', icon: '🎭' },
  { key: 'technical', label: 'Technisch', icon: '💻' },
  { key: 'situational', label: 'Situativ', icon: '🎯' },
  { key: 'company_specific', label: 'Firmenspezifisch', icon: '🏢' },
  { key: 'salary_negotiation', label: 'Gehalt', icon: '💰' }
]

const categoryCounts = computed(() => {
  const counts = {}
  questions.value.forEach(q => {
    counts[q.question_type] = (counts[q.question_type] || 0) + 1
  })
  return counts
})

const filteredQuestions = computed(() => {
  if (activeFilter.value === 'all') {
    return questions.value
  }
  return questions.value.filter(q => q.question_type === activeFilter.value)
})

const loadApplication = async () => {
  try {
    const { data } = await api.get(`/applications/${applicationId.value}`)
    application.value = data.application
  } catch (err) {
    console.error('Fehler beim Laden der Bewerbung:', err)
    router.push('/applications')
  }
}

const loadQuestions = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/applications/${applicationId.value}/interview-questions`)
    if (data.success) {
      // API returns data.data.all_questions as array (data.data.questions is grouped object)
      questions.value = data.data?.all_questions || []
    }
  } catch (err) {
    console.error('Fehler beim Laden der Fragen:', err)
    questions.value = []
  } finally {
    loading.value = false
  }
}

const regenerateQuestions = async () => {
  isGenerating.value = true
  try {
    // Send empty object to ensure Content-Type: application/json is set
    const { data } = await api.post(`/applications/${applicationId.value}/generate-questions`, {})
    if (data.success) {
      // API returns data.data.questions as array for POST generate-questions
      questions.value = data.data?.questions || []
      expandedQuestions.value = new Set()
    }
  } catch (err) {
    console.error('Fehler beim Generieren der Fragen:', err)
    if (window.$toast) { window.$toast(err.response?.data?.error || 'Fehler beim Generieren der Interview-Fragen', 'error') }
  } finally {
    isGenerating.value = false
  }
}

const toggleQuestion = (questionId) => {
  if (expandedQuestions.value.has(questionId)) {
    expandedQuestions.value.delete(questionId)
  } else {
    expandedQuestions.value.add(questionId)
  }
  // Force reactivity
  expandedQuestions.value = new Set(expandedQuestions.value)
}

const goToMockInterview = (question) => {
  // Navigate to mock interview page with this question
  router.push({
    path: `/applications/${applicationId.value}/mock-interview`,
    query: { questionId: question.id }
  })
}

const getCategoryLabel = (type) => {
  const labels = {
    behavioral: 'Verhaltens',
    technical: 'Technisch',
    situational: 'Situativ',
    company_specific: 'Firmenspezifisch',
    salary_negotiation: 'Gehalt'
  }
  return labels[type] || type
}

const getDifficultyLabel = (difficulty) => {
  const labels = {
    easy: 'Leicht',
    medium: 'Mittel',
    hard: 'Schwer'
  }
  return labels[difficulty] || difficulty
}

onMounted(async () => {
  await loadApplication()
  await loadQuestions()
})
</script>

<style scoped>
.interview-prep-page {
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

.page-header-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color 0.2s var(--ease-zen);
}

.back-link:hover {
  color: var(--color-ai);
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
}

.page-header h1 {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
}

.page-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0;
}

.header-actions {
  flex-shrink: 0;
}

/* ========================================
   STATS SECTION
   ======================================== */
.stats-section {
  margin-bottom: var(--space-lg);
}

.stats-grid {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 500;
  color: var(--color-ai);
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-top: var(--space-xs);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-sand);
}

/* ========================================
   FILTER SECTION
   ======================================== */
.filter-section {
  margin-bottom: var(--space-ma);
}

.filter-tabs {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s var(--ease-zen);
}

.filter-tab:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

.filter-tab.active {
  background: var(--color-ai);
  color: white;
  border-color: var(--color-ai);
}

.category-icon {
  font-size: 0.875rem;
}

/* ========================================
   LOADING SKELETON
   ======================================== */
.loading-skeleton {
  padding: var(--space-ma) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.skeleton-stats {
  display: flex;
  gap: var(--space-lg);
}

.skeleton-stat {
  width: 80px;
  height: 3rem;
}

.skeleton-filters {
  display: flex;
  gap: var(--space-sm);
}

.skeleton-filter {
  width: 100px;
  height: 2.25rem;
  border-radius: var(--radius-md);
}

.skeleton-questions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton-question {
  padding: var(--space-lg);
}

.skeleton-question-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton-badges {
  display: flex;
  gap: var(--space-sm);
}

.skeleton-badge {
  width: 80px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-badge-sm {
  width: 60px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-question-text {
  width: 85%;
  height: 1.25rem;
}

.skeleton {
  background: linear-gradient(90deg, var(--color-washi-aged) 25%, var(--color-washi-warm) 50%, var(--color-washi-aged) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.8s ease infinite;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Keep loading state for generating mode */
.loading-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.loading-enso {
  width: 60px;
  height: 60px;
  margin: 0 auto var(--space-lg);
  border: 2px solid var(--color-sand);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  color: var(--color-text-tertiary);
}

.loading-hint {
  font-size: 0.875rem;
  margin-top: var(--space-sm);
}

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

/* ========================================
   QUESTIONS LIST
   ======================================== */
.questions-section {
  margin-top: var(--space-ma);
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.question-card {
  padding: 0;
  overflow: hidden;
  transition: all 0.2s var(--ease-zen);
}

.question-card:hover {
  border-color: var(--color-ai);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg);
  cursor: pointer;
  transition: background 0.2s var(--ease-zen);
}

.question-header:hover {
  background: var(--color-washi);
}

.question-info {
  flex: 1;
  min-width: 0;
}

.question-badges {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.category-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.category-behavioral {
  background: rgba(138, 79, 125, 0.15);
  color: #8a4f7d;
}

.category-technical {
  background: rgba(61, 90, 108, 0.15);
  color: var(--color-ai);
}

.category-situational {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.category-company_specific {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.category-salary_negotiation {
  background: rgba(196, 163, 90, 0.15);
  color: #8a7a2a;
}

.difficulty-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.difficulty-easy {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.difficulty-medium {
  background: rgba(196, 163, 90, 0.15);
  color: #8a7a2a;
}

.difficulty-hard {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.question-text {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0;
  line-height: 1.5;
}

.question-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.expand-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--ease-zen);
}

.expand-btn:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

.expand-btn svg {
  transition: transform 0.3s var(--ease-zen);
}

.expand-btn.expanded svg {
  transform: rotate(180deg);
}

/* ========================================
   QUESTION ANSWER (Expandable)
   ======================================== */
.question-answer {
  padding: var(--space-lg);
  background: var(--color-washi);
  border-top: 1px solid var(--color-border-light);
}

.answer-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-ai);
  margin-bottom: var(--space-md);
}

.answer-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
}

.star-hint {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
  padding: var(--space-md);
  background: rgba(61, 90, 108, 0.08);
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  color: var(--color-ai);
}

.star-hint svg {
  flex-shrink: 0;
  margin-top: 2px;
}

/* Expand Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s var(--ease-zen);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* ========================================
   EMPTY STATE
   ======================================== */
.empty-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.empty-enso {
  width: 100px;
  height: 100px;
  margin: 0 auto var(--space-lg);
  border: 2px solid var(--color-sand);
  border-width: 2px 3px 2px 2.5px;
  border-radius: 50%;
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.empty-state p {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-lg);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .header-main {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .zen-btn {
    width: 100%;
    justify-content: center;
  }

  .stats-grid {
    justify-content: flex-start;
  }

  .filter-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: var(--space-sm);
    -webkit-overflow-scrolling: touch;
  }

  .filter-tab {
    white-space: nowrap;
    flex-shrink: 0;
  }

  .question-header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .question-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 1.75rem;
  }

  .question-badges {
    flex-wrap: wrap;
  }
}

/* ========================================
   COMPANY RESEARCH SECTION
   ======================================== */
.company-research-section {
  margin-bottom: var(--space-lg);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.section-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  transition: background 0.2s var(--ease-zen);
}

.section-toggle:hover {
  background: var(--color-washi);
}

.section-toggle h2 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-sumi);
}

.section-toggle h2 svg {
  color: var(--color-ai);
}

.toggle-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: transform 0.3s var(--ease-zen);
}

.toggle-btn.expanded svg {
  transform: rotate(180deg);
}

.research-wrapper {
  padding: 0 var(--space-lg) var(--space-lg);
}

.research-wrapper .company-research {
  background: var(--color-washi);
  border: none;
}

/* ========================================
   SALARY COACH SECTION
   ======================================== */
.salary-coach-section {
  margin-bottom: var(--space-lg);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.salary-wrapper {
  padding: 0 var(--space-lg) var(--space-lg);
}

.salary-wrapper .salary-coach {
  background: transparent;
}

.salary-wrapper .zen-card {
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
}
</style>
