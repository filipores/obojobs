<template>
  <div class="job-dashboard">
    <div class="dashboard-container">
      <!-- Page Header -->
      <div class="page-header animate-fade-up">
        <div class="header-content">
          <h1>{{ $t('jobDashboard.title') }}</h1>
          <p class="subtitle">{{ $t('jobDashboard.subtitle') }}</p>
        </div>
      </div>

      <!-- Search Section -->
      <div class="search-section zen-card animate-fade-up">
        <h2 class="search-title">{{ $t('jobDashboard.searchTitle') }}</h2>
        <div class="search-form">
          <div class="search-field">
            <label for="search-location">{{ $t('jobDashboard.location') }}</label>
            <input
              id="search-location"
              v-model="searchFilters.location"
              type="text"
              class="form-input"
              :placeholder="$t('jobDashboard.locationPlaceholder')"
              :disabled="isSearching"
            />
          </div>
          <div class="search-field">
            <label for="search-worktime">{{ $t('jobDashboard.workingTime') }}</label>
            <select
              id="search-worktime"
              v-model="searchFilters.working_time"
              class="form-input"
              :disabled="isSearching"
            >
              <option value="">{{ $t('jobDashboard.allTypes') }}</option>
              <option value="vz">{{ $t('jobDashboard.fullTime') }}</option>
              <option value="tz">{{ $t('jobDashboard.partTime') }}</option>
              <option value="ho">{{ $t('jobDashboard.homeOffice') }}</option>
            </select>
          </div>
          <button
            @click="handleSearch"
            class="zen-btn zen-btn-ai search-btn"
            :disabled="isSearching"
          >
            <svg v-if="!isSearching" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
            <span v-if="isSearching">{{ $t('jobDashboard.searching') }}</span>
            <span v-else>{{ $t('jobDashboard.searchButton') }}</span>
          </button>
        </div>
      </div>

      <!-- Stats Row -->
      <div v-if="stats" class="stats-row animate-fade-up">
        <div class="stat-item">
          <span class="stat-value">{{ stats.active }}</span>
          <span class="stat-label">{{ $t('jobDashboard.statsActive') }}</span>
        </div>
        <div class="stat-item stat-sehr-gut">
          <span class="stat-value">{{ stats.by_score?.sehr_gut || 0 }}</span>
          <span class="stat-label">{{ $t('jobDashboard.statsVeryGood') }}</span>
        </div>
        <div class="stat-item stat-gut">
          <span class="stat-value">{{ stats.by_score?.gut || 0 }}</span>
          <span class="stat-label">{{ $t('jobDashboard.statsGood') }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.applied }}</span>
          <span class="stat-label">{{ $t('jobDashboard.statsApplied') }}</span>
        </div>
      </div>

      <!-- Search Results -->
      <div v-if="searchResults.length > 0" class="results-section animate-fade-up">
        <h2 class="section-title">{{ $t('jobDashboard.searchResults') }} ({{ searchResults.length }})</h2>
        <div class="results-grid">
          <div
            v-for="(job, index) in searchResults"
            :key="index"
            class="job-card zen-card"
            :class="[`score-${job.fit_category || 'mittel'}`]"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <div class="card-header">
              <div class="score-badge" :class="job.fit_category || 'mittel'">
                {{ job.fit_score || 50 }}%
              </div>
              <div class="job-info">
                <h3 class="job-title">{{ job.title || $t('jobDashboard.unknownPosition') }}</h3>
                <p class="company-name">{{ job.company || $t('jobDashboard.unknownCompany') }}</p>
                <p v-if="job.location" class="location">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                  {{ job.location }}
                </p>
              </div>
            </div>
            <div class="card-body">
              <div class="source-tag">Arbeitsagentur</div>
            </div>
            <div class="card-footer">
              <a
                v-if="job.url"
                :href="job.url"
                target="_blank"
                rel="noopener noreferrer"
                class="zen-btn zen-btn-sm zen-btn-ghost"
              >
                {{ $t('jobDashboard.openJob') }}
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading Skeleton -->
      <div v-if="isLoading" class="loading-skeleton">
        <div v-for="i in 3" :key="i" class="skeleton-card zen-card">
          <div class="skeleton-card-header">
            <div class="skeleton skeleton-badge"></div>
            <div class="skeleton-job-info">
              <div class="skeleton skeleton-title"></div>
              <div class="skeleton skeleton-text"></div>
              <div class="skeleton skeleton-text-short"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendations Section -->
      <div v-else-if="activeRecommendations.length > 0" class="recommendations-section animate-fade-up">
        <h2 class="section-title">{{ $t('jobDashboard.savedRecommendations') }} ({{ activeRecommendations.length }})</h2>
        <div class="results-grid">
          <div
            v-for="rec in activeRecommendations"
            :key="rec.id"
            class="job-card zen-card"
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
              <div class="card-actions">
                <button
                  v-if="rec.job_url"
                  @click="openUrl(rec.job_url)"
                  class="action-btn"
                  :title="$t('jobDashboard.openJob')"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                  </svg>
                </button>
                <button
                  @click="handleDismiss(rec.id)"
                  class="action-btn action-dismiss"
                  :title="$t('jobDashboard.dismiss')"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
                <button
                  @click="handleApply(rec.id)"
                  class="action-btn action-apply"
                  :title="$t('jobDashboard.markApplied')"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="card-body">
              <div v-if="rec.source" class="source-tag">
                {{ getSourceLabel(rec.source) }}
              </div>
              <p class="recommended-at">
                {{ formatDate(rec.recommended_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State (no recommendations and no search results) -->
      <div v-else-if="!isLoading && !isSearching" class="empty-state animate-fade-up">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
        </div>
        <h3>{{ $t('jobDashboard.emptyTitle') }}</h3>
        <p>{{ $t('jobDashboard.emptyDescription') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useJobRecommendations } from '../composables/useJobRecommendations'
import { getFullLocale } from '../i18n'

const {
  searchResults,
  stats,
  isLoading,
  isSearching,
  searchFilters,
  activeRecommendations,
  fetchRecommendations,
  fetchStats,
  searchJobs,
  dismissRecommendation,
  markAsApplied,
} = useJobRecommendations()

const handleSearch = async () => {
  try {
    await searchJobs()
  } catch (err) {
    console.error('Search failed:', err)
  }
}

const handleDismiss = async (id) => {
  await dismissRecommendation(id)
}

const handleApply = async (id) => {
  await markAsApplied(id)
}

const openUrl = (url) => {
  window.open(url, '_blank')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const getSourceLabel = (source) => {
  const labels = {
    'arbeitsagentur': 'Arbeitsagentur',
    'indeed': 'Indeed',
    'stepstone': 'StepStone',
    'manual': 'Manuell',
  }
  return labels[source] || source
}

onMounted(async () => {
  await Promise.all([fetchRecommendations(), fetchStats()])
})
</script>

<style scoped>
/* Use Wafu Design tokens for consistency */
.job-dashboard {
  padding: var(--space-lg) var(--space-ma);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* Fade up animation */
.animate-fade-up {
  animation: fadeUp 0.4s var(--ease-zen) both;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Page Header */
.page-header {
  margin-bottom: var(--space-sm);
}

.page-header h1 {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  margin: 0;
}

/* Search Section */
.search-section {
  padding: var(--space-lg);
}

.search-title {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
  color: var(--color-sumi);
}

.search-form {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
}

.search-field {
  flex: 1;
}

.search-field label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
  color: var(--color-text-secondary);
}

.form-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-family: inherit;
  background: var(--color-washi);
  color: var(--color-sumi);
  transition: border-color var(--transition-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-ai);
}

.search-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  white-space: nowrap;
  height: fit-content;
}

/* Stats Row */
.stats-row {
  display: flex;
  gap: var(--space-lg);
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

.stat-sehr-gut .stat-value { color: var(--color-success); }
.stat-gut .stat-value { color: var(--color-warning); }

/* Section titles */
.section-title {
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
  color: var(--color-sumi);
}

/* Results Grid */
.results-grid {
  display: grid;
  gap: var(--space-md);
}

/* Job Card */
.job-card {
  padding: var(--space-lg);
  transition: all var(--transition-base);
  animation: fadeUp 0.4s var(--ease-zen) both;
}

.job-card:hover {
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

.score-badge.sehr_gut { background: var(--color-success); }
.score-badge.gut { background: var(--color-warning); }
.score-badge.mittel { background: var(--color-orange, #f57c00); }
.score-badge.niedrig { background: var(--color-error); }

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

.action-apply:hover {
  border-color: var(--color-success);
  color: var(--color-success);
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

.skeleton-title { height: 1.25rem; width: 70%; }
.skeleton-text { height: 1rem; width: 50%; }
.skeleton-text-short { height: 0.875rem; width: 30%; }

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
  margin: 0 auto;
}

/* Responsive */
@media (max-width: 768px) {
  .job-dashboard {
    padding: var(--space-md);
  }

  .search-form {
    flex-direction: column;
  }

  .search-btn {
    width: 100%;
    justify-content: center;
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
