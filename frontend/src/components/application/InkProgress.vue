<template>
  <div
    :class="[
      'ink-progress',
      `ink-progress--${variant}`,
      `ink-progress--${size}`,
      { 'ink-progress--indeterminate': indeterminate }
    ]"
    :style="cssVars"
    role="progressbar"
    :aria-valuenow="indeterminate ? undefined : progress"
    :aria-valuemin="0"
    :aria-valuemax="100"
    :aria-label="ariaLabel"
  >
    <svg
      :width="dimensions.width"
      :height="dimensions.height"
      :viewBox="`0 0 ${dimensions.viewBox} ${dimensions.strokeHeight}`"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      class="ink-progress__svg"
    >
      <!-- Background track with hand-drawn effect -->
      <path
        :d="trackPath"
        :stroke="trackColor"
        :stroke-width="dimensions.strokeWidth"
        stroke-linecap="round"
        fill="none"
        class="ink-progress__track"
      />

      <!-- Progress fill with ink animation -->
      <path
        :d="progressPath"
        :stroke="fillColor"
        :stroke-width="dimensions.strokeWidth"
        stroke-linecap="round"
        fill="none"
        class="ink-progress__fill"
        :style="fillStyle"
      />
    </svg>

    <!-- Optional label -->
    <span v-if="showLabel" class="ink-progress__label">
      {{ labelText }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  progress: {
    type: Number,
    default: 0,
    validator: (value) => value >= 0 && value <= 100
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'brush', 'dotted'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  indeterminate: {
    type: Boolean,
    default: false
  },
  showLabel: {
    type: Boolean,
    default: false
  },
  labelFormat: {
    type: Function,
    default: (value) => `${Math.round(value)}%`
  },
  color: {
    type: String,
    default: null
  },
  duration: {
    type: Number,
    default: 4000
  }
})

const emit = defineEmits(['complete'])

const sizeMap = {
  sm: { width: 120, height: 8, viewBox: 120, strokeHeight: 8, strokeWidth: 3 },
  md: { width: 200, height: 12, viewBox: 200, strokeHeight: 12, strokeWidth: 4 },
  lg: { width: 300, height: 16, viewBox: 300, strokeHeight: 16, strokeWidth: 5 }
}

const dimensions = computed(() => sizeMap[props.size])

const trackColor = computed(() => 'var(--color-sand)')

const fillColor = computed(() => props.color || 'var(--color-sumi)')

const ariaLabel = computed(() => {
  if (props.indeterminate) return 'Loading in progress'
  return `Progress: ${Math.round(props.progress)} percent`
})

const labelText = computed(() => props.labelFormat(props.progress))

const cssVars = computed(() => ({
  '--ink-duration': `${props.duration}ms`,
  '--ink-progress': props.progress / 100
}))

const generateHandDrawnPath = (startX, endX, y, seed = 1) => {
  const points = []
  const segments = 8
  const segmentWidth = (endX - startX) / segments

  for (let i = 0; i <= segments; i++) {
    const x = startX + i * segmentWidth
    const wobble = Math.sin(i * seed * 0.7) * 0.8
    points.push(`${x},${y + wobble}`)
  }

  return `M ${points.join(' L ')}`
}

const trackPath = computed(() => {
  const padding = dimensions.value.strokeWidth
  const y = dimensions.value.strokeHeight / 2
  return generateHandDrawnPath(padding, dimensions.value.viewBox - padding, y, 1)
})

const progressPath = computed(() => {
  const padding = dimensions.value.strokeWidth
  const y = dimensions.value.strokeHeight / 2
  const progressWidth = (dimensions.value.viewBox - padding * 2) * (props.progress / 100)
  return generateHandDrawnPath(padding, padding + progressWidth, y, 2)
})

const totalPathLength = computed(() => dimensions.value.viewBox - dimensions.value.strokeWidth * 2)

const fillStyle = computed(() => {
  if (props.indeterminate) {
    return {
      strokeDasharray: `${totalPathLength.value * 0.3} ${totalPathLength.value * 0.7}`,
      animation: `drawInk var(--ink-duration) linear infinite`
    }
  }

  return {
    strokeDasharray: totalPathLength.value,
    strokeDashoffset: totalPathLength.value * (1 - props.progress / 100),
    transition: `stroke-dashoffset var(--ink-duration) var(--ease-zen)`
  }
})

if (props.progress >= 100 && !props.indeterminate) {
  emit('complete')
}
</script>

<style scoped>
.ink-progress {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-xs);
}

.ink-progress__svg {
  display: block;
  overflow: visible;
}

.ink-progress__track {
  opacity: 0.4;
}

.ink-progress__fill {
  transform-origin: left center;
}

/* Size variants */
.ink-progress--sm {
  font-size: 0.75rem;
}

.ink-progress--md {
  font-size: 0.875rem;
}

.ink-progress--lg {
  font-size: 1rem;
}

/* Default variant */
.ink-progress--default .ink-progress__fill {
  filter: none;
}

/* Brush variant - more organic ink feel */
.ink-progress--brush .ink-progress__track,
.ink-progress--brush .ink-progress__fill {
  filter: url(#ink-texture);
}

.ink-progress--brush .ink-progress__fill {
  opacity: 0.9;
}

/* Dotted variant */
.ink-progress--dotted .ink-progress__track {
  stroke-dasharray: 2 6;
}

.ink-progress--dotted .ink-progress__fill {
  stroke-dasharray: 4 4;
}

/* Indeterminate state */
.ink-progress--indeterminate .ink-progress__fill {
  animation: drawInk var(--ink-duration) linear infinite;
}

/* Label styling */
.ink-progress__label {
  font-family: var(--font-body);
  font-size: inherit;
  color: var(--color-text-tertiary);
  letter-spacing: var(--tracking-wide);
}

/* Animations */
@keyframes drawInk {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -200;
  }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .ink-progress__fill {
    animation: none !important;
    transition: none !important;
  }

  .ink-progress--indeterminate .ink-progress__fill {
    stroke-dasharray: none;
    stroke-dashoffset: 0;
  }
}
</style>
