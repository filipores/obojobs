<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isVisible"
        class="confirm-overlay"
        @click="handleCancel"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        :aria-describedby="messageId"
      >
        <div class="confirm-modal zen-card animate-fade-up" @click.stop>
          <div class="confirm-header">
            <div class="confirm-icon" :class="type">
              <svg v-if="type === 'danger'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <h2 :id="titleId">{{ title }}</h2>
          </div>
          <p :id="messageId" class="confirm-message">{{ message }}</p>

          <!-- Optional checkbox -->
          <div v-if="showCheckbox" class="confirm-checkbox">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="checkboxChecked"
                :id="checkboxId"
              />
              <span class="checkbox-text">{{ checkboxLabel }}</span>
            </label>
          </div>

          <div class="confirm-actions">
            <button
              ref="cancelButton"
              @click="handleCancel"
              class="zen-btn"
              type="button"
            >
              {{ cancelText }}
            </button>
            <button
              ref="confirmButton"
              @click="handleConfirm"
              class="zen-btn"
              :class="type === 'danger' ? 'zen-btn-danger' : 'zen-btn-filled'"
              type="button"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Bestätigung'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: 'Bestätigen'
  },
  cancelText: {
    type: String,
    default: 'Abbrechen'
  },
  type: {
    type: String,
    default: 'default', // 'default' or 'danger'
    validator: (val) => ['default', 'danger'].includes(val)
  },
  showCheckbox: {
    type: Boolean,
    default: false
  },
  checkboxLabel: {
    type: String,
    default: ''
  },
  checkboxDefault: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['confirm', 'cancel', 'update:visible'])

const isVisible = ref(props.visible)
const confirmButton = ref(null)
const cancelButton = ref(null)
const checkboxChecked = ref(props.checkboxDefault)
const titleId = `confirm-title-${Date.now()}`
const messageId = `confirm-message-${Date.now()}`
const checkboxId = `confirm-checkbox-${Date.now()}`

watch(() => props.visible, (newVal) => {
  isVisible.value = newVal
  if (newVal) {
    // Reset checkbox to default when modal opens
    checkboxChecked.value = props.checkboxDefault
    nextTick(() => {
      cancelButton.value?.focus()
    })
  }
})

const handleConfirm = () => {
  isVisible.value = false
  emit('update:visible', false)
  emit('confirm', { checkboxChecked: checkboxChecked.value })
}

const handleCancel = () => {
  isVisible.value = false
  emit('update:visible', false)
  emit('cancel')
}

const handleKeydown = (e) => {
  if (!isVisible.value) return
  if (e.key === 'Escape') {
    handleCancel()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(44, 44, 44, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.confirm-modal {
  width: 100%;
  max-width: 420px;
  padding: var(--space-xl);
  text-align: center;
}

.confirm-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.confirm-header h2 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
  color: var(--color-sumi);
}

.confirm-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-icon.danger {
  background: var(--color-error-light);
  color: var(--color-error);
}

.confirm-icon.default {
  background: rgba(61, 90, 108, 0.1);
  color: var(--color-ai);
}

.confirm-message {
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-xl) 0;
  line-height: 1.6;
}

.confirm-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
}

.confirm-actions .zen-btn {
  min-width: 120px;
}

/* Checkbox */
.confirm-checkbox {
  margin-bottom: var(--space-lg);
  text-align: left;
  background: var(--color-washi-warm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-sand);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
  font-size: 0.9375rem;
  color: var(--color-sumi);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-ai);
  cursor: pointer;
}

.checkbox-text {
  flex: 1;
}

/* Transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-active .confirm-modal,
.modal-fade-leave-active .confirm-modal {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .confirm-modal,
.modal-fade-leave-to .confirm-modal {
  transform: scale(0.95);
  opacity: 0;
}

@media (max-width: 480px) {
  .confirm-actions {
    flex-direction: column;
  }

  .confirm-actions .zen-btn {
    width: 100%;
  }
}
</style>
