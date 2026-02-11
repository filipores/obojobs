import axios from 'axios'
import { translateError } from '@/utils/errorTranslations'
import i18n from '@/i18n'

// Helper function to detect JWT error messages
function isJWTErrorMessage(msg) {
  if (!msg) return false

  const jwtErrorPatterns = [
    'token',
    'Not enough segments',
    'Signature verification failed',
    'Invalid token',
    'Expired token',
    'Token has expired',
    'Invalid header',
    'Invalid payload',
    'jwt',
    'Bearer'
  ]

  return jwtErrorPatterns.some(pattern =>
    msg.toLowerCase().includes(pattern.toLowerCase())
  )
}

const api = axios.create({
  baseURL: '/api'
})

// Add token to requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors and show toast notifications
// Note: Toast deduplication is handled by Toast.vue component (2 second window)
api.interceptors.response.use(
  response => response,
  error => {
    // Check if caller wants to suppress automatic toast (e.g., has own error handler)
    const suppressToast = error.config?.suppressToast

    // Check if this is a login request - don't do global 401 handling for login
    // Login-Route should show its own error message for invalid credentials
    const isLoginRequest = error.config?.url === '/auth/login'

    // 401 Unauthorized or 422 with JWT errors
    // Skip global handling for login route to allow proper error display
    const isJWTError = error.response?.status === 401 ||
      (error.response?.status === 422 && isJWTErrorMessage(error.response?.data?.msg))

    if (!isLoginRequest && isJWTError) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.$toast && !suppressToast) {
        window.$toast(i18n.global.t('errors.sessionExpired'), 'warning')
      }
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
      // Forbidden - show permission denied
      if (window.$toast && !suppressToast) {
        window.$toast(i18n.global.t('errors.forbidden'), 'error')
      }
    } else if (error.response?.status === 404) {
      // Not found
      if (window.$toast && !suppressToast) {
        window.$toast(i18n.global.t('errors.notFound'), 'error')
      }
    } else if (error.response?.status >= 500) {
      // Server errors - always show unless suppressed
      if (window.$toast && !suppressToast) {
        window.$toast(i18n.global.t('errors.serverError'), 'error')
      }
    } else if (error.response?.status === 400 || error.response?.status === 422) {
      // Validation errors - show specific message (translated if needed)
      const rawMessage = error.response?.data?.error || i18n.global.t('errors.invalidInput')
      const message = translateError(rawMessage)
      if (window.$toast && !suppressToast) {
        window.$toast(message, 'error')
      }
    }
    return Promise.reject(error)
  }
)

// Helper to make requests without automatic toast on error
// Usage: api.silent.get('/path'), api.silent.post('/path', data)
api.silent = {
  get: (url, config = {}) => api.get(url, { ...config, suppressToast: true }),
  post: (url, data, config = {}) => api.post(url, data, { ...config, suppressToast: true }),
  put: (url, data, config = {}) => api.put(url, data, { ...config, suppressToast: true }),
  delete: (url, config = {}) => api.delete(url, { ...config, suppressToast: true }),
  patch: (url, data, config = {}) => api.patch(url, data, { ...config, suppressToast: true })
}

export default api
