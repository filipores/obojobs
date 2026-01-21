<template>
  <div class="gap-analysis">
    <!-- Loading State - Skeleton -->
    <div v-if="loading" class="gap-loading-skeleton" aria-label="Lade Lernempfehlungen">
      <div class="skeleton-header">
        <div class="skeleton-header-info">
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-subtitle"></div>
        </div>
        <div class="skeleton skeleton-badge"></div>
      </div>
      <div class="skeleton-filters">
        <div class="skeleton skeleton-filter"></div>
        <div class="skeleton skeleton-filter"></div>
        <div class="skeleton skeleton-filter"></div>
      </div>
      <div class="skeleton-cards">
        <div v-for="i in 2" :key="i" class="skeleton-card">
          <div class="skeleton-card-header">
            <div class="skeleton skeleton-skill-badge"></div>
            <div class="skeleton skeleton-priority"></div>
          </div>
          <div class="skeleton-card-content">
            <div class="skeleton skeleton-icon"></div>
            <div class="skeleton-card-text">
              <div class="skeleton skeleton-card-title"></div>
              <div class="skeleton skeleton-card-desc"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Gaps Message -->
    <div v-else-if="!hasGaps" class="gap-success">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
      <div>
        <strong>Keine Skill-Luecken gefunden!</strong>
        <p>Ihr Profil erfuellt alle Anforderungen fuer diese Stelle.</p>
      </div>
    </div>

    <!-- Gap Analysis Content -->
    <div v-else class="gap-content">
      <!-- Header -->
      <div class="gap-header">
        <div class="header-info">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            Lernempfehlungen
          </h3>
          <p class="header-subtitle">
            Verbessern Sie Ihre Qualifikationen fuer zukuenftige Bewerbungen
          </p>
        </div>
        <div class="gap-summary">
          <span class="gap-count">{{ totalGaps }} Skill-Luecken</span>
          <span class="recommendation-count">{{ recommendations.length }} Empfehlungen</span>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="filter-tabs">
        <button
          :class="['filter-tab', { active: activeFilter === 'all' }]"
          @click="activeFilter = 'all'"
        >
          Alle
        </button>
        <button
          :class="['filter-tab', { active: activeFilter === 'online_course' }]"
          @click="activeFilter = 'online_course'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
            <path d="M6 12v5c3 3 9 3 12 0v-5"/>
          </svg>
          Kurse
        </button>
        <button
          :class="['filter-tab', { active: activeFilter === 'certification' }]"
          @click="activeFilter = 'certification'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="7"/>
            <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>
          </svg>
          Zertifikate
        </button>
        <button
          :class="['filter-tab', { active: activeFilter === 'project_idea' }]"
          @click="activeFilter = 'project_idea'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          Projekte
        </button>
        <button
          :class="['filter-tab', { active: activeFilter === 'book' }]"
          @click="activeFilter = 'book'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          Buecher
        </button>
      </div>

      <!-- Recommendations List -->
      <div class="recommendations-list">
        <div
          v-for="(rec, index) in filteredRecommendations"
          :key="index"
          :class="['recommendation-card', `priority-${rec.priority}`]"
        >
          <div class="card-header">
            <div class="skill-badge">{{ rec.skill_name }}</div>
            <span :class="['priority-badge', `priority-${rec.priority}`]">
              {{ getPriorityLabel(rec.priority) }}
            </span>
          </div>

          <div class="card-content">
            <div class="category-icon">
              <svg v-if="rec.category === 'online_course'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                <path d="M6 12v5c3 3 9 3 12 0v-5"/>
              </svg>
              <svg v-else-if="rec.category === 'certification'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="7"/>
                <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>
              </svg>
              <svg v-else-if="rec.category === 'project_idea'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div class="card-details">
              <h4>{{ rec.title }}</h4>
              <p>{{ rec.description }}</p>
            </div>
          </div>

          <div v-if="rec.resource_url" class="card-actions">
            <a
              :href="rec.resource_url"
              target="_blank"
              rel="noopener noreferrer"
              class="resource-link"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              Ressource oeffnen
            </a>
          </div>
        </div>
      </div>

      <!-- Empty Filter State -->
      <div v-if="filteredRecommendations.length === 0 && activeFilter !== 'all'" class="empty-filter">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <p>Keine Empfehlungen in dieser Kategorie.</p>
        <button class="zen-btn zen-btn-sm" @click="activeFilter = 'all'">
          Alle anzeigen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  },
  missingSkills: {
    type: Array,
    default: () => []
  },
  partialMatches: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const activeFilter = ref('all')

const hasGaps = computed(() => {
  return props.missingSkills.length > 0 || props.partialMatches.length > 0
})

const totalGaps = computed(() => {
  return props.missingSkills.length + props.partialMatches.length
})

const filteredRecommendations = computed(() => {
  if (activeFilter.value === 'all') {
    return props.recommendations
  }
  return props.recommendations.filter(rec => rec.category === activeFilter.value)
})

const getPriorityLabel = (priority) => {
  const labels = {
    high: 'Wichtig',
    medium: 'Mittel',
    low: 'Optional'
  }
  return labels[priority] || priority
}
</script>

<style scoped>
.gap-analysis {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-lg);
}

/* Loading Skeleton */
.gap-loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.gap-loading-skeleton .skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.skeleton-header-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-title {
  width: 160px;
  height: 1.25rem;
}

.skeleton-subtitle {
  width: 240px;
  height: 1rem;
}

.skeleton-badge {
  width: 100px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-filters {
  display: flex;
  gap: var(--space-sm);
}

.skeleton-filter {
  width: 80px;
  height: 2rem;
  border-radius: var(--radius-md);
}

.skeleton-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton-card {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.skeleton-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.skeleton-skill-badge {
  width: 80px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-priority {
  width: 60px;
  height: 1.25rem;
  border-radius: var(--radius-sm);
}

.skeleton-card-content {
  display: flex;
  gap: var(--space-md);
}

.skeleton-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.skeleton-card-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-card-title {
  width: 70%;
  height: 1rem;
}

.skeleton-card-desc {
  width: 100%;
  height: 2.5rem;
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

/* Success State */
.gap-success {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-success-light);
  border-radius: var(--radius-md);
}

.gap-success svg {
  flex-shrink: 0;
  color: var(--color-success);
}

.gap-success strong {
  display: block;
  color: var(--color-success);
  margin-bottom: var(--space-xs);
}

.gap-success p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* Header */
.gap-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.header-info h3 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--space-xs) 0;
  color: var(--color-sumi);
}

.header-info h3 svg {
  color: var(--color-ai);
}

.header-subtitle {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.gap-summary {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-xs);
}

.gap-count {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-error);
  background: var(--color-error-light);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.recommendation-count {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Filter Tabs */
.filter-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
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
  background: var(--color-washi);
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

.filter-tab svg {
  opacity: 0.7;
}

.filter-tab.active svg {
  opacity: 1;
}

/* Recommendations List */
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.recommendation-card {
  background: var(--color-washi);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  border-left: 3px solid var(--color-border);
  padding: var(--space-md);
  transition: all 0.2s var(--ease-zen);
}

.recommendation-card:hover {
  box-shadow: var(--shadow-paper);
  transform: translateY(-1px);
}

.recommendation-card.priority-high {
  border-left-color: var(--color-error);
}

.recommendation-card.priority-medium {
  border-left-color: #c9a227;
}

.recommendation-card.priority-low {
  border-left-color: var(--color-ai);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.skill-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-ai);
  background: rgba(61, 90, 108, 0.1);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
}

.priority-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.priority-badge.priority-high {
  background: var(--color-error-light);
  color: var(--color-error);
}

.priority-badge.priority-medium {
  background: rgba(196, 163, 90, 0.15);
  color: #8a7a2a;
}

.priority-badge.priority-low {
  background: var(--color-ai-light);
  color: var(--color-ai);
}

.card-content {
  display: flex;
  gap: var(--space-md);
}

.category-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  color: var(--color-ai);
}

.card-details {
  flex: 1;
  min-width: 0;
}

.card-details h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
}

.card-details p {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.card-actions {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.resource-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-ai);
  text-decoration: none;
  transition: color 0.2s var(--ease-zen);
}

.resource-link:hover {
  color: var(--color-ai-light);
}

.resource-link svg {
  transition: transform 0.2s var(--ease-zen);
}

.resource-link:hover svg {
  transform: translate(2px, -2px);
}

/* Empty Filter State */
.empty-filter {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-tertiary);
}

.empty-filter svg {
  margin-bottom: var(--space-md);
  opacity: 0.5;
}

.empty-filter p {
  margin: 0 0 var(--space-md) 0;
  font-size: 0.875rem;
}

/* Responsive */
@media (max-width: 640px) {
  .gap-header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .gap-summary {
    align-items: flex-start;
    flex-direction: row;
    gap: var(--space-md);
  }

  .filter-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: var(--space-sm);
  }

  .filter-tab {
    white-space: nowrap;
  }

  .card-content {
    flex-direction: column;
  }

  .category-icon {
    width: 32px;
    height: 32px;
  }
}
</style>
