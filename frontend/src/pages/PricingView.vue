<template>
  <div class="pricing-page">
    <!-- Top Navigation -->
    <nav class="landing-nav">
      <div class="landing-nav-inner">
        <router-link to="/" class="nav-brand">
          <div class="nav-brand-enso"></div>
          <span>obo</span>
        </router-link>
        <div class="nav-links">
          <router-link to="/" class="nav-link">Start</router-link>
          <router-link to="/pricing" class="nav-link">{{ $t('landing.nav.pricing') }}</router-link>
          <router-link to="/login" class="nav-link">{{ $t('landing.nav.login') }}</router-link>
          <router-link to="/register" class="nav-link nav-link-cta">{{ $t('landing.nav.register') }}</router-link>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="pricing-hero">
      <div class="container">
        <div class="pricing-hero-content animate-fade-up">
          <h1>{{ $t('pricing.title') }}</h1>
          <p>{{ $t('pricing.subtitle') }}</p>
        </div>
      </div>
    </section>

    <!-- Pricing Cards -->
    <section class="pricing-cards-section" data-reveal>
      <div class="container">
        <div class="pricing-cards-grid">
          <div
            v-for="plan in plans"
            :key="plan.key"
            class="pricing-card"
            :class="{ 'pricing-card-featured': plan.featured }"
          >
            <div v-if="plan.featured" class="pricing-badge">
              {{ $t('pricing.starter.popular') }}
            </div>
            <div class="pricing-header">
              <h3>{{ $t(`pricing.${plan.key}.name`) }}</h3>
              <p class="pricing-description">{{ $t(`pricing.${plan.key}.description`) }}</p>
              <div class="pricing-price">
                <span class="price-amount">{{ plan.price }}</span>
                <div class="price-meta">
                  <span class="price-currency">EUR</span>
                  <span class="price-period">{{ $t(`pricing.${plan.key}.period`) }}</span>
                </div>
              </div>
            </div>
            <ul class="pricing-features">
              <li v-for="feature in plan.features" :key="feature">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-koke)" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ feature }}
              </li>
            </ul>
            <router-link
              :to="`/register?plan=${plan.key}`"
              class="zen-btn pricing-cta"
              :class="plan.btnClass"
            >
              {{ $t(`pricing.${plan.key}.cta`) }}
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Feature Comparison Table (desktop) -->
    <section class="pricing-comparison-section" data-reveal>
      <div class="container">
        <div class="section-header">
          <h2>Feature-Vergleich</h2>
        </div>
        <div class="pricing-table-wrapper">
          <table class="pricing-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Free</th>
                <th class="pricing-table-featured">Starter</th>
                <th>Pro</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in comparisonRows" :key="row.label">
                <td>{{ row.label }}</td>
                <td>
                  <template v-if="row.free === true">
                    <svg class="pricing-check" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-koke)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </template>
                  <template v-else-if="row.free === false">
                    <svg class="pricing-cross" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-ghost)" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </template>
                  <template v-else>
                    <span class="pricing-text-value">{{ row.free }}</span>
                  </template>
                </td>
                <td class="pricing-table-featured">
                  <template v-if="row.starter === true">
                    <svg class="pricing-check" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-koke)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </template>
                  <template v-else-if="row.starter === false">
                    <svg class="pricing-cross" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-ghost)" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </template>
                  <template v-else>
                    <span class="pricing-text-value">{{ row.starter }}</span>
                  </template>
                </td>
                <td>
                  <template v-if="row.pro === true">
                    <svg class="pricing-check" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-koke)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </template>
                  <template v-else-if="row.pro === false">
                    <svg class="pricing-cross" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-ghost)" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </template>
                  <template v-else>
                    <span class="pricing-text-value">{{ row.pro }}</span>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile comparison cards -->
        <div class="pricing-comparison-mobile">
          <div v-for="plan in plans" :key="plan.key" class="pricing-mobile-card">
            <h4>{{ $t(`pricing.${plan.key}.name`) }}</h4>
            <ul>
              <li v-for="row in comparisonRows" :key="row.label">
                <span class="pricing-mobile-label">{{ row.label }}</span>
                <span class="pricing-mobile-value">
                  <template v-if="row[plan.key] === true">
                    <svg class="pricing-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-koke)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </template>
                  <template v-else-if="row[plan.key] === false">
                    <svg class="pricing-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-ghost)" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </template>
                  <template v-else>{{ row[plan.key] }}</template>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ Section -->
    <section class="pricing-faq-section" data-reveal>
      <div class="container">
        <div class="section-header">
          <h2>{{ $t('pricing.faq.title') }}</h2>
        </div>
        <FaqAccordion :items="pricingFaqItems" />
      </div>
    </section>

    <!-- Final CTA -->
    <section class="pricing-final-cta" data-reveal>
      <div class="container">
        <div class="pricing-cta-content">
          <h2>{{ $t('pricing.cta.title') }}</h2>
          <p>{{ $t('pricing.cta.subtitle') }}</p>
          <router-link to="/register" class="zen-btn pricing-cta-btn">
            {{ $t('pricing.cta.button') }}
          </router-link>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="pricing-footer">
      <div class="container">
        <div class="pricing-footer-grid">
          <div class="pricing-footer-brand">
            <div class="pricing-footer-brand-top">
              <div class="footer-enso"></div>
              <span>obo</span>
            </div>
            <p class="pricing-footer-tagline">{{ $t('landing.footer.tagline') }}</p>
            <div class="pricing-footer-badges">
              <span class="pricing-footer-badge">DSGVO</span>
              <span class="pricing-footer-badge">Made in Germany</span>
            </div>
          </div>
          <div class="pricing-footer-col">
            <h4>{{ $t('landing.footer.product') }}</h4>
            <router-link to="/">Start</router-link>
            <router-link to="/pricing">{{ $t('landing.footer.pricing') }}</router-link>
          </div>
          <div class="pricing-footer-col">
            <h4>{{ $t('landing.footer.legal') }}</h4>
            <router-link to="/impressum">Impressum</router-link>
            <router-link to="/datenschutz">Datenschutz</router-link>
          </div>
          <div class="pricing-footer-col">
            <h4>Konto</h4>
            <router-link to="/login">{{ $t('landing.nav.login') }}</router-link>
            <router-link to="/register">Registrieren</router-link>
          </div>
        </div>
        <div class="pricing-footer-bottom">
          &copy; {{ currentYear }} obo
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import FaqAccordion from '../components/landing/FaqAccordion.vue'
import { useScrollReveal } from '../composables/useScrollReveal.js'

const { t } = useI18n()

useScrollReveal()

const currentYear = computed(() => new Date().getFullYear())

const plans = [
  {
    key: 'free',
    price: '0',
    featured: false,
    btnClass: '',
    features: [
      '3 Bewerbungen/Monat',
      'KI-Anschreiben',
      'Basis-Vorlagen',
      'PDF-Export'
    ]
  },
  {
    key: 'starter',
    price: '9,90',
    featured: true,
    btnClass: 'zen-btn-filled',
    features: [
      '50 Bewerbungen/Monat',
      'KI-Anschreiben',
      'Alle Vorlagen',
      'PDF-Export',
      'ATS-Check',
      'E-Mail-Entwurf',
      'Job-Fit Score'
    ]
  },
  {
    key: 'pro',
    price: '19,90',
    featured: false,
    btnClass: 'zen-btn-ai',
    features: [
      'Unbegrenzt',
      'KI-Anschreiben',
      'Premium-Vorlagen',
      'PDF-Export',
      'ATS-Check',
      'E-Mail-Entwurf',
      'Job-Fit Score',
      'Interview-Vorbereitung',
      'Gehalts-Coach',
      'Prioritäts-Support',
      'Bewerbungs-Insights'
    ]
  }
]

const comparisonRows = [
  { label: 'Bewerbungen/Monat', free: '3', starter: '50', pro: '\u221E' },
  { label: 'Anschreiben-Generator', free: true, starter: true, pro: true },
  { label: 'Vorlagen', free: 'Basis', starter: 'Alle', pro: 'Premium' },
  { label: 'PDF-Export', free: true, starter: true, pro: true },
  { label: 'ATS-Check', free: false, starter: true, pro: true },
  { label: 'E-Mail-Entwurf', free: false, starter: true, pro: true },
  { label: 'Job-Fit Score', free: false, starter: true, pro: true },
  { label: 'Interview-Vorbereitung', free: false, starter: false, pro: true },
  { label: 'Gehalts-Coach', free: false, starter: false, pro: true },
  { label: 'Prioritäts-Support', free: false, starter: false, pro: true },
  { label: 'Bewerbungs-Insights', free: false, starter: false, pro: true }
]

const pricingFaqItems = computed(() => [
  { question: t('pricing.faq.q1'), answer: t('pricing.faq.a1') },
  { question: t('pricing.faq.q2'), answer: t('pricing.faq.a2') },
  { question: t('pricing.faq.q3'), answer: t('pricing.faq.a3') },
  { question: t('pricing.faq.q4'), answer: t('pricing.faq.a4') }
])
</script>

<style scoped>
.pricing-page {
  min-height: 100vh;
  background: var(--color-washi);
}

/* ========================================
   NAV (reused from Landing)
   ======================================== */
.landing-nav {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  padding: var(--space-md) var(--space-ma);
}

.landing-nav-inner {
  max-width: var(--container-xl);
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  text-decoration: none;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
  letter-spacing: -0.02em;
}

.nav-brand-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  opacity: 0.7;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.nav-link {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-full);
  transition: color var(--transition-base);
}

.nav-link:hover {
  color: var(--color-sumi);
}

.nav-link-cta {
  background: var(--color-ai);
  color: var(--color-text-inverse);
  font-weight: 500;
}

.nav-link-cta:hover {
  color: var(--color-text-inverse);
  opacity: 0.9;
}

/* ========================================
   HERO
   ======================================== */
.pricing-hero {
  padding: var(--space-ma-2xl) 0 var(--space-ma-lg);
  text-align: center;
}

.pricing-hero-content h1 {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  color: var(--color-sumi);
  margin-bottom: var(--space-md);
}

.pricing-hero-content p {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  max-width: 560px;
  margin: 0 auto;
  line-height: var(--leading-relaxed);
}

/* ========================================
   PRICING CARDS
   ======================================== */
.pricing-cards-section {
  padding: 0 0 var(--space-ma-2xl);
}

.pricing-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
  max-width: 1080px;
  margin: 0 auto;
  align-items: start;
}

.pricing-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-light);
  padding: var(--space-xl);
  position: relative;
  transition: all var(--transition-base);
}

.pricing-card:hover {
  box-shadow: var(--shadow-lifted);
  transform: translateY(-4px);
}

.pricing-card-featured {
  border-color: var(--color-ai);
  background: linear-gradient(135deg, var(--color-bg-elevated) 0%, var(--color-ai-subtle) 100%);
  box-shadow: var(--shadow-lifted);
}

.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  white-space: nowrap;
}

.pricing-header {
  text-align: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.pricing-header h3 {
  font-size: 1.25rem;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
}

.pricing-description {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-md);
}

.pricing-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--space-xs);
}

.price-amount {
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: 500;
  color: var(--color-sumi);
  line-height: 1;
}

.price-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.price-currency {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.price-period {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.pricing-features {
  list-style: none;
  margin-bottom: var(--space-xl);
  padding: 0;
}

.pricing-features li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.pricing-features svg {
  flex-shrink: 0;
}

.pricing-cta {
  width: 100%;
  justify-content: center;
  text-align: center;
  display: flex;
}

/* ========================================
   FEATURE COMPARISON TABLE
   ======================================== */
.pricing-comparison-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-ma-lg);
}

.section-header h2 {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
  color: var(--color-sumi);
}

.pricing-table-wrapper {
  max-width: 900px;
  margin: 0 auto;
  overflow-x: auto;
}

.pricing-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border-light);
}

.pricing-table thead {
  background: var(--color-washi-aged);
}

.pricing-table th {
  padding: var(--space-md) var(--space-lg);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-sumi);
  text-align: center;
}

.pricing-table th:first-child {
  text-align: left;
}

.pricing-table td {
  padding: var(--space-md) var(--space-lg);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  text-align: center;
  border-top: 1px solid var(--color-border-light);
}

.pricing-table td:first-child {
  text-align: left;
  font-weight: 500;
  color: var(--color-sumi);
}

.pricing-table-featured {
  background: var(--color-ai-subtle);
}

.pricing-check,
.pricing-cross {
  display: inline-block;
  vertical-align: middle;
}

.pricing-text-value {
  font-weight: 500;
  color: var(--color-sumi);
}

/* Mobile comparison cards (hidden on desktop) */
.pricing-comparison-mobile {
  display: none;
}

/* ========================================
   FAQ SECTION
   ======================================== */
.pricing-faq-section {
  padding: var(--space-ma-2xl) 0;
}

/* ========================================
   FINAL CTA
   ======================================== */
.pricing-final-cta {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-ai);
  text-align: center;
}

.pricing-cta-content h2 {
  font-size: clamp(1.5rem, 4vw, 2rem);
  color: var(--color-text-inverse);
  margin-bottom: var(--space-md);
}

.pricing-cta-content p {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--space-lg);
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.pricing-cta-btn {
  background: var(--color-washi);
  color: var(--color-ai);
  font-weight: 500;
}

.pricing-cta-btn:hover {
  background: var(--color-washi-warm);
}

/* ========================================
   FOOTER
   ======================================== */
.pricing-footer {
  padding: var(--space-ma-lg) 0 var(--space-xl);
  background: var(--color-washi-warm);
  border-top: 1px solid var(--color-border-light);
}

.pricing-footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.pricing-footer-brand-top {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.footer-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1.5px solid var(--color-text-ghost);
  opacity: 0.6;
}

.pricing-footer-tagline {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-md);
  line-height: var(--leading-relaxed);
}

.pricing-footer-badges {
  display: flex;
  gap: var(--space-sm);
}

.pricing-footer-badge {
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-washi-aged);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.pricing-footer-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.pricing-footer-col h4 {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.pricing-footer-col a {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  transition: color var(--transition-base);
}

.pricing-footer-col a:hover {
  color: var(--color-ai);
}

.pricing-footer-bottom {
  text-align: center;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
}

/* ========================================
   CONTAINER
   ======================================== */
.container {
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: 0 var(--space-ma);
}

/* ========================================
   ANIMATIONS
   ======================================== */
.animate-fade-up {
  animation: fadeUp 0.6s var(--ease-zen) both;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 1024px) {
  .pricing-cards-grid {
    grid-template-columns: 1fr;
    max-width: 420px;
  }

  .pricing-footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-lg);
  }

  .pricing-footer-brand {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .landing-nav {
    padding: var(--space-sm) var(--space-md);
  }

  .nav-link {
    padding: var(--space-xs) var(--space-sm);
    font-size: 0.875rem;
  }

  .pricing-hero {
    padding: var(--space-ma-xl) 0 var(--space-ma);
  }

  .pricing-hero-content h1 {
    font-size: clamp(1.75rem, 7vw, 2.25rem);
  }

  .pricing-hero-content p {
    font-size: 1.0625rem;
  }

  /* Hide desktop table, show mobile cards */
  .pricing-table-wrapper {
    display: none;
  }

  .pricing-comparison-mobile {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
  }

  .pricing-mobile-card {
    background: var(--color-bg-elevated);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border-light);
    padding: var(--space-lg);
  }

  .pricing-mobile-card h4 {
    font-size: 1.125rem;
    font-weight: 500;
    color: var(--color-sumi);
    margin-bottom: var(--space-md);
    padding-bottom: var(--space-sm);
    border-bottom: 1px solid var(--color-border-light);
  }

  .pricing-mobile-card ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .pricing-mobile-card li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-sm) 0;
    font-size: 0.875rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .pricing-mobile-card li:last-child {
    border-bottom: none;
  }

  .pricing-mobile-label {
    color: var(--color-text-secondary);
  }

  .pricing-mobile-value {
    font-weight: 500;
    color: var(--color-sumi);
  }

  .pricing-footer-grid {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .pricing-footer-brand-top {
    justify-content: center;
  }

  .pricing-footer-badges {
    justify-content: center;
  }

  .pricing-footer-col {
    align-items: center;
  }
}
</style>
