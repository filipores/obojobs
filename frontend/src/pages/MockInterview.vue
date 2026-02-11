<template>
  <div class="mock-interview-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <div class="page-header-content">
          <router-link v-if="applicationId" :to="applicationId ? `/applications/${applicationId}/interview` : '/applications'" class="back-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            {{ t('mockInterview.backToPrep') }}
          </router-link>
          <div class="header-main">
            <div>
              <h1>Mock-Interview</h1>
              <p class="page-subtitle" v-if="application">
                {{ application.firma }} - {{ application.position || 'Position' }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Error State -->
      <section v-if="error" class="empty-state">
        <div class="empty-card zen-card">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <h2>Fehler beim Laden</h2>
          <p>{{ error }}</p>
          <router-link to="/applications" class="zen-btn zen-btn-ai">
            Zurück zu Bewerbungen
          </router-link>
        </div>
      </section>

      <!-- Loading State -->
      <div v-else-if="loading" class="loading-state">
        <div class="loading-enso"></div>
        <p>Lade Interview-Fragen...</p>
      </div>

      <!-- No Questions State -->
      <section v-else-if="questions.length === 0" class="empty-state">
        <div class="empty-card zen-card">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9 9a3 3 0 1 1 2.83 4"/>
              <line x1="12" y1="17" x2="12" y2="17"/>
            </svg>
          </div>
          <h2>Keine Fragen vorhanden</h2>
          <p>Generieren Sie zuerst Interview-Fragen in der Interview-Vorbereitung.</p>
          <router-link :to="applicationId ? `/applications/${applicationId}/interview` : '/applications'" class="zen-btn zen-btn-ai">
            Zur Interview-Vorbereitung
          </router-link>
        </div>
      </section>

      <!-- Interview Flow -->
      <template v-else>
        <!-- Timer Settings -->
        <section v-if="!interviewComplete" class="timer-settings-section animate-fade-up" style="animation-delay: 50ms;">
          <div class="timer-toggle-row">
            <button
              @click="toggleTimer"
              :class="['timer-toggle-btn', { active: timerEnabled }]"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ timerEnabled ? 'Timer aktiv' : 'Timer aktivieren' }}
            </button>

            <button
              v-if="timerEnabled"
              @click="showTimerSettings = !showTimerSettings"
              class="timer-settings-btn"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
              Einstellungen
            </button>
          </div>

          <!-- Timer Settings Panel -->
          <div v-if="timerEnabled && showTimerSettings" class="timer-settings-panel">
            <label class="timer-minutes-label">
              Zeit pro Frage:
              <select v-model.number="timerMinutes" class="timer-minutes-select">
                <option :value="1">1 Minute</option>
                <option :value="2">2 Minuten</option>
                <option :value="3">3 Minuten</option>
                <option :value="5">5 Minuten</option>
              </select>
            </label>
          </div>
        </section>

        <!-- Progress Section -->
        <section v-if="!interviewComplete" class="progress-section animate-fade-up" style="animation-delay: 100ms;">
          <div class="progress-bar-container">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <span class="progress-text">Frage {{ currentQuestionIndex + 1 }} von {{ questions.length }}</span>
          </div>

          <!-- Timer Display -->
          <div v-if="timerEnabled && !currentFeedback" class="timer-display-container">
            <div
              :class="['timer-display', {
                'timer-low': timerIsLow,
                'timer-critical': timerIsCritical,
                'timer-expired': timerExpired
              }]"
            >
              <div class="timer-progress-ring">
                <svg viewBox="0 0 36 36">
                  <path
                    class="timer-ring-bg"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    class="timer-ring-fill"
                    :stroke-dasharray="`${100 - timerProgressPercent}, 100`"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <div class="timer-value">
                  <span class="timer-time">{{ timerDisplay }}</span>
                </div>
              </div>
              <span v-if="timerExpired" class="timer-expired-text">Zeit abgelaufen!</span>
            </div>
          </div>
        </section>

        <!-- Question Card -->
        <section v-if="!interviewComplete" class="question-section animate-fade-up" style="animation-delay: 150ms;">
          <div class="question-card zen-card">
            <div class="question-badges">
              <span :class="['category-badge', `category-${currentQuestion.question_type}`]">
                {{ getCategoryLabel(currentQuestion.question_type) }}
              </span>
              <span :class="['difficulty-badge', `difficulty-${currentQuestion.difficulty}`]">
                {{ getDifficultyLabel(currentQuestion.difficulty) }}
              </span>
            </div>

            <h2 class="question-text">{{ currentQuestion.question_text }}</h2>

            <!-- STAR Hint for behavioral questions -->
            <div v-if="currentQuestion.question_type === 'behavioral'" class="star-hint">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              <span>Tipp: Nutzen Sie die STAR-Methode (Situation, Task, Action, Result)</span>
            </div>

            <!-- Alternative tips for non-behavioral questions -->
            <div v-else class="question-type-hint">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              <div class="hint-content">
                <span class="hint-title">{{ getQuestionTypeHintTitle(currentQuestion.question_type) }}</span>
                <span class="hint-text">{{ getQuestionTypeHint(currentQuestion.question_type) }}</span>
              </div>
            </div>

            <!-- Answer Input -->
            <div class="answer-section">
              <label for="answer-input" class="answer-label">Ihre Antwort:</label>
              <textarea
                id="answer-input"
                v-model="currentAnswer"
                :disabled="isEvaluating"
                class="answer-textarea"
                placeholder="Tippen Sie hier Ihre Antwort ein..."
                rows="6"
                @keydown.ctrl.enter="submitAnswer"
              ></textarea>
              <div class="answer-footer">
                <span class="char-count" :class="{ 'low': currentAnswer.length < 50 }">
                  {{ currentAnswer.length }} Zeichen
                </span>
                <button
                  @click="submitAnswer"
                  :disabled="isEvaluating || currentAnswer.length < 10"
                  class="zen-btn zen-btn-ai"
                >
                  <span v-if="isEvaluating" class="loading-spinner-sm"></span>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                  {{ isEvaluating ? 'Bewerte...' : 'Antwort absenden' }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Feedback Section -->
        <section v-if="currentFeedback && !interviewComplete" class="feedback-section animate-fade-up">
          <div class="feedback-card zen-card">
            <div class="feedback-header">
              <div class="score-circle" :class="getScoreClass(currentFeedback.overall_score)">
                <span class="score-value">{{ currentFeedback.overall_score }}</span>
                <span class="score-label">Punkte</span>
              </div>
              <div class="feedback-title">
                <h3>{{ getRatingLabel(currentFeedback.overall_rating) }}</h3>
                <p class="rating-description">{{ getRatingDescription(currentFeedback.overall_rating) }}</p>
              </div>
            </div>

            <div class="feedback-grid">
              <!-- Strengths -->
              <div class="feedback-block strengths">
                <h4>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                  Staerken
                </h4>
                <ul>
                  <li v-for="(strength, index) in currentFeedback.strengths" :key="'s-' + index">
                    {{ strength }}
                  </li>
                </ul>
              </div>

              <!-- Improvements -->
              <div class="feedback-block improvements">
                <h4>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  Verbesserungen
                </h4>
                <ul>
                  <li v-for="(improvement, index) in currentFeedback.improvements" :key="'i-' + index">
                    {{ improvement }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- Suggestion -->
            <div class="suggestion-block">
              <h4>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                </svg>
                Konkreter Verbesserungsvorschlag
              </h4>
              <p>{{ currentFeedback.suggestion }}</p>
            </div>

            <!-- STAR Analysis for behavioral questions -->
            <div v-if="currentFeedback.star_analysis" class="star-analysis">
              <div class="star-analysis-header">
                <h4>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                  STAR-Methode Analyse
                </h4>
                <button
                  v-if="currentQuestion.question_type === 'behavioral'"
                  @click="loadDetailedStarAnalysis"
                  :disabled="isLoadingStarAnalysis"
                  class="zen-btn zen-btn-sm"
                >
                  <span v-if="isLoadingStarAnalysis" class="loading-spinner-sm"></span>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  {{ isLoadingStarAnalysis ? 'Lade...' : 'Detaillierte Analyse' }}
                </button>
              </div>
              <div class="star-grid">
                <div
                  v-for="(component, key) in currentFeedback.star_analysis"
                  :key="key"
                  class="star-component"
                  :class="[`quality-${component.quality}`]"
                >
                  <div class="star-header">
                    <span class="star-letter">{{ getStarLetter(key) }}</span>
                    <span class="star-name">{{ getStarName(key) }}</span>
                    <span class="star-status" :class="{ present: component.present }">
                      {{ component.present ? 'Vorhanden' : 'Fehlt' }}
                    </span>
                  </div>
                  <p class="star-feedback">{{ component.feedback }}</p>
                </div>
              </div>
            </div>

            <!-- Info hint for non-behavioral questions explaining why STAR analysis is not available -->
            <div v-else-if="currentQuestion.question_type !== 'behavioral'" class="star-not-applicable-hint">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              <div class="hint-content">
                <span class="hint-title">{{ t('mockInterview.noStarAnalysis') }}</span>
                <span class="hint-text">
                  {{ t('mockInterview.starExplanation') }}
                  Diese {{ getQuestionTypeLabel(currentQuestion.question_type) }} Frage erfordert einen anderen Antwort-Ansatz.
                </span>
              </div>
            </div>

            <!-- Detailed STAR Feedback Component -->
            <STARFeedback
              v-if="detailedStarAnalysis"
              :analysis="detailedStarAnalysis"
              :loading="isLoadingStarAnalysis"
              class="detailed-star-section"
            />

            <!-- Length & Structure Assessment -->
            <div class="assessment-row">
              <div class="assessment-item">
                <span class="assessment-label">Laenge:</span>
                <span :class="['assessment-value', `length-${currentFeedback.length_assessment?.rating}`]">
                  {{ getLengthLabel(currentFeedback.length_assessment?.rating) }}
                </span>
              </div>
              <div class="assessment-item">
                <span class="assessment-label">Struktur:</span>
                <span :class="['assessment-value', `structure-${currentFeedback.structure_assessment?.rating}`]">
                  {{ getStructureLabel(currentFeedback.structure_assessment?.rating) }}
                </span>
              </div>
            </div>

            <!-- Next Button -->
            <div class="feedback-actions">
              <button v-if="currentQuestionIndex < questions.length - 1" @click="nextQuestion" class="zen-btn zen-btn-ai">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14"/>
                  <polyline points="12 5 19 12 12 19"/>
                </svg>
                {{ t('mockInterview.nextQuestion') }}
              </button>
              <button v-else @click="finishInterview" class="zen-btn zen-btn-ai">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                {{ t('mockInterview.finishInterview') }}
              </button>
            </div>
          </div>
        </section>

        <!-- Summary Section -->
        <section v-if="interviewComplete && summary" class="summary-section animate-fade-up">
          <div class="summary-card zen-card">
            <div class="summary-header">
              <div class="summary-score-circle" :class="getScoreClass(summary.overall_score)">
                <span class="score-value">{{ Math.round(summary.overall_score) }}</span>
                <span class="score-label">Gesamt</span>
              </div>
              <div class="summary-title">
                <h2>Interview abgeschlossen!</h2>
                <p>{{ summary.overall_assessment }}</p>
              </div>
            </div>

            <!-- Category Scores -->
            <div v-if="Object.keys(summary.category_scores || {}).length > 0" class="category-scores">
              <h3>Bewertung nach Kategorie</h3>
              <div class="scores-grid">
                <div
                  v-for="(score, category) in summary.category_scores"
                  :key="category"
                  class="score-item"
                >
                  <span class="score-category">{{ getCategoryLabel(category) }}</span>
                  <div class="score-bar-container">
                    <div class="score-bar" :style="{ width: score + '%' }" :class="getScoreClass(score)"></div>
                  </div>
                  <span class="score-number">{{ Math.round(score) }}%</span>
                </div>
              </div>
            </div>

            <!-- Top Strengths -->
            <div v-if="summary.top_strengths?.length" class="summary-block">
              <h3>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                Ihre Staerken
              </h3>
              <ul>
                <li v-for="(strength, index) in summary.top_strengths" :key="'ts-' + index">
                  {{ strength }}
                </li>
              </ul>
            </div>

            <!-- Priority Improvements -->
            <div v-if="summary.priority_improvements?.length" class="summary-block improvements">
              <h3>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                </svg>
                Verbesserungspotenzial
              </h3>
              <ul>
                <li v-for="(improvement, index) in summary.priority_improvements" :key="'pi-' + index">
                  {{ improvement }}
                </li>
              </ul>
            </div>

            <!-- Next Steps -->
            <div v-if="summary.next_steps?.length" class="summary-block next-steps">
              <h3>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14"/>
                  <polyline points="12 5 19 12 12 19"/>
                </svg>
                {{ t('mockInterview.nextSteps') }}
              </h3>
              <ol>
                <li v-for="(step, index) in summary.next_steps" :key="'ns-' + index">
                  {{ step }}
                </li>
              </ol>
            </div>

            <!-- Timer Statistics -->
            <div v-if="timerStats.answersCount > 0" class="timer-stats-block">
              <h3>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                Zeit-Statistik
              </h3>
              <div class="timer-stats-grid">
                <div class="timer-stat-item">
                  <span class="timer-stat-value">{{ averageAnswerTimeDisplay }}</span>
                  <span class="timer-stat-label">Durchschnittliche Antwortzeit</span>
                </div>
                <div class="timer-stat-item">
                  <span class="timer-stat-value">{{ timerStats.answersCount }}</span>
                  <span class="timer-stat-label">Beantwortete Fragen</span>
                </div>
                <div class="timer-stat-item" :class="{ 'stat-warning': timerStats.timeExceeded > 0 }">
                  <span class="timer-stat-value">{{ timerStats.timeExceeded }}</span>
                  <span class="timer-stat-label">Zeitueberschreitungen</span>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="summary-actions">
              <button @click="restartInterview" class="zen-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
                Nochmal ueben
              </button>
              <router-link :to="applicationId ? `/applications/${applicationId}/interview` : '/applications'" class="zen-btn zen-btn-ai">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M19 12H5"/>
                  <polyline points="12 19 5 12 12 5"/>
                </svg>
                Zur Interview-Vorbereitung
              </router-link>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api/client'
import STARFeedback from '../components/STARFeedback.vue'

const { t } = useI18n()
const route = useRoute()

const applicationId = computed(() => route.params.id)
const startQuestionId = computed(() => route.query.questionId)

const application = ref(null)
const questions = ref([])
const loading = ref(true)
const error = ref(null)
const isEvaluating = ref(false)
const currentQuestionIndex = ref(0)
const currentAnswer = ref('')
const currentFeedback = ref(null)
const interviewComplete = ref(false)
const summary = ref(null)
const answerHistory = ref([])
const isLoadingStarAnalysis = ref(false)
const detailedStarAnalysis = ref(null)

// Timer state
const timerEnabled = ref(false)
const timerMinutes = ref(2) // Default: 2 Minuten pro Frage
const timerSeconds = ref(0) // Verbleibende Sekunden
const timerInterval = ref(null)
const timerExpired = ref(false)
const showTimerSettings = ref(false)

// Timer statistics
const timerStats = ref({
  totalAnswerTime: 0, // in Sekunden
  answersCount: 0,
  timeExceeded: 0 // Anzahl Zeitueberschreitungen
})

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value] || {})
const progressPercent = computed(() => ((currentQuestionIndex.value + 1) / questions.value.length) * 100)

// Timer computed
const timerDisplay = computed(() => {
  const mins = Math.floor(timerSeconds.value / 60)
  const secs = timerSeconds.value % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
})

const timerProgressPercent = computed(() => {
  const totalSeconds = timerMinutes.value * 60
  return ((totalSeconds - timerSeconds.value) / totalSeconds) * 100
})

const timerIsLow = computed(() => timerSeconds.value <= 30 && timerSeconds.value > 0)
const timerIsCritical = computed(() => timerSeconds.value <= 10 && timerSeconds.value > 0)

const averageAnswerTime = computed(() => {
  if (timerStats.value.answersCount === 0) return 0
  return Math.round(timerStats.value.totalAnswerTime / timerStats.value.answersCount)
})

const averageAnswerTimeDisplay = computed(() => {
  const secs = averageAnswerTime.value
  const mins = Math.floor(secs / 60)
  const remainingSecs = secs % 60
  if (mins === 0) return `${remainingSecs}s`
  return `${mins}m ${remainingSecs}s`
})

const loadApplication = async () => {
  try {
    const { data } = await api.get(`/applications/${applicationId.value}`)
    if (data.success && data.application) {
      application.value = data.application
    } else {
      throw new Error('Bewerbung nicht gefunden')
    }
  } catch (err) {
    console.error('Fehler beim Laden der Bewerbung:', err)
    error.value = 'Bewerbung konnte nicht geladen werden'
    loading.value = false
  }
}

const loadQuestions = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/applications/${applicationId.value}/interview-questions`)
    if (data.success) {
      questions.value = data.data?.all_questions || data.questions || []

      // If a specific question was requested, start there
      if (startQuestionId.value) {
        const idx = questions.value.findIndex(q => q.id === parseInt(startQuestionId.value))
        if (idx >= 0) {
          currentQuestionIndex.value = idx
        }
      }
    }
  } catch (err) {
    console.error('Fehler beim Laden der Fragen:', err)
    questions.value = []
  } finally {
    loading.value = false
  }
}

// Timer functions
const startTimer = () => {
  if (!timerEnabled.value) return

  stopTimer()
  timerSeconds.value = timerMinutes.value * 60
  timerExpired.value = false

  timerInterval.value = setInterval(() => {
    if (timerSeconds.value > 0) {
      timerSeconds.value--

      // Akustischer Hinweis bei 10 Sekunden
      if (timerSeconds.value === 10) {
        playTimerWarning()
      }
    } else {
      // Zeit abgelaufen
      timerExpired.value = true
      stopTimer()
      playTimerExpired()
    }
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

const resetTimer = () => {
  stopTimer()
  timerSeconds.value = timerMinutes.value * 60
  timerExpired.value = false
}

const playTimerWarning = () => {
  // Einfacher Beep-Sound (Web Audio API)
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    oscillator.frequency.value = 880 // A5
    oscillator.type = 'sine'
    gainNode.gain.value = 0.1

    oscillator.start()
    oscillator.stop(audioContext.currentTime + 0.15)
  } catch {
    // Audio nicht verfuegbar, ignorieren
  }
}

const playTimerExpired = () => {
  // Doppelter Beep bei Zeitablauf
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    oscillator.frequency.value = 660 // E5
    oscillator.type = 'sine'
    gainNode.gain.value = 0.15

    oscillator.start()
    oscillator.stop(audioContext.currentTime + 0.3)

    // Zweiter Beep nach kurzer Pause
    setTimeout(() => {
      const osc2 = audioContext.createOscillator()
      const gain2 = audioContext.createGain()
      osc2.connect(gain2)
      gain2.connect(audioContext.destination)
      osc2.frequency.value = 660
      osc2.type = 'sine'
      gain2.gain.value = 0.15
      osc2.start()
      osc2.stop(audioContext.currentTime + 0.3)
    }, 200)
  } catch {
    // Audio nicht verfuegbar, ignorieren
  }
}

const toggleTimer = () => {
  timerEnabled.value = !timerEnabled.value
  if (timerEnabled.value && !currentFeedback.value) {
    startTimer()
  } else {
    stopTimer()
  }
}

const recordAnswerTime = () => {
  if (!timerEnabled.value) return

  const totalSeconds = timerMinutes.value * 60
  const timeTaken = totalSeconds - timerSeconds.value

  timerStats.value.totalAnswerTime += timeTaken
  timerStats.value.answersCount++

  if (timerExpired.value) {
    timerStats.value.timeExceeded++
  }
}

const submitAnswer = async () => {
  if (isEvaluating.value || currentAnswer.value.length < 10) return

  // Timer stoppen und Zeit erfassen
  recordAnswerTime()
  stopTimer()

  isEvaluating.value = true
  currentFeedback.value = null

  try {
    const { data } = await api.post('/applications/interview/evaluate-answer', {
      question_id: currentQuestion.value.id,
      answer_text: currentAnswer.value,
      application_id: applicationId.value
    })

    if (data.success) {
      currentFeedback.value = data.data.evaluation

      // Store answer for summary
      answerHistory.value.push({
        question_id: currentQuestion.value.id,
        question_type: currentQuestion.value.question_type,
        question_text: currentQuestion.value.question_text,
        answer_text: currentAnswer.value,
        score: data.data.evaluation.overall_score,
        strengths: data.data.evaluation.strengths,
        improvements: data.data.evaluation.improvements
      })
    }
  } catch (err) {
    console.error('Fehler bei der Bewertung:', err)
    if (window.$toast) { window.$toast(err.response?.data?.error || 'Fehler bei der Bewertung der Antwort', 'error') }
  } finally {
    isEvaluating.value = false
  }
}

const nextQuestion = () => {
  currentQuestionIndex.value++
  currentAnswer.value = ''
  currentFeedback.value = null
  detailedStarAnalysis.value = null
  timerExpired.value = false

  // Timer fuer naechste Frage starten
  if (timerEnabled.value) {
    startTimer()
  }
}

const loadDetailedStarAnalysis = async () => {
  if (isLoadingStarAnalysis.value) return

  isLoadingStarAnalysis.value = true
  try {
    const { data } = await api.post('/applications/interview/analyze-star', {
      question_id: currentQuestion.value.id,
      question_text: currentQuestion.value.question_text,
      answer_text: currentAnswer.value,
      application_id: applicationId.value
    })

    if (data.success) {
      detailedStarAnalysis.value = data.data.star_analysis
    }
  } catch (err) {
    console.error('Fehler bei der STAR-Analyse:', err)
    if (window.$toast) { window.$toast(err.response?.data?.error || 'Fehler bei der detaillierten STAR-Analyse', 'error') }
  } finally {
    isLoadingStarAnalysis.value = false
  }
}

const finishInterview = async () => {
  try {
    const { data } = await api.post('/applications/interview/summary', {
      application_id: applicationId.value,
      answers: answerHistory.value
    })

    if (data.success) {
      summary.value = data.data.summary
      interviewComplete.value = true
    }
  } catch (err) {
    console.error('Fehler bei der Zusammenfassung:', err)
    // Still show completion even if summary fails
    summary.value = {
      overall_score: answerHistory.value.reduce((sum, a) => sum + a.score, 0) / answerHistory.value.length,
      overall_assessment: 'Interview abgeschlossen.',
      total_questions: answerHistory.value.length
    }
    interviewComplete.value = true
  }
}

const restartInterview = () => {
  currentQuestionIndex.value = 0
  currentAnswer.value = ''
  currentFeedback.value = null
  interviewComplete.value = false
  summary.value = null
  answerHistory.value = []
  detailedStarAnalysis.value = null
  timerExpired.value = false
  timerStats.value = {
    totalAnswerTime: 0,
    answersCount: 0,
    timeExceeded: 0
  }

  // Timer starten wenn aktiviert
  if (timerEnabled.value) {
    startTimer()
  }
}

// Helper functions
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

const getScoreClass = (score) => {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-adequate'
  return 'score-needs-improvement'
}

const getRatingLabel = (rating) => {
  const labels = {
    excellent: 'Ausgezeichnet!',
    good: 'Gut gemacht!',
    adequate: 'Solide Basis',
    needs_improvement: t('mockInterview.needsImprovement')
  }
  return labels[rating] || rating
}

const getRatingDescription = (rating) => {
  const descriptions = {
    excellent: 'Ihre Antwort war überzeugend und gut strukturiert.',
    good: t('mockInterview.goodWithImprovements'),
    adequate: 'Die Grundlagen sind da, aber es gibt Potenzial nach oben.',
    needs_improvement: 'Diese Antwort könnte deutlich verbessert werden.'
  }
  return descriptions[rating] || ''
}

const getLengthLabel = (rating) => {
  const labels = {
    too_short: 'Zu kurz',
    adequate: 'Angemessen',
    too_long: 'Zu lang'
  }
  return labels[rating] || 'Unbekannt'
}

const getStructureLabel = (rating) => {
  const labels = {
    well_structured: 'Gut strukturiert',
    partially_structured: 'Teilweise strukturiert',
    unstructured: 'Unstrukturiert'
  }
  return labels[rating] || 'Unbekannt'
}

const getStarLetter = (key) => key.charAt(0).toUpperCase()

const getStarName = (key) => {
  const names = {
    situation: 'Situation',
    task: 'Aufgabe',
    action: 'Handlung',
    result: 'Ergebnis'
  }
  return names[key] || key
}

const getQuestionTypeLabel = (type) => {
  const labels = {
    behavioral: 'Verhaltens-',
    technical: 'technische',
    situational: 'situative',
    company_specific: 'firmenspezifische',
    salary_negotiation: 'Gehaltsverhandlungs-'
  }
  return labels[type] || type
}

const getQuestionTypeHintTitle = (type) => {
  const titles = {
    technical: 'Technische Frage',
    situational: 'Situative Frage',
    company_specific: 'Firmenspezifische Frage',
    salary_negotiation: 'Gehaltsverhandlungs-Frage'
  }
  return titles[type] || 'Tipp'
}

const getQuestionTypeHint = (type) => {
  const hints = {
    technical: t('mockInterview.hintTechnical'),
    situational: t('mockInterview.hintSituational'),
    company_specific: t('mockInterview.hintCompanySpecific'),
    salary_negotiation: t('mockInterview.hintSalaryNegotiation')
  }
  return hints[type] || t('mockInterview.defaultHint')
}

onMounted(async () => {
  // Validate application ID
  if (!applicationId.value || isNaN(parseInt(applicationId.value))) {
    console.error('Invalid application ID:', applicationId.value)
    error.value = 'Ungültige Bewerbungs-ID'
    loading.value = false
    return
  }

  try {
    await loadApplication()
    // Only load questions if application was loaded successfully
    if (!error.value) {
      await loadQuestions()
    }
  } catch (err) {
    console.error('Error during component initialization:', err)
    if (!error.value) {
      error.value = 'Fehler beim Laden der Daten'
    }
    loading.value = false
  }
})

onUnmounted(() => {
  stopTimer()
})

// Watch fuer Timer-Minuten-Aenderungen
watch(timerMinutes, () => {
  if (timerEnabled.value && !currentFeedback.value) {
    resetTimer()
    startTimer()
  }
})
</script>

<style scoped>
.mock-interview-page {
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

/* ========================================
   LOADING & EMPTY STATES
   ======================================== */
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

.empty-state {
  display: flex;
  justify-content: center;
  padding: var(--space-ma-xl) 0;
}

.empty-card {
  max-width: 400px;
  text-align: center;
  padding: var(--space-xl);
}

.empty-icon {
  margin-bottom: var(--space-lg);
  color: var(--color-text-ghost);
}

.empty-card h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
}

.empty-card p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
}

/* ========================================
   PROGRESS SECTION
   ======================================== */
.progress-section {
  margin-bottom: var(--space-lg);
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-ai);
  border-radius: var(--radius-full);
  transition: width 0.3s var(--ease-zen);
}

.progress-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

/* ========================================
   QUESTION CARD
   ======================================== */
.question-section {
  margin-bottom: var(--space-lg);
}

.question-card {
  padding: var(--space-xl);
}

.question-badges {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.category-badge,
.difficulty-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.category-behavioral { background: rgba(138, 79, 125, 0.15); color: #8a4f7d; }
.category-technical { background: rgba(61, 90, 108, 0.15); color: var(--color-ai); }
.category-situational { background: rgba(184, 122, 94, 0.15); color: var(--color-terra); }
.category-company_specific { background: rgba(122, 139, 110, 0.15); color: var(--color-koke); }
.category-salary_negotiation { background: rgba(196, 163, 90, 0.15); color: #8a7a2a; }

.difficulty-easy { background: rgba(122, 139, 110, 0.15); color: var(--color-koke); }
.difficulty-medium { background: rgba(196, 163, 90, 0.15); color: #8a7a2a; }
.difficulty-hard { background: rgba(180, 80, 80, 0.15); color: #b45050; }

.question-text {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
  line-height: 1.5;
  margin-bottom: var(--space-lg);
}

.star-hint {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: rgba(61, 90, 108, 0.08);
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  color: var(--color-ai);
  margin-bottom: var(--space-lg);
}

/* ========================================
   ANSWER SECTION
   ======================================== */
.answer-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-lg);
}

.answer-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.answer-textarea {
  width: 100%;
  padding: var(--space-md);
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-sumi);
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  resize: vertical;
  transition: all 0.2s var(--ease-zen);
}

.answer-textarea:focus {
  outline: none;
  border-color: var(--color-ai);
  box-shadow: 0 0 0 3px rgba(61, 90, 108, 0.1);
}

.answer-textarea:disabled {
  background: var(--color-washi-aged);
  cursor: not-allowed;
}

.answer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-md);
}

.char-count {
  font-size: 0.75rem;
  color: var(--color-text-ghost);
}

.char-count.low {
  color: var(--color-terra);
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
   FEEDBACK SECTION
   ======================================== */
.feedback-section {
  margin-bottom: var(--space-lg);
}

.feedback-card {
  padding: var(--space-xl);
}

.feedback-header {
  display: flex;
  gap: var(--space-lg);
  align-items: center;
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.score-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-circle.score-excellent { background: rgba(122, 139, 110, 0.15); color: var(--color-koke); }
.score-circle.score-good { background: rgba(61, 90, 108, 0.15); color: var(--color-ai); }
.score-circle.score-adequate { background: rgba(196, 163, 90, 0.15); color: #8a7a2a; }
.score-circle.score-needs-improvement { background: rgba(180, 80, 80, 0.15); color: #b45050; }

.score-value {
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1;
}

.score-label {
  font-size: 0.625rem;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  margin-top: 2px;
}

.feedback-title h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
}

.rating-description {
  color: var(--color-text-secondary);
  margin: 0;
}

.feedback-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.feedback-block h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: var(--space-md);
}

.feedback-block.strengths h4 { color: var(--color-koke); }
.feedback-block.improvements h4 { color: var(--color-terra); }

.feedback-block ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feedback-block li {
  position: relative;
  padding-left: var(--space-md);
  margin-bottom: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.feedback-block li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
}

.feedback-block.strengths li::before { background: var(--color-koke); }
.feedback-block.improvements li::before { background: var(--color-terra); }

.suggestion-block {
  padding: var(--space-lg);
  background: rgba(61, 90, 108, 0.05);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.suggestion-block h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-ai);
  margin-bottom: var(--space-md);
}

.suggestion-block p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* ========================================
   STAR ANALYSIS
   ======================================== */
.star-analysis {
  margin-bottom: var(--space-lg);
}

.star-analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.star-analysis h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-ai);
  margin: 0;
}

.detailed-star-section {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.star-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.star-component {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-sand);
}

.star-component.quality-strong { border-left-color: var(--color-koke); }
.star-component.quality-adequate { border-left-color: var(--color-ai); }
.star-component.quality-weak { border-left-color: #c4a35a; }
.star-component.quality-missing { border-left-color: #b45050; }

.star-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.star-letter {
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

.star-name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-sumi);
}

.star-status {
  margin-left: auto;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: #b45050;
}

.star-status.present {
  color: var(--color-koke);
}

.star-feedback {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* ========================================
   ASSESSMENT ROW
   ======================================== */
.assessment-row {
  display: flex;
  gap: var(--space-xl);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-border-light);
  margin-bottom: var(--space-lg);
}

.assessment-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.assessment-label {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
}

.assessment-value {
  font-size: 0.8125rem;
  font-weight: 600;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

.assessment-value.length-too_short,
.assessment-value.length-too_long,
.assessment-value.structure-unstructured {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.assessment-value.length-adequate,
.assessment-value.structure-partially_structured {
  background: rgba(196, 163, 90, 0.15);
  color: #8a7a2a;
}

.assessment-value.structure-well_structured {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.feedback-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}

/* ========================================
   SUMMARY SECTION
   ======================================== */
.summary-section {
  margin-top: var(--space-lg);
}

.summary-card {
  padding: var(--space-xl);
}

.summary-header {
  display: flex;
  gap: var(--space-lg);
  align-items: center;
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.summary-score-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.summary-title h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.summary-title p {
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
}

.category-scores {
  margin-bottom: var(--space-xl);
}

.category-scores h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-md);
}

.scores-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.score-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.score-category {
  width: 120px;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.score-bar-container {
  flex: 1;
  height: 8px;
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.score-bar {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.5s var(--ease-zen);
}

.score-bar.score-excellent { background: var(--color-koke); }
.score-bar.score-good { background: var(--color-ai); }
.score-bar.score-adequate { background: #c4a35a; }
.score-bar.score-needs-improvement { background: #b45050; }

.score-number {
  width: 40px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi);
  text-align: right;
}

.summary-block {
  margin-bottom: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-washi);
  border-radius: var(--radius-md);
}

.summary-block h3 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-md);
  color: var(--color-koke);
}

.summary-block.improvements h3 {
  color: var(--color-terra);
}

.summary-block.next-steps h3 {
  color: var(--color-ai);
}

.summary-block ul,
.summary-block ol {
  margin: 0;
  padding-left: var(--space-lg);
}

.summary-block li {
  margin-bottom: var(--space-sm);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.summary-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

/* ========================================
   TIMER STYLES
   ======================================== */
.timer-settings-section {
  margin-bottom: var(--space-md);
}

.timer-toggle-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.timer-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
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

.timer-toggle-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.timer-toggle-btn.active {
  background: rgba(61, 90, 108, 0.1);
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.timer-settings-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.75rem;
  color: var(--color-text-ghost);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.2s var(--ease-zen);
}

.timer-settings-btn:hover {
  color: var(--color-ai);
}

.timer-settings-panel {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
}

.timer-minutes-label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.timer-minutes-select {
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-sumi);
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.timer-display-container {
  display: flex;
  justify-content: center;
  margin-top: var(--space-lg);
}

.timer-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.timer-progress-ring {
  position: relative;
  width: 80px;
  height: 80px;
}

.timer-progress-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.timer-ring-bg {
  fill: none;
  stroke: var(--color-washi-aged);
  stroke-width: 3;
}

.timer-ring-fill {
  fill: none;
  stroke: var(--color-ai);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s var(--ease-zen);
}

.timer-low .timer-ring-fill {
  stroke: #c4a35a;
}

.timer-critical .timer-ring-fill {
  stroke: #b45050;
  animation: timer-pulse 0.5s ease-in-out infinite;
}

.timer-expired .timer-ring-fill {
  stroke: #b45050;
}

@keyframes timer-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.timer-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.timer-time {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-sumi);
  font-variant-numeric: tabular-nums;
}

.timer-low .timer-time {
  color: #8a7a2a;
}

.timer-critical .timer-time {
  color: #b45050;
}

.timer-expired .timer-time {
  color: #b45050;
}

.timer-expired-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #b45050;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  animation: timer-pulse 1s ease-in-out infinite;
}

/* Timer Statistics in Summary */
.timer-stats-block {
  margin-bottom: var(--space-lg);
  padding: var(--space-lg);
  background: rgba(61, 90, 108, 0.05);
  border-radius: var(--radius-md);
}

.timer-stats-block h3 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-lg);
  color: var(--color-ai);
}

.timer-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.timer-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.timer-stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-sumi);
  line-height: 1;
  margin-bottom: var(--space-xs);
}

.timer-stat-label {
  font-size: 0.75rem;
  color: var(--color-text-ghost);
}

.timer-stat-item.stat-warning .timer-stat-value {
  color: #b45050;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .feedback-grid {
    grid-template-columns: 1fr;
  }

  .star-grid {
    grid-template-columns: 1fr;
  }

  .feedback-header,
  .summary-header {
    flex-direction: column;
    text-align: center;
  }

  .assessment-row {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .summary-actions {
    flex-direction: column;
  }

  .summary-actions .zen-btn {
    width: 100%;
    justify-content: center;
  }

  .timer-stats-grid {
    grid-template-columns: 1fr;
    gap: var(--space-md);
  }

  .timer-toggle-row {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ========================================
   QUESTION TYPE HINTS (Non-behavioral)
   ======================================== */
.question-type-hint {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: rgba(61, 90, 108, 0.08);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.question-type-hint svg {
  flex-shrink: 0;
  color: var(--color-ai);
  margin-top: 2px;
}

.question-type-hint .hint-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.question-type-hint .hint-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-ai);
}

.question-type-hint .hint-text {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* ========================================
   STAR NOT APPLICABLE HINT
   ======================================== */
.star-not-applicable-hint {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: rgba(155, 149, 143, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  border-left: 3px solid var(--color-stone);
}

.star-not-applicable-hint svg {
  flex-shrink: 0;
  color: var(--color-stone);
  margin-top: 2px;
}

.star-not-applicable-hint .hint-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.star-not-applicable-hint .hint-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-sumi-light);
}

.star-not-applicable-hint .hint-text {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}
</style>
