<template>
  <div class="auth-page">
    <!-- Theme Toggle - Floating -->
    <button @click="toggleTheme" class="theme-toggle-float" :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
      <svg v-if="isDarkMode" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </button>

    <!-- Decorative Elements -->
    <div class="auth-decoration">
      <div class="enso-decoration enso-1"></div>
      <div class="enso-decoration enso-2"></div>
      <div class="vertical-text">確</div>
    </div>

    <!-- Main Content -->
    <div class="auth-container">
      <!-- Form Section -->
      <div class="auth-form-section animate-fade-up">
        <!-- Brand -->
        <router-link to="/" class="auth-brand">
          <div class="brand-enso"></div>
          <span>obo</span>
        </router-link>

        <!-- Header -->
        <div class="auth-header">
          <h1>E-Mail bestätigen</h1>
          <p>Verifizieren Sie Ihre E-Mail-Adresse</p>
        </div>

        <!-- Main Card -->
        <div class="verification-card zen-card">
          <div class="verification-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>

          <h3>Verifizierungs-E-Mail gesendet</h3>
          <p class="email-info">
            Wir haben eine Bestätigungs-E-Mail an <strong>{{ userEmail }}</strong> gesendet.
          </p>
          <p class="instructions">
            Klicken Sie auf den Link in der E-Mail, um Ihr Konto zu verifizieren.
            Falls Sie die E-Mail nicht finden, prüfen Sie bitte auch Ihren Spam-Ordner.
          </p>

          <!-- Success Message -->
          <div v-if="successMessage" class="alert alert-success">
            {{ successMessage }}
          </div>

          <!-- Error Message -->
          <div v-if="error" class="alert alert-error">
            {{ error }}
          </div>

          <!-- Resend Button -->
          <button
            @click="resendVerification"
            class="zen-btn zen-btn-filled zen-btn-lg"
            :disabled="loading || cooldownSeconds > 0"
          >
            <span v-if="loading">Wird gesendet...</span>
            <span v-else-if="cooldownSeconds > 0">
              Erneut senden in {{ formattedCooldown }}
            </span>
            <span v-else>Erneut senden</span>
          </button>

          <p class="rate-limit-info" v-if="cooldownSeconds > 0">
            Sie können maximal 3 Verifizierungs-E-Mails pro Stunde anfordern.
          </p>
        </div>

        <!-- Divider -->
        <div class="ink-stroke"></div>

        <!-- Footer -->
        <div class="auth-footer">
          <p>Falsche E-Mail? <router-link to="/register">Neu registrieren</router-link></p>
          <p>Bereits verifiziert? <router-link to="/login">Anmelden</router-link></p>
        </div>
      </div>

      <!-- Info Section -->
      <div class="auth-info-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="info-content">
          <h2>Warum E-Mail<br/>verifizieren?</h2>
          <p class="info-description">
            Die Verifizierung schützt Ihr Konto und ermöglicht uns,
            wichtige Informationen sicher zuzustellen.
          </p>

          <ul class="feature-list">
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Schutz vor unbefugtem Zugriff</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Passwort-Wiederherstellung möglich</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Wichtige Benachrichtigungen</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Voller Funktionsumfang</span>
            </li>
          </ul>
        </div>

        <!-- Seasonal accent -->
        <div class="seasonal-accent"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/client'

const route = useRoute()

const userEmail = ref('')
const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const cooldownSeconds = ref(0)
const isDarkMode = ref(false)

let cooldownInterval = null

const THEME_KEY = 'obojobs-theme'

// Format countdown as "X Min Y Sek" when > 60s, otherwise just "Xs"
const formattedCooldown = computed(() => {
  const seconds = cooldownSeconds.value
  if (seconds > 60) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes} Min ${remainingSeconds} Sek`
  }
  return `${seconds}s`
})

// Initialize theme state
const initTheme = () => {
  const savedTheme = localStorage.getItem(THEME_KEY)
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark'
  } else {
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
}

// Toggle theme
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem(THEME_KEY, isDarkMode.value ? 'dark' : 'light')

  const root = document.documentElement
  if (isDarkMode.value) {
    root.classList.add('dark-mode')
    root.classList.remove('light-mode')
  } else {
    root.classList.add('light-mode')
    root.classList.remove('dark-mode')
  }
}

const startCooldown = (seconds) => {
  cooldownSeconds.value = seconds
  if (cooldownInterval) {
    clearInterval(cooldownInterval)
  }
  cooldownInterval = setInterval(() => {
    cooldownSeconds.value--
    if (cooldownSeconds.value <= 0) {
      clearInterval(cooldownInterval)
      cooldownInterval = null
    }
  }, 1000)
}

const resendVerification = async () => {
  try {
    loading.value = true
    error.value = ''
    successMessage.value = ''

    await api.post('/auth/send-verification')

    successMessage.value = 'Verifizierungs-E-Mail wurde erneut gesendet!'
    startCooldown(60) // 60 seconds cooldown
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Fehler beim Senden der E-Mail.'
    error.value = errorMsg

    // If rate limited, show cooldown
    if (e.response?.status === 429) {
      startCooldown(60)
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initTheme()
  // Get email from query param or localStorage
  userEmail.value = route.query.email || localStorage.getItem('pendingVerificationEmail') || 'ihre@email.de'
})

onUnmounted(() => {
  if (cooldownInterval) {
    clearInterval(cooldownInterval)
  }
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--color-washi);
  position: relative;
  overflow: hidden;
}

/* ========================================
   FLOATING THEME TOGGLE
   ======================================== */
.theme-toggle-float {
  position: fixed;
  top: var(--space-lg);
  right: var(--space-lg);
  z-index: 100;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  box-shadow: var(--shadow-paper);
  transition: all var(--transition-base);
}

.theme-toggle-float:hover {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  box-shadow: var(--shadow-lifted);
  transform: scale(1.05);
}

.theme-toggle-float:hover svg {
  transform: rotate(15deg);
}

.theme-toggle-float svg {
  transition: transform var(--transition-base);
}

/* ========================================
   DECORATIVE ELEMENTS
   ======================================== */
.auth-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.enso-decoration {
  position: absolute;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  opacity: 0.04;
}

.enso-1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -100px;
  border-width: 3px 4px 3px 3.5px;
  animation: float 30s var(--ease-zen) infinite;
}

.enso-2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -100px;
  border-width: 2px 3px 2px 2.5px;
  animation: float 25s var(--ease-zen) infinite reverse;
}

.vertical-text {
  position: absolute;
  right: 80px;
  top: 50%;
  transform: translateY(-50%);
  font-family: var(--font-display);
  font-size: 12rem;
  color: var(--color-sumi);
  opacity: 0.02;
  writing-mode: vertical-rl;
  user-select: none;
}

/* ========================================
   MAIN CONTAINER - Asymmetric Grid
   ======================================== */
.auth-container {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: var(--space-ma-xl);
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-ma-xl) var(--space-ma);
  align-items: center;
}

/* ========================================
   FORM SECTION
   ======================================== */
.auth-form-section {
  max-width: 480px;
}

.auth-brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  color: var(--color-sumi);
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-ma-lg);
}

.brand-enso {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 2.5px 2px 2px;
  opacity: 0.8;
}

.auth-header {
  margin-bottom: var(--space-ma);
}

.auth-header h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 400;
  margin-bottom: var(--space-sm);
  letter-spacing: -0.03em;
}

.auth-header p {
  color: var(--color-text-tertiary);
  font-size: 1.0625rem;
  margin-bottom: 0;
}

/* Verification Card */
.verification-card {
  text-align: center;
  padding: var(--space-ma-lg);
  margin-bottom: var(--space-ma);
}

.verification-icon {
  color: var(--color-ai);
  margin-bottom: var(--space-lg);
}

.verification-card h3 {
  font-size: 1.5rem;
  margin-bottom: var(--space-md);
}

.email-info {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-sm);
}

.email-info strong {
  color: var(--color-sumi);
}

.instructions {
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

.verification-card .zen-btn {
  width: 100%;
  margin-top: var(--space-md);
}

.rate-limit-info {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
  margin-top: var(--space-md);
  margin-bottom: 0;
}

/* Alerts */
.alert {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  font-size: 0.9375rem;
}

.alert-success {
  background: var(--color-success-subtle, #e8f5e9);
  color: var(--color-success, #2e7d32);
  border: 1px solid var(--color-success, #2e7d32);
}

.alert-error {
  background: var(--color-error-subtle, #fbe9e7);
  color: var(--color-error, #c62828);
  border: 1px solid var(--color-error, #c62828);
}

.auth-footer {
  text-align: center;
}

.auth-footer p {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-sm);
}

.auth-footer p:last-child {
  margin-bottom: 0;
}

.auth-footer a {
  color: var(--color-ai);
  font-weight: 500;
}

/* ========================================
   INFO SECTION
   ======================================== */
.auth-info-section {
  position: relative;
  padding: var(--space-ma-xl);
  padding-left: var(--space-ma-lg);
  border-left: 1px solid var(--color-border-light);
}

.info-content {
  position: relative;
  z-index: 1;
}

.auth-info-section h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 400;
  line-height: 1.2;
  margin-bottom: var(--space-ma);
  color: var(--color-sumi);
}

.info-description {
  font-size: 1.125rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-ma);
  max-width: 400px;
}

.feature-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
}

.feature-marker {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-ai);
  flex-shrink: 0;
}

/* Seasonal accent */
.seasonal-accent {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle at center, var(--color-seasonal) 0%, transparent 70%);
  opacity: 0.15;
  pointer-events: none;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 968px) {
  .auth-container {
    grid-template-columns: 1fr;
    gap: var(--space-ma);
    padding: var(--space-ma) var(--space-md);
  }

  .auth-form-section {
    max-width: 100%;
  }

  .auth-info-section {
    display: none;
  }

  .vertical-text {
    display: none;
  }

  .enso-1 {
    width: 300px;
    height: 300px;
    top: -100px;
    right: -50px;
  }
}

@media (max-width: 480px) {
  .auth-header h1 {
    font-size: 2rem;
  }

  .auth-brand {
    font-size: 1.25rem;
  }

  .brand-enso {
    width: 24px;
    height: 24px;
  }

  .verification-card {
    padding: var(--space-lg);
  }
}
</style>
