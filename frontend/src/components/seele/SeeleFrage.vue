<script setup>
import { ref, computed } from 'vue'
import SeeleChip from './SeeleChip.vue'

const props = defineProps({
  frage: { type: Object, required: true },
  fortschritt: { type: Object, default: () => ({ aktuell: 0, gesamt: 0 }) }
})

const emit = defineEmits(['antwort', 'ueberspringen'])

const selectedValues = ref([])
const freitextValue = ref('')
const sliderValue = ref(props.frage.min_wert || 0)

const isMulti = computed(() => props.frage.mehrfach === true)

const maxReached = computed(() => {
  if (!isMulti.value || !props.frage.max_auswahl) return false
  return selectedValues.value.length >= props.frage.max_auswahl
})

const canSubmit = computed(() => {
  const typ = props.frage.typ
  if (typ === 'slider') return true
  if (typ === 'freitext') return freitextValue.value.trim().length > 0
  if (typ === 'chips' || typ === 'chips_freitext') {
    return selectedValues.value.length > 0 || (typ === 'chips_freitext' && freitextValue.value.trim().length > 0)
  }
  return selectedValues.value.length > 0
})

function toggleChip(value) {
  if (isMulti.value) {
    const idx = selectedValues.value.indexOf(value)
    if (idx >= 0) {
      selectedValues.value.splice(idx, 1)
    } else if (!maxReached.value) {
      selectedValues.value.push(value)
    }
  } else {
    selectedValues.value = [value]
  }
}

function submit() {
  if (!canSubmit.value) return

  let antwort
  const typ = props.frage.typ

  if (typ === 'slider') {
    antwort = sliderValue.value
  } else if (typ === 'freitext') {
    antwort = freitextValue.value.trim()
  } else if (typ === 'chips_freitext' && freitextValue.value.trim()) {
    antwort = [...selectedValues.value, freitextValue.value.trim()]
  } else if (isMulti.value) {
    antwort = selectedValues.value
  } else {
    antwort = selectedValues.value[0]
  }

  emit('antwort', { frage_key: props.frage.key, antwort })
}

function skip() {
  emit('ueberspringen', props.frage.key)
}
</script>

<template>
  <div class="seele-frage">
    <!-- Progress dots -->
    <div class="frage-progress">
      <span
        v-for="i in fortschritt.gesamt"
        :key="i"
        class="progress-dot"
        :class="{
          'progress-dot--done': i < fortschritt.aktuell,
          'progress-dot--current': i === fortschritt.aktuell
        }"
      />
    </div>

    <!-- Question text -->
    <h2 class="frage-text">{{ frage.frage }}</h2>

    <!-- Chips for options -->
    <div
      v-if="frage.typ === 'chips' || frage.typ === 'chips_freitext'"
      class="frage-chips"
    >
      <SeeleChip
        v-for="option in frage.optionen"
        :key="option"
        :label="option"
        :value="option"
        :is-selected="selectedValues.includes(option)"
        @toggle="toggleChip"
      />
    </div>

    <!-- Freitext for chips_freitext -->
    <div v-if="frage.typ === 'chips_freitext'" class="frage-freitext">
      <input
        v-model="freitextValue"
        type="text"
        class="freitext-input"
        placeholder="Eigene Antwort..."
        @keydown.enter.prevent="submit"
      />
    </div>

    <!-- Pure freitext -->
    <div v-if="frage.typ === 'freitext'" class="frage-freitext">
      <textarea
        v-model="freitextValue"
        class="freitext-textarea"
        rows="3"
        placeholder="Deine Antwort..."
        @keydown.enter.ctrl.prevent="submit"
      />
    </div>

    <!-- Slider -->
    <div v-if="frage.typ === 'slider'" class="frage-slider">
      <input
        v-model.number="sliderValue"
        type="range"
        class="slider-input"
        :min="frage.min_wert || 0"
        :max="frage.max_wert || 10"
        :step="frage.schritt || 1"
      />
      <div class="slider-labels">
        <span>{{ frage.min_wert || 0 }}</span>
        <span class="slider-current">{{ sliderValue }}</span>
        <span>{{ frage.max_wert || 10 }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="frage-actions">
      <button
        class="skip-link"
        type="button"
        @click="skip"
      >
        Ueberspringen
      </button>
      <button
        class="zen-btn zen-btn-ai"
        :disabled="!canSubmit"
        type="button"
        @click="submit"
      >
        Weiter
      </button>
    </div>
  </div>
</template>

<style scoped>
.seele-frage {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-lg) 0;
  animation: frageFadeIn 0.4s var(--ease-zen, ease);
}

@keyframes frageFadeIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Progress dots */
.frage-progress {
  display: flex;
  gap: 6px;
  margin-bottom: var(--space-xl);
}

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-sand);
  transition: all 0.3s var(--ease-zen, ease);
}

.progress-dot--done {
  background: var(--color-ai);
}

.progress-dot--current {
  background: var(--color-ai);
  transform: scale(1.3);
}

/* Question text */
.frage-text {
  font-family: var(--font-display);
  font-size: clamp(1.25rem, 3vw, 1.75rem);
  font-weight: 400;
  color: var(--color-sumi);
  letter-spacing: -0.01em;
  margin-bottom: var(--space-xl);
  max-width: 500px;
  line-height: var(--leading-relaxed, 1.6);
}

/* Chips grid */
.frage-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  max-width: 500px;
}

/* Freitext */
.frage-freitext {
  width: 100%;
  max-width: 400px;
  margin-bottom: var(--space-lg);
}

.freitext-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 1.5px solid var(--color-sand);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  color: var(--color-sumi);
  background: var(--color-washi);
  transition: border-color 0.2s;
  font-family: inherit;
}

.freitext-input:focus {
  outline: none;
  border-color: var(--color-ai);
}

.freitext-textarea {
  width: 100%;
  padding: var(--space-md);
  border: 1.5px solid var(--color-sand);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  color: var(--color-sumi);
  background: var(--color-washi);
  resize: vertical;
  font-family: inherit;
  line-height: var(--leading-relaxed, 1.6);
  transition: border-color 0.2s;
}

.freitext-textarea:focus {
  outline: none;
  border-color: var(--color-ai);
}

/* Slider */
.frage-slider {
  width: 100%;
  max-width: 400px;
  margin-bottom: var(--space-lg);
}

.slider-input {
  width: 100%;
  -webkit-appearance: none;
  height: 6px;
  border-radius: var(--radius-full, 9999px);
  background: var(--color-sand);
  outline: none;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-ai);
  cursor: pointer;
  border: 3px solid var(--color-washi);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-sm);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.slider-current {
  font-weight: 600;
  color: var(--color-ai);
  font-size: 1rem;
}

/* Actions */
.frage-actions {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-top: var(--space-md);
}

.skip-link {
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  cursor: pointer;
  padding: var(--space-xs) var(--space-sm);
  transition: color 0.2s;
}

.skip-link:hover {
  color: var(--color-text-secondary);
}

.zen-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .frage-text {
    font-size: 1.25rem;
  }

  .frage-chips {
    gap: var(--space-xs);
  }
}
</style>
