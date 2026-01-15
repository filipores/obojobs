<template>
  <div class="variable-panel">
    <div class="panel-header">
      <span class="panel-title">Variablen</span>
      <span class="panel-hint">Klicken zum Einfügen</span>
    </div>
    <div class="panel-buttons">
      <button
        v-for="(info, type) in variableTypes"
        :key="type"
        class="variable-btn"
        :class="`variable-btn--${info.color}`"
        :title="info.description"
        @click="$emit('insert', type)"
      >
        <span class="btn-label">{{ info.label }}</span>
        <span class="btn-syntax">{{ getVariableSyntax(type) }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { VARIABLE_TYPES } from '../../composables/useTemplateParser'

defineEmits(['insert'])

const variableTypes = VARIABLE_TYPES

function getVariableSyntax(type) {
  return '{{' + type + '}}'
}
</script>

<style scoped>
.variable-panel {
  background: var(--color-washi-warm, #F2EDE3);
  border: 1px solid var(--color-border, #D4C9BA);
  border-radius: var(--radius-md, 0.5rem);
  padding: var(--space-md, 1rem);
  margin-bottom: var(--space-md, 1rem);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm, 0.5rem);
}

.panel-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-primary, #2C2C2C);
  letter-spacing: 0.02em;
}

.panel-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
}

.panel-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs, 0.375rem);
}

.variable-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
  border: 1.5px solid transparent;
  position: relative;
}

.variable-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-paper, 0 2px 8px rgba(44, 44, 44, 0.08));
}

.variable-btn:active {
  transform: translateY(0) scale(0.98);
}

/* Color variants */
.variable-btn--ai {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
  border-color: var(--color-ai, #3D5A6C);
}

.variable-btn--ai:hover {
  background: var(--color-ai, #3D5A6C);
  color: white;
}

.variable-btn--success {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
  border-color: var(--color-success, #7A8B6E);
}

.variable-btn--success:hover {
  background: var(--color-success, #7A8B6E);
  color: white;
}

.variable-btn--warning {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
  border-color: var(--color-warning, #C4A35A);
}

.variable-btn--warning:hover {
  background: var(--color-warning, #C4A35A);
  color: white;
}

.variable-btn--terra {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
  border-color: var(--color-terra, #B87A5E);
}

.variable-btn--terra:hover {
  background: var(--color-terra, #B87A5E);
  color: white;
}

.variable-btn--bamboo {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
  border-color: var(--color-bamboo, #8B9A6B);
}

.variable-btn--bamboo:hover {
  background: var(--color-bamboo, #8B9A6B);
  color: white;
}

.btn-label {
  pointer-events: none;
}

.btn-syntax {
  font-size: 0.6875rem;
  opacity: 0.7;
  font-family: monospace;
  pointer-events: none;
}

/* Tooltip via title attribute - browser native */
.variable-btn[title] {
  cursor: pointer;
}

/* Responsive */
@media (max-width: 480px) {
  .panel-buttons {
    gap: var(--space-xs, 0.25rem);
  }

  .variable-btn {
    padding: 0.3rem 0.5rem;
    font-size: 0.75rem;
  }

  .btn-syntax {
    display: none;
  }
}
</style>
