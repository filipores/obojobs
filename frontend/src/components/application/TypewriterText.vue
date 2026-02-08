<template>
  <span
    :class="[
      'typewriter',
      `typewriter--${variant}`,
      { 'typewriter--cursor': showCursor && !isComplete }
    ]"
    :style="cssVars"
    :aria-label="text"
    role="text"
  >
    <span class="typewriter__text" aria-hidden="true">{{ displayedText }}</span>
    <span
      v-if="showCursor && !isComplete"
      class="typewriter__cursor"
      aria-hidden="true"
    >|</span>
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

const displayedText = ref('')
const isComplete = ref(false)
const isTyping = ref(false)
let typingTimeout = null
let charIndex = 0

const cssVars = computed(() => ({
  '--typewriter-speed': `${props.speed}ms`,
  '--typewriter-cursor-blink': '800ms'
}))

const typeNextChar = () => {
  if (charIndex < props.text.length) {
    displayedText.value = props.text.slice(0, charIndex + 1)
    emit('char', props.text[charIndex])
    charIndex++

    const variation = Math.random() * 20 - 10
    const nextDelay = props.speed + variation

    typingTimeout = setTimeout(typeNextChar, Math.max(30, nextDelay))
  } else {
    isTyping.value = false
    isComplete.value = true
    emit('complete')

    if (props.loop) {
      typingTimeout = setTimeout(() => {
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

  typingTimeout = setTimeout(typeNextChar, props.delay)
}

const reset = () => {
  clearTimeout(typingTimeout)
  displayedText.value = ''
  charIndex = 0
  isComplete.value = false
  isTyping.value = false
}

const pause = () => {
  clearTimeout(typingTimeout)
  isTyping.value = false
}

const resume = () => {
  if (!isComplete.value && !isTyping.value) {
    isTyping.value = true
    typeNextChar()
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
  clearTimeout(typingTimeout)
})

defineExpose({ start, reset, pause, resume })
</script>

<style scoped>
.typewriter {
  display: inline;
  font-family: var(--font-body);
  color: var(--color-text-primary);
}

.typewriter__text {
  display: inline;
}

.typewriter__cursor {
  display: inline;
  animation: cursorBlink var(--typewriter-cursor-blink) step-end infinite;
  color: var(--color-ai);
  font-weight: 300;
  margin-left: 1px;
}

/* Default variant - clean typewriter */
.typewriter--default .typewriter__text {
  letter-spacing: var(--tracking-normal);
}

/* Brush variant - calligraphic reveal */
.typewriter--brush {
  font-family: var(--font-display);
  font-weight: 400;
}

.typewriter--brush .typewriter__text {
  background: linear-gradient(
    90deg,
    var(--color-sumi) 0%,
    var(--color-ai) 45%,
    var(--color-sumi) 55%,
    var(--color-sumi) 100%
  );
  background-size: 300% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: brushShimmer 3s ease-in-out infinite;
}

.typewriter--brush .typewriter__cursor {
  text-shadow: 0 0 8px var(--color-ai);
}

/* Fade variant - gentle appearance */
.typewriter--fade .typewriter__text {
  opacity: 0;
  animation: fadeChar 0.4s var(--ease-zen) forwards;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@keyframes brushReveal {
  from {
    background-position: 100% 0;
    opacity: 0.5;
  }
  to {
    background-position: 0 0;
    opacity: 1;
  }
}

@keyframes brushShimmer {
  0% { background-position: 100% 0; }
  50% { background-position: 0% 0; }
  100% { background-position: 100% 0; }
}

@keyframes fadeChar {
  from {
    opacity: 0;
    transform: translateY(2px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .typewriter__cursor {
    animation: none;
    opacity: 1;
  }

  .typewriter--brush .typewriter__text,
  .typewriter--fade .typewriter__text {
    animation: none;
    opacity: 1;
  }
}
</style>
