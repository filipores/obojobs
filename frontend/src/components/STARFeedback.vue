<template>
  <div class="star-feedback">
    <!-- Loading State -->
    <div v-if="loading" class="star-loading">
      <div class="loading-spinner"></div>
      <span>Analysiere STAR-Struktur...</span>
    </div>

    <!-- Analysis Content -->
    <div v-else-if="analysis" class="star-content">
      <!-- Header with Score -->
      <div class="star-header">
        <div class="star-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          <h3>STAR-Methode Analyse</h3>
        </div>
        <div class="star-score" :class="getScoreClass(analysis.overall_star_score)">
          <span class="score-value">{{ analysis.overall_star_score }}</span>
          <span class="score-label">/ 100</span>
        </div>
      </div>

      <!-- Components Grid -->
      <div class="components-grid">
        <div
          v-for="(component, key) in analysis.components"
          :key="key"
          :class="['component-card', `quality-${component.quality}`]"
        >
          <div class="component-header">
            <div class="component-badge" :class="`quality-${component.quality}`">
              <span class="component-letter">{{ getComponentLetter(key) }}</span>
              <span class="component-name">{{ getComponentName(key) }}</span>
            </div>
            <span class="quality-indicator" :class="`quality-${component.quality}`">
              {{ getQualityLabel(component.quality) }}
            </span>
          </div>

          <!-- Found Content -->
          <div v-if="component.found_content && component.present" class="found-content">
            <span class="content-label">Erkannt:</span>
            <p class="content-text">"{{ component.found_content }}"</p>
          </div>

          <!-- Feedback -->
          <div class="component-feedback">
            <p>{{ component.feedback }}</p>
          </div>

          <!-- Improvement Tip -->
          <div v-if="!component.present || component.quality === 'weak'" class="improvement-tip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>{{ component.improvement_tip }}</span>
          </div>
        </div>
      </div>

      <!-- General Feedback -->
      <div v-if="analysis.general_feedback" class="general-feedback">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Allgemeines Feedback
        </h4>
        <p>{{ analysis.general_feedback }}</p>
      </div>

      <!-- Improvement Suggestions -->
      <div v-if="analysis.improvement_suggestions?.length > 0" class="suggestions-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          Verbesserungsvorschlaege
        </h4>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in analysis.improvement_suggestions" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>

      <!-- Improved Answer Example -->
      <div v-if="analysis.improved_answer_example && showExample" class="example-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          Beispiel einer verbesserten Antwort
        </h4>
        <div class="example-content">
          <p>{{ analysis.improved_answer_example }}</p>
        </div>
      </div>

      <!-- Toggle Example Button -->
      <div v-if="analysis.improved_answer_example" class="example-toggle">
        <button class="zen-btn zen-btn-sm" @click="showExample = !showExample">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="showExample" d="M18 15l-6-6-6 6"/>
            <path v-else d="M6 9l6 6 6-6"/>
          </svg>
          {{ showExample ? 'Beispiel ausblenden' : 'Beispiel zeigen' }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="star-empty">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
      <p>{{ t('components.starFeedback.noAnalysis') }}</p>
      <span>Beantworten Sie eine Verhaltens-Frage, um eine Analyse zu erhalten.</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({
  analysis: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const showExample = ref(false)

const getComponentLetter = (key) => {
  const letters = {
    situation: 'S',
    task: 'T',
    action: 'A',
    result: 'R'
  }
  return letters[key] || key.charAt(0).toUpperCase()
}

const getComponentName = (key) => {
  const names = {
    situation: 'Situation',
    task: 'Aufgabe',
    action: 'Handlung',
    result: 'Ergebnis'
  }
  return names[key] || key
}

const getQualityLabel = (quality) => {
  const labels = {
    strong: 'Stark',
    adequate: 'Ausreichend',
    weak: 'Schwach',
    missing: 'Fehlt'
  }
  return labels[quality] || quality
}

const getScoreClass = (score) => {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-adequate'
  return 'score-needs-improvement'
}
</script>

<style scoped>
.star-feedback {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-lg);
}

/* Loading State */
.star-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-xl);
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Header */
.star-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.star-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.star-title svg {
  color: var(--color-ai);
}

.star-title h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-sumi);
}

.star-score {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
}

.star-score.score-excellent { background: rgba(122, 139, 110, 0.15); color: var(--color-koke); }
.star-score.score-good { background: rgba(61, 90, 108, 0.15); color: var(--color-ai); }
.star-score.score-adequate { background: rgba(196, 163, 90, 0.15); color: #8a7a2a; }
.star-score.score-needs-improvement { background: rgba(180, 80, 80, 0.15); color: #b45050; }

.score-value {
  font-size: 1.5rem;
  font-weight: 600;
}

.score-label {
  font-size: 0.875rem;
  opacity: 0.7;
}

/* Components Grid */
.components-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.component-card {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-border);
}

.component-card.quality-strong { border-left-color: var(--color-koke); }
.component-card.quality-adequate { border-left-color: var(--color-ai); }
.component-card.quality-weak { border-left-color: #c4a35a; }
.component-card.quality-missing { border-left-color: #b45050; }

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.component-badge {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.component-letter {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
}

.component-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi);
}

.quality-indicator {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.quality-indicator.quality-strong { background: rgba(122, 139, 110, 0.15); color: var(--color-koke); }
.quality-indicator.quality-adequate { background: rgba(61, 90, 108, 0.15); color: var(--color-ai); }
.quality-indicator.quality-weak { background: rgba(196, 163, 90, 0.15); color: #8a7a2a; }
.quality-indicator.quality-missing { background: rgba(180, 80, 80, 0.15); color: #b45050; }

/* Found Content */
.found-content {
  margin-bottom: var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-sm);
}

.content-label {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.content-text {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  font-style: italic;
  line-height: 1.5;
}

/* Component Feedback */
.component-feedback {
  margin-bottom: var(--space-sm);
}

.component-feedback p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* Improvement Tip */
.improvement-tip {
  display: flex;
  gap: var(--space-xs);
  padding: var(--space-sm);
  background: rgba(196, 163, 90, 0.1);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: #8a7a2a;
}

.improvement-tip svg {
  flex-shrink: 0;
  margin-top: 1px;
}

/* General Feedback */
.general-feedback {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.general-feedback h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-ai);
  margin: 0 0 var(--space-sm) 0;
}

.general-feedback p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Suggestions Section */
.suggestions-section {
  padding: var(--space-md);
  background: rgba(61, 90, 108, 0.05);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.suggestions-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-ai);
  margin: 0 0 var(--space-md) 0;
}

.suggestions-list {
  margin: 0;
  padding-left: var(--space-lg);
}

.suggestions-list li {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-sm);
}

.suggestions-list li:last-child {
  margin-bottom: 0;
}

/* Example Section */
.example-section {
  padding: var(--space-md);
  background: rgba(122, 139, 110, 0.08);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.example-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-koke);
  margin: 0 0 var(--space-md) 0;
}

.example-content {
  padding: var(--space-md);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-koke);
}

.example-content p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

/* Example Toggle */
.example-toggle {
  text-align: center;
}

/* Empty State */
.star-empty {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-tertiary);
}

.star-empty svg {
  margin-bottom: var(--space-md);
  opacity: 0.4;
}

.star-empty p {
  margin: 0 0 var(--space-xs) 0;
  font-weight: 500;
}

.star-empty span {
  font-size: 0.875rem;
  opacity: 0.7;
}

/* Responsive */
@media (max-width: 768px) {
  .components-grid {
    grid-template-columns: 1fr;
  }

  .star-header {
    flex-direction: column;
    gap: var(--space-md);
    align-items: flex-start;
  }
}
</style>
