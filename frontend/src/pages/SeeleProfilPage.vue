<script setup>
import { ref, computed, onMounted } from 'vue'
import { seeleStore } from '../stores/seele'
import SeeleFlow from '../components/seele/SeeleFlow.vue'

const showFlow = ref(false)

const hasProfil = computed(() => !!seeleStore.profil)
const vollstaendigkeit = computed(() => seeleStore.vollstaendigkeit)

// Profile sections for display
const sektionen = computed(() => {
  if (!seeleStore.profil) return []
  const p = seeleStore.profil
  const sections = []

  if (p.arbeitsweise || p.teamrolle) {
    sections.push({
      titel: 'Arbeitsweise',
      felder: [
        p.arbeitsweise && { label: 'Bevorzugte Arbeitsweise', wert: p.arbeitsweise },
        p.teamrolle && { label: 'Teamrolle', wert: p.teamrolle },
      ].filter(Boolean)
    })
  }

  if (p.branche || p.erfahrung) {
    sections.push({
      titel: 'Berufliches',
      felder: [
        p.branche && { label: 'Branche', wert: p.branche },
        p.erfahrung && { label: 'Erfahrung', wert: p.erfahrung },
      ].filter(Boolean)
    })
  }

  if (p.motivation || p.werte?.length) {
    sections.push({
      titel: 'Motivation & Werte',
      felder: [
        p.motivation && { label: 'Motivation', wert: p.motivation },
        p.werte?.length && { label: 'Werte', wert: p.werte.join(', ') },
      ].filter(Boolean)
    })
  }

  if (p.staerken?.length || p.interessen?.length) {
    sections.push({
      titel: 'Staerken & Interessen',
      felder: [
        p.staerken?.length && { label: 'Staerken', wert: p.staerken.join(', ') },
        p.interessen?.length && { label: 'Interessen', wert: p.interessen.join(', ') },
      ].filter(Boolean)
    })
  }

  if (p.kommunikationsstil || p.fuehrungspraeferenz) {
    sections.push({
      titel: 'Kommunikation',
      felder: [
        p.kommunikationsstil && { label: 'Kommunikationsstil', wert: p.kommunikationsstil },
        p.fuehrungspraeferenz && { label: 'Fuehrungspraeferenz', wert: p.fuehrungspraeferenz },
      ].filter(Boolean)
    })
  }

  return sections
})

function openFlow() {
  showFlow.value = true
}

function onFlowClose() {
  showFlow.value = false
}

function onFlowComplete() {
  showFlow.value = false
  seeleStore.fetchProfil()
}

onMounted(() => {
  seeleStore.fetchProfil()
})
</script>

<template>
  <div class="seele-profil-page">
    <div class="container">
      <!-- Header -->
      <section class="page-header animate-fade-up">
        <h1>Persoenlichkeitsprofil</h1>
        <p class="page-subtitle">
          Dein Profil hilft uns, Bewerbungen individuell auf dich zuzuschneiden.
        </p>
      </section>

      <!-- Completeness bar -->
      <section class="completeness-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="completeness-card zen-card">
          <div class="completeness-info">
            <span class="completeness-label">Vollstaendigkeit</span>
            <span class="completeness-value">{{ vollstaendigkeit }}%</span>
          </div>
          <div class="completeness-bar">
            <div class="completeness-fill" :style="{ width: `${vollstaendigkeit}%` }"></div>
          </div>
          <button class="zen-btn zen-btn-ai zen-btn-sm completeness-btn" @click="openFlow">
            {{ hasProfil ? 'Profil erweitern' : 'Profil erstellen' }}
          </button>
        </div>
      </section>

      <!-- Profile sections -->
      <section v-if="hasProfil && sektionen.length" class="profil-sections">
        <div class="ink-stroke"></div>
        <div class="sections-grid">
          <div
            v-for="sektion in sektionen"
            :key="sektion.titel"
            class="section-card zen-card animate-fade-up"
          >
            <h3 class="section-title">{{ sektion.titel }}</h3>
            <div class="section-fields">
              <div v-for="feld in sektion.felder" :key="feld.label" class="section-field">
                <span class="field-label">{{ feld.label }}</span>
                <span class="field-value">{{ feld.wert }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Empty state -->
      <section v-else-if="!hasProfil" class="empty-section animate-fade-up">
        <div class="empty-card zen-card">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <h2>Noch kein Profil vorhanden</h2>
          <p>Beantworte ein paar kurze Fragen und wir personalisieren deine Bewerbungen automatisch.</p>
          <button class="zen-btn zen-btn-ai" @click="openFlow">
            Jetzt erstellen
          </button>
        </div>
      </section>
    </div>

    <!-- SeeleFlow overlay -->
    <SeeleFlow
      v-if="showFlow"
      :overlay="true"
      session-typ="onboarding"
      @close="onFlowClose"
      @complete="onFlowComplete"
    />
  </div>
</template>

<style scoped>
.seele-profil-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

.page-header {
  padding: var(--space-ma-lg) 0 var(--space-ma);
}

.page-header h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
}

.page-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin-bottom: 0;
}

/* Completeness */
.completeness-section {
  margin-bottom: var(--space-ma);
}

.completeness-card {
  padding: var(--space-lg) var(--space-xl);
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.completeness-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  flex-shrink: 0;
}

.completeness-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.completeness-value {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-ai);
}

.completeness-bar {
  flex: 1;
  height: 6px;
  background: var(--color-sand);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.completeness-fill {
  height: 100%;
  background: var(--color-ai);
  border-radius: var(--radius-full, 9999px);
  transition: width 0.6s var(--ease-zen, ease);
}

.completeness-btn {
  flex-shrink: 0;
}

/* Profile sections */
.profil-sections {
  margin-top: var(--space-ma);
}

.profil-sections .ink-stroke {
  margin-bottom: var(--space-ma);
}

.sections-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.section-card {
  padding: var(--space-lg);
}

.section-title {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-border-light);
}

.section-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.section-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-label {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-ghost);
}

.field-value {
  font-size: 0.9375rem;
  color: var(--color-sumi);
  line-height: var(--leading-relaxed, 1.6);
}

/* Empty state */
.empty-section {
  margin-top: var(--space-ma-lg);
}

.empty-card {
  text-align: center;
  padding: var(--space-ma-xl) var(--space-xl);
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: 50%;
  color: var(--color-ai);
  margin: 0 auto var(--space-lg);
}

.empty-card h2 {
  font-size: 1.5rem;
  font-weight: 400;
  margin-bottom: var(--space-sm);
}

.empty-card p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0 auto var(--space-xl);
}

@media (max-width: 768px) {
  .sections-grid {
    grid-template-columns: 1fr;
  }

  .completeness-card {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-md);
  }

  .completeness-info {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
