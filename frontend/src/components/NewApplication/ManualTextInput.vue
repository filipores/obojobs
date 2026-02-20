<template>
  <div class="manual-fallback-section manual-fallback-expanding">
    <div class="manual-fallback-header">
      <div class="manual-fallback-enso">
        <EnsoCircle state="breathing" size="md" color="var(--color-ai)" :duration="4000" />
      </div>
      <div class="manual-fallback-intro">
        <h3>{{ t('newApplication.manualTextInput.title') }}</h3>
        <p>{{ t('newApplication.manualTextInput.description') }}</p>
      </div>
      <button @click="$emit('close')" class="close-fallback-btn" :aria-label="t('newApplication.manualTextInput.close')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="manual-fallback-fields">
      <div class="form-row manual-compact-row">
        <div class="form-group">
          <label class="form-label">{{ t('newApplication.manualTextInput.companyLabel') }}</label>
          <input
            v-model="manualCompany"
            type="text"
            class="form-input"
            :placeholder="t('newApplication.manualTextInput.companyPlaceholder')"
            :disabled="analyzingManualText"
          />
        </div>

        <div class="form-group">
          <label class="form-label">{{ t('newApplication.manualTextInput.positionLabel') }}</label>
          <input
            v-model="manualTitle"
            type="text"
            class="form-input"
            :placeholder="t('newApplication.manualTextInput.positionPlaceholder')"
            :disabled="analyzingManualText"
          />
        </div>
      </div>

      <div class="form-group manual-text-group">
        <label class="form-label required" for="manual-job-text">{{ t('newApplication.manualTextInput.jobTextLabel') }}</label>
        <textarea
          id="manual-job-text"
          ref="manualTextareaRef"
          v-model="manualJobText"
          class="form-textarea manual-text-area"
          rows="10"
          :placeholder="t('newApplication.manualTextInput.jobTextPlaceholder')"
          :disabled="analyzingManualText"
          required
          aria-required="true"
        ></textarea>
        <p class="form-hint">
          <span v-if="manualJobText.length > 0" class="char-count" :class="{ 'char-count--valid': canAnalyzeManualText }">
            {{ manualJobText.length }} / 100 {{ t('newApplication.manualTextInput.chars') }}
          </span>
          <span v-else>{{ t('newApplication.manualTextInput.minChars') }}</span>
        </p>
      </div>

      <div v-if="manualTextError" class="manual-error-hint">
        {{ manualTextError }}
      </div>

      <div class="form-actions manual-actions">
        <button
          @click="handleAnalyze"
          :disabled="!canAnalyzeManualText || analyzingManualText"
          class="zen-btn zen-btn-ai zen-btn-lg"
        >
          <span v-if="analyzingManualText" class="btn-loading">
            <EnsoCircle state="rotating" size="sm" color="currentColor" :duration="1500" />
            <span>{{ t('newApplication.manualTextInput.analyzing') }}</span>
          </span>
          <span v-else>
            {{ t('newApplication.manualTextInput.createApplication') }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import EnsoCircle from '../application/EnsoCircle.vue'

const { t } = useI18n()

defineProps({
  analyzingManualText: { type: Boolean, default: false }
})

const emit = defineEmits(['analyze', 'close'])

const manualJobText = ref('')
const manualCompany = ref('')
const manualTitle = ref('')
const manualTextError = ref('')
const manualTextareaRef = ref(null)

const canAnalyzeManualText = computed(() => {
  return manualJobText.value.trim().length >= 100
})

const handleAnalyze = () => {
  emit('analyze', {
    jobText: manualJobText.value,
    company: manualCompany.value,
    title: manualTitle.value
  })
}

defineExpose({
  manualJobText,
  manualCompany,
  manualTitle,
  manualTextError
})
</script>

<style scoped>
.manual-fallback-section {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.manual-fallback-expanding {
  animation: manual-expand-in 0.5s var(--ease-zen) forwards;
  background: linear-gradient(180deg, var(--color-washi) 0%, var(--color-washi-warm) 100%);
  border: 1px solid var(--color-border-light);
}

.manual-fallback-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}

.manual-fallback-enso {
  flex-shrink: 0;
}

.manual-fallback-intro {
  flex: 1;
}

.manual-fallback-intro h3 {
  font-size: 1.25rem;
  font-weight: 400;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
}

.manual-fallback-intro p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.manual-fallback-fields {
  animation: manual-fields-appear 0.4s var(--ease-zen) 0.2s forwards;
  opacity: 0;
}

.manual-compact-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}

.manual-text-group {
  margin-top: var(--space-md);
}

.manual-text-group .form-textarea {
  transition: min-height 0.3s var(--ease-zen), box-shadow 0.2s var(--ease-zen);
}

.manual-text-group .form-textarea:focus {
  min-height: 280px;
  box-shadow: 0 0 0 3px var(--color-ai-subtle);
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

.form-label.required::after {
  content: ' *';
  color: #b45050;
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.char-count {
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.char-count--valid {
  color: var(--color-koke);
}

.manual-error-hint {
  font-size: 0.875rem;
  color: #b45050;
  padding: var(--space-sm) var(--space-md);
  background: rgba(180, 80, 80, 0.08);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.manual-actions {
  margin-top: var(--space-lg);
}

.manual-actions .btn-loading {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.manual-text-area {
  min-height: 200px;
  resize: vertical;
}

.form-actions {
  text-align: center;
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

.close-fallback-btn {
  background: transparent;
  border: none;
  padding: var(--space-xs);
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.close-fallback-btn:hover {
  background: var(--color-washi);
  color: var(--color-sumi);
}

@keyframes manual-expand-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
    max-height: 0;
  }
  to {
    opacity: 1;
    transform: translateY(0);
    max-height: 1000px;
  }
}

@keyframes manual-fields-appear {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .manual-compact-row {
    grid-template-columns: 1fr;
  }

  .manual-fallback-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>
