<template>
  <div class="job-recommendations">
    <div class="recommendations-header">
      <div class="header-content">
        <h2>Job-Empfehlungen</h2>
        <p class="subtitle">Basierend auf Ihrem Profil und Ihren Skills</p>
      </div>
      <div class="header-actions">
        <router-link to="/job-dashboard" class="zen-btn zen-btn-sm zen-btn-ghost">
          Alle Vorschläge
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="stats" class="stats-row">
      <div class="stat-item">
        <span class="stat-value">{{ stats.active }}</span>
        <span class="stat-label">Aktiv</span>
      </div>
      <div class="stat-item stat-sehr-gut">
        <span class="stat-value">{{ stats.by_score?.sehr_gut || 0 }}</span>
        <span class="stat-label">Sehr gut (80%+)</span>
      </div>
      <div class="stat-item stat-gut">
        <span class="stat-value">{{ stats.by_score?.gut || 0 }}</span>
        <span class="stat-label">Gut (60-79%)</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.applied }}</span>
        <span class="stat-label">Beworben</span>
      </div>
    </div>

    <!-- Loading State - Skeleton -->
    <div v-if="loading" class="loading-skeleton" aria-label="Lade Empfehlungen">
      <div v-for="i in 3" :key="i" class="skeleton-card zen-card">
        <div class="skeleton-card-header">
          <div class="skeleton skeleton-badge"></div>
          <div class="skeleton-job-info">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text-short"></div>
          </div>
        </div>
        <div class="skeleton-card-body">
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-text-short"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="recommendations.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/>
          <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
      </div>
      <h3 v-if="searching">Suche passende Jobs...</h3>
      <template v-else>
        <h3>Noch keine passenden Jobs gefunden</h3>
        <p>
          Laden Sie Ihren Lebenslauf unter Dokumente hoch, damit wir
          automatisch passende Stellen für Sie finden.
        </p>
        <router-link to="/documents" class="zen-btn zen-btn-ai">
          Lebenslauf hochladen
        </router-link>
      </template>
    </div>

    <!-- Recommendations List (Top 3) -->
    <div v-else class="recommendations-list">
      <div
        v-for="rec in recommendations.slice(0, 3)"
        :key="rec.id"
        class="recommendation-card zen-card"
        :class="[`score-${rec.fit_category}`]"
      >
        <div class="card-header">
          <div class="score-badge" :class="rec.fit_category">
            {{ rec.fit_score }}%
          </div>
          <div class="job-info">
            <h3 class="job-title">{{ rec.job_title || 'Unbekannte Position' }}</h3>
            <p class="company-name">{{ rec.company_name || 'Unbekanntes Unternehmen' }}</p>
            <p v-if="rec.location" class="location">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              {{ rec.location }}
            </p>
          </div>
          <div class="card-actions">
            <button
              v-if="rec.job_url"
              @click="openJobUrl(rec.job_url)"
              class="action-btn"
              title="Stellenanzeige öffnen"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </button>
            <button
              @click="dismissRecommendation(rec.id)"
              class="action-btn action-dismiss"
              title="Ausblenden"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="card-body">
          <div v-if="rec.source" class="source-tag">
            {{ getSourceLabel(rec.source) }}
          </div>
          <p class="recommended-at">
            Empfohlen am {{ formatDate(rec.recommended_at) }}
          </p>
        </div>

        <div class="card-footer">
          <router-link
            :to="`/new-application?url=${encodeURIComponent(rec.job_url)}`"
            class="zen-btn zen-btn-sm"
            @click="markAsApplied(rec.id)"
          >
            Bewerbung starten
          </router-link>
        </div>
      </div>

      <!-- View All Link -->
      <div v-if="recommendations.length > 3" class="view-all-link">
        <router-link to="/job-dashboard" class="zen-btn zen-btn-ghost">
          Alle {{ recommendations.length }} Vorschläge ansehen
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { getFullLocale } from '../i18n'

const recommendations = ref([])
const stats = ref(null)
const loading = ref(true)
const searching = ref(false)

const loadRecommendations = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/recommendations')
    recommendations.value = data.recommendations || []
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const { data } = await api.get('/recommendations/stats')
    stats.value = data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const searchJobs = async () => {
  searching.value = true
  try {
    await api.post('/recommendations/search', {})
    await loadRecommendations()
    await loadStats()
  } catch (error) {
    console.error('Failed to search jobs:', error)
  } finally {
    searching.value = false
  }
}

const dismissRecommendation = async (id) => {
  try {
    await api.post(`/recommendations/${id}/dismiss`)
    recommendations.value = recommendations.value.filter(r => r.id !== id)
    await loadStats()
  } catch (error) {
    console.error('Failed to dismiss:', error)
  }
}

const markAsApplied = async (id) => {
  try {
    await api.post(`/recommendations/${id}/apply`)
  } catch (error) {
    console.error('Failed to mark as applied:', error)
  }
}

const openJobUrl = (url) => {
  window.open(url, '_blank')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const SOURCE_LABELS = {
  indeed: 'Indeed',
  stepstone: 'StepStone',
  xing: 'XING',
  arbeitsagentur: 'Arbeitsagentur',
  generic: 'Web',
}

const getSourceLabel = (source) => SOURCE_LABELS[source] || source

onMounted(async () => {
  await loadRecommendations()
  await loadStats()

  // Auto-search if no recommendations exist yet
  if (recommendations.value.length === 0) {
    await searchJobs()
  }
})
</script>

<style scoped>
.job-recommendations {
  padding: var(--space-lg);
}

.recommendations-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-lg);
}

.header-content h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

/* Stats Row */
.stats-row {
  display: flex;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-sumi);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-sehr-gut .stat-value {
  color: var(--color-success);
}

.stat-gut .stat-value {
  color: var(--color-warning);
}

/* Loading Skeleton */
.loading-skeleton {
  display: grid;
  gap: var(--space-md);
}

.skeleton-card {
  padding: var(--space-lg);
}

.skeleton-card-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.skeleton-badge {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.skeleton-job-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-title {
  height: 1.25rem;
  width: 70%;
}

.skeleton-text {
  height: 1rem;
  width: 50%;
}

.skeleton-text-short {
  height: 0.875rem;
  width: 30%;
}

.skeleton-card-body {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.skeleton-tag {
  height: 1.5rem;
  width: 60px;
  border-radius: var(--radius-sm);
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

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--space-xl);
}

.empty-icon {
  margin-bottom: var(--space-md);
  color: var(--color-text-ghost);
}

.empty-state h3 {
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.empty-state p {
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0 auto var(--space-lg);
}

/* Recommendations List */
.recommendations-list {
  display: grid;
  gap: var(--space-md);
}

.recommendation-card {
  padding: var(--space-lg);
  transition: all var(--transition-base);
}

.recommendation-card:hover {
  box-shadow: var(--shadow-lifted);
}

.card-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.score-badge {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  color: white;
}

.score-badge.sehr_gut {
  background: var(--color-success);
}

.score-badge.gut {
  background: var(--color-warning);
}

.score-badge.mittel {
  background: var(--color-orange, #f57c00);
}

.score-badge.niedrig {
  background: var(--color-error);
}

.job-info {
  flex: 1;
  min-width: 0;
}

.job-title {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
}

.company-name {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.location {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.card-actions {
  display: flex;
  gap: var(--space-xs);
}

.action-btn {
  padding: var(--space-sm);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.action-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.action-dismiss:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

.card-body {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.source-tag {
  font-size: 0.75rem;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-sm);
}

.recommended-at {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  margin: 0;
}

.card-footer {
  margin-top: var(--space-md);
}

.view-all-link {
  display: flex;
  justify-content: center;
  margin-top: var(--space-lg);
}

/* Responsive */
@media (max-width: 768px) {
  .recommendations-header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .stats-row {
    flex-wrap: wrap;
    justify-content: center;
  }

  .card-header {
    flex-wrap: wrap;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
