import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/auth'

const routes = [
  // Public routes
  { path: '/login', component: () => import('../pages/Login.vue') },
  { path: '/register', component: () => import('../pages/Register.vue') },
  { path: '/impressum', component: () => import('../pages/Impressum.vue') },
  { path: '/datenschutz', component: () => import('../pages/Datenschutz.vue') },

  // Protected routes
  { path: '/', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/documents', component: () => import('../pages/Documents.vue'), meta: { requiresAuth: true } },
  { path: '/templates', component: () => import('../pages/Templates.vue'), meta: { requiresAuth: true } },
  { path: '/applications', component: () => import('../pages/Applications.vue'), meta: { requiresAuth: true } },
  { path: '/settings', component: () => import('../pages/Settings.vue'), meta: { requiresAuth: true } },
  { path: '/buy-credits', component: () => import('../pages/BuyCredits.vue'), meta: { requiresAuth: true } },
  { path: '/payment/success', component: () => import('../pages/PaymentSuccess.vue'), meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !authStore.isAuthenticated()) {
    next('/login')
  } else {
    next()
  }
})

export default router
