<template>
  <transition-group
    name="toast-fade"
    tag="div"
    class="toast-container"
    aria-live="polite"
    aria-label="Benachrichtigungen"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', toast.type]"
      :role="getRole(toast.type)"
      :aria-live="getAriaLive(toast.type)"
    >
      <span class="toast-icon" aria-hidden="true">{{ getIcon(toast.type) }}</span>
      <div class="toast-body">
        <span class="toast-message">{{ toast.message }}</span>
        <router-link
          v-if="toast.action"
          :to="toast.action.route"
          class="toast-action"
          @click="remove(toast.id)"
        >{{ toast.action.label }}</router-link>
      </div>
      <button
        @click="remove(toast.id)"
        class="toast-close"
        aria-label="Benachrichtigung schließen"
      >✕</button>
    </div>
  </transition-group>
</template>

<script setup>
import { ref } from 'vue'

let nextId = 1

const toasts = ref([])
const recentMessages = ref(new Map()) // Track recent messages for deduplication
const DEDUPE_WINDOW_MS = 2000 // Don't show same/similar message within 2 seconds

// Normalize message for deduplication comparison
const normalizeMessage = (msg) => {
  return msg
    .toLowerCase()
    .replace(/[^\wäöüß\s]/g, '') // Remove punctuation
    .replace(/\s+/g, ' ')        // Normalize whitespace
    .trim()
}

// Check if two messages are similar (for deduplication)
const isSimilarMessage = (msg1, msg2) => {
  const norm1 = normalizeMessage(msg1)
  const norm2 = normalizeMessage(msg2)

  // Exact match after normalization
  if (norm1 === norm2) return true

  // Check if one contains the other (for partial matches like "Fehler" vs "Fehler beim...")
  if (norm1.includes(norm2) || norm2.includes(norm1)) return true

  // Check common error keywords in both
  const errorKeywords = ['fehler', 'error', 'ungültig', 'invalid', 'nicht gefunden', 'verbinden']
  const hasCommonKeyword = errorKeywords.some(
    keyword => norm1.includes(keyword) && norm2.includes(keyword)
  )
  if (hasCommonKeyword && norm1.length < 50 && norm2.length < 50) {
    // Both are short error messages with common keywords - likely duplicates
    return true
  }

  return false
}

const add = (message, type = 'info', duration = 3000) => {
  const now = Date.now()

  // Deduplicate: Check if same or similar message was shown recently
  for (const [key, { timestamp, originalMessage }] of recentMessages.value.entries()) {
    if ((now - timestamp) < DEDUPE_WINDOW_MS) {
      const [storedType] = key.split(':')
      // Check if same type and similar message
      if (storedType === type && isSimilarMessage(message, originalMessage)) {
        // Skip duplicate message
        return
      }
    }
  }

  // Track this message
  const dedupeKey = `${type}:${now}`
  recentMessages.value.set(dedupeKey, { timestamp: now, originalMessage: message })

  // Clean up old entries (prevent memory leak)
  if (recentMessages.value.size > 50) {
    const cutoff = now - DEDUPE_WINDOW_MS * 2
    for (const [key, { timestamp }] of recentMessages.value.entries()) {
      if (timestamp < cutoff) {
        recentMessages.value.delete(key)
      }
    }
  }

  const id = nextId++
  toasts.value.push({ id, message, type })

  if (duration > 0) {
    setTimeout(() => remove(id), duration)
  }

  return id
}

const update = (id, message, type, options = {}) => {
  const toast = toasts.value.find(t => t.id === id)
  if (!toast) return

  toast.message = message
  if (type) toast.type = type
  if (options.action) toast.action = options.action
  if (options.duration > 0) {
    setTimeout(() => remove(id), options.duration)
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

// ARIA role: 'alert' for critical messages (error, warning), 'status' for non-critical
const getRole = (type) => {
  return (type === 'error' || type === 'warning') ? 'alert' : 'status'
}

// ARIA live: 'assertive' for critical messages, 'polite' for non-critical
const getAriaLive = (type) => {
  return (type === 'error' || type === 'warning') ? 'assertive' : 'polite'
}

defineExpose({ add, update, remove })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: var(--z-toast);
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
  border-left-color: var(--color-success);
}

.toast.error {
  border-left-color: var(--color-error);
}

.toast.warning {
  border-left-color: var(--color-warning);
}

.toast.info {
  border-left-color: var(--color-ai);
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

.toast-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.toast-message {
  font-size: 0.95em;
}

.toast-action {
  font-size: 0.85em;
  font-weight: 500;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
  opacity: 0.9;
}

.toast-action:hover {
  opacity: 1;
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
