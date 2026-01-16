<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <!-- Zen Navigation - 禅ナビ -->
    <nav v-if="authStore.isAuthenticated()" class="zen-nav">
      <div class="nav-container">
        <!-- Mobile Hamburger Menu (only visible on mobile) -->
        <button @click="toggleMobileSidebar" class="mobile-hamburger" aria-label="Navigation öffnen">
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </button>

        <!-- Brand - Minimal mark -->
        <router-link to="/" class="nav-brand" title="Zur Startseite">
          <div class="brand-mark">
            <div class="enso-mark"></div>
          </div>
          <span class="brand-text">obo</span>
        </router-link>

        <!-- Center Navigation - Horizontal links -->
        <div class="nav-center">
          <router-link to="/" class="nav-link" exact-active-class="active" title="Dashboard">
            <span class="nav-text">Dashboard</span>
          </router-link>
          <router-link to="/documents" class="nav-link" active-class="active" title="Dokumente verwalten">
            <span class="nav-text">Dokumente</span>
          </router-link>
          <router-link to="/templates" class="nav-link" active-class="active" title="Bewerbungsvorlagen">
            <span class="nav-text">Templates</span>
          </router-link>
          <router-link to="/applications" class="nav-link" active-class="active" title="Meine Bewerbungen">
            <span class="nav-text">Bewerbungen</span>
          </router-link>
          <router-link to="/timeline" class="nav-link" active-class="active" title="Aktivitäten-Timeline">
            <span class="nav-text">Timeline</span>
          </router-link>
          <router-link to="/ats" class="nav-link" active-class="active" title="ATS-Optimierung">
            <span class="nav-text">ATS</span>
          </router-link>
          <router-link to="/company-insights" class="nav-link nav-link-with-icon" active-class="active" title="Firmen-Insights">
            <svg class="nav-icon-mobile" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M18 20V10"/>
              <path d="M12 20V4"/>
              <path d="M6 20v-6"/>
            </svg>
            <span class="nav-text">Insights</span>
          </router-link>
          <router-link to="/new-application" class="nav-link nav-link-cta" active-class="active" title="Neue Bewerbung erstellen">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span class="nav-text">Neu</span>
          </router-link>
        </div>

        <!-- Actions - Subscription & Settings -->
        <div class="nav-actions">
          <!-- Subscription Display -->
          <router-link to="/subscription" class="subscription-display" title="Abo-Einstellungen">
            <span class="subscription-plan">{{ getPlanLabel() }}</span>
          </router-link>

          <!-- Theme Toggle -->
          <button @click="toggleTheme" class="nav-icon theme-toggle" :title="isDarkMode ? 'Heller Modus' : 'Dunkler Modus'">
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

    <!-- Mobile Sidebar - 禅モバイルサイドバー -->
    <div v-if="authStore.isAuthenticated()" class="mobile-sidebar" :class="{ 'sidebar-open': isSidebarOpen }">
      <!-- Sidebar Overlay -->
      <div class="sidebar-overlay" @click="closeMobileSidebar"></div>

      <!-- Sidebar Content -->
      <div class="sidebar-content">
        <!-- Sidebar Header -->
        <div class="sidebar-header">
          <div class="sidebar-brand">
            <div class="sidebar-enso"></div>
            <span>obo</span>
          </div>
          <button @click="closeMobileSidebar" class="sidebar-close" aria-label="Navigation schließen">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Sidebar Navigation -->
        <nav class="sidebar-nav">
          <router-link to="/" class="sidebar-link" exact-active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <span>Dashboard</span>
          </router-link>

          <router-link to="/documents" class="sidebar-link" active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <span>Dokumente</span>
          </router-link>

          <router-link to="/templates" class="sidebar-link" active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14.5 2 14.5 8 20.5 8"/>
            </svg>
            <span>Templates</span>
          </router-link>

          <router-link to="/applications" class="sidebar-link" active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <span>Bewerbungen</span>
          </router-link>

          <router-link to="/timeline" class="sidebar-link" active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <span>Timeline</span>
          </router-link>

          <router-link to="/ats" class="sidebar-link" active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 20V10"/>
              <path d="M18 20V4"/>
              <path d="M6 20v-4"/>
            </svg>
            <span>ATS-Optimierung</span>
          </router-link>

          <router-link to="/company-insights" class="sidebar-link" active-class="active" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M18 20V10"/>
              <path d="M12 20V4"/>
              <path d="M6 20v-6"/>
            </svg>
            <span>Firmen-Insights</span>
          </router-link>
        </nav>

        <!-- Sidebar Footer -->
        <div class="sidebar-footer">
          <router-link to="/subscription" class="sidebar-link" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <path d="M12 17h.01"/>
            </svg>
            <span>Abo ({{ getPlanLabel() }})</span>
          </router-link>

          <router-link to="/settings" class="sidebar-link" @click="closeMobileSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            <span>Einstellungen</span>
          </router-link>

          <button @click="logout" class="sidebar-link sidebar-logout">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>Abmelden</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="main-content" :class="{ 'with-nav': authStore.isAuthenticated() }">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Bottom Navigation - Mobile Only -->
    <nav v-if="authStore.isAuthenticated()" class="bottom-nav" aria-label="Mobile Navigation">
      <router-link to="/" class="bottom-nav-item" exact-active-class="active" title="Dashboard">
        <svg class="bottom-nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span class="bottom-nav-label">Start</span>
      </router-link>
      <router-link to="/applications" class="bottom-nav-item" active-class="active" title="Bewerbungen">
        <svg class="bottom-nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        <span class="bottom-nav-label">Bewerbungen</span>
      </router-link>
      <router-link to="/new-application" class="bottom-nav-item bottom-nav-cta" active-class="active" title="Neue Bewerbung">
        <div class="bottom-nav-cta-circle">
          <svg class="bottom-nav-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </div>
        <span class="bottom-nav-label">Neu</span>
      </router-link>
      <router-link to="/ats" class="bottom-nav-item" active-class="active" title="ATS-Optimierung">
        <svg class="bottom-nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 20V10"/>
          <path d="M18 20V4"/>
          <path d="M6 20v-4"/>
        </svg>
        <span class="bottom-nav-label">ATS</span>
      </router-link>
      <router-link to="/timeline" class="bottom-nav-item" active-class="active" title="Timeline">
        <svg class="bottom-nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        <span class="bottom-nav-label">Timeline</span>
      </router-link>
    </nav>

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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { authStore } from './store/auth'
import { useRouter } from 'vue-router'
import Toast from './components/Toast.vue'

const router = useRouter()
const toastRef = ref(null)
const isDarkMode = ref(false)
const isSidebarOpen = ref(false)
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

const getPlanLabel = () => {
  const subscription = authStore.user?.subscription
  if (!subscription) return 'Free'
  return subscription.plan?.charAt(0).toUpperCase() + subscription.plan?.slice(1) || 'Free'
}

// Mobile sidebar functions
const toggleMobileSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value

  // Disable body scroll when sidebar is open
  if (isSidebarOpen.value) {
    document.body.classList.add('sidebar-open')
  } else {
    document.body.classList.remove('sidebar-open')
  }
}

const closeMobileSidebar = () => {
  isSidebarOpen.value = false
  document.body.classList.remove('sidebar-open')
}

// Close sidebar on escape key
const handleEscapeKey = (event) => {
  if (event.key === 'Escape' && isSidebarOpen.value) {
    closeMobileSidebar()
  }
}

// Close sidebar on route change
const handleRouteChange = () => {
  if (isSidebarOpen.value) {
    closeMobileSidebar()
  }
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

  // Add keyboard listener for escape key
  document.addEventListener('keydown', handleEscapeKey)

  // Watch for route changes to close sidebar
  router.afterEach(handleRouteChange)
})

onUnmounted(() => {
  // Clean up event listeners
  document.removeEventListener('keydown', handleEscapeKey)
  document.body.classList.remove('sidebar-open')
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

/* ========================================
   MOBILE HAMBURGER MENU
   ======================================== */
.mobile-hamburger {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  cursor: pointer;
  gap: 4px;
  transition: all var(--transition-base);
}

.hamburger-line {
  width: 20px;
  height: 2px;
  background: var(--color-sumi);
  border-radius: 2px;
  transition: all var(--transition-base);
}

.mobile-hamburger:hover .hamburger-line {
  background: var(--color-ai);
}

/* Show hamburger only on mobile */
@media (max-width: 768px) {
  .mobile-hamburger {
    display: flex;
  }
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

/* Mobile icon for nav links */
.nav-link-with-icon {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.nav-icon-mobile {
  display: none;
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

.subscription-display {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all var(--transition-base);
}

.subscription-display:hover {
  background: var(--color-ai);
}

.subscription-display:hover .subscription-plan {
  color: var(--color-text-inverse);
}

.subscription-plan {
  font-size: 0.8125rem;
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

  .nav-icon-mobile {
    display: block;
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
}

@media (max-width: 480px) {
  .nav-actions {
    gap: var(--space-xs);
  }

  .nav-icon {
    width: 36px;
    height: 36px;
  }

  .subscription-display {
    padding: var(--space-xs) var(--space-sm);
    min-width: 0; /* Allow flex shrinking */
  }

  .subscription-plan {
    font-size: 0.75rem; /* Make subscription text smaller */
  }
}

@media (max-width: 375px) {
  .nav-container {
    padding: 0 var(--space-sm);
  }

  .nav-actions {
    gap: 2px;
  }

  .nav-icon {
    width: 32px;
    height: 32px;
  }

  .subscription-display {
    padding: var(--space-xs);
    min-width: 0;
  }

  .subscription-plan {
    font-size: 0.7rem;
    white-space: nowrap;
  }

  /* Ensure nav-actions remain visible and accessible on very small screens */
  .nav-actions {
    flex-shrink: 0;
    min-width: fit-content;
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

  /* Add padding for bottom nav */
  .main-content.with-nav {
    padding-bottom: 72px;
  }

  .zen-footer {
    padding-bottom: calc(var(--space-lg) + 72px);
  }
}

/* ========================================
   BOTTOM NAVIGATION - Mobile Only
   ======================================== */
.bottom-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: var(--z-nav);
  background: var(--color-washi);
  border-top: 1px solid var(--color-border-light);
  padding: var(--space-xs) 0;
  padding-bottom: calc(var(--space-xs) + env(safe-area-inset-bottom, 0px));
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

@media (max-width: 768px) {
  .bottom-nav {
    display: flex;
    justify-content: space-around;
    align-items: flex-end;
  }
}

.bottom-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-xs);
  text-decoration: none;
  color: var(--color-text-tertiary);
  transition: color var(--transition-base);
  min-width: 60px;
}

.bottom-nav-item:hover,
.bottom-nav-item.active {
  color: var(--color-ai);
}

.bottom-nav-icon {
  flex-shrink: 0;
  transition: transform var(--transition-base);
}

.bottom-nav-item.active .bottom-nav-icon {
  transform: scale(1.1);
}

.bottom-nav-label {
  font-size: 0.625rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  white-space: nowrap;
}

/* CTA Button (Neu) - Elevated */
.bottom-nav-cta {
  position: relative;
  margin-top: -12px;
}

.bottom-nav-cta-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--color-ai);
  border-radius: 50%;
  color: var(--color-washi);
  box-shadow: 0 2px 8px rgba(61, 90, 108, 0.3);
  transition: all var(--transition-base);
}

.bottom-nav-cta:hover .bottom-nav-cta-circle {
  background: var(--color-ai-light);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(61, 90, 108, 0.4);
}

.bottom-nav-cta.active .bottom-nav-cta-circle {
  background: var(--color-sumi);
}

.bottom-nav-cta .bottom-nav-icon {
  color: var(--color-washi);
}

.bottom-nav-cta .bottom-nav-label {
  margin-top: 4px;
}

/* ========================================
   MOBILE SIDEBAR - 禅モバイルサイドバー
   ======================================== */
.mobile-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  display: none;
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--transition-base);
}

.mobile-sidebar.sidebar-open {
  display: block;
  pointer-events: auto;
  opacity: 1;
}

.sidebar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  transition: opacity var(--transition-base);
}

.sidebar-content {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  max-width: 85vw;
  background: var(--color-washi);
  border-right: 1px solid var(--color-border-light);
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  transform: translateX(-100%);
  transition: transform var(--transition-base);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-open .sidebar-content {
  transform: translateX(0);
}

/* Sidebar Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-washi-warm);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.sidebar-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 2.5px 2px 2px;
  opacity: 0.8;
}

.sidebar-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.sidebar-close:hover {
  background: var(--color-washi-aged);
  color: var(--color-text-primary);
}

/* Sidebar Navigation */
.sidebar-nav {
  flex: 1;
  padding: var(--space-sm) 0;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  text-decoration: none;
  color: var(--color-text-tertiary);
  font-weight: 400;
  transition: all var(--transition-base);
  border: none;
  background: transparent;
  width: 100%;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.9375rem;
}

.sidebar-link:hover {
  background: var(--color-washi-aged);
  color: var(--color-text-primary);
}

.sidebar-link.active {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  font-weight: 500;
}

.sidebar-link.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--color-ai);
  border-radius: 0 2px 2px 0;
}

.sidebar-link svg {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

/* Sidebar Footer */
.sidebar-footer {
  border-top: 1px solid var(--color-border-light);
  padding: var(--space-sm) 0;
  background: var(--color-washi-warm);
}

.sidebar-logout:hover {
  background: var(--color-error-light);
  color: var(--color-error);
}

/* Prevent body scroll when sidebar is open */
:global(body.sidebar-open) {
  overflow: hidden;
}

/* Show sidebar only on mobile */
@media (min-width: 769px) {
  .mobile-sidebar {
    display: none !important;
  }
}
</style>
