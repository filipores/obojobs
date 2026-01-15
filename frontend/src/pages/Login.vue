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
      <div class="vertical-text">書</div>
    </div>

    <!-- Main Content - Asymmetric layout -->
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
          <h1>Willkommen</h1>
          <p>Melden Sie sich an, um fortzufahren</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="form-group">
            <label class="form-label required" for="email">E-Mail</label>
            <input
              id="email"
              v-model="email"
              type="email"
              class="form-input"
              :class="{ 'input-error': emailError, 'input-valid': emailTouched && !emailError && email }"
              placeholder="ihre@email.de"
              required
              aria-required="true"
              aria-invalid="emailError ? 'true' : 'false'"
              :aria-describedby="emailError ? 'email-error' : undefined"
              autocomplete="email"
              @blur="emailTouched = true"
              @input="emailTouched = true"
            />
            <p v-if="emailError" id="email-error" class="field-error" role="alert">
              {{ emailError }}
            </p>
          </div>

          <div class="form-group">
            <label class="form-label required" for="password">Passwort</label>
            <div class="password-input-wrapper">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': passwordError, 'input-valid': passwordTouched && !passwordError && password }"
                placeholder="••••••••"
                required
                aria-required="true"
                aria-invalid="passwordError ? 'true' : 'false'"
                :aria-describedby="passwordError ? 'password-error' : undefined"
                autocomplete="current-password"
                @blur="passwordTouched = true"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
                :title="showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'"
              >
                <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </button>
            </div>
            <p v-if="passwordError" id="password-error" class="field-error" role="alert">
              {{ passwordError }}
            </p>
            <div class="forgot-password-link">
              <router-link to="/forgot-password">Passwort vergessen?</router-link>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="alert alert-error">
            {{ error }}
          </div>

          <!-- Submit Button -->
          <button type="submit" class="zen-btn zen-btn-filled zen-btn-lg" :disabled="loading">
            <span v-if="!loading">Anmelden</span>
            <span v-else>Wird angemeldet...</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="ink-stroke"></div>

        <!-- Footer -->
        <div class="auth-footer">
          <p>Noch kein Konto? <router-link to="/register">Registrieren</router-link></p>
        </div>
      </div>

      <!-- Info Section - Offset for asymmetry -->
      <div class="auth-info-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="info-content">
          <h2>KI-gestützte<br/>Bewerbungen</h2>
          <p class="info-description">
            Erstellen Sie professionelle, personalisierte Anschreiben
            in Sekunden mit Künstlicher Intelligenz.
          </p>

          <ul class="feature-list">
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Automatische Anschreiben-Generierung</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Chrome Extension für 1-Klick Bewerbungen</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>Template-Verwaltung</span>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../store/auth'

const router = useRouter()
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const loading = ref(false)
const isDarkMode = ref(false)

// Validation states
const emailTouched = ref(false)
const passwordTouched = ref(false)

// Email validation
const isValidEmail = (emailStr) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(emailStr)
}

const emailError = computed(() => {
  if (!emailTouched.value) return ''
  if (!email.value) return 'E-Mail ist erforderlich'
  if (!isValidEmail(email.value)) return 'Bitte geben Sie eine gültige E-Mail-Adresse ein'
  return ''
})

const passwordError = computed(() => {
  if (!passwordTouched.value) return ''
  if (!password.value) return 'Passwort ist erforderlich'
  return ''
})

// Form is valid when email format is correct and password is provided
const _isFormValid = computed(() => {
  return email.value && isValidEmail(email.value) && password.value
})

const THEME_KEY = 'obojobs-theme'

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

const handleLogin = async () => {
  try {
    loading.value = true
    error.value = ''
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.error || 'Login fehlgeschlagen. Bitte überprüfen Sie Ihre Anmeldedaten.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initTheme()
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
  max-width: 420px;
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

.auth-form {
  margin-bottom: var(--space-ma);
}

.auth-form .form-group {
  margin-bottom: var(--space-lg);
}

.form-label.required::after {
  content: ' *';
  color: #b45050;
}

.auth-form .zen-btn {
  width: 100%;
  margin-top: var(--space-md);
}

.password-input-wrapper {
  position: relative;
}

.password-input-wrapper .form-input {
  padding-right: 48px;
}

.password-toggle {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: color var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.password-toggle:hover {
  color: var(--color-ai);
}

.forgot-password-link {
  text-align: right;
  margin-top: var(--space-sm);
}

.forgot-password-link a {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  transition: color var(--transition-base);
}

.forgot-password-link a:hover {
  color: var(--color-ai);
}

.auth-footer {
  text-align: center;
}

.auth-footer p {
  color: var(--color-text-tertiary);
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

/* Seasonal accent - subtle color touch */
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
}

/* ========================================
   INLINE VALIDATION
   ======================================== */
.form-input.input-error {
  border-color: #b45050;
  background-color: rgba(180, 80, 80, 0.05);
}

.form-input.input-error:focus {
  border-color: #b45050;
  box-shadow: 0 0 0 3px rgba(180, 80, 80, 0.1);
}

.form-input.input-valid {
  border-color: #4a7c59;
  background-color: rgba(74, 124, 89, 0.03);
}

.form-input.input-valid:focus {
  border-color: #4a7c59;
  box-shadow: 0 0 0 3px rgba(74, 124, 89, 0.1);
}

.field-error {
  color: #b45050;
  font-size: 0.8125rem;
  margin-top: var(--space-xs);
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.field-error::before {
  content: '!';
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  font-size: 0.6875rem;
  font-weight: 600;
  background: #b45050;
  color: white;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
