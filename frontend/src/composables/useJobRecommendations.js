import { ref, computed } from 'vue'
import api from '../api/client'

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

  const markAsApplied = async (id) => {
    try {
      await api.post(`/recommendations/${id}/apply`)
    } catch (error) {
      console.error('Failed to mark as applied:', error)
    }
  }

  const searching = ref(false)

  const searchJobs = async () => {
    searching.value = true
    try {
      await api.post('/recommendations/search', {})
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
    markAsApplied
  }
}

export default useJobRecommendations
