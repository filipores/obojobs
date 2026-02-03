<template>
  <div
    class="scrollable-table-container"
    :class="{
      'can-scroll-left': canScrollLeft,
      'can-scroll-right': canScrollRight
    }"
  >
    <div
      ref="scrollContainer"
      class="scrollable-table-inner"
      @scroll="updateScrollState"
    >
      <slot></slot>
    </div>

    <!-- Left scroll indicator -->
    <button
      v-if="canScrollLeft"
      class="scroll-indicator scroll-indicator-left"
      @click="scrollLeft"
      aria-label="Nach links scrollen"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="15 18 9 12 15 6"/>
      </svg>
    </button>

    <!-- Right scroll indicator -->
    <button
      v-if="canScrollRight"
      class="scroll-indicator scroll-indicator-right"
      @click="scrollRight"
      aria-label="Nach rechts scrollen"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="9 18 15 12 9 6"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const scrollContainer = ref(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

const updateScrollState = () => {
  if (!scrollContainer.value) return

  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value

  // Check if we can scroll left (not at the beginning)
  canScrollLeft.value = scrollLeft > 5

  // Check if we can scroll right (not at the end)
  canScrollRight.value = scrollLeft + clientWidth < scrollWidth - 5
}

const scrollLeft = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({
    left: -200,
    behavior: 'smooth'
  })
}

const scrollRight = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({
    left: 200,
    behavior: 'smooth'
  })
}

// Create a ResizeObserver to update scroll state when content changes
let resizeObserver = null

onMounted(() => {
  nextTick(() => {
    updateScrollState()

    // Observe resize events
     
    if (typeof ResizeObserver !== 'undefined' && scrollContainer.value) {
      // eslint-disable-next-line no-undef
      resizeObserver = new ResizeObserver(() => {
        updateScrollState()
      })
      resizeObserver.observe(scrollContainer.value)
    }

    // Also listen to window resize
    window.addEventListener('resize', updateScrollState)
  })
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  window.removeEventListener('resize', updateScrollState)
})

// Expose method to manually update scroll state (useful when slot content changes)
defineExpose({
  updateScrollState
})
</script>

<style scoped>
.scrollable-table-container {
  position: relative;
}

.scrollable-table-inner {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: var(--color-sand) transparent;
}

.scrollable-table-inner::-webkit-scrollbar {
  height: 6px;
}

.scrollable-table-inner::-webkit-scrollbar-track {
  background: transparent;
}

.scrollable-table-inner::-webkit-scrollbar-thumb {
  background: var(--color-sand);
  border-radius: 3px;
}

.scrollable-table-inner::-webkit-scrollbar-thumb:hover {
  background: var(--color-stone);
}

/* Fade overlay effects */
.scrollable-table-container::before,
.scrollable-table-container::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 6px; /* Account for scrollbar */
  width: 40px;
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: 1;
}

.scrollable-table-container::before {
  left: 0;
  background: linear-gradient(
    to right,
    var(--color-bg-elevated, #fff) 0%,
    transparent 100%
  );
}

.scrollable-table-container::after {
  right: 0;
  background: linear-gradient(
    to left,
    var(--color-bg-elevated, #fff) 0%,
    transparent 100%
  );
}

.scrollable-table-container.can-scroll-left::before {
  opacity: 1;
}

.scrollable-table-container.can-scroll-right::after {
  opacity: 1;
}

/* Scroll indicator buttons */
.scroll-indicator {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated, #fff);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full, 50%);
  color: var(--color-sumi);
  cursor: pointer;
  z-index: 2;
  opacity: 0.9;
  box-shadow: var(--shadow-paper);
  transition: all var(--transition-base);
}

.scroll-indicator:hover {
  opacity: 1;
  background: var(--color-ai-subtle);
  border-color: var(--color-ai);
  color: var(--color-ai);
  transform: translateY(-50%) scale(1.05);
}

.scroll-indicator:focus-visible {
  outline: 2px solid var(--color-ai);
  outline-offset: 2px;
}

.scroll-indicator-left {
  left: var(--space-sm, 8px);
}

.scroll-indicator-right {
  right: var(--space-sm, 8px);
}

/* Hide buttons on touch devices (they can swipe naturally) */
@media (hover: none) and (pointer: coarse) {
  .scroll-indicator {
    display: none;
  }

  /* Make fade effects more visible on touch */
  .scrollable-table-container::before,
  .scrollable-table-container::after {
    width: 24px;
  }
}

/* Reduce fade on smaller screens */
@media (max-width: 480px) {
  .scrollable-table-container::before,
  .scrollable-table-container::after {
    width: 20px;
  }

  .scroll-indicator {
    width: 28px;
    height: 28px;
  }
}
</style>
