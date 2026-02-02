<template>
  <div
    :class="[
      'enso-circle',
      `enso-circle--${state}`,
      `enso-circle--${size}`,
      { 'enso-circle--seasonal': seasonal }
    ]"
    :style="cssVars"
    role="img"
    :aria-label="ariaLabel"
  >
    <svg
      :width="dimensions.width"
      :height="dimensions.height"
      :viewBox="`0 0 ${dimensions.viewBox} ${dimensions.viewBox}`"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        ref="circleRef"
        :cx="dimensions.viewBox / 2"
        :cy="dimensions.viewBox / 2"
        :r="dimensions.radius"
        :stroke="strokeColor"
        :stroke-width="dimensions.strokeWidth"
        stroke-linecap="round"
        fill="none"
        :class="['enso-circle__path', `enso-circle__path--${state}`]"
        :style="pathStyle"
      />
    </svg>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  state: {
    type: String,
    default: 'broken',
    validator: (value) => ['broken', 'complete', 'breathing', 'rotating'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl'].includes(value)
  },
  color: {
    type: String,
    default: null
  },
  seasonal: {
    type: Boolean,
    default: false
  },
  duration: {
    type: Number,
    default: 4000
  }
})

const emit = defineEmits(['complete', 'cycle'])

const circleRef = ref(null)
const isAnimating = ref(false)

const sizeMap = {
  sm: { width: 40, height: 40, viewBox: 100, radius: 42, strokeWidth: 4 },
  md: { width: 80, height: 80, viewBox: 100, radius: 42, strokeWidth: 5 },
  lg: { width: 160, height: 160, viewBox: 100, radius: 42, strokeWidth: 6 },
  xl: { width: 240, height: 240, viewBox: 100, radius: 42, strokeWidth: 7 }
}

const dimensions = computed(() => sizeMap[props.size])

const circumference = computed(() => 2 * Math.PI * dimensions.value.radius)

const strokeColor = computed(() => {
  if (props.color) return props.color
  return props.seasonal ? 'var(--color-seasonal)' : 'var(--color-sumi)'
})

const ariaLabel = computed(() => {
  const stateLabels = {
    broken: 'Incomplete enso circle, representing openness',
    complete: 'Complete enso circle, representing wholeness',
    breathing: 'Breathing enso circle, representing meditation',
    rotating: 'Rotating enso circle, representing continuous flow'
  }
  return stateLabels[props.state]
})

const cssVars = computed(() => ({
  '--enso-duration': `${props.duration}ms`,
  '--enso-circumference': circumference.value
}))

const pathStyle = computed(() => {
  const baseStyle = {
    strokeDasharray: circumference.value,
    transformOrigin: 'center'
  }

  switch (props.state) {
    case 'broken':
      return {
        ...baseStyle,
        strokeDashoffset: circumference.value * 0.15
      }
    case 'complete':
      return {
        ...baseStyle,
        strokeDashoffset: 0
      }
    case 'breathing':
    case 'rotating':
      return {
        ...baseStyle,
        strokeDashoffset: 0
      }
    default:
      return baseStyle
  }
})

watch(() => props.state, (newState, oldState) => {
  if (oldState === 'broken' && newState === 'complete') {
    isAnimating.value = true
    setTimeout(() => {
      isAnimating.value = false
      emit('complete')
    }, props.duration)
  }
})

onMounted(() => {
  if (props.state === 'rotating' || props.state === 'breathing') {
    const handleCycle = () => {
      emit('cycle')
    }
    if (circleRef.value) {
      circleRef.value.addEventListener('animationiteration', handleCycle)
    }
  }
})
</script>

<style scoped>
.enso-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.enso-circle__path {
  transition: stroke-dashoffset var(--enso-duration) var(--ease-zen);
}

/* Broken state - gap represents breath, openness */
.enso-circle__path--broken {
  opacity: 0.7;
}

/* Complete state - wholeness achieved */
.enso-circle__path--complete {
  opacity: 1;
  animation: completeEnso var(--enso-duration) var(--ease-zen) forwards;
}

/* Breathing state - meditative pulsing */
.enso-circle__path--breathing {
  animation: breatheEnso var(--enso-duration) var(--ease-zen) infinite;
}

/* Rotating state - continuous contemplation */
.enso-circle__path--rotating {
  animation: rotateZen var(--enso-duration) linear infinite;
}

/* Size-specific adjustments for intentional imperfection */
.enso-circle--sm .enso-circle__path {
  stroke-width: 4;
}

.enso-circle--md .enso-circle__path {
  stroke-width: 5;
}

.enso-circle--lg .enso-circle__path {
  stroke-width: 6;
}

.enso-circle--xl .enso-circle__path {
  stroke-width: 7;
}

/* Seasonal color variant */
.enso-circle--seasonal .enso-circle__path {
  stroke: var(--color-seasonal);
}

/* Animations */
@keyframes completeEnso {
  0% {
    stroke-dashoffset: calc(var(--enso-circumference) * 0.15);
    opacity: 0.7;
  }
  60% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  80% {
    transform: scale(1.02);
  }
  100% {
    stroke-dashoffset: 0;
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes breatheEnso {
  0%, 100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.03);
    opacity: 1;
  }
}

@keyframes rotateZen {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .enso-circle__path {
    animation: none !important;
    transition: none !important;
  }
}
</style>
