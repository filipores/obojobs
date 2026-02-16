import { ref, computed } from 'vue'
import api from '../api/client'
import { getFullLocale } from '../i18n'

const WORK_TYPE_MAP = {
  vollzeit: 'vz',
  teilzeit: 'tz',
  remote: 'ho',
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

    if (window.$toast) {
      window.$toast(`Bewerbung für ${rec.company_name || 'diese Stelle'} wird erstellt...`, 'info', 30000)
    }

    try {
      const { data } = await api.post('/applications/generate-from-url', {
        url: rec.job_url,
        tone: 'modern'
      })

      if (data.success) {
        await markAsApplied(rec.id, data.application?.id)
        suggestions.value = suggestions.value.filter(r => r.id !== rec.id)
        await loadStats()

        if (window.$toast) {
          window.$toast('Bewerbung erstellt! Unter "Bewerbungen" einsehen.', 'success', 5000)
        }
      } else {
        if (window.$toast) {
          window.$toast(data.error || 'Fehler bei der Generierung', 'error')
        }
      }
    } catch (e) {
      const errorMsg = e.response?.data?.error || 'Fehler bei der Generierung. Bitte versuche es erneut.'
      if (window.$toast) {
        window.$toast(errorMsg, 'error')
      }
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
