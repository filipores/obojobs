<template>
  <span
    class="suggestion-chip"
    :data-type="suggestedVariable"
    :title="tooltipText"
    contenteditable="false"
    @mouseenter="showActions = true"
    @mouseleave="showActions = false"
  >
    <span class="suggestion-icon">&#10024;</span>
    <span class="suggestion-content">{{ content }}</span>

    <Transition name="fade">
      <span v-if="showActions" class="suggestion-actions">
        <button
          class="action-btn accept-btn"
          @click.stop="$emit('accept')"
          title="Als Variable annehmen"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>
        <button
          class="action-btn reject-btn"
          @click.stop="$emit('reject')"
          title="Vorschlag ablehnen"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </span>
    </Transition>

    <span class="suggestion-badge">{{ variableLabel }}</span>
  </span>
</template>

<script setup>
import { ref, computed } from 'vue'
import { VARIABLE_TYPES } from '../../composables/useTemplateParser'

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  suggestedVariable: {
    type: String,
    required: true
  },
  reason: {
    type: String,
    default: ''
  }
})

defineEmits(['accept', 'reject'])

const showActions = ref(false)

const variableInfo = computed(() => VARIABLE_TYPES[props.suggestedVariable] || {})

const variableLabel = computed(() => variableInfo.value.label || props.suggestedVariable)

const tooltipText = computed(() => {
  let text = `Vorschlag: Als "${variableLabel.value}" markieren`
  if (props.reason) {
    text += `\n${props.reason}`
  }
  return text
})
</script>

<style scoped>
.suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
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

.suggestion-chip:hover {
  background: var(--color-washi-aged, #E8E2D5);
  border-color: var(--color-ai, #3D5A6C);
  box-shadow: var(--shadow-paper, 0 2px 8px rgba(44, 44, 44, 0.08));
}

.suggestion-icon {
  font-size: 0.75rem;
  opacity: 0.7;
}

.suggestion-content {
  pointer-events: none;
}

/* Variable type badge */
.suggestion-badge {
  display: inline-flex;
  align-items: center;
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

/* Action buttons container */
.suggestion-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-left: 0.375rem;
}

.action-btn {
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

.action-btn:hover {
  transform: scale(1.1);
}

.accept-btn {
  color: var(--color-success, #7A8B6E);
}

.accept-btn:hover {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  border-color: var(--color-success, #7A8B6E);
}

.reject-btn {
  color: var(--color-error, #B87A6E);
}

.reject-btn:hover {
  background: var(--color-error-light, rgba(184, 122, 110, 0.15));
  border-color: var(--color-error, #B87A6E);
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 150ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Badge colors based on variable type */
.suggestion-chip[data-type="FIRMA"] .suggestion-badge {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
}

.suggestion-chip[data-type="POSITION"] .suggestion-badge {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
}

.suggestion-chip[data-type="ANSPRECHPARTNER"] .suggestion-badge {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
}

.suggestion-chip[data-type="QUELLE"] .suggestion-badge {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
}

.suggestion-chip[data-type="EINLEITUNG"] .suggestion-badge {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .suggestion-chip {
    background: rgba(44, 44, 44, 0.3);
    border-color: var(--color-stone, #9B958F);
  }

  .suggestion-chip:hover {
    background: rgba(44, 44, 44, 0.4);
  }

  .action-btn {
    background: rgba(44, 44, 44, 0.5);
    border-color: rgba(255, 255, 255, 0.2);
  }
}
</style>
