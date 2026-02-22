import { reactive } from 'vue'
import api from '../api/client'

const STORAGE_KEY = 'obo_seele_state'

function loadState() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

const initialState = loadState()

export const seeleStore = reactive({
  profil: initialState?.profil || null,
  vollstaendigkeit: initialState?.vollstaendigkeit || 0,
  aktiveSession: null,
  aktuelleFragen: [],
  loading: false,
  nudgeDismissed: initialState?.nudgeDismissed || false,

  async fetchProfil() {
    try {
      const { data } = await api.get('/seele/profil')
      this.profil = data.profil
      this.vollstaendigkeit = data.vollstaendigkeit || 0
      this._save()
    } catch (error) {
      if (error.response?.status !== 404) {
        console.error('Seele profil fetch error:', error)
      }
    }
  },

  async starteSession(typ, kontext = null) {
    this.loading = true
    try {
      const { data } = await api.post('/seele/sessions', { typ, kontext })
      this.aktiveSession = data.session
      this.aktuelleFragen = data.fragen || []
      return data
    } catch (error) {
      console.error('Session start error:', error)
      throw error
    } finally {
      this.loading = false
    }
  },

  async beantworte(sessionId, frageKey, antwort) {
    try {
      const { data } = await api.post('/seele/antworten', {
        session_id: sessionId,
        frage_key: frageKey,
        antwort
      })
      this.aktuelleFragen = data.naechste_fragen || []
      if (data.profil) {
        this.profil = data.profil
        this.vollstaendigkeit = data.vollstaendigkeit || 0
        this._save()
      }
      return data
    } catch (error) {
      console.error('Answer error:', error)
      throw error
    }
  },

  async ueberspringen(sessionId, frageKey) {
    try {
      const { data } = await api.post('/seele/antworten/ueberspringen', {
        session_id: sessionId,
        frage_key: frageKey
      })
      this.aktuelleFragen = data.naechste_fragen || []
      return data
    } catch (error) {
      console.error('Skip error:', error)
      throw error
    }
  },

  async checkTrigger(trigger) {
    try {
      const { data } = await api.get(`/seele/check?trigger=${trigger}`)
      return data.empfohlen || false
    } catch {
      return false
    }
  },

  dismissNudge() {
    this.nudgeDismissed = true
    this._save()
  },

  _save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        profil: this.profil,
        vollstaendigkeit: this.vollstaendigkeit,
        nudgeDismissed: this.nudgeDismissed
      }))
    } catch { /* ignore */ }
  },

  clear() {
    this.profil = null
    this.vollstaendigkeit = 0
    this.aktiveSession = null
    this.aktuelleFragen = []
    this.nudgeDismissed = false
    localStorage.removeItem(STORAGE_KEY)
  }
})
