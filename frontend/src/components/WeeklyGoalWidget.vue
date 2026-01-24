<template>
  <div class="weekly-goal-widget zen-card" :class="{ 'goal-achieved': isAchieved }">
    <div class="widget-header">
      <div class="widget-title">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        <h3>Wochenziel</h3>
      </div>
      <button
        v-if="!editing"
        @click="startEditing"
        class="edit-goal-btn"
        aria-label="Ziel bearbeiten"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="widget-loading">
      <div class="loading-spinner"></div>
    </div>

    <!-- Goal Content -->
    <div v-else class="widget-content">
      <!-- Goal Header with Edit -->
      <div class="goal-header">
        <div v-if="editing" class="goal-edit">
          <input
            ref="goalInput"
            type="number"
            v-model.number="editGoal"
            min="1"
            max="50"
            @keyup.enter="saveGoal"
            @keyup.escape="cancelEditing"
            class="goal-input"
          />
          <span class="goal-suffix">Bewerbungen</span>
          <div class="edit-actions">
            <button @click="saveGoal" class="save-btn" :disabled="saving">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </button>
            <button @click="cancelEditing" class="cancel-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
        <div v-else class="goal-display">
          <span class="goal-icon" v-if="isAchieved">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </span>
          <span class="goal-text">
            <strong>{{ completed }}</strong> von <strong>{{ goal }}</strong> Bewerbungen diese Woche
          </span>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="progress-container">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: `${progress}%` }"
            :class="{ 'achieved': isAchieved }"
          ></div>
        </div>
        <span class="progress-text">{{ progress }}%</span>
      </div>

      <!-- Achievement Message -->
      <div v-if="isAchieved" class="achievement-message">
        <span class="achievement-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </span>
        <span>Ziel erreicht! Weiter so!</span>
      </div>

      <!-- Motivational Message -->
      <div v-else class="motivation-message">
        <span v-if="remaining === 1">Noch eine Bewerbung bis zum Ziel!</span>
        <span v-else-if="remaining <= 2">Fast geschafft - nur noch {{ remaining }} Bewerbungen!</span>
        <span v-else>Noch {{ remaining }} Bewerbungen bis zum Wochenziel</span>
      </div>

      <!-- CTA Button -->
      <router-link to="/new-application" class="zen-btn zen-btn-primary cta-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Neue Bewerbung
      </router-link>
    </div>

    <!-- Confetti Animation (for goal achievement) -->
    <div v-if="showConfetti" class="confetti-container">
      <div v-for="i in 20" :key="i" class="confetti" :style="confettiStyle(i)"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import api from '../api/client'

const loading = ref(true)
const goal = ref(5)
const completed = ref(0)
const progress = ref(0)
const isAchieved = ref(false)
const editing = ref(false)
const editGoal = ref(5)
const saving = ref(false)
const goalInput = ref(null)
const showConfetti = ref(false)
const previousAchieved = ref(false)

// GOAL-002-BUG-001: Track celebration in localStorage to prevent repeat triggers on page load
const CELEBRATION_KEY = 'obojobs-goal-celebration'
const celebrationShownThisWeek = ref(false)

const remaining = computed(() => Math.max(0, goal.value - completed.value))

// Get current week identifier (ISO week)
const getCurrentWeekId = () => {
  const now = new Date()
  const onejan = new Date(now.getFullYear(), 0, 1)
  const week = Math.ceil((((now - onejan) / 86400000) + onejan.getDay() + 1) / 7)
  return `${now.getFullYear()}-W${week}`
}

// Check if celebration was already shown this week
const wasCelebrationShownThisWeek = () => {
  const stored = localStorage.getItem(CELEBRATION_KEY)
  return stored === getCurrentWeekId()
}

// Mark celebration as shown this week
const markCelebrationShown = () => {
  localStorage.setItem(CELEBRATION_KEY, getCurrentWeekId())
  celebrationShownThisWeek.value = true
}

const startEditing = () => {
  editGoal.value = goal.value
  editing.value = true
  nextTick(() => {
    goalInput.value?.focus()
    goalInput.value?.select()
  })
}

const cancelEditing = () => {
  editing.value = false
  editGoal.value = goal.value
}

const saveGoal = async () => {
  if (saving.value) return
  if (editGoal.value < 1 || editGoal.value > 50) return

  saving.value = true
  try {
    const { data } = await api.put('/stats/weekly-goal', { goal: editGoal.value })
    if (data.success) {
      goal.value = data.data.goal
      completed.value = data.data.completed
      progress.value = data.data.progress
      isAchieved.value = data.data.is_achieved
      editing.value = false
    }
  } catch (err) {
    console.error('Failed to update goal:', err)
  } finally {
    saving.value = false
  }
}

const loadGoalData = async () => {
  try {
    const { data } = await api.silent.get('/stats/weekly-goal')
    if (data.success) {
      goal.value = data.data.goal
      completed.value = data.data.completed
      progress.value = data.data.progress
      isAchieved.value = data.data.is_achieved
      editGoal.value = data.data.goal
    }
  } catch (err) {
    console.error('Failed to load weekly goal:', err)
  } finally {
    loading.value = false
  }
}

// Watch for goal achievement to trigger confetti
// GOAL-002-BUG-001: Only show confetti once per week, not on page refreshes
watch(isAchieved, (newValue, _oldValue) => {
  if (newValue && !previousAchieved.value && !wasCelebrationShownThisWeek()) {
    showConfetti.value = true
    markCelebrationShown()
    setTimeout(() => {
      showConfetti.value = false
    }, 3000)
  }
  previousAchieved.value = newValue
})

const confettiStyle = (i) => {
  const colors = ['#4a9d4a', '#3D5A6C', '#C8B273', '#A67B5B', '#6B8E23']
  const left = Math.random() * 100
  const delay = Math.random() * 0.5
  const duration = 1.5 + Math.random() * 1
  const rotation = Math.random() * 360

  return {
    left: `${left}%`,
    backgroundColor: colors[i % colors.length],
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    transform: `rotate(${rotation}deg)`,
  }
}

onMounted(() => {
  loadGoalData()
})
</script>

<style scoped>
.weekly-goal-widget {
  padding: var(--space-lg);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
}

.weekly-goal-widget.goal-achieved {
  border-color: var(--color-koke);
  background: linear-gradient(135deg, var(--color-bg-elevated) 0%, rgba(107, 142, 35, 0.05) 100%);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.widget-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.widget-title svg {
  color: var(--color-ai);
}

.widget-title h3 {
  font-size: 1rem;
  font-weight: 500;
  margin: 0;
  color: var(--color-sumi);
}

.edit-goal-btn {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.edit-goal-btn:hover {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

/* Loading */
.widget-loading {
  display: flex;
  justify-content: center;
  padding: var(--space-xl);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--color-sand);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Content */
.widget-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* Goal Header */
.goal-header {
  display: flex;
  align-items: center;
}

.goal-display {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.goal-icon {
  color: var(--color-koke);
  display: flex;
}

.goal-text {
  font-size: 1rem;
  color: var(--color-text-secondary);
}

.goal-text strong {
  color: var(--color-sumi);
  font-weight: 600;
}

/* Goal Edit */
.goal-edit {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.goal-input {
  width: 60px;
  padding: var(--space-xs) var(--space-sm);
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  border: 1px solid var(--color-ai);
  border-radius: var(--radius-sm);
  background: var(--color-bg-elevated);
  color: var(--color-sumi);
}

.goal-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(61, 90, 108, 0.2);
}

.goal-suffix {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.edit-actions {
  display: flex;
  gap: var(--space-xs);
}

.save-btn,
.cancel-btn {
  padding: var(--space-xs);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.save-btn {
  background: var(--color-koke);
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #5a7a2e;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  background: var(--color-sand);
  color: var(--color-text-secondary);
}

.cancel-btn:hover {
  background: var(--color-stone);
  color: var(--color-sumi);
}

/* Progress Bar */
.progress-container {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.progress-bar {
  flex: 1;
  height: 12px;
  background: var(--color-sand);
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-ai);
  border-radius: 6px;
  transition: width 0.6s ease-out, background-color 0.3s ease;
}

.progress-fill.achieved {
  background: var(--color-koke);
}

.progress-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi);
  min-width: 40px;
  text-align: right;
}

/* Messages */
.achievement-message,
.motivation-message {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
}

.achievement-message {
  background: rgba(107, 142, 35, 0.1);
  color: var(--color-koke);
  font-weight: 500;
}

.achievement-icon {
  display: flex;
}

.motivation-message {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

/* CTA Button */
.cta-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  font-weight: 500;
  margin-top: var(--space-sm);
  text-decoration: none;
  transition: all var(--transition-base);
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lifted);
}

/* Confetti Animation */
/* GOAL-002-BUG-002: Fixed clipping by allowing overflow visible during animation */
.confetti-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: visible;
  z-index: 10;
}

.confetti {
  position: absolute;
  top: -10px;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  animation: confetti-fall linear forwards;
}

@keyframes confetti-fall {
  0% {
    opacity: 1;
    transform: translateY(0) rotate(0deg);
  }
  100% {
    opacity: 0;
    transform: translateY(300px) rotate(720deg);
  }
}

/* Responsive */
@media (max-width: 480px) {
  .goal-edit {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .edit-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .progress-container {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-xs);
  }

  .progress-text {
    text-align: center;
  }
}
</style>
