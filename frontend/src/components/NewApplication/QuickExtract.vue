<template>
  <section class="quick-confirm-section animate-fade-up" style="animation-delay: 150ms;">
    <div class="quick-confirm-card zen-card">
      <div class="quick-confirm-header">
        <span :class="['portal-tag', `portal-${quickConfirmData.portal_id}`]">
          {{ quickConfirmData.portal }}
        </span>
        <button @click="$emit('reset')" class="reset-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="quick-confirm-content">
        <h2 class="quick-confirm-title">Bewerbung erstellen?</h2>
        <p class="quick-confirm-job">
          <strong>{{ quickConfirmData.title || 'Position' }}</strong>
          <span class="quick-confirm-at">bei</span>
          <strong>{{ quickConfirmData.company || 'Unbekannt' }}</strong>
        </p>
      </div>

      <!-- Tone Selection -->
      <div class="form-group tone-selection">
        <label class="form-label">Anschreiben-Stil</label>
        <SegmentedControl
          :modelValue="localTone"
          @update:modelValue="localTone = $event"
          :options="toneOptions"
          :disabled="generating"
        />
      </div>

      <!-- Quick Actions -->
      <div class="quick-confirm-actions">
        <button
          @click="$emit('generate')"
          :disabled="!canGenerate || generating"
          class="zen-btn zen-btn-ai zen-btn-lg"
        >
          <span v-if="generating" class="btn-loading">
            <span class="loading-spinner"></span>
            Generiere Bewerbung...
          </span>
          <span v-else>
            Bewerbung generieren
          </span>
        </button>

        <button
          @click="$emit('load-full-preview')"
          :disabled="loading"
          class="zen-btn zen-btn-secondary"
        >
          <span v-if="loading" class="btn-loading">
            <span class="loading-spinner"></span>
            Lade Details...
          </span>
          <span v-else>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Details bearbeiten
          </span>
        </button>
      </div>

      <p class="usage-info">
        <span v-if="usage?.unlimited">Unbegrenzte Bewerbungen ({{ getPlanLabel() }})</span>
        <span v-else>Noch {{ usage?.remaining || 0 }} von {{ usage?.limit || 3 }} Bewerbungen diesen Monat</span>
      </p>

      <!-- Error Message -->
      <div v-if="error" class="error-box" :class="{ 'error-with-action': isDocMissing || isSubLimitError }">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div class="error-content">
          <span>{{ error }}</span>
          <div v-if="isDocMissing" class="error-actions">
            <router-link to="/documents" class="zen-btn zen-btn-sm">
              Zu den Dokumenten
            </router-link>
          </div>
          <div v-if="isSubLimitError" class="error-actions">
            <router-link to="/subscription" class="zen-btn zen-btn-sm zen-btn-ai">
              Abo upgraden
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import SegmentedControl from '../SegmentedControl.vue'
import { toneOptions } from '../../data/applicationOptions.js'
import { isDocumentMissingError, isSubscriptionLimitError } from '../../utils/errorClassification.js'
import { capitalize } from '../../utils/format.js'

const props = defineProps({
  quickConfirmData: { type: Object, required: true },
  selectedTone: { type: String, default: 'modern' },
  generating: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  canGenerate: { type: Boolean, default: false },
  usage: { type: Object, default: null },
  error: { type: String, default: '' }
})

const emit = defineEmits(['generate', 'load-full-preview', 'reset', 'update:selectedTone'])

const localTone = computed({
  get: () => props.selectedTone,
  set: (val) => emit('update:selectedTone', val)
})

const isDocMissing = computed(() => isDocumentMissingError(props.error))
const isSubLimitError = computed(() => isSubscriptionLimitError(props.error))

function getPlanLabel() {
  return capitalize(props.usage?.plan || 'free')
}
</script>

<style scoped>
.quick-confirm-section {
  max-width: 560px;
}

.quick-confirm-card {
  padding: var(--space-xl);
  text-align: center;
}

.quick-confirm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.quick-confirm-content {
  margin-bottom: var(--space-xl);
}

.quick-confirm-title {
  font-size: 1.5rem;
  font-weight: 400;
  margin: 0 0 var(--space-md) 0;
  color: var(--color-text-primary);
}

.quick-confirm-job {
  font-size: 1.125rem;
  margin: 0;
  line-height: 1.6;
}

.quick-confirm-job strong {
  color: var(--color-ai);
}

.quick-confirm-at {
  color: var(--color-text-secondary);
  margin: 0 var(--space-xs);
}

.quick-confirm-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.quick-confirm-actions .zen-btn-ai {
  width: 100%;
}

.quick-confirm-actions .zen-btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.quick-confirm-actions .zen-btn-secondary:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.tone-selection {
  text-align: left;
  margin-bottom: var(--space-lg);
}

.usage-info {
  text-align: center;
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.error-box {
  text-align: left;
  margin-top: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(180, 80, 80, 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid #b45050;
  color: #b45050;
  font-size: 0.875rem;
}

.error-box svg {
  flex-shrink: 0;
}

.error-box.error-with-action {
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  padding-left: calc(var(--space-md) + 28px);
}

.error-box.error-with-action > svg {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
}

.error-box .error-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  width: 100%;
}

.error-actions {
  margin-top: var(--space-sm);
}

.error-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ai);
  border-color: var(--color-ai);
  text-decoration: none;
}

.error-actions .zen-btn:hover {
  background-color: var(--color-ai);
  color: white;
}

.portal-tag {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.portal-tag.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-tag.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-tag.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-tag.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.reset-btn:hover {
  background: var(--color-washi-warm);
  color: var(--color-text-primary);
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.zen-btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  min-width: 240px;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
