import axios from 'axios'

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
api.interceptors.response.use(
  response => response,
  error => {
    // 401 Unauthorized or 422 with JWT errors
    if (error.response?.status === 401 ||
        (error.response?.status === 422 && error.response?.data?.msg?.includes('token'))) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.$toast) {
        window.$toast('Sitzung abgelaufen. Bitte neu anmelden.', 'warning')
      }
      window.location.href = '/login'
    } else if (error.response?.status >= 500) {
      // Server errors
      if (window.$toast) {
        window.$toast('Serverfehler. Bitte später erneut versuchen.', 'error')
      }
    } else if (error.response?.status === 400 || error.response?.status === 422) {
      // Validation errors - show specific message
      const message = error.response?.data?.error || 'Ungültige Eingabe'
      if (window.$toast) {
        window.$toast(message, 'error')
      }
    }
    return Promise.reject(error)
  }
)

export default api
