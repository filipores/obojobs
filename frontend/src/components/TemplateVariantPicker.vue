<template>
  <Teleport to="body">
    <Transition name="picker">
      <div
        v-if="isVisible"
        class="variant-picker"
        role="dialog"
        aria-modal="true"
        aria-label="Vorlage auswählen"
      >
        <!-- Background -->
        <div class="variant-picker__backdrop" />

        <!-- Main content -->
        <div class="variant-picker__container">
          <!-- Close button -->
          <button class="variant-picker__close" @click="close" aria-label="Schließen">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>

          <!-- Loading State -->
          <div v-if="loading" class="variant-picker__loading">
            <div class="loading-enso">
              <EnsoCircle
                state="rotating"
                size="lg"
                :duration="2000"
              />
            </div>
            <div class="loading-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${progress}%` }" />
              </div>
              <p class="loading-text">{{ loadingText }}</p>
            </div>
          </div>

          <!-- Variants Display -->
          <div v-else class="variant-picker__content">
            <div class="variant-picker__header">
              <h2 class="variant-picker__title">Wähle deinen Stil</h2>
              <p class="variant-picker__subtitle">Drei Varianten, ein Klick zur perfekten Vorlage</p>
            </div>

            <!-- Variant Cards -->
            <div class="variant-cards">
              <div
                v-for="variant in variants"
                :key="variant.key"
                class="variant-card"
                :class="{ 'variant-card--selected': selectedVariant === variant.key }"
                @click="selectVariant(variant)"
                @mouseenter="hoveredVariant = variant.key"
                @mouseleave="hoveredVariant = null"
              >
                <div class="variant-card__header">
                  <span class="variant-card__badge" :class="`variant-card__badge--${variant.key}`">
                    {{ variant.name }}
                  </span>
                  <span class="variant-card__hint">{{ variant.hint }}</span>
                </div>

                <div class="variant-card__preview" :class="{ 'variant-card__preview--expanded': hoveredVariant === variant.key }">
                  <p>{{ getPreviewText(variant) }}</p>
                </div>

                <div class="variant-card__footer">
                  <div v-if="selectedVariant === variant.key" class="selected-indicator">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Ausgewählt
                  </div>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="variant-picker__actions">
              <button class="zen-btn" @click="close">
                Abbrechen
              </button>
              <button
                class="zen-btn zen-btn-filled"
                :disabled="!selectedVariant"
                @click="confirmSelection"
              >
                Vorlage übernehmen
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import EnsoCircle from './application/EnsoCircle.vue'

const props = defineProps({
  isActive: {
    type: Boolean,
    default: false
  },
  variants: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'select'])

const isVisible = ref(false)
const selectedVariant = ref(null)
const hoveredVariant = ref(null)
const progress = ref(0)
let progressInterval = null

const loadingTexts = [
  'Analysiere deine Beschreibung...',
  'Erstelle professionelle Variante...',
  'Gestalte moderne Version...',
  'Generiere kreative Alternative...',
  'Finalisiere Vorlagen...'
]

const loadingText = computed(() => {
  const index = Math.min(Math.floor(progress.value / 25), loadingTexts.length - 1)
  return loadingTexts[index]
})

const getPreviewText = (variant) => {
  const preview = variant.preview || ''
  const isExpanded = hoveredVariant.value === variant.key
  const maxLength = isExpanded ? 600 : 200

  if (preview.length <= maxLength) return preview
  return preview.substring(0, maxLength) + '...'
}

const selectVariant = (variant) => {
  selectedVariant.value = variant.key
}

const confirmSelection = () => {
  if (!selectedVariant.value) return

  const variant = props.variants.find(v => v.key === selectedVariant.value)
  if (variant) {
    emit('select', variant)
  }
  close()
}

const close = () => {
  isVisible.value = false
  stopProgressSimulation()
  setTimeout(() => {
    emit('close')
  }, 300)
}

const startProgressSimulation = () => {
  progress.value = 0
  progressInterval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 15
    }
  }, 500)
}

const stopProgressSimulation = () => {
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
}

watch(() => props.isActive, (active) => {
  if (active) {
    selectedVariant.value = null
    hoveredVariant.value = null
    isVisible.value = true
    if (props.loading) {
      startProgressSimulation()
    }
  } else {
    isVisible.value = false
    stopProgressSimulation()
  }
})

watch(() => props.loading, (isLoading) => {
  if (isLoading) {
    startProgressSimulation()
  } else {
    progress.value = 100
    setTimeout(() => {
      stopProgressSimulation()
    }, 300)
  }
})

onUnmounted(() => {
  stopProgressSimulation()
})
</script>

<style scoped>
.variant-picker {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
  padding: var(--space-lg);
}

.variant-picker__backdrop {
  position: fixed;
  inset: 0;
  background: linear-gradient(
    135deg,
    var(--color-washi) 0%,
    var(--color-washi-warm) 50%,
    var(--color-washi-aged) 100%
  );
  opacity: 0.98;
}

.variant-picker__container {
  position: relative;
  width: 100%;
  max-width: 1100px;
  margin: auto;
}

.variant-picker__close {
  position: absolute;
  top: 0;
  right: 0;
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
  z-index: 10;
}

.variant-picker__close:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

/* Loading State */
.variant-picker__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.loading-enso {
  margin-bottom: var(--space-xl);
}

.loading-progress {
  width: 100%;
  max-width: 300px;
}

.progress-bar {
  height: 6px;
  background: var(--color-sand);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--space-md);
}

.progress-fill {
  height: 100%;
  background: var(--color-ai);
  border-radius: var(--radius-full);
  transition: width 0.3s var(--ease-zen);
}

.loading-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Content */
.variant-picker__content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.variant-picker__header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.variant-picker__title {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
  color: var(--color-sumi);
  letter-spacing: -0.02em;
  margin: 0 0 var(--space-sm);
}

.variant-picker__subtitle {
  font-size: 1rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

/* Variant Cards */
.variant-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
  width: 100%;
  margin-bottom: var(--space-xl);
}

.variant-card {
  background: var(--color-bg-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  flex-direction: column;
  min-height: 320px;
}

.variant-card:hover {
  border-color: var(--color-ai);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.variant-card--selected {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.variant-card__header {
  margin-bottom: var(--space-md);
}

.variant-card__badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-full);
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  margin-bottom: var(--space-xs);
}

.variant-card__badge--professional {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.variant-card__badge--modern {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.variant-card__badge--creative {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
}

.variant-card__hint {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-ghost);
}

.variant-card__preview {
  flex: 1;
  overflow: hidden;
  transition: all var(--transition-smooth);
}

.variant-card__preview p {
  font-size: 0.875rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
  margin: 0;
  white-space: pre-wrap;
}

.variant-card__preview--expanded {
  max-height: none;
}

.variant-card__footer {
  margin-top: var(--space-md);
  min-height: 24px;
}

.selected-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-ai);
}

/* Actions */
.variant-picker__actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
}

/* Transitions */
.picker-enter-active {
  animation: pickerEnter 0.4s var(--ease-zen);
}

.picker-leave-active {
  animation: pickerLeave 0.3s var(--ease-zen);
}

@keyframes pickerEnter {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

@keyframes pickerLeave {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.picker-enter-active .variant-picker__container {
  animation: containerEnter 0.5s var(--ease-zen) 0.1s both;
}

@keyframes containerEnter {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Variant cards stagger animation */
.picker-enter-active .variant-card:nth-child(1) {
  animation: cardEnter 0.4s var(--ease-zen) 0.2s both;
}
.picker-enter-active .variant-card:nth-child(2) {
  animation: cardEnter 0.4s var(--ease-zen) 0.3s both;
}
.picker-enter-active .variant-card:nth-child(3) {
  animation: cardEnter 0.4s var(--ease-zen) 0.4s both;
}

@keyframes cardEnter {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .picker-enter-active,
  .picker-leave-active,
  .picker-enter-active .variant-picker__container,
  .picker-enter-active .variant-card {
    animation: none;
    transition: opacity 0.2s;
  }
}

/* Responsive */
@media (max-width: 968px) {
  .variant-cards {
    grid-template-columns: 1fr;
    max-width: 500px;
  }

  .variant-card {
    min-height: auto;
  }
}

@media (max-width: 480px) {
  .variant-picker {
    padding: var(--space-md);
  }

  .variant-picker__actions {
    flex-direction: column;
    width: 100%;
  }

  .variant-picker__actions button {
    width: 100%;
  }
}
</style>
