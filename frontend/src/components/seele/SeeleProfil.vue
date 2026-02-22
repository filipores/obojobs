<script setup>
import { computed } from 'vue'
import { seeleStore } from '../../stores/seele'

const emit = defineEmits(['erweitern'])

const hasProfil = computed(() => !!seeleStore.profil)
const vollstaendigkeit = computed(() => seeleStore.vollstaendigkeit)

// Preview key fields from profile
const vorschau = computed(() => {
  if (!seeleStore.profil) return []
  const p = seeleStore.profil
  const items = []
  if (p.motivation?.aktuelle_situation) items.push({ label: 'Situation', wert: p.motivation.aktuelle_situation })
  if (p.arbeitsstil?.arbeitsmodell?.length) items.push({ label: 'Arbeitsmodell', wert: p.arbeitsstil.arbeitsmodell.join(', ') })
  if (p.motivation?.wichtig_im_job?.length) items.push({ label: 'Prioritäten', wert: p.motivation.wichtig_im_job.slice(0, 3).join(', ') })
  if (p.motivation?.wechsel_tempo) items.push({ label: 'Verfügbarkeit', wert: p.motivation.wechsel_tempo })
  if (p.arbeitsstil?.staerken?.length) items.push({ label: 'Stärken', wert: p.arbeitsstil.staerken.slice(0, 3).join(', ') })
  if (p.berufserfahrung?.branche) items.push({ label: 'Branche', wert: p.berufserfahrung.branche })
  return items.slice(0, 4)
})

// SVG circle math
const circumference = 2 * Math.PI * 42
const dasharray = computed(() => `${(vollstaendigkeit.value / 100) * circumference} ${circumference}`)
</script>

<template>
  <div class="seele-profil zen-card">
    <div class="profil-header">
      <h3 class="profil-title">Persönlichkeitsprofil</h3>
      <span v-if="hasProfil" class="profil-badge">
        {{ vollstaendigkeit }}%
      </span>
    </div>

    <template v-if="hasProfil">
      <!-- Completeness ring + preview -->
      <div class="profil-content">
        <div class="profil-ring">
          <svg viewBox="0 0 100 100" class="ring-svg">
            <circle
              cx="50" cy="50" r="42"
              fill="none"
              stroke="var(--color-sand)"
              stroke-width="5"
            />
            <circle
              cx="50" cy="50" r="42"
              fill="none"
              stroke="var(--color-ai)"
              stroke-width="5"
              stroke-linecap="round"
              :stroke-dasharray="dasharray"
              transform="rotate(-90 50 50)"
              class="ring-fill"
            />
          </svg>
          <div class="ring-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-ai)" stroke-width="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
        </div>

        <div class="profil-fields">
          <div v-for="item in vorschau" :key="item.label" class="profil-field">
            <span class="field-label">{{ item.label }}</span>
            <span class="field-value">{{ item.wert }}</span>
          </div>
        </div>
      </div>

      <button class="zen-btn zen-btn-sm zen-btn-ai profil-btn" @click="emit('erweitern')">
        Profil erweitern
      </button>
    </template>

    <template v-else>
      <!-- Empty state -->
      <div class="profil-empty">
        <div class="empty-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
        <p class="empty-text">Noch kein Profil erstellt</p>
        <p class="empty-hint">Beantworte ein paar Fragen, damit wir deine Bewerbungen personalisieren können.</p>
        <button class="zen-btn zen-btn-sm zen-btn-ai" @click="emit('erweitern')">
          Jetzt erstellen
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.seele-profil {
  padding: var(--space-lg);
}

.profil-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}

.profil-title {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0;
}

.profil-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-ai);
  background: var(--color-ai-subtle);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full, 9999px);
}

/* Content with ring */
.profil-content {
  display: flex;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.profil-ring {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-fill {
  transition: stroke-dasharray 0.8s var(--ease-zen, ease);
}

.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profil-fields {
  flex: 1;
  min-width: 0;
}

.profil-field {
  display: flex;
  flex-direction: column;
  margin-bottom: var(--space-sm);
}

.profil-field:last-child {
  margin-bottom: 0;
}

.field-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.field-value {
  font-size: 0.875rem;
  color: var(--color-sumi);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profil-btn {
  width: 100%;
}

/* Empty state */
.profil-empty {
  text-align: center;
  padding: var(--space-md) 0;
}

.empty-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: 50%;
  color: var(--color-ai);
  margin: 0 auto var(--space-md);
}

.empty-text {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  line-height: var(--leading-relaxed, 1.6);
  margin-bottom: var(--space-lg);
  max-width: 280px;
  margin-left: auto;
  margin-right: auto;
}
</style>
