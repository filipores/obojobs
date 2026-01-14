import axios from 'axios'
import { translateError } from '@/utils/errorTranslations'

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

    // 401 Unauthorized or 422 with JWT errors
    if (error.response?.status === 401 ||
        (error.response?.status === 422 && error.response?.data?.msg?.includes('token'))) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.$toast && !suppressToast) {
        window.$toast('Sitzung abgelaufen. Bitte neu anmelden.', 'warning')
      }
      window.location.href = '/login'
    } else if (error.response?.status >= 500) {
      // Server errors - always show unless suppressed
      if (window.$toast && !suppressToast) {
        window.$toast('Serverfehler. Bitte später erneut versuchen.', 'error')
      }
    } else if (error.response?.status === 400 || error.response?.status === 422) {
      // Validation errors - show specific message (translated if needed)
      const rawMessage = error.response?.data?.error || 'Ungültige Eingabe'
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
