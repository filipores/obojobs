/**
 * Job Recommendations Composable
 *
 * Handles job search, recommendations, and dashboard state.
 */

import { ref, computed, readonly } from 'vue'
import api from '../api/client'

const recommendations = ref([])
const searchResults = ref([])
const stats = ref(null)
const isLoading = ref(false)
const isSearching = ref(false)
const error = ref(null)
const searchFilters = ref({
  location: '',
  working_time: '',
  max_results: 10
})

const activeRecommendations = computed(() =>
  recommendations.value.filter(r => !r.dismissed && !r.applied)
)

const hasSkillsError = computed(() =>
  error.value?.toLowerCase().includes('keine skills')
)

function extractErrorMessage(err) {
  return err.response?.data?.error || err.message
}

async function fetchRecommendations() {
  isLoading.value = true
  error.value = null

  try {
    const { data } = await api.get('/recommendations')
    recommendations.value = data.recommendations || []
    return data.recommendations
  } catch (err) {
    error.value = extractErrorMessage(err)
    throw err
  } finally {
    isLoading.value = false
  }
}

async function fetchStats() {
  try {
    const { data } = await api.get('/recommendations/stats')
    stats.value = data
    return data
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

async function searchJobs(filters = {}) {
  isSearching.value = true
  error.value = null
  searchResults.value = []

  const payload = {
    location: filters.location || searchFilters.value.location,
    working_time: filters.working_time || searchFilters.value.working_time,
    max_results: filters.max_results || searchFilters.value.max_results,
  }

  try {
    const { data } = await api.post('/recommendations/search', payload)
    if (data.success) {
      searchResults.value = data.data.results || []
      // Reload recommendations and stats after search (new ones may have been saved)
      await Promise.all([fetchRecommendations(), fetchStats()])
      return data.data
    }
    throw new Error('Search failed')
  } catch (err) {
    error.value = extractErrorMessage(err)
    throw err
  } finally {
    isSearching.value = false
  }
}

async function dismissRecommendation(id) {
  try {
    await api.post(`/recommendations/${id}/dismiss`)
    recommendations.value = recommendations.value.filter(r => r.id !== id)
    await fetchStats()
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

async function markAsApplied(id) {
  try {
    await api.post(`/recommendations/${id}/apply`)
    const rec = recommendations.value.find(r => r.id === id)
    if (rec) rec.applied = true
    await fetchStats()
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

async function deleteRecommendation(id) {
  try {
    await api.delete(`/recommendations/${id}`)
    recommendations.value = recommendations.value.filter(r => r.id !== id)
    await fetchStats()
  } catch (err) {
    error.value = extractErrorMessage(err)
  }
}

export function useJobRecommendations() {
  return {
    recommendations: readonly(recommendations),
    searchResults: readonly(searchResults),
    stats: readonly(stats),
    isLoading: readonly(isLoading),
    isSearching: readonly(isSearching),
    error: readonly(error),
    searchFilters,
    activeRecommendations,
    hasSkillsError,
    fetchRecommendations,
    fetchStats,
    searchJobs,
    dismissRecommendation,
    markAsApplied,
    deleteRecommendation,
  }
}

export default useJobRecommendations
