<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import SeeleFrage from './SeeleFrage.vue'
import { seeleStore } from '../../stores/seele'

const props = defineProps({
  overlay: { type: Boolean, default: true },
  sessionTyp: { type: String, default: 'onboarding' },
  kontext: { type: Object, default: null }
})

const emit = defineEmits(['close', 'complete'])

// Screens: intro, fragen, complete
const screen = ref('intro')
const error = ref(null)
const frageIndex = ref(0)

const fragenGesamt = computed(() => seeleStore.aktuelleFragen.length)
const aktuelleFrage = computed(() => seeleStore.aktuelleFragen[frageIndex.value] || null)
const fortschritt = computed(() => ({
  aktuell: frageIndex.value + 1,
  gesamt: fragenGesamt.value
}))

async function starten() {
  error.value = null
  try {
    await seeleStore.starteSession(props.sessionTyp, props.kontext)
    frageIndex.value = 0
    screen.value = 'fragen'
  } catch (e) {
    error.value = 'Sitzung konnte nicht gestartet werden. Bitte versuche es erneut.'
    console.error('SeeleFlow start error:', e)
  }
}

async function onAntwort({ frage_key, antwort }) {
  const sessionId = seeleStore.aktiveSession?.id
  if (!sessionId) return

  try {
    const result = await seeleStore.beantworte(sessionId, frage_key, antwort)
    advanceOrComplete(result)
  } catch (e) {
    console.error('SeeleFlow answer error:', e)
  }
}

async function onUeberspringen(frageKey) {
  const sessionId = seeleStore.aktiveSession?.id
  if (!sessionId) return

  try {
    const result = await seeleStore.ueberspringen(sessionId, frageKey)
    advanceOrComplete(result)
  } catch (e) {
    console.error('SeeleFlow skip error:', e)
  }
}

function advanceOrComplete(result) {
  if (!seeleStore.aktuelleFragen.length || result?.fertig) {
    screen.value = 'complete'
  } else {
    frageIndex.value = 0
  }
}

function fertig() {
  emit('complete')
  emit('close')
}

function close() {
  emit('close')
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  if (props.overlay) {
    document.addEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport v-if="overlay" to="body">
    <div class="seele-flow-overlay" @click.self="close">
      <div class="seele-flow-card" role="dialog" aria-modal="true" aria-label="Seele Persoenlichkeitsprofil">
        <!-- Close button -->
        <button class="flow-close" type="button" @click="close" aria-label="Schliessen">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <!-- Intro screen -->
        <div v-if="screen === 'intro'" class="flow-screen flow-intro">
          <div class="intro-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <h2 class="intro-title">Lass uns dich kennenlernen</h2>
          <p class="intro-desc">
            Ein paar kurze Fragen, damit wir deine Bewerbungen noch besser personalisieren koennen.
          </p>
          <p class="intro-time">Weniger als 2 Minuten</p>
          <div v-if="error" class="flow-error">{{ error }}</div>
          <button
            class="zen-btn zen-btn-ai"
            :disabled="seeleStore.loading"
            @click="starten"
          >
            {{ seeleStore.loading ? 'Wird geladen...' : "Los geht's" }}
          </button>
        </div>

        <!-- Questions screen -->
        <div v-else-if="screen === 'fragen'" class="flow-screen flow-fragen">
          <SeeleFrage
            v-if="aktuelleFrage"
            :key="aktuelleFrage.key"
            :frage="aktuelleFrage"
            :fortschritt="fortschritt"
            @antwort="onAntwort"
            @ueberspringen="onUeberspringen"
          />
        </div>

        <!-- Completion screen -->
        <div v-else-if="screen === 'complete'" class="flow-screen flow-complete">
          <!-- Completion ring -->
          <div class="complete-ring">
            <svg viewBox="0 0 100 100" class="ring-svg">
              <circle
                cx="50" cy="50" r="42"
                fill="none"
                stroke="var(--color-sand)"
                stroke-width="6"
              />
              <circle
                cx="50" cy="50" r="42"
                fill="none"
                stroke="var(--color-ai)"
                stroke-width="6"
                stroke-linecap="round"
                :stroke-dasharray="`${seeleStore.vollstaendigkeit * 2.64} 264`"
                transform="rotate(-90 50 50)"
                class="ring-progress"
              />
            </svg>
            <span class="ring-value">{{ seeleStore.vollstaendigkeit }}%</span>
          </div>
          <h2 class="complete-title">Danke!</h2>
          <p class="complete-desc">
            Dein Profil ist jetzt zu {{ seeleStore.vollstaendigkeit }}% ausgefuellt.
          </p>
          <button class="zen-btn zen-btn-ai" @click="fertig">
            Fertig
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Non-overlay mode (inline) -->
  <div v-if="!overlay" class="seele-flow-inline">
    <div v-if="screen === 'intro'" class="flow-screen flow-intro">
      <h2 class="intro-title">Lass uns dich kennenlernen</h2>
      <p class="intro-desc">
        Ein paar kurze Fragen, damit wir deine Bewerbungen noch besser personalisieren koennen.
      </p>
      <div v-if="error" class="flow-error">{{ error }}</div>
      <button
        class="zen-btn zen-btn-ai"
        :disabled="seeleStore.loading"
        @click="starten"
      >
        {{ seeleStore.loading ? 'Wird geladen...' : "Los geht's" }}
      </button>
    </div>

    <div v-else-if="screen === 'fragen'" class="flow-screen flow-fragen">
      <SeeleFrage
        v-if="aktuelleFrage"
        :key="aktuelleFrage.key"
        :frage="aktuelleFrage"
        :fortschritt="fortschritt"
        @antwort="onAntwort"
        @ueberspringen="onUeberspringen"
      />
    </div>

    <div v-else-if="screen === 'complete'" class="flow-screen flow-complete">
      <h2 class="complete-title">Danke!</h2>
      <p class="complete-desc">Profil zu {{ seeleStore.vollstaendigkeit }}% ausgefuellt.</p>
      <button class="zen-btn zen-btn-ai" @click="fertig">Fertig</button>
    </div>
  </div>
</template>

<style scoped>
/* Overlay */
.seele-flow-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal, 1000);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  padding: var(--space-md);
  animation: overlayFadeIn 0.3s var(--ease-zen, ease);
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.seele-flow-card {
  position: relative;
  background: var(--color-bg-elevated, var(--color-washi));
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lifted);
  max-width: 540px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  padding: var(--space-xl);
  animation: cardSlideUp 0.35s var(--ease-zen, ease);
}

@keyframes cardSlideUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.flow-close {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.flow-close:hover {
  background: var(--color-washi-aged, #f0ede8);
  color: var(--color-sumi);
}

/* Screens */
.flow-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  min-height: 300px;
  justify-content: center;
}

/* Intro */
.intro-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: 50%;
  color: var(--color-ai);
  margin-bottom: var(--space-lg);
}

.intro-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--color-sumi);
  margin-bottom: var(--space-md);
}

.intro-desc {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  max-width: 360px;
  line-height: var(--leading-relaxed, 1.6);
  margin-bottom: var(--space-sm);
}

.intro-time {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xl);
}

.flow-error {
  color: var(--color-error, #c53030);
  font-size: 0.875rem;
  margin-bottom: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-error-light, #fee);
  border-radius: var(--radius-sm);
}

/* Complete */
.complete-ring {
  position: relative;
  width: 120px;
  height: 120px;
  margin-bottom: var(--space-lg);
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-progress {
  transition: stroke-dasharray 1s var(--ease-zen, ease);
}

.ring-value {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-ai);
}

.complete-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.complete-desc {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xl);
}

/* Inline mode */
.seele-flow-inline {
  padding: var(--space-lg);
}

@media (max-width: 480px) {
  .seele-flow-card {
    padding: var(--space-lg);
    max-height: 95vh;
  }

  .intro-title,
  .complete-title {
    font-size: 1.25rem;
  }
}
</style>
