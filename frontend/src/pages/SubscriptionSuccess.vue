<template>
  <div class="subscription-success-page">
    <div class="container">
      <div class="success-container">
        <!-- Loading State -->
        <div v-if="loading" class="state-card zen-card animate-fade-up">
          <div class="loading-enso"></div>
          <h2>Abo wird eingerichtet</h2>
          <p>Bitte warten Sie, wahrend wir Ihr Abonnement aktivieren.</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="state-card zen-card animate-fade-up">
          <div class="state-icon state-icon-error">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <h2>Aktivierung fehlgeschlagen</h2>
          <p class="error-message">{{ errorMessage }}</p>
          <div class="state-actions">
            <router-link to="/settings" class="zen-btn zen-btn-ai">
              Zu den Einstellungen
            </router-link>
            <router-link to="/dashboard" class="zen-btn">
              Zum Dashboard
            </router-link>
          </div>
        </div>

        <!-- Success State -->
        <div v-else-if="success" class="state-card zen-card animate-fade-up">
          <div class="state-icon state-icon-success">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h2>Abo erfolgreich aktiviert</h2>
          <p class="success-message">Ihr Abonnement wurde erfolgreich eingerichtet.</p>

          <!-- Subscription Details -->
          <div v-if="subscription" class="subscription-details">
            <h3>Abo-Details</h3>
            <div class="detail-row">
              <span class="detail-label">Plan</span>
              <span class="detail-value">{{ getPlanName(subscription.plan) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Status</span>
              <span class="detail-value">
                <span class="badge badge-success">Aktiv</span>
              </span>
            </div>
            <div v-if="subscription.current_period_end" class="detail-row">
              <span class="detail-label">Nachste Abrechnung</span>
              <span class="detail-value">{{ formatDate(subscription.current_period_end) }}</span>
            </div>
          </div>

          <div class="state-actions">
            <router-link to="/dashboard" class="zen-btn zen-btn-filled">
              Zum Dashboard
            </router-link>
            <router-link to="/new-application" class="zen-btn">
              Bewerbung erstellen
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { authStore } from '../stores/auth'
import { getFullLocale } from '../i18n'

const route = useRoute()

const loading = ref(true)
const success = ref(false)
const error = ref(false)
const errorMessage = ref('')
const subscription = ref(null)

const getPlanName = (plan) => {
  const names = {
    'free': 'Free',
    'basic': 'Basic',
    'pro': 'Pro'
  }
  return names[plan] || plan
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const verifySubscription = async () => {
  const sessionId = route.query.session_id

  if (!sessionId) {
    // No session_id means direct navigation - just refresh user data
    try {
      await authStore.fetchUser()
      const user = authStore.user
      if (user?.subscription && user.subscription.status === 'active') {
        success.value = true
        subscription.value = user.subscription
      } else {
        error.value = true
        errorMessage.value = 'Kein aktives Abonnement gefunden. Falls Sie gerade bezahlt haben, warten Sie bitte einen Moment und aktualisieren Sie die Seite.'
      }
    } catch (err) {
      console.error('Failed to verify subscription:', err)
      error.value = true
      errorMessage.value = 'Fehler beim Laden der Abonnement-Daten.'
    } finally {
      loading.value = false
    }
    return
  }

  // With session_id, refresh user data to get updated subscription
  try {
    await authStore.fetchUser()
    const user = authStore.user

    if (user?.subscription) {
      success.value = true
      subscription.value = user.subscription
    } else {
      // Subscription might not be created yet (webhook delay)
      // Show success anyway as payment was completed
      success.value = true
      subscription.value = null
    }
  } catch (err) {
    console.error('Subscription verification error:', err)
    error.value = true
    errorMessage.value = err.response?.data?.error || err.message || 'Ein unerwarteter Fehler ist aufgetreten'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  verifySubscription()
})
</script>

<style scoped>
.subscription-success-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma) 0;
}

.success-container {
  width: 100%;
  max-width: 500px;
}

/* ========================================
   STATE CARD
   ======================================== */
.state-card {
  text-align: center;
  padding: var(--space-ma);
}

.state-card h2 {
  font-size: 1.75rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.state-card > p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
}

/* ========================================
   LOADING STATE
   ======================================== */
.loading-enso {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--space-lg);
  border: 2px solid var(--color-sand);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   STATE ICONS
   ======================================== */
.state-icon {
  width: 100px;
  height: 100px;
  margin: 0 auto var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.state-icon-success {
  background: var(--color-koke);
  color: var(--color-washi);
}

.state-icon-error {
  background: #b45050;
  color: var(--color-washi);
}

.error-message {
  color: #b45050;
}

.success-message {
  color: var(--color-koke);
  font-weight: 500;
}

/* ========================================
   SUBSCRIPTION DETAILS
   ======================================== */
.subscription-details {
  background: var(--color-washi);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  text-align: left;
}

.subscription-details h3 {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-md);
  text-align: center;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) 0;
}

.detail-label {
  color: var(--color-text-secondary);
}

.detail-value {
  font-weight: 500;
  color: var(--color-sumi);
}

.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.badge-success {
  background: var(--color-koke);
  color: var(--color-washi);
}

/* ========================================
   STATE ACTIONS
   ======================================== */
.state-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 480px) {
  .state-card {
    padding: var(--space-lg);
  }

  .state-card h2 {
    font-size: 1.5rem;
  }

  .state-icon {
    width: 80px;
    height: 80px;
  }

  .state-icon svg {
    width: 36px;
    height: 36px;
  }
}
</style>
