<script setup>
const emit = defineEmits(['starten', 'dismiss'])
</script>

<template>
  <div class="seele-nudge zen-card">
    <div class="nudge-content">
      <div class="nudge-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </div>
      <div class="nudge-text">
        <h4>Lass uns dich kennenlernen</h4>
        <p>Beantworte ein paar kurze Fragen, damit wir deine Bewerbungen besser personalisieren können.</p>
      </div>
    </div>
    <div class="nudge-actions">
      <button class="zen-btn zen-btn-sm" @click="emit('dismiss')">
        Später
      </button>
      <button class="zen-btn zen-btn-sm zen-btn-ai" @click="emit('starten')">
        Los geht's
      </button>
    </div>
  </div>
</template>

<style scoped>
.seele-nudge {
  padding: var(--space-lg);
  border-left: 3px solid var(--color-ai);
}

.nudge-content {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.nudge-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.nudge-text h4 {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
}

.nudge-text p {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  line-height: var(--leading-relaxed, 1.6);
  margin: 0;
}

.nudge-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
</style>
