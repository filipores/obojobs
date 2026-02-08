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

        <!-- Phase 3: Email CTA and actions -->
        <div class="premium-reveal-actions" :class="{ 'premium-reveal-actions--visible': revealPhase >= 3 }">
          <!-- Email CTA -->
          <div v-if="recipientEmail" class="premium-reveal-email-cta">
            <div class="premium-reveal-email-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </div>
            <div class="premium-reveal-email-info">
              <span class="premium-reveal-email-label">Bewerbung jetzt versenden!</span>
              <span class="premium-reveal-email-recipient">An: {{ recipientEmail }}</span>
            </div>
            <button @click="$emit('send-email')" class="zen-btn zen-btn-ai premium-reveal-email-btn">
              Per E-Mail versenden
            </button>
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
import { computed, watch, onUnmounted } from 'vue'
import EnsoCircle from '../application/EnsoCircle.vue'

const props = defineProps({
  generatedApp: { type: Object, default: null },
  revealPhase: { type: Number, default: 0 },
  ensoState: { type: String, default: 'broken' }
})

defineEmits(['close', 'download-pdf', 'go-to-applications', 'send-email'])

const einleitungPreview = computed(() => {
  if (!props.generatedApp?.einleitung) return ''
  const text = props.generatedApp.einleitung
  const sentences = text.match(/[^.!?]*[.!?]+/g) || []
  return sentences.slice(0, 2).join(' ').trim()
})

const recipientEmail = computed(() => {
  const app = props.generatedApp
  if (!app) return ''
  if (app.email) return app.email
  try {
    const links = JSON.parse(app.links_json || '{}')
    return links.email_from_text || ''
  } catch { return '' }
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
  max-width: 520px;
  max-height: calc(100dvh - 2 * var(--space-lg));
  overflow-y: auto;
  background: var(--color-washi);
  border-radius: var(--radius-lg);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  padding: var(--space-xl);
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

/* Email CTA */
.premium-reveal-email-cta {
  background: linear-gradient(135deg, var(--color-ai-subtle), rgba(61, 90, 108, 0.12));
  border: 1px solid var(--color-ai);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.premium-reveal-email-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  border-radius: var(--radius-sm);
  color: white;
}

.premium-reveal-email-info {
  flex: 1;
  min-width: 0;
}

.premium-reveal-email-label {
  display: block;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-sumi);
  margin-bottom: 2px;
}

.premium-reveal-email-recipient {
  display: block;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.premium-reveal-email-btn {
  flex-shrink: 0;
  white-space: nowrap;
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

  .premium-reveal-email-cta {
    flex-direction: column;
    text-align: center;
  }

  .premium-reveal-email-info {
    text-align: center;
  }

  .premium-reveal-email-btn {
    width: 100%;
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
