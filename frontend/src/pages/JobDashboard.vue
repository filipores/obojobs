<template>
  <div class="job-dashboard">
    <!-- Header -->
    <section class="dashboard-header">
      <div class="container">
        <div class="header-content">
          <h1>{{ $t('jobDashboard.title') }}</h1>
          <p class="subtitle">{{ $t('jobDashboard.subtitle') }}</p>
        </div>

        <!-- Compact Filter -->
        <div class="filter-bar">
          <div class="filter-field">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            <input
              v-model="filters.location"
              type="text"
              :placeholder="$t('jobDashboard.locationPlaceholder')"
              class="filter-input"
            />
          </div>
          <div class="filter-field">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            <select v-model="filters.workType" class="filter-select">
              <option value="">{{ $t('jobDashboard.allWorkTypes') }}</option>
              <option value="vollzeit">{{ $t('jobDashboard.fullTime') }}</option>
              <option value="teilzeit">{{ $t('jobDashboard.partTime') }}</option>
              <option value="remote">Remote</option>
            </select>
          </div>
          <button @click="refresh" class="refresh-btn" :disabled="searching" :title="$t('jobDashboard.refresh')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" :class="{ spinning: loading || searching }">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M8 16H3v5"/>
            </svg>
          </button>
        </div>
      </div>
    </section>

    <!-- Loading Skeleton -->
    <section v-if="loading" class="suggestions-section">
      <div class="container">
        <div class="suggestions-grid">
          <div v-for="i in 6" :key="i" class="skeleton-card zen-card">
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
      </div>
    </section>

    <!-- No Skills Empty State -->
    <section v-else-if="!hasSkills" class="suggestions-section">
      <div class="container">
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h3>{{ $t('jobDashboard.noSkillsTitle') }}</h3>
          <p>{{ $t('jobDashboard.noSkills') }}</p>
          <router-link to="/documents" class="zen-btn zen-btn-ai">
            {{ $t('jobDashboard.uploadCV') }}
          </router-link>
        </div>
      </div>
    </section>

    <!-- No Suggestions -->
    <section v-else-if="filteredSuggestions.length === 0" class="suggestions-section">
      <div class="container">
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
          </div>
          <h3 v-if="searching">Suche passende Jobs...</h3>
          <template v-else>
            <h3>{{ $t('jobDashboard.noSuggestionsTitle') }}</h3>
            <p>{{ $t('jobDashboard.noSuggestions') }}</p>
            <button @click="refresh" class="zen-btn zen-btn-ai">
              Jetzt suchen
            </button>
          </template>
        </div>
      </div>
    </section>

    <!-- Suggestions Grid -->
    <section v-else class="suggestions-section">
      <div class="container">
        <div class="suggestions-grid">
          <div
            v-for="rec in filteredSuggestions"
            :key="rec.id"
            class="suggestion-card zen-card"
            :class="[`score-${rec.fit_category}`]"
          >
            <div class="card-header">
              <div class="score-badge" :class="rec.fit_category">
                {{ rec.fit_score }}%
              </div>
              <div class="job-info">
                <h3 class="job-title">{{ rec.job_title || $t('jobDashboard.unknownPosition') }}</h3>
                <p class="company-name">{{ rec.company_name || $t('jobDashboard.unknownCompany') }}</p>
                <p v-if="rec.location" class="location">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                  {{ rec.location }}
                </p>
              </div>
            </div>

            <div v-if="rec.source" class="card-meta">
              <span class="source-tag">{{ getSourceLabel(rec.source) }}</span>
              <span class="recommended-at">{{ formatDate(rec.recommended_at) }}</span>
            </div>

            <div class="card-actions">
              <router-link
                v-if="rec.job_url"
                :to="`/new-application?url=${encodeURIComponent(rec.job_url)}`"
                class="zen-btn zen-btn-sm zen-btn-ai"
                @click="markAsApplied(rec.id)"
              >
                {{ $t('jobDashboard.apply') }}
              </router-link>
              <button
                v-if="rec.job_url"
                @click="openJobUrl(rec.job_url)"
                class="zen-btn zen-btn-sm zen-btn-ghost"
              >
                {{ $t('jobDashboard.openJob') }}
              </button>
              <button
                @click="dismissSuggestion(rec.id)"
                class="action-btn action-dismiss"
                :title="$t('jobDashboard.dismiss')"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Load More -->
        <div v-if="hasMore" class="load-more">
          <button @click="loadMore" class="zen-btn zen-btn-ghost" :disabled="loadingMore">
            <span v-if="loadingMore">{{ $t('common.loading') }}</span>
            <span v-else>{{ $t('jobDashboard.loadMore') }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Stats Summary -->
    <section v-if="stats && !loading" class="stats-section">
      <div class="container">
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ stats.active }}</span>
            <span class="stat-label">{{ $t('jobDashboard.statsActive') }}</span>
          </div>
          <div class="stat-item stat-sehr-gut">
            <span class="stat-value">{{ stats.by_score?.sehr_gut || 0 }}</span>
            <span class="stat-label">{{ $t('jobDashboard.statsSehrGut') }}</span>
          </div>
          <div class="stat-item stat-gut">
            <span class="stat-value">{{ stats.by_score?.gut || 0 }}</span>
            <span class="stat-label">{{ $t('jobDashboard.statsGut') }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.applied }}</span>
            <span class="stat-label">{{ $t('jobDashboard.statsApplied') }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useJobRecommendations } from '../composables/useJobRecommendations'
import { getFullLocale } from '../i18n'

const {
  filteredSuggestions,
  stats,
  loading,
  loadingMore,
  hasMore,
  filters,
  hasSkills,
  searching,
  loadSuggestions,
  loadMore,
  loadStats,
  searchJobs,
  dismissSuggestion,
  markAsApplied
} = useJobRecommendations()

const refresh = async () => {
  await searchJobs({
    location: filters.value.location,
    workType: filters.value.workType,
  })
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
  await loadSuggestions()
  await loadStats()

  if (filteredSuggestions.value.length === 0 && hasSkills.value) {
    await refresh()
  }
})
</script>

<style scoped>
.job-dashboard {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
}

/* ========================================
   HEADER
   ======================================== */
.dashboard-header {
  padding: var(--space-xl) 0 var(--space-lg);
}

.dashboard-header .container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.header-content h1 {
  font-size: 1.75rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  margin: 0;
}

/* ========================================
   FILTER BAR
   ======================================== */
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.filter-field {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
}

.filter-field:focus-within {
  border-color: var(--color-ai);
}

.filter-input,
.filter-select {
  border: none;
  background: transparent;
  font-size: 0.875rem;
  color: var(--color-sumi);
  outline: none;
  min-width: 120px;
}

.filter-select {
  cursor: pointer;
}

.refresh-btn {
  padding: var(--space-sm);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   SUGGESTIONS GRID
   ======================================== */
.suggestions-section {
  padding: var(--space-lg) 0 var(--space-xl);
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--space-md);
}

.suggestion-card {
  padding: var(--space-lg);
  transition: all var(--transition-base);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.suggestion-card:hover {
  box-shadow: var(--shadow-lifted);
}

/* ========================================
   CARD HEADER
   ======================================== */
.card-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.score-badge {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 600;
  color: white;
}

.score-badge.sehr_gut { background: var(--color-success); }
.score-badge.gut { background: var(--color-warning); }
.score-badge.mittel { background: var(--color-orange, #f57c00); }
.score-badge.niedrig { background: var(--color-error); }

.job-info {
  flex: 1;
  min-width: 0;
}

.job-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.company-name {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--space-xs);
}

.location {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
}

/* ========================================
   CARD META
   ======================================== */
.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding-top: var(--space-sm);
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
  font-size: 0.8125rem;
}

/* ========================================
   CARD ACTIONS
   ======================================== */
.card-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-top: auto;
}

.action-btn {
  padding: var(--space-xs);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-base);
  margin-left: auto;
}

.action-dismiss:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

/* ========================================
   LOAD MORE
   ======================================== */
.load-more {
  display: flex;
  justify-content: center;
  margin-top: var(--space-xl);
}

/* ========================================
   EMPTY STATE
   ======================================== */
.empty-state {
  text-align: center;
  padding: var(--space-xl);
  max-width: 400px;
  margin: 0 auto;
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
  margin-bottom: var(--space-lg);
}

/* ========================================
   STATS SECTION
   ======================================== */
.stats-section {
  padding: 0 0 var(--space-xl);
}

.stats-row {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
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

.stat-sehr-gut .stat-value { color: var(--color-success); }
.stat-gut .stat-value { color: var(--color-warning); }

/* ========================================
   LOADING SKELETON
   ======================================== */
.skeleton-card {
  padding: var(--space-lg);
}

.skeleton-card-header {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.skeleton-badge {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.skeleton-job-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-title { height: 1.25rem; width: 70%; }
.skeleton-text { height: 1rem; width: 50%; }
.skeleton-text-short { height: 0.875rem; width: 30%; }

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

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .dashboard-header .container {
    flex-direction: column;
  }

  .filter-bar {
    width: 100%;
    flex-wrap: wrap;
  }

  .filter-field {
    flex: 1;
    min-width: 0;
  }

  .suggestions-grid {
    grid-template-columns: 1fr;
  }

  .stats-row {
    flex-wrap: wrap;
    justify-content: center;
  }

  .card-actions {
    flex-wrap: wrap;
  }
}
</style>
