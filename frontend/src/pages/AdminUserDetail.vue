<template>
  <div class="admin-user-detail">
    <section class="admin-header">
      <div class="container">
        <router-link to="/admin/users" class="back-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          {{ $t('admin.userDetail.backToUsers') }}
        </router-link>
        <div class="admin-header-content">
          <div>
            <span class="admin-label">{{ $t('admin.userDetail.userDetail') }}</span>
            <h1 v-if="userData">{{ userData.name || userData.email }}</h1>
            <h1 v-else>{{ $t('admin.userDetail.loading') }}</h1>
          </div>
        </div>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading" class="container">
      <div class="user-info-card">
        <div class="skeleton skeleton-card"></div>
      </div>
    </div>

    <!-- User Data -->
    <template v-else-if="userData">
      <!-- User Info Card -->
      <section class="user-info-section">
        <div class="container">
          <div class="user-info-card">
            <div class="info-row">
              <span class="info-label">{{ $t('admin.userDetail.email') }}</span>
              <span class="info-value">{{ userData.email }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('admin.userDetail.name') }}</span>
              <span class="info-value">{{ userData.name || '–' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('admin.userDetail.plan') }}</span>
              <span class="info-value">
                <span class="plan-badge" :class="'plan-' + (userData.plan || 'free')">
                  {{ capitalize(userData.plan || 'free') }}
                </span>
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('admin.userDetail.registered') }}</span>
              <span class="info-value">{{ formatDateDE(userData.created_at) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('admin.userDetail.lastLogin') }}</span>
              <span class="info-value">{{ formatDateDE(userData.last_login) }}</span>
            </div>
            <div class="info-row" v-if="userData.stripe_customer_id">
              <span class="info-label">Stripe ID</span>
              <span class="info-value info-mono">{{ userData.stripe_customer_id }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Toggle Actions -->
      <section class="user-actions-section">
        <div class="container">
          <h2 class="section-title">{{ $t('admin.userDetail.actions') }}</h2>
          <div class="action-toggles">
            <div class="toggle-row">
              <div class="toggle-info">
                <span class="toggle-label">{{ $t('admin.userDetail.accountActive') }}</span>
                <span class="toggle-desc">{{ $t('admin.userDetail.accountActiveDesc') }}</span>
              </div>
              <button
                @click="toggleField('is_active')"
                :disabled="updating"
                class="toggle-btn"
                :class="{ 'toggle-on': userData.is_active, 'toggle-off': !userData.is_active }"
              >
                {{ userData.is_active ? $t('admin.userDetail.active') : $t('admin.userDetail.inactive') }}
              </button>
            </div>
            <div class="toggle-row">
              <div class="toggle-info">
                <span class="toggle-label">{{ $t('admin.userDetail.adminRole') }}</span>
                <span class="toggle-desc">{{ $t('admin.userDetail.adminRoleDesc') }}</span>
              </div>
              <button
                @click="toggleField('is_admin')"
                :disabled="updating"
                class="toggle-btn"
                :class="{ 'toggle-on': userData.is_admin, 'toggle-off': !userData.is_admin }"
              >
                {{ userData.is_admin ? $t('admin.userDetail.yes') : $t('admin.userDetail.no') }}
              </button>
            </div>
            <div class="toggle-row">
              <div class="toggle-info">
                <span class="toggle-label">{{ $t('admin.userDetail.emailVerified') }}</span>
                <span class="toggle-desc">{{ $t('admin.userDetail.emailVerifiedDesc') }}</span>
              </div>
              <button
                @click="toggleField('email_verified')"
                :disabled="updating"
                class="toggle-btn"
                :class="{ 'toggle-on': userData.email_verified, 'toggle-off': !userData.email_verified }"
              >
                {{ userData.email_verified ? $t('admin.userDetail.yes') : $t('admin.userDetail.no') }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Stats -->
      <section class="user-stats-section">
        <div class="container">
          <h2 class="section-title">{{ $t('admin.userDetail.statistics') }}</h2>
          <div class="user-stats-grid">
            <div class="mini-stat-card">
              <div class="mini-stat-value">{{ userData.document_count ?? 0 }}</div>
              <div class="mini-stat-label">{{ $t('admin.userDetail.documents') }}</div>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-value">{{ userData.template_count ?? 0 }}</div>
              <div class="mini-stat-label">{{ $t('admin.userDetail.templates') }}</div>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-value">{{ userData.application_count ?? 0 }}</div>
              <div class="mini-stat-label">{{ $t('admin.userDetail.applications') }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Recent Applications -->
      <section v-if="userData.recent_applications?.length" class="user-applications-section">
        <div class="container">
          <h2 class="section-title">{{ $t('admin.userDetail.recentApplications') }}</h2>
          <div class="applications-list">
            <div v-for="app in userData.recent_applications" :key="app.id" class="application-row">
              <div class="app-info">
                <span class="app-company">{{ app.firma || '–' }}</span>
                <span class="app-position">{{ app.position || '–' }}</span>
              </div>
              <div class="app-meta">
                <span class="app-status" :class="'status-' + (app.status || 'erstellt')">{{ app.status || 'erstellt' }}</span>
                <span class="app-date">{{ formatDateDE(app.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- Error -->
    <div v-else class="container">
      <div class="admin-error">
        <p>{{ $t('admin.userDetail.loadError') }}</p>
        <button @click="loadUser" class="zen-btn zen-btn-ai zen-btn-sm">{{ $t('admin.userDetail.retry') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import api from '@/api/client'
import { capitalize, formatDateDE } from '@/utils/format.js'

const { t } = useI18n()
const route = useRoute()
const userData = ref(null)
const loading = ref(true)
const updating = ref(false)

const loadUser = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/admin/users/${route.params.id}`)
    userData.value = data.user
  } catch (e) {
    console.error('Failed to load user:', e)
  } finally {
    loading.value = false
  }
}

const toggleField = async (field) => {
  if (!userData.value || updating.value) return
  updating.value = true
  try {
    const newValue = !userData.value[field]
    await api.patch(`/admin/users/${route.params.id}`, { [field]: newValue })
    userData.value[field] = newValue
    window.$toast?.('success', t('admin.userDetail.updateSuccess'))
  } catch (e) {
    console.error('Failed to update user:', e)
    const msg = e.response?.data?.error || t('admin.userDetail.updateError')
    window.$toast?.('error', msg)
  } finally {
    updating.value = false
  }
}

onMounted(loadUser)
</script>

<style scoped>
.admin-user-detail {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
}

/* ========================================
   ADMIN HEADER
   ======================================== */
.admin-header {
  padding: var(--space-ma-xl) 0 var(--space-ma);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  margin-bottom: var(--space-md);
  transition: color var(--transition-base);
}

.back-link:hover {
  color: var(--color-ai);
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
   USER INFO CARD
   ======================================== */
.user-info-section {
  padding: 0 0 var(--space-ma);
}

.user-info-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.info-value {
  font-size: 0.9375rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.info-mono {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

/* Plan Badge */
.plan-badge {
  display: inline-block;
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full, 9999px);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.plan-free {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}

.plan-basic {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.plan-pro {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

/* ========================================
   TOGGLE ACTIONS
   ======================================== */
.user-actions-section {
  padding: 0 0 var(--space-ma);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.action-toggles {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.toggle-row:last-child {
  border-bottom: none;
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.toggle-label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.toggle-desc {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.toggle-btn {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
  min-width: 80px;
  text-align: center;
}

.toggle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-on {
  background: var(--color-success-light);
  color: var(--color-success);
  border-color: var(--color-success);
}

.toggle-on:hover:not(:disabled) {
  background: var(--color-success);
  color: var(--color-text-inverse);
}

.toggle-off {
  background: var(--color-error-light);
  color: var(--color-error);
  border-color: var(--color-error);
}

.toggle-off:hover:not(:disabled) {
  background: var(--color-error);
  color: var(--color-text-inverse);
}

/* ========================================
   USER STATS
   ======================================== */
.user-stats-section {
  padding: 0 0 var(--space-ma);
}

.user-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.mini-stat-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  text-align: center;
}

.mini-stat-value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.mini-stat-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

/* ========================================
   RECENT APPLICATIONS
   ======================================== */
.user-applications-section {
  padding: 0 0 var(--space-ma-xl);
}

.applications-list {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.application-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.application-row:last-child {
  border-bottom: none;
}

.app-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.app-company {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.app-position {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.app-meta {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.app-status {
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full, 9999px);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-erstellt {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}

.status-versendet {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.status-absage {
  background: var(--color-error-light);
  color: var(--color-error);
}

.status-zusage {
  background: var(--color-success-light);
  color: var(--color-success);
}

.app-date {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

/* ========================================
   ERROR
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
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .user-stats-grid {
    grid-template-columns: 1fr;
  }

  .toggle-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .toggle-btn {
    width: 100%;
  }

  .application-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }
}
</style>
