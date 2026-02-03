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

  // CV text extracted from uploaded PDF (for post-registration direct generation)
  cvText: initialState?.cvText || null,

  // Original CV filename for UI display
  cvFileName: initialState?.cvFileName || null,

  // Preview data from demo generation
  previewData: initialState?.previewData || null,

  // PDF blob from demo generation (not persisted to session)
  pdfBlob: null,

  // Current crafting phase (0-4)
  craftingPhase: 0,

  /**
   * Store demo completion data before redirecting to register
   */
  setDemoComplete(jobUrl, result) {
    this.jobUrl = jobUrl
    this.demoResult = result
    this.postRegistrationFlow = true
    this.regeneratedResult = null
    this._saveToSession()
  },

  /**
   * Store CV data for post-registration direct generation
   */
  setCvData(cvText, fileName) {
    this.cvText = cvText
    this.cvFileName = fileName
    this._saveToSession()
  },

  /**
   * Store preview data from demo generation
   */
  setPreviewData(data) {
    this.previewData = data
    this._saveToSession()
  },

  /**
   * Store PDF blob from demo generation
   */
  setPdfBlob(blob) {
    this.pdfBlob = blob
    this._saveToSession()
  },

  /**
   * Set current crafting phase
   */
  setCraftingPhase(phase) {
    this.craftingPhase = phase
  },

  /**
   * Internal method to save all state to session
   */
  _saveToSession() {
    saveState({
      jobUrl: this.jobUrl,
      demoResult: this.demoResult,
      postRegistrationFlow: this.postRegistrationFlow,
      regeneratedResult: this.regeneratedResult,
      cvText: this.cvText,
      cvFileName: this.cvFileName,
      previewData: this.previewData
    })
  },

  /**
   * Store the regenerated result after CV upload
   */
  setRegeneratedResult(result) {
    this.regeneratedResult = result
    this._saveToSession()
  },

  /**
   * Check if we're in the demo-to-registration flow
   */
  isInDemoFlow() {
    return this.postRegistrationFlow && this.jobUrl
  },

  /**
   * Check if we have CV data stored
   */
  hasCvData() {
    return !!this.cvText
  },

  /**
   * Clear all demo state (after completing the flow or abandoning it)
   */
  clear() {
    this.jobUrl = null
    this.demoResult = null
    this.postRegistrationFlow = false
    this.regeneratedResult = null
    this.cvText = null
    this.cvFileName = null
    this.previewData = null
    this.pdfBlob = null
    this.craftingPhase = 0
    sessionStorage.removeItem(STORAGE_KEY)
  }
})
