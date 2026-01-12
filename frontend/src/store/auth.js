import { reactive } from 'vue'
import api from '../api/client'

export const authStore = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token'),

  async login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    this.token = data.access_token
    this.user = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
  },

  async register(email, password, full_name) {
    const { data } = await api.post('/auth/register', { email, password, full_name })
    // Store email for verification page
    localStorage.setItem('pendingVerificationEmail', email)
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

  logout() {
    this.user = null
    this.token = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  isAuthenticated() {
    return !!this.token
  }
})
