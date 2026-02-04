<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="isActive"
        class="demo-crafting-overlay"
        role="dialog"
        aria-modal="true"
        :aria-label="ariaLabel"
        aria-live="polite"
      >
        <!-- Background with subtle gradient -->
        <div class="demo-crafting-overlay__backdrop" />

        <!-- Main content container -->
        <div class="demo-crafting-overlay__content">
          <!-- Brand -->
          <div class="crafting-brand" :class="{ 'visible': currentPhase >= 0 }">
            <div class="brand-enso" :class="{ 'enso-complete': currentPhase >= 6 }">
              <EnsoCircle :state="ensoState" size="xl" :duration="4000" />
            </div>
            <span class="brand-text">obo</span>
          </div>

          <!-- Phase Title -->
          <div class="phase-title-container">
            <Transition name="phase-text" mode="out-in">
              <h2
                :key="currentPhase"
                class="phase-title"
                :class="{ 'phase-title-complete': currentPhase === 6 }"
              >
                {{ phases[currentPhase].title }}
              </h2>
            </Transition>
          </div>

          <!-- Progressive Data Cards -->
          <div class="data-cards">
            <Transition name="data-card">
              <div v-if="currentPhase >= 1" class="data-card" :class="{ 'visible': currentPhase >= 1 }">
                <span class="data-label">An</span>
                <span class="data-value">{{ data.ansprechpartner }}</span>
              </div>
            </Transition>
            <Transition name="data-card-firma">
              <div v-if="currentPhase >= 2" class="data-card firma-card" :class="{ 'visible': currentPhase >= 2 }">
                <span class="data-label">Fur</span>
                <span class="data-value">{{ data.firma }}</span>
                <div class="brush-stroke-effect"></div>
              </div>
            </Transition>
            <Transition name="data-card-slide">
              <div v-if="currentPhase >= 3" class="data-card" :class="{ 'visible': currentPhase >= 3 }">
                <span class="data-label">Position</span>
                <span class="data-value">{{ data.position }}</span>
              </div>
            </Transition>
          </div>

          <!-- PDF Card with Hover Preview (replaces einleitung typewriter and pdf preview) -->
          <Transition name="pdf-card">
            <div v-if="currentPhase >= 4" class="pdf-card-container">
              <div
                class="data-card pdf-card"
                :class="{ 'visible': currentPhase >= 4 }"
                @mouseenter="handlePdfCardHover(true)"
                @mouseleave="handlePdfCardHover(false)"
                @click="togglePdfPreview"
              >
                <span class="data-label">Anschreiben</span>
                <div class="pdf-card-content">
                  <svg class="pdf-card-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                  <span class="data-value">Dein personalisiertes Anschreiben</span>
                </div>
                <span v-if="pdfBlob" class="pdf-card-hint">{{ isMobile ? 'Tippen fur Vorschau' : 'Hover fur Vorschau' }}</span>
                <span v-else class="pdf-card-hint pdf-card-loading">Wird erstellt...</span>
              </div>

              <Transition name="pdf-preview-float">
                <div v-if="showPdfPreview && pdfBlob" class="pdf-preview-floating">
                  <DemoPdfPreview :pdfBlob="pdfBlob" :floating="true" />
                </div>
              </Transition>
            </div>
          </Transition>

          <!-- CTA -->
          <Transition name="cta">
            <button
              v-if="currentPhase >= 6"
              @click="handleRegister"
              class="zen-btn zen-btn-ai cta-pulse"
              :class="{ 'visible': currentPhase >= 6 }"
            >
              Kostenlos registrieren
            </button>
          </Transition>

          <!-- Progress -->
          <div class="demo-crafting-overlay__progress">
            <InkProgress :progress="overallProgress" variant="brush" size="lg" :duration="1000" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import EnsoCircle from '@/components/application/EnsoCircle.vue'
import InkProgress from '@/components/application/InkProgress.vue'
import DemoPdfPreview from './DemoPdfPreview.vue'

const props = defineProps({
  isActive: {
    type: Boolean,
    default: false
  },
  data: {
    type: Object,
    default: () => ({
      ansprechpartner: '',
      firma: '',
      position: '',
      einleitung: ''
    })
  },
  pdfBlob: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['register', 'complete'])

// Phase definitions with timing (in ms) - staggered for momentum
// Phase 0: 2000ms (preparation)
// Phase 1: 2500ms (slower start)
// Phase 2: 2000ms (faster)
// Phase 3: 1500ms (even faster)
// Phase 4: 4000ms (PDF card with loading)
// Phase 5: 2000ms (quick transition)
// Phase 6: 3000ms (celebration)
const phases = [
  { title: 'Bereite vor...', duration: 2000 },
  { title: 'Empfanger gefunden', duration: 2500 },
  { title: 'Unternehmen analysiert', duration: 2000 },
  { title: 'Position verstanden', duration: 1500 },
  { title: 'Erstelle Anschreiben...', duration: 4000 },
  { title: 'Fast fertig...', duration: 2000 },
  { title: 'Fertig!', duration: 3000 }
]

// State
const currentPhase = ref(0)
const phaseStartTime = ref(0)
const elapsedTime = ref(0)
const phaseTimer = ref(null)
const progressTimer = ref(null)
const showPdfPreview = ref(false)
const isMobile = ref(false)

// Computed
const ensoState = computed(() => {
  if (currentPhase.value <= 3) return 'breathing'
  if (currentPhase.value <= 5) return 'rotating'
  return 'complete'
})

const totalDuration = computed(() => phases.reduce((sum, p) => sum + p.duration, 0))

const overallProgress = computed(() => {
  let elapsed = 0
  for (let i = 0; i < currentPhase.value; i++) {
    elapsed += phases[i].duration
  }
  // Add partial progress within current phase
  const phaseProgress = Math.min(elapsedTime.value, phases[currentPhase.value].duration)
  elapsed += phaseProgress
  return Math.min(100, (elapsed / totalDuration.value) * 100)
})

const ariaLabel = computed(() => {
  return `Demo wird erstellt: ${phases[currentPhase.value].title}`
})

// Methods
const startPhaseSequence = () => {
  if (currentPhase.value >= phases.length - 1) {
    // Complete sequence after final phase duration
    phaseTimer.value = setTimeout(() => {
      emit('complete')
    }, phases[currentPhase.value].duration)
    return
  }

  phaseStartTime.value = Date.now()
  elapsedTime.value = 0

  // Update progress more frequently for smooth animation
  progressTimer.value = setInterval(() => {
    elapsedTime.value = Date.now() - phaseStartTime.value
  }, 50)

  phaseTimer.value = setTimeout(() => {
    clearInterval(progressTimer.value)
    currentPhase.value++
    startPhaseSequence()
  }, phases[currentPhase.value].duration)
}

const handleRegister = () => {
  emit('register')
}

const handlePdfCardHover = (isHovering) => {
  if (!isMobile.value) {
    showPdfPreview.value = isHovering
  }
}

const togglePdfPreview = () => {
  if (isMobile.value) {
    showPdfPreview.value = !showPdfPreview.value
  }
}

const checkMobile = () => {
  isMobile.value = window.matchMedia('(max-width: 768px)').matches ||
                   'ontouchstart' in window
}

const reset = () => {
  currentPhase.value = 0
  elapsedTime.value = 0
  phaseStartTime.value = 0
  showPdfPreview.value = false
  clearTimeout(phaseTimer.value)
  clearInterval(progressTimer.value)
}

// Watchers
watch(() => props.isActive, (active) => {
  if (active) {
    reset()
    // Small delay for overlay entrance animation
    setTimeout(startPhaseSequence, 500)
  } else {
    reset()
  }
})

// Lifecycle
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  if (props.isActive) {
    setTimeout(startPhaseSequence, 500)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  clearTimeout(phaseTimer.value)
  clearInterval(progressTimer.value)
})

// Expose methods for parent control
defineExpose({ reset })
</script>

<style scoped>
.demo-crafting-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  /* Safe area support for notched phones */
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
}

.demo-crafting-overlay__backdrop {
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

.demo-crafting-overlay__content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  padding: var(--space-xl);
  max-width: 600px;
  width: 100%;
  text-align: center;
  /* Responsive fixes */
  max-height: 100vh;
  max-height: 100dvh;
  overflow-y: auto;
}

/* Brand */
.crafting-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  opacity: 0;
  animation: brandFadeIn 0.8s var(--ease-zen) forwards;
}

.crafting-brand.visible {
  opacity: 1;
}

.brand-enso {
  margin-bottom: var(--space-sm);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              filter 0.4s var(--ease-zen);
}

/* Enso completion emphasis - scale pulse and glow */
.brand-enso.enso-complete {
  animation: ensoCompletePulse 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 0 12px var(--color-ai-subtle));
}

@keyframes ensoCompletePulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.brand-text {
  font-family: var(--font-display);
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 400;
  color: var(--color-sumi);
  letter-spacing: var(--tracking-tight);
}

@keyframes brandFadeIn {
  0% {
    opacity: 0;
    transform: translateY(-10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Phase Title */
.phase-title-container {
  min-height: 3rem;
}

.phase-title {
  font-family: var(--font-display);
  font-size: clamp(1.25rem, 3vw, 1.5rem);
  font-weight: 400;
  color: var(--color-text-secondary);
  letter-spacing: var(--tracking-tight);
  margin: 0;
}

/* Celebration animation for "Fertig!" */
.phase-title-complete {
  animation: celebrateTitle 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes celebrateTitle {
  0% {
    transform: scale(1);
    color: var(--color-text-secondary);
  }
  40% {
    transform: scale(1.15);
    color: var(--color-ai);
  }
  100% {
    transform: scale(1);
    color: var(--color-koke);
  }
}

/* Data Cards */
.data-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  width: 100%;
  max-width: 400px;
}

.data-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  text-align: left;
  box-shadow: var(--shadow-paper);
  position: relative;
  overflow: hidden;
}

.data-label {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
}

.data-value {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* Firma card special effect */
.firma-card {
  position: relative;
}

.firma-card .data-value {
  color: var(--color-ai);
  font-weight: 600;
}

.brush-stroke-effect {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--color-ai) 20%,
    var(--color-ai) 80%,
    transparent 100%
  );
  opacity: 0;
  animation: brushStroke 0.8s var(--ease-zen) 0.3s forwards;
}

@keyframes brushStroke {
  0% {
    opacity: 0;
    transform: scaleX(0);
  }
  100% {
    opacity: 1;
    transform: scaleX(1);
  }
}

/* PDF Card Container */
.pdf-card-container {
  position: relative;
  width: 100%;
  max-width: 400px;
}

/* PDF Card */
.pdf-card {
  cursor: pointer;
  transition: all 0.2s var(--ease-zen);
  border: 1px solid var(--color-ai-subtle);
}

.pdf-card:hover {
  border-color: var(--color-ai);
  box-shadow: var(--shadow-lifted);
}

.pdf-card-content {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.pdf-card-icon {
  color: var(--color-ai);
  flex-shrink: 0;
}

.pdf-card .data-value {
  color: var(--color-ai);
  font-weight: 500;
}

.pdf-card-hint {
  font-size: 0.75rem;
  color: var(--color-text-ghost);
  margin-top: var(--space-xs);
}

.pdf-card-loading {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

/* Floating PDF Preview */
.pdf-preview-floating {
  position: absolute;
  bottom: calc(100% + var(--space-md));
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  pointer-events: none;
}

/* CTA Button */
.cta-pulse {
  animation: ctaPulse 2s var(--ease-zen) infinite;
}

@keyframes ctaPulse {
  0%, 100% {
    box-shadow: var(--shadow-button), 0 0 0 0 var(--color-ai-subtle);
  }
  50% {
    box-shadow: var(--shadow-button), 0 0 0 12px transparent;
  }
}

/* Progress */
.demo-crafting-overlay__progress {
  margin-top: var(--space-lg);
}

/* Transitions */
.overlay-enter-active {
  animation: overlayEnter 0.6s var(--ease-zen);
}

.overlay-leave-active {
  animation: overlayLeave 0.5s var(--ease-zen);
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
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(1.02);
  }
}

.phase-text-enter-active,
.phase-text-leave-active {
  transition: all 0.4s var(--ease-zen);
}

.phase-text-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.phase-text-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Data card transitions with bounce easing */
.data-card-enter-active {
  animation: dataCardFadeUpBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.data-card-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes dataCardFadeUpBounce {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  70% {
    transform: translateY(-4px) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes dataCardFadeOut {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

/* Firma card scale + brush transition - faster */
.data-card-firma-enter-active {
  animation: firmaEnterBounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.data-card-firma-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes firmaEnterBounce {
  0% {
    opacity: 0;
    transform: scale(0.85);
  }
  70% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Position slide from right - fastest */
.data-card-slide-enter-active {
  animation: slideFromRightBounce 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.data-card-slide-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes slideFromRightBounce {
  0% {
    opacity: 0;
    transform: translateX(30px) scale(0.95);
  }
  70% {
    transform: translateX(-4px) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* PDF Card transition */
.pdf-card-enter-active {
  animation: pdfCardEnter 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pdf-card-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes pdfCardEnter {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  70% {
    transform: translateY(-4px) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Floating PDF preview transition */
.pdf-preview-float-enter-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pdf-preview-float-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.pdf-preview-float-enter-from {
  opacity: 0;
  transform: translateX(-50%) scale(0.9) translateY(8px);
}

.pdf-preview-float-leave-to {
  opacity: 0;
  transform: translateX(-50%) scale(0.95) translateY(4px);
}

/* CTA fade in + dramatic bounce */
.cta-enter-active {
  animation: ctaEnterDramatic 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.cta-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes ctaEnterDramatic {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(10px);
  }
  60% {
    transform: scale(1.1) translateY(-4px);
  }
  80% {
    transform: scale(0.98) translateY(2px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .crafting-brand,
  .cta-pulse,
  .phase-title-complete,
  .brand-enso.enso-complete {
    animation: none;
    opacity: 1;
  }

  .brush-stroke-effect {
    animation: none;
    opacity: 1;
    transform: scaleX(1);
  }

  .overlay-enter-active,
  .overlay-leave-active,
  .phase-text-enter-active,
  .phase-text-leave-active,
  .data-card-enter-active,
  .data-card-leave-active,
  .data-card-firma-enter-active,
  .data-card-firma-leave-active,
  .data-card-slide-enter-active,
  .data-card-slide-leave-active,
  .pdf-card-enter-active,
  .pdf-card-leave-active,
  .pdf-preview-float-enter-active,
  .pdf-preview-float-leave-active,
  .cta-enter-active,
  .cta-leave-active {
    animation: none;
    transition: opacity 0.2s;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .demo-crafting-overlay__content {
    padding: var(--space-lg);
    gap: var(--space-md);
  }

  .data-cards {
    max-width: 100%;
  }

  /* Position floating preview better on mobile */
  .pdf-preview-floating {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    bottom: auto;
    pointer-events: auto;
    z-index: 100;
  }

  .pdf-preview-float-enter-from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9);
  }

  .pdf-preview-float-leave-to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.95);
  }
}

/* Very small screens (320-375px) */
@media (max-width: 375px) {
  .demo-crafting-overlay__content {
    padding: var(--space-md);
    gap: var(--space-sm);
    justify-content: flex-start;
    padding-top: var(--space-lg);
  }

  .crafting-brand {
    gap: var(--space-sm);
  }

  .brand-enso {
    margin-bottom: 0;
    transform: scale(0.85);
  }

  .brand-text {
    font-size: 1.5rem;
  }

  .phase-title-container {
    min-height: 2.5rem;
  }

  .phase-title {
    font-size: 1rem;
  }

  .data-cards {
    gap: var(--space-sm);
  }

  .data-card {
    padding: var(--space-sm);
  }

  .data-label {
    font-size: 0.6875rem;
  }

  .data-value {
    font-size: 0.875rem;
  }

  .pdf-card-container {
    max-width: 100%;
  }

  .pdf-card-content {
    gap: var(--space-xs);
  }

  .pdf-card-icon {
    width: 20px;
    height: 20px;
  }

  .demo-crafting-overlay__progress {
    margin-top: var(--space-md);
    position: sticky;
    bottom: var(--space-sm);
    background: var(--color-washi);
    padding: var(--space-sm);
    border-radius: var(--radius-md);
    width: 100%;
  }

  .zen-btn {
    padding: var(--space-sm) var(--space-md);
    font-size: 0.875rem;
  }
}

/* Extra small screens (< 320px) */
@media (max-width: 320px) {
  .demo-crafting-overlay__content {
    padding: var(--space-sm);
    gap: var(--space-xs);
  }

  .brand-enso {
    transform: scale(0.7);
  }

  .brand-text {
    font-size: 1.25rem;
  }

  .data-card {
    padding: var(--space-xs);
  }

  .pdf-card-hint {
    font-size: 0.6875rem;
  }
}
</style>
