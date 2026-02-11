<template>
  <span
    :class="[
      'ink-reveal',
      `ink-reveal--${variant}`,
    ]"
    :style="cssVars"
    :aria-label="text"
    role="text"
  >
    <span class="ink-reveal__text" aria-hidden="true">
      <span
        v-for="(word, i) in words"
        :key="i"
        class="ink-reveal__word"
        :class="{ 'ink-reveal__word--visible': i < revealedCount }"
        :style="{ transitionDelay: `${i * staggerMs}ms` }"
      >{{ word }}</span>
    </span>
  </span>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  text: {
    type: String,
    required: true
  },
  delay: {
    type: Number,
    default: 0
  },
  speed: {
    type: Number,
    default: 80
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'brush', 'fade'].includes(value)
  },
  showCursor: {
    type: Boolean,
    default: true
  },
  autoStart: {
    type: Boolean,
    default: true
  },
  loop: {
    type: Boolean,
    default: false
  },
  loopDelay: {
    type: Number,
    default: 2000
  }
})

const emit = defineEmits(['start', 'complete', 'char'])

const revealedCount = ref(0)
const isComplete = ref(false)
const isTyping = ref(false)
let revealTimeout = null

// Split text into words, preserving whitespace and newlines as part of each word
const words = computed(() => {
  if (!props.text) return []
  // Split on word boundaries but keep spaces attached to the following word
  // This preserves the original spacing when rendered
  const result = []
  const parts = props.text.split(/(\s+)/)
  let current = ''
  for (const part of parts) {
    if (/^\s+$/.test(part)) {
      // Whitespace - attach to next word
      current += part
    } else {
      // Word - combine with any preceding whitespace
      current += part
      if (current) {
        result.push(current)
        current = ''
      }
    }
  }
  if (current) result.push(current)
  return result
})

// Stagger delay between words - derived from speed prop
// speed is per-character in the old API, so multiply by avg word length (~5)
const staggerMs = computed(() => Math.max(20, props.speed * 1.5))

const cssVars = computed(() => ({
  '--ink-settle-duration': '420ms',
  '--ink-blur-start': '6px',
}))

const revealNextWord = () => {
  if (revealedCount.value < words.value.length) {
    revealedCount.value++
    emit('char', words.value[revealedCount.value - 1])

    // Slight timing variation for natural feel
    const variation = Math.random() * 30 - 15
    const nextDelay = staggerMs.value + variation

    revealTimeout = setTimeout(revealNextWord, Math.max(20, nextDelay))
  } else {
    isTyping.value = false
    isComplete.value = true
    emit('complete')

    if (props.loop) {
      revealTimeout = setTimeout(() => {
        reset()
        start()
      }, props.loopDelay)
    }
  }
}

const start = () => {
  if (isTyping.value) return

  isTyping.value = true
  isComplete.value = false
  emit('start')

  revealTimeout = setTimeout(revealNextWord, props.delay)
}

const reset = () => {
  clearTimeout(revealTimeout)
  revealedCount.value = 0
  isComplete.value = false
  isTyping.value = false
}

const pause = () => {
  clearTimeout(revealTimeout)
  isTyping.value = false
}

const resume = () => {
  if (!isComplete.value && !isTyping.value) {
    isTyping.value = true
    revealNextWord()
  }
}

watch(() => props.text, () => {
  reset()
  if (props.autoStart) {
    start()
  }
})

onMounted(() => {
  if (props.autoStart) {
    start()
  }
})

onUnmounted(() => {
  clearTimeout(revealTimeout)
})

defineExpose({ start, reset, pause, resume })
</script>

<style scoped>
.ink-reveal {
  display: inline;
  font-family: var(--font-body);
  color: var(--color-text-primary);
}

.ink-reveal__text {
  display: inline;
  white-space: pre-wrap;
}

.ink-reveal__word {
  display: inline;
  opacity: 0;
  filter: blur(var(--ink-blur-start));
  transform: translateY(6px);
  transition:
    opacity var(--ink-settle-duration) var(--ease-zen),
    filter var(--ink-settle-duration) var(--ease-zen),
    transform var(--ink-settle-duration) var(--ease-zen);
}

.ink-reveal__word--visible {
  opacity: 1;
  filter: blur(0);
  transform: translateY(0);
}

/* Default variant */
.ink-reveal--default .ink-reveal__word {
  letter-spacing: var(--tracking-normal);
}

/* Brush variant - calligraphic feel with ink-wash coloring */
.ink-reveal--brush {
  font-family: var(--font-display);
  font-weight: 400;
}

.ink-reveal--brush .ink-reveal__word {
  --ink-settle-duration: 500ms;
  --ink-blur-start: 8px;
  transform: translateY(8px) scaleY(0.96);
}

.ink-reveal--brush .ink-reveal__word--visible {
  transform: translateY(0) scaleY(1);
  color: var(--color-sumi);
}

/* Fade variant - gentler, less movement */
.ink-reveal--fade .ink-reveal__word {
  --ink-settle-duration: 350ms;
  --ink-blur-start: 3px;
  transform: translateY(3px);
}

.ink-reveal--fade .ink-reveal__word--visible {
  transform: translateY(0);
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .ink-reveal__word {
    filter: none;
    transform: none;
    transition: opacity 0.2s;
  }

  .ink-reveal__word--visible {
    filter: none;
    transform: none;
  }
}
</style>
