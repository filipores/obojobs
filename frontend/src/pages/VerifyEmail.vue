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
      <div class="vertical-text">認</div>
    </div>

    <!-- Main Content -->
    <div class="verify-container animate-fade-up">
      <!-- Brand -->
      <router-link to="/" class="auth-brand">
        <div class="brand-enso"></div>
        <span>obo</span>
      </router-link>

      <!-- Loading State -->
      <div v-if="loading" class="verify-card zen-card">
        <div class="verify-icon loading-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10" stroke-dasharray="40" stroke-dashoffset="10">
              <animateTransform
                attributeName="transform"
                type="rotate"
                from="0 12 12"
                to="360 12 12"
                dur="1s"
                repeatCount="indefinite"
              />
            </circle>
          </svg>
        </div>
        <h2>E-Mail wird verifiziert...</h2>
        <p>Bitte warte einen Moment.</p>
      </div>

      <!-- Success State -->
      <div v-else-if="success" class="verify-card zen-card">
        <div class="verify-icon success-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <h2>E-Mail erfolgreich verifiziert!</h2>
        <p>Dein Konto ist jetzt vollständig aktiviert. Du wirst in {{ formattedRedirectCountdown }} zum Dashboard weitergeleitet.</p>
        <router-link to="/" class="zen-btn zen-btn-filled zen-btn-lg">
          Zum Dashboard
        </router-link>
      </div>

      <!-- Error State -->
      <div v-else class="verify-card zen-card">
        <div class="verify-icon error-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h2>Verifizierung fehlgeschlagen</h2>
        <p class="error-message">{{ error }}</p>

        <div class="error-actions">
          <router-link to="/email-verification" class="zen-btn zen-btn-filled">
            Neuen Link anfordern
          </router-link>
          <router-link to="/login" class="zen-btn">
            Zum Login
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import { authStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const success = ref(false)
const error = ref('')
const redirectSeconds = ref(5)
const isDarkMode = ref(false)

let redirectInterval = null

const THEME_KEY = 'obojobs-theme'

// Format countdown as "X Min Y Sek" when > 60s, otherwise just "X Sekunden"
const formattedRedirectCountdown = computed(() => {
  const seconds = redirectSeconds.value
  if (seconds > 60) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes} Min ${remainingSeconds} Sek`
  }
  return `${seconds} Sekunden`
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

const startRedirectCountdown = () => {
  redirectInterval = setInterval(() => {
    redirectSeconds.value--
    if (redirectSeconds.value <= 0) {
      clearInterval(redirectInterval)
      router.push('/')
    }
  }, 1000)
}

const verifyEmail = async () => {
  const token = route.query.token

  if (!token) {
    loading.value = false
    error.value = 'Kein Verifizierungs-Token gefunden. Bitte verwende den Link aus deiner E-Mail.'
    return
  }

  try {
    await api.post('/auth/verify-email', { token })

    success.value = true

    // Update user in auth store if logged in
    if (authStore.isAuthenticated()) {
      await authStore.fetchUser()
    }

    // Clear pending verification email
    localStorage.removeItem('pendingVerificationEmail')

    // Start countdown and redirect
    startRedirectCountdown()
  } catch (e) {
    const errorCode = e.response?.data?.error
    if (errorCode === 'Bestätigungstoken ist abgelaufen') {
      error.value = 'Der Verifizierungs-Link ist abgelaufen. Bitte fordere einen neuen Link an.'
    } else if (errorCode === 'Ungültiger Bestätigungstoken') {
      error.value = 'Der Verifizierungs-Link ist ungültig. Bitte fordere einen neuen Link an.'
    } else if (errorCode === 'E-Mail ist bereits bestätigt') {
      error.value = 'Deine E-Mail-Adresse wurde bereits verifiziert. Du kannst dich anmelden.'
    } else {
      error.value = errorCode || 'Ein unbekannter Fehler ist aufgetreten. Bitte versuche es erneut.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initTheme()
  verifyEmail()
})

onUnmounted(() => {
  if (redirectInterval) {
    clearInterval(redirectInterval)
  }
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--color-washi);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
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
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
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
   VERIFY CONTAINER
   ======================================== */
.verify-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  padding: var(--space-ma);
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
  margin-bottom: var(--space-ma);
}

.brand-enso {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 2.5px 2px 2px;
  opacity: 0.8;
}

/* ========================================
   VERIFY CARD
   ======================================== */
.verify-card {
  text-align: center;
  padding: var(--space-ma-xl);
}

.verify-icon {
  margin-bottom: var(--space-lg);
}

.loading-icon {
  color: var(--color-ai);
}

.success-icon {
  color: var(--color-success, #4CAF50);
}

.error-icon {
  color: var(--color-error, #c62828);
}

.verify-card h2 {
  font-size: 1.75rem;
  font-weight: 400;
  margin-bottom: var(--space-md);
}

.verify-card p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

.error-message {
  color: var(--color-text-secondary);
}

.error-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.error-actions .zen-btn {
  width: 100%;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 480px) {
  .verify-container {
    padding: var(--space-md);
  }

  .verify-card {
    padding: var(--space-lg);
  }

  .verify-card h2 {
    font-size: 1.5rem;
  }

  .vertical-text {
    display: none;
  }
}
</style>
