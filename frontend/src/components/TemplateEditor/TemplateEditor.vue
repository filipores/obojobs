<template>
  <div class="template-editor-wrapper">
    <!-- Variable insert panel -->
    <VariablePanel @insert="handleInsertVariable" />

    <!-- Suggestions banner -->
    <Transition name="banner">
      <div v-if="hasSuggestions" class="suggestions-banner">
        <div class="banner-content">
          <span class="banner-icon">&#10024;</span>
          <span class="banner-text">
            {{ pendingSuggestions.length }} KI-Vorschlag{{ pendingSuggestions.length !== 1 ? 'e' : '' }} verfügbar
          </span>
        </div>
        <div class="banner-actions">
          <button class="banner-btn accept-all" @click="handleAcceptAll">
            Alle annehmen
          </button>
          <button class="banner-btn reject-all" @click="handleRejectAll">
            Alle ablehnen
          </button>
        </div>
      </div>
    </Transition>

    <!-- Main editor -->
    <div
      ref="editorRef"
      class="template-editor"
      :class="{ 'has-suggestions': hasSuggestions, 'drag-over': isDragOver }"
      contenteditable="true"
      :placeholder="placeholder"
      @input="handleInput"
      @mouseup="handleMouseUp"
      @keyup="handleKeyUp"
      @paste="handlePaste"
      @blur="handleBlur"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    ></div>

    <!-- Character count -->
    <div class="editor-footer">
      <span class="char-count">{{ charCount }} Zeichen</span>
      <span v-if="hasSuggestions" class="suggestions-hint">
        Klicke auf markierte Passagen, um Vorschläge anzunehmen oder abzulehnen
      </span>
    </div>

    <!-- Variable dropdown -->
    <VariableDropdown
      :show="showDropdown"
      :position="dropdownPosition"
      :selected-text="selectedText"
      @select="handleVariableSelect"
      @close="closeDropdown"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
// VariableChip and SuggestionChip are created dynamically in createVariableChipElement/createSuggestionChipElement
import _VariableChip from './VariableChip.vue'
import _SuggestionChip from './SuggestionChip.vue'
import VariableDropdown from './VariableDropdown.vue'
import VariablePanel from './VariablePanel.vue'
import {
  useTemplateParser,
  parseTemplate as _parseTemplate,
  serializeTemplate as _serializeTemplate,
  VARIABLE_TYPES
} from '../../composables/useTemplateParser'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  suggestions: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Schreibe dein Anschreiben hier...'
  }
})

const emit = defineEmits(['update:modelValue', 'suggestion-accepted', 'suggestion-rejected'])

// Template parser state
const {
  segments,
  plainText,
  hasSuggestions,
  pendingSuggestions,
  setContent,
  applySuggestionsToContent,
  acceptSuggestionById,
  rejectSuggestionById,
  acceptAllSuggestions,
  rejectAllSuggestions
} = useTemplateParser(props.modelValue)

// Local state
const editorRef = ref(null)
const showDropdown = ref(false)
const dropdownPosition = ref({ top: 0, left: 0 })
const selectedText = ref('')
const selectedRange = ref(null)
const isRendering = ref(false)
const lastEmittedValue = ref('')
const isInternalUpdate = ref(false)
const isDragOver = ref(false)

const charCount = computed(() => plainText.value.length)

// Watch for external changes (from parent component)
watch(() => props.modelValue, (newValue) => {
  // Skip if this is our own emit or during rendering
  if (isRendering.value || newValue === lastEmittedValue.value) {
    return
  }

  // Only update if value actually changed from external source
  if (newValue !== plainText.value) {
    isInternalUpdate.value = true
    setContent(newValue)
    renderEditor()
    isInternalUpdate.value = false
  }
})

// Watch for suggestions
watch(() => props.suggestions, (newSuggestions) => {
  if (newSuggestions && newSuggestions.length > 0) {
    applySuggestionsToContent(newSuggestions)
    renderEditor()
  }
}, { immediate: true })

// Emit changes when segments change (from user input)
watch(plainText, (newValue) => {
  // Only emit if this is a user-driven change, not from external prop update
  if (!isInternalUpdate.value && newValue !== props.modelValue) {
    lastEmittedValue.value = newValue
    emit('update:modelValue', newValue)
  }
})

// Render the editor content from segments
function renderEditor() {
  if (!editorRef.value) return

  isRendering.value = true

  // Save cursor position
  const savedSelection = saveSelection()

  // Clear and rebuild content
  editorRef.value.innerHTML = ''

  for (const segment of segments.value) {
    if (segment.type === 'text') {
      // Create text node
      const textNode = document.createTextNode(segment.content)
      editorRef.value.appendChild(textNode)
    } else if (segment.type === 'variable') {
      // Create variable chip
      const chip = createVariableChipElement(segment)
      editorRef.value.appendChild(chip)
    } else if (segment.type === 'suggestion') {
      // Create suggestion chip
      const chip = createSuggestionChipElement(segment)
      editorRef.value.appendChild(chip)
    }
  }

  // Restore cursor position
  nextTick(() => {
    restoreSelection(savedSelection)
    isRendering.value = false
  })
}

function createVariableChipElement(segment) {
  const chip = document.createElement('span')
  chip.className = 'variable-chip'
  chip.setAttribute('data-type', segment.variableType)
  chip.setAttribute('data-segment-id', segment.id)
  chip.setAttribute('contenteditable', 'false')
  chip.setAttribute('title', VARIABLE_TYPES[segment.variableType]?.description || '')

  const label = document.createElement('span')
  label.className = 'chip-label'
  label.textContent = VARIABLE_TYPES[segment.variableType]?.label || segment.variableType
  chip.appendChild(label)

  const removeBtn = document.createElement('button')
  removeBtn.className = 'chip-remove'
  removeBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
  removeBtn.title = 'Variable entfernen'
  removeBtn.onclick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    removeVariable(segment.id)
  }
  chip.appendChild(removeBtn)

  return chip
}

function createSuggestionChipElement(segment) {
  const chip = document.createElement('span')
  chip.className = 'suggestion-chip'
  chip.setAttribute('data-type', segment.suggestedVariable)
  chip.setAttribute('data-segment-id', segment.id)
  chip.setAttribute('contenteditable', 'false')

  const icon = document.createElement('span')
  icon.className = 'suggestion-icon'
  icon.innerHTML = '&#10024;'
  chip.appendChild(icon)

  const content = document.createElement('span')
  content.className = 'suggestion-content'
  content.textContent = segment.content
  chip.appendChild(content)

  const badge = document.createElement('span')
  badge.className = 'suggestion-badge'
  badge.textContent = VARIABLE_TYPES[segment.suggestedVariable]?.label || segment.suggestedVariable
  chip.appendChild(badge)

  const actions = document.createElement('span')
  actions.className = 'suggestion-actions'

  const acceptBtn = document.createElement('button')
  acceptBtn.className = 'action-btn accept-btn'
  acceptBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>'
  acceptBtn.title = 'Als Variable annehmen'
  acceptBtn.onclick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    handleAcceptSuggestion(segment.id)
  }
  actions.appendChild(acceptBtn)

  const rejectBtn = document.createElement('button')
  rejectBtn.className = 'action-btn reject-btn'
  rejectBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
  rejectBtn.title = 'Vorschlag ablehnen'
  rejectBtn.onclick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    handleRejectSuggestion(segment.id)
  }
  actions.appendChild(rejectBtn)

  chip.appendChild(actions)

  return chip
}

function removeVariable(segmentId) {
  const newSegments = segments.value.filter(s => s.id !== segmentId)
  // Merge adjacent text segments
  const merged = []
  for (const seg of newSegments) {
    const last = merged[merged.length - 1]
    if (last && last.type === 'text' && seg.type === 'text') {
      last.content += seg.content
    } else {
      merged.push({ ...seg })
    }
  }
  segments.value = merged
  renderEditor()
}

function handleAcceptSuggestion(segmentId) {
  acceptSuggestionById(segmentId)
  emit('suggestion-accepted', segmentId)
  renderEditor()
}

function handleRejectSuggestion(segmentId) {
  rejectSuggestionById(segmentId)
  emit('suggestion-rejected', segmentId)
  renderEditor()
}

function handleAcceptAll() {
  acceptAllSuggestions()
  renderEditor()
}

function handleRejectAll() {
  rejectAllSuggestions()
  renderEditor()
}

// Handle text input
function handleInput(_event) {
  if (isRendering.value) return

  // Parse the current content back to segments
  const newPlainText = getPlainTextFromEditor()
  setContent(newPlainText)
}

function getPlainTextFromEditor() {
  if (!editorRef.value) return ''

  let text = ''
  const walker = document.createTreeWalker(
    editorRef.value,
    NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
    null,
    false
  )

  let node
  while ((node = walker.nextNode()) !== null) {
    if (node.nodeType === Node.TEXT_NODE) {
      // Skip text nodes inside chips (already handled by the chip element handlers)
      if (node.parentElement?.closest('.variable-chip') ||
          node.parentElement?.closest('.suggestion-chip')) {
        continue
      }
      text += node.textContent
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.classList?.contains('variable-chip')) {
        const type = node.getAttribute('data-type')
        text += `{{${type}}}`
      } else if (node.classList?.contains('suggestion-chip')) {
        // For suggestions, include the original text
        const contentEl = node.querySelector('.suggestion-content')
        if (contentEl) {
          text += contentEl.textContent
        }
      }
    }
  }

  return text
}

// Handle text selection for variable creation
function handleMouseUp(event) {
  // Don't show dropdown if clicking on chips
  if (event.target.closest('.variable-chip') || event.target.closest('.suggestion-chip')) {
    return
  }

  checkSelection()
}

function handleKeyUp(event) {
  // Check selection on shift+arrow keys
  if (event.shiftKey && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
    checkSelection()
  }
}

function checkSelection() {
  const selection = window.getSelection()

  if (!selection || selection.isCollapsed || selection.toString().trim().length === 0) {
    closeDropdown()
    return
  }

  const range = selection.getRangeAt(0)

  // Check if selection is within our editor
  if (!editorRef.value.contains(range.commonAncestorContainer)) {
    closeDropdown()
    return
  }

  // Check if selection spans multiple segments (we only support single text node selection)
  if (range.startContainer !== range.endContainer) {
    // Selection spans multiple nodes - could be complex, skip for now
    closeDropdown()
    return
  }

  // Check if selection is within a text node
  if (range.startContainer.nodeType !== Node.TEXT_NODE) {
    closeDropdown()
    return
  }

  const text = selection.toString().trim()
  if (text.length === 0) {
    closeDropdown()
    return
  }

  selectedText.value = text
  selectedRange.value = range.cloneRange()

  // Position dropdown near selection
  const rect = range.getBoundingClientRect()
  dropdownPosition.value = {
    top: rect.bottom + window.scrollY + 8,
    left: rect.left + window.scrollX
  }

  showDropdown.value = true
}

function closeDropdown() {
  showDropdown.value = false
  selectedText.value = ''
  selectedRange.value = null
}

function handleVariableSelect(variableType) {
  if (!selectedRange.value) {
    closeDropdown()
    return
  }

  // Insert variable at selection
  const chip = document.createElement('span')
  chip.className = 'variable-chip'
  chip.setAttribute('data-type', variableType)
  chip.setAttribute('data-segment-id', `seg_new_${Date.now()}`)
  chip.setAttribute('contenteditable', 'false')
  chip.setAttribute('title', VARIABLE_TYPES[variableType]?.description || '')

  const label = document.createElement('span')
  label.className = 'chip-label'
  label.textContent = VARIABLE_TYPES[variableType]?.label || variableType
  chip.appendChild(label)

  const removeBtn = document.createElement('button')
  removeBtn.className = 'chip-remove'
  removeBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
  removeBtn.title = 'Variable entfernen'
  chip.appendChild(removeBtn)

  // Replace selection with chip
  selectedRange.value.deleteContents()
  selectedRange.value.insertNode(chip)

  // Update segments from editor
  const newPlainText = getPlainTextFromEditor()
  setContent(newPlainText)

  closeDropdown()

  // Re-render to ensure proper structure
  renderEditor()
}

// Handle inserting variable from panel at cursor position
function handleInsertVariable(variableType) {
  if (!editorRef.value) return

  // Focus the editor first
  editorRef.value.focus()

  const selection = window.getSelection()

  // If no selection or selection is outside editor, append at end
  if (!selection || selection.rangeCount === 0 ||
      !editorRef.value.contains(selection.anchorNode)) {
    // Append variable at end
    const variableText = `{{${variableType}}}`
    const currentContent = getPlainTextFromEditor()
    setContent(currentContent + variableText)
    renderEditor()

    // Place cursor after the inserted variable
    nextTick(() => {
      const sel = window.getSelection()
      const range = document.createRange()
      range.selectNodeContents(editorRef.value)
      range.collapse(false) // collapse to end
      sel.removeAllRanges()
      sel.addRange(range)
    })
    return
  }

  const range = selection.getRangeAt(0)

  // Create variable chip element
  const chip = document.createElement('span')
  chip.className = 'variable-chip'
  chip.setAttribute('data-type', variableType)
  chip.setAttribute('data-segment-id', `seg_new_${Date.now()}`)
  chip.setAttribute('contenteditable', 'false')
  chip.setAttribute('title', VARIABLE_TYPES[variableType]?.description || '')

  const label = document.createElement('span')
  label.className = 'chip-label'
  label.textContent = VARIABLE_TYPES[variableType]?.label || variableType
  chip.appendChild(label)

  const removeBtn = document.createElement('button')
  removeBtn.className = 'chip-remove'
  removeBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
  removeBtn.title = 'Variable entfernen'
  chip.appendChild(removeBtn)

  // If there's selected text, replace it
  if (!range.collapsed) {
    range.deleteContents()
  }

  // Insert chip at cursor position
  range.insertNode(chip)

  // Move cursor after the chip
  range.setStartAfter(chip)
  range.setEndAfter(chip)
  selection.removeAllRanges()
  selection.addRange(range)

  // Update segments from editor
  const newPlainText = getPlainTextFromEditor()
  setContent(newPlainText)

  // Re-render to ensure proper structure
  renderEditor()
}

// Handle paste - strip formatting and use modern API
function handlePaste(event) {
  event.preventDefault()

  const text = event.clipboardData.getData('text/plain')
  const selection = window.getSelection()

  if (!selection || selection.rangeCount === 0) return

  // Delete selected content and insert plain text
  selection.deleteFromDocument()
  const textNode = document.createTextNode(text)
  selection.getRangeAt(0).insertNode(textNode)

  // Move cursor to end of inserted text
  selection.collapseToEnd()

  // Update segments from editor content
  const newPlainText = getPlainTextFromEditor()
  setContent(newPlainText)
}

function handleBlur() {
  // Small delay to allow clicking on dropdown
  setTimeout(() => {
    if (!showDropdown.value) {
      // Could save state here if needed
    }
  }, 200)
}

// Drag and drop handlers
function handleDragOver(event) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
  isDragOver.value = true
}

function handleDragLeave(event) {
  // Only set to false if we're leaving the editor entirely
  if (!editorRef.value.contains(event.relatedTarget)) {
    isDragOver.value = false
  }
}

function handleDrop(event) {
  event.preventDefault()
  isDragOver.value = false

  // Check if this is a template variable
  const variableType = event.dataTransfer.getData('application/x-template-variable')
  if (variableType) {
    // Insert variable at drop position
    handleInsertVariable(variableType)
  } else {
    // Fallback: insert plain text
    const text = event.dataTransfer.getData('text/plain')
    if (text) {
      const selection = window.getSelection()
      if (selection && selection.rangeCount > 0) {
        selection.deleteFromDocument()
        const textNode = document.createTextNode(text)
        selection.getRangeAt(0).insertNode(textNode)
        selection.collapseToEnd()
        const newPlainText = getPlainTextFromEditor()
        setContent(newPlainText)
      }
    }
  }
}

// Selection save/restore helpers
function saveSelection() {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) return null

  const range = selection.getRangeAt(0)
  if (!editorRef.value.contains(range.commonAncestorContainer)) return null

  return {
    startOffset: getAbsoluteOffset(range.startContainer, range.startOffset),
    endOffset: getAbsoluteOffset(range.endContainer, range.endOffset)
  }
}

function restoreSelection(savedSelection) {
  if (!savedSelection || !editorRef.value) return

  try {
    const { node: startNode, offset: startOffset } = getNodeAtOffset(savedSelection.startOffset)
    const { node: endNode, offset: endOffset } = getNodeAtOffset(savedSelection.endOffset)

    if (startNode && endNode) {
      const range = document.createRange()
      range.setStart(startNode, startOffset)
      range.setEnd(endNode, endOffset)

      const selection = window.getSelection()
      selection.removeAllRanges()
      selection.addRange(range)
    }
  } catch (_e) {
    // Ignore selection restore errors
  }
}

function getAbsoluteOffset(node, offset) {
  let absoluteOffset = 0
  const walker = document.createTreeWalker(
    editorRef.value,
    NodeFilter.SHOW_TEXT,
    null,
    false
  )

  let currentNode
  while ((currentNode = walker.nextNode()) !== null) {
    if (currentNode === node) {
      return absoluteOffset + offset
    }
    absoluteOffset += currentNode.textContent.length
  }

  return absoluteOffset
}

function getNodeAtOffset(targetOffset) {
  let currentOffset = 0
  const walker = document.createTreeWalker(
    editorRef.value,
    NodeFilter.SHOW_TEXT,
    null,
    false
  )

  let node
  while ((node = walker.nextNode()) !== null) {
    const nodeLength = node.textContent.length
    if (currentOffset + nodeLength >= targetOffset) {
      return { node, offset: targetOffset - currentOffset }
    }
    currentOffset += nodeLength
  }

  // Return last position if not found
  const lastNode = walker.currentNode
  return { node: lastNode, offset: lastNode?.textContent?.length || 0 }
}

// Initialize
onMounted(() => {
  renderEditor()
})
</script>

<style scoped>
.template-editor-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Suggestions banner */
.suggestions-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, var(--color-ai-subtle, rgba(61, 90, 108, 0.08)), var(--color-washi-warm, #F2EDE3));
  border: 1px solid var(--color-ai, #3D5A6C);
  border-bottom: none;
  border-radius: var(--radius-md, 0.5rem) var(--radius-md, 0.5rem) 0 0;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.banner-icon {
  font-size: 1rem;
}

.banner-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-ai, #3D5A6C);
}

.banner-actions {
  display: flex;
  gap: 0.5rem;
}

.banner-btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-sm, 0.25rem);
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
}

.banner-btn.accept-all {
  background: var(--color-success, #7A8B6E);
  color: white;
  border: none;
}

.banner-btn.accept-all:hover {
  background: var(--color-koke, #7A8B6E);
  filter: brightness(0.9);
}

.banner-btn.reject-all {
  background: transparent;
  color: var(--color-text-secondary, #4A4A4A);
  border: 1px solid var(--color-border, #D4C9BA);
}

.banner-btn.reject-all:hover {
  background: var(--color-washi-aged, #E8E2D5);
}

/* Main editor */
.template-editor {
  background: var(--color-washi-cream, #FAF8F3);
  border: 1.5px solid var(--color-border, #D4C9BA);
  border-radius: var(--radius-md, 0.5rem);
  padding: var(--space-lg, 1.5rem);
  min-height: 300px;
  font-family: var(--font-body, 'Karla', sans-serif);
  font-size: 1rem;
  line-height: var(--leading-relaxed, 1.85);
  color: var(--color-text-primary, #2C2C2C);
  outline: none;
  transition: border-color var(--transition-base, 350ms ease);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.template-editor.has-suggestions {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.template-editor:focus {
  border-color: var(--color-ai, #3D5A6C);
  box-shadow: 0 0 0 3px var(--color-ai-subtle, rgba(61, 90, 108, 0.08));
}

.template-editor.drag-over {
  border-color: var(--color-ai, #3D5A6C);
  border-style: dashed;
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.04));
}

.template-editor:empty::before {
  content: attr(placeholder);
  color: var(--color-text-ghost, #8A8A8A);
  pointer-events: none;
}

/* Editor footer */
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
}

.suggestions-hint {
  font-style: italic;
}

/* Variable chip styles (inline in editor) */
.template-editor :deep(.variable-chip) {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.6rem;
  margin: 0 0.125rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: default;
  user-select: none;
  transition: all var(--transition-subtle, 200ms ease);
  vertical-align: baseline;
  line-height: 1.4;
  white-space: nowrap;
}

.template-editor :deep(.variable-chip[data-type="FIRMA"]) {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
  border: 1px solid var(--color-ai, #3D5A6C);
}

.template-editor :deep(.variable-chip[data-type="POSITION"]) {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
  border: 1px solid var(--color-success, #7A8B6E);
}

.template-editor :deep(.variable-chip[data-type="ANSPRECHPARTNER"]) {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
  border: 1px solid var(--color-warning, #C4A35A);
}

.template-editor :deep(.variable-chip[data-type="QUELLE"]) {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
  border: 1px solid var(--color-terra, #B87A5E);
}

.template-editor :deep(.variable-chip[data-type="EINLEITUNG"]) {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
  border: 1px solid var(--color-bamboo, #8B9A6B);
}

.template-editor :deep(.variable-chip:hover) {
  transform: scale(1.02);
  box-shadow: var(--shadow-paper, 0 2px 8px rgba(44, 44, 44, 0.08));
}

.template-editor :deep(.chip-label) {
  pointer-events: none;
}

.template-editor :deep(.chip-remove) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  margin-left: 0.125rem;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  opacity: 0;
  transition: all var(--transition-subtle, 200ms ease);
  color: inherit;
}

.template-editor :deep(.variable-chip:hover .chip-remove) {
  opacity: 0.6;
}

.template-editor :deep(.chip-remove:hover) {
  opacity: 1 !important;
  background: rgba(0, 0, 0, 0.1);
}

/* Suggestion chip styles */
.template-editor :deep(.suggestion-chip) {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  margin: 0 0.125rem;
  border-radius: var(--radius-lg, 0.75rem);
  font-size: inherit;
  font-family: inherit;
  background: var(--color-washi-warm, #F2EDE3);
  color: var(--color-text-secondary, #4A4A4A);
  border: 1.5px dashed var(--color-stone, #9B958F);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-subtle, 200ms ease);
  line-height: inherit;
}

.template-editor :deep(.suggestion-chip:hover) {
  background: var(--color-washi-aged, #E8E2D5);
  border-color: var(--color-ai, #3D5A6C);
}

.template-editor :deep(.suggestion-icon) {
  font-size: 0.75rem;
  opacity: 0.7;
}

.template-editor :deep(.suggestion-content) {
  pointer-events: none;
}

.template-editor :deep(.suggestion-badge) {
  display: inline-flex;
  padding: 0.1rem 0.4rem;
  margin-left: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.1));
  color: var(--color-ai, #3D5A6C);
  border-radius: var(--radius-sm, 0.25rem);
  opacity: 0.8;
}

.template-editor :deep(.suggestion-actions) {
  display: none;
  align-items: center;
  gap: 0.25rem;
  margin-left: 0.375rem;
}

.template-editor :deep(.suggestion-chip:hover .suggestion-actions) {
  display: flex;
}

.template-editor :deep(.action-btn) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  background: var(--color-washi-cream, #FAF8F3);
  border: 1px solid var(--color-border, #D4C9BA);
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
}

.template-editor :deep(.action-btn:hover) {
  transform: scale(1.1);
}

.template-editor :deep(.accept-btn) {
  color: var(--color-success, #7A8B6E);
}

.template-editor :deep(.accept-btn:hover) {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  border-color: var(--color-success, #7A8B6E);
}

.template-editor :deep(.reject-btn) {
  color: var(--color-error, #B87A6E);
}

.template-editor :deep(.reject-btn:hover) {
  background: var(--color-error-light, rgba(184, 122, 110, 0.15));
  border-color: var(--color-error, #B87A6E);
}

/* Banner transition */
.banner-enter-active,
.banner-leave-active {
  transition: all 300ms var(--ease-zen, ease);
}

.banner-enter-from,
.banner-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
