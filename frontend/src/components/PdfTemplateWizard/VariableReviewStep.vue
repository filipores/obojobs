<template>
  <div class="variable-review-step">
    <div class="review-header">
      <div class="step-marker">03</div>
      <h3>Variablen ueberpruefen</h3>
      <p class="review-hint">
        Ueberpruefen Sie die von der KI erkannten Variablen und passen Sie sie bei Bedarf an.
      </p>
    </div>

    <!-- Stats Summary -->
    <div class="stats-summary">
      <div class="stat-item">
        <span class="stat-value">{{ suggestions.length }}</span>
        <span class="stat-label">Erkannte Variablen</span>
      </div>
      <div class="stat-item stat-accepted">
        <span class="stat-value">{{ acceptedCount }}</span>
        <span class="stat-label">Akzeptiert</span>
      </div>
      <div class="stat-item stat-rejected">
        <span class="stat-value">{{ rejectedCount }}</span>
        <span class="stat-label">Abgelehnt</span>
      </div>
      <div class="stat-item stat-pending">
        <span class="stat-value">{{ pendingCount }}</span>
        <span class="stat-label">Ausstehend</span>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="pendingCount > 0" class="bulk-actions">
      <button class="zen-btn zen-btn-sm" @click="acceptAllPending">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        Alle annehmen
      </button>
      <button class="zen-btn zen-btn-sm" @click="rejectAllPending">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        Alle ablehnen
      </button>
    </div>

    <!-- Suggestions List -->
    <div class="suggestions-list">
      <TransitionGroup name="suggestion-list">
        <div
          v-for="suggestion in suggestions"
          :key="suggestion.id"
          class="suggestion-card zen-card"
          :class="{
            'is-accepted': suggestion.status === 'accepted',
            'is-rejected': suggestion.status === 'rejected',
            'is-pending': !suggestion.status || suggestion.status === 'pending'
          }"
        >
          <!-- Variable Info -->
          <div class="suggestion-main">
            <div class="variable-badge" :class="getVariableClass(suggestion.variable_name)">
              {{ suggestion.variable_name }}
            </div>
            <div class="suggestion-content">
              <div class="suggestion-text">
                <span class="text-label">Erkannter Text:</span>
                <span class="text-value">"{{ suggestion.suggested_text }}"</span>
              </div>
              <div v-if="suggestion.reason" class="suggestion-reason">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="16" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                {{ suggestion.reason }}
              </div>
              <div v-if="suggestion.position" class="suggestion-position">
                <span class="position-label">Position:</span>
                Seite {{ suggestion.position.page }}, Zeile {{ suggestion.position.line || '?' }}
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="suggestion-actions">
            <template v-if="!suggestion.status || suggestion.status === 'pending'">
              <button
                class="action-btn accept-btn"
                @click="handleAccept(suggestion)"
                title="Variable annehmen"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </button>
              <button
                class="action-btn reject-btn"
                @click="handleReject(suggestion)"
                title="Variable ablehnen"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </template>
            <template v-else>
              <div class="status-badge" :class="suggestion.status">
                <svg v-if="suggestion.status === 'accepted'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                {{ suggestion.status === 'accepted' ? 'Angenommen' : 'Abgelehnt' }}
              </div>
              <button
                class="action-btn undo-btn"
                @click="resetSuggestion(suggestion)"
                title="Rueckgaengig machen"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                  <path d="M3 3v5h5"/>
                </svg>
              </button>
            </template>
          </div>
        </div>
      </TransitionGroup>

      <!-- Empty State -->
      <div v-if="suggestions.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
          </svg>
        </div>
        <h4>Keine Variablen erkannt</h4>
        <p>Die KI konnte keine Variablen in diesem PDF identifizieren.</p>
      </div>
    </div>

    <!-- Save Section -->
    <div v-if="suggestions.length > 0" class="save-section">
      <div class="save-info">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span>{{ acceptedCount }} Variable{{ acceptedCount !== 1 ? 'n' : '' }} werden im Template gespeichert.</span>
      </div>
      <button
        class="zen-btn zen-btn-filled"
        :disabled="acceptedCount === 0"
        @click="handleSave"
      >
        Template speichern
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  suggestions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['accept', 'reject', 'save'])

// Computed counts
const acceptedCount = computed(() =>
  props.suggestions.filter(s => s.status === 'accepted').length
)

const rejectedCount = computed(() =>
  props.suggestions.filter(s => s.status === 'rejected').length
)

const pendingCount = computed(() =>
  props.suggestions.filter(s => !s.status || s.status === 'pending').length
)

// Variable type styling
function getVariableClass(variableName) {
  const classMap = {
    'FIRMA': 'var-firma',
    'POSITION': 'var-position',
    'ANSPRECHPARTNER': 'var-ansprechpartner',
    'QUELLE': 'var-quelle',
    'EINLEITUNG': 'var-einleitung',
    'DATUM': 'var-datum',
    'NAME': 'var-name',
    'ADRESSE': 'var-adresse'
  }
  return classMap[variableName?.toUpperCase()] || 'var-default'
}

// Actions
function handleAccept(suggestion) {
  emit('accept', suggestion)
}

function handleReject(suggestion) {
  emit('reject', suggestion)
}

function resetSuggestion(suggestion) {
  // Reset by re-emitting as pending
  suggestion.status = 'pending'
}

function acceptAllPending() {
  props.suggestions
    .filter(s => !s.status || s.status === 'pending')
    .forEach(s => emit('accept', s))
}

function rejectAllPending() {
  props.suggestions
    .filter(s => !s.status || s.status === 'pending')
    .forEach(s => emit('reject', s))
}

function handleSave() {
  emit('save')
}
</script>

<style scoped>
.variable-review-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg, 1.5rem);
}

.review-header {
  text-align: center;
}

.step-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-ai, #3D5A6C);
  color: var(--color-text-inverse, #FAF8F3);
  border-radius: 50%;
  font-weight: 500;
  font-size: 0.875rem;
  margin-bottom: var(--space-md, 1rem);
}

.review-header h3 {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi, #2C2C2C);
  margin-bottom: var(--space-sm, 0.5rem);
}

.review-hint {
  color: var(--color-text-secondary, #4A4A4A);
  font-size: 0.9375rem;
  max-width: 500px;
  margin: 0 auto;
  line-height: var(--leading-relaxed, 1.85);
}

/* Stats Summary */
.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md, 1rem);
  padding: var(--space-lg, 1.5rem);
  background: var(--color-washi-warm, #F2EDE3);
  border-radius: var(--radius-md, 0.5rem);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--color-sumi, #2C2C2C);
  line-height: 1.2;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.stat-accepted .stat-value {
  color: var(--color-success, #7A8B6E);
}

.stat-rejected .stat-value {
  color: var(--color-error, #B87A6E);
}

.stat-pending .stat-value {
  color: var(--color-ai, #3D5A6C);
}

/* Bulk Actions */
.bulk-actions {
  display: flex;
  gap: var(--space-sm, 0.5rem);
  justify-content: center;
}

.bulk-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs, 0.25rem);
}

/* Suggestions List */
.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md, 1rem);
}

.suggestion-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg, 1.5rem);
  padding: var(--space-lg, 1.5rem);
  transition: all var(--transition-base, 350ms ease);
}

.suggestion-card.is-accepted {
  border-color: var(--color-success, #7A8B6E);
  background: var(--color-success-light, rgba(122, 139, 110, 0.05));
}

.suggestion-card.is-rejected {
  border-color: var(--color-error, #B87A6E);
  background: var(--color-error-light, rgba(184, 122, 110, 0.05));
  opacity: 0.7;
}

.suggestion-main {
  display: flex;
  gap: var(--space-md, 1rem);
  flex: 1;
  min-width: 0;
}

/* Variable Badge */
.variable-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs, 0.25rem) var(--space-sm, 0.5rem);
  border-radius: var(--radius-sm, 0.25rem);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
  flex-shrink: 0;
  height: fit-content;
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

.var-datum,
.var-name,
.var-adresse,
.var-default {
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-stone, #9B958F);
}

/* Suggestion Content */
.suggestion-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 0.5rem);
}

.suggestion-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs, 0.25rem);
}

.text-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary, #6B6B6B);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.text-value {
  font-size: 0.9375rem;
  color: var(--color-sumi, #2C2C2C);
  font-style: italic;
}

.suggestion-reason {
  display: flex;
  align-items: flex-start;
  gap: var(--space-xs, 0.25rem);
  font-size: 0.8125rem;
  color: var(--color-text-secondary, #4A4A4A);
  line-height: var(--leading-relaxed, 1.85);
}

.suggestion-reason svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-ai, #3D5A6C);
}

.suggestion-position {
  font-size: 0.75rem;
  color: var(--color-text-ghost, #8A8A8A);
}

.position-label {
  font-weight: 500;
}

/* Actions */
.suggestion-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: var(--color-washi-cream, #FAF8F3);
  border: 1.5px solid var(--color-border, #D4C9BA);
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
}

.action-btn:hover {
  transform: scale(1.08);
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

.undo-btn {
  width: 32px;
  height: 32px;
  color: var(--color-text-tertiary, #6B6B6B);
}

.undo-btn:hover {
  color: var(--color-ai, #3D5A6C);
  border-color: var(--color-ai, #3D5A6C);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs, 0.25rem);
  padding: var(--space-xs, 0.25rem) var(--space-sm, 0.5rem);
  border-radius: var(--radius-full, 9999px);
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.accepted {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
}

.status-badge.rejected {
  background: var(--color-error-light, rgba(184, 122, 110, 0.15));
  color: var(--color-error, #B87A6E);
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--space-xl, 2rem);
  color: var(--color-text-ghost, #8A8A8A);
}

.empty-icon {
  margin-bottom: var(--space-md, 1rem);
  opacity: 0.5;
}

.empty-state h4 {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-text-secondary, #4A4A4A);
  margin-bottom: var(--space-sm, 0.5rem);
}

.empty-state p {
  font-size: 0.9375rem;
}

/* Save Section */
.save-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg, 1.5rem);
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.08));
  border: 1px solid var(--color-ai, #3D5A6C);
  border-radius: var(--radius-md, 0.5rem);
  gap: var(--space-md, 1rem);
}

.save-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 0.5rem);
  font-size: 0.9375rem;
  color: var(--color-ai, #3D5A6C);
}

/* List Transition */
.suggestion-list-enter-active,
.suggestion-list-leave-active {
  transition: all 300ms ease;
}

.suggestion-list-enter-from,
.suggestion-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.suggestion-list-move {
  transition: transform 300ms ease;
}

/* Responsive */
@media (max-width: 768px) {
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
  }

  .suggestion-card {
    flex-direction: column;
    gap: var(--space-md, 1rem);
  }

  .suggestion-main {
    flex-direction: column;
  }

  .suggestion-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .save-section {
    flex-direction: column;
    text-align: center;
  }
}
</style>
