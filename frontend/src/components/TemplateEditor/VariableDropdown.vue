<template>
  <Teleport to="body">
    <Transition name="dropdown">
      <div
        v-if="show"
        ref="dropdownRef"
        class="variable-dropdown"
        :style="positionStyle"
        @click.stop
      >
        <div class="dropdown-header">
          <span class="dropdown-title">Variable einfügen</span>
          <button class="dropdown-close" @click="$emit('close')" title="Schließen">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="dropdown-options">
          <button
            v-for="(info, type) in variableTypes"
            :key="type"
            class="dropdown-option"
            :data-type="type"
            @click="selectVariable(type)"
          >
            <span class="option-color" :data-type="type"></span>
            <span class="option-content">
              <span class="option-label">{{ info.label }}</span>
              <span class="option-description">{{ info.description }}</span>
            </span>
          </button>
        </div>

        <div class="dropdown-footer">
          <span class="selection-preview" v-if="selectedText">
            "{{ truncatedSelection }}"
          </span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { VARIABLE_TYPES } from '../../composables/useTemplateParser'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object,
    default: () => ({ top: 0, left: 0 })
  },
  selectedText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select', 'close'])

const dropdownRef = ref(null)
const variableTypes = VARIABLE_TYPES

const positionStyle = computed(() => ({
  top: `${props.position.top}px`,
  left: `${props.position.left}px`
}))

const truncatedSelection = computed(() => {
  const maxLength = 30
  if (props.selectedText.length > maxLength) {
    return props.selectedText.slice(0, maxLength) + '...'
  }
  return props.selectedText
})

function selectVariable(type) {
  emit('select', type)
}

function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    emit('close')
  }
}

function handleEscape(event) {
  if (event.key === 'Escape') {
    emit('close')
  }
}

// Track if listeners are currently attached
const listenersAttached = ref(false)

function attachListeners() {
  if (!listenersAttached.value) {
    document.addEventListener('click', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    listenersAttached.value = true
  }
}

function detachListeners() {
  if (listenersAttached.value) {
    document.removeEventListener('click', handleClickOutside)
    document.removeEventListener('keydown', handleEscape)
    listenersAttached.value = false
  }
}

watch(() => props.show, (newValue) => {
  if (newValue) {
    nextTick(() => {
      attachListeners()
    })
  } else {
    detachListeners()
  }
})

onUnmounted(() => {
  detachListeners()
})
</script>

<style scoped>
.variable-dropdown {
  position: fixed;
  z-index: var(--z-modal, 2000);
  min-width: 220px;
  max-width: 280px;
  background: var(--color-washi-cream, #FAF8F3);
  border: 1px solid var(--color-border, #D4C9BA);
  border-radius: var(--radius-lg, 0.75rem);
  box-shadow: var(--shadow-floating, 0 16px 48px rgba(44, 44, 44, 0.08));
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border-light, #E8E2D5);
  background: var(--color-washi-warm, #F2EDE3);
}

.dropdown-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-primary, #2C2C2C);
  letter-spacing: 0.02em;
}

.dropdown-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm, 0.25rem);
  color: var(--color-text-tertiary, #6B6B6B);
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
}

.dropdown-close:hover {
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-text-primary, #2C2C2C);
}

.dropdown-options {
  padding: 0.5rem;
}

.dropdown-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.625rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md, 0.5rem);
  cursor: pointer;
  text-align: left;
  transition: all var(--transition-subtle, 200ms ease);
}

.dropdown-option:hover {
  background: var(--color-washi-warm, #F2EDE3);
}

.dropdown-option:active {
  transform: scale(0.98);
}

.option-color {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.option-color[data-type="FIRMA"] {
  background: var(--color-ai, #3D5A6C);
}

.option-color[data-type="POSITION"] {
  background: var(--color-success, #7A8B6E);
}

.option-color[data-type="ANSPRECHPARTNER"] {
  background: var(--color-warning, #C4A35A);
}

.option-color[data-type="QUELLE"] {
  background: var(--color-terra, #B87A5E);
}

.option-color[data-type="EINLEITUNG"] {
  background: var(--color-bamboo, #8B9A6B);
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.option-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary, #2C2C2C);
}

.option-description {
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
}

.dropdown-footer {
  padding: 0.5rem 1rem 0.75rem;
  border-top: 1px solid var(--color-border-light, #E8E2D5);
}

.selection-preview {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Dropdown transition */
.dropdown-enter-active {
  transition: all 200ms var(--ease-zen, cubic-bezier(0.25, 0.1, 0.25, 1));
}

.dropdown-leave-active {
  transition: all 150ms ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .variable-dropdown {
    background: #1a1a1a;
    border-color: rgba(255, 255, 255, 0.1);
  }

  .dropdown-header {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .dropdown-option:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .dropdown-footer {
    border-color: rgba(255, 255, 255, 0.1);
  }
}
</style>
