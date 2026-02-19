import { ref, computed } from 'vue'
import api from '../api/client'
import { getFullLocale } from '../i18n'

const DEFAULT_MODEL = 'qwen'

const WORK_TYPE_MAP = {
  vollzeit: 'vz',
  teilzeit: 'tz',
  remote: 'ho',
}

const SOURCE_LABELS = {
  indeed: 'Indeed',
  stepstone: 'StepStone',
  xing: 'XING',
  arbeitsagentur: 'Arbeitsagentur',
  generic: 'Web',
}

/**
 * Streams a cover letter generation via SSE from the backend.
 * Returns the complete event payload on success, or throws on error.
 */
async function streamGeneration(payload, onProgress) {
  const token = localStorage.getItem('token')
  const response = await fetch('/api/applications/generate-from-url-stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    const errorData = await response.json()
    throw new Error(errorData.error || 'Fehler bei der Generierung')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) throw new Error('Fehler bei der Generierung')

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop()

    for (const chunk of chunks) {
      if (!chunk.startsWith('data: ')) continue

      let event
      try { event = JSON.parse(chunk.slice(6)) } catch { continue }

      if (event.type === 'complete') {
        if (event.success === false) {
          throw new Error(event.error || 'Fehler bei der Generierung')
        }
        return event
      }
      if (event.type === 'error') {
        throw new Error(event.error || 'Fehler bei der Generierung')
      }
      if (event.step && event.message && typeof onProgress === 'function') {
        onProgress(event.message)
      }
    }
  }
}

// Shared state (module-level singleton)
const suggestions = ref([])
const stats = ref(null)
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(false)
const filters = ref({
  location: '',
  workType: ''
})
const hasSkills = ref(true)
const page = ref(1)
const perPage = 12
const generatingIds = ref(new Set())
const searching = ref(false)
const error = ref(null)

export function useJobRecommendations() {
  const filteredSuggestions = computed(() => {
    let result = suggestions.value
    if (filters.value.location) {
      const loc = filters.value.location.toLowerCase()
      result = result.filter(r =>
        r.location && r.location.toLowerCase().includes(loc)
      )
    }
    if (filters.value.workType) {
      const wt = filters.value.workType.toLowerCase()
      result = result.filter(r =>
        r.work_type && r.work_type.toLowerCase().includes(wt)
      )
    }
    return result
  })

  function addDefaultModel(recommendations) {
    return (recommendations || []).map(r => ({ ...r, model: r.model || DEFAULT_MODEL }))
  }

  async function loadSuggestions() {
    loading.value = true
    error.value = null
    page.value = 1
    try {
      const skillsRes = await api.silent.get('/users/me/skills')
      const userSkills = skillsRes.data.skills || []
      if (userSkills.length === 0) {
        hasSkills.value = false
        suggestions.value = []
        loading.value = false
        return
      }
      hasSkills.value = true

      const { data } = await api.get('/recommendations', {
        params: { limit: perPage }
      })
      suggestions.value = addDefaultModel(data.recommendations)
      hasMore.value = suggestions.value.length >= perPage
    } catch (err) {
      error.value = err.message || 'Fehler beim Laden der Jobs'
      console.error('Failed to load suggestions:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (loadingMore.value || !hasMore.value) return
    loadingMore.value = true
    const offset = suggestions.value.length
    try {
      const { data } = await api.silent.get('/recommendations', {
        params: { limit: perPage, offset }
      })
      const newItems = addDefaultModel(data.recommendations)
      suggestions.value = [...suggestions.value, ...newItems]
      hasMore.value = newItems.length >= perPage
    } catch (err) {
      console.error('Failed to load more:', err)
    } finally {
      loadingMore.value = false
    }
  }

  async function loadStats() {
    try {
      const { data } = await api.silent.get('/recommendations/stats')
      stats.value = data
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  async function dismissSuggestion(id) {
    try {
      await api.post(`/recommendations/${id}/dismiss`)
      suggestions.value = suggestions.value.filter(r => r.id !== id)
      await loadStats()
    } catch (err) {
      console.error('Failed to dismiss:', err)
    }
  }

  async function markAsApplied(id, applicationId) {
    try {
      const body = applicationId ? { application_id: applicationId } : {}
      await api.post(`/recommendations/${id}/apply`, body)
    } catch (err) {
      console.error('Failed to mark as applied:', err)
    }
  }

  function isGenerating(id) {
    return generatingIds.value.has(id)
  }

  async function applyToJob(rec) {
    if (!rec.job_url || generatingIds.value.has(rec.id)) return

    generatingIds.value = new Set([...generatingIds.value, rec.id])
    const toastId = window.$toast?.('Stellenanzeige wird geladen...', 'info', 0)

    function updateToast(msg, type, opts) {
      if (toastId != null && window.$toast?.update) {
        window.$toast.update(toastId, msg, type, opts)
      }
    }

    try {
      const result = await streamGeneration(
        {
          url: rec.job_url,
          tone: 'modern',
          model: rec.model || DEFAULT_MODEL,
          company: rec.company_name || '',
          title: rec.job_title || '',
          fit_score: rec.fit_score,
        },
        (msg) => updateToast(msg, 'info')
      )

      await markAsApplied(rec.id, result.application?.id)
      suggestions.value = suggestions.value.filter(r => r.id !== rec.id)
      await loadStats()

      const firma = rec.company_name || 'das Unternehmen'
      const appId = result.application?.id
      updateToast(`Bewerbung für ${firma} erstellt!`, 'success', {
        action: appId ? { label: 'Details ansehen', route: `/applications/${appId}` } : undefined,
        duration: 8000,
      })
    } catch (e) {
      const errorMsg = e.message || 'Fehler bei der Generierung. Bitte versuche es erneut.'
      updateToast(errorMsg, 'error', { duration: 5000 })
    } finally {
      const next = new Set(generatingIds.value)
      next.delete(rec.id)
      generatingIds.value = next
    }
  }

  function getSourceLabel(source) {
    return SOURCE_LABELS[source] || source
  }

  function formatDate(dateStr) {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString(getFullLocale(), {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  function openJobUrl(url) {
    window.open(url, '_blank')
  }

  async function searchJobs({ location, workType, keywords } = {}) {
    searching.value = true
    try {
      const body = {}
      if (location) body.location = location
      if (workType) body.working_time = WORK_TYPE_MAP[workType] || workType
      if (keywords) body.keywords = keywords
      await api.post('/recommendations/search', body)
      await loadSuggestions()
      await loadStats()
    } catch (err) {
      console.error('Failed to search jobs:', err)
    } finally {
      searching.value = false
    }
  }

  return {
    suggestions,
    filteredSuggestions,
    stats,
    loading,
    loadingMore,
    hasMore,
    filters,
    hasSkills,
    searching,
    error,
    loadSuggestions,
    loadMore,
    loadStats,
    searchJobs,
    dismissSuggestion,
    markAsApplied,
    generatingIds,
    isGenerating,
    applyToJob,
    formatDate,
    getSourceLabel,
    openJobUrl
  }
}

export default useJobRecommendations
