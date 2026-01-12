<template>
  <div class="payment-success-page">
    <div class="container">
      <div class="success-container">
        <!-- Loading State -->
        <div v-if="loading" class="state-card zen-card animate-fade-up">
          <div class="loading-enso"></div>
          <h2>Zahlung wird verarbeitet</h2>
          <p>Bitte warten Sie, während wir Ihre Zahlung bestätigen.</p>
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
          <h2>Zahlung fehlgeschlagen</h2>
          <p class="error-message">{{ errorMessage }}</p>
          <div class="state-actions">
            <router-link to="/buy-credits" class="zen-btn zen-btn-ai">
              Erneut versuchen
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
          <h2>Zahlung erfolgreich</h2>
          <p class="success-message">{{ successMessage }}</p>

          <!-- Purchase Details -->
          <div class="purchase-details">
            <h3>Kaufdetails</h3>
            <div class="detail-row">
              <span class="detail-label">Paket</span>
              <span class="detail-value">{{ purchase.package_name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Credits</span>
              <span class="detail-value">{{ purchase.credits_purchased }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Preis</span>
              <span class="detail-value">{{ purchase.price_eur }}€</span>
            </div>
            <div class="detail-divider"></div>
            <div class="detail-row detail-row-highlight">
              <span class="detail-label">Neue Credits</span>
              <span class="detail-value">{{ newCredits }}</span>
            </div>
          </div>

          <div class="state-actions">
            <router-link to="/dashboard" class="zen-btn zen-btn-filled">
              Zum Dashboard
            </router-link>
            <router-link to="/buy-credits" class="zen-btn">
              Weitere Credits kaufen
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api/client'
import { authStore } from '../store/auth'

const _router = useRouter()
const route = useRoute()

const loading = ref(true)
const success = ref(false)
const error = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const purchase = ref(null)
const newCredits = ref(0)

const executePayment = async () => {
  const paymentId = route.query.paymentId || route.query.token
  const payerId = route.query.PayerID

  if (!paymentId || !payerId) {
    error.value = true
    errorMessage.value = 'Ungültige Zahlungsinformationen. Bitte versuchen Sie es erneut.'
    loading.value = false
    return
  }

  try {
    const { data } = await api.post('/payments/execute-payment', {
      payment_id: paymentId,
      payer_id: payerId
    })

    if (data.success) {
      success.value = true
      successMessage.value = data.message
      purchase.value = data.purchase
      newCredits.value = data.new_credits

      await authStore.fetchUser()
    } else {
      throw new Error(data.error || 'Zahlung konnte nicht abgeschlossen werden')
    }
  } catch (err) {
    console.error('Payment execution error:', err)
    error.value = true
    errorMessage.value = err.response?.data?.error || err.message || 'Ein unerwarteter Fehler ist aufgetreten'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  executePayment()
})
</script>

<style scoped>
.payment-success-page {
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
   PURCHASE DETAILS
   ======================================== */
.purchase-details {
  background: var(--color-washi);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  text-align: left;
}

.purchase-details h3 {
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

.detail-divider {
  height: 1px;
  background: var(--color-border-light);
  margin: var(--space-md) 0;
}

.detail-row-highlight {
  background: var(--color-ai);
  color: var(--color-text-inverse);
  margin: var(--space-md) calc(var(--space-lg) * -1) calc(var(--space-lg) * -1);
  padding: var(--space-md) var(--space-lg);
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

.detail-row-highlight .detail-label {
  color: rgba(255, 255, 255, 0.8);
}

.detail-row-highlight .detail-value {
  color: var(--color-text-inverse);
  font-family: var(--font-display);
  font-size: 1.25rem;
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
