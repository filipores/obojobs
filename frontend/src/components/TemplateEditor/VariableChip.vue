<template>
  <span
    ref="chipRef"
    class="variable-chip"
    :data-type="variableType"
    contenteditable="false"
    @click="handleClick"
    @mouseenter="showTooltip"
    @mouseleave="hideTooltip"
  >
    <span class="chip-label">{{ label }}</span>
    <button
      v-if="removable"
      class="chip-remove"
      @click.stop="$emit('remove')"
      title="Variable entfernen"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  </span>

  <Teleport to="body">
    <Transition name="tooltip">
      <div
        v-if="isTooltipVisible"
        ref="tooltipRef"
        class="variable-tooltip"
        :style="tooltipStyle"
        @mouseenter="keepTooltipOpen"
        @mouseleave="hideTooltip"
      >
        <div class="tooltip-header">
          <span class="tooltip-color" :data-type="variableType"></span>
          <span class="tooltip-title">{{ tooltipData.title }}</span>
        </div>

        <p class="tooltip-description">{{ tooltipData.description }}</p>

        <div class="tooltip-example">
          <span class="example-label">Beispiel:</span>
          <span class="example-value">{{ tooltipData.example }}</span>
        </div>

        <div v-if="tooltipData.aiNote" class="tooltip-ai-note">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-6h2zm0-8h-2V7h2z"/>
          </svg>
          <span>{{ tooltipData.aiNote }}</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { VARIABLE_TYPES } from '../../composables/useTemplateParser'
import { variableDescriptions } from '../../data/variableDescriptions'

const props = defineProps({
  variableType: {
    type: String,
    required: true,
    validator: (value) => Object.keys(VARIABLE_TYPES).includes(value)
  },
  removable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['click', 'remove'])

const chipRef = ref(null)
const tooltipRef = ref(null)
const isTooltipVisible = ref(false)
const tooltipPosition = ref({ top: 0, left: 0 })
let hideTimeout = null

const variableInfo = computed(() => VARIABLE_TYPES[props.variableType] || {})
const label = computed(() => variableInfo.value.label || props.variableType)

const tooltipData = computed(() => {
  return variableDescriptions[props.variableType] || {
    title: variableInfo.value.label || props.variableType,
    description: variableInfo.value.description || '',
    example: ''
  }
})

const tooltipStyle = computed(() => ({
  top: `${tooltipPosition.value.top}px`,
  left: `${tooltipPosition.value.left}px`
}))

function handleClick(e) {
  emit('click', e)
}

function showTooltip() {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
    hideTimeout = null
  }

  isTooltipVisible.value = true
  nextTick(() => {
    positionTooltip()
  })
}

function hideTooltip() {
  hideTimeout = setTimeout(() => {
    isTooltipVisible.value = false
  }, 100)
}

function keepTooltipOpen() {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
    hideTimeout = null
  }
}

function positionTooltip() {
  if (!chipRef.value || !tooltipRef.value) return

  const chipRect = chipRef.value.getBoundingClientRect()
  const tooltipRect = tooltipRef.value.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const padding = 8

  // Default: position below the chip
  let top = chipRect.bottom + padding
  let left = chipRect.left + (chipRect.width / 2) - (tooltipRect.width / 2)

  // If tooltip would overflow right edge
  if (left + tooltipRect.width > viewportWidth - padding) {
    left = viewportWidth - tooltipRect.width - padding
  }

  // If tooltip would overflow left edge
  if (left < padding) {
    left = padding
  }

  // If tooltip would overflow bottom, position above chip
  if (top + tooltipRect.height > viewportHeight - padding) {
    top = chipRect.top - tooltipRect.height - padding
  }

  tooltipPosition.value = { top, left }
}
</script>

<style scoped>
.variable-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.8125rem;
  font-weight: 500;
  font-family: var(--font-body);
  cursor: default;
  user-select: none;
  transition: all var(--transition-subtle, 200ms ease);
  vertical-align: baseline;
  line-height: 1.4;
  white-space: nowrap;
}

/* Color variants based on variable type */
.variable-chip[data-type="FIRMA"] {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
  border: 1px solid var(--color-ai, #3D5A6C);
}

.variable-chip[data-type="POSITION"] {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
  border: 1px solid var(--color-success, #7A8B6E);
}

.variable-chip[data-type="ANSPRECHPARTNER"] {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
  border: 1px solid var(--color-warning, #C4A35A);
}

.variable-chip[data-type="QUELLE"] {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
  border: 1px solid var(--color-terra, #B87A5E);
}

.variable-chip[data-type="EINLEITUNG"] {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
  border: 1px solid var(--color-bamboo, #8B9A6B);
}

/* Hover state */
.variable-chip:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-paper, 0 2px 8px rgba(44, 44, 44, 0.08));
}

/* Label */
.chip-label {
  pointer-events: none;
}

/* Remove button */
.chip-remove {
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

.variable-chip:hover .chip-remove {
  opacity: 0.6;
}

.chip-remove:hover {
  opacity: 1 !important;
  background: rgba(0, 0, 0, 0.1);
}

/* Tooltip styles */
.variable-tooltip {
  position: fixed;
  z-index: var(--z-tooltip, 3000);
  width: 280px;
  padding: 0.875rem;
  background: var(--color-washi-cream, #FAF8F3);
  border: 1px solid var(--color-border, #D4C9BA);
  border-radius: var(--radius-lg, 0.75rem);
  box-shadow: var(--shadow-floating, 0 16px 48px rgba(44, 44, 44, 0.12));
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.tooltip-color {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tooltip-color[data-type="FIRMA"] {
  background: var(--color-ai, #3D5A6C);
}

.tooltip-color[data-type="POSITION"] {
  background: var(--color-success, #7A8B6E);
}

.tooltip-color[data-type="ANSPRECHPARTNER"] {
  background: var(--color-warning, #C4A35A);
}

.tooltip-color[data-type="QUELLE"] {
  background: var(--color-terra, #B87A5E);
}

.tooltip-color[data-type="EINLEITUNG"] {
  background: var(--color-bamboo, #8B9A6B);
}

.tooltip-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary, #2C2C2C);
}

.tooltip-description {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--color-text-secondary, #4A4A4A);
  margin: 0 0 0.75rem 0;
}

.tooltip-example {
  padding: 0.625rem;
  background: var(--color-washi-warm, #F2EDE3);
  border-radius: var(--radius-md, 0.5rem);
  margin-bottom: 0.5rem;
}

.example-label {
  display: block;
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-tertiary, #6B6B6B);
  margin-bottom: 0.25rem;
}

.example-value {
  display: block;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-primary, #2C2C2C);
  font-style: italic;
}

.tooltip-ai-note {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(139, 154, 107, 0.1);
  border-radius: var(--radius-sm, 0.25rem);
  font-size: 0.75rem;
  color: var(--color-bamboo, #8B9A6B);
}

.tooltip-ai-note svg {
  flex-shrink: 0;
  margin-top: 0.125rem;
}

/* Tooltip transition */
.tooltip-enter-active {
  transition: all 200ms var(--ease-zen, cubic-bezier(0.25, 0.1, 0.25, 1));
}

.tooltip-leave-active {
  transition: all 150ms ease;
}

.tooltip-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.tooltip-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .variable-chip[data-type="FIRMA"] {
    background: rgba(90, 122, 138, 0.2);
    color: var(--color-ai-light, #5A7A8A);
    border-color: var(--color-ai-light, #5A7A8A);
  }

  .variable-chip[data-type="POSITION"] {
    background: rgba(122, 139, 110, 0.2);
  }

  .variable-chip[data-type="ANSPRECHPARTNER"] {
    background: rgba(196, 163, 90, 0.2);
  }

  .variable-chip[data-type="QUELLE"] {
    background: rgba(184, 122, 94, 0.2);
  }

  .variable-chip[data-type="EINLEITUNG"] {
    background: rgba(139, 154, 107, 0.2);
  }

  .chip-remove:hover {
    background: rgba(255, 255, 255, 0.15);
  }

  .variable-tooltip {
    background: #1a1a1a;
    border-color: rgba(255, 255, 255, 0.1);
  }

  .tooltip-title {
    color: #f0f0f0;
  }

  .tooltip-description {
    color: #b0b0b0;
  }

  .tooltip-example {
    background: rgba(255, 255, 255, 0.05);
  }

  .example-value {
    color: #e0e0e0;
  }

  .tooltip-ai-note {
    background: rgba(139, 154, 107, 0.15);
  }
}
</style>
