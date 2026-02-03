/**
 * Template Preview Composable
 *
 * Provides example job data and generates live preview text
 * by substituting template variables with realistic example values.
 */

import { ref, computed } from 'vue'
import { VARIABLE_TYPES } from './useTemplateParser'

// Default example data for preview
const DEFAULT_PREVIEW_DATA = {
  FIRMA: 'Muster GmbH',
  POSITION: 'Software-Entwickler',
  ANSPRECHPARTNER: 'Frau Müller',
  QUELLE: 'LinkedIn',
  EINLEITUNG: 'Mit großem Interesse habe ich Ihre Stellenausschreibung auf LinkedIn entdeckt und möchte mich bei Ihnen als engagierter Software-Entwickler bewerben.'
}

/**
 * Generate preview text by replacing variables with example values
 * @param {string} templateContent - Template text with {{VARIABLE}} placeholders
 * @param {Object} previewData - Object mapping variable names to example values
 * @returns {string} Preview text with variables replaced
 */
export function generatePreview(templateContent, previewData = DEFAULT_PREVIEW_DATA) {
  if (!templateContent) return ''

  let text = templateContent
  for (const [key, value] of Object.entries(previewData)) {
    text = text.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value)
  }
  return text
}

/**
 * Get the list of variables used in a template
 * @param {string} templateContent - Template text with {{VARIABLE}} placeholders
 * @returns {Array<string>} Array of unique variable names found
 */
export function getUsedVariables(templateContent) {
  if (!templateContent) return []

  const matches = templateContent.match(/\{\{([A-Z_]+)\}\}/g)
  if (!matches) return []

  return [...new Set(matches.map(m => m.replace(/\{\{|\}\}/g, '')))]
}

/**
 * Composable for managing template preview state
 * @param {Ref<string>} templateContent - Reactive template content
 * @param {Object} customPreviewData - Optional custom preview data
 * @returns {Object} Preview state and methods
 */
export function useTemplatePreview(templateContent, customPreviewData = null) {
  const previewData = ref(customPreviewData || { ...DEFAULT_PREVIEW_DATA })

  // Computed preview text that updates when template or preview data changes
  const previewText = computed(() => {
    return generatePreview(templateContent.value, previewData.value)
  })

  // List of variables used in the template
  const usedVariables = computed(() => {
    return getUsedVariables(templateContent.value)
  })

  // Check if template has any variables
  const hasVariables = computed(() => {
    return usedVariables.value.length > 0
  })

  // Get variable info for used variables (for legend display)
  const variableLegend = computed(() => {
    return usedVariables.value.map(varName => ({
      name: varName,
      label: VARIABLE_TYPES[varName]?.label || varName,
      value: previewData.value[varName] || `{{${varName}}}`,
      color: VARIABLE_TYPES[varName]?.color || 'ai'
    }))
  })

  // Update a specific preview value
  function setPreviewValue(variableName, value) {
    previewData.value = {
      ...previewData.value,
      [variableName]: value
    }
  }

  // Reset preview data to defaults
  function resetPreviewData() {
    previewData.value = { ...DEFAULT_PREVIEW_DATA }
  }

  // Update all preview data at once
  function setPreviewData(data) {
    previewData.value = { ...previewData.value, ...data }
  }

  return {
    previewData,
    previewText,
    usedVariables,
    hasVariables,
    variableLegend,
    setPreviewValue,
    resetPreviewData,
    setPreviewData
  }
}

export { DEFAULT_PREVIEW_DATA }
export default useTemplatePreview
