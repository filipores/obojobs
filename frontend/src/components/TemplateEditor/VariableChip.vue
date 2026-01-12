<template>
  <span
    class="variable-chip"
    :data-type="variableType"
    :title="description"
    contenteditable="false"
    @click="handleClick"
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
</template>

<script setup>
import { computed } from 'vue'
import { VARIABLE_TYPES } from '../../composables/useTemplateParser'

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

const variableInfo = computed(() => VARIABLE_TYPES[props.variableType] || {})

const label = computed(() => variableInfo.value.label || props.variableType)

const description = computed(() => variableInfo.value.description || '')

function handleClick(e) {
  emit('click', e)
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
}
</style>
