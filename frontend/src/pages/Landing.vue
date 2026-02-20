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
                <strong>PDF hier ablegen</strong> oder <button type="button" @click="triggerFileSelect" class="drop-zone-link">Datei auswählen</button>
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
            Später hochladen
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
            für {{ demoStore.demoResult.data.firma }}
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
            für {{ regeneratedResult.firma }} - {{ regeneratedResult.position }}
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
              Noch {{ usageInfo.remaining }} von {{ usageInfo.limit }} Bewerbungen diesen Monat übrig
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

    <!-- CraftingOverlay (shows 5-phase animation while API runs) -->
    <CraftingOverlay
      :isActive="showCraftingScreen"
      :companyName="craftingData?.firma || ''"
      :jobTitle="craftingData?.position || ''"
      :jobDescription="craftingData?.einleitung || ''"
      :contactPerson="craftingData?.ansprechpartner || ''"
      @complete="onCraftingComplete"
    />

    <!-- Demo Result Overlay (3-phase reveal) -->
    <Teleport to="body">
      <Transition name="demo-result">
        <div v-if="showDemoResult" class="demo-reveal-overlay" @click="showDemoResult = false">
          <div class="demo-reveal-modal" role="dialog" aria-modal="true" @click.stop>
            <!-- Close button -->
            <button @click="showDemoResult = false" class="demo-reveal-close" aria-label="Schließen">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>

            <!-- Phase 1: Enso Circle -->
            <div class="demo-reveal-enso" :class="{ 'demo-reveal-enso--visible': revealPhase >= 1 }">
              <EnsoCircle state="complete" size="lg" :duration="600" />
            </div>

            <!-- Phase 2: Content reveal -->
            <div class="demo-reveal-content" :class="{ 'demo-reveal-content--visible': revealPhase >= 2 }">
              <div class="demo-reveal-header">
                <h2 class="demo-reveal-title">Bewerbung erstellt</h2>
                <p v-if="demoResultData?.firma" class="demo-reveal-company">
                  {{ demoResultData.position }} bei <strong>{{ demoResultData.firma }}</strong>
                </p>
              </div>

              <!-- Peek card for intro preview -->
              <div
                v-if="einleitungPreview"
                class="demo-reveal-peek"
                :class="{ 'demo-reveal-peek--expanded': peekExpanded }"
                @mouseenter="peekExpanded = true"
                @mouseleave="peekExpanded = false"
                @click="peekExpanded = !peekExpanded"
              >
                <div class="demo-reveal-peek-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <span class="demo-reveal-peek-label">Vorschau</span>
                  <svg class="demo-reveal-peek-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </div>
                <div class="demo-reveal-peek-body">
                  <p class="demo-reveal-peek-text">{{ einleitungPreview }}</p>
                </div>
              </div>
            </div>

            <!-- Phase 3: Action buttons -->
            <div class="demo-reveal-actions" :class="{ 'demo-reveal-actions--visible': revealPhase >= 3 }">
              <div class="demo-reveal-buttons">
                <button @click="downloadDemoPdf" class="zen-btn zen-btn-ai demo-reveal-btn-primary">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  {{ demoResultData?.pdf_base64 ? 'PDF herunterladen' : 'Kostenlos registrieren' }}
                </button>
                <button @click="showDemoResult = false" class="zen-btn demo-reveal-btn-secondary">
                  Zurück zur Startseite
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Registration Nudge Modal -->
    <Teleport to="body">
      <Transition name="nudge-modal">
        <div v-if="showRegistrationNudge" class="nudge-overlay" @click="dismissNudge">
          <div class="nudge-modal" @click.stop>
            <div class="nudge-enso">
              <EnsoCircle state="breathing" size="md" />
            </div>

            <h2 class="nudge-title">Hat dir dein Anschreiben gefallen?</h2>
            <p class="nudge-subtitle">
              Erstelle jetzt 3 weitere Bewerbungen — kostenlos und ohne Kreditkarte.
            </p>

            <ul class="nudge-features">
              <li>Professionelle PDF-Bewerbungen</li>
              <li>Job-Fit Analyse deiner Qualifikation</li>
              <li>E-Mail-Vorlagen direkt zum Versenden</li>
            </ul>

            <button @click="goToRegister" class="zen-btn zen-btn-ai zen-btn-lg nudge-cta">
              Kostenlos registrieren
            </button>
            <button @click="dismissNudge" class="nudge-dismiss">
              Vielleicht später
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Normal Landing Page (when not in CV upload flow) -->
    <template v-if="!showCvUploadFlow">
      <!-- Top Navigation -->
      <nav class="landing-nav">
        <div class="landing-nav-inner">
          <router-link to="/" class="nav-brand">
            <div class="nav-brand-enso"></div>
            <span>obo</span>
          </router-link>
          <div class="nav-links">
            <a href="#features" class="nav-link" @click.prevent="scrollToSection('features')">{{ $t('landing.nav.features') }}</a>
            <router-link to="/pricing" class="nav-link">{{ $t('landing.nav.pricing') }}</router-link>
            <router-link to="/login" class="nav-link">{{ $t('landing.nav.login') }}</router-link>
            <router-link to="/register" class="nav-link nav-link-cta">{{ $t('landing.nav.register') }}</router-link>
          </div>
        </div>
      </nav>

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
            />

            <!-- Supported Sites -->
            <div class="supported-sites">
              <span class="supported-label">Unterstützte Portale:</span>
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
              <h3>URL einfügen</h3>
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
              <p>Unsere KI extrahiert die Anforderungen und erstellt ein maßgeschneidertes Anschreiben.</p>
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

      <!-- Features Grid -->
      <section id="features" class="features-section">
        <div class="container">
          <div class="section-header" data-reveal>
            <span class="section-label">{{ $t('landing.features.label') }}</span>
            <h2 class="section-title">{{ $t('landing.features.title') }}</h2>
          </div>

          <div class="features-grid">
            <div class="feature-card" data-reveal>
              <div class="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <h3>{{ $t('landing.features.aiCoverLetter') }}</h3>
              <p>{{ $t('landing.features.aiCoverLetterDesc') }}</p>
            </div>

            <div class="feature-card" data-reveal>
              <div class="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <h3>{{ $t('landing.features.pdfExport') }}</h3>
              <p>{{ $t('landing.features.pdfExportDesc') }}</p>
            </div>

            <div class="feature-card" data-reveal>
              <div class="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4"/>
                  <path d="M12 8h.01"/>
                </svg>
              </div>
              <h3>{{ $t('landing.features.atsOptimization') }}</h3>
              <p>{{ $t('landing.features.atsOptimizationDesc') }}</p>
            </div>

            <div class="feature-card" data-reveal>
              <div class="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
              </div>
              <h3>{{ $t('landing.features.emailDraft') }}</h3>
              <p>{{ $t('landing.features.emailDraftDesc') }}</p>
            </div>

            <div class="feature-card" data-reveal>
              <div class="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h3>{{ $t('landing.features.interviewPrep') }}</h3>
              <p>{{ $t('landing.features.interviewPrepDesc') }}</p>
            </div>

            <div class="feature-card" data-reveal>
              <div class="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="3" width="7" height="7"/>
                  <rect x="14" y="3" width="7" height="7"/>
                  <rect x="14" y="14" width="7" height="7"/>
                  <rect x="3" y="14" width="7" height="7"/>
                </svg>
              </div>
              <h3>{{ $t('landing.features.tracker') }}</h3>
              <p>{{ $t('landing.features.trackerDesc') }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Social Proof -->
      <section class="social-proof-section">
        <div class="container">
          <div class="proof-content" data-reveal>
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

      <!-- Comparison Table -->
      <section class="comparison-section">
        <div class="container">
          <div class="section-header" data-reveal>
            <span class="section-label">Vergleich</span>
            <h2 class="section-title">{{ $t('landing.comparison.title') }}</h2>
          </div>

          <div class="comparison-table-wrapper" data-reveal>
            <table class="comparison-table">
              <thead>
                <tr>
                  <th>{{ $t('landing.comparison.feature') }}</th>
                  <th>{{ $t('landing.comparison.manual') }}</th>
                  <th>{{ $t('landing.comparison.chatgpt') }}</th>
                  <th class="comparison-highlight">{{ $t('landing.comparison.obo') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ $t('landing.comparison.time') }}</td>
                  <td>{{ $t('landing.comparison.timeManual') }}</td>
                  <td>{{ $t('landing.comparison.timeChatgpt') }}</td>
                  <td class="comparison-highlight"><strong>{{ $t('landing.comparison.timeObo') }}</strong></td>
                </tr>
                <tr>
                  <td>{{ $t('landing.comparison.personalized') }}</td>
                  <td>
                    <svg class="icon-partial" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
                  </td>
                  <td>
                    <svg class="icon-partial" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
                  </td>
                  <td class="comparison-highlight">
                    <svg class="icon-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </td>
                </tr>
                <tr>
                  <td>{{ $t('landing.comparison.pdfReady') }}</td>
                  <td>
                    <svg class="icon-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </td>
                  <td>
                    <svg class="icon-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </td>
                  <td class="comparison-highlight">
                    <svg class="icon-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </td>
                </tr>
                <tr>
                  <td>{{ $t('landing.comparison.atsOptimized') }}</td>
                  <td>
                    <svg class="icon-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </td>
                  <td>
                    <svg class="icon-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </td>
                  <td class="comparison-highlight">
                    <svg class="icon-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </td>
                </tr>
                <tr>
                  <td>{{ $t('landing.comparison.jobAnalysis') }}</td>
                  <td>
                    <svg class="icon-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </td>
                  <td>
                    <svg class="icon-partial" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
                  </td>
                  <td class="comparison-highlight">
                    <svg class="icon-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </td>
                </tr>
                <tr>
                  <td>{{ $t('landing.comparison.tracking') }}</td>
                  <td>
                    <svg class="icon-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </td>
                  <td>
                    <svg class="icon-cross" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </td>
                  <td class="comparison-highlight">
                    <svg class="icon-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Testimonials -->
      <section class="testimonials-section">
        <div class="container">
          <div class="section-header" data-reveal>
            <span class="section-label">Erfahrungen</span>
            <h2 class="section-title">{{ $t('landing.testimonials.title') }}</h2>
          </div>

          <div class="testimonials-grid">
            <div class="testimonial-card" data-reveal>
              <svg class="testimonial-quote-icon" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/>
              </svg>
              <p class="testimonial-text">{{ $t('landing.testimonials.t1Quote') }}</p>
              <div class="testimonial-author">
                <div class="testimonial-avatar">SM</div>
                <div>
                  <div class="testimonial-name">{{ $t('landing.testimonials.t1Name') }}</div>
                  <div class="testimonial-role">{{ $t('landing.testimonials.t1Role') }}</div>
                </div>
              </div>
            </div>

            <div class="testimonial-card" data-reveal>
              <svg class="testimonial-quote-icon" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/>
              </svg>
              <p class="testimonial-text">{{ $t('landing.testimonials.t2Quote') }}</p>
              <div class="testimonial-author">
                <div class="testimonial-avatar">LK</div>
                <div>
                  <div class="testimonial-name">{{ $t('landing.testimonials.t2Name') }}</div>
                  <div class="testimonial-role">{{ $t('landing.testimonials.t2Role') }}</div>
                </div>
              </div>
            </div>

            <div class="testimonial-card" data-reveal>
              <svg class="testimonial-quote-icon" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/>
              </svg>
              <p class="testimonial-text">{{ $t('landing.testimonials.t3Quote') }}</p>
              <div class="testimonial-author">
                <div class="testimonial-avatar">LW</div>
                <div>
                  <div class="testimonial-name">{{ $t('landing.testimonials.t3Name') }}</div>
                  <div class="testimonial-role">{{ $t('landing.testimonials.t3Role') }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Pricing Preview (3 tiers) -->
      <section class="pricing-section">
        <div class="container">
          <div class="section-header" data-reveal>
            <span class="section-label">Preise</span>
            <h2 class="section-title">Starte kostenlos</h2>
          </div>

          <div class="pricing-grid-3">
            <!-- Free -->
            <div class="pricing-card" data-reveal>
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
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  3 Anschreiben pro Monat
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Basis-Vorlagen
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  PDF-Export
                </li>
              </ul>
              <router-link to="/register" class="pricing-cta zen-btn">
                Kostenlos starten
              </router-link>
            </div>

            <!-- Basic -->
            <div class="pricing-card pricing-card-featured" data-reveal>
              <div class="pricing-badge">Beliebt</div>
              <div class="pricing-header">
                <h3>Basic</h3>
                <div class="pricing-price">
                  <span class="price-amount">9,99</span>
                  <span class="price-currency">EUR</span>
                  <span class="price-period">/Monat</span>
                </div>
              </div>
              <ul class="pricing-features">
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  20 Anschreiben pro Monat
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Alle Vorlagen
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  PDF-Export
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  ATS-Check
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  E-Mail-Entwurf
                </li>
              </ul>
              <router-link to="/register?plan=basic" class="pricing-cta zen-btn zen-btn-filled">
                Basic wählen
              </router-link>
            </div>

            <!-- Pro -->
            <div class="pricing-card" data-reveal>
              <div class="pricing-header">
                <h3>Pro</h3>
                <div class="pricing-price">
                  <span class="price-amount">19,99</span>
                  <span class="price-currency">EUR</span>
                  <span class="price-period">/Monat</span>
                </div>
              </div>
              <ul class="pricing-features">
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Unbegrenzte Anschreiben
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Premium-Vorlagen
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Job-Fit Score
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Interview-Vorbereitung
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Prioritäts-Support
                </li>
              </ul>
              <router-link to="/register?plan=pro" class="pricing-cta zen-btn zen-btn-ai">
                Pro wählen
              </router-link>
            </div>
          </div>

          <div class="pricing-compare-link" data-reveal>
            <router-link to="/pricing">
              Alle Features vergleichen
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </router-link>
          </div>
        </div>
      </section>

      <!-- Trust Badges -->
      <section class="trust-section">
        <div class="container">
          <div class="trust-badges" data-reveal>
            <div class="trust-badge">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span>{{ $t('landing.trust.gdpr') }}</span>
            </div>
            <div class="trust-badge">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>{{ $t('landing.trust.madeInGermany') }}</span>
            </div>
            <div class="trust-badge">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <span>{{ $t('landing.trust.noDataSharing') }}</span>
            </div>
            <div class="trust-badge">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
              <span>{{ $t('landing.trust.sslEncrypted') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section class="faq-section">
        <div class="container">
          <div class="section-header" data-reveal>
            <span class="section-label">FAQ</span>
            <h2 class="section-title">{{ $t('landing.faq.title') }}</h2>
          </div>
          <FaqAccordion :items="landingFaqItems" />
        </div>
      </section>

      <!-- Final CTA -->
      <section class="final-cta-section">
        <div class="container">
          <div class="cta-content" data-reveal>
            <h2>{{ $t('landing.cta.title') }}</h2>
            <p>{{ $t('landing.cta.subtitle') }}</p>
            <router-link to="/register" class="zen-btn zen-btn-ai zen-btn-lg">
              {{ $t('landing.cta.button') }}
            </router-link>
          </div>
        </div>
      </section>

      <!-- Footer -->
      <footer class="landing-footer">
        <div class="container">
          <div class="footer-grid">
            <div class="footer-brand-col">
              <div class="footer-brand">
                <div class="footer-enso"></div>
                <span>obo</span>
              </div>
              <p class="footer-tagline">{{ $t('landing.footer.tagline') }}</p>
              <div class="footer-micro-badges">
                <span class="micro-badge">DSGVO</span>
                <span class="micro-badge">Germany</span>
              </div>
            </div>
            <div class="footer-col">
              <h4>{{ $t('landing.footer.product') }}</h4>
              <a href="#features" @click.prevent="scrollToSection('features')">{{ $t('landing.footer.features') }}</a>
              <router-link to="/pricing">{{ $t('landing.footer.pricing') }}</router-link>
              <router-link to="/register">{{ $t('auth.register') }}</router-link>
            </div>
            <div class="footer-col">
              <h4>{{ $t('landing.footer.legal') }}</h4>
              <router-link to="/impressum">{{ $t('pages.impressum') }}</router-link>
              <router-link to="/datenschutz">{{ $t('pages.datenschutz') }}</router-link>
            </div>
            <div class="footer-col">
              <h4>Konto</h4>
              <router-link to="/login">{{ $t('auth.login') }}</router-link>
              <router-link to="/register">{{ $t('auth.register') }}</router-link>
            </div>
          </div>
          <div class="footer-bottom">
            <span>&copy; {{ currentYear }} obo</span>
          </div>
        </div>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import DemoGenerator from '../components/landing/DemoGenerator.vue'
import CraftingOverlay from '../components/application/CraftingOverlay.vue'
import FaqAccordion from '../components/landing/FaqAccordion.vue'
import EnsoCircle from '../components/application/EnsoCircle.vue'
import { useScrollReveal } from '../composables/useScrollReveal.js'
import { demoStore } from '../stores/demo'
import { authStore } from '../stores/auth'
import api from '../api/client'

const router = useRouter()
const { t } = useI18n()
const currentYear = computed(() => new Date().getFullYear())

useScrollReveal()

const landingFaqItems = computed(() => [
  { question: t('landing.faq.q1'), answer: t('landing.faq.a1') },
  { question: t('landing.faq.q2'), answer: t('landing.faq.a2') },
  { question: t('landing.faq.q3'), answer: t('landing.faq.a3') },
  { question: t('landing.faq.q4'), answer: t('landing.faq.a4') },
  { question: t('landing.faq.q5'), answer: t('landing.faq.a5') },
  { question: t('landing.faq.q6'), answer: t('landing.faq.a6') }
])

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

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

// Demo flow state
const showCraftingScreen = ref(false)
const craftingData = ref(null)
const demoResultData = ref(null)
const showDemoResult = ref(false)
const apiComplete = ref(false)

// 3-phase reveal state
const revealPhase = ref(0)
const peekExpanded = ref(false)
const showRegistrationNudge = ref(false)

const showCvUploadFlow = computed(() => {
  return authStore.isAuthenticated() && demoStore.isInDemoFlow()
})

const einleitungPreview = computed(() => {
  if (!demoResultData.value?.einleitung) return ''
  const text = demoResultData.value.einleitung
  const sentences = text.match(/[^.!?]*[.!?]+/g) || []
  return sentences.slice(0, 3).join(' ').trim()
})

// Trigger 3-phase reveal when demo result shows
watch(showDemoResult, (show) => {
  if (show) {
    revealPhase.value = 0
    peekExpanded.value = false
    setTimeout(() => { revealPhase.value = 1 }, 200)
    setTimeout(() => { revealPhase.value = 2 }, 800)
    setTimeout(() => { revealPhase.value = 3 }, 1400)
    document.body.style.overflow = 'hidden'
  } else {
    revealPhase.value = 0
    document.body.style.overflow = ''
  }
})

function handleFileSelection(file) {
  if (!file) return
  if (file.type === 'application/pdf') {
    selectedFile.value = file
    uploadError.value = ''
  } else {
    uploadError.value = 'Bitte wähle eine PDF-Datei aus.'
  }
}

function triggerFileSelect() {
  fileInput.value?.click()
}

function onFileSelect(event) {
  handleFileSelection(event.target.files?.[0])
}

function onDragOver() {
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(event) {
  isDragging.value = false
  handleFileSelection(event.dataTransfer.files?.[0])
}

function clearFile() {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function uploadCvAndRegenerate() {
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

        try {
          const statsResponse = await api.silent.get('/stats')
          usageInfo.value = statsResponse.data.usage
        } catch {
          // Usage info is non-critical
        }

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
  } catch (uploadErr) {
    uploadError.value = uploadErr.response?.data?.error || 'Upload fehlgeschlagen. Bitte versuche es erneut.'
  } finally {
    isUploading.value = false
  }
}

function skipToDashboard() {
  demoStore.clear()
  router.push('/dashboard')
}

async function downloadPdf() {
  if (!createdApplicationId.value) {
    router.push('/dashboard')
    return
  }

  try {
    const response = await api.get(`/applications/${createdApplicationId.value}/pdf`, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Anschreiben_${regeneratedResult.value?.firma || 'Bewerbung'}.pdf`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('PDF download failed:', err)
    router.push('/applications')
  }
}

function onDemoStarted() {
  showCraftingScreen.value = true
  apiComplete.value = false
  demoResultData.value = null

  craftingData.value = {
    ansprechpartner: '',
    firma: '',
    position: '',
    einleitung: ''
  }
}

function onDemoComplete(result) {
  apiComplete.value = true

  if (result.result?.data) {
    craftingData.value = {
      ansprechpartner: result.result.data.ansprechpartner || '',
      firma: result.result.data.firma || '',
      position: result.result.data.position || '',
      einleitung: result.result.data.einleitung || ''
    }

    demoResultData.value = result.result.data

    if (result.result.data.cv_text) {
      demoStore.setCvData(result.result.data.cv_text, null)
    }
    demoStore.setPreviewData(result.result.data)
    demoStore.setDemoComplete(result.url, result.result)

    if (!showCraftingScreen.value) {
      showDemoResult.value = true
    }
  } else {
    showCraftingScreen.value = false
    router.push({
      path: '/register',
      query: { demo: 'complete' }
    })
  }
}

function onCraftingComplete() {
  showCraftingScreen.value = false

  if (apiComplete.value && demoResultData.value) {
    showDemoResult.value = true
  }
}

function onDemoRegister() {
  showDemoResult.value = false
  router.push('/register')
}

function downloadDemoPdf() {
  if (!demoResultData.value?.pdf_base64) {
    // Fallback if no PDF available: go straight to register
    onDemoRegister()
    return
  }

  const byteCharacters = window.atob(demoResultData.value.pdf_base64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const blob = new Blob([byteArray], { type: 'application/pdf' })

  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Anschreiben_${demoResultData.value.firma || 'Bewerbung'}.pdf`
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)

  // Show nudge modal after brief delay
  setTimeout(() => {
    showDemoResult.value = false
    showRegistrationNudge.value = true
  }, 500)
}

function dismissNudge() {
  showRegistrationNudge.value = false
}

function goToRegister() {
  showRegistrationNudge.value = false
  router.push('/register')
}

onMounted(() => {
  // Clear leftover demo state if user is no longer authenticated
  if (!authStore.isAuthenticated() && demoStore.isInDemoFlow()) {
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
   DEMO REVEAL OVERLAY (3-phase)
   ======================================== */
.demo-reveal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(30, 30, 30, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.demo-reveal-modal {
  width: 100%;
  max-width: 480px;
  max-height: calc(100dvh - 2 * var(--space-lg));
  overflow-y: auto;
  background: var(--color-washi);
  border-radius: var(--radius-lg);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  padding: var(--space-2xl) var(--space-xl) var(--space-xl);
  position: relative;
}

.demo-reveal-close {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
  background: transparent;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  opacity: 0.6;
  transition: opacity var(--transition-base), color var(--transition-base);
  z-index: 10;
}

.demo-reveal-close:hover {
  opacity: 1;
  color: var(--color-sumi);
}

/* Phase 1: Enso */
.demo-reveal-enso {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-xl) 0 var(--space-lg);
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.4s var(--ease-zen), transform 0.4s var(--ease-zen);
}

.demo-reveal-enso--visible {
  opacity: 1;
  transform: scale(1);
}

/* Phase 2: Content */
.demo-reveal-content {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s var(--ease-zen) 0.1s, transform 0.5s var(--ease-zen) 0.1s;
}

.demo-reveal-content--visible {
  opacity: 1;
  transform: translateY(0);
}

.demo-reveal-header {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.demo-reveal-title {
  font-size: 1.75rem;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--color-sumi);
  margin: 0 0 var(--space-sm) 0;
}

.demo-reveal-company {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.demo-reveal-company strong {
  color: var(--color-ai);
  font-weight: 500;
}

/* Peek card */
.demo-reveal-peek {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  cursor: pointer;
  transition: border-color 0.2s var(--ease-zen), box-shadow 0.2s var(--ease-zen);
  overflow: hidden;
}

.demo-reveal-peek:hover {
  border-color: var(--color-ai);
  box-shadow: 0 2px 8px rgba(61, 90, 108, 0.08);
}

.demo-reveal-peek-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  font-weight: 500;
}

.demo-reveal-peek-label {
  flex: 1;
}

.demo-reveal-peek-chevron {
  transition: transform 0.2s var(--ease-zen);
  flex-shrink: 0;
}

.demo-reveal-peek--expanded .demo-reveal-peek-chevron {
  transform: rotate(180deg);
}

.demo-reveal-peek-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s var(--ease-zen), padding 0.3s var(--ease-zen);
  padding: 0 var(--space-md);
}

.demo-reveal-peek--expanded .demo-reveal-peek-body {
  max-height: 120px;
  padding: 0 var(--space-md) var(--space-md);
}

.demo-reveal-peek-text {
  font-size: 0.875rem;
  line-height: var(--leading-relaxed);
  color: var(--color-text-secondary);
  margin: 0;
  font-style: italic;
}

/* Phase 3: Actions */
.demo-reveal-actions {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.5s var(--ease-zen), transform 0.5s var(--ease-zen);
  padding-top: var(--space-md);
}

.demo-reveal-actions--visible {
  opacity: 1;
  transform: translateY(0);
}

.demo-reveal-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  align-items: center;
}

.demo-reveal-btn-primary {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.demo-reveal-btn-secondary {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.demo-reveal-btn-secondary:hover {
  border-color: var(--color-sumi);
  color: var(--color-sumi);
  background: var(--color-washi-warm);
}

/* ========================================
   REGISTRATION NUDGE MODAL
   ======================================== */
.nudge-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(30, 30, 30, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.nudge-modal {
  width: 100%;
  max-width: 440px;
  background: var(--color-washi);
  border-radius: var(--radius-lg);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  padding: var(--space-2xl) var(--space-xl) var(--space-xl);
  text-align: center;
}

.nudge-enso {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-lg);
}

.nudge-title {
  font-size: 1.5rem;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--color-sumi);
  margin: 0 0 var(--space-sm) 0;
}

.nudge-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-lg) 0;
  line-height: var(--leading-relaxed);
}

.nudge-features {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-xl) 0;
  text-align: left;
}

.nudge-features li {
  position: relative;
  padding: var(--space-xs) 0 var(--space-xs) var(--space-xl);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
}

.nudge-features li::before {
  content: "\2713";
  position: absolute;
  left: 0;
  color: var(--color-koke);
  font-weight: 600;
}

.nudge-cta {
  width: 100%;
  margin-bottom: var(--space-md);
}

.nudge-dismiss {
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: color var(--transition-base);
}

.nudge-dismiss:hover {
  color: var(--color-ai);
}

/* Demo result transitions */
.demo-result-enter-active {
  animation: demoRevealEnter 0.4s var(--ease-zen);
}

.demo-result-leave-active {
  animation: demoRevealLeave 0.3s var(--ease-zen);
}

/* Nudge modal transitions */
.nudge-modal-enter-active {
  animation: nudgeEnter 0.4s var(--ease-zen);
}

.nudge-modal-leave-active {
  animation: nudgeLeave 0.3s var(--ease-zen);
}

@keyframes demoRevealEnter {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

@keyframes demoRevealLeave {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

@keyframes nudgeEnter {
  0% {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 1;
  }
}

@keyframes nudgeLeave {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

/* ========================================
   LANDING NAV
   ======================================== */
.landing-nav {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  padding: var(--space-md) var(--space-ma);
}

.landing-nav-inner {
  max-width: var(--container-xl);
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  text-decoration: none;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
  letter-spacing: -0.02em;
}

.nav-brand-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--color-sumi);
  opacity: 0.7;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  justify-content: flex-end;
}

.nav-link {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-full);
  transition: color var(--transition-base);
}

.nav-link:hover {
  color: var(--color-sumi);
}

.nav-link-cta {
  background: var(--color-ai);
  color: var(--color-text-inverse);
  font-weight: 500;
}

.nav-link-cta:hover {
  color: var(--color-text-inverse);
  opacity: 0.9;
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

.pricing-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
  max-width: 1000px;
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

.pricing-compare-link {
  text-align: center;
  margin-top: var(--space-xl);
}

.pricing-compare-link a {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ai);
  text-decoration: none;
  font-size: 0.9375rem;
  font-weight: 500;
  transition: gap var(--transition-base);
}

.pricing-compare-link a:hover {
  gap: var(--space-sm);
}

/* ========================================
   FEATURES SECTION
   ======================================== */
.features-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.feature-card {
  padding: var(--space-xl);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lifted);
}

.feature-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  margin-bottom: var(--space-lg);
}

.feature-card h3 {
  font-size: 1.125rem;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.feature-card p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

/* ========================================
   COMPARISON SECTION
   ======================================== */
.comparison-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
}

.comparison-table-wrapper {
  max-width: 800px;
  margin: 0 auto;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.comparison-table {
  width: 100%;
  min-width: 480px;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.comparison-table th,
.comparison-table td {
  padding: var(--space-md) var(--space-lg);
  text-align: center;
  border-bottom: 1px solid var(--color-border-light);
}

.comparison-table th:first-child,
.comparison-table td:first-child {
  text-align: left;
  font-weight: 500;
  color: var(--color-sumi);
}

.comparison-table th {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-tertiary);
  padding-bottom: var(--space-lg);
}

.comparison-table th.comparison-highlight {
  color: var(--color-ai);
}

.comparison-table td.comparison-highlight {
  background: var(--color-ai-subtle);
}

.comparison-table td.comparison-highlight strong {
  color: var(--color-ai);
}

.icon-check {
  color: var(--color-koke);
}

.icon-cross {
  color: var(--color-text-ghost);
}

.icon-partial {
  color: var(--color-text-tertiary);
}

/* ========================================
   TESTIMONIALS SECTION
   ======================================== */
.testimonials-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi);
}

.testimonials-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.testimonial-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: var(--space-xl);
  position: relative;
  display: flex;
  flex-direction: column;
}

.testimonial-quote-icon {
  color: var(--color-ai);
  opacity: 0.15;
  margin-bottom: var(--space-md);
}

.testimonial-text {
  font-size: 0.9375rem;
  font-style: italic;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-lg);
  flex: 1;
}

.testimonial-author {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.testimonial-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8125rem;
  font-weight: 600;
  flex-shrink: 0;
}

.testimonial-name {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.testimonial-role {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

/* ========================================
   TRUST SECTION
   ======================================== */
.trust-section {
  padding: var(--space-ma-lg) 0;
  background: var(--color-washi);
}

.trust-badges {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--space-xl);
}

.trust-badge {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  font-weight: 500;
}

.trust-badge svg {
  color: var(--color-koke);
  opacity: 0.7;
}

/* ========================================
   FAQ SECTION
   ======================================== */
.faq-section {
  padding: var(--space-ma-2xl) 0;
  background: var(--color-washi-warm);
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
  padding: var(--space-ma-lg) 0 var(--space-xl);
  background: var(--color-washi-warm);
  border-top: 1px solid var(--color-border-light);
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.footer-brand-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-size: 1.125rem;
  color: var(--color-sumi);
}

.footer-enso {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1.5px solid var(--color-text-ghost);
  opacity: 0.6;
}

.footer-tagline {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

.footer-micro-badges {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.micro-badge {
  padding: 2px var(--space-sm);
  background: var(--color-washi-aged);
  border-radius: var(--radius-full);
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--color-text-ghost);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.footer-col h4 {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-xs);
}

.footer-col a {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-base);
}

.footer-col a:hover {
  color: var(--color-ai);
}

.footer-bottom {
  text-align: center;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
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
  .steps-grid,
  .features-grid,
  .testimonials-grid {
    grid-template-columns: repeat(2, 1fr);
    max-width: 700px;
  }

  .pricing-grid-3 {
    grid-template-columns: 1fr;
    max-width: 400px;
  }

  .footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-lg);
  }

  .footer-brand-col {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .landing-nav {
    padding: var(--space-sm) var(--space-md);
  }

  .nav-link {
    padding: var(--space-xs) var(--space-sm);
    font-size: 0.875rem;
  }

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

  .steps-grid,
  .features-grid,
  .testimonials-grid {
    grid-template-columns: 1fr;
    max-width: 500px;
  }

  .comparison-table th:nth-child(2),
  .comparison-table td:nth-child(2) {
    display: none;
  }

  .footer-grid {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .footer-brand-col {
    align-items: center;
  }

  .footer-micro-badges {
    justify-content: center;
  }

  .footer-col {
    align-items: center;
  }

  .trust-badges {
    gap: var(--space-lg);
  }

  .result-actions {
    gap: var(--space-sm);
  }

  .demo-result-overlay {
    padding: var(--space-md);
  }
}

@media (max-width: 480px) {
  .supported-sites {
    flex-direction: column;
  }

  .site-badges {
    justify-content: center;
  }

  .nav-links {
    gap: var(--space-xs);
  }

  .nav-link {
    padding: 4px var(--space-xs);
    font-size: 0.8125rem;
  }

  .trust-badges {
    flex-direction: column;
    gap: var(--space-md);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .demo-reveal-enso,
  .demo-reveal-content,
  .demo-reveal-actions {
    transition: none;
    opacity: 1;
    transform: none;
  }

  .demo-reveal-peek-body,
  .demo-reveal-peek-chevron {
    transition: none;
  }
}

/* Mobile responsive for reveal + nudge */
@media (max-width: 768px) {
  .demo-reveal-modal {
    padding: var(--space-xl) var(--space-lg) var(--space-lg);
    margin: var(--space-md);
    max-width: calc(100% - var(--space-lg));
  }

  .demo-reveal-title {
    font-size: 1.5rem;
  }

  .nudge-modal {
    padding: var(--space-xl) var(--space-lg) var(--space-lg);
    margin: var(--space-md);
    max-width: calc(100% - var(--space-lg));
  }

  .nudge-title {
    font-size: 1.25rem;
  }
}
</style>
