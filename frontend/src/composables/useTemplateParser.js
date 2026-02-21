/**
 * Template Parser Composable
 *
 * Parses template content with {{VARIABLE}} syntax into structured segments
 * and serializes segments back to plain text.
 */

import { ref, computed } from 'vue'

// Available variable types with their metadata
export const VARIABLE_TYPES = {
  FIRMA: {
    label: 'Firma',
    description: 'Firmenname',
    color: 'ai'
  },
  POSITION: {
    label: 'Position',
    description: 'Stellenbezeichnung',
    color: 'success'
  },
  ANSPRECHPARTNER: {
    label: 'Ansprechpartner',
    description: 'Anrede mit Namen',
    color: 'warning'
  },
  QUELLE: {
    label: 'Quelle',
    description: 'Wo die Stelle gefunden wurde',
    color: 'terra'
  },
  EINLEITUNG: {
    label: 'Einleitung',
    description: 'KI-generierte Einleitung',
    color: 'bamboo'
  }
}

// Maximum allowed template size (500KB)
const MAX_TEMPLATE_SIZE = 500000

let segmentIdCounter = 0

function generateSegmentId() {
  return `seg_${++segmentIdCounter}_${Date.now()}`
}

/**
 * Parse plain text template into structured segments
 * @param {string} plainText - Template text with {{VARIABLE}} placeholders
 * @returns {Array} Array of segment objects
 * @throws {Error} If template exceeds maximum size
 */
export function parseTemplate(plainText) {
  if (!plainText) return []

  // Validate input size to prevent performance issues
  if (plainText.length > MAX_TEMPLATE_SIZE) {
    plainText = plainText.slice(0, MAX_TEMPLATE_SIZE)
  }

  const regex = /\{\{(\w+)\}\}/g
  const segments = []
  let lastIndex = 0
  let match

  while ((match = regex.exec(plainText)) !== null) {
    // Add text before this variable
    if (match.index > lastIndex) {
      segments.push({
        id: generateSegmentId(),
        type: 'text',
        content: plainText.slice(lastIndex, match.index)
      })
    }

    // Add the variable segment
    const variableType = match[1]
    if (VARIABLE_TYPES[variableType]) {
      segments.push({
        id: generateSegmentId(),
        type: 'variable',
        variableType: variableType
      })
    } else {
      // Unknown variable, treat as text
      segments.push({
        id: generateSegmentId(),
        type: 'text',
        content: match[0]
      })
    }

    lastIndex = regex.lastIndex
  }

  // Add remaining text after last variable
  if (lastIndex < plainText.length) {
    segments.push({
      id: generateSegmentId(),
      type: 'text',
      content: plainText.slice(lastIndex)
    })
  }

  return segments
}

/**
 * Serialize segment array back to plain text
 * @param {Array} segments - Array of segment objects
 * @returns {string} Plain text with {{VARIABLE}} placeholders
 */
export function serializeTemplate(segments) {
  return segments.map(seg => {
    if (seg.type === 'variable') {
      return `{{${seg.variableType}}}`
    }
    return seg.content || ''
  }).join('')
}

/**
 * Apply suggestions to segments, marking suggested text portions
 * @param {Array} segments - Current segments
 * @param {Array} suggestions - Suggestions from AI
 * @returns {Array} Segments with suggestion markers
 */
export function applySuggestions(segments, suggestions) {
  if (!suggestions || suggestions.length === 0) return segments

  // Convert segments to plain text with position tracking
  let plainText = ''
  const segmentPositions = []

  segments.forEach((seg, index) => {
    const start = plainText.length
    const content = seg.type === 'variable' ? `{{${seg.variableType}}}` : seg.content
    plainText += content
    segmentPositions.push({
      segmentIndex: index,
      start,
      end: plainText.length,
      segment: seg
    })
  })

  // Find and mark suggestions
  const newSegments = []
  let processedIndex = 0

  // Filter valid suggestions and sort by position in text
  const sortedSuggestions = [...suggestions]
    .filter(s => s.text && typeof s.text === 'string' && plainText.includes(s.text))
    .sort((a, b) => {
      const posA = plainText.indexOf(a.text)
      const posB = plainText.indexOf(b.text)
      return posA - posB
    })

  for (const suggestion of sortedSuggestions) {
    const startIndex = plainText.indexOf(suggestion.text, processedIndex)
    if (startIndex === -1) continue

    const endIndex = startIndex + suggestion.text.length

    // Add text before suggestion
    if (startIndex > processedIndex) {
      newSegments.push({
        id: generateSegmentId(),
        type: 'text',
        content: plainText.slice(processedIndex, startIndex)
      })
    }

    // Add suggestion segment
    newSegments.push({
      id: suggestion.id || generateSegmentId(),
      type: 'suggestion',
      content: suggestion.text,
      suggestedVariable: suggestion.suggestedVariable || suggestion.variable,
      reason: suggestion.reason
    })

    processedIndex = endIndex
  }

  // Add remaining text
  if (processedIndex < plainText.length) {
    newSegments.push({
      id: generateSegmentId(),
      type: 'text',
      content: plainText.slice(processedIndex)
    })
  }

  return newSegments.length > 0 ? newSegments : segments
}

/**
 * Accept a suggestion, converting it to a variable
 * @param {Array} segments - Current segments
 * @param {string} suggestionId - ID of suggestion to accept
 * @returns {Array} Updated segments
 */
export function acceptSuggestion(segments, suggestionId) {
  return segments.map(seg => {
    if (seg.id === suggestionId && seg.type === 'suggestion') {
      return {
        id: seg.id,
        type: 'variable',
        variableType: seg.suggestedVariable
      }
    }
    return seg
  })
}

/**
 * Reject a suggestion, converting it to plain text
 * @param {Array} segments - Current segments
 * @param {string} suggestionId - ID of suggestion to reject
 * @returns {Array} Updated segments
 */
export function rejectSuggestion(segments, suggestionId) {
  return segments.map(seg => {
    if (seg.id === suggestionId && seg.type === 'suggestion') {
      return {
        id: seg.id,
        type: 'text',
        content: seg.content
      }
    }
    return seg
  })
}

/**
 * Insert a variable at a specific position in segments
 * @param {Array} segments - Current segments
 * @param {number} segmentIndex - Index of segment to split
 * @param {number} startOffset - Character offset within segment
 * @param {number} endOffset - End character offset
 * @param {string} variableType - Type of variable to insert
 * @returns {Array} Updated segments
 */
export function insertVariable(segments, segmentIndex, startOffset, endOffset, variableType) {
  const newSegments = [...segments]
  const targetSegment = newSegments[segmentIndex]

  if (!targetSegment || targetSegment.type !== 'text') {
    return segments
  }

  const content = targetSegment.content
  const replacements = []

  // Text before selection
  if (startOffset > 0) {
    replacements.push({
      id: generateSegmentId(),
      type: 'text',
      content: content.slice(0, startOffset)
    })
  }

  // The variable
  replacements.push({
    id: generateSegmentId(),
    type: 'variable',
    variableType: variableType
  })

  // Text after selection
  if (endOffset < content.length) {
    replacements.push({
      id: generateSegmentId(),
      type: 'text',
      content: content.slice(endOffset)
    })
  }

  newSegments.splice(segmentIndex, 1, ...replacements)
  return newSegments
}

/**
 * Remove a variable, optionally replacing with placeholder text
 * @param {Array} segments - Current segments
 * @param {string} variableId - ID of variable to remove
 * @returns {Array} Updated segments with variable removed
 */
export function removeVariable(segments, variableId) {
  const newSegments = []

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i]

    if (seg.id === variableId && seg.type === 'variable') {
      // Skip this segment (remove the variable)
      continue
    }

    newSegments.push(seg)
  }

  // Merge adjacent text segments
  return mergeAdjacentTextSegments(newSegments)
}

/**
 * Merge adjacent text segments into single segments
 * @param {Array} segments - Segments to merge
 * @returns {Array} Merged segments
 */
function mergeAdjacentTextSegments(segments) {
  const merged = []

  for (const seg of segments) {
    const last = merged[merged.length - 1]

    if (last && last.type === 'text' && seg.type === 'text') {
      last.content += seg.content
    } else {
      merged.push({ ...seg })
    }
  }

  return merged
}

/**
 * Composable for managing template state
 */
export function useTemplateParser(initialContent = '') {
  const segments = ref(parseTemplate(initialContent))

  const plainText = computed(() => serializeTemplate(segments.value))

  const hasSuggestions = computed(() =>
    segments.value.some(seg => seg.type === 'suggestion')
  )

  const pendingSuggestions = computed(() =>
    segments.value.filter(seg => seg.type === 'suggestion')
  )

  function setContent(content) {
    segments.value = parseTemplate(content)
  }

  function updateSegments(newSegments) {
    segments.value = newSegments
  }

  function applySuggestionsToContent(suggestions) {
    segments.value = applySuggestions(segments.value, suggestions)
  }

  function acceptSuggestionById(suggestionId) {
    segments.value = acceptSuggestion(segments.value, suggestionId)
  }

  function rejectSuggestionById(suggestionId) {
    segments.value = rejectSuggestion(segments.value, suggestionId)
  }

  function insertVariableAt(segmentIndex, startOffset, endOffset, variableType) {
    segments.value = insertVariable(segments.value, segmentIndex, startOffset, endOffset, variableType)
  }

  function removeVariableById(variableId) {
    segments.value = removeVariable(segments.value, variableId)
  }

  function acceptAllSuggestions() {
    let updated = segments.value
    for (const seg of segments.value) {
      if (seg.type === 'suggestion') {
        updated = acceptSuggestion(updated, seg.id)
      }
    }
    segments.value = updated
  }

  function rejectAllSuggestions() {
    let updated = segments.value
    for (const seg of segments.value) {
      if (seg.type === 'suggestion') {
        updated = rejectSuggestion(updated, seg.id)
      }
    }
    segments.value = updated
  }

  return {
    segments,
    plainText,
    hasSuggestions,
    pendingSuggestions,
    setContent,
    updateSegments,
    applySuggestionsToContent,
    acceptSuggestionById,
    rejectSuggestionById,
    insertVariableAt,
    removeVariableById,
    acceptAllSuggestions,
    rejectAllSuggestions
  }
}

export default useTemplateParser
