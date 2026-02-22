<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number, Boolean, Object], default: null },
  isSelected: { type: Boolean, default: false }
})

const emit = defineEmits(['toggle'])
</script>

<template>
  <button
    class="seele-chip"
    :class="{ 'seele-chip--selected': isSelected }"
    type="button"
    @click="emit('toggle', value ?? label)"
  >
    {{ label }}
  </button>
</template>

<style scoped>
.seele-chip {
  display: inline-flex;
  align-items: center;
  padding: var(--space-sm) var(--space-lg);
  border: 1.5px solid var(--color-sand);
  border-radius: var(--radius-full, 9999px);
  background: var(--color-washi);
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  font-weight: 400;
  cursor: pointer;
  transition: all 0.2s var(--ease-zen, ease);
  user-select: none;
  white-space: nowrap;
}

.seele-chip:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
  transform: translateY(-1px);
}

.seele-chip--selected {
  background: var(--color-ai);
  border-color: var(--color-ai);
  color: var(--color-washi);
  font-weight: 500;
}

.seele-chip--selected:hover {
  background: var(--color-ai-light, var(--color-ai));
  border-color: var(--color-ai-light, var(--color-ai));
  color: var(--color-washi);
}
</style>
