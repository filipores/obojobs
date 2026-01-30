<template>
  <div class="new-application-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Neue Bewerbung</h1>
        <p class="page-subtitle">Generiere ein Anschreiben aus einer Stellenanzeigen-URL</p>
      </section>

      <!-- Resume/CV Missing Warning Banner - vor dem Formular (höhere Priorität) -->
      <section v-if="!checkingResume && !hasResume" class="resume-warning-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="resume-warning zen-card">
          <div class="resume-warning-icon-box">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <line x1="10" y1="9" x2="8" y2="9"/>
            </svg>
          </div>
          <div class="resume-warning-text-content">
            <h3>Lebenslauf erforderlich</h3>
            <p>
              Um eine <strong>personalisierte Bewerbung</strong> zu generieren, benötigen wir deinen Lebenslauf.
              Dieser wird für die Erstellung des Anschreibens und den Job-Fit Score verwendet.
            </p>
            <div class="resume-warning-actions">
              <router-link to="/documents?from=new-application&upload=lebenslauf" class="zen-btn zen-btn-ai">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Lebenslauf hochladen
              </router-link>
              <span class="resume-warning-hint">PDF-Format, max. 10 MB</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Skills Missing Warning Banner - vor dem Formular -->
      <section v-if="!checkingSkills && !hasSkills && hasResume" class="skills-warning-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="skills-warning zen-card">
          <div class="warning-icon-box">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <div class="warning-text-content">
            <h3>Skills für Job-Fit-Analyse benötigt</h3>
            <p>
              Um den <strong>Job-Fit Score</strong> zu berechnen, werden deine Skills mit den Anforderungen der Stellenanzeige verglichen.
              Du kannst trotzdem eine Bewerbung generieren, aber der Job-Fit Score ist ohne Skills nicht verfügbar.
            </p>
            <div class="warning-actions">
              <router-link to="/documents" class="zen-btn zen-btn-ai">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Lebenslauf hochladen
              </router-link>
              <span class="warning-hint">Skills werden automatisch aus deinem Lebenslauf extrahiert</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Form Section -->
      <section class="form-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="form-card zen-card">
          <!-- URL Input with Portal Detection -->
          <div class="form-group">
            <label class="form-label">Stellenanzeigen-URL</label>
            <div class="url-input-wrapper">
              <svg class="url-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              <input
                v-model="url"
                type="url"
                placeholder="https://example.com/jobs/stellenanzeige"
                class="form-input url-input"
                :class="{
                  'url-valid': showUrlValidation && urlValidation.isValid === true,
                  'url-invalid': showUrlValidation && urlValidation.isValid === false
                }"
                :disabled="loading || generating"
                @input="onUrlInput"
                @keydown.enter="onUrlEnterPressed"
              />
              <!-- Validation Icon -->
              <span v-if="showUrlValidation && urlValidation.isValid === true" class="url-validation-icon url-validation-valid">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </span>
              <span v-else-if="showUrlValidation && urlValidation.isValid === false" class="url-validation-icon url-validation-invalid" :title="urlValidation.message">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </span>
              <!-- Portal Badge -->
              <span v-if="detectedPortal && urlValidation.isValid !== false" :class="['portal-badge', `portal-${detectedPortal.id}`]">
                {{ detectedPortal.name }}
              </span>
            </div>
            <!-- Validation Error Message -->
            <p v-if="showUrlValidation && urlValidation.isValid === false" class="url-validation-message">
              {{ urlValidation.message }}
            </p>
            <p v-else class="form-hint">Kopiere die URL der Stellenanzeige und füge sie hier ein</p>
            <!-- ARIA Live Region for Screenreaders -->
            <div class="sr-only" aria-live="polite" aria-atomic="true">
              {{ urlValidationAnnouncement }}
            </div>
          </div>

          <!-- Preview Button (only show if no preview yet) -->
          <div v-if="!previewData" class="form-actions preview-actions">
            <button
              @click="loadPreview"
              :disabled="!url || loading || urlValidation.isValid !== true"
              class="zen-btn zen-btn-lg"
            >
              <span v-if="loading" class="btn-loading">
                <span class="loading-spinner"></span>
                Lade Stellenanzeige...
              </span>
              <span v-else>
                Stellenanzeige laden
              </span>
            </button>
          </div>

          <!-- Error Message with Fallback Option -->
          <div v-if="error && !previewData && !showManualFallback" class="error-box error-with-fallback">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <div class="error-content">
              <span>{{ error }}</span>
              <p class="fallback-hint">
                Einige Job-Portale blockieren automatisches Laden.
                Sie können den Stellentext auch manuell einfügen.
              </p>
              <button @click="showManualFallback = true" class="zen-btn zen-btn-sm fallback-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                Stellentext manuell einfügen
              </button>
            </div>
          </div>

          <!-- Manual Text Fallback Section -->
          <div v-if="showManualFallback && !previewData" class="manual-fallback-section">
            <div class="fallback-header">
              <h3>Stellentext manuell einfügen</h3>
              <button @click="showManualFallback = false" class="close-fallback-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <p class="fallback-description">
              Kopieren Sie den vollständigen Text der Stellenanzeige und fügen Sie ihn hier ein.
              Die Daten werden automatisch analysiert.
            </p>

            <div class="form-group">
              <label class="form-label">Firmenname</label>
              <input
                v-model="manualCompany"
                type="text"
                class="form-input"
                placeholder="z.B. Beispiel GmbH"
                :disabled="analyzingManualText"
              />
            </div>

            <div class="form-group">
              <label class="form-label">Position (optional)</label>
              <input
                v-model="manualTitle"
                type="text"
                class="form-input"
                placeholder="z.B. Software Entwickler (m/w/d)"
                :disabled="analyzingManualText"
              />
            </div>

            <div class="form-group">
              <label class="form-label required" for="manual-job-text">Stellentext</label>
              <textarea
                id="manual-job-text"
                v-model="manualJobText"
                class="form-textarea manual-text-area"
                rows="12"
                placeholder="Fügen Sie hier den vollständigen Text der Stellenanzeige ein..."
                :disabled="analyzingManualText"
                required
                aria-required="true"
              ></textarea>
              <p class="form-hint">Mindestens 100 Zeichen erforderlich</p>
            </div>

            <div v-if="manualTextError" class="error-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <span>{{ manualTextError }}</span>
            </div>

            <div class="form-actions">
              <button
                @click="analyzeManualText"
                :disabled="!canAnalyzeManualText || analyzingManualText"
                class="zen-btn zen-btn-ai"
              >
                <span v-if="analyzingManualText" class="btn-loading">
                  <span class="loading-spinner"></span>
                  Analysiere...
                </span>
                <span v-else>
                  Stellentext analysieren
                </span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Preview Section (shown after loading) -->
      <section v-if="previewData" class="preview-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="preview-card zen-card">
          <div class="preview-header">
            <div class="preview-title-row">
              <h2>Stellenanzeige Preview</h2>
              <span :class="['portal-tag', `portal-${previewData.portal_id}`]">
                {{ previewData.portal }}
              </span>
            </div>
            <button @click="resetPreview" class="reset-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M8 16H3v5"/>
              </svg>
              Neu laden
            </button>
          </div>

          <!-- Missing Fields Warning -->
          <div v-if="previewData.missing_fields?.length > 0" class="warning-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <div>
              <strong>Fehlende Daten</strong>
              <p>Folgende wichtige Felder konnten nicht automatisch erkannt werden: {{ previewData.missing_fields.join(', ') }}</p>
            </div>
          </div>

          <!-- Editable Preview Form -->
          <div class="preview-form">
            <!-- Core Fields Row -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label required" for="preview-company">Firma</label>
                <input
                  id="preview-company"
                  v-model="editableData.company"
                  type="text"
                  class="form-input"
                  :class="{ 'field-warning': !editableData.company }"
                  placeholder="Firmenname eingeben"
                  required
                  aria-required="true"
                />
              </div>
              <div class="form-group">
                <label class="form-label required" for="preview-title">Position</label>
                <input
                  id="preview-title"
                  v-model="editableData.title"
                  type="text"
                  class="form-input"
                  :class="{ 'field-warning': !editableData.title }"
                  placeholder="Stellentitel eingeben"
                  required
                  aria-required="true"
                />
              </div>
            </div>

            <!-- Location and Employment Type Row -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label" for="location-input">Standort</label>
                <input
                  id="location-input"
                  v-model="editableData.location"
                  type="text"
                  class="form-input"
                  placeholder="z.B. Berlin, Hamburg"
                />
              </div>
              <div class="form-group">
                <label class="form-label" for="employment-type-input">Anstellungsart</label>
                <input
                  id="employment-type-input"
                  v-model="editableData.employment_type"
                  type="text"
                  class="form-input"
                  placeholder="z.B. Vollzeit, Teilzeit"
                />
              </div>
            </div>

            <!-- Contact Fields Row -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label" for="contact-person-input">Ansprechpartner</label>
                <input
                  id="contact-person-input"
                  v-model="editableData.contact_person"
                  type="text"
                  class="form-input"
                  placeholder="Name des Ansprechpartners"
                />
              </div>
              <div class="form-group">
                <label class="form-label" for="contact-email-input">Kontakt-Email</label>
                <input
                  id="contact-email-input"
                  v-model="editableData.contact_email"
                  type="email"
                  class="form-input"
                  placeholder="email@firma.de"
                />
              </div>
            </div>

            <!-- Salary (if available) -->
            <div v-if="editableData.salary || previewData.salary" class="form-group">
              <label class="form-label" for="salary-input">Gehalt</label>
              <input
                id="salary-input"
                v-model="editableData.salary"
                type="text"
                class="form-input"
                placeholder="Gehaltsangabe"
              />
            </div>

            <!-- Description (collapsible) -->
            <div class="form-group description-group">
              <div
                class="description-header"
                tabindex="0"
                role="button"
                :aria-expanded="showDescription"
                aria-controls="description-content"
                @click="showDescription = !showDescription"
                @keydown.enter.prevent="showDescription = !showDescription"
                @keydown.space.prevent="showDescription = !showDescription"
              >
                <label class="form-label">Stellenbeschreibung</label>
                <button type="button" class="toggle-btn" tabindex="-1" aria-hidden="true">
                  <svg
                    :class="['toggle-icon', { rotated: showDescription }]"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
              </div>
              <div v-show="showDescription" id="description-content" class="description-content">
                <textarea
                  v-model="editableData.description"
                  class="form-textarea"
                  rows="8"
                  placeholder="Stellenbeschreibung..."
                ></textarea>
              </div>
            </div>

            <!-- Template Variables Info -->
            <div class="template-variables-info">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              <div>
                <strong>Template-Variablen werden automatisch befüllt:</strong>
                <span class="variable-list">
                  <code
                    v-for="(value, key) in templateVariables"
                    :key="key"
                    :title="value || 'nicht verfügbar'"
                    :class="{ missing: !value }"
                  >{{ getVariableDisplay(key) }}</code>
                </span>
              </div>
            </div>
          </div>

          <!-- Requirements Analysis Status (NEW-003) -->
          <div v-if="analyzingRequirements" class="requirements-analyzing">
            <div class="analyzing-content">
              <div class="loading-spinner"></div>
              <div class="analyzing-text">
                <strong>Analysiere Anforderungen...</strong>
                <p>KI extrahiert Must-Have und Nice-to-Have Anforderungen aus der Stellenanzeige.</p>
              </div>
            </div>
          </div>

          <!-- Requirements Error - nur zeigen wenn kein tempApplicationId und kein allgemeiner error -->
          <div v-else-if="requirementsError.message && !tempApplicationId && !error" class="requirements-error" :class="{ 'error-temporary': requirementsError.isTemporary }">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <div class="requirements-error-content">
              <strong>{{ requirementsError.message }}</strong>
              <p v-if="requirementsError.hint">{{ requirementsError.hint }}</p>

              <!-- Alternative Aktionen - klar strukturiert -->
              <div class="requirements-alternatives">
                <p class="alternatives-header">Was Sie jetzt tun koennen:</p>
                <ul class="alternatives-list">
                  <li>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>Bewerbung ohne Job-Fit Score generieren</span>
                  </li>
                  <li v-if="requirementsError.isTemporary">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                      <path d="M21 3v5h-5"/>
                    </svg>
                    <span>Analyse erneut versuchen</span>
                  </li>
                  <li v-if="!hasSkills">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    <span>Lebenslauf hochladen fuer bessere Analyse</span>
                  </li>
                </ul>
              </div>

              <div class="requirements-error-actions">
                <!-- Retry Button for temporary errors -->
                <button
                  v-if="requirementsError.isTemporary"
                  @click="retryRequirementsAnalysis"
                  class="zen-btn zen-btn-sm requirements-retry-btn"
                  :disabled="analyzingRequirements"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                    <path d="M21 3v5h-5"/>
                    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                    <path d="M8 16H3v5"/>
                  </svg>
                  Erneut versuchen
                </button>
                <!-- Continue without score button -->
                <button
                  @click="scrollToGenerateButton"
                  class="zen-btn zen-btn-sm requirements-continue-btn"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                  Ohne Score fortfahren
                </button>
                <!-- Contact link for persistent errors -->
                <router-link
                  v-if="requirementsError.showContactLink"
                  to="/support"
                  class="requirements-contact-link"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                  Support kontaktieren
                </router-link>
              </div>
            </div>
          </div>

          <!-- Job-Fit Score -->
          <JobFitScore
            v-if="tempApplicationId"
            :application-id="tempApplicationId"
            @score-loaded="onJobFitScoreLoaded"
          />

          <!-- Template Selection -->
          <div class="form-group template-selection">
            <label class="form-label">Anschreiben-Template</label>
            <select v-model="selectedTemplateId" class="form-select" :disabled="generating || loadingTemplates">
              <option :value="null">Standard-Template verwenden</option>
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}{{ template.is_default ? ' (Standard)' : '' }}
              </option>
            </select>
          </div>

          <!-- Low Score Warning on Generate Button -->
          <div v-if="showLowScoreWarning" class="low-score-generate-warning">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span>Der Job-Fit Score ist niedrig ({{ jobFitScore?.overall_score }}%). Moeglicherweise passt diese Stelle nicht optimal zu Ihrem Profil.</span>
          </div>

          <!-- Generate Button -->
          <div class="form-actions">
            <button
              @click="generateApplication"
              :disabled="!canGenerate || generating"
              class="zen-btn zen-btn-ai zen-btn-lg"
            >
              <span v-if="generating" class="btn-loading">
                <span class="loading-spinner"></span>
                Generiere Bewerbung...
              </span>
              <span v-else>
                Bewerbung generieren
              </span>
            </button>
            <p class="usage-info">
              <span v-if="usage?.unlimited">Unbegrenzte Bewerbungen ({{ getPlanLabel() }})</span>
              <span v-else>Noch {{ usage?.remaining || 0 }} von {{ usage?.limit || 3 }} Bewerbungen diesen Monat</span>
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="error && previewData" class="error-box" :class="{ 'error-with-action': isDocumentMissingError || isSubscriptionLimitError }">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <div class="error-content">
              <span>{{ error }}</span>
              <div v-if="isDocumentMissingError" class="error-actions">
                <router-link to="/documents" class="zen-btn zen-btn-sm">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <line x1="10" y1="9" x2="8" y2="9"/>
                  </svg>
                  Zu den Dokumenten
                </router-link>
              </div>
              <div v-if="isSubscriptionLimitError" class="error-actions">
                <router-link to="/subscription" class="zen-btn zen-btn-sm zen-btn-ai">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                    <path d="M2 17l10 5 10-5"/>
                    <path d="M2 12l10 5 10-5"/>
                  </svg>
                  Abo upgraden
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Info Box (show when no preview) -->
      <section v-if="!previewData" class="info-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="info-box zen-card">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <div class="info-content">
            <strong>So funktioniert's:</strong>
            <ul>
              <li>Füge eine Stellenanzeigen-URL ein</li>
              <li>Die Daten werden automatisch extrahiert (Firma, Position, Kontakt...)</li>
              <li>Prüfe und bearbeite die Daten vor der Generierung</li>
              <li>Ein personalisiertes Anschreiben wird erstellt</li>
            </ul>
            <div class="supported-portals">
              <strong>Unterstützte Job-Portale:</strong>
              <div class="portal-list">
                <span class="portal-item portal-stepstone">StepStone</span>
                <span class="portal-item portal-indeed">Indeed</span>
                <span class="portal-item portal-xing">XING</span>
                <span class="portal-item portal-generic">+ Weitere</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Success Modal -->
      <Teleport to="body">
        <div v-if="generatedApp" class="modal-overlay" @click="closeModal">
          <div
            class="modal zen-card animate-fade-up"
            role="dialog"
            aria-modal="true"
            aria-labelledby="success-modal-title"
            @click.stop
            @keydown.tab="trapFocus"
          >
            <div class="modal-header success-header">
              <div class="success-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <div>
                <h2 id="success-modal-title">Bewerbung erstellt!</h2>
                <p class="modal-subtitle">{{ generatedApp.firma }}</p>
              </div>
              <button @click="closeModal" class="modal-close" aria-label="Modal schließen">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div class="modal-content">
              <!-- Info Grid -->
              <div class="info-grid">
                <div class="detail-group">
                  <label class="detail-label">Firma</label>
                  <p class="detail-value">{{ generatedApp.firma }}</p>
                </div>

                <div class="detail-group">
                  <label class="detail-label">Position</label>
                  <p class="detail-value">{{ generatedApp.position || 'Nicht angegeben' }}</p>
                </div>

                <div v-if="generatedApp.ansprechpartner" class="detail-group">
                  <label class="detail-label">Ansprechpartner</label>
                  <p class="detail-value">{{ generatedApp.ansprechpartner }}</p>
                </div>

                <div v-if="generatedApp.email" class="detail-group">
                  <label class="detail-label">Email</label>
                  <p class="detail-value">
                    <a :href="`mailto:${generatedApp.email}`" class="detail-link">{{ generatedApp.email }}</a>
                  </p>
                </div>
              </div>

              <!-- Betreff -->
              <div v-if="generatedApp.betreff" class="detail-group">
                <label class="detail-label">Betreff</label>
                <p class="detail-value detail-value-block">{{ generatedApp.betreff }}</p>
              </div>
            </div>

            <div class="modal-footer">
              <button @click="downloadPDF" class="zen-btn zen-btn-ai">
                PDF herunterladen
              </button>
              <button @click="goToApplications" class="zen-btn">
                Alle Bewerbungen
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import JobFitScore from '../components/JobFitScore.vue'

const router = useRouter()

// Escape key handler for modal
const handleKeydown = (e) => {
  if (e.key === 'Escape' && generatedApp.value) {
    closeModal()
  }
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// Skills check state
const checkingSkills = ref(true)
const hasSkills = ref(true)

// Resume/CV check state
const checkingResume = ref(true)
const hasResume = ref(true)

// State
const url = ref('')
const urlTouched = ref(false)
const selectedTemplateId = ref(null)
const templates = ref([])
const loadingTemplates = ref(false)
const loading = ref(false)
const generating = ref(false)
const error = ref('')
const usage = ref(null)
const generatedApp = ref(null)

// Preview state
const previewData = ref(null)
const editableData = ref({
  company: '',
  title: '',
  location: '',
  employment_type: '',
  contact_person: '',
  contact_email: '',
  salary: '',
  description: ''
})
const showDescription = ref(false)

// Manual text fallback state
const showManualFallback = ref(false)
const manualJobText = ref('')
const manualCompany = ref('')
const manualTitle = ref('')
const manualTextError = ref('')
const analyzingManualText = ref(false)
const isManualEntry = ref(false)

// Can analyze manual text check
const canAnalyzeManualText = computed(() => {
  return manualJobText.value.trim().length >= 100
})

// Job-Fit Score state
const tempApplicationId = ref(null)
const jobFitScore = ref(null)
const showLowScoreWarning = ref(false)

// Requirements analysis state
const analyzingRequirements = ref(false)
const requirementsError = ref({
  message: '',
  hint: '',
  isTemporary: false,
  showContactLink: false
})
const requirementsCount = ref(0)

// URL validation
const urlValidation = computed(() => {
  const urlValue = url.value.trim()

  // Empty - no validation state
  if (!urlValue) {
    return { isValid: null, message: '' }
  }

  // Must start with http:// or https://
  if (!urlValue.match(/^https?:\/\//i)) {
    return { isValid: false, message: 'URL muss mit http:// oder https:// beginnen' }
  }

  // Basic URL pattern check
  try {
    const parsedUrl = new URL(urlValue)

    // Check for valid hostname (must have at least one dot)
    if (!parsedUrl.hostname.includes('.')) {
      return { isValid: false, message: 'Ungültige Domain (z.B. example.com)' }
    }

    // Check for common typos
    if (parsedUrl.hostname.endsWith('.')) {
      return { isValid: false, message: 'Domain darf nicht mit einem Punkt enden' }
    }

    return { isValid: true, message: '' }
  } catch {
    return { isValid: false, message: 'Ungültiges URL-Format' }
  }
})

// Show validation feedback only after user has interacted
const showUrlValidation = computed(() => {
  return urlTouched.value && url.value.trim().length > 0
})

// ARIA announcement for screenreaders
const urlValidationAnnouncement = computed(() => {
  if (!showUrlValidation.value) return ''
  if (urlValidation.value.isValid === true) {
    return 'URL ist gültig'
  }
  if (urlValidation.value.isValid === false) {
    return `URL ungültig: ${urlValidation.value.message}`
  }
  return ''
})

// Portal detection (real-time based on URL)
const detectedPortal = computed(() => {
  if (!url.value) return null

  const urlLower = url.value.toLowerCase()

  if (urlLower.includes('stepstone.de')) {
    return { id: 'stepstone', name: 'StepStone' }
  }
  if (urlLower.includes('indeed.com') || urlLower.includes('indeed.de')) {
    return { id: 'indeed', name: 'Indeed' }
  }
  if (urlLower.includes('xing.com')) {
    return { id: 'xing', name: 'XING' }
  }
  if (urlLower.includes('arbeitsagentur.de')) {
    return { id: 'arbeitsagentur', name: 'Arbeitsagentur' }
  }

  // Generic if it looks like a URL
  if (url.value.startsWith('http')) {
    return { id: 'generic', name: 'Sonstige' }
  }

  return null
})

// Template variables computed from editable data
const templateVariables = computed(() => ({
  FIRMA: editableData.value.company,
  POSITION: editableData.value.title,
  ANSPRECHPARTNER: editableData.value.contact_person,
  STANDORT: editableData.value.location,
  QUELLE: previewData.value?.portal || ''
}))

// Can generate check
const canGenerate = computed(() => {
  return editableData.value.company && editableData.value.title
})

// Check if error is about missing documents (CV/resume/Lebenslauf)
const isDocumentMissingError = computed(() => {
  if (!error.value) return false
  const errorLower = error.value.toLowerCase()
  return errorLower.includes('lebenslauf') ||
         errorLower.includes('resume') ||
         errorLower.includes('cv') ||
         errorLower.includes('arbeitszeugnis')
})

// Check if error is about subscription limit (CORE-016-BUG-001)
const isSubscriptionLimitError = computed(() => {
  if (!error.value) return false
  const errorLower = error.value.toLowerCase()
  return errorLower.includes('limit') ||
         errorLower.includes('subscription') ||
         errorLower.includes('abonnement') ||
         errorLower.includes('kontingent')
})

// Helper to display template variable name with double braces
const getVariableDisplay = (key) => {
  return `{{${key}}}`
}

// Debounce URL input
let urlInputTimeout = null
const onUrlInput = () => {
  // Mark as touched for validation display
  urlTouched.value = true

  // Clear any existing timeout
  if (urlInputTimeout) clearTimeout(urlInputTimeout)

  // Reset preview when URL changes significantly
  if (previewData.value && url.value !== previewData.value.url) {
    previewData.value = null
    editableData.value = {
      company: '',
      title: '',
      location: '',
      employment_type: '',
      contact_person: '',
      contact_email: '',
      salary: '',
      description: ''
    }
  }
}

// Handle Enter key press in URL input
const onUrlEnterPressed = (event) => {
  // Only proceed if URL is valid and not already loading
  if (url.value && urlValidation.value.isValid === true && !loading.value && !generating.value && !previewData.value) {
    event.preventDefault()
    loadPreview()
  }
}

// Load preview data from URL
const loadPreview = async () => {
  if (!url.value) return

  error.value = ''
  loading.value = true
  tempApplicationId.value = null
  jobFitScore.value = null
  showLowScoreWarning.value = false
  analyzingRequirements.value = false
  requirementsError.value = { message: '', hint: '', isTemporary: false, showContactLink: false }
  requirementsCount.value = 0

  try {
    const { data } = await api.post('/applications/preview-job', {
      url: url.value
    })

    if (data.success) {
      previewData.value = data.data

      // Populate editable data from preview
      editableData.value = {
        company: data.data.company || '',
        title: data.data.title || '',
        location: data.data.location || '',
        employment_type: data.data.employment_type || '',
        contact_person: data.data.contact_person || '',
        contact_email: data.data.contact_email || '',
        salary: data.data.salary || '',
        description: data.data.description || ''
      }

      // Stop main loading, start requirements analysis
      loading.value = false

      if (window.$toast) {
        window.$toast('Stellenanzeige geladen!', 'success')
      }

      // Auto-analyze requirements for job-fit score (NEW-003)
      if (data.data.description) {
        await analyzeRequirementsForJobFit(
          data.data.description,
          data.data.company,
          data.data.title,
          url.value
        )
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
      loading.value = false
    }
  } catch (e) {
    // Handle different HTTP status codes appropriately
    if (e.response?.status === 400 && e.response?.data?.error) {
      // Client errors (403, 404, 429, etc.) from WebScraper - show original error message
      error.value = e.response.data.error
    } else if (e.response?.status === 500 && e.response?.data?.error) {
      // Server errors - show user-friendly message from backend
      error.value = e.response.data.error
    } else if (e.response?.data?.error) {
      // Generic case - use provided error message
      error.value = e.response.data.error
    } else {
      // Network or unknown errors
      error.value = 'Fehler beim Laden der Stellenanzeige. Bitte versuche es erneut.'
    }
    loading.value = false
  }
}

/**
 * Parse HTTP error for requirements analysis and return user-friendly error state
 */
const parseRequirementsError = (e) => {
  const status = e.response?.status
  const serverError = e.response?.data?.error

  // 5xx Server errors - temporary, can retry
  if (status >= 500) {
    return {
      message: 'Voruebergehender Serverfehler',
      hint: 'Die Anforderungsanalyse ist momentan nicht verfuegbar. Bitte versuchen Sie es spaeter erneut.',
      isTemporary: true,
      showContactLink: false
    }
  }

  // 429 - Rate limit exceeded
  if (status === 429) {
    return {
      message: 'Zu viele Anfragen',
      hint: 'Bitte warten Sie einen Moment und versuchen Sie es dann erneut.',
      isTemporary: true,
      showContactLink: false
    }
  }

  // 404 - Endpoint not found or no requirements
  if (status === 404) {
    return {
      message: 'Anforderungsanalyse nicht verfuegbar',
      hint: 'Die Stelle enthaelt keine analysierbaren Anforderungen.',
      isTemporary: false,
      showContactLink: false
    }
  }

  // Network error (no response)
  if (!e.response) {
    return {
      message: 'Netzwerkfehler',
      hint: 'Bitte pruefen Sie Ihre Internetverbindung und versuchen Sie es erneut.',
      isTemporary: true,
      showContactLink: false
    }
  }

  // Other/unknown errors
  return {
    message: serverError || 'Anforderungsanalyse nicht moeglich',
    hint: 'Falls das Problem weiterhin besteht, kontaktieren Sie bitte den Support.',
    isTemporary: false,
    showContactLink: true
  }
}

// Store description/company/title for retry functionality
const lastAnalysisParams = ref({ description: '', company: '', title: '', jobUrl: null })

// Analyze requirements for job-fit score (separate function for clear state management)
const analyzeRequirementsForJobFit = async (description, company, title, jobUrl = null) => {
  analyzingRequirements.value = true
  requirementsError.value = { message: '', hint: '', isTemporary: false, showContactLink: false }
  requirementsCount.value = 0

  // Store params for potential retry
  lastAnalysisParams.value = { description, company, title, jobUrl }

  try {
    const analyzeResponse = await api.post('/applications/analyze-job-fit', {
      url: jobUrl,
      description: description,
      company: company,
      title: title
    })

    if (analyzeResponse.data.success) {
      tempApplicationId.value = analyzeResponse.data.application_id
      requirementsCount.value = analyzeResponse.data.requirements_count || 0

      if (requirementsCount.value > 0 && window.$toast) {
        window.$toast(`${requirementsCount.value} Anforderungen analysiert`, 'success')
      }
    } else {
      requirementsError.value = {
        message: analyzeResponse.data.error || 'Anforderungsanalyse fehlgeschlagen',
        hint: '',
        isTemporary: false,
        showContactLink: true
      }
    }
  } catch (analyzeError) {
    requirementsError.value = parseRequirementsError(analyzeError)
  } finally {
    analyzingRequirements.value = false
  }
}

// Retry requirements analysis
const retryRequirementsAnalysis = () => {
  const { description, company, title, jobUrl } = lastAnalysisParams.value
  if (description) {
    analyzeRequirementsForJobFit(description, company, title, jobUrl)
  }
}

// Handle job-fit score loaded event
const onJobFitScoreLoaded = (score) => {
  jobFitScore.value = score
  showLowScoreWarning.value = score.overall_score < 40
}

// Scroll to generate button for "continue without score" action
const scrollToGenerateButton = () => {
  const generateSection = document.querySelector('.form-actions')
  if (generateSection) {
    generateSection.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// Reset preview and start fresh
const resetPreview = () => {
  previewData.value = null
  editableData.value = {
    company: '',
    title: '',
    location: '',
    employment_type: '',
    contact_person: '',
    contact_email: '',
    salary: '',
    description: ''
  }
  error.value = ''
  isManualEntry.value = false
  showManualFallback.value = false
  manualJobText.value = ''
  manualCompany.value = ''
  manualTitle.value = ''
  urlTouched.value = false
}

// Analyze manually pasted job text
const analyzeManualText = async () => {
  if (!canAnalyzeManualText.value) return

  analyzingManualText.value = true
  manualTextError.value = ''
  analyzingRequirements.value = false
  requirementsError.value = { message: '', hint: '', isTemporary: false, showContactLink: false }
  requirementsCount.value = 0

  try {
    const { data } = await api.post('/applications/analyze-manual-text', {
      job_text: manualJobText.value,
      company: manualCompany.value,
      title: manualTitle.value
    })

    if (data.success) {
      previewData.value = data.data
      isManualEntry.value = true

      // Populate editable data from analysis
      editableData.value = {
        company: data.data.company || manualCompany.value || '',
        title: data.data.title || manualTitle.value || '',
        location: data.data.location || '',
        employment_type: data.data.employment_type || '',
        contact_person: data.data.contact_person || '',
        contact_email: data.data.contact_email || '',
        salary: data.data.salary || '',
        description: data.data.description || manualJobText.value
      }

      showManualFallback.value = false
      analyzingManualText.value = false
      error.value = '' // Clear any previous error from URL loading

      if (window.$toast) {
        window.$toast('Stellentext analysiert!', 'success')
      }

      // Auto-analyze requirements for job-fit score (NEW-003)
      if (editableData.value.description) {
        await analyzeRequirementsForJobFit(
          editableData.value.description,
          editableData.value.company,
          editableData.value.title,
          null
        )
      }
    } else {
      manualTextError.value = data.error || 'Analyse fehlgeschlagen'
      analyzingManualText.value = false
    }
  } catch (e) {
    manualTextError.value = e.response?.data?.error || 'Fehler bei der Analyse'
    analyzingManualText.value = false
  }
}

// Load templates
const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const { data } = await api.get('/templates')
    templates.value = data.templates || []
  } catch (e) {
    console.error('Fehler beim Laden der Templates:', e)
  } finally {
    loadingTemplates.value = false
  }
}

// Load usage
const loadUsage = async () => {
  try {
    const { data } = await api.get('/stats')
    usage.value = data.usage
  } catch (e) {
    console.error('Fehler beim Laden der Nutzung:', e)
  }
}

const getPlanLabel = () => {
  const plan = usage.value?.plan || 'free'
  return plan.charAt(0).toUpperCase() + plan.slice(1)
}

// Generate application
const generateApplication = async () => {
  if (!canGenerate.value) return

  error.value = ''
  generating.value = true

  try {
    let response

    if (isManualEntry.value) {
      // Generate from manually entered text
      response = await api.post('/applications/generate-from-text', {
        job_text: editableData.value.description,
        company: editableData.value.company,
        title: editableData.value.title,
        template_id: selectedTemplateId.value,
        description: editableData.value.description // Include structured description for interview prep
      })
    } else {
      // Generate from URL with user-edited preview data
      response = await api.post('/applications/generate-from-url', {
        url: url.value,
        template_id: selectedTemplateId.value,
        // Include user-edited data to preserve their changes
        company: editableData.value.company,
        title: editableData.value.title,
        contact_person: editableData.value.contact_person,
        contact_email: editableData.value.contact_email,
        location: editableData.value.location,
        description: editableData.value.description
      })
    }

    const { data } = response

    if (data.success) {
      generatedApp.value = data.application
      // Reload usage after generation
      await loadUsage()
      // Reset form
      url.value = ''
      urlTouched.value = false
      previewData.value = null
      editableData.value = {
        company: '',
        title: '',
        location: '',
        employment_type: '',
        contact_person: '',
        contact_email: '',
        salary: '',
        description: ''
      }
      isManualEntry.value = false
      showManualFallback.value = false
      manualJobText.value = ''
      manualCompany.value = ''
      manualTitle.value = ''

      if (window.$toast) {
        window.$toast('Bewerbung erfolgreich generiert!', 'success')
      }
    } else {
      error.value = data.error || 'Unbekannter Fehler'
    }
  } catch (e) {
    if (e.response?.status === 403 && e.response?.data?.error_code === 'SUBSCRIPTION_LIMIT_REACHED') {
      error.value = e.response.data.error
    } else if (e.response?.data?.error) {
      error.value = e.response.data.error
    } else {
      error.value = 'Fehler bei der Generierung. Bitte versuche es erneut.'
    }
  } finally {
    generating.value = false
  }
}

const downloadPDF = async () => {
  if (!generatedApp.value?.id) return

  try {
    // Use authenticated request to fetch PDF blob
    const response = await api.get(`/applications/${generatedApp.value.id}/pdf`, {
      responseType: 'blob'
    })

    // Create download link from blob
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bewerbung_${generatedApp.value.id}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('PDF download error:', err)
    error.value = 'Fehler beim Herunterladen des PDF'
  }
}

const goToApplications = () => {
  router.push('/applications')
}

const closeModal = () => {
  generatedApp.value = null
}

// Focus trap for success modal (CORE-020-BUG-002)
const trapFocus = (e) => {
  const modal = e.currentTarget
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const firstFocusable = focusableElements[0]
  const lastFocusable = focusableElements[focusableElements.length - 1]

  if (e.shiftKey) {
    // Shift + Tab: if on first element, go to last
    if (document.activeElement === firstFocusable) {
      e.preventDefault()
      lastFocusable.focus()
    }
  } else {
    // Tab: if on last element, go to first
    if (document.activeElement === lastFocusable) {
      e.preventDefault()
      firstFocusable.focus()
    }
  }
}

// Check if user has skills for Job-Fit analysis
const checkUserSkills = async () => {
  checkingSkills.value = true
  try {
    const { data } = await api.get('/users/me/skills')
    const userSkills = data.skills || []
    hasSkills.value = userSkills.length > 0
  } catch {
    // On error, assume skills exist to not block the user
    hasSkills.value = true
  } finally {
    checkingSkills.value = false
  }
}

// Check if user has a resume/CV uploaded
const checkUserResume = async () => {
  checkingResume.value = true
  try {
    const { data } = await api.get('/documents')
    const documents = data.documents || []
    // Check if any document is of type 'lebenslauf'
    hasResume.value = documents.some(doc => doc.doc_type === 'lebenslauf')
  } catch {
    // On error, assume resume exists to not block the user
    hasResume.value = true
  } finally {
    checkingResume.value = false
  }
}

onMounted(() => {
  loadTemplates()
  loadUsage()
  checkUserSkills()
  checkUserResume()
  // Add escape key listener for modal
  document.addEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.new-application-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

/* ========================================
   PAGE HEADER
   ======================================== */
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
  margin-bottom: 0;
}

/* ========================================
   RESUME/CV MISSING WARNING BANNER
   ======================================== */
.resume-warning-section {
  max-width: 640px;
  margin-bottom: var(--space-lg);
}

.resume-warning {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-xl);
  border: 2px solid #b45050;
  background: rgba(180, 80, 80, 0.08);
}

.resume-warning-icon-box {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #b45050;
  border-radius: var(--radius-md);
  color: white;
}

.resume-warning-text-content h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 var(--space-sm) 0;
  color: #8a3a3a;
}

.resume-warning-text-content p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-lg) 0;
}

.resume-warning-text-content p strong {
  color: #b45050;
}

.resume-warning-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.resume-warning-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
}

.resume-warning-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  font-style: italic;
}

@media (max-width: 768px) {
  .resume-warning {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .resume-warning-text-content {
    text-align: center;
  }

  .resume-warning-actions {
    flex-direction: column;
    align-items: center;
  }
}

/* ========================================
   SKILLS WARNING BANNER
   ======================================== */
.skills-warning-section {
  max-width: 640px;
  margin-bottom: var(--space-lg);
}

.skills-warning {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-xl);
  border: 2px solid var(--color-ai);
  background: var(--color-ai-subtle);
}

.warning-icon-box {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai);
  border-radius: var(--radius-md);
  color: white;
}

.warning-text-content h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-sumi);
}

.warning-text-content p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-lg) 0;
}

.warning-text-content p strong {
  color: var(--color-ai);
}

.warning-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.warning-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
}

.warning-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  font-style: italic;
}

@media (max-width: 768px) {
  .skills-warning {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .warning-text-content {
    text-align: center;
  }

  .warning-actions {
    flex-direction: column;
    align-items: center;
  }
}

/* ========================================
   FORM SECTION
   ======================================== */
.form-section {
  max-width: 640px;
}

.form-card {
  padding: var(--space-xl);
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.form-label.required::after {
  content: ' *';
  color: #b45050;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.url-input-wrapper {
  position: relative;
}

.url-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-stone);
  pointer-events: none;
}

.url-input {
  padding-left: calc(var(--space-md) + 28px);
  padding-right: 130px;
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

/* URL Validation Styles */
.url-input.url-valid {
  border-color: var(--color-koke);
  box-shadow: 0 0 0 3px rgba(122, 139, 110, 0.15);
}

.url-input.url-invalid {
  border-color: #b45050;
  box-shadow: 0 0 0 3px rgba(180, 80, 80, 0.15);
}

.url-validation-icon {
  position: absolute;
  right: 100px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.url-validation-valid {
  color: var(--color-koke);
  background: rgba(122, 139, 110, 0.15);
}

.url-validation-invalid {
  color: #b45050;
  background: rgba(180, 80, 80, 0.15);
  cursor: help;
}

.url-validation-message {
  font-size: 0.8125rem;
  color: #b45050;
  margin-top: var(--space-xs);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* Screen reader only - visually hidden but accessible */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ========================================
   PORTAL BADGE
   ======================================== */
.portal-badge {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.portal-badge.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-badge.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-badge.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-badge.portal-arbeitsagentur {
  background: rgba(0, 68, 103, 0.15);
  color: #004467;
}

.portal-badge.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

/* ========================================
   PREVIEW SECTION
   ======================================== */
.preview-section {
  max-width: 800px;
}

.preview-card {
  padding: var(--space-xl);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
}

.preview-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.preview-title-row h2 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.portal-tag {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.portal-tag.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-tag.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-tag.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-tag.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.reset-btn:hover {
  background: var(--color-washi-warm);
  color: var(--color-text-primary);
}

/* ========================================
   WARNING BOX
   ======================================== */
.warning-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(201, 162, 39, 0.1);
  border: 1px solid rgba(201, 162, 39, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.warning-box svg {
  flex-shrink: 0;
  color: #c9a227;
}

.warning-box strong {
  display: block;
  color: #8a6d17;
  margin-bottom: var(--space-xs);
  font-size: 0.875rem;
}

.warning-box p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

/* ========================================
   PREVIEW FORM
   ======================================== */
.preview-form {
  margin-bottom: var(--space-lg);
}

.field-warning {
  border-color: rgba(201, 162, 39, 0.5);
  background: rgba(201, 162, 39, 0.05);
}

/* Description Toggle */
.description-group {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.description-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.description-header .form-label {
  margin-bottom: 0;
  cursor: pointer;
}

.toggle-btn {
  background: none;
  border: none;
  padding: var(--space-xs);
  cursor: pointer;
  color: var(--color-text-tertiary);
}

.toggle-icon {
  transition: transform var(--transition-base);
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.description-content {
  margin-top: var(--space-md);
}

/* ========================================
   TEMPLATE VARIABLES INFO
   ======================================== */
.template-variables-info {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  margin-top: var(--space-lg);
}

.template-variables-info svg {
  flex-shrink: 0;
  color: var(--color-ai);
  margin-top: 2px;
}

.template-variables-info strong {
  display: block;
  font-size: 0.8125rem;
  color: var(--color-sumi);
  margin-bottom: var(--space-sm);
}

.variable-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.variable-list code {
  padding: 2px var(--space-xs);
  background: var(--color-washi);
  border-radius: var(--radius-xs);
  font-size: 0.75rem;
  color: var(--color-ai);
}

.variable-list code.missing {
  color: var(--color-text-tertiary);
  opacity: 0.6;
}

/* ========================================
   TEMPLATE SELECTION
   ======================================== */
.template-selection {
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

/* ========================================
   INFO SECTION
   ======================================== */
.info-section {
  max-width: 640px;
}

.info-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
}

.info-box svg {
  flex-shrink: 0;
  color: var(--color-ai);
}

.info-content {
  font-size: 0.875rem;
  color: var(--color-sumi-light);
}

.info-content strong {
  display: block;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.info-content ul {
  margin: 0 0 var(--space-lg) 0;
  padding-left: var(--space-lg);
}

.info-content li {
  margin-bottom: var(--space-xs);
}

.supported-portals {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.portal-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.portal-item {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.portal-item.portal-stepstone {
  background: rgba(0, 102, 204, 0.15);
  color: #0066cc;
}

.portal-item.portal-indeed {
  background: rgba(46, 92, 168, 0.15);
  color: #2e5ca8;
}

.portal-item.portal-xing {
  background: rgba(0, 111, 107, 0.15);
  color: #006f6b;
}

.portal-item.portal-generic {
  background: var(--color-washi-aged);
  color: var(--color-text-tertiary);
}

/* ========================================
   FORM ACTIONS
   ======================================== */
.form-actions {
  text-align: center;
}

.preview-actions {
  margin-top: var(--space-lg);
}

.zen-btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  min-width: 240px;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.usage-info {
  margin-top: var(--space-md);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

/* ========================================
   REQUIREMENTS ANALYSIS (NEW-003)
   ======================================== */
.requirements-analyzing {
  background: var(--color-ai-subtle);
  border: 1px solid var(--color-ai-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-top: var(--space-lg);
}

.analyzing-content {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.requirements-analyzing .loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-ai-light);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.analyzing-text strong {
  display: block;
  color: var(--color-ai);
  margin-bottom: var(--space-xs);
}

.analyzing-text p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.requirements-error {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-error-light);
  border: 1px solid rgba(180, 80, 80, 0.3);
  border-radius: var(--radius-lg);
  margin-top: var(--space-lg);
}

.requirements-error.error-temporary {
  background: var(--color-warning-light);
  border: 1px solid var(--color-warning);
}

.requirements-error > svg {
  flex-shrink: 0;
  color: var(--color-error);
  margin-top: 2px;
}

.requirements-error.error-temporary > svg {
  color: var(--color-warning);
}

.requirements-error-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.requirements-error strong {
  display: block;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.requirements-error p {
  margin: 0 0 var(--space-xs) 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* Requirements Alternatives List */
.requirements-alternatives {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-md);
}

.requirements-alternatives .alternatives-header {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0 0 var(--space-sm) 0;
}

.requirements-alternatives .alternatives-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.requirements-alternatives .alternatives-list li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.requirements-alternatives .alternatives-list li svg {
  flex-shrink: 0;
  color: var(--color-koke);
}

.requirements-error-actions {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-top: var(--space-sm);
}

.requirements-retry-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: transparent;
  border: 1px solid #8a6d17;
  color: #8a6d17;
  font-size: 0.8125rem;
  padding: var(--space-xs) var(--space-sm);
}

.requirements-retry-btn:hover {
  background: rgba(201, 162, 39, 0.15);
}

.requirements-retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.requirements-continue-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: var(--color-koke);
  border: 1px solid var(--color-koke);
  color: white;
  font-size: 0.8125rem;
  padding: var(--space-xs) var(--space-sm);
}

.requirements-continue-btn:hover {
  background: var(--color-koke-dark, #5a6b4e);
}

.requirements-contact-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ai);
  text-decoration: none;
  font-size: 0.8125rem;
  font-weight: 500;
}

.requirements-contact-link:hover {
  text-decoration: underline;
}

/* ========================================
   LOW SCORE WARNING
   ======================================== */
.low-score-generate-warning {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(201, 162, 39, 0.1);
  border: 1px solid rgba(201, 162, 39, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.low-score-generate-warning svg {
  flex-shrink: 0;
  color: #c9a227;
  margin-top: 2px;
}

/* ========================================
   ERROR BOX
   ======================================== */
.error-box {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: rgba(180, 80, 80, 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid #b45050;
  margin-top: var(--space-lg);
  color: #b45050;
  font-size: 0.875rem;
}

.error-box svg {
  flex-shrink: 0;
}

/* Error with action button (document missing) */
.error-box.error-with-action {
  flex-direction: column;
  align-items: flex-start;
}

.error-box.error-with-action > svg {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
}

.error-box.error-with-action {
  position: relative;
  padding-left: calc(var(--space-md) + 28px);
}

.error-box .error-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  width: 100%;
}

.error-actions {
  margin-top: var(--space-sm);
}

.error-actions .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-ai);
  border-color: var(--color-ai);
  text-decoration: none;
}

.error-actions .zen-btn:hover {
  background-color: var(--color-ai);
  color: white;
}

/* Error with Fallback */
.error-with-fallback {
  flex-direction: column;
  align-items: flex-start;
}

.error-with-fallback > svg {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
}

.error-with-fallback {
  position: relative;
  padding-left: calc(var(--space-md) + 28px);
}

.error-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.fallback-hint {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.fallback-btn {
  margin-top: var(--space-sm);
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

/* ========================================
   MANUAL FALLBACK SECTION
   ======================================== */
.manual-fallback-section {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.fallback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.fallback-header h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0;
}

.close-fallback-btn {
  background: transparent;
  border: none;
  padding: var(--space-xs);
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.close-fallback-btn:hover {
  background: var(--color-washi);
  color: var(--color-sumi);
}

.fallback-description {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--space-lg);
}

.manual-text-area {
  min-height: 200px;
  resize: vertical;
}

/* ========================================
   MODAL
   ======================================== */
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(44, 44, 44, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.modal {
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-xl);
  border-bottom: 1px solid var(--color-border-light);
}

.success-header {
  background: rgba(122, 139, 110, 0.1);
}

.success-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-koke);
  color: white;
  border-radius: 50%;
  flex-shrink: 0;
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0 0 var(--space-xs) 0;
}

.modal-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.modal-close {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  padding: var(--space-xs);
  transition: color var(--transition-base);
}

.modal-close:hover {
  color: var(--color-sumi);
}

.modal-content {
  padding: var(--space-xl);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.detail-group {
  margin-bottom: var(--space-md);
}

.detail-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.detail-value {
  margin: 0;
  color: var(--color-sumi);
  font-size: 1rem;
}

.detail-value-block {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
}

.detail-link {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.detail-link:hover {
  text-decoration: underline;
}

.modal-footer {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-washi);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .form-card,
  .preview-card {
    padding: var(--space-lg);
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }

  .zen-btn-lg {
    width: 100%;
  }

  .url-input {
    padding-right: var(--space-md);
  }

  .url-input.url-valid,
  .url-input.url-invalid {
    padding-right: 50px;
  }

  .url-validation-icon {
    right: var(--space-md);
  }

  .portal-badge {
    position: static;
    transform: none;
    display: inline-block;
    margin-top: var(--space-sm);
  }

  .url-input-wrapper {
    display: flex;
    flex-direction: column;
  }
}
</style>
