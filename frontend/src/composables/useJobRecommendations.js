import { ref, computed } from 'vue'
import api from '../api/client'
import { getFullLocale } from '../i18n'

const WORK_TYPE_MAP = {
  vollzeit: 'vz',
  teilzeit: 'tz',
  remote: 'ho',
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

export function useJobRecommendations() {
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

  const loadSuggestions = async () => {
    loading.value = true
    page.value = 1
    try {
      // Check if user has skills
      const skillsRes = await api.silent.get('/users/me/skills')
      const userSkills = skillsRes.data.skills || []
      if (userSkills.length === 0) {
        hasSkills.value = false
        suggestions.value = []
        loading.value = false
        return
      }
      hasSkills.value = true

      const { data } = await api.silent.get('/recommendations', {
        params: { limit: perPage }
      })
      suggestions.value = data.recommendations || []
      hasMore.value = suggestions.value.length >= perPage
    } catch (error) {
      console.error('Failed to load suggestions:', error)
    } finally {
      loading.value = false
    }
  }

  const loadMore = async () => {
    if (loadingMore.value || !hasMore.value) return
    loadingMore.value = true
    page.value++
    try {
      const { data } = await api.silent.get('/recommendations', {
        params: { limit: perPage * page.value }
      })
      const all = data.recommendations || []
      if (all.length <= suggestions.value.length) {
        hasMore.value = false
      } else {
        suggestions.value = all
        hasMore.value = all.length >= perPage * page.value
      }
    } catch (error) {
      console.error('Failed to load more:', error)
    } finally {
      loadingMore.value = false
    }
  }

  const loadStats = async () => {
    try {
      const { data } = await api.silent.get('/recommendations/stats')
      stats.value = data
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const dismissSuggestion = async (id) => {
    try {
      await api.post(`/recommendations/${id}/dismiss`)
      suggestions.value = suggestions.value.filter(r => r.id !== id)
      await loadStats()
    } catch (error) {
      console.error('Failed to dismiss:', error)
    }
  }

  const markAsApplied = async (id, applicationId) => {
    try {
      const body = applicationId ? { application_id: applicationId } : {}
      await api.post(`/recommendations/${id}/apply`, body)
    } catch (error) {
      console.error('Failed to mark as applied:', error)
    }
  }

  const generatingIds = ref(new Set())

  const isGenerating = (id) => generatingIds.value.has(id)

  const applyToJob = async (rec) => {
    if (!rec.job_url || generatingIds.value.has(rec.id)) return

    generatingIds.value = new Set([...generatingIds.value, rec.id])
    const toastId = window.$toast?.('Stellenanzeige wird geladen...', 'info', 0)
    const updateToast = (msg, type, opts) => {
      if (toastId != null && window.$toast?.update) {
        window.$toast.update(toastId, msg, type, opts)
      }
    }

    try {
      const result = await streamGeneration(
        {
          url: rec.job_url,
          tone: 'modern',
          company: rec.company_name || '',
          title: rec.job_title || '',
          fit_score: rec.fit_score ?? undefined,
        },
        (message) => updateToast(message)
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

  const SOURCE_LABELS = {
    indeed: 'Indeed',
    stepstone: 'StepStone',
    xing: 'XING',
    arbeitsagentur: 'Arbeitsagentur',
    generic: 'Web',
  }

  const getSourceLabel = (source) => SOURCE_LABELS[source] || source

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString(getFullLocale(), {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const openJobUrl = (url) => {
    window.open(url, '_blank')
  }

  const searching = ref(false)

  const searchJobs = async ({ location, workType, keywords } = {}) => {
    searching.value = true
    try {
      const body = {}
      if (location) body.location = location
      if (workType) body.working_time = WORK_TYPE_MAP[workType] || workType
      if (keywords) body.keywords = keywords
      await api.post('/recommendations/search', body)
      await loadSuggestions()
      await loadStats()
    } catch (error) {
      console.error('Failed to search jobs:', error)
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
