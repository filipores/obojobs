<template>
  <div class="landing-page">
    <!-- Post-Registration CV Upload Flow -->
    <section v-if="showCvUploadFlow" class="cv-upload-section">
      <div class="cv-upload-container">
        <!-- Brand Mark -->
        <div class="hero-brand animate-fade-up">
          <div class="brand-enso"></div>
          <span class="brand-name">obo</span>
        </div>

        <!-- CV Upload State -->
        <div v-if="flowState === 'upload'" class="cv-upload-content animate-fade-up">
          <h1 class="cv-upload-title">Fast geschafft!</h1>
          <p class="cv-upload-subtitle">Lade deinen Lebenslauf hoch.</p>

          <!-- Drop Zone -->
          <div
            class="cv-drop-zone"
            :class="{ 'is-dragging': isDragging, 'has-file': selectedFile, 'is-uploading': isUploading }"
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".pdf"
              class="file-input"
              @change="onFileSelect"
            />

            <div v-if="!selectedFile" class="drop-zone-content">
              <div class="drop-zone-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <p class="drop-zone-text">
                <strong>PDF hier ablegen</strong> oder <button type="button" @click="triggerFileSelect" class="drop-zone-link">Datei auswahlen</button>
              </p>
            </div>

            <div v-else class="selected-file-info">
              <div class="file-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <span class="file-name">{{ selectedFile.name }}</span>
              <button type="button" @click="clearFile" class="clear-file-btn" aria-label="Datei entfernen">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>

          <p class="cv-upload-hint">Wir extrahieren automatisch deine Skills.</p>

          <!-- Upload Button -->
          <button
            v-if="selectedFile"
            @click="uploadCvAndRegenerate"
            :disabled="isUploading"
            class="zen-btn zen-btn-ai zen-btn-lg cv-upload-btn"
          >
            <span v-if="!isUploading">Hochladen und Bewerbung erstellen</span>
            <span v-else>Wird hochgeladen...</span>
          </button>

          <!-- Error Message -->
          <div v-if="uploadError" class="cv-upload-error">
            {{ uploadError }}
          </div>

          <!-- Skip Link -->
          <button @click="skipToDashboard" class="skip-link">
            Spater hochladen
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
        </div>

        <!-- Crafting State -->
        <div v-else-if="flowState === 'crafting'" class="crafting-content animate-fade-up">
          <div class="crafting-animation">
            <div class="loading-enso">
              <svg class="enso-circle" viewBox="0 0 100 100">
                <circle
                  class="enso-path"
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke-width="3"
                  stroke-linecap="round"
                />
              </svg>
            </div>
          </div>
          <h2 class="crafting-title">Erstelle dein Anschreiben...</h2>
          <p class="crafting-subtitle">{{ craftingText }}</p>
          <p v-if="demoStore.demoResult?.data?.firma" class="crafting-job">
            fur {{ demoStore.demoResult.data.firma }}
          </p>
        </div>

        <!-- Result State -->
        <div v-else-if="flowState === 'result'" class="result-content animate-fade-up">
          <div class="result-success-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <h2 class="result-title">Dein personalisiertes Anschreiben</h2>
          <p v-if="regeneratedResult?.firma" class="result-job">
            fur {{ regeneratedResult.firma }} - {{ regeneratedResult.position }}
          </p>

          <!-- Application Preview -->
          <div class="result-preview">
            <div class="preview-header">
              <span class="preview-label">Anschreiben</span>
            </div>
            <div class="preview-content">
              {{ regeneratedResult?.anschreiben || 'Dein personalisiertes Anschreiben wurde erstellt.' }}
            </div>
          </div>

          <!-- Usage Info -->
          <div v-if="usageInfo" class="usage-info">
            <span class="usage-remaining">
              Noch {{ usageInfo.remaining }} von {{ usageInfo.limit }} Bewerbungen diesen Monat ubrig
            </span>
          </div>

          <!-- Actions -->
          <div class="result-actions">
            <button @click="downloadPdf" class="zen-btn zen-btn-ai zen-btn-lg">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              PDF herunterladen
            </button>
            <router-link to="/dashboard" class="zen-btn dashboard-btn">
              Zum Dashboard
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </router-link>
          </div>
        </div>

        <!-- Decorative Enso -->
        <div class="hero-enso-bg"></div>
      </div>
    </section>

    <!-- NEW: Crafting Screen (shows animation while API runs) -->
    <DemoCraftingScreen
      :isActive="showCraftingScreen"
      :data="craftingData"
      :pdfBlob="pdfBlob"
      @register="onCraftingRegister"
    />

    <!-- Normal Landing Page (when not in CV upload flow) -->
    <template v-if="!showCvUploadFlow">
      <!-- CV Upload Modal -->
      <CVUploadModal
        :visible="showCvModal"
        @close="showCvModal = false"
        @submit="onCvSubmitted"
      />

      <!-- Hero Section - The product IS the hero -->
      <section class="hero-section">
        <div class="hero-container">
          <!-- Brand Mark -->
          <div class="hero-brand animate-fade-up">
            <div class="brand-enso"></div>
            <span class="brand-name">obo</span>
          </div>

          <!-- Hero Content -->
          <div class="hero-content animate-fade-up" style="animation-delay: 100ms;">
            <h1 class="hero-title">Bewerbungen, die sich selbst schreiben.</h1>
            <p class="hero-subtitle">
              Paste die URL einer Stellenanzeige. Erhalte in Sekunden ein personalisiertes Anschreiben.
            </p>
          </div>

          <!-- Demo Generator - The core experience -->
          <div class="demo-input-section animate-fade-up" style="animation-delay: 200ms;">
            <DemoGenerator
              ref="demoGeneratorRef"
              @demo-started="onDemoStarted"
              @demo-complete="onDemoComplete"
              @request-cv="onRequestCv"
            />

            <!-- Supported Sites -->
            <div class="supported-sites">
              <span class="supported-label">Unterstutzte Portale:</span>
              <div class="site-badges">
                <span class="site-badge">Indeed</span>
                <span class="site-badge">StepStone</span>
                <span class="site-badge">XING</span>
                <span class="site-badge site-badge-more">+50 weitere</span>
              </div>
            </div>
          </div>

          <!-- Decorative Enso -->
          <div class="hero-enso-bg"></div>
        </div>
      </section>

      <!-- How It Works - Below the fold -->
      <section class="how-it-works-section">
        <div class="container">
          <div class="section-header animate-fade-up">
            <span class="section-label">So funktioniert's</span>
            <h2 class="section-title">Drei Schritte zum perfekten Anschreiben</h2>
          </div>

          <div class="steps-grid">
            <div class="step-card animate-fade-up" style="animation-delay: 100ms;">
              <div class="step-number">1</div>
              <div class="step-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
              </div>
              <h3>URL einfugen</h3>
              <p>Kopiere die URL der Stellenanzeige von Indeed, StepStone oder anderen Jobportalen.</p>
            </div>

            <div class="step-card animate-fade-up" style="animation-delay: 200ms;">
              <div class="step-number">2</div>
              <div class="step-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
              </div>
              <h3>KI analysiert</h3>
              <p>Unsere KI extrahiert die Anforderungen und erstellt ein massgeschneidertes Anschreiben.</p>
            </div>

            <div class="step-card animate-fade-up" style="animation-delay: 300ms;">
              <div class="step-number">3</div>
              <div class="step-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <h3>Anschreiben erhalten</h3>
              <p>Bearbeite, exportiere als PDF und bewirb dich - alles in unter einer Minute.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Social Proof -->
      <section class="social-proof-section">
        <div class="container">
          <div class="proof-content animate-fade-up">
            <div class="proof-stats">
              <div class="proof-stat">
                <span class="stat-value">5.000+</span>
                <span class="stat-label">Anschreiben generiert</span>
              </div>
              <div class="proof-divider"></div>
              <div class="proof-stat">
                <span class="stat-value">4.8</span>
                <span class="stat-label">Durchschnittliche Bewertung</span>
              </div>
              <div class="proof-divider"></div>
              <div class="proof-stat">
                <span class="stat-value">&lt; 30s</span>
                <span class="stat-label">Durchschnittliche Zeit</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Pricing Preview -->
      <section class="pricing-section">
        <div class="container">
          <div class="section-header animate-fade-up">
            <span class="section-label">Preise</span>
            <h2 class="section-title">Starte kostenlos</h2>
          </div>

          <div class="pricing-grid">
            <div class="pricing-card animate-fade-up" style="animation-delay: 100ms;">
              <div class="pricing-header">
                <h3>Free</h3>
                <div class="pricing-price">
                  <span class="price-amount">0</span>
                  <span class="price-currency">EUR</span>
                  <span class="price-period">/Monat</span>
                </div>
              </div>
              <ul class="pricing-features">
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  3 Anschreiben pro Monat
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Basis-Vorlagen
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  PDF-Export
                </li>
              </ul>
              <router-link to="/register" class="pricing-cta zen-btn">
                Kostenlos starten
              </router-link>
            </div>

            <div class="pricing-card pricing-card-featured animate-fade-up" style="animation-delay: 200ms;">
              <div class="pricing-badge">Beliebt</div>
              <div class="pricing-header">
                <h3>Pro</h3>
                <div class="pricing-price">
                  <span class="price-amount">9</span>
                  <span class="price-currency">EUR</span>
                  <span class="price-period">/Monat</span>
                </div>
              </div>
              <ul class="pricing-features">
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Unbegrenzte Anschreiben
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Alle Premium-Vorlagen
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Job-Fit Score
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Interview-Vorbereitung
                </li>
              </ul>
              <router-link to="/register?plan=pro" class="pricing-cta zen-btn zen-btn-ai">
                Pro wahlen
              </router-link>
            </div>
          </div>
        </div>
      </section>

      <!-- Final CTA -->
      <section class="final-cta-section">
        <div class="container">
          <div class="cta-content animate-fade-up">
            <h2>Bereit fur deine nachste Bewerbung?</h2>
            <p>Probiere es jetzt aus - kostenlos und ohne Anmeldung.</p>
            <button @click="scrollToTop" class="zen-btn zen-btn-ai zen-btn-lg">
              Jetzt Anschreiben erstellen
            </button>
          </div>
        </div>
      </section>

      <!-- Footer Links -->
      <footer class="landing-footer">
        <div class="container">
          <div class="footer-content">
            <div class="footer-brand">
              <div class="footer-enso"></div>
              <span>obo</span>
            </div>
            <div class="footer-links">
              <router-link to="/login">{{ $t('auth.login') }}</router-link>
              <router-link to="/register">{{ $t('auth.register') }}</router-link>
              <router-link to="/impressum">{{ $t('pages.impressum') }}</router-link>
              <router-link to="/datenschutz">{{ $t('pages.datenschutz') }}</router-link>
            </div>
            <div class="footer-copyright">
              &copy; {{ currentYear }} obo
            </div>
          </div>
        </div>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import DemoGenerator from '../components/landing/DemoGenerator.vue'
import CVUploadModal from '../components/landing/CVUploadModal.vue'
import DemoCraftingScreen from '../components/landing/DemoCraftingScreen.vue'
import { demoStore } from '../stores/demo'
import { authStore } from '../stores/auth'
import api from '../api/client'

const router = useRouter()
const route = useRoute()
const currentYear = computed(() => new Date().getFullYear())

// Demo Generator ref
const demoGeneratorRef = ref(null)

// CV Upload Flow State (post-registration)
const flowState = ref('upload') // 'upload' | 'crafting' | 'result'
const selectedFile = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadError = ref('')
const fileInput = ref(null)
const craftingText = ref('Analysiere deinen Lebenslauf...')
const regeneratedResult = ref(null)
const usageInfo = ref(null)
const createdApplicationId = ref(null)

// NEW: Demo flow state (pre-registration)
const showCvModal = ref(false)
const pendingJobUrl = ref('')
const previewData = ref(null)
const isGenerating = ref(false)

// NEW: Crafting screen state
const showCraftingScreen = ref(false)
const craftingData = ref(null)
const pdfBlob = ref(null)

// Show CV upload flow when user is authenticated and in demo flow
const showCvUploadFlow = computed(() => {
  return authStore.isAuthenticated() && demoStore.isInDemoFlow()
})

// File handling
const triggerFileSelect = () => {
  fileInput.value?.click()
}

const onFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file && file.type === 'application/pdf') {
    selectedFile.value = file
    uploadError.value = ''
  } else if (file) {
    uploadError.value = 'Bitte wahle eine PDF-Datei aus.'
  }
}

const onDragOver = () => {
  isDragging.value = true
}

const onDragLeave = () => {
  isDragging.value = false
}

const onDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file && file.type === 'application/pdf') {
    selectedFile.value = file
    uploadError.value = ''
  } else if (file) {
    uploadError.value = 'Bitte wahle eine PDF-Datei aus.'
  }
}

const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Upload CV and regenerate application
const uploadCvAndRegenerate = async () => {
  if (!selectedFile.value || isUploading.value) return

  isUploading.value = true
  uploadError.value = ''

  try {
    // Step 1: Upload CV
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('doc_type', 'lebenslauf')

    await api.post('/documents', formData)

    // Step 2: Show crafting animation
    flowState.value = 'crafting'

    // Animate crafting text
    const craftingTexts = [
      'Analysiere deinen Lebenslauf...',
      'Extrahiere deine Skills...',
      'Erstelle personalisiertes Anschreiben...'
    ]
    let textIndex = 0
    const textInterval = setInterval(() => {
      textIndex = (textIndex + 1) % craftingTexts.length
      craftingText.value = craftingTexts[textIndex]
    }, 2000)

    // Step 3: Generate application with real CV
    try {
      const response = await api.post('/applications/generate-from-url', {
        url: demoStore.jobUrl
      })

      clearInterval(textInterval)

      if (response.data.success) {
        regeneratedResult.value = response.data.data
        createdApplicationId.value = response.data.data?.id

        // Get usage info
        try {
          const statsResponse = await api.silent.get('/stats')
          usageInfo.value = statsResponse.data.usage
        } catch {
          // Ignore usage fetch errors
        }

        // Store in demo store for reference
        demoStore.setRegeneratedResult(response.data.data)

        flowState.value = 'result'
      } else {
        throw new Error(response.data.message || 'Generierung fehlgeschlagen')
      }
    } catch (genError) {
      clearInterval(textInterval)
      flowState.value = 'upload'
      uploadError.value = genError.response?.data?.error || 'Anschreiben konnte nicht erstellt werden. Bitte versuche es erneut.'
    }
  } catch (error) {
    uploadError.value = error.response?.data?.error || 'Upload fehlgeschlagen. Bitte versuche es erneut.'
  } finally {
    isUploading.value = false
  }
}

// Skip CV upload and go to dashboard
const skipToDashboard = () => {
  demoStore.clear()
  router.push('/dashboard')
}

// Download PDF
const downloadPdf = async () => {
  if (!createdApplicationId.value) {
    // Fallback: go to dashboard
    router.push('/dashboard')
    return
  }

  try {
    const response = await api.get(`/applications/${createdApplicationId.value}/pdf`, {
      responseType: 'blob'
    })

    // Create download link
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Anschreiben_${regeneratedResult.value?.firma || 'Bewerbung'}.pdf`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (error) {
    console.error('PDF download failed:', error)
    // On error, redirect to application details
    router.push(`/applications`)
  }
}

// NEW: Handle CV upload request from DemoGenerator
const onRequestCv = (url) => {
  pendingJobUrl.value = url
  showCvModal.value = true
}

// NEW: Handle CV file submission from modal
const onCvSubmitted = async (cvFile) => {
  showCvModal.value = false
  showCraftingScreen.value = true  // Show immediately
  isGenerating.value = true

  // Prepare crafting data from demoStore or default
  craftingData.value = {
    ansprechpartner: demoStore.previewData?.ansprechpartner || 'Personalabteilung',
    firma: demoStore.previewData?.firma || 'Unternehmen',
    position: demoStore.previewData?.position || 'Position',
    einleitung: ''  // Will be filled by API
  }

  // API call runs parallel to animation
  if (demoGeneratorRef.value) {
    demoGeneratorRef.value.generateWithCV(cvFile)
  }
}

// Demo flow handlers
const onDemoStarted = () => {
  // Track demo start for analytics
  isGenerating.value = true
}

const onDemoComplete = (result) => {
  isGenerating.value = false

  // If we have valid result data, update crafting data with real results
  if (result.result?.data) {
    // Update crafting data with real results
    craftingData.value = {
      ...craftingData.value,
      ansprechpartner: result.result.data.ansprechpartner,
      firma: result.result.data.firma,
      position: result.result.data.position,
      einleitung: result.result.data.einleitung
    }

    // Store preview data for later use
    previewData.value = result.result.data

    // Store CV text for post-registration use
    if (result.result.data.cv_text) {
      demoStore.setCvData(result.result.data.cv_text, null)
    }
    demoStore.setPreviewData(result.result.data)

    // If crafting screen is not shown, show it now (fallback for non-CV flow)
    if (!showCraftingScreen.value) {
      showCraftingScreen.value = true
    }
  } else {
    // Fallback: redirect to register directly
    showCraftingScreen.value = false
    demoStore.setDemoComplete(result.url, result)
    router.push({
      path: '/register',
      query: { demo: 'complete' }
    })
  }
}

// NEW: Handle register click from crafting screen
const onCraftingRegister = () => {
  showCraftingScreen.value = false
  // Store demo data before redirecting
  demoStore.setDemoComplete(pendingJobUrl.value, { data: previewData.value })
  // Navigate to registration
  router.push('/register')
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Check on mount if we should show CV upload flow
onMounted(() => {
  // If user is authenticated and came from demo flow, show CV upload
  if (route.query.demo === 'complete' && authStore.isAuthenticated()) {
    // User just registered after demo - stay in CV upload flow
    // demoStore should already have the data
  } else if (!authStore.isAuthenticated() && demoStore.isInDemoFlow()) {
    // User is not authenticated but has demo data - they probably logged out
    // Clear the demo state to show normal landing
    demoStore.clear()
  }
})
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: var(--color-washi);
}

/* ========================================
   CV UPLOAD SECTION
   ======================================== */
.cv-upload-section {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma-xl) var(--space-ma);
  position: relative;
  overflow: hidden;
}

.cv-upload-container {
  max-width: 560px;
  width: 100%;
  text-align: center;
  position: relative;
  z-index: 1;
}

.cv-upload-content,
.crafting-content,
.result-content {
  margin-top: var(--space-ma-lg);
}

.cv-upload-title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.cv-upload-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-ma);
}

/* Drop Zone */
.cv-drop-zone {
  border: 2px dashed var(--color-sand);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  transition: all var(--transition-base);
  background: var(--color-washi);
  cursor: pointer;
  margin-bottom: var(--space-lg);
}

.cv-drop-zone:hover,
.cv-drop-zone.is-dragging {
  border-color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.cv-drop-zone.has-file {
  border-style: solid;
  border-color: var(--color-koke);
  background: rgba(122, 139, 110, 0.05);
}

.cv-drop-zone.is-uploading {
  opacity: 0.6;
  pointer-events: none;
}

.file-input {
  display: none;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
}

.drop-zone-icon {
  color: var(--color-stone);
  opacity: 0.6;
}

.drop-zone-text {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.drop-zone-text strong {
  color: var(--color-sumi);
}

.drop-zone-link {
  background: none;
  border: none;
  color: var(--color-ai);
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.selected-file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.file-icon {
  color: var(--color-koke);
}

.file-name {
  font-weight: 500;
  color: var(--color-sumi);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clear-file-btn {
  background: none;
  border: none;
  padding: var(--space-xs);
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.clear-file-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-error);
}

.cv-upload-hint {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-lg);
}

.cv-upload-btn {
  width: 100%;
  margin-bottom: var(--space-md);
}

.cv-upload-error {
  padding: var(--space-md);
  background: var(--color-error-light);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: 0.875rem;
  margin-bottom: var(--space-md);
}

.skip-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
  cursor: pointer;
  transition: color var(--transition-base);
}

.skip-link:hover {
  color: var(--color-ai);
}

/* Crafting State */
.crafting-content {
  padding: var(--space-xl) 0;
}

.crafting-animation {
  margin-bottom: var(--space-xl);
}

.loading-enso {
  width: 100px;
  height: 100px;
  margin: 0 auto;
}

.enso-circle {
  width: 100%;
  height: 100%;
}

.enso-path {
  stroke: var(--color-ai);
  stroke-dasharray: 283;
  stroke-dashoffset: 283;
  animation: draw-enso 2s var(--ease-zen) forwards, pulse-opacity 2s ease-in-out infinite 2s;
}

@keyframes draw-enso {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes pulse-opacity {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.crafting-title {
  font-size: 1.5rem;
  font-weight: 400;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.crafting-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.crafting-job {
  font-size: 0.9375rem;
  color: var(--color-ai);
  font-weight: 500;
}

/* Result State */
.result-content {
  text-align: center;
}

.result-success-icon {
  color: var(--color-koke);
  margin-bottom: var(--space-lg);
}

.result-title {
  font-size: 1.75rem;
  font-weight: 400;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.result-job {
  font-size: 1rem;
  color: var(--color-ai);
  font-weight: 500;
  margin-bottom: var(--space-lg);
}

.result-preview {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  text-align: left;
  margin-bottom: var(--space-lg);
  overflow: hidden;
}

.preview-header {
  padding: var(--space-sm) var(--space-md);
  background: var(--color-washi-warm);
  border-bottom: 1px solid var(--color-border-light);
}

.preview-label {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
}

.preview-content {
  padding: var(--space-lg);
  font-size: 0.9375rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.usage-info {
  margin-bottom: var(--space-lg);
}

.usage-remaining {
  display: inline-block;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  color: var(--color-ai);
  font-weight: 500;
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.dashboard-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
}

/* ========================================
   HERO SECTION
   ======================================== */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma-xl) var(--space-ma);
  overflow: hidden;
}

.hero-container {
  max-width: var(--container-md);
  width: 100%;
  text-align: center;
  position: relative;
  z-index: 1;
}

.hero-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-ma-lg);
}

.brand-enso {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2.5px solid var(--color-sumi);
  border-width: 2.5px 3px 2.5px 2.5px;
  opacity: 0.8;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 500;
  color: var(--color-sumi);
  letter-spacing: -0.02em;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 400;
  line-height: 1.1;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-lg);
  color: var(--color-sumi);
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin: 0 auto var(--space-ma-lg);
  line-height: var(--leading-relaxed);
}

.hero-enso-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 600px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  border-width: 2px 3px 2px 2.5px;
  opacity: 0.02;
  pointer-events: none;
}

/* Demo Input Section */
.demo-input-section {
  max-width: 600px;
  margin: 0 auto;
}

.supported-sites {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}

.supported-label {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.site-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.site-badge {
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.site-badge-more {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

/* ========================================
   HOW IT WORKS SECTION
   ======================================== */
.how-it-works-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-ma-lg);
}

.section-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-ai);
  margin-bottom: var(--space-sm);
}

.section-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 400;
  color: var(--color-sumi);
  margin-bottom: 0;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.step-card {
  text-align: center;
  padding: var(--space-xl);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  position: relative;
}

.step-number {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  color: var(--color-text-inverse);
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 600;
}

.step-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-lg);
  color: var(--color-ai);
}

.step-card h3 {
  font-size: 1.125rem;
  margin-bottom: var(--space-sm);
}

.step-card p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

/* ========================================
   SOCIAL PROOF SECTION
   ======================================== */
.social-proof-section {
  padding: var(--space-ma-lg) 0;
  background: var(--color-washi);
}

.proof-content {
  max-width: var(--container-lg);
  margin: 0 auto;
}

.proof-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xl);
}

.proof-stat {
  text-align: center;
}

.proof-stat .stat-value {
  display: block;
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 500;
  color: var(--color-ai);
  line-height: 1;
  margin-bottom: var(--space-xs);
}

.proof-stat .stat-label {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.proof-divider {
  width: 1px;
  height: 48px;
  background: var(--color-border);
}

/* ========================================
   PRICING SECTION
   ======================================== */
.pricing-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-xl);
  max-width: 800px;
  margin: 0 auto;
}

.pricing-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-light);
  padding: var(--space-xl);
  position: relative;
  transition: all var(--transition-base);
}

.pricing-card:hover {
  box-shadow: var(--shadow-lifted);
  transform: translateY(-4px);
}

.pricing-card-featured {
  border-color: var(--color-ai);
  background: linear-gradient(135deg, var(--color-bg-elevated) 0%, var(--color-ai-subtle) 100%);
}

.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.pricing-header {
  text-align: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.pricing-header h3 {
  font-size: 1.25rem;
  margin-bottom: var(--space-sm);
}

.pricing-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--space-xs);
}

.price-amount {
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: 500;
  color: var(--color-sumi);
  line-height: 1;
}

.price-currency {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
}

.price-period {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.pricing-features {
  list-style: none;
  margin-bottom: var(--space-xl);
}

.pricing-features li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.pricing-features svg {
  color: var(--color-koke);
  flex-shrink: 0;
}

.pricing-cta {
  width: 100%;
  justify-content: center;
}

/* ========================================
   FINAL CTA SECTION
   ======================================== */
.final-cta-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-ai);
  text-align: center;
}

.cta-content h2 {
  font-size: clamp(1.5rem, 4vw, 2rem);
  color: var(--color-text-inverse);
  margin-bottom: var(--space-md);
}

.cta-content p {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--space-lg);
}

.cta-content .zen-btn {
  background: var(--color-washi);
  color: var(--color-ai);
}

.cta-content .zen-btn:hover {
  background: var(--color-washi-cream);
}

/* ========================================
   FOOTER
   ======================================== */
.landing-footer {
  padding: var(--space-xl) 0;
  background: var(--color-washi-warm);
  border-top: 1px solid var(--color-border-light);
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-size: 1.125rem;
  color: var(--color-text-tertiary);
}

.footer-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1.5px solid var(--color-text-ghost);
  opacity: 0.6;
}

.footer-links {
  display: flex;
  gap: var(--space-lg);
}

.footer-links a {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  transition: color var(--transition-base);
}

.footer-links a:hover {
  color: var(--color-ai);
}

.footer-copyright {
  font-size: 0.8125rem;
  color: var(--color-text-ghost);
}

/* ========================================
   CONTAINER
   ======================================== */
.container {
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: 0 var(--space-ma);
}

/* ========================================
   ANIMATIONS
   ======================================== */
.animate-fade-up {
  animation: fadeUp 0.6s var(--ease-zen) both;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 1024px) {
  .steps-grid {
    grid-template-columns: 1fr;
    max-width: 500px;
  }
}

@media (max-width: 768px) {
  .hero-section,
  .cv-upload-section {
    padding: var(--space-ma-lg) var(--space-md);
    min-height: auto;
    padding-top: var(--space-ma-xl);
    padding-bottom: var(--space-ma-xl);
  }

  .hero-title,
  .cv-upload-title {
    font-size: clamp(2rem, 8vw, 2.5rem);
  }

  .hero-subtitle {
    font-size: 1.125rem;
  }

  .proof-stats {
    flex-direction: column;
    gap: var(--space-lg);
  }

  .proof-divider {
    width: 48px;
    height: 1px;
  }

  .pricing-grid {
    grid-template-columns: 1fr;
  }

  .footer-content {
    flex-direction: column;
    text-align: center;
  }

  .footer-links {
    flex-wrap: wrap;
    justify-content: center;
  }

  .result-actions {
    gap: var(--space-sm);
  }
}

@media (max-width: 480px) {
  .supported-sites {
    flex-direction: column;
  }

  .site-badges {
    justify-content: center;
  }
}
</style>
