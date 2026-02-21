import { reactive } from 'vue'
import api from '../api/client'

// Safe localStorage JSON parse with corruption handling
function safeParseUser() {
  try {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  } catch {
    // Clear corrupted data
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    return null
  }
}

// Helper to decode token expiration
function getExpiration(token) {
  if (!token) return null
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(window.atob(parts[1]))
    return payload.exp ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export const authStore = reactive({
  user: safeParseUser(),
  token: localStorage.getItem('token'),
  tokenExpiration: getExpiration(localStorage.getItem('token')),

  setToken(token) {
    this.token = token
    this.tokenExpiration = getExpiration(token)
    localStorage.setItem('token', token)
  },

  async login(email, password) {
    const { data } = await api.silent.post('/auth/login', { email, password })
    this.setToken(data.access_token)
    this.user = data.user
    localStorage.setItem('user', JSON.stringify(data.user))
  },

  async register(email, password, full_name) {
    const { data } = await api.post('/auth/register', { email, password, full_name })
    // Store email for verification page
    localStorage.setItem('pendingVerificationEmail', email)
    return data
  },

  async loginWithGoogle(credential) {
    const { data } = await api.silent.post('/auth/google', { credential })
    this.setToken(data.access_token)
    this.user = data.user
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  },

  async sendVerificationEmail() {
    await api.post('/auth/send-verification')
  },

  async fetchUser() {
    const { data } = await api.get('/auth/me')
    this.user = data
    localStorage.setItem('user', JSON.stringify(data))
  },

  async logout() {
    try {
      // Call logout endpoint to invalidate token on server
      if (this.token) {
        await api.post('/auth/logout')
      }
    } catch (error) {
      // Even if server logout fails, clear local state
      console.warn('Server logout failed:', error)
    } finally {
      // Always clear local state
      this.clearAuthState()
    }
  },

  isAuthenticated() {
    if (!this.token) {
      return false
    }

    // Optimization: check cached expiration
    if (this.tokenExpiration) {
      if (this.tokenExpiration < Date.now()) {
        this.clearAuthState()
        return false
      }
      return true
    }

    try {
      // Check if token is a valid JWT structure (3 parts separated by dots)
      const parts = this.token.split('.')
      if (parts.length !== 3) {
        this.clearAuthState()
        return false
      }

      // Decode the payload to check expiration
      const payload = JSON.parse(window.atob(parts[1]))

      // Check if token is expired (exp is in seconds, Date.now() is in milliseconds)
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        this.clearAuthState()
        return false
      }

      return true
    } catch (error) {
      // If parsing fails, token is invalid
      console.warn('Invalid token format:', error)
      this.clearAuthState()
      return false
    }
  },

  clearAuthState() {
    this.user = null
    this.token = null
    this.tokenExpiration = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
})
