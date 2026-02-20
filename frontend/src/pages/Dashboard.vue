<template>
  <div class="dashboard">
    <!-- Email Verification Reminder - Subtle banner for notifications -->
    <div v-if="needsVerification && !verificationBannerDismissed" class="verification-reminder">
      <div class="container">
        <router-link to="/email-verification" class="reminder-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
          <span>{{ t('dashboard.verifyEmailNotification') }}</span>
          <svg class="arrow-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
        <button @click="dismissVerificationBanner" class="reminder-dismiss" :aria-label="t('dashboard.closeHint')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Hero Section with Ma (negative space) -->
    <section class="hero-section">
      <div class="container">
        <div class="hero-content animate-fade-up">
          <div class="hero-greeting">
            <span class="greeting-label">{{ t('dashboard.hero.greeting') }}</span>
            <h1>{{ t('dashboard.hero.welcomeBack') }}</h1>
          </div>
          <p class="hero-subtitle">
            {{ t('dashboard.hero.subtitle') }}
          </p>
        </div>

        <!-- Decorative enso -->
        <div class="hero-enso"></div>
      </div>
    </section>

    <!-- Onboarding Steps (for new users) -->
    <section v-if="showOnboarding" class="onboarding-section">
      <div class="container">
        <div class="onboarding-card zen-card">
          <div class="onboarding-header">
            <h2>{{ t('dashboard.onboarding.title') }}</h2>
            <span class="onboarding-progress">{{ completedSteps }}/3</span>
          </div>
          <div class="onboarding-steps">
            <!-- Step 1: CV Upload -->
            <div class="onboarding-step" :class="{ completed: hasSkills, active: !hasSkills }">
              <div class="step-indicator">
                <svg v-if="hasSkills" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span v-else>1</span>
              </div>
              <div class="step-content">
                <h4>{{ t('dashboard.onboarding.uploadCv') }}</h4>
                <p>{{ t('dashboard.onboarding.skillsExtracted') }}</p>
                <router-link v-if="!hasSkills" to="/documents" class="zen-btn zen-btn-sm zen-btn-ai">
                  {{ t('dashboard.onboarding.upload') }}
                </router-link>
              </div>
            </div>

            <!-- Step 2: Email Verification -->
            <div class="onboarding-step" :class="{ completed: hasVerifiedEmail, active: hasSkills && !hasVerifiedEmail }">
              <div class="step-indicator">
                <svg v-if="hasVerifiedEmail" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span v-else>2</span>
              </div>
              <div class="step-content">
                <h4>{{ t('dashboard.onboarding.verifyEmail') }}</h4>
                <p>{{ t('dashboard.onboarding.notificationsAndSecurity') }}</p>
                <router-link v-if="!hasVerifiedEmail" to="/email-verification" class="zen-btn zen-btn-sm zen-btn-ghost">
                  {{ t('dashboard.onboarding.verify') }}
                </router-link>
              </div>
            </div>

            <!-- Step 3: First Application -->
            <div class="onboarding-step" :class="{ completed: hasApplications, active: hasSkills && hasVerifiedEmail && !hasApplications }">
              <div class="step-indicator">
                <svg v-if="hasApplications" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span v-else>3</span>
              </div>
              <div class="step-content">
                <h4>{{ t('dashboard.onboarding.createFirstApp') }}</h4>
                <p>{{ t('dashboard.onboarding.aiGenerated') }}</p>
                <router-link v-if="!hasApplications" to="/new-application" class="zen-btn zen-btn-sm zen-btn-ghost">
                  {{ t('dashboard.onboarding.create') }}
                </router-link>
              </div>
            </div>
          </div>
        </div>
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
              <span class="stat-label">{{ t('dashboard.stats.thisMonth') }}</span>
              <div class="stat-icon" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
              </div>
            </div>
            <div class="stat-value" aria-hidden="true">{{ usage?.unlimited ? '∞' : usage?.remaining || 0 }}</div>
            <div class="stat-name" aria-hidden="true">{{ usage?.unlimited ? t('dashboard.stats.unlimited') : t('dashboard.stats.remaining') }}</div>
            <router-link to="/subscription" class="stat-link">
              {{ getPlanLabel() }} {{ t('dashboard.stats.plan') }}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </router-link>
          </div>

          <!-- Applications Card -->
          <div
            class="stat-card stagger-item"
            :aria-label="`${t('dashboard.stats.total')}: ${stats.gesamt} ${t('dashboard.stats.applications')}`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">{{ t('dashboard.stats.total') }}</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.gesamt }}</div>
            <div class="stat-name" aria-hidden="true">{{ t('dashboard.stats.applications') }}</div>
          </div>

          <!-- Created Card -->
          <div
            class="stat-card stagger-item"
            :aria-label="`${t('dashboard.stats.created')}: ${stats.erstellt} ${t('dashboard.stats.coverLetters')}`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">{{ t('dashboard.stats.created') }}</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.erstellt }}</div>
            <div class="stat-name" aria-hidden="true">{{ t('dashboard.stats.coverLetters') }}</div>
          </div>

          <!-- Sent Card -->
          <div
            class="stat-card stagger-item"
            :aria-label="`${t('dashboard.stats.sent')}: ${stats.versendet} ${t('dashboard.stats.applications')}`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">{{ t('dashboard.stats.sent') }}</span>
              <span v-if="stats.versendet_heute > 0" class="stat-badge">+{{ stats.versendet_heute }} {{ t('dashboard.stats.today') }}</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.versendet }}</div>
            <div class="stat-name" aria-hidden="true">{{ t('dashboard.stats.applications') }}</div>
          </div>

          <!-- Responses Card (from topaz) -->
          <div
            class="stat-card stagger-item"
            :aria-label="`${t('dashboard.stats.responses')}: ${stats.antwort_erhalten} ${t('dashboard.stats.received')}`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">{{ t('dashboard.stats.responses') }}</span>
              <span v-if="stats.antworten_heute > 0" class="stat-badge stat-badge-new">+{{ stats.antworten_heute }} {{ t('dashboard.stats.new') }}</span>
            </div>
            <div class="stat-value" aria-hidden="true">{{ stats.antwort_erhalten }}</div>
            <div class="stat-name" aria-hidden="true">{{ t('dashboard.stats.received') }}</div>
          </div>

          <!-- Interviews Card - Prominent display of upcoming interviews (from opal) -->
          <router-link
            v-if="nextInterview"
            :to="`/applications/${nextInterview.id}/interview`"
            class="stat-card stat-interviews stagger-item"
            :aria-label="`${upcomingInterviewCount} Interview${upcomingInterviewCount !== 1 ? 's' : ''} ${t('dashboard.stats.planned')}, ${t('common.next')}: ${nextInterview.firma} ${getRelativeTime(nextInterview.interview_date)}`"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">{{ t('dashboard.stats.interviews') }}</span>
              <span v-if="stats.interviews_heute > 0" class="stat-badge stat-badge-new">+{{ stats.interviews_heute }} {{ t('dashboard.stats.new') }}</span>
              <div class="stat-icon" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
              </div>
            </div>
            <div class="stat-value" aria-hidden="true">{{ upcomingInterviewCount }}</div>
            <div class="stat-name stat-name-highlight" aria-hidden="true">
              {{ formatInterviewDate(nextInterview.interview_date) }}
            </div>
            <div class="stat-interview-company">{{ nextInterview.firma }}</div>
            <div class="stat-interview-cta">
              {{ t('dashboard.stats.prepare') }}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
          </router-link>

          <!-- Interviews Card - Empty state (from opal) -->
          <div
            v-else
            class="stat-card stagger-item"
            :aria-label="t('dashboard.stats.noInterviewsPlanned')"
            role="region"
          >
            <div class="stat-header">
              <span class="stat-label">{{ t('dashboard.stats.interviews') }}</span>
              <div class="stat-icon" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
              </div>
            </div>
            <div class="stat-value" aria-hidden="true">0</div>
            <div class="stat-name" aria-hidden="true">{{ t('dashboard.stats.planned') }}</div>
          </div>
        </div>

        <!-- Loading State -->
        <!-- SKEL-002-BUG-001: Changed from 5 to 6 skeletons to match actual stats count -->
        <div v-else-if="!loadError && !stats" class="stats-grid" role="status" :aria-label="t('common.loading')">
          <div v-for="i in 6" :key="i" class="stat-card">
            <div class="skeleton skeleton-card" aria-hidden="true"></div>
          </div>
          <span class="sr-only">{{ t('common.loading') }}</span>
        </div>

        <!-- Error State -->
        <div v-else class="loading-error" role="alert">
          <svg class="loading-error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p class="loading-error-message">{{ t('dashboard.stats.loadError') }}</p>
          <button @click="retryLoadStats" class="loading-error-retry">
            {{ t('dashboard.stats.retry') }}
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
        <h2 class="section-title">{{ t('dashboard.actions.title') }}</h2>

        <div class="actions-grid">
          <!-- State: No skills (CV not uploaded) -->
          <template v-if="!hasSkills">
            <router-link to="/documents" class="action-card action-card-prominent stagger-item">
              <div class="action-icon action-icon-ai">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="12" y1="18" x2="12" y2="12"/>
                  <line x1="9" y1="15" x2="15" y2="15"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.onboarding.uploadCv') }}</h3>
                <p>{{ t('dashboard.actions.uploadCvDesc') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </router-link>

            <router-link to="/settings" class="action-card stagger-item">
              <div class="action-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                  <line x1="8" y1="21" x2="16" y2="21"/>
                  <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.actions.setupExtension') }}</h3>
                <p>{{ t('dashboard.actions.setupExtensionDesc') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </router-link>

            <div class="action-card action-card-disabled stagger-item" :title="t('dashboard.actions.uploadCvFirst')">
              <div class="action-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.actions.discoverJobs') }}</h3>
                <p>{{ t('dashboard.actions.uploadCvFirst') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </div>
          </template>

          <!-- State: Has skills but no applications -->
          <template v-else-if="!hasApplications">
            <router-link to="/new-application" class="action-card action-card-prominent stagger-item">
              <div class="action-icon action-icon-ai">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.onboarding.createFirstApp') }}</h3>
                <p>{{ t('dashboard.actions.createFirstAppDesc') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </router-link>

            <router-link to="/job-dashboard" class="action-card stagger-item">
              <div class="action-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.actions.discoverJobs') }}</h3>
                <p>{{ t('dashboard.actions.discoverJobsDesc') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </router-link>

            <div class="action-card action-card-disabled stagger-item" :title="t('dashboard.actions.createAppFirst')">
              <div class="action-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="3" y1="9" x2="21" y2="9"/>
                  <line x1="9" y1="21" x2="9" y2="9"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.actions.manageApplications') }}</h3>
                <p>{{ t('dashboard.actions.createAppFirst') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </div>
          </template>

          <!-- State: Has applications (normal) -->
          <template v-else>
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
                <h3>{{ t('dashboard.actions.documents') }}</h3>
                <p>{{ t('dashboard.actions.manageDocs') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </router-link>

            <router-link to="/job-dashboard" class="action-card stagger-item">
              <div class="action-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <div class="action-content">
                <h3>{{ t('dashboard.actions.discoverJobs') }}</h3>
                <p>{{ t('dashboard.actions.discoverJobsDesc') }}</p>
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
                <h3>{{ t('dashboard.stats.applications') }}</h3>
                <p>{{ t('dashboard.actions.allApplications') }}</p>
              </div>
              <div class="action-arrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </router-link>
          </template>
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
            <h3>{{ t('dashboard.info.howItWorks') }}</h3>
            <p>
              {{ t('dashboard.info.description') }}
            </p>
          </div>
          <router-link to="/settings" class="zen-btn zen-btn-ai zen-btn-sm">
            {{ t('dashboard.actions.setupExtension') }}
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api/client'
import { authStore } from '../stores/auth'
import WeeklyGoalWidget from '../components/WeeklyGoalWidget.vue'
import InterviewStatsWidget from '../components/InterviewStatsWidget.vue'
import JobRecommendations from '../components/JobRecommendations.vue'
import { getFullLocale } from '../i18n'

const { t } = useI18n()

const stats = ref(null)
const usage = ref(null)
const verificationBannerDismissed = ref(localStorage.getItem('verificationBannerDismissed') === 'true')
const loadError = ref(false)
const skills = ref([])
const skillsLoaded = ref(false)
const interviewStats = ref(null)

const needsVerification = computed(() => authStore.user?.email_verified === false)

function dismissVerificationBanner() {
  verificationBannerDismissed.value = true
  localStorage.setItem('verificationBannerDismissed', 'true')
}

function getPlanLabel() {
  const plan = usage.value?.plan || 'free'
  return plan.charAt(0).toUpperCase() + plan.slice(1)
}

function getSubscriptionAriaLabel() {
  if (usage.value?.unlimited) {
    return t('dashboard.aria.subscriptionUnlimited', { plan: getPlanLabel() })
  }
  const remaining = usage.value?.remaining || 0
  return t('dashboard.aria.subscriptionRemaining', { count: remaining, plan: getPlanLabel() })
}

async function loadStats() {
  loadError.value = false
  try {
    await authStore.fetchUser()
    const { data } = await api.silent.get('/stats')
    stats.value = data.stats
    usage.value = data.usage
  } catch (error) {
    console.error('Failed to load stats:', error)
    loadError.value = true
  }
}

async function loadSkills() {
  try {
    const { data } = await api.silent.get('/users/me/skills')
    skills.value = data.skills || []
  } catch (error) {
    console.error('Failed to load skills:', error)
  } finally {
    skillsLoaded.value = true
  }
}

async function loadInterviewStats() {
  try {
    const { data } = await api.silent.get('/applications/interview-stats')
    if (data.success) {
      interviewStats.value = data.data
    }
  } catch (error) {
    console.error('Failed to load interview stats:', error)
  }
}

const upcomingInterviewCount = computed(() => {
  return interviewStats.value?.upcoming_interviews?.length || 0
})

const nextInterview = computed(() => {
  return interviewStats.value?.upcoming_interviews?.[0] || null
})

const MS_PER_DAY = 1000 * 60 * 60 * 24

function daysFromNow(dateStr) {
  return Math.ceil((new Date(dateStr) - new Date()) / MS_PER_DAY)
}

function formatInterviewDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const diffDays = daysFromNow(dateStr)
  const time = date.toLocaleTimeString(getFullLocale(), { hour: '2-digit', minute: '2-digit' })

  if (diffDays === 0) return t('dashboard.time.todayAt', { time })
  if (diffDays === 1) return t('dashboard.time.tomorrowAt', { time })

  const dayNames = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
  return `${dayNames[date.getDay()]} ${time}`
}

function getRelativeTime(dateStr) {
  if (!dateStr) return ''
  const diffDays = daysFromNow(dateStr)

  if (diffDays === 0) return t('dashboard.time.today')
  if (diffDays === 1) return t('dashboard.time.tomorrow')
  return t('dashboard.time.inDays', { days: diffDays })
}

// Onboarding step computeds
const hasSkills = computed(() => skills.value.length > 0)
const hasVerifiedEmail = computed(() => authStore.user?.email_verified === true)
const hasApplications = computed(() => (stats.value?.gesamt || 0) > 0)
const completedSteps = computed(() =>
  [hasSkills.value, hasVerifiedEmail.value, hasApplications.value].filter(Boolean).length
)
const showOnboarding = computed(() => skillsLoaded.value && completedSteps.value < 3)

function retryLoadStats() {
  stats.value = null
  loadStats()
}

onMounted(async () => {
  await Promise.all([loadStats(), loadSkills(), loadInterviewStats()])
})
</script>

<style scoped>
.dashboard {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
}

/* ========================================
   VERIFICATION REMINDER - Subtle banner
   ======================================== */
.verification-reminder {
  background: var(--color-bg-subtle, #f8f9fa);
  border-bottom: 1px solid var(--color-border-light);
  padding: var(--space-sm) 0;
}

.verification-reminder .container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.reminder-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.8125rem;
  transition: all var(--transition-base);
}

.reminder-link:hover {
  color: var(--color-ai);
}

.reminder-link .arrow-icon {
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--transition-base);
}

.reminder-link:hover .arrow-icon {
  opacity: 1;
  transform: translateX(0);
}

.reminder-dismiss {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.reminder-dismiss:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-sumi);
}

/* ========================================
   ONBOARDING SECTION
   ======================================== */
.onboarding-section {
  padding: 0 0 var(--space-lg);
}

.onboarding-card {
  padding: var(--space-lg) var(--space-xl);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
}

.onboarding-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.onboarding-header h2 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
  color: var(--color-sumi);
}

.onboarding-progress {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-ai);
  background: var(--color-ai-subtle);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full, 9999px);
}

.onboarding-steps {
  display: flex;
  gap: var(--space-xl);
}

.onboarding-step {
  flex: 1;
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.onboarding-step.active {
  background: var(--color-ai-subtle);
  border: 1px solid rgba(61, 90, 108, 0.2);
}

.onboarding-step.completed {
  opacity: 0.7;
}

.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all var(--transition-base);
}

.onboarding-step.active .step-indicator {
  background: var(--color-ai);
  color: var(--color-text-inverse);
}

.onboarding-step.completed .step-indicator {
  background: var(--color-koke);
  color: var(--color-text-inverse);
}

.onboarding-step:not(.active):not(.completed) .step-indicator {
  background: var(--color-border-light);
  color: var(--color-text-ghost);
}

.step-content h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--space-xs) 0;
  color: var(--color-sumi);
}

.step-content p {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-sm) 0;
}

.onboarding-step.completed .step-content h4 {
  text-decoration: line-through;
  color: var(--color-text-tertiary);
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
  grid-template-columns: repeat(5, 1fr);

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

.stat-badge {
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full, 9999px);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  white-space: nowrap;
}

.stat-badge-new {
  background: var(--color-koke-subtle, rgba(122, 139, 110, 0.15));
  color: var(--color-koke);
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

/* Interview Stat Card - Prominent display */
.stat-interviews {
  background: linear-gradient(135deg, var(--color-koke) 0%, #5a7a5c 100%);
  border-color: transparent;
  cursor: pointer;
  text-decoration: none;
  display: flex;
  flex-direction: column;
}

.stat-interviews:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lifted), 0 8px 24px rgba(106, 142, 108, 0.25);
}

.stat-interviews .stat-label,
.stat-interviews .stat-value,
.stat-interviews .stat-name {
  color: var(--color-text-inverse);
}

.stat-interviews .stat-icon {
  color: rgba(255, 255, 255, 0.7);
}

.stat-name-highlight {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95) !important;
}

.stat-interview-company {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.8);
  margin-top: var(--space-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-interview-cta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: auto;
  padding-top: var(--space-md);
  font-size: 0.8125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  transition: gap var(--transition-base);
}

.stat-interviews:hover .stat-interview-cta {
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

/* Prominent action card (primary CTA) */
.action-card-prominent {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.action-card-prominent .action-icon,
.action-icon-ai {
  background: var(--color-ai);
  color: var(--color-text-inverse);
}

.action-card-prominent:hover .action-icon {
  background: var(--color-sumi);
}

/* Disabled action card */
.action-card-disabled {
  opacity: 0.45;
  pointer-events: none;
  cursor: not-allowed;
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
@media (max-width: 1280px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-badge {
    font-size: 0.625rem;
    padding: 0.125rem 0.375rem;
  }
}

@media (max-width: 768px) {
  .onboarding-steps {
    flex-direction: column;
    gap: var(--space-md);
  }

  .onboarding-card {
    padding: var(--space-md) var(--space-lg);
  }

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
