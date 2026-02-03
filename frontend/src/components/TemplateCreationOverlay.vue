<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="isVisible"
        class="creation-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="Neue Vorlage erstellen"
      >
        <!-- Background -->
        <div class="creation-overlay__backdrop" @click="handleBackdropClick" />

        <!-- Main content -->
        <div class="creation-overlay__content">
          <!-- Close button -->
          <button class="creation-overlay__close" @click="close" aria-label="Schließen">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>

          <!-- Breathing enso -->
          <div class="creation-overlay__enso">
            <EnsoCircle
              state="breathing"
              size="lg"
              :duration="4000"
            />
          </div>

          <!-- Urgency promise -->
          <div class="creation-overlay__promise">
            <span class="promise-badge">60 Sekunden</span>
            <span class="promise-text">zur perfekten Vorlage</span>
          </div>

          <!-- Main question -->
          <h2 class="creation-overlay__title">Beschreib dich in einem Satz</h2>
          <p class="creation-overlay__subtitle">Was machst du beruflich? Wofür brennst du?</p>

          <!-- Text input -->
          <div class="creation-overlay__input-container">
            <textarea
              ref="inputRef"
              v-model="userDescription"
              class="creation-overlay__input"
              placeholder="z.B. Frontend-Entwickler mit Leidenschaft für intuitive Benutzeroberflächen"
              rows="2"
              @keydown.enter.prevent="handleSubmit"
            />
          </div>

          <!-- OR divider -->
          <div class="creation-overlay__divider">
            <span>oder starte mit einer Kategorie</span>
          </div>

          <!-- Category chips -->
          <div class="creation-overlay__categories">
            <button
              v-for="category in categories"
              :key="category.id"
              class="category-chip"
              :class="{ 'category-chip--selected': selectedCategory === category.id }"
              @click="selectCategory(category)"
            >
              <span class="category-chip__icon">{{ category.icon }}</span>
              <span class="category-chip__label">{{ category.label }}</span>
            </button>
          </div>

          <!-- Submit button -->
          <button
            class="creation-overlay__submit zen-btn zen-btn-filled"
            :disabled="!canSubmit"
            @click="handleSubmit"
          >
            Vorlage erstellen
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import EnsoCircle from './application/EnsoCircle.vue'

const props = defineProps({
  isActive: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'submit'])

const isVisible = ref(false)
const userDescription = ref('')
const selectedCategory = ref(null)
const inputRef = ref(null)

const categories = [
  { id: 'tech', label: 'Tech / IT', icon: '💻', defaultDescription: 'Softwareentwickler mit Fokus auf moderne Technologien' },
  { id: 'sales', label: 'Vertrieb', icon: '🤝', defaultDescription: 'Vertriebsprofi mit Leidenschaft für Kundenbeziehungen' },
  { id: 'marketing', label: 'Marketing', icon: '📣', defaultDescription: 'Marketing-Spezialist mit kreativem Ansatz' },
  { id: 'other', label: 'Andere', icon: '✨', defaultDescription: '' }
]

const canSubmit = computed(() => {
  return userDescription.value.trim().length > 0 || selectedCategory.value !== null
})

const selectCategory = (category) => {
  if (selectedCategory.value === category.id) {
    selectedCategory.value = null
  } else {
    selectedCategory.value = category.id
    if (category.defaultDescription && !userDescription.value.trim()) {
      userDescription.value = category.defaultDescription
    }
  }
}

const handleSubmit = () => {
  if (!canSubmit.value) return

  const description = userDescription.value.trim() ||
    categories.find(c => c.id === selectedCategory.value)?.defaultDescription || ''

  emit('submit', {
    description,
    category: selectedCategory.value
  })
}

const close = () => {
  isVisible.value = false
  setTimeout(() => {
    emit('close')
  }, 300)
}

const handleBackdropClick = (e) => {
  if (e.target === e.currentTarget) {
    close()
  }
}

watch(() => props.isActive, async (active) => {
  if (active) {
    userDescription.value = ''
    selectedCategory.value = null
    isVisible.value = true
    await nextTick()
    inputRef.value?.focus()
  } else {
    isVisible.value = false
  }
})
</script>

<style scoped>
.creation-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.creation-overlay__backdrop {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    var(--color-washi) 0%,
    var(--color-washi-warm) 50%,
    var(--color-washi-aged) 100%
  );
  opacity: 0.98;
}

.creation-overlay__content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma-xl) var(--space-ma);
  max-width: 600px;
  width: 100%;
  text-align: center;
}

/* Close button */
.creation-overlay__close {
  position: absolute;
  top: var(--space-lg);
  right: var(--space-lg);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.creation-overlay__close:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

/* Enso */
.creation-overlay__enso {
  margin-bottom: var(--space-lg);
}

/* Promise badge */
.creation-overlay__promise {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-ma);
}

.promise-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.promise-text {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
}

/* Title */
.creation-overlay__title {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
  color: var(--color-sumi);
  letter-spacing: -0.02em;
  margin: 0 0 var(--space-sm);
}

.creation-overlay__subtitle {
  font-size: 1rem;
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-lg);
}

/* Input */
.creation-overlay__input-container {
  width: 100%;
  margin-bottom: var(--space-lg);
}

.creation-overlay__input {
  width: 100%;
  padding: var(--space-lg);
  background: var(--color-bg-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 1.125rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-primary);
  resize: none;
  transition: all var(--transition-base);
}

.creation-overlay__input:focus {
  outline: none;
  border-color: var(--color-ai);
  box-shadow: 0 0 0 4px var(--color-ai-subtle);
}

.creation-overlay__input::placeholder {
  color: var(--color-text-ghost);
}

/* Divider */
.creation-overlay__divider {
  display: flex;
  align-items: center;
  width: 100%;
  margin-bottom: var(--space-lg);
}

.creation-overlay__divider::before,
.creation-overlay__divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border-light);
}

.creation-overlay__divider span {
  padding: 0 var(--space-md);
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Categories */
.creation-overlay__categories {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-ma);
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-bg-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.category-chip:hover {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.category-chip--selected {
  border-color: var(--color-ai);
  background: var(--color-ai);
  color: var(--color-text-inverse);
}

.category-chip__icon {
  font-size: 1.125rem;
}

.category-chip__label {
  font-weight: 500;
}

/* Submit */
.creation-overlay__submit {
  min-width: 200px;
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
}

.creation-overlay__submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Transitions */
.overlay-enter-active {
  animation: overlayEnter 0.4s var(--ease-zen);
}

.overlay-leave-active {
  animation: overlayLeave 0.3s var(--ease-zen);
}

@keyframes overlayEnter {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

@keyframes overlayLeave {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

/* Content entrance */
.overlay-enter-active .creation-overlay__content {
  animation: contentEnter 0.5s var(--ease-zen) 0.1s both;
}

@keyframes contentEnter {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .overlay-enter-active,
  .overlay-leave-active {
    animation: none;
    transition: opacity 0.2s;
  }

  .overlay-enter-active .creation-overlay__content {
    animation: none;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .creation-overlay__content {
    padding: var(--space-ma) var(--space-lg);
  }

  .creation-overlay__close {
    top: var(--space-md);
    right: var(--space-md);
  }

  .creation-overlay__input {
    font-size: 1rem;
    padding: var(--space-md);
  }

  .category-chip {
    padding: var(--space-sm) var(--space-md);
    font-size: 0.875rem;
  }
}
</style>
