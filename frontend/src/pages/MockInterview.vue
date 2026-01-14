<template>
  <div class="mock-interview-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <div class="page-header-content">
          <router-link :to="`/applications/${applicationId}/interview`" class="back-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Zurueck zur Interview-Vorbereitung
          </router-link>
          <div class="header-main">
            <div>
              <h1>Mock-Interview</h1>
              <p class="page-subtitle">Ueben Sie Ihre Interview-Antworten</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Coming Soon -->
      <section class="coming-soon-section">
        <div class="coming-soon-card zen-card">
          <div class="coming-soon-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <h2>Demnachst verfuegbar</h2>
          <p>Das interaktive Mock-Interview Feature wird in Kuerze implementiert.</p>
          <p class="feature-preview">Geplante Funktionen:</p>
          <ul>
            <li>Interaktives Frage-Antwort Training</li>
            <li>KI-Feedback zu Ihren Antworten</li>
            <li>STAR-Methode Analyse</li>
            <li>Fortschrittsanzeige und Zusammenfassung</li>
          </ul>
          <router-link :to="`/applications/${applicationId}/interview`" class="zen-btn zen-btn-ai">
            Zurueck zur Interview-Vorbereitung
          </router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const applicationId = computed(() => route.params.id)
</script>

<style scoped>
.mock-interview-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

.page-header {
  padding: var(--space-ma-lg) 0 var(--space-ma);
}

.page-header-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color 0.2s var(--ease-zen);
}

.back-link:hover {
  color: var(--color-ai);
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
}

.page-header h1 {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
}

.page-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0;
}

.coming-soon-section {
  display: flex;
  justify-content: center;
  padding: var(--space-ma-xl) 0;
}

.coming-soon-card {
  max-width: 500px;
  text-align: center;
  padding: var(--space-xl);
}

.coming-soon-icon {
  margin-bottom: var(--space-lg);
  color: var(--color-ai);
}

.coming-soon-card h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
}

.coming-soon-card p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-md);
}

.feature-preview {
  font-weight: 600;
  color: var(--color-sumi);
}

.coming-soon-card ul {
  text-align: left;
  margin: 0 auto var(--space-xl);
  padding-left: var(--space-lg);
  color: var(--color-text-secondary);
  list-style-type: none;
}

.coming-soon-card ul li {
  position: relative;
  padding-left: var(--space-md);
  margin-bottom: var(--space-sm);
}

.coming-soon-card ul li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 8px;
  width: 6px;
  height: 6px;
  background: var(--color-ai);
  border-radius: 50%;
}
</style>
