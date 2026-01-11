<template>
  <div class="credits-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Credits</h1>
        <p class="page-subtitle">Kaufen Sie Credits für Ihre Bewerbungen</p>
      </section>

      <!-- Current Balance Card -->
      <section class="balance-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="balance-card zen-card zen-card-featured">
          <div class="balance-content">
            <span class="balance-label">Verfügbare Credits</span>
            <div class="balance-value">{{ authStore.user?.credits_remaining || 0 }}</div>
            <span class="balance-info">
              Insgesamt gekauft: {{ authStore.user?.total_credits_purchased || 0 }} Credits
            </span>
          </div>
          <div class="balance-decoration">
            <div class="balance-enso"></div>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Packages Section -->
      <section class="packages-section">
        <h2 class="section-title">Pakete wählen</h2>

        <div class="packages-grid">
          <div
            v-for="(pkg, index) in packages"
            :key="pkg.id"
            class="package-card zen-card stagger-item"
            :class="{ 'package-featured': pkg.id === 'medium' }"
          >
            <!-- Popular Badge -->
            <div v-if="pkg.id === 'medium'" class="package-badge">Beliebt</div>

            <!-- Package Content -->
            <div class="package-header">
              <h3>{{ pkg.name }}</h3>
            </div>

            <div class="package-credits">
              <span class="credits-value">{{ pkg.credits }}</span>
              <span class="credits-unit">Credits</span>
            </div>

            <div class="package-price">
              <span class="price-value">{{ pkg.price }}</span>
              <span class="price-currency">€</span>
            </div>

            <div class="package-rate">
              {{ pkg.price_per_credit }}€ pro Credit
            </div>

            <button
              @click="buyPackage(pkg.id)"
              :disabled="loading"
              class="zen-btn"
              :class="pkg.id === 'medium' ? 'zen-btn-filled' : 'zen-btn-ai'"
            >
              {{ loading ? 'Laden...' : 'Jetzt kaufen' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Purchase History -->
      <section v-if="purchases.length" class="history-section">
        <div class="ink-stroke"></div>

        <h2 class="section-title">Kaufhistorie</h2>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Datum</th>
                <th>Paket</th>
                <th>Credits</th>
                <th>Preis</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="purchase in purchases" :key="purchase.id">
                <td>{{ formatDate(purchase.created_at) }}</td>
                <td>{{ purchase.package_name }}</td>
                <td>{{ purchase.credits_purchased }}</td>
                <td>{{ purchase.price_eur }}€</td>
                <td>
                  <span class="badge" :class="'badge-' + getStatusType(purchase.status)">
                    {{ getStatusLabel(purchase.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="history-summary">
          <span class="summary-label">Gesamtausgaben</span>
          <span class="summary-value">{{ totalSpent }}€</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { authStore } from '../store/auth'

const packages = ref([])
const purchases = ref([])
const totalSpent = ref(0)
const loading = ref(false)

const loadPackages = async () => {
  try {
    const { data } = await api.get('/payments/packages')
    packages.value = data.packages
  } catch (error) {
    console.error('Failed to load packages:', error)
  }
}

const loadPurchaseHistory = async () => {
  try {
    const { data } = await api.get('/payments/history')
    purchases.value = data.purchases
    totalSpent.value = data.total_spent
  } catch (error) {
    console.error('Failed to load purchase history:', error)
  }
}

const buyPackage = async (packageId) => {
  loading.value = true
  try {
    const { data } = await api.post('/payments/create-order', {
      package: packageId,
      return_url: `${window.location.origin}/payment/success`,
      cancel_url: `${window.location.origin}/buy-credits`
    })

    if (data.success) {
      window.location.href = data.approval_url
    }
  } catch (error) {
    console.error('Payment creation error:', error)
    if (window.$toast) {
      window.$toast('Fehler beim Erstellen der Bestellung', 'error')
    }
    loading.value = false
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('de-DE')
}

const getStatusLabel = (status) => {
  const labels = {
    'pending': 'Ausstehend',
    'completed': 'Abgeschlossen',
    'failed': 'Fehlgeschlagen',
    'cancelled': 'Abgebrochen',
    'refunded': 'Erstattet'
  }
  return labels[status] || status
}

const getStatusType = (status) => {
  const types = {
    'pending': 'warning',
    'completed': 'success',
    'failed': 'error',
    'cancelled': 'neutral',
    'refunded': 'neutral'
  }
  return types[status] || 'neutral'
}

onMounted(() => {
  loadPackages()
  loadPurchaseHistory()
})
</script>

<style scoped>
.credits-page {
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
   BALANCE SECTION
   ======================================== */
.balance-section {
  margin-bottom: var(--space-ma);
}

.balance-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-ma-lg);
  position: relative;
  overflow: hidden;
}

.balance-content {
  position: relative;
  z-index: 1;
}

.balance-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  opacity: 0.8;
  margin-bottom: var(--space-sm);
}

.balance-value {
  font-family: var(--font-display);
  font-size: clamp(4rem, 10vw, 6rem);
  font-weight: 400;
  line-height: 1;
  margin-bottom: var(--space-sm);
}

.balance-info {
  font-size: 0.875rem;
  opacity: 0.7;
}

.balance-decoration {
  position: absolute;
  right: var(--space-ma);
  top: 50%;
  transform: translateY(-50%);
}

.balance-enso {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-width: 2px 3px 2px 2.5px;
  opacity: 0.15;
}

/* ========================================
   PACKAGES SECTION
   ======================================== */
.packages-section {
  margin: var(--space-ma) 0;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.package-card {
  text-align: center;
  padding: var(--space-ma);
  position: relative;
}

.package-featured {
  border-color: var(--color-ai);
}

.package-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-ai);
  color: var(--color-text-inverse);
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.package-header h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
  color: var(--color-sumi);
}

.package-credits {
  margin-bottom: var(--space-md);
}

.credits-value {
  font-family: var(--font-display);
  font-size: 3.5rem;
  font-weight: 400;
  color: var(--color-ai);
  line-height: 1;
}

.credits-unit {
  display: block;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.package-price {
  margin-bottom: var(--space-xs);
}

.price-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.price-currency {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
}

.package-rate {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-lg);
}

.package-card .zen-btn {
  width: 100%;
}

/* ========================================
   HISTORY SECTION
   ======================================== */
.history-section {
  margin-top: var(--space-ma-lg);
}

.history-summary {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-washi-warm);
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

.summary-label {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.summary-value {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-sumi);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 968px) {
  .packages-grid {
    grid-template-columns: 1fr;
    max-width: 400px;
    margin: 0 auto;
  }

  .balance-card {
    padding: var(--space-lg);
  }

  .balance-value {
    font-size: 4rem;
  }

  .balance-enso {
    width: 100px;
    height: 100px;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .balance-decoration {
    display: none;
  }

  .credits-value {
    font-size: 2.5rem;
  }
}
</style>
