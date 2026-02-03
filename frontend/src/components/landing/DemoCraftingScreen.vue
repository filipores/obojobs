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
            <div class="brand-enso">
              <EnsoCircle :state="ensoState" size="xl" :duration="4000" />
            </div>
            <span class="brand-text">obo</span>
          </div>

          <!-- Phase Title -->
          <div class="phase-title-container">
            <Transition name="phase-text" mode="out-in">
              <h2 :key="currentPhase" class="phase-title">
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

          <!-- Einleitung Typewriter -->
          <Transition name="einleitung">
            <div v-if="currentPhase >= 4" class="einleitung-card" :class="{ 'visible': currentPhase >= 4 }">
              <TypewriterText
                v-if="currentPhase >= 4"
                :text="data.einleitung"
                :speed="40"
                variant="default"
                :showCursor="true"
              />
            </div>
          </Transition>

          <!-- PDF Preview -->
          <Transition name="pdf-preview">
            <div v-if="currentPhase >= 5 && pdfBlob" class="pdf-preview-container" :class="{ 'visible': currentPhase >= 5 }">
              <DemoPdfPreview :pdfBlob="pdfBlob" />
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
import TypewriterText from '@/components/application/TypewriterText.vue'
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

// Phase definitions with timing (in ms)
// Phase 0: 0-2s, Phase 1: 2-5s, Phase 2: 5-9s, Phase 3: 9-13s, Phase 4: 13-17s, Phase 5: 17-21s, Phase 6: 21-24s
const phases = [
  { title: 'Bereite vor...', duration: 2000 },
  { title: 'Empfanger gefunden', duration: 3000 },
  { title: 'Unternehmen analysiert', duration: 4000 },
  { title: 'Position verstanden', duration: 4000 },
  { title: 'Schreibe Einleitung...', duration: 4000 },
  { title: 'Erstelle PDF...', duration: 4000 },
  { title: 'Fertig!', duration: 3000 }
]

// State
const currentPhase = ref(0)
const phaseStartTime = ref(0)
const elapsedTime = ref(0)
const phaseTimer = ref(null)
const progressTimer = ref(null)

// Computed
const ensoState = computed(() => {
  if (currentPhase.value <= 4) return 'breathing'
  if (currentPhase.value === 5) return 'rotating'
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

const reset = () => {
  currentPhase.value = 0
  elapsedTime.value = 0
  phaseStartTime.value = 0
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
  if (props.isActive) {
    setTimeout(startPhaseSequence, 500)
  }
})

onUnmounted(() => {
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

/* Einleitung Card */
.einleitung-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  text-align: left;
  box-shadow: var(--shadow-paper);
  max-width: 480px;
  width: 100%;
  min-height: 100px;
}

.einleitung-card :deep(.typewriter) {
  font-size: 0.9375rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
}

/* PDF Preview */
.pdf-preview-container {
  width: 100%;
  display: flex;
  justify-content: center;
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

/* Data card transitions */
.data-card-enter-active {
  animation: dataCardFadeUp 0.6s var(--ease-zen);
}

.data-card-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes dataCardFadeUp {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
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

/* Firma card scale + brush transition */
.data-card-firma-enter-active {
  animation: firmaEnter 0.7s var(--ease-zen);
}

.data-card-firma-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes firmaEnter {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  60% {
    transform: scale(1.02);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Position slide from right */
.data-card-slide-enter-active {
  animation: slideFromRight 0.6s var(--ease-zen);
}

.data-card-slide-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes slideFromRight {
  0% {
    opacity: 0;
    transform: translateX(30px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Einleitung transition */
.einleitung-enter-active {
  animation: einleitungEnter 0.6s var(--ease-zen);
}

.einleitung-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes einleitungEnter {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* PDF preview slide up + shadow lift */
.pdf-preview-enter-active {
  animation: pdfSlideUp 0.8s var(--ease-zen);
}

.pdf-preview-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes pdfSlideUp {
  0% {
    opacity: 0;
    transform: translateY(40px);
    filter: drop-shadow(0 0 0 transparent);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
    filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.1));
  }
}

/* CTA fade in + pulse */
.cta-enter-active {
  animation: ctaEnter 0.6s var(--ease-zen);
}

.cta-leave-active {
  animation: dataCardFadeOut 0.3s var(--ease-zen);
}

@keyframes ctaEnter {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  70% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .crafting-brand,
  .cta-pulse {
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
  .einleitung-enter-active,
  .einleitung-leave-active,
  .pdf-preview-enter-active,
  .pdf-preview-leave-active,
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

  .einleitung-card {
    padding: var(--space-md);
  }
}
</style>
