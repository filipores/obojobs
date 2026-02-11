<template>
  <Teleport to="body">
    <div v-if="generatedApp" class="premium-reveal-overlay" @click="$emit('close')">
      <div
        class="premium-reveal-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="success-modal-title"
        @click.stop
        @keydown.tab="trapFocus"
      >
        <!-- Close button -->
        <button @click="$emit('close')" class="premium-reveal-close" aria-label="Modal schließen">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>

        <!-- Phase 1: Enso Circle -->
        <div class="premium-reveal-enso" :class="{ 'premium-reveal-enso--visible': revealPhase >= 1 }">
          <EnsoCircle :state="ensoState" size="lg" :duration="600" />
        </div>

        <!-- Phase 2: Content reveal -->
        <div class="premium-reveal-content" :class="{ 'premium-reveal-content--visible': revealPhase >= 2 }">
          <!-- Success header -->
          <div class="premium-reveal-header">
            <h2 id="success-modal-title" class="premium-reveal-title">Bewerbung erstellt</h2>
            <p class="premium-reveal-company">{{ generatedApp.position }} bei <strong>{{ generatedApp.firma }}</strong></p>
          </div>

          <!-- Peek card for intro preview -->
          <div
            v-if="einleitungPreview"
            class="premium-reveal-peek"
            :class="{ 'premium-reveal-peek--expanded': peekExpanded }"
            @mouseenter="peekExpanded = true"
            @mouseleave="peekExpanded = false"
            @click="peekExpanded = !peekExpanded"
          >
            <div class="premium-reveal-peek-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <span class="premium-reveal-peek-label">Vorschau Einstieg</span>
              <svg class="premium-reveal-peek-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>
            <div class="premium-reveal-peek-body">
              <p class="premium-reveal-peek-text">{{ einleitungPreview }}</p>
            </div>
          </div>
        </div>

        <!-- Phase 3: Action buttons -->
        <div class="premium-reveal-actions" :class="{ 'premium-reveal-actions--visible': revealPhase >= 3 }">
          <div class="premium-reveal-buttons">
            <button @click="$emit('download-pdf')" class="zen-btn zen-btn-ai premium-reveal-btn-primary">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              PDF herunterladen
            </button>
            <button @click="$emit('download-email-draft')" class="zen-btn premium-reveal-btn-email">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              E-Mail versenden
            </button>
            <button @click="$emit('go-to-applications')" class="zen-btn premium-reveal-btn-secondary">
              Alle Bewerbungen
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import EnsoCircle from '../application/EnsoCircle.vue'

const props = defineProps({
  generatedApp: { type: Object, default: null },
  revealPhase: { type: Number, default: 0 },
  ensoState: { type: String, default: 'broken' }
})

defineEmits(['close', 'download-pdf', 'go-to-applications', 'download-email-draft'])

const peekExpanded = ref(false)

const einleitungPreview = computed(() => {
  if (!props.generatedApp?.einleitung) return ''
  const text = props.generatedApp.einleitung
  const sentences = text.match(/[^.!?]*[.!?]+/g) || []
  return sentences.slice(0, 3).join(' ').trim()
})

// Reset peek state when modal opens/closes
watch(() => props.generatedApp, () => {
  peekExpanded.value = false
})

// Body scroll lock when modal is open
watch(() => props.generatedApp, (app) => {
  document.body.style.overflow = app ? 'hidden' : ''
})

onUnmounted(() => {
  document.body.style.overflow = ''
})

function trapFocus(e) {
  const focusableElements = e.currentTarget.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const firstFocusable = focusableElements[0]
  const lastFocusable = focusableElements[focusableElements.length - 1]

  const targetFocusable = e.shiftKey ? firstFocusable : lastFocusable
  const wrapFocusable = e.shiftKey ? lastFocusable : firstFocusable

  if (document.activeElement === targetFocusable) {
    e.preventDefault()
    wrapFocusable.focus()
  }
}
</script>

<style scoped>
.premium-reveal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(30, 30, 30, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.premium-reveal-modal {
  width: 100%;
  max-width: 480px;
  max-height: calc(100dvh - 2 * var(--space-lg));
  overflow-y: auto;
  background: var(--color-washi);
  border-radius: var(--radius-lg);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  padding: var(--space-2xl) var(--space-xl) var(--space-xl);
  position: relative;
}

.premium-reveal-close {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
  background: transparent;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  opacity: 0.6;
  transition: opacity var(--transition-base), color var(--transition-base);
  z-index: 10;
}

.premium-reveal-close:hover {
  opacity: 1;
  color: var(--color-sumi);
}

.premium-reveal-enso {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-xl) 0 var(--space-lg);
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.4s var(--ease-zen), transform 0.4s var(--ease-zen);
}

.premium-reveal-enso--visible {
  opacity: 1;
  transform: scale(1);
}

.premium-reveal-content {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s var(--ease-zen) 0.1s, transform 0.5s var(--ease-zen) 0.1s;
}

.premium-reveal-content--visible {
  opacity: 1;
  transform: translateY(0);
}

.premium-reveal-header {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.premium-reveal-title {
  font-size: 1.75rem;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--color-sumi);
  margin: 0 0 var(--space-sm) 0;
}

.premium-reveal-company {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.premium-reveal-company strong {
  color: var(--color-ai);
  font-weight: 500;
}

/* Peek card */
.premium-reveal-peek {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  cursor: pointer;
  transition: border-color 0.2s var(--ease-zen), box-shadow 0.2s var(--ease-zen);
  overflow: hidden;
}

.premium-reveal-peek:hover {
  border-color: var(--color-ai);
  box-shadow: 0 2px 8px rgba(61, 90, 108, 0.08);
}

.premium-reveal-peek-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  font-weight: 500;
}

.premium-reveal-peek-label {
  flex: 1;
}

.premium-reveal-peek-chevron {
  transition: transform 0.2s var(--ease-zen);
  flex-shrink: 0;
}

.premium-reveal-peek--expanded .premium-reveal-peek-chevron {
  transform: rotate(180deg);
}

.premium-reveal-peek-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s var(--ease-zen), padding 0.3s var(--ease-zen);
  padding: 0 var(--space-md);
}

.premium-reveal-peek--expanded .premium-reveal-peek-body {
  max-height: 120px;
  padding: 0 var(--space-md) var(--space-md);
}

.premium-reveal-peek-text {
  font-size: 0.875rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
  margin: 0;
  font-style: italic;
}

/* Actions */
.premium-reveal-actions {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.5s var(--ease-zen), transform 0.5s var(--ease-zen);
  padding-top: var(--space-md);
}

.premium-reveal-actions--visible {
  opacity: 1;
  transform: translateY(0);
}

.premium-reveal-buttons {
  display: flex;
  gap: var(--space-sm);
}

.premium-reveal-btn-primary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.premium-reveal-btn-email {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  background: transparent;
  border: 1px solid var(--color-ai);
  color: var(--color-ai);
}

.premium-reveal-btn-email:hover {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-color: var(--color-ai);
}

.premium-reveal-btn-secondary {
  flex-shrink: 0;
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.premium-reveal-btn-secondary:hover {
  border-color: var(--color-sumi);
  color: var(--color-sumi);
  background: var(--color-washi-warm);
}

@media (max-width: 768px) {
  .premium-reveal-modal {
    padding: var(--space-xl) var(--space-lg) var(--space-lg);
    margin: var(--space-md);
    max-width: calc(100% - var(--space-lg));
  }

  .premium-reveal-title {
    font-size: 1.5rem;
  }

  .premium-reveal-buttons {
    flex-direction: column;
  }

  .premium-reveal-btn-secondary {
    width: 100%;
    justify-content: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .premium-reveal-enso,
  .premium-reveal-content,
  .premium-reveal-actions {
    transition: none;
    opacity: 1;
    transform: none;
  }

  .premium-reveal-peek-body,
  .premium-reveal-peek-chevron {
    transition: none;
  }
}
</style>
