<template>
  <div class="auth-page">
    <!-- Floating Controls - Theme Toggle & Language Switcher -->
    <div class="floating-controls">
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
      <LanguageSwitcher />
    </div>

    <!-- Decorative Elements -->
    <div class="auth-decoration">
      <div class="enso-decoration enso-1"></div>
      <div class="enso-decoration enso-2"></div>
      <div class="vertical-text">鍵</div>
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
          <h1>{{ $t('forgotPassword.title') }}</h1>
          <p>{{ $t('forgotPassword.subtitle') }}</p>
        </div>

        <!-- Success Card -->
        <div v-if="submitted" class="success-card zen-card">
          <div class="success-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <h3>{{ $t('forgotPassword.successTitle') }}</h3>
          <p class="success-message">{{ $t('forgotPassword.successMessageBefore') }} <strong>{{ email }}</strong> {{ $t('forgotPassword.successMessageAfter') }}</p>
          <p class="instructions">
            {{ $t('forgotPassword.successInstructions') }}
          </p>
          <router-link to="/login" class="zen-btn zen-btn-filled">
            {{ $t('forgotPassword.backToLogin') }}
          </router-link>
        </div>

        <!-- Form -->
        <form v-else @submit.prevent="handleSubmit" class="auth-form">
          <div class="form-group">
            <label class="form-label" for="email">{{ $t('forgotPassword.emailLabel') }}</label>
            <input
              id="email"
              v-model="email"
              type="email"
              class="form-input"
              :placeholder="$t('forgotPassword.emailPlaceholder')"
              required
              autocomplete="email"
            />
          </div>

          <!-- Error Message -->
          <div v-if="error" class="alert alert-error">
            {{ error }}
          </div>

          <!-- Submit Button -->
          <button type="submit" class="zen-btn zen-btn-filled zen-btn-lg" :disabled="loading">
            <span v-if="loading" class="btn-spinner"></span>
            {{ loading ? $t('forgotPassword.submitting') : $t('forgotPassword.submit') }}
          </button>
        </form>

        <!-- Divider -->
        <div class="ink-stroke"></div>

        <!-- Footer -->
        <div class="auth-footer">
          <p>{{ $t('forgotPassword.rememberPassword') }} <router-link to="/login">{{ $t('auth.login') }}</router-link></p>
        </div>
      </div>

      <!-- Info Section -->
      <div class="auth-info-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="info-content">
          <h2>{{ $t('forgotPassword.infoTitleLine1') }}<br/>{{ $t('forgotPassword.infoTitleLine2') }}</h2>
          <p class="info-description">
            {{ $t('forgotPassword.infoDescription') }}
          </p>

          <ul class="feature-list">
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>{{ $t('forgotPassword.featureSecureLink') }}</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>{{ $t('forgotPassword.featureLinkValidity') }}</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>{{ $t('forgotPassword.featureNewPassword') }}</span>
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
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api/client'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const { t } = useI18n()

const email = ref('')
const error = ref('')
const loading = ref(false)
const submitted = ref(false)
const isDarkMode = ref(false)

const THEME_KEY = 'obojobs-theme'

const initTheme = () => {
  const savedTheme = localStorage.getItem(THEME_KEY)
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark'
  } else {
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
}

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

const handleSubmit = async () => {
  try {
    loading.value = true
    error.value = ''

    await api.post('/auth/forgot-password', { email: email.value })
    submitted.value = true
  } catch (e) {
    // Only show error for non-200 responses that aren't rate limiting
    if (e.response?.status === 429) {
      error.value = t('forgotPassword.tooManyRequests')
    } else {
      // Backend always returns 200 to prevent email enumeration
      // so this case should rarely happen
      error.value = e.response?.data?.error || t('forgotPassword.genericError')
    }
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
   FLOATING CONTROLS
   ======================================== */
.floating-controls {
  position: fixed;
  top: var(--space-lg);
  right: var(--space-lg);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.theme-toggle-float {
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

.auth-form .zen-btn {
  width: 100%;
  margin-top: var(--space-md);
}

/* Success Card */
.success-card {
  text-align: center;
  padding: var(--space-ma-lg);
  margin-bottom: var(--space-ma);
}

.success-icon {
  color: var(--color-ai);
  margin-bottom: var(--space-lg);
}

.success-card h3 {
  font-size: 1.5rem;
  margin-bottom: var(--space-md);
}

.success-message {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-sm);
}

.success-message :deep(strong) {
  color: var(--color-sumi);
}

.instructions {
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

.success-card .zen-btn {
  display: inline-block;
  text-decoration: none;
}

/* Alerts */
.alert {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  font-size: 0.9375rem;
}

.alert-error {
  background: var(--color-error-subtle, #fbe9e7);
  color: var(--color-error, #c62828);
  border: 1px solid var(--color-error, #c62828);
}

/* Button Spinner */
.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: var(--space-sm);
  vertical-align: middle;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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

  .success-card {
    padding: var(--space-lg);
  }
}
</style>
