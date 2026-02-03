import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/auth'

const DEFAULT_TITLE = 'obo'

const routes = [
  // Public routes - explicitly marked to skip auth checks entirely
  { path: '/login', component: () => import('../pages/Login.vue'), meta: { title: 'Anmelden', public: true } },
  { path: '/register', component: () => import('../pages/Register.vue'), meta: { title: 'Registrieren', public: true } },
  { path: '/email-verification', component: () => import('../pages/EmailVerification.vue'), meta: { title: 'E-Mail-Bestätigung', public: true } },
  { path: '/verify-email', component: () => import('../pages/VerifyEmail.vue'), meta: { title: 'E-Mail verifizieren', public: true } },
  { path: '/forgot-password', component: () => import('../pages/ForgotPassword.vue'), meta: { title: 'Passwort vergessen', public: true } },
  { path: '/reset-password', component: () => import('../pages/ResetPassword.vue'), meta: { title: 'Passwort zurücksetzen', public: true } },
  { path: '/impressum', component: () => import('../pages/Impressum.vue'), meta: { title: 'Impressum', public: true } },
  { path: '/datenschutz', component: () => import('../pages/Datenschutz.vue'), meta: { title: 'Datenschutz', public: true } },

  // Landing page - shows for unauthenticated users, redirects authenticated users to dashboard
  { path: '/', component: () => import('../pages/Landing.vue'), meta: { title: 'obo - Bewerbungen, die sich selbst schreiben', public: true, landing: true } },

  // Dashboard - protected route for authenticated users
  { path: '/dashboard', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true, title: 'Dashboard' } },
  { path: '/documents', component: () => import('../pages/Documents.vue'), meta: { requiresAuth: true, title: 'Dokumente' } },
  { path: '/templates', component: () => import('../pages/Templates.vue'), meta: { requiresAuth: true, title: 'Vorlagen' } },
  { path: '/applications', component: () => import('../pages/Applications.vue'), meta: { requiresAuth: true, title: 'Bewerbungen' } },
  { path: '/timeline', component: () => import('../pages/Timeline.vue'), meta: { requiresAuth: true, title: 'Timeline' } },
  { path: '/company-insights', component: () => import('../pages/CompanyInsights.vue'), meta: { requiresAuth: true, title: 'Firmen-Insights' } },
  { path: '/new-application', component: () => import('../pages/NewApplication.vue'), meta: { requiresAuth: true, title: 'Neue Bewerbung' } },
  { path: '/ats', component: () => import('../pages/ATSView.vue'), meta: { requiresAuth: true, title: 'ATS-Check' } },
  { path: '/settings', component: () => import('../pages/Settings.vue'), meta: { requiresAuth: true, title: 'Einstellungen' } },
  { path: '/subscription', component: () => import('../pages/SubscriptionView.vue'), meta: { requiresAuth: true, title: 'Abonnement' } },
  { path: '/subscription/success', component: () => import('../pages/SubscriptionSuccess.vue'), meta: { requiresAuth: true, title: 'Abonnement erfolgreich' } },
  { path: '/applications/:id/interview', component: () => import('../pages/InterviewPrep.vue'), meta: { requiresAuth: true, title: 'Interview-Vorbereitung' } },
  { path: '/applications/:id/mock-interview', component: () => import('../pages/MockInterview.vue'), meta: { requiresAuth: true, title: 'Mock-Interview' } },

  // Catch-all route for 404 - must be last
  { path: '/:pathMatch(.*)*', component: () => import('../pages/NotFound.vue'), meta: { title: 'Seite nicht gefunden' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  // Landing page: redirect authenticated users to dashboard
  if (to.meta.landing && authStore.isAuthenticated()) {
    next('/dashboard')
    return
  }

  // Public routes: skip all auth checks to prevent side effects
  if (to.meta.public) {
    next()
    return
  }

  // Protected routes: check authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated()) {
    next('/login')
  } else {
    next()
  }
})

// Set dynamic page title after each navigation
router.afterEach((to) => {
  const pageTitle = to.meta.title
  document.title = pageTitle ? `${pageTitle} | ${DEFAULT_TITLE}` : DEFAULT_TITLE
})

export default router
