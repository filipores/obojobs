<template>
  <div class="company-insights-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>{{ $t('pages.companyInsights') }}</h1>
        <p class="page-subtitle">Statistiken und Antwortverhalten nach Firma</p>
      </section>

      <!-- Stats Summary -->
      <section class="filter-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="filter-row">
          <div class="filter-group">
            <label class="filter-label">Sortieren nach</label>
            <select v-model="sortBy" @change="loadCompanyStats" class="form-select">
              <option value="bewerbungen">Anzahl Bewerbungen</option>
              <option value="antwortrate">Antwortrate</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
          <div class="stats-summary">
            <span class="stat-item">
              <span class="stat-value">{{ companies.length }}</span>
              <span class="stat-label">Firmen</span>
            </span>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Loading State - Skeleton -->
      <div v-if="loading" class="loading-skeleton" :aria-label="$t('pages.companyInsights')">
        <div class="skeleton-table zen-card">
          <div class="skeleton-table-header">
            <div class="skeleton skeleton-th" style="width: 200px;"></div>
            <div class="skeleton skeleton-th" style="width: 80px;"></div>
            <div class="skeleton skeleton-th" style="width: 80px;"></div>
            <div class="skeleton skeleton-th" style="width: 80px;"></div>
            <div class="skeleton skeleton-th" style="width: 100px;"></div>
          </div>
          <div v-for="i in 5" :key="i" class="skeleton-table-row">
            <div class="skeleton skeleton-company-name"></div>
            <div class="skeleton skeleton-count"></div>
            <div class="skeleton skeleton-count"></div>
            <div class="skeleton skeleton-rate"></div>
            <div class="skeleton skeleton-time"></div>
          </div>
        </div>
      </div>

      <!-- Company Table -->
      <section v-else-if="companies.length > 0" class="table-section">
        <ScrollableTable class="zen-card table-container-outer">
          <table class="company-table">
            <thead>
              <tr>
                <th class="th-firma">Firma</th>
                <th class="th-center">Bewerbungen</th>
                <th class="th-center">Antworten</th>
                <th class="th-center">Antwortrate</th>
                <th class="th-center">Avg. Antwortzeit</th>
                <th class="th-action"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="company in companies"
                :key="company.firma"
                class="company-row"
              >
                <td class="td-firma">
                  <div class="firma-cell">
                    <span class="firma-name">{{ company.firma }}</span>
                    <button
                      @click="filterByCompany(company.firma)"
                      class="zen-btn zen-btn-xs mobile-action-btn"
                    >
                      Bewerbungen
                    </button>
                  </div>
                </td>
                <td class="td-center">
                  <span class="count-badge">{{ company.bewerbungen }}</span>
                </td>
                <td class="td-center">
                  <span class="count-badge count-badge-secondary">{{ company.antworten }}</span>
                </td>
                <td class="td-center">
                  <span
                    class="rate-badge"
                    :class="getRateClass(company.antwortrate)"
                  >
                    {{ company.antwortrate }}%
                  </span>
                </td>
                <td class="td-center">
                  <span class="time-value">
                    {{ company.durchschnittliche_antwortzeit !== null
                      ? `${company.durchschnittliche_antwortzeit} Tage`
                      : '-' }}
                  </span>
                </td>
                <td class="td-action">
                  <button
                    @click="filterByCompany(company.firma)"
                    class="zen-btn zen-btn-sm"
                  >
                    Bewerbungen
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </ScrollableTable>
      </section>

      <!-- Empty State -->
      <section v-else class="empty-state">
        <div class="empty-enso"></div>
        <h3>Keine Firmen-Insights verfügbar</h3>
        <p>Erstelle Bewerbungen, um Insights zu generieren.</p>
        <router-link to="/applications" class="zen-btn">
          Zu den Bewerbungen
        </router-link>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import ScrollableTable from '../components/ScrollableTable.vue'

const router = useRouter()
const companies = ref([])
const loading = ref(false)
const sortBy = ref('bewerbungen')

const loadCompanyStats = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/stats/companies', {
      params: { sort_by: sortBy.value }
    })
    companies.value = data.data?.companies || []
  } catch (err) {
    console.error('Fehler beim Laden der Company Stats:', err)
  } finally {
    loading.value = false
  }
}

const getRateClass = (rate) => {
  if (rate >= 50) return 'rate-high'
  if (rate >= 25) return 'rate-medium'
  return 'rate-low'
}

const filterByCompany = (firma) => {
  router.push({
    path: '/applications',
    query: { firma }
  })
}

onMounted(() => {
  loadCompanyStats()
})
</script>

<style scoped>
.company-insights-page {
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

.page-header h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
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
   FILTER SECTION
   ======================================== */
.filter-section {
  margin-bottom: var(--space-ma);
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.stats-summary {
  display: flex;
  gap: var(--space-lg);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 1.5rem;
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
}

/* ========================================
   LOADING SKELETON
   ======================================== */
.loading-skeleton {
  margin-top: var(--space-ma);
}

.skeleton-table {
  padding: 0;
  overflow: hidden;
}

.skeleton-table-header {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-washi);
  border-bottom: 1px solid var(--color-border-light);
}

.skeleton-th {
  height: 1rem;
}

.skeleton-table-row {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
  align-items: center;
}

.skeleton-table-row:last-child {
  border-bottom: none;
}

.skeleton-company-name {
  width: 180px;
  height: 1rem;
}

.skeleton-count {
  width: 40px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-rate {
  width: 56px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-time {
  width: 70px;
  height: 1rem;
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
   TABLE SECTION
   ======================================== */
.table-section {
  margin-top: var(--space-ma);
}

.table-container-outer {
  padding: 0;
}

.company-table {
  width: 100%;
  border-collapse: collapse;
}

.company-table th {
  padding: var(--space-md) var(--space-lg);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  text-align: left;
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-washi);
}

.th-center {
  text-align: center !important;
}

.th-action {
  width: 120px;
}

.company-table td {
  padding: var(--space-md) var(--space-lg);
  vertical-align: middle;
  border-bottom: 1px solid var(--color-border-light);
}

.company-row {
  transition: background var(--transition-base);
}

.company-row:hover {
  background: var(--color-washi);
}

.company-row:last-child td {
  border-bottom: none;
}

.td-firma {
  min-width: 200px;
}

.firma-cell {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.firma-name {
  font-weight: 500;
  color: var(--color-sumi);
}

.mobile-action-btn {
  display: none;
  align-self: flex-start;
}

.td-center {
  text-align: center;
}

.td-action {
  text-align: right;
}

/* ========================================
   BADGES
   ======================================== */
.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.count-badge-secondary {
  background: var(--color-washi-aged);
  color: var(--color-sumi-light);
}

.rate-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.rate-high {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.rate-medium {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.rate-low {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.time-value {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
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
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-summary {
    justify-content: flex-start;
  }

  .stat-item {
    align-items: flex-start;
  }

  .company-table th,
  .company-table td {
    padding: var(--space-sm) var(--space-md);
  }

  .td-firma {
    min-width: 150px;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .th-action {
    display: none;
  }

  .td-action {
    display: none;
  }

  .mobile-action-btn {
    display: inline-flex !important;
  }

  .td-firma {
    min-width: 180px;
  }
}
</style>
