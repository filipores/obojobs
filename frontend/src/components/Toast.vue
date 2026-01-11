<template>
  <transition-group name="toast-fade" tag="div" class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', toast.type]"
    >
      <span class="toast-icon">{{ getIcon(toast.type) }}</span>
      <span class="toast-message">{{ toast.message }}</span>
      <button @click="remove(toast.id)" class="toast-close">✕</button>
    </div>
  </transition-group>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])

const add = (message, type = 'info', duration = 3000) => {
  const id = Date.now()
  toasts.value.push({ id, message, type })

  if (duration > 0) {
    setTimeout(() => remove(id), duration)
  }
}

const remove = (id) => {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

const getIcon = (type) => {
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ⓘ'
  }
  return icons[type] || icons.info
}

defineExpose({ add, remove })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 400px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  background: white;
  border-left: 4px solid;
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  border-left-color: #28a745;
}

.toast.error {
  border-left-color: #dc3545;
}

.toast.warning {
  border-left-color: #ffc107;
}

.toast.info {
  border-left-color: #17a2b8;
}

.toast-icon {
  font-size: 1.2em;
  font-weight: bold;
}

.toast.success .toast-icon {
  color: #28a745;
}

.toast.error .toast-icon {
  color: #dc3545;
}

.toast.warning .toast-icon {
  color: #ffc107;
}

.toast.info .toast-icon {
  color: #17a2b8;
}

.toast-message {
  flex: 1;
  font-size: 0.95em;
}

.toast-close {
  background: none;
  border: none;
  font-size: 1.2em;
  cursor: pointer;
  opacity: 0.6;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-close:hover {
  opacity: 1;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s ease;
}

.toast-fade-enter-from {
  transform: translateX(400px);
  opacity: 0;
}

.toast-fade-leave-to {
  transform: translateX(400px);
  opacity: 0;
}
</style>
