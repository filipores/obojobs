<template>
  <div class="legal-page">
    <div class="container container-md">
      <!-- Header -->
      <section class="page-header animate-fade-up">
        <router-link to="/" class="back-link">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Zurück zur Startseite
        </router-link>
        <h1>404 - Seite nicht gefunden</h1>
      </section>

      <!-- Content -->
      <section class="legal-content zen-card animate-fade-up" style="animation-delay: 100ms;">
        <div class="legal-section">
          <div style="text-align: center; padding: 2rem 0;">
            <div style="font-size: 6rem; color: var(--color-sumi-faded, #6B6B6B); margin-bottom: 1rem;">404</div>
            <h2>Diese Seite existiert nicht</h2>
            <p>
              Die angeforderte Seite konnte leider nicht gefunden werden.
              Möglicherweise wurde sie verschoben oder der Link ist fehlerhaft.
            </p>

            <div style="margin-top: 2rem;">
              <router-link to="/" class="btn btn-outline btn-lg" style="margin-right: 1rem;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-right: 0.5rem;">
                  <path d="M3 9L12 2l9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                  <polyline points="9,22 9,12 15,12 15,22"/>
                </svg>
                Zur Startseite
              </router-link>

              <button @click="goBack" class="btn btn-outline btn-lg">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-right: 0.5rem;">
                  <path d="M19 12H5M12 19l-7-7 7-7"/>
                </svg>
                Zurück
              </button>
            </div>
          </div>
        </div>

        <div class="ink-stroke"></div>

        <div class="legal-section">
          <h3>Hilfreiche Links</h3>
          <ul style="list-style: none; padding: 0;">
            <li style="margin-bottom: 0.5rem;">
              <router-link to="/applications" class="text-link">→ Bewerbungen</router-link>
            </li>
            <li style="margin-bottom: 0.5rem;">
              <router-link to="/documents" class="text-link">→ Dokumente</router-link>
            </li>
            <li style="margin-bottom: 0.5rem;">
              <router-link to="/templates" class="text-link">→ Vorlagen</router-link>
            </li>
            <li style="margin-bottom: 0.5rem;">
              <router-link to="/settings" class="text-link">→ Einstellungen</router-link>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  // Go back in history if possible, otherwise go to home
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}
</script>