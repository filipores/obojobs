<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="isVisible"
        class="crafting-overlay"
        role="dialog"
        aria-modal="true"
        :aria-label="ariaLabel"
        aria-live="polite"
      >
        <!-- Background with subtle gradient -->
        <div class="crafting-overlay__backdrop" />

        <!-- Main content container -->
        <div class="crafting-overlay__content">
          <!-- Central enso circle -->
          <div class="crafting-overlay__enso">
            <EnsoCircle
              :state="ensoState"
              size="xl"
              :duration="4000"
            />
          </div>

          <!-- Phase indicator -->
          <div class="crafting-overlay__phase">
            <Transition name="phase-text" mode="out-in">
              <h2 :key="currentPhase" class="crafting-overlay__title">
                {{ phases[currentPhase]?.title }}
              </h2>
            </Transition>
          </div>

          <!-- Phase-specific content -->
          <div class="crafting-overlay__stage">
            <!-- Phase 1: Document collection -->
            <Transition name="stage-content">
              <div v-if="currentPhase === 0" class="stage-documents">
                <div class="document-icons">
                  <div
                    v-for="(doc, i) in documents"
                    :key="doc.name"
                    class="document-icon"
                    :style="{ animationDelay: `${i * 200}ms` }"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path :d="doc.icon" />
                    </svg>
                    <span class="document-label">{{ doc.name }}</span>
                  </div>
                </div>
              </div>
            </Transition>

            <!-- Phase 2: Understanding requirements -->
            <Transition name="stage-content">
              <div v-if="currentPhase === 1" class="stage-keywords">
                <div class="keywords-cloud">
                  <span
                    v-for="(keyword, i) in keywords"
                    :key="keyword"
                    class="keyword"
                    :style="{ animationDelay: `${i * 300}ms` }"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
            </Transition>

            <!-- Phase 3: Writing cover letter -->
            <Transition name="stage-content">
              <div v-if="currentPhase === 2" class="stage-typewriter">
                <div class="typewriter-preview">
                  <TypewriterText
                    :text="previewText"
                    :speed="35"
                    :delay="500"
                    variant="brush"
                    :show-cursor="true"
                  />
                </div>
              </div>
            </Transition>

            <!-- Phase 4: Final touches -->
            <Transition name="stage-content">
              <div v-if="currentPhase === 3" class="stage-checklist">
                <ul class="checklist">
                  <li
                    v-for="(item, i) in checklist"
                    :key="item"
                    class="checklist-item"
                    :class="{ 'checklist-item--complete': completedChecks > i }"
                    :style="{ animationDelay: `${i * 400}ms` }"
                  >
                    <span class="checklist-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path v-if="completedChecks > i" d="M5 13l4 4L19 7" />
                        <circle v-else cx="12" cy="12" r="4" />
                      </svg>
                    </span>
                    <span class="checklist-text">{{ item }}</span>
                  </li>
                </ul>
              </div>
            </Transition>

            <!-- Phase 5: Reveal transition (empty - handled by overlay exit) -->
            <Transition name="stage-content">
              <div v-if="currentPhase === 4" class="stage-reveal">
                <div class="reveal-message">
                  <span class="reveal-text">Fertig</span>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Progress indicator -->
          <div class="crafting-overlay__progress">
            <InkProgress
              :progress="overallProgress"
              variant="brush"
              size="lg"
              :duration="1000"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import EnsoCircle from './EnsoCircle.vue'
import TypewriterText from './TypewriterText.vue'
import InkProgress from './InkProgress.vue'

const props = defineProps({
  isActive: {
    type: Boolean,
    default: false
  },
  companyName: {
    type: String,
    default: ''
  },
  jobTitle: {
    type: String,
    default: ''
  },
  jobDescription: {
    type: String,
    default: ''
  },
  contactPerson: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['complete', 'phase-change'])

const MAX_KEYWORDS = 8
const MIN_LENGTH = 5
const MAX_LENGTH = 45

// Collect all regex matches into a Set, trimmed and optionally length-filtered
function addMatches(found, text, pattern, { minLength = 0, maxLength = Infinity } = {}) {
  for (const match of text.matchAll(pattern)) {
    const value = match[0].trim()
    if (value.length >= minLength && value.length <= maxLength) {
      found.add(value)
    }
  }
}

// Extract keywords from job description text
function extractKeywords(text, jobTitle) {
  const found = new Set()

  // Tech skills
  addMatches(found, text, /\b(Python|JavaScript|TypeScript|React|Vue|Angular|Node\.?js|Docker|Kubernetes|AWS|Azure|GCP|SAP|SQL|NoSQL|Git|CI\/CD|REST|GraphQL|Java|C\+\+|C#|\.NET|PHP|Ruby|Go|Rust|Swift|Kotlin|Flutter|Terraform|Jenkins|Linux|Scrum|Agile|Jira|Figma|Confluence)\b/gi)

  // Degrees / qualifications
  addMatches(found, text, /(?:Studium der \w+|Bachelor[\w\s]*|Master[\w\s]*|Ausbildung[\w\s]*|Diplom[\w\s]*)/gi, { minLength: MIN_LENGTH, maxLength: MAX_LENGTH })

  // Experience patterns
  addMatches(found, text, /\d\+?\s*(?:Jahre?|years?)\s*(?:Berufserfahrung|Erfahrung|experience)?/gi)

  // Language skills
  addMatches(found, text, /(?:fließend|verhandlungssicher|sehr gute?|gute?)\s+(?:Deutsch|Englisch|Französisch|Spanisch|Italienisch)(?:kenntnisse)?/gi)

  // Bullet point items (first 3 lines starting with bullet characters)
  const bullets = text.split('\n')
    .map(l => l.replace(/^[\s•\-–]+/, '').trim())
    .filter(l => l.length >= 8 && l.length <= MAX_LENGTH)
  for (const b of bullets.slice(0, 3)) {
    if (found.size < MAX_KEYWORDS) found.add(b)
  }

  if (jobTitle && found.size < MAX_KEYWORDS) found.add(jobTitle)

  return [...found]
    .filter(k => k.length >= MIN_LENGTH && k.length <= MAX_LENGTH)
    .slice(0, MAX_KEYWORDS)
}

// Phase definitions with timing (personalized with company name when available)
const phases = computed(() => {
  const company = props.companyName
  return [
    { title: 'Sammle deine Dokumente', duration: 2500 },
    { title: company ? `Analysiere ${company}` : 'Verstehe die Anforderungen', duration: 4000 },
    { title: company ? `Schreibe dein Anschreiben an ${company}` : 'Schreibe dein Anschreiben', duration: 7000 },
    { title: 'Letzte Pinselstriche', duration: 3500 },
    { title: '', duration: 1000 }
  ]
})

// State
const isVisible = ref(false)
const currentPhase = ref(0)
const completedChecks = ref(0)
const phaseTimer = ref(null)
const checklistTimer = ref(null)

// Document icons for phase 1
const documents = [
  { name: 'Lebenslauf', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { name: 'Zeugnisse', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
  { name: 'Profil', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }
]

// Keywords for phase 2 — extract from real job description
const keywords = computed(() => {
  const text = props.jobDescription || ''
  if (text.length > 50) return extractKeywords(text, props.jobTitle)
  // Fallback
  const base = ['Erfahrung', 'Motivation', 'Qualifikation', 'Teamfähigkeit']
  return props.jobTitle ? [props.jobTitle, ...base.slice(0, 3)] : base
})

// Preview text for phase 3 — personalized with real data
const previewText = computed(() => {
  const company = props.companyName || 'Ihr Unternehmen'
  const position = props.jobTitle || 'die ausgeschriebene Position'
  const contact = props.contactPerson
  const greeting = contact ? `Sehr geehrte/r ${contact},` : 'Sehr geehrte Damen und Herren,'
  return `${greeting}\n\nmit großem Interesse habe ich Ihre Stellenausschreibung als ${position} bei ${company} gelesen...`
})

// Checklist items for phase 4 -- personalized with real data when available
const checklist = computed(() => {
  const { contactPerson, jobTitle, companyName } = props
  return [
    contactPerson ? `Persönliche Anrede: ${contactPerson}` : 'Persönliche Anrede',
    jobTitle ? `Relevante Erfahrungen für ${jobTitle}` : 'Relevante Erfahrungen',
    companyName ? `Motivation für ${companyName}` : 'Motivation für die Stelle',
    'Professioneller Abschluss'
  ]
})

// Computed
const ensoState = computed(() => {
  if (currentPhase.value === 4) return 'complete'
  if (currentPhase.value >= 2) return 'rotating'
  return 'breathing'
})

const overallProgress = computed(() => {
  const totalDuration = phases.value.reduce((sum, p) => sum + p.duration, 0)
  let elapsed = 0
  for (let i = 0; i < currentPhase.value; i++) {
    elapsed += phases.value[i].duration
  }
  return Math.min(100, (elapsed / totalDuration) * 100)
})

const ariaLabel = computed(() => {
  return `Bewerbung wird erstellt: ${phases.value[currentPhase.value].title}`
})

// Methods
const startPhaseSequence = () => {
  if (currentPhase.value >= phases.value.length - 1) {
    completeOverlay()
    return
  }

  emit('phase-change', currentPhase.value)

  // Special handling for phase 3 (checklist)
  if (currentPhase.value === 3) {
    startChecklistAnimation()
  }

  phaseTimer.value = setTimeout(() => {
    currentPhase.value++
    startPhaseSequence()
  }, phases.value[currentPhase.value].duration)
}

const startChecklistAnimation = () => {
  completedChecks.value = 0
  const interval = phases.value[3].duration / (checklist.value.length + 1)

  const animateCheck = () => {
    if (completedChecks.value < checklist.value.length) {
      completedChecks.value++
      checklistTimer.value = setTimeout(animateCheck, interval)
    }
  }

  checklistTimer.value = setTimeout(animateCheck, interval)
}

const completeOverlay = () => {
  setTimeout(() => {
    isVisible.value = false
    emit('complete')
  }, 500)
}

const reset = () => {
  currentPhase.value = 0
  completedChecks.value = 0
  clearTimeout(phaseTimer.value)
  clearTimeout(checklistTimer.value)
}

// Watchers
watch(() => props.isActive, (active) => {
  if (active) {
    reset()
    isVisible.value = true
    // Small delay for overlay entrance animation
    setTimeout(startPhaseSequence, 500)
  } else {
    isVisible.value = false
    reset()
  }
})

// Lifecycle
onMounted(() => {
  if (props.isActive) {
    isVisible.value = true
    setTimeout(startPhaseSequence, 500)
  }
})

onUnmounted(() => {
  clearTimeout(phaseTimer.value)
  clearTimeout(checklistTimer.value)
})

// Expose methods for parent control
defineExpose({ reset })
</script>

<style scoped>
.crafting-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.crafting-overlay__backdrop {
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

.crafting-overlay__content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-ma);
  padding: var(--space-ma-xl);
  max-width: 600px;
  width: 100%;
  text-align: center;
}

/* Enso Circle */
.crafting-overlay__enso {
  margin-bottom: var(--space-lg);
}

/* Phase Title */
.crafting-overlay__phase {
  min-height: 3rem;
}

.crafting-overlay__title {
  font-family: var(--font-display);
  font-size: clamp(1.5rem, 4vw, 2rem);
  font-weight: 400;
  color: var(--color-sumi);
  letter-spacing: var(--tracking-tight);
  margin: 0;
}

/* Stage Container */
.crafting-overlay__stage {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

/* Phase 1: Documents */
.stage-documents {
  width: 100%;
}

.document-icons {
  display: flex;
  justify-content: center;
  gap: var(--space-xl);
}

.document-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  opacity: 0;
  animation: documentFloat 0.8s var(--ease-zen) forwards;
}

.document-icon svg {
  width: 48px;
  height: 48px;
  color: var(--color-ai);
}

.document-label {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  letter-spacing: var(--tracking-wide);
}

@keyframes documentFloat {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Phase 2: Keywords */
.stage-keywords {
  width: 100%;
}

.keywords-cloud {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-md);
}

.keyword {
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-full);
  font-size: 0.9375rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wide);
  opacity: 0;
  animation: keywordFade 0.6s var(--ease-zen) forwards;
}

@keyframes keywordFade {
  0% {
    opacity: 0;
    transform: scale(0.8);
    filter: blur(4px);
  }
  100% {
    opacity: 1;
    transform: scale(1);
    filter: blur(0);
  }
}

/* Phase 3: Typewriter */
.stage-typewriter {
  width: 100%;
}

.typewriter-preview {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  text-align: left;
  box-shadow: var(--shadow-paper);
  max-width: 480px;
  margin: 0 auto;
  min-height: 120px;
}

.typewriter-preview :deep(.typewriter) {
  font-size: 0.9375rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
  white-space: pre-wrap;
}

/* Phase 4: Checklist */
.stage-checklist {
  width: 100%;
}

.checklist {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  max-width: 320px;
  margin: 0 auto;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  opacity: 0;
  animation: checklistSlide 0.5s var(--ease-zen) forwards;
}

.checklist-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.checklist-icon svg {
  width: 100%;
  height: 100%;
  color: var(--color-stone);
  transition: color var(--transition-base);
}

.checklist-item--complete .checklist-icon svg {
  color: var(--color-success);
}

.checklist-text {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
  transition: color var(--transition-base);
}

.checklist-item--complete .checklist-text {
  color: var(--color-text-primary);
}

@keyframes checklistSlide {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Phase 5: Reveal */
.stage-reveal {
  width: 100%;
}

.reveal-message {
  display: flex;
  align-items: center;
  justify-content: center;
}

.reveal-text {
  font-family: var(--font-display);
  font-size: clamp(2rem, 6vw, 3rem);
  font-weight: 400;
  color: var(--color-ai);
  letter-spacing: var(--tracking-tight);
  animation: revealPulse 1s var(--ease-zen);
}

@keyframes revealPulse {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Progress */
.crafting-overlay__progress {
  margin-top: var(--space-ma);
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

.stage-content-enter-active {
  animation: stageEnter 0.5s var(--ease-zen);
}

.stage-content-leave-active {
  animation: stageLeave 0.3s var(--ease-zen);
}

@keyframes stageEnter {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes stageLeave {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .document-icon,
  .keyword,
  .checklist-item,
  .reveal-text {
    animation: none;
    opacity: 1;
    transform: none;
  }

  .overlay-enter-active,
  .overlay-leave-active,
  .phase-text-enter-active,
  .phase-text-leave-active,
  .stage-content-enter-active,
  .stage-content-leave-active {
    animation: none;
    transition: opacity 0.2s;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .crafting-overlay__content {
    padding: var(--space-lg);
  }

  .document-icons {
    gap: var(--space-lg);
  }

  .document-icon svg {
    width: 36px;
    height: 36px;
  }

  .typewriter-preview {
    padding: var(--space-md);
  }
}
</style>
