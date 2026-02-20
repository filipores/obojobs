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
      <LanguageSwitcher v-if="false" />
    </div>

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
          <h1>{{ $t('login.title') }}</h1>
          <p>{{ $t('login.subtitle') }}</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="form-group">
            <label class="form-label required" for="email">{{ $t('auth.email') }}</label>
            <input
              id="email"
              v-model="email"
              type="email"
              class="form-input"
              :class="{ 'input-error': emailError, 'input-valid': emailTouched && !emailError && email }"
              :placeholder="$t('auth.emailPlaceholder')"
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
            <label class="form-label required" for="password">{{ $t('auth.password') }}</label>
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
                :title="showPassword ? $t('auth.hidePassword') : $t('auth.showPassword')"
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
              <router-link to="/forgot-password">{{ $t('auth.forgotPassword') }}</router-link>
            </div>
          </div>

          <!-- Email Not Verified Message -->
          <div v-if="emailNotVerified" class="alert alert-warning">
            <p>{{ $t('login.emailNotVerified') }}</p>
            <button
              type="button"
              class="resend-verification-btn"
              :disabled="resendLoading || resendCooldown > 0"
              @click="handleResendVerification"
            >
              <span v-if="resendLoading">{{ $t('emailVerification.resending') }}</span>
              <span v-else-if="resendCooldown > 0">{{ $t('emailVerification.resendCountdown', { time: resendCooldown + 's' }) }}</span>
              <span v-else>{{ $t('login.resendVerification') }}</span>
            </button>
            <p v-if="resendSuccess" class="resend-success">{{ $t('emailVerification.resendSuccess') }}</p>
          </div>

          <!-- Error Message -->
          <div v-if="error && !emailNotVerified" class="alert alert-error">
            {{ error }}
          </div>

          <!-- Submit Button -->
          <button type="submit" class="zen-btn zen-btn-filled zen-btn-lg" :disabled="loading">
            <span v-if="!loading">{{ $t('auth.login') }}</span>
            <span v-else>{{ $t('auth.loggingIn') }}</span>
          </button>

          <!-- OAuth Divider -->
          <div class="oauth-divider">
            <span>{{ $t('auth.or') }}</span>
          </div>

          <!-- Google Sign In Button -->
          <button
            type="button"
            class="google-btn"
            :disabled="googleLoading"
            @click="handleGoogleLogin"
          >
            <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span v-if="!googleLoading">{{ $t('auth.continueWithGoogle') }}</span>
            <span v-else>{{ $t('auth.loading') }}</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="ink-stroke"></div>

        <!-- Footer -->
        <div class="auth-footer">
          <p>{{ $t('auth.noAccount') }} <router-link to="/register">{{ $t('auth.register') }}</router-link></p>
        </div>
      </div>

      <!-- Info Section - Offset for asymmetry -->
      <div class="auth-info-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="info-content">
          <h2>{{ $t('login.aiPoweredTitleLine1') }}<br>{{ $t('login.aiPoweredTitleLine2') }}</h2>
          <p class="info-description">
            {{ $t('login.aiPoweredDescription') }}
          </p>

          <ul class="feature-list">
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>{{ $t('login.featureAutoGeneration') }}</span>
            </li>
            <li class="feature-item stagger-item">
              <span class="feature-marker"></span>
              <span>{{ $t('login.featureChromeExtension') }}</span>
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
import { useI18n } from 'vue-i18n'
import { authStore } from '../stores/auth'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import api from '../api/client'

const { t, locale } = useI18n()

const router = useRouter()
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const loading = ref(false)
const googleLoading = ref(false)
const isDarkMode = ref(false)
const emailNotVerified = ref(false)
const resendLoading = ref(false)
const resendSuccess = ref(false)
const resendCooldown = ref(0)

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
  if (!email.value) return t('auth.emailRequired')
  if (!isValidEmail(email.value)) return t('auth.emailInvalid')
  return ''
})

const passwordError = computed(() => {
  if (!passwordTouched.value) return ''
  if (!password.value) return t('auth.passwordRequired')
  return ''
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
  // Mark fields as touched to trigger validation display
  emailTouched.value = true
  passwordTouched.value = true

  // Validate directly (don't rely on computed reactivity within same tick)
  const hasEmailError = !email.value || !isValidEmail(email.value)
  const hasPasswordError = !password.value

  if (hasEmailError || hasPasswordError) {
    // Focus first invalid field for better UX
    if (hasEmailError) {
      document.getElementById('email')?.focus()
    } else if (hasPasswordError) {
      document.getElementById('password')?.focus()
    }
    return // Don't submit if validation fails
  }

  try {
    loading.value = true
    error.value = ''
    await authStore.login(email.value, password.value)

    // I18N-002: Bidirectional language sync after login
    const userLanguage = authStore.user?.language
    const currentLocale = locale.value

    if (userLanguage && userLanguage !== currentLocale) {
      // Backend has different language - sync to frontend (I18N-002-BUG-001)
      locale.value = userLanguage
      localStorage.setItem('obojobs-locale', userLanguage)
    } else if (!userLanguage || userLanguage !== currentLocale) {
      // Sync frontend language to backend (I18N-002-BUG-002)
      try {
        await api.silent.put('/auth/language', { language: currentLocale })
      } catch {
        // Ignore error - language sync is not critical
      }
    }

    router.push('/')
  } catch (e) {
    if (e.response?.data?.email_not_verified) {
      emailNotVerified.value = true
      error.value = ''
      resendSuccess.value = false
    } else {
      emailNotVerified.value = false
      error.value = e.response?.data?.error || t('auth.loginFailed')
    }
  } finally {
    loading.value = false
  }
}

const handleResendVerification = async () => {
  try {
    resendLoading.value = true
    resendSuccess.value = false
    await api.silent.post('/auth/resend-verification', { email: email.value })
    resendSuccess.value = true
    // Start 60-second cooldown
    resendCooldown.value = 60
    const interval = setInterval(() => {
      resendCooldown.value--
      if (resendCooldown.value <= 0) {
        clearInterval(interval)
      }
    }, 1000)
  } catch {
    // Silently handle - the endpoint always returns 200
  } finally {
    resendLoading.value = false
  }
}

const handleGoogleLogin = async () => {
  try {
    googleLoading.value = true
    error.value = ''

    // Load Google Identity Services library dynamically
    if (!window.google?.accounts?.id) {
      await loadGoogleScript()
    }

    // Initialize Google Sign-In
    window.google.accounts.id.initialize({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      callback: handleGoogleCallback,
      auto_select: false,
      cancel_on_tap_outside: true
    })

    // Show the Google One Tap prompt
    window.google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        // Fallback to button click flow
        window.google.accounts.id.renderButton(
          document.createElement('div'),
          { theme: 'outline', size: 'large' }
        )
        // Trigger the popup
        window.google.accounts.oauth2.initCodeClient({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
          scope: 'email profile',
          ux_mode: 'popup',
          callback: () => {}
        })
      }
    })
  } catch (e) {
    console.error('Google login error:', e)
    error.value = t('auth.googleLoginFailed')
    googleLoading.value = false
  }
}

const handleGoogleCallback = async (response) => {
  try {
    await authStore.loginWithGoogle(response.credential)

    // I18N-002: Bidirectional language sync after login
    const userLanguage = authStore.user?.language
    const currentLocale = locale.value

    if (userLanguage && userLanguage !== currentLocale) {
      locale.value = userLanguage
      localStorage.setItem('obojobs-locale', userLanguage)
    } else if (!userLanguage || userLanguage !== currentLocale) {
      try {
        await api.silent.put('/auth/language', { language: currentLocale })
      } catch {
        // Ignore error - language sync is not critical
      }
    }

    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.error || t('auth.googleLoginFailed')
  } finally {
    googleLoading.value = false
  }
}

const loadGoogleScript = () => {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
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

/* ========================================
   OAUTH DIVIDER & GOOGLE BUTTON
   ======================================== */
.oauth-divider {
  display: flex;
  align-items: center;
  margin: var(--space-lg) 0;
  gap: var(--space-md);
}

.oauth-divider::before,
.oauth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border-light);
}

.oauth-divider span {
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.google-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.google-btn:hover:not(:disabled) {
  background: var(--color-bg-subtle);
  border-color: var(--color-border);
  box-shadow: var(--shadow-paper);
}

.google-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.google-icon {
  flex-shrink: 0;
}

/* ========================================
   EMAIL NOT VERIFIED WARNING
   ======================================== */
.alert-warning {
  background: rgba(200, 150, 50, 0.08);
  border: 1px solid rgba(200, 150, 50, 0.3);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-md);
  color: var(--color-text-primary);
}

.alert-warning p {
  margin: 0 0 var(--space-sm) 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.resend-verification-btn {
  display: inline-flex;
  align-items: center;
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
}

.resend-verification-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.resend-verification-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.resend-success {
  color: #4a7c59;
  font-size: 0.8125rem;
  margin-top: var(--space-xs);
}
</style>
