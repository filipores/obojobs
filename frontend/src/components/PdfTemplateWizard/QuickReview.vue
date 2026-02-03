<template>
  <div class="quick-review">
    <!-- Header -->
    <div class="review-header">
      <div class="success-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="16 10 10.5 15.5 8 13"/>
        </svg>
      </div>
      <h3>{{ suggestions.length }} Variablen erkannt</h3>
      <p class="review-subtitle">
        Die KI hat folgende Variablen in Ihrem PDF identifiziert:
      </p>
    </div>

    <!-- Variables List -->
    <div class="variables-list">
      <div
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        class="variable-item"
      >
        <div class="variable-check">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <div class="variable-info">
          <span class="variable-badge" :class="getVariableClass(suggestion.variable_name)">
            {{ suggestion.variable_name }}
          </span>
          <span class="variable-text">"{{ truncateText(suggestion.suggested_text, 40) }}"</span>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="review-actions">
      <p class="action-prompt">Moechten Sie diese Variablen speichern?</p>
      <div class="action-buttons">
        <button class="zen-btn zen-btn-filled zen-btn-success" @click="handleConfirm">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Ja, speichern
        </button>
        <button class="zen-btn" @click="handleAdjust">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Nein, anpassen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  suggestions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['confirm', 'adjust'])

function handleConfirm() {
  emit('confirm')
}

function handleAdjust() {
  emit('adjust')
}

function getVariableClass(variableName) {
  const classMap = {
    'FIRMA': 'var-firma',
    'POSITION': 'var-position',
    'ANSPRECHPARTNER': 'var-ansprechpartner',
    'QUELLE': 'var-quelle',
    'EINLEITUNG': 'var-einleitung'
  }
  return classMap[variableName?.toUpperCase()] || 'var-default'
}

function truncateText(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.quick-review {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-xl, 2rem);
  max-width: 500px;
  margin: 0 auto;
}

/* Header */
.review-header {
  margin-bottom: var(--space-xl, 2rem);
}

.success-icon {
  width: 64px;
  height: 64px;
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-success, #7A8B6E);
  margin: 0 auto var(--space-lg, 1.5rem);
}

.review-header h3 {
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-sm, 0.5rem);
}

.review-subtitle {
  color: var(--color-text-secondary, #4A4A4A);
  font-size: 0.9375rem;
}

/* Variables List */
.variables-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 0.5rem);
  margin-bottom: var(--space-xl, 2rem);
}

.variable-item {
  display: flex;
  align-items: center;
  gap: var(--space-md, 1rem);
  padding: var(--space-md, 1rem);
  background: var(--color-washi, #FAF8F3);
  border: 1px solid var(--color-border-light, #E5DFD4);
  border-radius: var(--radius-md, 0.5rem);
  text-align: left;
}

.variable-check {
  width: 28px;
  height: 28px;
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-success, #7A8B6E);
  flex-shrink: 0;
}

.variable-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  min-width: 0;
}

.variable-badge {
  display: inline-flex;
  padding: var(--space-xs, 0.25rem) var(--space-sm, 0.5rem);
  border-radius: var(--radius-sm, 0.25rem);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
  flex-shrink: 0;
}

.var-firma {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
}

.var-position {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
}

.var-ansprechpartner {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
}

.var-quelle {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
}

.var-einleitung {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
}

.var-default {
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-stone, #9B958F);
}

.variable-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #4A4A4A);
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Actions */
.review-actions {
  width: 100%;
}

.action-prompt {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-lg, 1.5rem);
}

.action-buttons {
  display: flex;
  gap: var(--space-md, 1rem);
  justify-content: center;
}

.action-buttons .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  min-width: 160px;
  justify-content: center;
}

.zen-btn-success {
  background: var(--color-success, #7A8B6E);
  border-color: var(--color-success, #7A8B6E);
  color: var(--color-text-inverse, #FAF8F3);
}

.zen-btn-success:hover {
  background: var(--color-success-dark, #6A7B5E);
  border-color: var(--color-success-dark, #6A7B5E);
}

/* Responsive */
@media (max-width: 480px) {
  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .zen-btn {
    width: 100%;
  }
}
</style>
