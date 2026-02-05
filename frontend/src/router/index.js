import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/auth'
import { demoStore } from '../stores/demo'
import i18n from '../i18n'

const DEFAULT_TITLE = 'obo'

const routes = [
  // Public routes - explicitly marked to skip auth checks entirely
  { path: '/login', component: () => import('../pages/Login.vue'), meta: { titleKey: 'pages.login', public: true } },
  { path: '/register', component: () => import('../pages/Register.vue'), meta: { titleKey: 'pages.register', public: true } },
  { path: '/email-verification', component: () => import('../pages/EmailVerification.vue'), meta: { titleKey: 'pages.emailVerification', public: true } },
  { path: '/verify-email', component: () => import('../pages/VerifyEmail.vue'), meta: { titleKey: 'pages.verifyEmail', public: true } },
  { path: '/forgot-password', component: () => import('../pages/ForgotPassword.vue'), meta: { titleKey: 'pages.forgotPassword', public: true } },
  { path: '/reset-password', component: () => import('../pages/ResetPassword.vue'), meta: { titleKey: 'pages.resetPassword', public: true } },
  { path: '/impressum', component: () => import('../pages/Impressum.vue'), meta: { titleKey: 'pages.impressum', public: true } },
  { path: '/datenschutz', component: () => import('../pages/Datenschutz.vue'), meta: { titleKey: 'pages.datenschutz', public: true } },

  // Landing page - shows for unauthenticated users, redirects authenticated users to dashboard
  { path: '/', component: () => import('../pages/Landing.vue'), meta: { titleKey: 'pages.landing', public: true, landing: true } },

  // Dashboard - protected route for authenticated users
  { path: '/dashboard', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true, titleKey: 'pages.dashboard' } },
  { path: '/documents', component: () => import('../pages/Documents.vue'), meta: { requiresAuth: true, titleKey: 'pages.documents' } },
  { path: '/templates', component: () => import('../pages/Templates.vue'), meta: { requiresAuth: true, titleKey: 'pages.templates' } },
  { path: '/applications', component: () => import('../pages/Applications.vue'), meta: { requiresAuth: true, titleKey: 'pages.applications' } },
  { path: '/timeline', component: () => import('../pages/Timeline.vue'), meta: { requiresAuth: true, titleKey: 'pages.timeline' } },
  { path: '/company-insights', component: () => import('../pages/CompanyInsights.vue'), meta: { requiresAuth: true, titleKey: 'pages.companyInsights' } },
  { path: '/new-application', component: () => import('../pages/NewApplication.vue'), meta: { requiresAuth: true, titleKey: 'pages.newApplication' } },
  { path: '/ats', component: () => import('../pages/ATSView.vue'), meta: { requiresAuth: true, titleKey: 'pages.ats' } },
  { path: '/settings', component: () => import('../pages/Settings.vue'), meta: { requiresAuth: true, titleKey: 'pages.settings' } },
  { path: '/subscription', component: () => import('../pages/SubscriptionView.vue'), meta: { requiresAuth: true, titleKey: 'pages.subscription' } },
  { path: '/subscription/success', component: () => import('../pages/SubscriptionSuccess.vue'), meta: { requiresAuth: true, titleKey: 'pages.subscriptionSuccess' } },
  { path: '/applications/:id/interview', component: () => import('../pages/InterviewPrep.vue'), meta: { requiresAuth: true, titleKey: 'pages.interviewPrep' } },
  { path: '/applications/:id/mock-interview', component: () => import('../pages/MockInterview.vue'), meta: { requiresAuth: true, titleKey: 'pages.mockInterview' } },

  // Catch-all route for 404 - must be last
  { path: '/:pathMatch(.*)*', component: () => import('../pages/NotFound.vue'), meta: { titleKey: 'pages.notFound' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  // Landing page: redirect authenticated users to dashboard
  // UNLESS they are in the demo flow (post-registration CV upload)
  if (to.meta.landing && authStore.isAuthenticated()) {
    // Allow staying on Landing if in demo flow or coming from registration with demo
    if (demoStore.isInDemoFlow() || to.query.demo === 'complete') {
      next()
      return
    }
    next('/dashboard')
    return
  }

  // Redirect authenticated users away from login/register to dashboard
  if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated()) {
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
  const titleKey = to.meta.titleKey
  const pageTitle = titleKey ? i18n.global.t(titleKey) : null
  document.title = pageTitle ? `${pageTitle} | ${DEFAULT_TITLE}` : DEFAULT_TITLE
})

export default router
