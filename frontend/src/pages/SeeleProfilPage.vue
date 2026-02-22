<script setup>
import { ref, computed, onMounted } from 'vue'
import { seeleStore } from '../stores/seele'
import SeeleFlow from '../components/seele/SeeleFlow.vue'

const showFlow = ref(false)

const hasProfil = computed(() => !!seeleStore.profil)
const vollstaendigkeit = computed(() => seeleStore.vollstaendigkeit)

const sessionTyp = computed(() => 'profil')

// Profile sections mapped to actual nested profile structure
const sektionen = computed(() => {
  if (!seeleStore.profil) return []
  const p = seeleStore.profil
  const sections = []

  const fmt = (val) => {
    if (Array.isArray(val)) return val.length ? val.join(', ') : null
    return val
  }

  // Motivation & Situation
  const mot = p.motivation || {}
  const motFelder = [
    mot.aktuelle_situation && { label: 'Aktuelle Situation', wert: mot.aktuelle_situation },
    mot.wechselgrund && { label: 'Wechselgrund', wert: mot.wechselgrund },
    mot.karriereziel && { label: 'Karriereziel', wert: mot.karriereziel },
    mot.wechsel_tempo && { label: 'Verfügbarkeit', wert: mot.wechsel_tempo },
    fmt(mot.wichtig_im_job) && { label: 'Wichtig im Job', wert: fmt(mot.wichtig_im_job) },
    fmt(mot.werte) && { label: 'Werte', wert: fmt(mot.werte) },
    fmt(mot.dealbreaker) && { label: 'Dealbreaker', wert: fmt(mot.dealbreaker) },
  ].filter(Boolean)
  if (motFelder.length) sections.push({ titel: 'Motivation & Situation', felder: motFelder })

  // Arbeitsstil
  const arb = p.arbeitsstil || {}
  const arbFelder = [
    arb.typ && { label: 'Arbeitstyp', wert: arb.typ },
    fmt(arb.arbeitsmodell) && { label: 'Arbeitsmodell', wert: fmt(arb.arbeitsmodell) },
    arb.teamrolle && { label: 'Teamrolle', wert: arb.teamrolle },
    arb.kommunikation && { label: 'Kommunikation', wert: arb.kommunikation },
    fmt(arb.staerken) && { label: 'Stärken', wert: fmt(arb.staerken) },
    fmt(arb.entwicklungsbereiche) && { label: 'Entwicklungsbereiche', wert: fmt(arb.entwicklungsbereiche) },
  ].filter(Boolean)
  if (arbFelder.length) sections.push({ titel: 'Arbeitsstil', felder: arbFelder })

  // Berufserfahrung
  const ber = p.berufserfahrung || {}
  const berFelder = [
    ber.aktuelle_position && { label: 'Aktuelle Position', wert: ber.aktuelle_position },
    ber.aktueller_arbeitgeber && { label: 'Arbeitgeber', wert: ber.aktueller_arbeitgeber },
    ber.branche && { label: 'Branche', wert: ber.branche },
    ber.erfahrungsjahre && { label: 'Erfahrungsjahre', wert: String(ber.erfahrungsjahre) },
    ber.fuehrungserfahrung && { label: 'Führungserfahrung', wert: ber.fuehrungserfahrung },
    fmt(ber.highlights) && { label: 'Highlights', wert: fmt(ber.highlights) },
  ].filter(Boolean)
  if (berFelder.length) sections.push({ titel: 'Berufserfahrung', felder: berFelder })

  // Qualifikationen
  const qual = p.qualifikationen || {}
  const qualFelder = [
    qual.ausbildung && { label: 'Ausbildung', wert: qual.ausbildung },
    fmt(qual.zertifikate) && { label: 'Zertifikate', wert: fmt(qual.zertifikate) },
    fmt(qual.sprachen) && { label: 'Sprachen', wert: fmt(qual.sprachen) },
    fmt(qual.top_skills) && { label: 'Top-Skills', wert: fmt(qual.top_skills) },
  ].filter(Boolean)
  if (qualFelder.length) sections.push({ titel: 'Qualifikationen', felder: qualFelder })

  // Gehaltsvorstellung
  const geh = p.gehaltsvorstellung || {}
  const gehFelder = [
    geh.wunsch && { label: 'Wunschgehalt', wert: `${geh.wunsch} EUR` },
    geh.minimum && { label: 'Minimum', wert: `${geh.minimum} EUR` },
    geh.verhandelbar != null && { label: 'Verhandelbar', wert: geh.verhandelbar ? 'Ja' : 'Nein' },
    fmt(geh.benefits_wichtig) && { label: 'Wichtige Benefits', wert: fmt(geh.benefits_wichtig) },
  ].filter(Boolean)
  if (gehFelder.length) sections.push({ titel: 'Gehaltsvorstellung', felder: gehFelder })

  // Persönlichkeit
  const pers = p.persoenlichkeit || {}
  const persFelder = [
    pers.selbstbeschreibung && { label: 'Selbstbeschreibung', wert: pers.selbstbeschreibung },
    fmt(pers.hobbys_relevant) && { label: 'Relevante Hobbys', wert: fmt(pers.hobbys_relevant) },
    pers.fun_fact && { label: 'Fun Fact', wert: pers.fun_fact },
  ].filter(Boolean)
  if (persFelder.length) sections.push({ titel: 'Persönlichkeit', felder: persFelder })

  // Persönliche Daten
  const pd = p.persoenliche_daten || {}
  const pdFelder = [
    pd.name && { label: 'Name', wert: pd.name },
    pd.standort && { label: 'Standort', wert: pd.standort },
    pd.verfuegbar_ab && { label: 'Verfügbar ab', wert: pd.verfuegbar_ab },
    pd.kuendigungsfrist && { label: 'Kündigungsfrist', wert: pd.kuendigungsfrist },
    fmt(pd.wunsch_standorte) && { label: 'Wunschstandorte', wert: fmt(pd.wunsch_standorte) },
  ].filter(Boolean)
  if (pdFelder.length) sections.push({ titel: 'Persönliche Daten', felder: pdFelder })

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
        <h1>Persönlichkeitsprofil</h1>
        <p class="page-subtitle">
          Dein Profil hilft uns, Bewerbungen individuell auf dich zuzuschneiden.
        </p>
      </section>

      <!-- Completeness bar -->
      <section class="completeness-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="completeness-card zen-card">
          <div class="completeness-info">
            <span class="completeness-label">Vollständigkeit</span>
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
      :session-typ="sessionTyp"
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
