<template>
  <div class="interview-stats-widget zen-card">
    <div class="widget-header">
      <div class="widget-title">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <h3>Interview-Statistiken</h3>
      </div>
      <router-link to="/applications" class="widget-link">
        Alle ansehen
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </router-link>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="widget-loading">
      <div class="loading-spinner"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!stats || stats.total_interviews === 0" class="widget-empty">
      <p>Noch keine Interview-Daten vorhanden.</p>
      <p class="hint">Tragen Sie Interview-Ergebnisse in Ihren Bewerbungen ein.</p>
    </div>

    <!-- Stats Content -->
    <div v-else class="widget-content">
      <!-- Success Rate -->
      <div class="success-rate-section">
        <div class="success-rate-ring">
          <svg viewBox="0 0 36 36" class="circular-chart">
            <path
              class="circle-bg"
              d="M18 2.0845
                 a 15.9155 15.9155 0 0 1 0 31.831
                 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              class="circle"
              :stroke-dasharray="`${stats.success_rate}, 100`"
              d="M18 2.0845
                 a 15.9155 15.9155 0 0 1 0 31.831
                 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div class="rate-value">{{ stats.success_rate }}%</div>
        </div>
        <div class="rate-label">Erfolgsrate</div>
      </div>

      <!-- Result Breakdown -->
      <div class="result-breakdown">
        <div
          v-for="(count, result) in stats.result_breakdown"
          :key="result"
          v-show="count > 0 || ['scheduled', 'passed', 'rejected'].includes(result)"
          class="result-item"
        >
          <span class="result-dot" :style="{ background: getResultColor(result) }"></span>
          <span class="result-label">{{ getResultLabel(result) }}</span>
          <span class="result-count">{{ count }}</span>
        </div>
      </div>

      <!-- Upcoming Interviews -->
      <div v-if="stats.upcoming_interviews?.length > 0" class="upcoming-section">
        <h4>Kommende Interviews</h4>
        <div class="upcoming-list">
          <router-link
            v-for="interview in stats.upcoming_interviews.slice(0, 3)"
            :key="interview.id"
            :to="`/applications/${interview.id}/interview`"
            class="upcoming-item"
          >
            <div class="upcoming-info">
              <span class="upcoming-company">{{ interview.firma }}</span>
              <span class="upcoming-position">{{ interview.position }}</span>
            </div>
            <span class="upcoming-date">{{ formatDate(interview.interview_date) }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'

const stats = ref(null)
const loading = ref(true)

const resultLabels = {
  scheduled: 'Geplant',
  completed: 'Durchgefuehrt',
  passed: 'Bestanden',
  rejected: 'Absage',
  offer_received: 'Angebot'
}

const resultColors = {
  scheduled: 'var(--color-ai)',
  completed: 'var(--color-terra)',
  passed: 'var(--color-koke)',
  rejected: '#b45050',
  offer_received: '#4a9d4a'
}

const getResultLabel = (result) => resultLabels[result] || result
const getResultColor = (result) => resultColors[result] || 'var(--color-stone)'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  try {
    const { data } = await api.get('/applications/interview-stats')
    if (data.success) {
      stats.value = data.data
    }
  } catch (err) {
    console.error('Failed to load interview stats:', err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.interview-stats-widget {
  padding: var(--space-lg);
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

.widget-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-ai);
  text-decoration: none;
  transition: gap var(--transition-base);
}

.widget-link:hover {
  gap: var(--space-sm);
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

/* Empty State */
.widget-empty {
  text-align: center;
  padding: var(--space-lg);
  color: var(--color-text-tertiary);
}

.widget-empty p {
  margin: 0;
}

.widget-empty .hint {
  font-size: 0.8125rem;
  margin-top: var(--space-xs);
}

/* Content */
.widget-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* Success Rate Ring */
.success-rate-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.success-rate-ring {
  position: relative;
  width: 100px;
  height: 100px;
}

.circular-chart {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  fill: none;
  stroke: var(--color-sand);
  stroke-width: 3;
}

.circle {
  fill: none;
  stroke: var(--color-koke);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

.rate-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.rate-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-top: var(--space-sm);
}

/* Result Breakdown */
.result-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
}

.result-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
}

.result-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.result-label {
  color: var(--color-text-secondary);
}

.result-count {
  font-weight: 600;
  color: var(--color-sumi);
  margin-left: var(--space-xs);
}

/* Upcoming Section */
.upcoming-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-md);
}

.upcoming-section h4 {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin: 0 0 var(--space-sm) 0;
}

.upcoming-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.upcoming-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all var(--transition-base);
}

.upcoming-item:hover {
  background: var(--color-ai-subtle);
}

.upcoming-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.upcoming-company {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.upcoming-position {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.upcoming-date {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-ai);
  white-space: nowrap;
}
</style>
