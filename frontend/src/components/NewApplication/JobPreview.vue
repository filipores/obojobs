<template>
  <section class="preview-section animate-fade-up" style="animation-delay: 150ms;">
    <div class="preview-card zen-card">
      <div class="preview-header">
        <div class="preview-title-row">
          <h2>{{ t('newApplication.jobPreview.title') }}</h2>
          <span :class="['portal-tag', `portal-${previewData.portal_id}`]">
            {{ previewData.portal }}
          </span>
        </div>
        <button @click="$emit('reset')" class="reset-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
            <path d="M8 16H3v5"/>
          </svg>
          {{ t('newApplication.jobPreview.reload') }}
        </button>
      </div>

      <!-- Missing Fields Warning -->
      <div v-if="previewData.missing_fields?.length > 0" class="warning-box">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <div>
          <strong>{{ t('newApplication.jobPreview.missingData') }}</strong>
          <p>{{ t('newApplication.jobPreview.missingDataMessage') }} {{ previewData.missing_fields.join(', ') }}</p>
        </div>
      </div>

      <!-- Editable Preview Form -->
      <div class="preview-form">
        <!-- Core Fields Row -->
        <div class="form-row">
          <div class="form-group">
            <label class="form-label required" for="preview-company">{{ t('newApplication.jobPreview.company') }}</label>
            <input
              id="preview-company"
              :value="editableData.company"
              @input="updateField('company', $event.target.value)"
              type="text"
              class="form-input"
              :class="{ 'field-warning': !editableData.company }"
              :placeholder="t('newApplication.jobPreview.companyPlaceholder')"
              required
              aria-required="true"
            />
          </div>
          <div class="form-group">
            <label class="form-label required" for="preview-title">{{ t('newApplication.jobPreview.position') }}</label>
            <input
              id="preview-title"
              :value="editableData.title"
              @input="updateField('title', $event.target.value)"
              type="text"
              class="form-input"
              :class="{ 'field-warning': !editableData.title }"
              :placeholder="t('newApplication.jobPreview.positionPlaceholder')"
              required
              aria-required="true"
            />
          </div>
        </div>

        <!-- Location and Employment Type Row -->
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" for="location-input">{{ t('newApplication.jobPreview.location') }}</label>
            <input
              id="location-input"
              :value="editableData.location"
              @input="updateField('location', $event.target.value)"
              type="text"
              class="form-input"
              :placeholder="t('newApplication.jobPreview.locationPlaceholder')"
            />
          </div>
          <div class="form-group">
            <label class="form-label" for="employment-type-input">{{ t('newApplication.jobPreview.employmentType') }}</label>
            <input
              id="employment-type-input"
              :value="editableData.employment_type"
              @input="updateField('employment_type', $event.target.value)"
              type="text"
              class="form-input"
              :placeholder="t('newApplication.jobPreview.employmentTypePlaceholder')"
            />
          </div>
        </div>

        <!-- Contact Fields Row -->
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" for="contact-person-input">{{ t('newApplication.jobPreview.contactPerson') }}</label>
            <input
              id="contact-person-input"
              :value="editableData.contact_person"
              @input="updateField('contact_person', $event.target.value)"
              type="text"
              class="form-input"
              :placeholder="t('newApplication.jobPreview.contactPersonPlaceholder')"
            />
          </div>
          <div class="form-group">
            <label class="form-label" for="contact-email-input">{{ t('newApplication.jobPreview.contactEmail') }}</label>
            <input
              id="contact-email-input"
              :value="editableData.contact_email"
              @input="updateField('contact_email', $event.target.value)"
              type="email"
              class="form-input"
              :placeholder="t('newApplication.jobPreview.contactEmailPlaceholder')"
            />
          </div>
        </div>

        <!-- Salary (if available) -->
        <div v-if="editableData.salary || previewData.salary" class="form-group">
          <label class="form-label" for="salary-input">{{ t('newApplication.jobPreview.salary') }}</label>
          <input
            id="salary-input"
            :value="editableData.salary"
            @input="updateField('salary', $event.target.value)"
            type="text"
            class="form-input"
            :placeholder="t('newApplication.jobPreview.salaryPlaceholder')"
          />
        </div>

        <!-- Description (collapsible) -->
        <div class="form-group description-group">
          <div
            class="description-header"
            tabindex="0"
            role="button"
            :aria-expanded="showDescription"
            aria-controls="description-content"
            @click="showDescription = !showDescription"
            @keydown.enter.prevent="showDescription = !showDescription"
            @keydown.space.prevent="showDescription = !showDescription"
          >
            <label class="form-label">{{ t('newApplication.jobPreview.description') }}</label>
            <button type="button" class="toggle-btn" tabindex="-1" aria-hidden="true">
              <svg
                :class="['toggle-icon', { rotated: showDescription }]"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
          </div>
          <div v-show="showDescription" id="description-content" class="description-content">
            <textarea
              :value="editableData.description"
              @input="updateField('description', $event.target.value)"
              class="form-textarea"
              rows="8"
              :placeholder="t('newApplication.jobPreview.descriptionPlaceholder')"
            ></textarea>
          </div>
        </div>

      </div>

      <!-- Tone Selection -->
      <div class="form-group tone-selection">
        <label class="form-label">{{ t('newApplication.jobPreview.toneStyle') }}</label>
        <SegmentedControl
          :modelValue="selectedTone"
          @update:modelValue="$emit('update:selectedTone', $event)"
          :options="toneOptions"
          :disabled="generating"
        />
      </div>

      <!-- Generate Button -->
      <div class="form-actions">
        <button
          @click="$emit('generate')"
          :disabled="!canGenerate || generating"
          class="zen-btn zen-btn-ai zen-btn-lg"
          :class="{ 'btn-disabled-limit': isAtUsageLimit }"
        >
          <span v-if="generating" class="btn-loading">
            <span class="loading-spinner"></span>
            {{ t('newApplication.jobPreview.generating') }}
          </span>
          <span v-else-if="isAtUsageLimit">
            {{ t('newApplication.jobPreview.limitReached') }}
          </span>
          <span v-else>
            {{ t('newApplication.jobCard.generateApplication') }}
          </span>
        </button>
        <p v-if="isAtUsageLimit" class="usage-info usage-info-limit">
          <router-link to="/subscription">{{ t('newApplication.jobPreview.upgradeCta') }}</router-link> {{ t('newApplication.jobPreview.upgradeToGenerateMore') }}
        </p>
        <p v-else class="usage-info">
          <span v-if="usage?.unlimited">{{ t('newApplication.jobPreview.unlimitedApps', { plan: getPlanLabel() }) }}</span>
          <span v-else>{{ t('newApplication.jobPreview.remainingApps', { remaining: usage?.remaining || 0, limit: usage?.limit || 3 }) }}</span>
        </p>
      </div>

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
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <line x1="10" y1="9" x2="8" y2="9"/>
              </svg>
              {{ t('newApplication.jobPreview.goToDocuments') }}
            </router-link>
          </div>
          <div v-if="isSubLimitError" class="error-actions">
            <router-link to="/subscription" class="zen-btn zen-btn-sm zen-btn-ai">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
              {{ t('newApplication.jobPreview.upgradeSubscription') }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import SegmentedControl from '../SegmentedControl.vue'
import { toneOptions } from '../../data/applicationOptions.js'
import { isDocumentMissingError, isSubscriptionLimitError } from '../../utils/errorClassification.js'
import { capitalize } from '../../utils/format.js'

const { t } = useI18n()

const props = defineProps({
  previewData: { type: Object, required: true },
  editableData: { type: Object, required: true },
  selectedTone: { type: String, default: 'modern' },
  generating: { type: Boolean, default: false },
  canGenerate: { type: Boolean, default: false },
  isAtUsageLimit: { type: Boolean, default: false },
  usage: { type: Object, default: null },
  error: { type: String, default: '' }
})

const emit = defineEmits(['reset', 'generate', 'update:editableData', 'update:selectedTone'])

const showDescription = ref(false)

const isDocMissing = computed(() => isDocumentMissingError(props.error))
const isSubLimitError = computed(() => isSubscriptionLimitError(props.error))

function getPlanLabel() {
  return capitalize(props.usage?.plan || 'free')
}

function updateField(field, value) {
  emit('update:editableData', { ...props.editableData, [field]: value })
}
</script>

<style scoped>
.preview-section {
  max-width: 800px;
}

.preview-card {
  padding: var(--space-xl);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.preview-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.preview-title-row h2 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
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

.warning-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(201, 162, 39, 0.1);
  border: 1px solid rgba(201, 162, 39, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.warning-box svg {
  flex-shrink: 0;
  color: #c9a227;
}

.warning-box strong {
  display: block;
  color: #8a6d17;
  margin-bottom: var(--space-xs);
  font-size: 0.875rem;
}

.warning-box p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.preview-form {
  margin-bottom: var(--space-lg);
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.field-warning {
  border-color: rgba(201, 162, 39, 0.5);
  background: rgba(201, 162, 39, 0.05);
}

.description-group {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.description-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.description-header .form-label {
  margin-bottom: 0;
  cursor: pointer;
}

.toggle-btn {
  background: none;
  border: none;
  padding: var(--space-xs);
  cursor: pointer;
  color: var(--color-text-tertiary);
}

.toggle-icon {
  transition: transform var(--transition-base);
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.description-content {
  margin-top: var(--space-md);
}

.tone-selection {
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
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

.usage-info {
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.usage-info-limit {
  color: var(--color-error);
}

.usage-info-limit a {
  color: var(--color-ai);
  font-weight: 500;
  text-decoration: none;
}

.usage-info-limit a:hover {
  text-decoration: underline;
}

.btn-disabled-limit {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-box {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(180, 80, 80, 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid #b45050;
  margin-top: var(--space-lg);
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

@media (max-width: 768px) {
  .preview-card {
    padding: var(--space-lg);
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .zen-btn-lg {
    width: 100%;
  }
}
</style>
