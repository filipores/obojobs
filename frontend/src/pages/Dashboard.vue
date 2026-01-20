<template>
  <div class="dashboard">
    <!-- Email Verification Banner - Full version -->
    <div v-if="showFullBanner" class="verification-banner">
      <div class="container">
        <div class="banner-content">
          <div class="banner-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <div class="banner-text">
            <strong>E-Mail-Adresse nicht verifiziert</strong>
            <span>Bitte verifizieren Sie Ihre E-Mail-Adresse, um alle Funktionen nutzen zu können.</span>
          </div>
          <router-link to="/email-verification" class="zen-btn zen-btn-sm">
            Jetzt verifizieren
          </router-link>
          <button @click="dismissBanner" class="banner-dismiss" aria-label="Banner schließen">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Email Verification Banner - Compact version (after dismissing full banner) -->
    <div v-else-if="showCompactBanner" class="verification-banner-compact">
      <div class="container">
        <router-link to="/email-verification" class="compact-banner-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
          <span>E-Mail noch nicht verifiziert</span>
          <svg class="arrow-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
      </div>
    </div>

    <!-- Skills Onboarding Hint -->
    <div v-if="showSkillsHint" class="skills-hint-banner">
      <div class="container">
        <div class="skills-hint-content">
          <div class="skills-hint-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="skills-hint-text">
            <strong>Skills fehlen noch</strong>
            <span>Laden Sie einen Lebenslauf hoch, um Skills automatisch zu extrahieren. Dies verbessert die Job-Analyse und Bewerbungserstellung.</span>
          </div>
          <router-link to="/documents" class="zen-btn zen-btn-ai zen-btn-sm">
            Lebenslauf hochladen
          </router-link>
          <button @click="dismissSkillsHint" class="skills-hint-dismiss" aria-label="Hinweis schliessen">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Hero Section with Ma (negative space) -->
    <section class="hero-section">
      <div class="container">
        <div class="hero-content animate-fade-up">
          <div class="hero-greeting">
            <span class="greeting-label">Guten Tag</span>
            <h1>Willkommen zurück</h1>
          </div>
          <p class="hero-subtitle">
            Verwalten Sie Ihre Bewerbungen mit Ruhe und Präzision
          </p>
        </div>

        <!-- Decorative enso -->
        <div class="hero-enso"></div>
      </div>
    </section>

    <!-- Weekly Goal Section -->
    <section class="weekly-goal-section">
      <div class="container">
        <WeeklyGoalWidget />
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
      <div class="container">
        <div v-if="stats" class="stats-grid">
          <!-- Subscription Card - Featured -->
          <div
            class="stat-card stat-featured stagger-item"
            :aria-label="getSubscriptionAriaLabel()"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">Diesen Monat</span>
              <div class="stat-icon" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
              </div>
            </div>
            <div class="stat-value" aria-hidden="true">{{ usage?.unlimited ? '∞' : usage?.remaining || 0 }}</div>
            <div class="stat-name" aria-hidden="true">{{ usage?.unlimited ? 'Unbegrenzt' : 'Verbleibend' }}</div>
            <router-link to="/subscription" class="stat-link">
              {{ getPlanLabel() }} Plan
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </router-link>
          </div>

          <!-- Applications Card -->
          <div
            class="stat-card stagger-item"
            :aria-label="`Gesamt: ${stats.gesamt} Bewerbungen`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">Gesamt</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.gesamt }}</div>
            <div class="stat-name" aria-hidden="true">Bewerbungen</div>
          </div>

          <!-- Created Card -->
          <div
            class="stat-card stagger-item"
            :aria-label="`Erstellt: ${stats.erstellt} Anschreiben`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">Erstellt</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.erstellt }}</div>
            <div class="stat-name" aria-hidden="true">Anschreiben</div>
          </div>

          <!-- Sent Card -->
          <div
            class="stat-card stagger-item"
            :aria-label="`Versendet: ${stats.versendet} Bewerbungen`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">Versendet</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.versendet }}</div>
            <div class="stat-name" aria-hidden="true">Bewerbungen</div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-else-if="!loadError && !stats" class="stats-grid" role="status" aria-label="Statistiken werden geladen">
          <div v-for="i in 4" :key="i" class="stat-card">
            <div class="skeleton skeleton-card" aria-hidden="true"></div>
          </div>
          <span class="sr-only">Statistiken werden geladen...</span>
        </div>

        <!-- Error State -->
        <div v-else class="loading-error" role="alert">
          <svg class="loading-error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p class="loading-error-message">Statistiken konnten nicht geladen werden</p>
          <button @click="retryLoadStats" class="loading-error-retry">
            Erneut versuchen
          </button>
        </div>
      </div>
    </section>

    <!-- Ink Stroke Divider -->
    <div class="container">
      <div class="ink-stroke"></div>
    </div>

    <!-- Quick Actions -->
    <section class="actions-section">
      <div class="container">
        <h2 class="section-title">Schnellzugriff</h2>

        <div class="actions-grid">
          <router-link to="/documents" class="action-card stagger-item">
            <div class="action-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <div class="action-content">
              <h3>Dokumente</h3>
              <p>CV, Zeugnisse und Dokumente verwalten</p>
            </div>
            <div class="action-arrow">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
          </router-link>

          <router-link to="/templates" class="action-card stagger-item">
            <div class="action-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </div>
            <div class="action-content">
              <h3>Templates</h3>
              <p>Anschreiben-Vorlagen erstellen</p>
            </div>
            <div class="action-arrow">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
          </router-link>

          <router-link to="/applications" class="action-card stagger-item">
            <div class="action-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
            <div class="action-content">
              <h3>Bewerbungen</h3>
              <p>Übersicht aller Bewerbungen</p>
            </div>
            <div class="action-arrow">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- Interview Stats Widget -->
    <section class="interview-stats-section">
      <div class="container">
        <InterviewStatsWidget />
      </div>
    </section>

    <!-- Job Recommendations -->
    <section class="recommendations-section">
      <div class="container">
        <JobRecommendations />
      </div>
    </section>

    <!-- Info Banner -->
    <section class="info-section">
      <div class="container">
        <div class="info-banner zen-card">
          <div class="info-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <div class="info-content">
            <h3>Wie funktioniert's?</h3>
            <p>
              Laden Sie Ihre Dokumente hoch, erstellen Sie Templates und nutzen Sie
              die Chrome Extension, um mit einem Klick personalisierte Bewerbungen zu generieren.
            </p>
          </div>
          <router-link to="/settings" class="zen-btn zen-btn-ai zen-btn-sm">
            Extension einrichten
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'
import { authStore } from '../store/auth'
import WeeklyGoalWidget from '../components/WeeklyGoalWidget.vue'
import InterviewStatsWidget from '../components/InterviewStatsWidget.vue'
import JobRecommendations from '../components/JobRecommendations.vue'

const stats = ref(null)
const usage = ref(null)
const bannerDismissedThisSession = ref(false)
const loadError = ref(false)
const skills = ref([])
const skillsLoaded = ref(false)

// Check if user needs to see the verification banner
const needsVerification = computed(() => {
  if (!authStore.user) return false
  return authStore.user.email_verified === false
})

// Show full banner if not dismissed this session and never dismissed before
const showFullBanner = computed(() => {
  if (!needsVerification.value) return false
  if (bannerDismissedThisSession.value) return false
  // Show full banner if never dismissed before (no localStorage entry)
  return !localStorage.getItem('verificationBannerDismissedOnce')
})

// Show compact banner if full banner was dismissed (either this session or before)
const showCompactBanner = computed(() => {
  if (!needsVerification.value) return false
  // Show compact if full banner is not shown and user has dismissed before
  return !showFullBanner.value && (bannerDismissedThisSession.value || localStorage.getItem('verificationBannerDismissedOnce'))
})

const dismissBanner = () => {
  bannerDismissedThisSession.value = true
  // Store that user has dismissed the banner at least once (persists across browser sessions)
  localStorage.setItem('verificationBannerDismissedOnce', 'true')
}

const getPlanLabel = () => {
  const plan = usage.value?.plan || 'free'
  return plan.charAt(0).toUpperCase() + plan.slice(1)
}

const getSubscriptionAriaLabel = () => {
  if (usage.value?.unlimited) {
    return `Diesen Monat: Unbegrenzte Bewerbungen im ${getPlanLabel()} Plan`
  }
  const remaining = usage.value?.remaining || 0
  return `Diesen Monat: ${remaining} Bewerbungen verbleibend im ${getPlanLabel()} Plan`
}

const loadStats = async () => {
  loadError.value = false
  try {
    // Fetch fresh user data to get current email_verified status
    await authStore.fetchUser()
    const { data } = await api.silent.get('/stats')
    stats.value = data.stats
    usage.value = data.usage
  } catch (error) {
    console.error('Failed to load stats:', error)
    loadError.value = true
  }
}

const loadSkills = async () => {
  try {
    const { data } = await api.silent.get('/users/me/skills')
    skills.value = data.skills || []
  } catch (error) {
    console.error('Failed to load skills:', error)
  } finally {
    skillsLoaded.value = true
  }
}

// Show skills hint if no skills and not dismissed for 7 days
const showSkillsHint = computed(() => {
  if (!skillsLoaded.value) return false
  if (skills.value.length > 0) return false
  const dismissed = localStorage.getItem('skillsHintDismissedAt')
  if (dismissed) {
    const dismissedAt = new Date(dismissed)
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    if (dismissedAt > sevenDaysAgo) return false
  }
  return true
})

const dismissSkillsHint = () => {
  localStorage.setItem('skillsHintDismissedAt', new Date().toISOString())
  skillsLoaded.value = false // Force recompute
  setTimeout(() => { skillsLoaded.value = true }, 0)
}

const retryLoadStats = () => {
  stats.value = null
  loadStats()
}

onMounted(async () => {
  await Promise.all([loadStats(), loadSkills()])
})
</script>

<style scoped>
.dashboard {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
}

/* ========================================
   VERIFICATION BANNER
   ======================================== */
.verification-banner {
  background: var(--color-warning-subtle, #fff3e0);
  border-bottom: 1px solid var(--color-warning, #f57c00);
  padding: var(--space-md) 0;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.banner-icon {
  color: var(--color-warning, #f57c00);
  flex-shrink: 0;
}

.banner-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.banner-text strong {
  color: var(--color-sumi);
  font-size: 0.9375rem;
}

.banner-text span {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.banner-dismiss {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.banner-dismiss:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-sumi);
}

/* Compact Banner (after first dismissal) */
.verification-banner-compact {
  background: var(--color-warning-subtle, #fff3e0);
  border-bottom: 1px solid var(--color-warning, #f57c00);
  padding: var(--space-sm) 0;
}

.compact-banner-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-warning-dark, #e65100);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-base);
}

.compact-banner-link:hover {
  color: var(--color-warning, #f57c00);
}

.compact-banner-link .arrow-icon {
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--transition-base);
}

.compact-banner-link:hover .arrow-icon {
  opacity: 1;
  transform: translateX(0);
}

@media (max-width: 768px) {
  .banner-content {
    flex-wrap: wrap;
  }

  .banner-text {
    flex-basis: calc(100% - 60px);
  }

  .verification-banner .zen-btn {
    width: 100%;
    margin-top: var(--space-sm);
  }
}

/* ========================================
   SKILLS HINT BANNER
   ======================================== */
.skills-hint-banner {
  background: var(--color-ai-subtle, #e8eef3);
  border-bottom: 1px solid var(--color-ai, #3d5a6c);
  padding: var(--space-md) 0;
}

.skills-hint-content {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.skills-hint-icon {
  color: var(--color-ai, #3d5a6c);
  flex-shrink: 0;
}

.skills-hint-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.skills-hint-text strong {
  color: var(--color-sumi);
  font-size: 0.9375rem;
}

.skills-hint-text span {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.skills-hint-dismiss {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.skills-hint-dismiss:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-sumi);
}

@media (max-width: 768px) {
  .skills-hint-content {
    flex-wrap: wrap;
  }

  .skills-hint-text {
    flex-basis: calc(100% - 60px);
  }

  .skills-hint-banner .zen-btn {
    width: 100%;
    margin-top: var(--space-sm);
  }
}

/* ========================================
   HERO SECTION - Ma (Negative Space)
   ======================================== */
.hero-section {
  position: relative;
  padding: var(--space-ma-xl) 0 var(--space-ma);
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-greeting {
  margin-bottom: var(--space-md);
}

.greeting-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.hero-section h1 {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: 0;
}

.hero-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin-bottom: 0;
}

.hero-enso {
  position: absolute;
  top: 50%;
  right: 10%;
  transform: translateY(-50%);
  width: 300px;
  height: 300px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 3px 2px 2.5px;
  opacity: 0.03;
  pointer-events: none;
}

/* ========================================
   WEEKLY GOAL SECTION
   ======================================== */
.weekly-goal-section {
  padding: 0 0 var(--space-ma);
  margin-top: calc(-1 * var(--space-lg));
}

/* ========================================
   STATS SECTION
   ======================================== */
.stats-section {
  padding: var(--space-ma) 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
}

.stat-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  box-shadow: var(--shadow-lifted);
  transform: translateY(-2px);
}

.stat-featured {
  background: var(--color-ai);
  border-color: transparent;
}

.stat-featured .stat-label,
.stat-featured .stat-value,
.stat-featured .stat-name {
  color: var(--color-text-inverse);
}

.stat-featured .stat-icon {
  color: rgba(255, 255, 255, 0.6);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-md);
}

.stat-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.stat-icon {
  color: var(--color-ai);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.stat-name {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.stat-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-md);
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  transition: gap var(--transition-base);
}

.stat-link:hover {
  gap: var(--space-sm);
}

/* ========================================
   LOADING ERROR STATE
   ======================================== */
.loading-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  grid-column: 1 / -1; /* Span all columns */
  text-align: center;
}

.loading-error-icon {
  width: 48px;
  height: 48px;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-md);
}

.loading-error-message {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-md);
}

.loading-error-retry {
  background: transparent;
  border: 1px solid var(--color-ai);
  color: var(--color-ai);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.loading-error-retry:hover {
  background: var(--color-ai);
  color: var(--color-text-inverse);
}

/* ========================================
   ACTIONS SECTION
   ======================================== */
.actions-section {
  padding: var(--space-ma) 0;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.actions-grid {
  display: grid;
  gap: var(--space-md);
}

.action-card {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-lg) var(--space-xl);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  text-decoration: none;
  transition: all var(--transition-base);
}

.action-card:hover {
  border-color: var(--color-ai);
  box-shadow: var(--shadow-lifted);
  transform: translateX(4px);
}

.action-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
  transition: all var(--transition-base);
}

.action-card:hover .action-icon {
  background: var(--color-ai);
  color: var(--color-text-inverse);
}

.action-content {
  flex: 1;
}

.action-content h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
}

.action-content p {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: 0;
}

.action-arrow {
  color: var(--color-ai);
  opacity: 0;
  transform: translateX(-8px);
  transition: all var(--transition-base);
}

.action-card:hover .action-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* ========================================
   INFO SECTION
   ======================================== */
.info-section {
  padding: var(--space-ma) 0 var(--space-ma-xl);
}

.info-banner {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-lg) var(--space-xl);
  background: var(--color-ai-subtle);
  border: 1px solid rgba(61, 90, 108, 0.15);
}

.info-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.info-content {
  flex: 1;
}

.info-content h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-xs);
  color: var(--color-sumi);
}

.info-content p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin-bottom: 0;
  max-width: 600px;
}

/* ========================================
   INTERVIEW STATS SECTION
   ======================================== */
.interview-stats-section {
  padding: var(--space-ma) 0;
}

/* ========================================
   RECOMMENDATIONS SECTION
   ======================================== */
.recommendations-section {
  padding: var(--space-ma) 0;
  background: var(--color-bg-subtle);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: var(--space-ma) 0 var(--space-lg);
  }

  .hero-enso {
    width: 200px;
    height: 200px;
    right: -50px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-value {
    font-size: 2.5rem;
  }

  .action-card {
    padding: var(--space-md) var(--space-lg);
  }

  .action-icon {
    width: 48px;
    height: 48px;
  }

  .info-banner {
    flex-direction: column;
    text-align: center;
    gap: var(--space-md);
    padding: var(--space-lg);
  }

  .info-content p {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .action-arrow {
    display: none;
  }
}
</style>
