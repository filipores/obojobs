<template>
  <div class="template-editor-wrapper">
    <!-- Variable insert panel -->
    <VariablePanel @insert="insertVariable" />

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

    <!-- Formatting toolbar -->
    <div class="editor-toolbar" v-if="editor" :class="{ 'has-suggestions': hasSuggestions }">
      <button
        type="button"
        class="toolbar-btn"
        :class="{ active: editor.isActive('bold') }"
        @click="editor.chain().focus().toggleBold().run()"
        title="Fett (Strg+B)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
          <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
        </svg>
      </button>
      <button
        type="button"
        class="toolbar-btn"
        :class="{ active: editor.isActive('italic') }"
        @click="editor.chain().focus().toggleItalic().run()"
        title="Kursiv (Strg+I)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="4" x2="10" y2="4"/>
          <line x1="14" y1="20" x2="5" y2="20"/>
          <line x1="15" y1="4" x2="9" y2="20"/>
        </svg>
      </button>
      <div class="toolbar-divider"></div>
      <button
        type="button"
        class="toolbar-btn"
        @click="editor.chain().focus().undo().run()"
        :disabled="!editor.can().undo()"
        title="Rückgängig (Strg+Z)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 10h10a5 5 0 0 1 5 5v2"/>
          <polyline points="3 10 7 6 3 10 7 14"/>
        </svg>
      </button>
      <button
        type="button"
        class="toolbar-btn"
        @click="editor.chain().focus().redo().run()"
        :disabled="!editor.can().redo()"
        title="Wiederholen (Strg+Y)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 10H11a5 5 0 0 0-5 5v2"/>
          <polyline points="21 10 17 6 21 10 17 14"/>
        </svg>
      </button>
    </div>

    <!-- Main editor -->
    <editor-content
      :editor="editor"
      class="template-editor"
      :class="{
        'has-suggestions': hasSuggestions,
        'has-toolbar': !!editor,
        'drag-over': isDragOver
      }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    />

    <!-- Character count -->
    <div class="editor-footer">
      <span class="char-count">{{ charCount }} Zeichen</span>
      <span v-if="hasSuggestions" class="suggestions-hint">
        Klicke auf markierte Passagen, um Vorschläge anzunehmen oder abzulehnen
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Editor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { Node, mergeAttributes } from '@tiptap/core'
import VariablePanel from './VariablePanel.vue'
import { VARIABLE_TYPES } from '../../composables/useTemplateParser'

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

// Local state
const editor = ref(null)
const isUpdating = ref(false)
const isDragOver = ref(false)
const processedSuggestions = ref([])

// Custom extension for variable chips
const VariableChip = Node.create({
  name: 'variableChip',
  group: 'inline',
  inline: true,
  atom: true,

  addAttributes() {
    return {
      type: {
        default: 'FIRMA'
      }
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-variable-chip]',
        getAttrs: (dom) => ({
          type: dom.getAttribute('data-type')
        })
      }
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    const variableType = node.attrs.type
    const label = VARIABLE_TYPES[variableType]?.label || variableType

    return ['span', mergeAttributes(HTMLAttributes, {
      'data-variable-chip': '',
      'data-type': variableType,
      class: `variable-chip variable-chip-${variableType.toLowerCase()}`,
      contenteditable: 'false'
    }), label]
  }
})

// Custom extension for suggestion chips (AI suggestions that can be accepted/rejected)
const SuggestionChip = Node.create({
  name: 'suggestionChip',
  group: 'inline',
  inline: true,
  atom: true,

  addAttributes() {
    return {
      id: { default: '' },
      text: { default: '' },
      suggestedVariable: { default: 'FIRMA' },
      reason: { default: '' }
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-suggestion-chip]',
        getAttrs: (dom) => ({
          id: dom.getAttribute('data-id'),
          text: dom.getAttribute('data-text'),
          suggestedVariable: dom.getAttribute('data-suggested-variable'),
          reason: dom.getAttribute('data-reason')
        })
      }
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    const varLabel = VARIABLE_TYPES[node.attrs.suggestedVariable]?.label || node.attrs.suggestedVariable

    return ['span', mergeAttributes(HTMLAttributes, {
      'data-suggestion-chip': '',
      'data-id': node.attrs.id,
      'data-text': node.attrs.text,
      'data-suggested-variable': node.attrs.suggestedVariable,
      'data-reason': node.attrs.reason,
      class: 'suggestion-chip',
      contenteditable: 'false'
    }), [
      ['span', { class: 'suggestion-icon' }, '\u2728'],
      ['span', { class: 'suggestion-content' }, node.attrs.text],
      ['span', { class: 'suggestion-badge' }, varLabel],
      ['span', { class: 'suggestion-actions' }, [
        ['button', {
          class: 'action-btn accept-btn',
          title: 'Als Variable annehmen',
          'data-action': 'accept'
        }, '\u2713'],
        ['button', {
          class: 'action-btn reject-btn',
          title: 'Vorschlag ablehnen',
          'data-action': 'reject'
        }, '\u2717']
      ]]
    ]]
  }
})

// Convert plain text with {{VARIABLE}} to HTML
function textToHtml(text) {
  if (!text) return '<p></p>'

  // Escape HTML entities first
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

  // Convert {{VARIABLE}} to chip HTML
  html = html.replace(/\{\{(\w+)\}\}/g, (match, varType) => {
    if (VARIABLE_TYPES[varType]) {
      return `<span data-variable-chip data-type="${varType}" class="variable-chip variable-chip-${varType.toLowerCase()}">${VARIABLE_TYPES[varType].label}</span>`
    }
    return match
  })

  // Convert line breaks to HTML
  // Double line breaks become paragraph breaks
  const paragraphs = html.split(/\n\n+/)
  if (paragraphs.length > 1) {
    html = paragraphs.map(p => {
      const content = p.replace(/\n/g, '<br>').trim()
      return content ? `<p>${content}</p>` : '<p></p>'
    }).join('')
  } else {
    // Single paragraph with possible line breaks
    const content = html.replace(/\n/g, '<br>').trim()
    html = content ? `<p>${content}</p>` : '<p></p>'
  }

  return html
}

// Convert HTML back to plain text with {{VARIABLE}}
function htmlToText(html) {
  if (!html) return ''

  // Create a temporary div to parse HTML
  const div = document.createElement('div')
  div.innerHTML = html

  // Replace variable chips with {{VARIABLE}}
  div.querySelectorAll('[data-variable-chip]').forEach(chip => {
    const varType = chip.getAttribute('data-type')
    const placeholder = document.createTextNode(`{{${varType}}}`)
    chip.parentNode.replaceChild(placeholder, chip)
  })

  // Replace suggestion chips with their text content
  div.querySelectorAll('[data-suggestion-chip]').forEach(chip => {
    const text = chip.getAttribute('data-text')
    const placeholder = document.createTextNode(text)
    chip.parentNode.replaceChild(placeholder, chip)
  })

  // Convert paragraphs and line breaks
  const paragraphs = div.querySelectorAll('p')
  if (paragraphs.length > 0) {
    const texts = []
    paragraphs.forEach(p => {
      // Get inner HTML, convert <br> to \n, then strip remaining tags
      let pText = p.innerHTML
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<[^>]+>/g, '')
      texts.push(decodeHtmlEntities(pText))
    })
    return texts.join('\n\n').trim()
  }

  // If no paragraphs, just get text content
  let text = div.innerHTML
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
  return decodeHtmlEntities(text).trim()
}

function decodeHtmlEntities(text) {
  const textarea = document.createElement('textarea')
  textarea.innerHTML = text
  return textarea.value
}

// Character count
const charCount = computed(() => {
  if (!editor.value) return 0
  return editor.value.getText().length
})

// Suggestions state
const hasSuggestions = computed(() => processedSuggestions.value.length > 0)
const pendingSuggestions = computed(() => processedSuggestions.value)

// Initialize editor
onMounted(() => {
  editor.value = new Editor({
    extensions: [
      StarterKit.configure({
        heading: false,
        bulletList: false,
        orderedList: false,
        blockquote: false,
        codeBlock: false,
        code: false,
        horizontalRule: false
      }),
      Placeholder.configure({
        placeholder: props.placeholder,
        emptyEditorClass: 'is-editor-empty'
      }),
      VariableChip,
      SuggestionChip
    ],
    content: textToHtml(props.modelValue),
    onUpdate: ({ editor: ed }) => {
      if (isUpdating.value) return
      const plainText = htmlToText(ed.getHTML())
      emit('update:modelValue', plainText)
    }
  })

  // Handle suggestion chip clicks
  editor.value.view.dom.addEventListener('click', handleEditorClick)
})

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.view.dom.removeEventListener('click', handleEditorClick)
    editor.value.destroy()
  }
})

// Handle clicks on suggestion chips
function handleEditorClick(event) {
  const actionBtn = event.target.closest('[data-action]')
  if (!actionBtn) return

  const chip = actionBtn.closest('[data-suggestion-chip]')
  if (!chip) return

  const action = actionBtn.getAttribute('data-action')
  const suggestionId = chip.getAttribute('data-id')
  const suggestedVariable = chip.getAttribute('data-suggested-variable')
  const text = chip.getAttribute('data-text')

  if (action === 'accept') {
    // Replace suggestion with variable
    acceptSuggestion(suggestionId, suggestedVariable)
    emit('suggestion-accepted', suggestionId)
  } else if (action === 'reject') {
    // Replace suggestion with plain text
    rejectSuggestion(suggestionId, text)
    emit('suggestion-rejected', suggestionId)
  }
}

// Accept suggestion - convert to variable chip
function acceptSuggestion(suggestionId, variableType) {
  if (!editor.value) return

  const html = editor.value.getHTML()
  const regex = new RegExp(`<span[^>]*data-suggestion-chip[^>]*data-id="${suggestionId}"[^>]*>[^]*?<\\/span>`, 'g')
  const newHtml = html.replace(regex, `<span data-variable-chip data-type="${variableType}" class="variable-chip variable-chip-${variableType.toLowerCase()}">${VARIABLE_TYPES[variableType]?.label || variableType}</span>`)

  isUpdating.value = true
  editor.value.commands.setContent(newHtml, false)
  isUpdating.value = false

  // Remove from processed suggestions
  processedSuggestions.value = processedSuggestions.value.filter(s => s.id !== suggestionId)

  // Emit the change
  const plainText = htmlToText(editor.value.getHTML())
  emit('update:modelValue', plainText)
}

// Reject suggestion - convert to plain text
function rejectSuggestion(suggestionId, text) {
  if (!editor.value) return

  const html = editor.value.getHTML()
  const escapedText = text.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
  const regex = new RegExp(`<span[^>]*data-suggestion-chip[^>]*data-id="${suggestionId}"[^>]*>[^]*?<\\/span>`, 'g')
  const newHtml = html.replace(regex, escapedText)

  isUpdating.value = true
  editor.value.commands.setContent(newHtml, false)
  isUpdating.value = false

  // Remove from processed suggestions
  processedSuggestions.value = processedSuggestions.value.filter(s => s.id !== suggestionId)

  // Emit the change
  const plainText = htmlToText(editor.value.getHTML())
  emit('update:modelValue', plainText)
}

// Accept all suggestions
function handleAcceptAll() {
  const suggestions = [...processedSuggestions.value]
  suggestions.forEach(s => {
    acceptSuggestion(s.id, s.suggestedVariable)
    emit('suggestion-accepted', s.id)
  })
}

// Reject all suggestions
function handleRejectAll() {
  const suggestions = [...processedSuggestions.value]
  suggestions.forEach(s => {
    rejectSuggestion(s.id, s.text)
    emit('suggestion-rejected', s.id)
  })
}

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (!editor.value || isUpdating.value) return

  const currentText = htmlToText(editor.value.getHTML())
  if (newValue !== currentText) {
    isUpdating.value = true
    editor.value.commands.setContent(textToHtml(newValue), false)
    isUpdating.value = false
  }
})

// Watch for suggestions changes
watch(() => props.suggestions, (newSuggestions) => {
  if (!editor.value || !newSuggestions || newSuggestions.length === 0) {
    processedSuggestions.value = []
    return
  }

  // Apply suggestions to the content
  let html = editor.value.getHTML()
  const appliedSuggestions = []

  for (const suggestion of newSuggestions) {
    const text = suggestion.text || suggestion.suggestedText
    const variable = suggestion.suggestedVariable || suggestion.variable
    const id = suggestion.id || `sug_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    if (!text || !html.includes(text)) continue

    // Escape text for regex
    const escapedText = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`(?<!data-text=")${escapedText}(?![^<]*<\\/span>)`, 'g')

    const replacement = `<span data-suggestion-chip data-id="${id}" data-text="${text.replace(/"/g, '&quot;')}" data-suggested-variable="${variable}" data-reason="${(suggestion.reason || '').replace(/"/g, '&quot;')}" class="suggestion-chip" contenteditable="false"><span class="suggestion-icon">\u2728</span><span class="suggestion-content">${text}</span><span class="suggestion-badge">${VARIABLE_TYPES[variable]?.label || variable}</span><span class="suggestion-actions"><button class="action-btn accept-btn" title="Als Variable annehmen" data-action="accept">\u2713</button><button class="action-btn reject-btn" title="Vorschlag ablehnen" data-action="reject">\u2717</button></span></span>`

    if (regex.test(html)) {
      html = html.replace(regex, replacement)
      appliedSuggestions.push({
        id,
        text,
        suggestedVariable: variable,
        reason: suggestion.reason
      })
    }
  }

  if (appliedSuggestions.length > 0) {
    isUpdating.value = true
    editor.value.commands.setContent(html, false)
    isUpdating.value = false
    processedSuggestions.value = appliedSuggestions
  }
}, { immediate: true })

// Insert variable at cursor
function insertVariable(variableType) {
  if (!editor.value) return

  editor.value
    .chain()
    .focus()
    .insertContent({
      type: 'variableChip',
      attrs: { type: variableType }
    })
    .run()
}

// Drag and drop handlers
function handleDragOver(event) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
  isDragOver.value = true
}

function handleDragLeave(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragOver.value = false
  }
}

function handleDrop(event) {
  event.preventDefault()
  isDragOver.value = false

  const variableType = event.dataTransfer.getData('application/x-template-variable')
  if (variableType) {
    insertVariable(variableType)
  }
}
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

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-washi-warm, #F2EDE3);
  border: 1.5px solid var(--color-border, #D4C9BA);
  border-bottom: none;
  border-radius: var(--radius-md, 0.5rem) var(--radius-md, 0.5rem) 0 0;
}

.editor-toolbar.has-suggestions {
  border-radius: 0;
  border-top: none;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm, 0.25rem);
  color: var(--color-text-secondary, #4A4A4A);
  cursor: pointer;
  transition: all 150ms ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-text-primary, #2C2C2C);
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.toolbar-btn.active {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border, #D4C9BA);
  margin: 0 0.25rem;
}

/* Main editor */
.template-editor {
  background: var(--color-washi-cream, #FAF8F3);
  border: 1.5px solid var(--color-border, #D4C9BA);
  border-radius: var(--radius-md, 0.5rem);
  min-height: 300px;
  transition: border-color var(--transition-base, 350ms ease);
}

.template-editor.has-toolbar {
  border-top: none;
  border-radius: 0 0 var(--radius-md, 0.5rem) var(--radius-md, 0.5rem);
}

.template-editor.has-suggestions.has-toolbar {
  border-top: none;
}

.template-editor:has(.ProseMirror-focused) {
  border-color: var(--color-ai, #3D5A6C);
  box-shadow: 0 0 0 3px var(--color-ai-subtle, rgba(61, 90, 108, 0.08));
}

.template-editor.drag-over {
  border-color: var(--color-ai, #3D5A6C);
  border-style: dashed;
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.04));
}

.template-editor :deep(.ProseMirror) {
  padding: var(--space-lg, 1.5rem);
  min-height: 300px;
  font-family: var(--font-body, 'Karla', sans-serif);
  font-size: 1rem;
  line-height: var(--leading-relaxed, 1.85);
  color: var(--color-text-primary, #2C2C2C);
  outline: none;
}

.template-editor :deep(.ProseMirror p) {
  margin: 0 0 1em 0;
}

.template-editor :deep(.ProseMirror p:last-child) {
  margin-bottom: 0;
}

.template-editor :deep(.ProseMirror.is-editor-empty:first-child::before),
.template-editor :deep(.ProseMirror > p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--color-text-ghost, #8A8A8A);
  pointer-events: none;
  height: 0;
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

/* Variable chip styles */
.template-editor :deep(.variable-chip) {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.5rem;
  margin: 0 0.125rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: default;
  user-select: none;
  vertical-align: baseline;
  line-height: 1.4;
  white-space: nowrap;
}

.template-editor :deep(.variable-chip-firma) {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
  border: 1px solid var(--color-ai, #3D5A6C);
}

.template-editor :deep(.variable-chip-position) {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
  border: 1px solid var(--color-success, #7A8B6E);
}

.template-editor :deep(.variable-chip-ansprechpartner) {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
  border: 1px solid var(--color-warning, #C4A35A);
}

.template-editor :deep(.variable-chip-quelle) {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
  border: 1px solid var(--color-terra, #B87A5E);
}

.template-editor :deep(.variable-chip-einleitung) {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
  border: 1px solid var(--color-bamboo, #8B9A6B);
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
  font-size: 0.75rem;
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
