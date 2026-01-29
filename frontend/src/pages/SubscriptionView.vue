<template>
  <div class="subscription-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Abonnement</h1>
        <p class="page-subtitle">Verwalten Sie Ihr Abo und Ihre Nutzung</p>
      </section>

      <!-- Loading State -->
      <div v-if="isLoading && !subscription" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Lade Abo-Details...</p>
      </div>

      <!-- Current Plan Section -->
      <section v-else class="subscription-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/>
              <path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/>
              <path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z"/>
            </svg>
          </div>
          <h2>Aktueller Plan</h2>
        </div>

        <div class="settings-card zen-card current-plan-card">
          <div class="plan-header">
            <div class="plan-badge" :class="subscription?.plan">
              {{ getPlanDisplayName(subscription?.plan) }}
            </div>
            <span v-if="subscription?.status === 'active'" class="status-badge active">Aktiv</span>
            <span v-else-if="subscription?.status === 'canceled'" class="status-badge canceled">Gekuendigt</span>
            <span v-else-if="subscription?.status === 'past_due'" class="status-badge past-due">Zahlung ausstehend</span>
            <span v-else-if="subscription?.status === 'trialing'" class="status-badge trialing">Testphase</span>
          </div>

          <div class="plan-details">
            <div class="detail-row">
              <span class="detail-label">Monatlicher Preis</span>
              <span class="detail-value">{{ subscription?.plan_details?.price_formatted || '0 EUR/Monat' }}</span>
            </div>
            <div class="detail-divider"></div>
            <div class="detail-row">
              <span class="detail-label">Naechste Abrechnung</span>
              <span class="detail-value">{{ formatDate(subscription?.next_billing_date) || 'Keine' }}</span>
            </div>
          </div>

          <div class="plan-features">
            <h4>Enthaltene Features</h4>
            <ul class="features-list">
              <li v-for="feature in getCurrentPlanFeatures()" :key="feature">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ feature }}
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Usage Section -->
      <section v-if="subscription" class="subscription-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <h2>Nutzung diesen Monat</h2>
        </div>

        <div class="settings-card zen-card usage-card">
          <div class="usage-display">
            <div class="usage-number">
              <span class="usage-current">{{ subscription.usage?.used || 0 }}</span>
              <span class="usage-separator">/</span>
              <span class="usage-limit">{{ subscription.usage?.unlimited ? 'Unbegrenzt' : subscription.usage?.limit }}</span>
            </div>
            <span class="usage-label">Bewerbungen erstellt</span>
          </div>

          <!-- Progress Bar (only for limited plans) -->
          <div v-if="!subscription.usage?.unlimited" class="usage-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: usagePercentage + '%' }"></div>
            </div>
            <div class="progress-info">
              <span>{{ subscription.usage?.remaining || 0 }} verbleibend</span>
              <span>{{ usagePercentage }}% genutzt</span>
            </div>
          </div>

          <!-- Unlimited Badge -->
          <div v-else class="unlimited-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18.178 8c5.096 0 5.096 8 0 8-5.095 0-7.133-8-12.739-8-4.585 0-4.585 8 0 8 5.606 0 7.644-8 12.74-8z"/>
            </svg>
            <span>Unbegrenzte Bewerbungen</span>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Manage Subscription Section -->
      <section v-if="subscription" class="subscription-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
          <div>
            <h2>Abo verwalten</h2>
            <p class="section-description">Zahlungsmethode, Plan aendern oder kuendigen</p>
          </div>
        </div>

        <div class="settings-card zen-card manage-card">
          <!-- Portal Access -->
          <div v-if="subscription.has_stripe_customer" class="portal-section">
            <p class="portal-info">
              Ueber das Stripe Kundenportal koennen Sie Ihre Zahlungsmethode aendern,
              Ihren Plan upgraden oder downgraden und Rechnungen einsehen.
            </p>
            <button
              @click="handleOpenPortal"
              class="zen-btn zen-btn-filled"
              :disabled="isPortalLoading"
            >
              {{ isPortalLoading ? 'Wird geoeffnet...' : 'Abo verwalten' }}
            </button>
          </div>

          <!-- Upgrade Prompt (for free users) -->
          <div v-else class="upgrade-section">
            <p class="upgrade-info">
              Sie haben aktuell den kostenlosen Plan. Upgraden Sie fuer mehr Bewerbungen pro Monat!
            </p>
            <div class="upgrade-buttons">
              <button
                @click="handleUpgrade('basic')"
                class="zen-btn zen-btn-filled"
                :class="{ 'is-loading-other': isUpgrading && upgradingPlan !== 'basic' }"
                :disabled="isUpgrading"
              >
                <span v-if="upgradingPlan === 'basic'" class="btn-spinner"></span>
                {{ upgradingPlan === 'basic' ? 'Wird geladen...' : 'Basic - 9,99 EUR/Monat' }}
              </button>
              <button
                @click="handleUpgrade('pro')"
                class="zen-btn zen-btn-ai"
                :class="{ 'is-loading-other': isUpgrading && upgradingPlan !== 'pro' }"
                :disabled="isUpgrading"
              >
                <span v-if="upgradingPlan === 'pro'" class="btn-spinner"></span>
                {{ upgradingPlan === 'pro' ? 'Wird geladen...' : 'Pro - 19,99 EUR/Monat' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Plan Comparison Section - Always visible -->
      <section v-if="subscription" class="subscription-section animate-fade-up" style="animation-delay: 250ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </div>
          <div>
            <h2>Alle Plaene im Vergleich</h2>
            <p class="section-description">Waehlen Sie den Plan, der zu Ihren Beduerfnissen passt</p>
          </div>
        </div>

        <!-- Plan Comparison Table (Desktop) -->
        <div class="plan-comparison-table zen-card">
          <table class="comparison-table" role="grid" aria-label="Plan-Vergleichstabelle">
            <thead>
              <tr>
                <th class="feature-column">Features</th>
                <th
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  class="plan-column"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan, 'recommended-plan': plan.plan_id === 'pro' }"
                >
                  <div class="plan-header-cell">
                    <span v-if="plan.plan_id === subscription.plan" class="table-badge current">Aktuell</span>
                    <span v-else-if="plan.plan_id === 'pro'" class="table-badge recommended">Empfohlen</span>
                    <span class="plan-name">{{ plan.name }}</span>
                    <span class="plan-price-cell">
                      {{ plan.price === 0 ? 'Kostenlos' : plan.price.toFixed(2).replace('.', ',') + ' EUR/Monat' }}
                    </span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="feature-name">Bewerbungen pro Monat</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span class="feature-value" :class="{ 'highlight': plan.plan_id === 'pro' }">
                    {{ getApplicationLimit(plan.plan_id) }}
                  </span>
                </td>
              </tr>
              <tr>
                <td class="feature-name">AI-Bewerbungsgenerator</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">Template-Verwaltung</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">ATS-Analyse</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">Email-Vorschlaege</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span v-if="plan.plan_id === 'free'" class="feature-limited">Begrenzt</span>
                  <svg v-else class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">Gehalts-Coach</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span v-if="plan.plan_id === 'free'" class="feature-unavailable">—</span>
                  <svg v-else class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">Prioritaets-Support</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span v-if="plan.plan_id !== 'pro'" class="feature-unavailable">—</span>
                  <svg v-else class="check-icon highlight" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td></td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <button
                    v-if="plan.plan_id !== subscription.plan && plan.plan_id !== 'free'"
                    @click="handleUpgrade(plan.plan_id)"
                    class="zen-btn upgrade-btn"
                    :class="[
                      plan.plan_id === 'pro' ? 'zen-btn-ai' : 'zen-btn-filled',
                      { 'is-loading-other': isUpgrading && upgradingPlan !== plan.plan_id }
                    ]"
                    :disabled="isUpgrading"
                  >
                    <span v-if="upgradingPlan === plan.plan_id" class="btn-spinner"></span>
                    {{ upgradingPlan === plan.plan_id ? 'Wird geladen...' : getUpgradeButtonText(plan.plan_id) }}
                  </button>
                  <span v-else-if="plan.plan_id === subscription.plan" class="current-plan-indicator">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Ihr aktueller Plan
                  </span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Plan Cards (Mobile) -->
        <div class="plans-grid mobile-only">
          <div
            v-for="plan in getAvailablePlans"
            :key="plan.plan_id"
            class="plan-card zen-card"
            :class="{ 'current': plan.plan_id === subscription.plan, 'recommended': plan.plan_id === 'pro' }"
          >
            <div v-if="plan.plan_id === 'pro' && plan.plan_id !== subscription.plan" class="recommended-badge">Empfohlen</div>
            <div v-if="plan.plan_id === subscription.plan" class="current-badge">Aktueller Plan</div>

            <h3>{{ plan.name }}</h3>
            <div class="plan-price">
              <span class="price-amount">{{ plan.price === 0 ? 'Kostenlos' : plan.price.toFixed(2).replace('.', ',') + ' EUR' }}</span>
              <span v-if="plan.price > 0" class="price-period">/ Monat</span>
            </div>

            <div class="plan-limit-badge">
              {{ getApplicationLimit(plan.plan_id) }} Bewerbungen/Monat
            </div>

            <ul class="plan-features-list">
              <li v-for="feature in plan.features" :key="feature">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ feature }}
              </li>
            </ul>

            <button
              v-if="plan.plan_id !== subscription.plan && plan.plan_id !== 'free'"
              @click="handleUpgrade(plan.plan_id)"
              class="zen-btn upgrade-btn-large"
              :class="[
                plan.plan_id === 'pro' ? 'zen-btn-ai' : 'zen-btn-filled',
                { 'is-loading-other': isUpgrading && upgradingPlan !== plan.plan_id }
              ]"
              :disabled="isUpgrading"
            >
              <span v-if="upgradingPlan === plan.plan_id" class="btn-spinner"></span>
              {{ upgradingPlan === plan.plan_id ? 'Wird geladen...' : getUpgradeButtonText(plan.plan_id) }}
            </button>
            <div v-else-if="plan.plan_id === subscription.plan" class="current-plan-text">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Ihr aktueller Plan
            </div>
          </div>
        </div>
      </section>

      <!-- Error Message -->
      <div v-if="errorMessage" class="error-message animate-fade-up">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSubscription } from '../composables/useSubscription'
import { getFullLocale } from '../i18n'

const { fetchPlans, fetchCurrentSubscription, openBillingPortal, startCheckout, isLoading } = useSubscription()

const subscription = ref(null)
const availablePlans = ref([])
const isPortalLoading = ref(false)
const isUpgrading = ref(false)
const upgradingPlan = ref(null) // Track which plan is being upgraded to
const errorMessage = ref('')

const usagePercentage = computed(() => {
  if (!subscription.value?.usage || subscription.value.usage.unlimited) return 0
  const { used, limit } = subscription.value.usage
  if (limit === 0) return 0
  return Math.min(Math.round((used / limit) * 100), 100)
})

const getCurrentPlanFeatures = computed(() => {
  // First try to get features from subscription plan_details
  if (subscription.value?.plan_details?.features?.length) {
    return subscription.value.plan_details.features
  }

  // Fallback: get features from the current plan based on plan name
  const currentPlan = subscription.value?.plan || 'free'
  const planFromAvailable = getAvailablePlans.value.find(plan => plan.plan_id === currentPlan)
  if (planFromAvailable?.features?.length) {
    return planFromAvailable.features
  }

  // Last resort: hardcoded features for the free plan
  if (currentPlan === 'free') {
    return [
      '3 Bewerbungen pro Monat',
      'Basis-Templates',
      'PDF Export'
    ]
  } else if (currentPlan === 'basic') {
    return [
      '20 Bewerbungen pro Monat',
      'Alle Templates',
      'PDF Export',
      'ATS-Optimierung',
      'E-Mail Support'
    ]
  } else if (currentPlan === 'pro') {
    return [
      'Unbegrenzte Bewerbungen',
      'Alle Templates',
      'PDF Export',
      'ATS-Optimierung',
      'Prioritäts-Support',
      'Erweiterte Analyse'
    ]
  }

  // Absolute fallback
  return ['Keine Features verfügbar']
})

const getAvailablePlans = computed(() => {
  // If API data is available, use it
  if (availablePlans.value?.length > 0) {
    return availablePlans.value
  }

  // Fallback: hardcoded plan data that matches backend structure
  return [
    {
      plan_id: 'free',
      name: 'Free',
      price: 0,
      price_formatted: '€0/Monat',
      features: [
        '3 Bewerbungen pro Monat',
        'Basis-Templates',
        'PDF Export'
      ]
    },
    {
      plan_id: 'basic',
      name: 'Basic',
      price: 9.99,
      price_formatted: '€9,99/Monat',
      features: [
        '20 Bewerbungen pro Monat',
        'Alle Templates',
        'PDF Export',
        'ATS-Optimierung',
        'E-Mail Support'
      ]
    },
    {
      plan_id: 'pro',
      name: 'Pro',
      price: 19.99,
      price_formatted: '€19,99/Monat',
      features: [
        'Unbegrenzte Bewerbungen',
        'Alle Templates',
        'PDF Export',
        'ATS-Optimierung',
        'Prioritäts-Support',
        'Erweiterte Analyse'
      ]
    }
  ]
})

const getPlanDisplayName = (plan) => {
  const names = {
    free: 'Free',
    basic: 'Basic',
    pro: 'Pro'
  }
  return names[plan] || 'Free'
}

const formatDate = (dateString) => {
  if (!dateString) return null
  return new Date(dateString).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const getUpgradeButtonText = (planId) => {
  if (!subscription.value) return 'Upgraden'
  const currentPlanOrder = { free: 0, basic: 1, pro: 2 }
  const targetOrder = currentPlanOrder[planId] || 0
  const currentOrder = currentPlanOrder[subscription.value.plan] || 0

  if (targetOrder > currentOrder) return 'Upgraden'
  if (targetOrder < currentOrder) return 'Downgraden'
  return 'Aktueller Plan'
}

const getApplicationLimit = (planId) => {
  const limits = {
    free: '3',
    basic: '20',
    pro: 'Unbegrenzt'
  }
  return limits[planId] || '3'
}

const handleOpenPortal = async () => {
  isPortalLoading.value = true
  errorMessage.value = ''

  try {
    await openBillingPortal()
  } catch (err) {
    errorMessage.value = err.message || 'Fehler beim Oeffnen des Portals'
  } finally {
    isPortalLoading.value = false
  }
}

const handleUpgrade = async (planId) => {
  isUpgrading.value = true
  upgradingPlan.value = planId
  errorMessage.value = ''

  try {
    await startCheckout(planId)
  } catch (err) {
    errorMessage.value = err.message || 'Fehler beim Starten des Checkouts'
  } finally {
    isUpgrading.value = false
    upgradingPlan.value = null
  }
}

const loadData = async () => {
  try {
    const [subscriptionData, plansData] = await Promise.all([
      fetchCurrentSubscription(),
      fetchPlans()
    ])
    subscription.value = subscriptionData
    availablePlans.value = plansData
  } catch (err) {
    errorMessage.value = err.message || 'Fehler beim Laden der Daten'
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.subscription-page {
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
   LOADING STATE
   ======================================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma-xl);
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-md);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   SUBSCRIPTION SECTION
   ======================================== */
.subscription-section {
  margin-bottom: var(--space-ma);
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.section-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
}

.section-description {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
  margin: var(--space-xs) 0 0 0;
}

.settings-card {
  padding: var(--space-xl);
}

/* ========================================
   CURRENT PLAN CARD
   ======================================== */
.plan-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.plan-badge {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.plan-badge.pro {
  background: linear-gradient(135deg, var(--color-ai) 0%, var(--color-ai-light) 100%);
  color: white;
}

.plan-badge.basic {
  background: var(--color-koke);
  color: white;
}

.status-badge {
  font-size: 0.75rem;
  font-weight: 500;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

.status-badge.active {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.status-badge.canceled {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.status-badge.past-due {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.status-badge.trialing {
  background: rgba(61, 90, 108, 0.15);
  color: var(--color-ai);
}

.plan-details {
  margin-bottom: var(--space-lg);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) 0;
}

.detail-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.detail-value {
  font-weight: 500;
  color: var(--color-sumi);
}

.detail-divider {
  height: 1px;
  background: var(--color-border-light);
}

.plan-features h4 {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  margin: 0 0 var(--space-md) 0;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-sm);
}

.features-list li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.features-list svg {
  color: var(--color-koke);
  flex-shrink: 0;
}

/* ========================================
   USAGE CARD
   ======================================== */
.usage-display {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.usage-number {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--space-xs);
}

.usage-current {
  font-family: var(--font-display);
  font-size: 3.5rem;
  font-weight: 400;
  color: var(--color-ai);
  line-height: 1;
}

.usage-separator {
  font-size: 2rem;
  color: var(--color-text-ghost);
}

.usage-limit {
  font-family: var(--font-display);
  font-size: 2rem;
  color: var(--color-text-tertiary);
}

.usage-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin-top: var(--space-sm);
  display: block;
}

.usage-progress {
  max-width: 400px;
  margin: 0 auto;
}

.progress-bar {
  height: 8px;
  background: var(--color-border-light);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--space-sm);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-ai) 0%, var(--color-ai-light) 100%);
  border-radius: 4px;
  transition: width 0.5s var(--easing-zen);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.unlimited-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: linear-gradient(135deg, var(--color-ai-subtle) 0%, rgba(61, 90, 108, 0.1) 100%);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  font-weight: 500;
}

/* ========================================
   MANAGE CARD
   ======================================== */
.portal-section,
.upgrade-section {
  text-align: center;
}

.portal-info,
.upgrade-info {
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-lg) 0;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.upgrade-buttons {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  flex-wrap: wrap;
}

/* Button Spinner */
.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: var(--space-sm);
  vertical-align: middle;
}

.zen-btn-ai .btn-spinner {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

.zen-btn-filled .btn-spinner {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

/* Disabled visual state for buttons when another upgrade is in progress */
.zen-btn.is-loading-other {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* ========================================
   PLANS GRID
   ======================================== */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}

.plan-card {
  padding: var(--space-xl);
  position: relative;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.plan-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lifted);
}

.plan-card.current {
  border: 2px solid var(--color-ai);
}

.plan-card.recommended {
  border: 2px solid var(--color-ai);
}

.recommended-badge,
.current-badge {
  position: absolute;
  top: calc(-1 * var(--space-sm));
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  font-weight: 500;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
}

.recommended-badge {
  background: var(--color-ai);
  color: white;
}

.current-badge {
  background: var(--color-koke);
  color: white;
}

.plan-card h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0 0 var(--space-md) 0;
  text-align: center;
}

.plan-price {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.price-amount {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 400;
  color: var(--color-sumi);
}

.price-period {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
}

.plan-features-list {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-lg) 0;
}

.plan-features-list li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  padding: var(--space-xs) 0;
}

.plan-features-list svg {
  color: var(--color-koke);
  flex-shrink: 0;
}

.plan-card .zen-btn {
  width: 100%;
}

/* ========================================
   ERROR MESSAGE
   ======================================== */
.error-message {
  padding: var(--space-md) var(--space-lg);
  background: rgba(184, 122, 94, 0.1);
  border: 1px solid var(--color-terra);
  border-radius: var(--radius-md);
  color: var(--color-terra);
  text-align: center;
  margin-top: var(--space-lg);
}

/* ========================================
   PLAN COMPARISON TABLE
   ======================================== */
.plan-comparison-table {
  padding: 0;
  overflow: hidden;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.comparison-table th,
.comparison-table td {
  padding: var(--space-md) var(--space-lg);
  text-align: center;
  border-bottom: 1px solid var(--color-border-light);
  vertical-align: middle;
}

.comparison-table thead th {
  background: var(--color-washi-warm);
  padding: var(--space-lg);
}

.comparison-table .feature-column {
  width: 200px;
  text-align: left;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.comparison-table .plan-column {
  min-width: 180px;
}

.comparison-table .current-plan {
  background: rgba(61, 90, 108, 0.05);
}

.comparison-table thead .current-plan {
  background: rgba(61, 90, 108, 0.1);
}

.comparison-table .recommended-plan {
  background: rgba(61, 90, 108, 0.03);
}

.plan-header-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
}

.table-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px var(--space-sm);
  border-radius: var(--radius-sm);
}

.table-badge.current {
  background: var(--color-ai);
  color: white;
}

.table-badge.recommended {
  background: linear-gradient(135deg, var(--color-ai) 0%, var(--color-ai-light) 100%);
  color: white;
}

.plan-name {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.plan-price-cell {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.feature-name {
  text-align: left !important;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.feature-value {
  font-weight: 600;
  color: var(--color-sumi);
}

.feature-value.highlight {
  color: var(--color-ai);
}

.check-icon {
  color: var(--color-koke);
  margin: 0 auto;
  display: block;
}

.check-icon.highlight {
  color: var(--color-ai);
}

.feature-limited {
  font-size: 0.8125rem;
  color: var(--color-terra);
  font-weight: 500;
}

.feature-unavailable {
  font-size: 1.25rem;
  color: var(--color-text-ghost);
}

.comparison-table tfoot td {
  padding: var(--space-lg);
  border-bottom: none;
  background: var(--color-washi-warm);
}

.upgrade-btn {
  width: 100%;
  max-width: 200px;
  font-size: 0.9375rem;
  padding: var(--space-sm) var(--space-md);
}

.current-plan-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
  color: var(--color-koke);
  font-weight: 500;
}

.current-plan-indicator svg {
  color: var(--color-koke);
}

/* Mobile Plan Cards */
.mobile-only {
  display: none;
}

.plan-limit-badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
}

.upgrade-btn-large {
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  font-weight: 500;
}

.current-plan-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  color: var(--color-koke);
  font-weight: 500;
  background: rgba(122, 139, 110, 0.1);
  border-radius: var(--radius-md);
}

.current-plan-text svg {
  color: var(--color-koke);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .plan-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .features-list {
    grid-template-columns: 1fr;
  }

  .upgrade-buttons {
    flex-direction: column;
  }

  .upgrade-buttons .zen-btn {
    width: 100%;
  }

  .plans-grid {
    grid-template-columns: 1fr;
  }

  /* Hide table on mobile, show cards */
  .plan-comparison-table {
    display: none;
  }

  .mobile-only {
    display: grid;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .section-header {
    flex-direction: column;
  }

  .usage-current {
    font-size: 2.5rem;
  }

  .usage-limit {
    font-size: 1.5rem;
  }
}
</style>
