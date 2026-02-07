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

          <!-- Einleitung preview - the "holy shit" moment -->
          <div v-if="einleitungPreview" class="premium-reveal-einleitung">
            <div class="premium-reveal-einleitung-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
              </svg>
              Dein personalisierter Einstieg
            </div>
            <p class="premium-reveal-einleitung-text">{{ einleitungPreview }}</p>
          </div>

          <!-- Subject line preview -->
          <div v-if="generatedApp.betreff" class="premium-reveal-betreff">
            <div class="premium-reveal-betreff-label">Betreff</div>
            <p class="premium-reveal-betreff-text">{{ generatedApp.betreff }}</p>
          </div>
        </div>

        <!-- Phase 3: PDF card and actions -->
        <div class="premium-reveal-actions" :class="{ 'premium-reveal-actions--visible': revealPhase >= 3 }">
          <!-- PDF Preview Card -->
          <div class="premium-reveal-pdf-card" @click="$emit('download-pdf')">
            <div class="premium-reveal-pdf-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <line x1="10" y1="9" x2="8" y2="9"/>
              </svg>
            </div>
            <div class="premium-reveal-pdf-info">
              <span class="premium-reveal-pdf-name">Anschreiben_{{ generatedApp.firma }}.pdf</span>
              <span class="premium-reveal-pdf-action">Klicken zum Herunterladen</span>
            </div>
            <div class="premium-reveal-pdf-download">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="premium-reveal-buttons">
            <button @click="$emit('download-pdf')" class="zen-btn zen-btn-ai zen-btn-lg premium-reveal-btn-primary">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              PDF herunterladen
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
import { computed } from 'vue'
import EnsoCircle from '../application/EnsoCircle.vue'

const props = defineProps({
  generatedApp: { type: Object, default: null },
  revealPhase: { type: Number, default: 0 },
  ensoState: { type: String, default: 'broken' }
})

defineEmits(['close', 'download-pdf', 'go-to-applications'])

const einleitungPreview = computed(() => {
  if (!props.generatedApp?.einleitung) return ''
  const text = props.generatedApp.einleitung
  const sentences = text.match(/[^.!?]*[.!?]+/g) || []
  return sentences.slice(0, 2).join(' ').trim()
})

const trapFocus = (e) => {
  const modal = e.currentTarget
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const firstFocusable = focusableElements[0]
  const lastFocusable = focusableElements[focusableElements.length - 1]

  if (e.shiftKey) {
    if (document.activeElement === firstFocusable) {
      e.preventDefault()
      lastFocusable.focus()
    }
  } else {
    if (document.activeElement === lastFocusable) {
      e.preventDefault()
      firstFocusable.focus()
    }
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
  max-width: 520px;
  background: var(--color-washi);
  border-radius: var(--radius-lg);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  padding: var(--space-xl);
  position: relative;
  overflow: hidden;
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
  padding: var(--space-lg) 0;
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
  margin-bottom: var(--space-xl);
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

.premium-reveal-einleitung {
  background: linear-gradient(135deg, var(--color-ai-subtle) 0%, rgba(61, 90, 108, 0.08) 100%);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  border-left: 3px solid var(--color-ai);
}

.premium-reveal-einleitung-label {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-ai);
  margin-bottom: var(--space-sm);
}

.premium-reveal-einleitung-text {
  font-size: 1rem;
  line-height: var(--leading-relaxed);
  color: var(--color-sumi);
  margin: 0;
  font-style: italic;
}

.premium-reveal-betreff {
  background: var(--color-washi-warm);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
}

.premium-reveal-betreff-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.premium-reveal-betreff-text {
  font-size: 0.9375rem;
  color: var(--color-sumi);
  margin: 0;
  font-weight: 500;
}

.premium-reveal-actions {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.5s var(--ease-zen), transform 0.5s var(--ease-zen);
}

.premium-reveal-actions--visible {
  opacity: 1;
  transform: translateY(0);
}

.premium-reveal-pdf-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.premium-reveal-pdf-card:hover {
  border-color: var(--color-ai);
  box-shadow: 0 4px 16px rgba(61, 90, 108, 0.12);
  transform: translateY(-2px);
}

.premium-reveal-pdf-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8f5f0 0%, #ebe7e0 100%);
  border-radius: var(--radius-sm);
  color: var(--color-ai);
}

.premium-reveal-pdf-info {
  flex: 1;
  min-width: 0;
}

.premium-reveal-pdf-name {
  display: block;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-sumi);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.premium-reveal-pdf-action {
  display: block;
  font-size: 0.8125rem;
  color: var(--color-ai);
  margin-top: 2px;
}

.premium-reveal-pdf-download {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  border-radius: 50%;
  color: white;
}

.premium-reveal-buttons {
  display: flex;
  gap: var(--space-md);
}

.premium-reveal-btn-primary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
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

.zen-btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  min-width: 240px;
}

@media (max-width: 768px) {
  .premium-reveal-modal {
    padding: var(--space-lg);
    margin: var(--space-md);
    max-width: calc(100% - var(--space-lg));
  }

  .premium-reveal-title {
    font-size: 1.5rem;
  }

  .premium-reveal-einleitung {
    padding: var(--space-md);
  }

  .premium-reveal-einleitung-text {
    font-size: 0.9375rem;
  }

  .premium-reveal-pdf-card {
    padding: var(--space-md);
  }

  .premium-reveal-pdf-icon {
    width: 40px;
    height: 40px;
  }

  .premium-reveal-pdf-icon svg {
    width: 24px;
    height: 24px;
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
}
</style>
