<template>
  <div class="company-research">
    <!-- Loading State - Skeleton -->
    <div v-if="loading" class="research-loading-skeleton" aria-label="Recherchiere Firmen-Informationen">
      <div class="skeleton-header">
        <div class="skeleton-header-info">
          <div class="skeleton skeleton-company-name"></div>
          <div class="skeleton skeleton-industry"></div>
        </div>
        <div class="skeleton-actions">
          <div class="skeleton skeleton-btn"></div>
        </div>
      </div>
      <div class="skeleton-facts">
        <div class="skeleton skeleton-fact"></div>
        <div class="skeleton skeleton-fact"></div>
        <div class="skeleton skeleton-fact"></div>
      </div>
      <div class="skeleton-section">
        <div class="skeleton skeleton-subtitle"></div>
        <div class="skeleton-tags">
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-tag"></div>
        </div>
      </div>
      <div class="skeleton-section">
        <div class="skeleton skeleton-subtitle"></div>
        <div class="skeleton skeleton-text-block"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="research-error">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <strong>Recherche nicht moeglich</strong>
        <p>{{ error }}</p>
        <button class="zen-btn zen-btn-sm" @click="fetchResearch">
          Erneut versuchen
        </button>
      </div>
    </div>

    <!-- Research Content -->
    <div v-else-if="research" class="research-content">
      <!-- Header -->
      <div class="research-header">
        <div class="header-info">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            {{ research.company_name }}
          </h3>
          <p v-if="research.industry" class="industry-badge">{{ research.industry }}</p>
        </div>
        <div class="header-actions">
          <a
            v-if="research.website_url"
            :href="research.website_url"
            target="_blank"
            rel="noopener noreferrer"
            class="website-link"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
            Website
          </a>
          <button
            class="refresh-btn"
            @click="refreshResearch"
            :disabled="loading"
            title="Daten aktualisieren"
            aria-label="Firmen-Informationen aktualisieren - Neue Daten abrufen"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Quick Facts -->
      <div class="quick-facts">
        <div v-if="research.company_size" class="fact-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span>{{ research.company_size }}</span>
        </div>
        <div v-if="research.founded_year" class="fact-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span>Gegruendet {{ research.founded_year }}</span>
        </div>
        <div v-if="research.locations && research.locations.length > 0" class="fact-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
          <span>{{ research.locations.slice(0, 3).join(', ') }}{{ research.locations.length > 3 ? '...' : '' }}</span>
        </div>
      </div>

      <!-- Products/Services -->
      <div v-if="research.products_services && research.products_services.length > 0" class="info-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
            <line x1="7" y1="7" x2="7.01" y2="7"/>
          </svg>
          Produkte / Dienstleistungen
        </h4>
        <ul class="products-list">
          <li v-for="(product, index) in research.products_services" :key="index">
            {{ product }}
          </li>
        </ul>
      </div>

      <!-- About -->
      <div v-if="research.about_text" class="info-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Ueber das Unternehmen
        </h4>
        <p id="about-text-content" class="about-text" :class="{ expanded: aboutExpanded }">
          {{ aboutExpanded ? research.about_text : truncatedAbout }}
        </p>
        <button
          v-if="research.about_text.length > 300"
          class="expand-btn"
          @click="aboutExpanded = !aboutExpanded"
          :aria-expanded="aboutExpanded"
          aria-controls="about-text-content"
        >
          {{ aboutExpanded ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
        </button>
      </div>

      <!-- Mission/Values -->
      <div v-if="research.mission_values" class="info-section mission-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          Mission & Werte
        </h4>
        <blockquote>{{ research.mission_values }}</blockquote>
      </div>

      <!-- Interview Tips -->
      <div v-if="research.interview_tips && research.interview_tips.length > 0" class="info-section tips-section">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          Tipps fuers Interview
        </h4>
        <ul class="tips-list">
          <li v-for="(tip, index) in research.interview_tips" :key="index">
            {{ tip }}
          </li>
        </ul>
      </div>

      <!-- Cache Info -->
      <div v-if="research.cached_at" class="cache-info">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        Daten von {{ formatCacheDate(research.cached_at) }}
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="research-empty">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
      <p>Keine Firmen-Informationen vorhanden.</p>
      <button class="zen-btn zen-btn-sm zen-btn-ai" @click="fetchResearch">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        Jetzt recherchieren
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api/client'

const props = defineProps({
  companyName: {
    type: String,
    required: true
  },
  jobUrl: {
    type: String,
    default: ''
  },
  websiteUrl: {
    type: String,
    default: ''
  },
  autoLoad: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['loaded', 'error'])

const research = ref(null)
const loading = ref(false)
const error = ref(null)
const aboutExpanded = ref(false)

const truncatedAbout = computed(() => {
  if (!research.value?.about_text) return ''
  if (research.value.about_text.length <= 300) return research.value.about_text
  return research.value.about_text.substring(0, 300) + '...'
})

const formatCacheDate = (isoString) => {
  try {
    const date = new Date(isoString)
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return isoString
  }
}

const fetchResearch = async (forceRefresh = false) => {
  if (!props.companyName) {
    error.value = 'Kein Firmenname angegeben'
    return
  }

  loading.value = true
  error.value = null

  try {
    // Build query params
    const queryParts = []
    if (props.websiteUrl) queryParts.push(`website_url=${encodeURIComponent(props.websiteUrl)}`)
    if (props.jobUrl) queryParts.push(`job_url=${encodeURIComponent(props.jobUrl)}`)
    if (forceRefresh) queryParts.push('force_refresh=true')

    const queryString = queryParts.join('&')
    const url = `/companies/${encodeURIComponent(props.companyName)}/research${queryString ? '?' + queryString : ''}`

    const { data } = await api.get(url)

    if (data.success) {
      research.value = data.data
      emit('loaded', data.data)
    } else {
      error.value = data.error || 'Unbekannter Fehler'
      emit('error', error.value)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Fehler bei der Firmenrecherche'
    emit('error', error.value)
  } finally {
    loading.value = false
  }
}

const refreshResearch = () => {
  fetchResearch(true)
}

// Watch for company name changes
watch(() => props.companyName, (newName, oldName) => {
  if (newName && newName !== oldName && props.autoLoad) {
    research.value = null
    fetchResearch()
  }
})

onMounted(() => {
  if (props.autoLoad && props.companyName) {
    fetchResearch()
  }
})

// Expose method for parent components
defineExpose({
  fetchResearch,
  refreshResearch
})
</script>

<style scoped>
.company-research {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-lg);
}

/* Loading Skeleton */
.research-loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.skeleton-header {
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

.skeleton-company-name {
  width: 180px;
  height: 1.25rem;
}

.skeleton-industry {
  width: 100px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-actions {
  display: flex;
  gap: var(--space-sm);
}

.skeleton-btn {
  width: 80px;
  height: 2rem;
  border-radius: var(--radius-sm);
}

.skeleton-facts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
}

.skeleton-fact {
  width: 120px;
  height: 1rem;
}

.skeleton-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton-subtitle {
  width: 160px;
  height: 1rem;
}

.skeleton-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.skeleton-tag {
  width: 80px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-text-block {
  width: 100%;
  height: 80px;
  border-radius: var(--radius-md);
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

/* Error State */
.research-error {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
}

.research-error svg {
  flex-shrink: 0;
  color: var(--color-error);
}

.research-error strong {
  display: block;
  color: var(--color-error);
  margin-bottom: var(--space-xs);
}

.research-error p {
  margin: 0 0 var(--space-md) 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* Header */
.research-header {
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
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-sumi);
}

.header-info h3 svg {
  color: var(--color-ai);
}

.industry-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-ai);
  background: rgba(61, 90, 108, 0.1);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.website-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-ai);
  text-decoration: none;
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-ai);
  border-radius: var(--radius-sm);
  transition: all 0.2s var(--ease-zen);
}

.website-link:hover {
  background: var(--color-ai);
  color: white;
}

.refresh-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-washi);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--ease-zen);
}

.refresh-btn:hover:not(:disabled) {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Quick Facts */
.quick-facts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
}

.fact-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.fact-item svg {
  color: var(--color-ai);
  opacity: 0.7;
}

/* Info Sections */
.info-section {
  margin-bottom: var(--space-lg);
}

.info-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin: 0 0 var(--space-md) 0;
}

.info-section h4 svg {
  color: var(--color-ai);
}

.products-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  list-style: none;
  margin: 0;
  padding: 0;
}

.products-list li {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  background: var(--color-washi);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
}

.about-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
  max-height: 120px;
  overflow: hidden;
  transition: max-height 0.3s var(--ease-zen);
}

.about-text.expanded {
  max-height: none;
}

.expand-btn {
  display: inline-block;
  margin-top: var(--space-sm);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-ai);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.expand-btn:hover {
  text-decoration: underline;
}

.mission-section blockquote {
  margin: 0;
  padding: var(--space-md);
  background: var(--color-washi);
  border-left: 3px solid var(--color-ai);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  font-size: 0.875rem;
  font-style: italic;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Interview Tips */
.tips-section {
  background: rgba(61, 90, 108, 0.05);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.tips-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.tips-list li {
  position: relative;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  padding-left: var(--space-lg);
}

.tips-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 6px;
  height: 6px;
  background: var(--color-ai);
  border-radius: 50%;
}

/* Cache Info */
.cache-info {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.75rem;
  color: var(--color-text-ghost);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

/* Empty State */
.research-empty {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-tertiary);
}

.research-empty svg {
  margin-bottom: var(--space-md);
  opacity: 0.5;
}

.research-empty p {
  margin: 0 0 var(--space-md) 0;
  font-size: 0.875rem;
}

/* Responsive */
@media (max-width: 640px) {
  .research-header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .quick-facts {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .products-list {
    flex-direction: column;
  }

  .products-list li {
    width: fit-content;
  }
}
</style>
