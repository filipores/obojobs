<script setup>
import { ref } from 'vue'

defineProps({
  items: {
    type: Array,
    required: true
  }
})

const openIndex = ref(null)

function toggle(index) {
  openIndex.value = openIndex.value === index ? null : index
}
</script>

<template>
  <div class="faq-list">
    <div v-for="(item, index) in items" :key="index" class="faq-item">
      <button
        :id="`faq-question-${index}`"
        class="faq-question"
        :aria-expanded="openIndex === index"
        :aria-controls="`faq-answer-${index}`"
        @click="toggle(index)"
      >
        <span>{{ item.question }}</span>
        <svg
          class="faq-chevron"
          :class="{ 'faq-chevron-open': openIndex === index }"
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
        >
          <path
            d="M5 7.5L10 12.5L15 7.5"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <div
        :id="`faq-answer-${index}`"
        role="region"
        :aria-labelledby="`faq-question-${index}`"
        class="faq-answer"
        :class="{ 'faq-answer-visible': openIndex === index }"
      >
        <p>{{ item.answer }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.faq-list {
  max-width: 800px;
  margin: 0 auto;
}

.faq-item {
  border-bottom: 1px solid var(--color-border-light);
}

.faq-item:first-child {
  border-top: 1px solid var(--color-border-light);
}

.faq-question {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: var(--space-md) 0;
  border: none;
  background: none;
  font-family: var(--font-body);
  font-size: 1.0625rem;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
  transition: color var(--transition-base);
}

.faq-question:hover {
  color: var(--color-ai);
}

.faq-chevron {
  flex-shrink: 0;
  transition: transform 0.3s var(--ease-zen);
}

.faq-chevron-open {
  transform: rotate(180deg);
}

.faq-answer {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s var(--ease-zen);
}

.faq-answer-visible {
  max-height: 300px;
  padding-bottom: var(--space-lg);
}

.faq-answer p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  max-width: 65ch;
}
</style>
