import { reactive } from 'vue'

/**
 * Demo store - persists demo job URL for auto-regeneration after registration
 *
 * Flow:
 * 1. User completes demo with a job URL (anonymous)
 * 2. URL is stored here before redirecting to register
 * 3. After registration + CV upload, we regenerate with real CV for the same job
 * 4. User sees their REAL personalized application
 */

const STORAGE_KEY = 'obo_demo_state'

// Load from sessionStorage (persists across page refreshes, clears on tab close)
function loadState() {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

function saveState(state) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Ignore storage errors
  }
}

const initialState = loadState()

export const demoStore = reactive({
  // The job URL from the demo
  jobUrl: initialState?.jobUrl || null,

  // The demo result (cover letter, job info) before registration
  demoResult: initialState?.demoResult || null,

  // Whether we're in post-registration CV upload flow
  postRegistrationFlow: initialState?.postRegistrationFlow || false,

  // The regenerated result after CV upload
  regeneratedResult: initialState?.regeneratedResult || null,

  /**
   * Store demo completion data before redirecting to register
   */
  setDemoComplete(jobUrl, result) {
    this.jobUrl = jobUrl
    this.demoResult = result
    this.postRegistrationFlow = true
    this.regeneratedResult = null
    saveState({
      jobUrl: this.jobUrl,
      demoResult: this.demoResult,
      postRegistrationFlow: true,
      regeneratedResult: null
    })
  },

  /**
   * Store the regenerated result after CV upload
   */
  setRegeneratedResult(result) {
    this.regeneratedResult = result
    saveState({
      jobUrl: this.jobUrl,
      demoResult: this.demoResult,
      postRegistrationFlow: this.postRegistrationFlow,
      regeneratedResult: result
    })
  },

  /**
   * Check if we're in the demo-to-registration flow
   */
  isInDemoFlow() {
    return this.postRegistrationFlow && this.jobUrl
  },

  /**
   * Clear all demo state (after completing the flow or abandoning it)
   */
  clear() {
    this.jobUrl = null
    this.demoResult = null
    this.postRegistrationFlow = false
    this.regeneratedResult = null
    sessionStorage.removeItem(STORAGE_KEY)
  }
})
