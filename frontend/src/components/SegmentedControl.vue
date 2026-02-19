<template>
  <div class="segmented-control" :class="[`segmented-control--${size}`]" role="group">
    <button
      v-for="opt in options"
      :key="opt.value"
      class="segment"
      :class="{ active: modelValue === opt.value }"
      :aria-pressed="modelValue === opt.value"
      :disabled="disabled"
      @click="$emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, required: true },
  options: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  size: { type: String, default: 'md', validator: (v) => ['sm', 'md'].includes(v) }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.segmented-control {
  display: inline-flex;
  gap: 2px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 2px;
}

.segment {
  padding: var(--space-xs) var(--space-md);
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-subtle);
  white-space: nowrap;
  line-height: 1.4;
}

.segment:hover:not(.active):not(:disabled) {
  background: rgba(61, 90, 108, 0.06);
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.segment.active {
  background: var(--color-ai);
  color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.segment:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Small size */
.segmented-control--sm .segment {
  padding: 2px var(--space-sm);
  font-size: 0.8125rem;
}
</style>
