<template>
  <div class="form-card zen-card">
    <div class="form-group">
      <label class="form-label">{{ t('newApplication.jobUrlInput.label') }}</label>
      <div class="url-input-wrapper">
        <svg class="url-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        <input
          v-model="localUrl"
          type="url"
          :placeholder="t('newApplication.jobUrlInput.placeholder')"
          class="form-input url-input"
          :class="{
            'url-valid': showUrlValidation && urlValidation.isValid === true,
            'url-invalid': showUrlValidation && urlValidation.isValid === false
          }"
          :disabled="loading"
          @input="onUrlInput"
          @paste="onUrlPaste"
          @keydown.enter="onUrlEnterPressed"
        />
        <span v-if="showUrlValidation && urlValidation.isValid === true" class="url-validation-icon url-validation-valid">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </span>
        <span v-else-if="showUrlValidation && urlValidation.isValid === false" class="url-validation-icon url-validation-invalid" :title="urlValidation.message">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </span>
        <span v-if="detectedPortal && urlValidation.isValid !== false" :class="['portal-badge', `portal-${detectedPortal.id}`]">
          {{ detectedPortal.name }}
        </span>
      </div>
      <p v-if="showUrlValidation && urlValidation.isValid === false" class="url-validation-message">
        {{ urlValidation.message }}
      </p>
      <p v-else class="form-hint">{{ t('newApplication.jobUrlInput.hint') }}</p>
      <div class="sr-only" aria-live="polite" aria-atomic="true">
        {{ urlValidationAnnouncement }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const urlTouched = ref(false)
let pasteTimeout = null

const localUrl = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const urlValidation = computed(() => {
  const urlValue = props.modelValue.trim()

  if (!urlValue) {
    return { isValid: null, message: '' }
  }

  if (!/^https?:\/\//i.test(urlValue)) {
    return { isValid: false, message: t('newApplication.jobUrlInput.validation.protocol') }
  }

  try {
    const parsedUrl = new URL(urlValue)

    if (!parsedUrl.hostname.includes('.')) {
      return { isValid: false, message: t('newApplication.jobUrlInput.validation.invalidDomain') }
    }

    if (parsedUrl.hostname.endsWith('.')) {
      return { isValid: false, message: t('newApplication.jobUrlInput.validation.domainDot') }
    }

    return { isValid: true, message: '' }
  } catch {
    return { isValid: false, message: t('newApplication.jobUrlInput.validation.invalidFormat') }
  }
})

const showUrlValidation = computed(() => {
  return urlTouched.value && props.modelValue.trim().length > 0
})

const urlValidationAnnouncement = computed(() => {
  if (!showUrlValidation.value) return ''
  if (urlValidation.value.isValid === true) {
    return t('newApplication.jobUrlInput.validation.valid')
  }
  if (urlValidation.value.isValid === false) {
    return t('newApplication.jobUrlInput.validation.invalid', { message: urlValidation.value.message })
  }
  return ''
})

const detectedPortal = computed(() => {
  if (!props.modelValue) return null

  const urlLower = props.modelValue.toLowerCase()

  if (urlLower.includes('stepstone.de')) {
    return { id: 'stepstone', name: 'StepStone' }
  }
  if (urlLower.includes('indeed.com') || urlLower.includes('indeed.de')) {
    return { id: 'indeed', name: 'Indeed' }
  }
  if (urlLower.includes('xing.com')) {
    return { id: 'xing', name: 'XING' }
  }
  if (urlLower.includes('arbeitsagentur.de')) {
    return { id: 'arbeitsagentur', name: 'Arbeitsagentur' }
  }

  if (props.modelValue.startsWith('http')) {
    return { id: 'generic', name: t('newApplication.jobUrlInput.portalOther') }
  }

  return null
})

const onUrlInput = () => {
  urlTouched.value = true
}

const onUrlPaste = () => {
  urlTouched.value = true
  if (pasteTimeout) clearTimeout(pasteTimeout)
  // Delay to let v-model update from pasted content, then auto-submit if valid
  pasteTimeout = setTimeout(() => {
    if (props.modelValue && urlValidation.value.isValid === true && !props.loading) {
      emit('submit', props.modelValue)
    }
  }, 300)
}

const onUrlEnterPressed = (event) => {
  if (props.modelValue && urlValidation.value.isValid === true && !props.loading) {
    event.preventDefault()
    emit('submit', props.modelValue)
  }
}
</script>

<style scoped>
.form-card {
  padding: var(--space-xl);
}

.form-group {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.url-input-wrapper {
  position: relative;
}

.url-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-stone);
  pointer-events: none;
}

.url-input {
  padding-left: calc(var(--space-md) + 28px);
  padding-right: 144px;
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.url-input.url-valid {
  border-color: var(--color-koke);
  box-shadow: 0 0 0 3px rgba(122, 139, 110, 0.15);
}

.url-input.url-invalid {
  border-color: #b45050;
  box-shadow: 0 0 0 3px rgba(180, 80, 80, 0.15);
}

.url-validation-icon {
  position: absolute;
  right: 112px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.url-validation-valid {
  color: var(--color-koke);
  background: rgba(122, 139, 110, 0.15);
}

.url-validation-invalid {
  color: #b45050;
  background: rgba(180, 80, 80, 0.15);
  cursor: help;
}

.url-validation-message {
  font-size: 0.8125rem;
  color: #b45050;
  margin-top: var(--space-xs);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.portal-badge {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.portal-badge.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-badge.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-badge.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-badge.portal-arbeitsagentur {
  background: rgba(0, 68, 103, 0.15);
  color: #004467;
}

.portal-badge.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

@media (max-width: 768px) {
  .url-input {
    padding-right: var(--space-md);
  }

  .url-input.url-valid,
  .url-input.url-invalid {
    padding-right: 50px;
  }

  .url-validation-icon {
    right: var(--space-md);
  }

  .portal-badge {
    position: static;
    transform: none;
    display: inline-block;
    margin-top: var(--space-sm);
  }

  .url-input-wrapper {
    display: flex;
    flex-direction: column;
  }
}
</style>
