<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <!-- Zen Navigation - 禅ナビ -->
    <nav v-if="authStore.isAuthenticated()" class="zen-nav">
      <div class="nav-container">
        <!-- Brand - Minimal mark -->
        <router-link to="/" class="nav-brand">
          <div class="brand-mark">
            <div class="enso-mark"></div>
          </div>
          <span class="brand-text">obo</span>
        </router-link>

        <!-- Center Navigation - Horizontal links -->
        <div class="nav-center">
          <router-link to="/" class="nav-link" exact-active-class="active">
            <span class="nav-text">Dashboard</span>
          </router-link>
          <router-link to="/documents" class="nav-link" active-class="active">
            <span class="nav-text">Dokumente</span>
          </router-link>
          <router-link to="/templates" class="nav-link" active-class="active">
            <span class="nav-text">Templates</span>
          </router-link>
          <router-link to="/applications" class="nav-link" active-class="active">
            <span class="nav-text">Bewerbungen</span>
          </router-link>
          <router-link to="/new-application" class="nav-link nav-link-cta" active-class="active">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span class="nav-text">Neu</span>
          </router-link>
        </div>

        <!-- Actions - Credits & Settings -->
        <div class="nav-actions">
          <!-- Credits Display -->
          <router-link to="/buy-credits" class="credits-display">
            <span class="credits-number">{{ authStore.user?.credits_remaining || 0 }}</span>
            <span class="credits-label">Credits</span>
          </router-link>

          <!-- Theme Toggle -->
          <button @click="toggleTheme" class="nav-icon theme-toggle" :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
            <!-- Sun icon (show when dark mode is active) -->
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
            <!-- Moon icon (show when light mode is active) -->
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>

          <!-- Settings -->
          <router-link to="/settings" class="nav-icon" title="Einstellungen">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </router-link>

          <!-- Logout -->
          <button @click="logout" class="nav-icon logout" title="Abmelden">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Ink stroke under nav -->
      <div class="nav-ink-stroke"></div>
    </nav>

    <!-- Main Content -->
    <main class="main-content" :class="{ 'with-nav': authStore.isAuthenticated() }">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Footer -->
    <footer class="zen-footer">
      <div class="footer-container">
        <div class="footer-brand">
          <div class="footer-enso"></div>
          <span>obo</span>
        </div>
        <div class="footer-links">
          <router-link to="/impressum">Impressum</router-link>
          <span class="footer-divider">|</span>
          <router-link to="/datenschutz">Datenschutz</router-link>
        </div>
        <div class="footer-copyright">
          &copy; {{ currentYear }} obo
        </div>
      </div>
    </footer>

    <!-- Toast Notifications -->
    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { authStore } from './store/auth'
import { useRouter } from 'vue-router'
import Toast from './components/Toast.vue'

const router = useRouter()
const toastRef = ref(null)
const isDarkMode = ref(false)
const currentYear = computed(() => new Date().getFullYear())

const THEME_KEY = 'obojobs-theme'

// Initialize theme from localStorage or system preference
const initTheme = () => {
  const savedTheme = localStorage.getItem(THEME_KEY)

  if (savedTheme) {
    // User has a saved preference
    isDarkMode.value = savedTheme === 'dark'
  } else {
    // Fall back to system preference
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  applyTheme()
}

// Apply theme to document root
const applyTheme = () => {
  const root = document.documentElement

  if (isDarkMode.value) {
    root.classList.add('dark-mode')
    root.classList.remove('light-mode')
  } else {
    root.classList.add('light-mode')
    root.classList.remove('dark-mode')
  }
}

// Toggle theme and save to localStorage
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem(THEME_KEY, isDarkMode.value ? 'dark' : 'light')
  applyTheme()
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

// Watch for system preference changes
const watchSystemTheme = () => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  mediaQuery.addEventListener('change', (e) => {
    // Only apply system preference if user hasn't set a manual preference
    if (!localStorage.getItem(THEME_KEY)) {
      isDarkMode.value = e.matches
      applyTheme()
    }
  })
}

onMounted(() => {
  // Make toast globally available
  if (toastRef.value) {
    window.$toast = toastRef.value.add
  }

  // Initialize theme
  initTheme()
  watchSystemTheme()
})
</script>

<style scoped>
/* ========================================
   ZEN NAVIGATION - 禅ナビ
   ======================================== */
.zen-nav {
  position: sticky;
  top: 0;
  z-index: var(--z-nav);
  background: var(--color-washi);
}

.nav-container {
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: 0 var(--space-ma);
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-ma);
}

/* Brand */
.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  color: var(--color-sumi);
}

.brand-mark {
  position: relative;
  width: 32px;
  height: 32px;
}

.enso-mark {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 2.5px 2px 2px;
  opacity: 0.8;
  transition: all var(--transition-base);
}

.nav-brand:hover .enso-mark {
  opacity: 1;
  transform: rotate(90deg);
}

.brand-text {
  font-family: var(--font-display);
  font-size: 1.375rem;
  font-weight: 500;
  letter-spacing: -0.02em;
}

/* Center Navigation */
.nav-center {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.nav-link {
  position: relative;
  padding: var(--space-sm) var(--space-md);
  text-decoration: none;
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
  font-weight: 400;
  letter-spacing: var(--tracking-normal);
  transition: color var(--transition-base);
}

.nav-link-cta {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  background: var(--color-ai);
  color: var(--color-washi) !important;
  border-radius: var(--radius-full);
  padding: var(--space-xs) var(--space-md);
  margin-left: var(--space-sm);
  font-weight: 500;
  transition: all var(--transition-base);
}

.nav-link-cta:hover {
  background: var(--color-ai-light);
  transform: translateY(-1px);
}

.nav-link-cta.active {
  background: var(--color-sumi);
}

.nav-link-cta svg {
  flex-shrink: 0;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 1.5px;
  background: var(--color-sumi);
  transition: all var(--transition-base);
  transform: translateX(-50%);
}

.nav-link:hover {
  color: var(--color-text-primary);
}

.nav-link:hover::after {
  width: 24px;
}

.nav-link.active {
  color: var(--color-text-primary);
  font-weight: 500;
}

.nav-link.active::after {
  width: 24px;
  background: var(--color-ai);
}

/* Actions */
.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.credits-display {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all var(--transition-base);
}

.credits-display:hover {
  background: var(--color-ai);
}

.credits-display:hover .credits-number,
.credits-display:hover .credits-label {
  color: var(--color-text-inverse);
}

.credits-number {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-ai);
  transition: color var(--transition-base);
}

.credits-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--color-ai);
  transition: color var(--transition-base);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-base);
  text-decoration: none;
}

.nav-icon:hover {
  background: var(--color-washi-aged);
  color: var(--color-text-primary);
}

.nav-icon.logout:hover {
  background: var(--color-error-light);
  color: var(--color-error);
}

/* Theme Toggle */
.theme-toggle {
  position: relative;
}

.theme-toggle svg {
  transition: transform var(--transition-base), opacity var(--transition-base);
}

.theme-toggle:hover svg {
  transform: rotate(15deg);
}

.theme-toggle:hover {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

/* Ink stroke under nav */
.nav-ink-stroke {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--color-sand) 15%,
    var(--color-stone) 50%,
    var(--color-sand) 85%,
    transparent 100%
  );
}

/* ========================================
   MAIN CONTENT
   ======================================== */
.main-content {
  min-height: 100vh;
}

.main-content.with-nav {
  min-height: calc(100vh - 73px);
}

/* Page transitions */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--transition-base), transform var(--transition-base);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .nav-container {
    padding: 0 var(--space-md);
    gap: var(--space-md);
  }

  .nav-center {
    gap: 0;
  }

  .nav-link {
    padding: var(--space-sm);
    font-size: 0.8125rem;
  }

  .nav-text {
    display: none;
  }

  .nav-link-cta .nav-text {
    display: inline;
  }

  .nav-link-cta {
    padding: var(--space-xs) var(--space-sm);
  }

  .brand-text {
    display: none;
  }

  .credits-label {
    display: none;
  }
}

@media (max-width: 480px) {
  .nav-actions {
    gap: var(--space-sm);
  }

  .nav-icon {
    width: 36px;
    height: 36px;
  }

  .credits-display {
    padding: var(--space-xs) var(--space-sm);
  }
}

/* ========================================
   FOOTER - 禅フッター
   ======================================== */
.zen-footer {
  background: var(--color-washi-warm);
  border-top: 1px solid var(--color-border-light);
  padding: var(--space-lg) 0;
  margin-top: auto;
}

.footer-container {
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: 0 var(--space-ma);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--color-text-tertiary);
}

.footer-enso {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1.5px solid var(--color-text-ghost);
  border-width: 1.5px 2px 1.5px 1.5px;
  opacity: 0.6;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.footer-links a {
  color: var(--color-text-tertiary);
  text-decoration: none;
  font-size: 0.875rem;
  transition: color var(--transition-base);
}

.footer-links a:hover {
  color: var(--color-ai);
}

.footer-divider {
  color: var(--color-text-ghost);
  font-size: 0.75rem;
}

.footer-copyright {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
}

@media (max-width: 768px) {
  .footer-container {
    flex-direction: column;
    text-align: center;
    gap: var(--space-sm);
  }

  .footer-brand {
    order: 1;
  }

  .footer-links {
    order: 2;
  }

  .footer-copyright {
    order: 3;
  }
}
</style>
