<template>
  <div class="admin-dashboard">
    <section class="admin-header">
      <div class="container">
        <div class="admin-header-content">
          <div>
            <span class="admin-label">Administration</span>
            <h1>{{ $t('admin.dashboard.title') }}</h1>
          </div>
          <router-link to="/admin/users" class="zen-btn zen-btn-ai">
            {{ $t('admin.dashboard.viewAllUsers') }}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </router-link>
        </div>
      </div>
    </section>

    <section class="admin-stats-section">
      <div class="container">
        <div v-if="stats" class="admin-stats-grid">
          <!-- Total Users -->
          <div class="stat-card stat-featured">
            <div class="stat-header">
              <span class="stat-label">{{ $t('admin.dashboard.totalUsers') }}</span>
              <div class="stat-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
            </div>
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-name">{{ $t('admin.dashboard.emailVerified') }}: {{ stats.email_verified_count }}</div>
          </div>

          <!-- Active Users 30d -->
          <div class="stat-card">
            <div class="stat-header">
              <span class="stat-label">{{ $t('admin.dashboard.activeUsers') }}</span>
            </div>
            <div class="stat-value">{{ stats.active_users_30d }}</div>
            <div class="stat-name">{{ $t('admin.dashboard.signupsLast7Days') }}: {{ stats.signups_last_7_days }}</div>
          </div>

          <!-- Total Applications -->
          <div class="stat-card">
            <div class="stat-header">
              <span class="stat-label">{{ $t('admin.dashboard.totalApplications') }}</span>
            </div>
            <div class="stat-value">{{ stats.total_applications }}</div>
            <div class="stat-name">{{ $t('admin.dashboard.applicationsThisMonth') }}: {{ stats.applications_this_month }}</div>
          </div>

          <!-- MRR -->
          <div class="stat-card">
            <div class="stat-header">
              <span class="stat-label">{{ $t('admin.dashboard.mrr') }}</span>
            </div>
            <div class="stat-value">{{ formatCurrency(stats.revenue_estimate) }}</div>
            <div class="stat-name">EUR / Monat</div>
          </div>
        </div>

        <!-- Loading -->
        <div v-else-if="!error" class="admin-stats-grid">
          <div v-for="i in 4" :key="i" class="stat-card">
            <div class="skeleton skeleton-card"></div>
          </div>
        </div>

        <!-- Error -->
        <div v-else class="admin-error">
          <p>Fehler beim Laden der Daten</p>
          <button @click="loadStats" class="zen-btn zen-btn-ai zen-btn-sm">Erneut versuchen</button>
        </div>
      </div>
    </section>

    <!-- Subscription Distribution -->
    <section v-if="stats" class="admin-subscriptions-section">
      <div class="container">
        <h2 class="section-title">{{ $t('admin.dashboard.subscriptions') }}</h2>
        <div class="subscription-cards">
          <div class="sub-card" v-for="plan in ['free', 'starter', 'pro']" :key="plan">
            <div class="sub-plan-name">{{ capitalize(plan) }}</div>
            <div class="sub-plan-count">{{ stats.subscriptions[plan] || 0 }}</div>
            <div class="sub-plan-bar">
              <div class="sub-plan-bar-fill" :style="{ width: getSubPercent(plan) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import { capitalize } from '@/utils/format.js'

const stats = ref(null)
const error = ref(false)

const formatCurrency = (val) => {
  if (val == null) return '0,00'
  return val.toFixed(2).replace('.', ',')
}

const getSubPercent = (plan) => {
  if (!stats.value) return 0
  const total = stats.value.total_users || 1
  return Math.round(((stats.value.subscriptions[plan] || 0) / total) * 100)
}

const loadStats = async () => {
  error.value = false
  try {
    const { data } = await api.get('/admin/stats')
    stats.value = data
  } catch (e) {
    console.error('Failed to load admin stats:', e)
    error.value = true
  }
}

onMounted(loadStats)
</script>

<style scoped>
.admin-dashboard {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
}

/* ========================================
   ADMIN HEADER
   ======================================== */
.admin-header {
  padding: var(--space-ma-xl) 0 var(--space-ma);
}

.admin-header-content {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-lg);
}

.admin-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.admin-header h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: 0;
}

/* ========================================
   ADMIN STATS GRID
   ======================================== */
.admin-stats-section {
  padding: 0 0 var(--space-ma);
}

.admin-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
}

.stat-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  box-shadow: var(--shadow-lifted);
  transform: translateY(-2px);
}

.stat-featured {
  background: var(--color-ai);
  border-color: transparent;
}

.stat-featured .stat-label,
.stat-featured .stat-value,
.stat-featured .stat-name {
  color: var(--color-text-inverse);
}

.stat-featured .stat-icon {
  color: rgba(255, 255, 255, 0.6);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-md);
}

.stat-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.stat-icon {
  color: var(--color-ai);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.stat-name {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

/* ========================================
   ADMIN ERROR
   ======================================== */
.admin-error {
  text-align: center;
  padding: var(--space-xl);
}

.admin-error p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-md);
}

/* ========================================
   SUBSCRIPTION DISTRIBUTION
   ======================================== */
.admin-subscriptions-section {
  padding: 0 0 var(--space-ma-xl);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.subscription-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.sub-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
}

.sub-plan-name {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.sub-plan-count {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-sumi);
  margin-bottom: var(--space-md);
}

.sub-plan-bar {
  height: 4px;
  border-radius: var(--radius-full, 9999px);
  background: var(--color-border-light);
  overflow: hidden;
}

.sub-plan-bar-fill {
  height: 100%;
  border-radius: var(--radius-full, 9999px);
  background: var(--color-ai);
  transition: width 0.6s ease;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 1024px) {
  .admin-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .admin-header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .admin-stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-value {
    font-size: 2.5rem;
  }

  .subscription-cards {
    grid-template-columns: 1fr;
  }
}
</style>
