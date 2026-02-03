<template>
  <div class="landing-page">
    <!-- Hero Section - The product IS the hero -->
    <section class="hero-section">
      <div class="hero-container">
        <!-- Brand Mark -->
        <div class="hero-brand animate-fade-up">
          <div class="brand-enso"></div>
          <span class="brand-name">obo</span>
        </div>

        <!-- Hero Content -->
        <div class="hero-content animate-fade-up" style="animation-delay: 100ms;">
          <h1 class="hero-title">Bewerbungen, die sich selbst schreiben.</h1>
          <p class="hero-subtitle">
            Paste die URL einer Stellenanzeige. Erhalte in Sekunden ein personalisiertes Anschreiben.
          </p>
        </div>

        <!-- Demo Generator - The core experience -->
        <div class="demo-input-section animate-fade-up" style="animation-delay: 200ms;">
          <DemoGenerator @demo-started="onDemoStarted" @demo-complete="onDemoComplete" />

          <!-- Supported Sites -->
          <div class="supported-sites">
            <span class="supported-label">Unterstützte Portale:</span>
            <div class="site-badges">
              <span class="site-badge">Indeed</span>
              <span class="site-badge">StepStone</span>
              <span class="site-badge">XING</span>
              <span class="site-badge site-badge-more">+50 weitere</span>
            </div>
          </div>
        </div>

        <!-- Decorative Enso -->
        <div class="hero-enso-bg"></div>
      </div>
    </section>

    <!-- How It Works - Below the fold -->
    <section class="how-it-works-section">
      <div class="container">
        <div class="section-header animate-fade-up">
          <span class="section-label">So funktioniert's</span>
          <h2 class="section-title">Drei Schritte zum perfekten Anschreiben</h2>
        </div>

        <div class="steps-grid">
          <div class="step-card animate-fade-up" style="animation-delay: 100ms;">
            <div class="step-number">1</div>
            <div class="step-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </div>
            <h3>URL einfugen</h3>
            <p>Kopiere die URL der Stellenanzeige von Indeed, StepStone oder anderen Jobportalen.</p>
          </div>

          <div class="step-card animate-fade-up" style="animation-delay: 200ms;">
            <div class="step-number">2</div>
            <div class="step-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
            </div>
            <h3>KI analysiert</h3>
            <p>Unsere KI extrahiert die Anforderungen und erstellt ein massgeschneidertes Anschreiben.</p>
          </div>

          <div class="step-card animate-fade-up" style="animation-delay: 300ms;">
            <div class="step-number">3</div>
            <div class="step-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <h3>Anschreiben erhalten</h3>
            <p>Bearbeite, exportiere als PDF und bewirb dich - alles in unter einer Minute.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Social Proof -->
    <section class="social-proof-section">
      <div class="container">
        <div class="proof-content animate-fade-up">
          <div class="proof-stats">
            <div class="proof-stat">
              <span class="stat-value">5.000+</span>
              <span class="stat-label">Anschreiben generiert</span>
            </div>
            <div class="proof-divider"></div>
            <div class="proof-stat">
              <span class="stat-value">4.8</span>
              <span class="stat-label">Durchschnittliche Bewertung</span>
            </div>
            <div class="proof-divider"></div>
            <div class="proof-stat">
              <span class="stat-value">&lt; 30s</span>
              <span class="stat-label">Durchschnittliche Zeit</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing Preview -->
    <section class="pricing-section">
      <div class="container">
        <div class="section-header animate-fade-up">
          <span class="section-label">Preise</span>
          <h2 class="section-title">Starte kostenlos</h2>
        </div>

        <div class="pricing-grid">
          <div class="pricing-card animate-fade-up" style="animation-delay: 100ms;">
            <div class="pricing-header">
              <h3>Free</h3>
              <div class="pricing-price">
                <span class="price-amount">0</span>
                <span class="price-currency">EUR</span>
                <span class="price-period">/Monat</span>
              </div>
            </div>
            <ul class="pricing-features">
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                3 Anschreiben pro Monat
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Basis-Vorlagen
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                PDF-Export
              </li>
            </ul>
            <router-link to="/register" class="pricing-cta zen-btn">
              Kostenlos starten
            </router-link>
          </div>

          <div class="pricing-card pricing-card-featured animate-fade-up" style="animation-delay: 200ms;">
            <div class="pricing-badge">Beliebt</div>
            <div class="pricing-header">
              <h3>Pro</h3>
              <div class="pricing-price">
                <span class="price-amount">9</span>
                <span class="price-currency">EUR</span>
                <span class="price-period">/Monat</span>
              </div>
            </div>
            <ul class="pricing-features">
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Unbegrenzte Anschreiben
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Alle Premium-Vorlagen
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Job-Fit Score
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Interview-Vorbereitung
              </li>
            </ul>
            <router-link to="/register?plan=pro" class="pricing-cta zen-btn zen-btn-ai">
              Pro wahlen
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Final CTA -->
    <section class="final-cta-section">
      <div class="container">
        <div class="cta-content animate-fade-up">
          <h2>Bereit fur deine nachste Bewerbung?</h2>
          <p>Probiere es jetzt aus - kostenlos und ohne Anmeldung.</p>
          <button @click="scrollToTop" class="zen-btn zen-btn-ai zen-btn-lg">
            Jetzt Anschreiben erstellen
          </button>
        </div>
      </div>
    </section>

    <!-- Footer Links -->
    <footer class="landing-footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-brand">
            <div class="footer-enso"></div>
            <span>obo</span>
          </div>
          <div class="footer-links">
            <router-link to="/login">Anmelden</router-link>
            <router-link to="/register">Registrieren</router-link>
            <router-link to="/impressum">Impressum</router-link>
            <router-link to="/datenschutz">Datenschutz</router-link>
          </div>
          <div class="footer-copyright">
            &copy; {{ currentYear }} obo
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import DemoGenerator from '../components/landing/DemoGenerator.vue'

const router = useRouter()
const currentYear = computed(() => new Date().getFullYear())

const onDemoStarted = () => {
  // Track demo start for analytics
}

const onDemoComplete = (result) => {
  // When demo is complete, redirect to register with the result
  // The demo result will be stored and shown after registration
  router.push({
    path: '/register',
    query: { demo: 'complete', jobUrl: result.url }
  })
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: var(--color-washi);
}

/* ========================================
   HERO SECTION
   ======================================== */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma-xl) var(--space-ma);
  overflow: hidden;
}

.hero-container {
  max-width: var(--container-md);
  width: 100%;
  text-align: center;
  position: relative;
  z-index: 1;
}

.hero-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-ma-lg);
}

.brand-enso {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2.5px solid var(--color-sumi);
  border-width: 2.5px 3px 2.5px 2.5px;
  opacity: 0.8;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 500;
  color: var(--color-sumi);
  letter-spacing: -0.02em;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 400;
  line-height: 1.1;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-lg);
  color: var(--color-sumi);
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin: 0 auto var(--space-ma-lg);
  line-height: var(--leading-relaxed);
}

.hero-enso-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 600px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 3px 2px 2.5px;
  opacity: 0.02;
  pointer-events: none;
}

/* Demo Input Section */
.demo-input-section {
  max-width: 600px;
  margin: 0 auto;
}

.supported-sites {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}

.supported-label {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.site-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.site-badge {
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.site-badge-more {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

/* ========================================
   HOW IT WORKS SECTION
   ======================================== */
.how-it-works-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-ma-lg);
}

.section-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-ai);
  margin-bottom: var(--space-sm);
}

.section-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
  color: var(--color-sumi);
  margin-bottom: 0;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.step-card {
  text-align: center;
  padding: var(--space-xl);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  position: relative;
}

.step-number {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  color: var(--color-text-inverse);
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 600;
}

.step-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-lg);
  color: var(--color-ai);
}

.step-card h3 {
  font-size: 1.125rem;
  margin-bottom: var(--space-sm);
}

.step-card p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

/* ========================================
   SOCIAL PROOF SECTION
   ======================================== */
.social-proof-section {
  padding: var(--space-ma-lg) 0;
  background: var(--color-washi);
}

.proof-content {
  max-width: var(--container-lg);
  margin: 0 auto;
}

.proof-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xl);
}

.proof-stat {
  text-align: center;
}

.proof-stat .stat-value {
  display: block;
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 500;
  color: var(--color-ai);
  line-height: 1;
  margin-bottom: var(--space-xs);
}

.proof-stat .stat-label {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.proof-divider {
  width: 1px;
  height: 48px;
  background: var(--color-border);
}

/* ========================================
   PRICING SECTION
   ======================================== */
.pricing-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-xl);
  max-width: 800px;
  margin: 0 auto;
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
}

.pricing-header {
  text-align: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.pricing-header h3 {
  font-size: 1.25rem;
  margin-bottom: var(--space-sm);
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

.price-currency {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
}

.price-period {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.pricing-features {
  list-style: none;
  margin-bottom: var(--space-xl);
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
  color: var(--color-koke);
  flex-shrink: 0;
}

.pricing-cta {
  width: 100%;
  justify-content: center;
}

/* ========================================
   FINAL CTA SECTION
   ======================================== */
.final-cta-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-ai);
  text-align: center;
}

.cta-content h2 {
  font-size: clamp(1.5rem, 4vw, 2rem);
  color: var(--color-text-inverse);
  margin-bottom: var(--space-md);
}

.cta-content p {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--space-lg);
}

.cta-content .zen-btn {
  background: var(--color-washi);
  color: var(--color-ai);
}

.cta-content .zen-btn:hover {
  background: var(--color-washi-cream);
}

/* ========================================
   FOOTER
   ======================================== */
.landing-footer {
  padding: var(--space-xl) 0;
  background: var(--color-washi-warm);
  border-top: 1px solid var(--color-border-light);
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-size: 1.125rem;
  color: var(--color-text-tertiary);
}

.footer-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1.5px solid var(--color-text-ghost);
  opacity: 0.6;
}

.footer-links {
  display: flex;
  gap: var(--space-lg);
}

.footer-links a {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  transition: color var(--transition-base);
}

.footer-links a:hover {
  color: var(--color-ai);
}

.footer-copyright {
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
  .steps-grid {
    grid-template-columns: 1fr;
    max-width: 500px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: var(--space-ma-lg) var(--space-md);
    min-height: auto;
    padding-top: var(--space-ma-xl);
    padding-bottom: var(--space-ma-xl);
  }

  .hero-title {
    font-size: clamp(2rem, 8vw, 2.5rem);
  }

  .hero-subtitle {
    font-size: 1.125rem;
  }

  .proof-stats {
    flex-direction: column;
    gap: var(--space-lg);
  }

  .proof-divider {
    width: 48px;
    height: 1px;
  }

  .pricing-grid {
    grid-template-columns: 1fr;
  }

  .footer-content {
    flex-direction: column;
    text-align: center;
  }

  .footer-links {
    flex-wrap: wrap;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .supported-sites {
    flex-direction: column;
  }

  .site-badges {
    justify-content: center;
  }
}
</style>
