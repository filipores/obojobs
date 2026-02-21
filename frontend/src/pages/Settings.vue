<template>
  <div class="settings-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Einstellungen</h1>
        <p class="page-subtitle">Verwalten Sie Ihr Konto und API-Zugang</p>
      </section>

      <!-- Settings Layout with Sidebar -->
      <div class="settings-layout">
        <!-- Sidebar Navigation -->
        <nav class="settings-nav animate-fade-up" aria-label="Einstellungen-Navigation">
          <ul class="nav-list" role="tablist" aria-orientation="vertical">
            <li>
              <button
                role="tab"
                :aria-selected="activeSection === 'profile'"
                :class="['nav-item', { active: activeSection === 'profile' }]"
                @click="activeSection = 'profile'"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <span>Profil</span>
              </button>
            </li>
            <li>
              <button
                role="tab"
                :aria-selected="activeSection === 'security'"
                :class="['nav-item', { active: activeSection === 'security' }]"
                @click="activeSection = 'security'"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <span>Sicherheit</span>
              </button>
            </li>
            <li>
              <button
                role="tab"
                :aria-selected="activeSection === 'integrations'"
                :class="['nav-item', { active: activeSection === 'integrations' }]"
                @click="activeSection = 'integrations'"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
                </svg>
                <span>Integrationen</span>
              </button>
            </li>
            <li>
              <button
                role="tab"
                :aria-selected="activeSection === 'danger'"
                :class="['nav-item nav-item-danger', { active: activeSection === 'danger' }]"
                @click="activeSection = 'danger'"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <span>Gefahrenzone</span>
              </button>
            </li>
          </ul>
        </nav>

        <!-- Settings Content -->
        <div class="settings-content">
          <!-- Profile Section -->
          <section v-show="activeSection === 'profile'" class="settings-section animate-fade-up">
            <div class="section-header">
              <div class="section-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h2>Profil</h2>
            </div>

            <div class="settings-card zen-card">
              <form @submit.prevent="updateProfile" class="profile-form">
                <div class="form-group">
                  <label for="full-name">Vollständiger Name</label>
                  <input
                    id="full-name"
                    v-model="profileForm.fullName"
                    type="text"
                    class="zen-input"
                    placeholder="Max Mustermann"
                    maxlength="255"
                  />
                  <p class="form-hint">Wird in Bewerbungen und offiziellen Dokumenten verwendet</p>
                </div>

                <div class="form-group">
                  <label for="display-name">Anzeigename (optional)</label>
                  <input
                    id="display-name"
                    v-model="profileForm.displayName"
                    type="text"
                    class="zen-input"
                    placeholder="Max"
                    maxlength="100"
                  />
                  <p class="form-hint">Wird in der App-Oberfläche angezeigt</p>
                </div>

                <div class="form-divider"></div>
                <p class="form-section-label">Kontaktdaten für Bewerbungen</p>

                <div class="form-group">
                  <label for="phone">Telefonnummer</label>
                  <input
                    id="phone"
                    v-model="profileForm.phone"
                    type="tel"
                    class="zen-input"
                    placeholder="+49 170 1234567"
                    maxlength="50"
                  />
                  <p class="form-hint">Wird im Briefkopf und in E-Mail-Signaturen verwendet</p>
                </div>

                <div class="form-group">
                  <label for="address">Straße und Hausnummer</label>
                  <input
                    id="address"
                    v-model="profileForm.address"
                    type="text"
                    class="zen-input"
                    placeholder="Musterstraße 42"
                    maxlength="255"
                  />
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label for="postal-code">PLZ</label>
                    <input
                      id="postal-code"
                      v-model="profileForm.postalCode"
                      type="text"
                      class="zen-input"
                      placeholder="80331"
                      maxlength="20"
                    />
                  </div>

                  <div class="form-group">
                    <label for="city">Stadt</label>
                    <input
                      id="city"
                      v-model="profileForm.city"
                      type="text"
                      class="zen-input"
                      placeholder="München"
                      maxlength="100"
                    />
                  </div>
                </div>

                <div class="form-group">
                  <label for="website">Website (optional)</label>
                  <input
                    id="website"
                    v-model="profileForm.website"
                    type="url"
                    class="zen-input"
                    placeholder="www.maxmustermann.de"
                    maxlength="255"
                  />
                  <p class="form-hint">Persönliche Website oder Portfolio</p>
                </div>

                <div class="form-divider"></div>
                <p class="form-section-label">Jobsuche-Präferenzen</p>

                <div class="form-group">
                  <label for="preferred-location">Bevorzugter Standort</label>
                  <input
                    id="preferred-location"
                    v-model="profileForm.preferredLocation"
                    type="text"
                    class="zen-input"
                    placeholder="z.B. Berlin, München"
                    maxlength="255"
                  />
                </div>

                <div class="form-group">
                  <label for="preferred-working-time">Bevorzugte Arbeitszeit</label>
                  <select
                    id="preferred-working-time"
                    v-model="profileForm.preferredWorkingTime"
                    class="zen-input"
                  >
                    <option value="">Keine Präferenz</option>
                    <option value="vz">Vollzeit</option>
                    <option value="tz">Teilzeit</option>
                    <option value="ho">Remote</option>
                  </select>
                  <p class="form-hint">Wird für automatische Jobvorschläge alle 6 Stunden verwendet</p>
                </div>

                <div v-if="profileError" class="profile-error-message">
                  {{ profileError }}
                </div>

                <div v-if="profileSuccess" class="profile-success-message">
                  {{ profileSuccess }}
                </div>

                <button
                  type="submit"
                  class="zen-btn zen-btn-filled"
                  :disabled="isUpdatingProfile || !hasProfileChanges"
                >
                  {{ isUpdatingProfile ? 'Wird gespeichert...' : 'Profil speichern' }}
                </button>
              </form>
            </div>

            <!-- Ink Stroke -->
            <div class="ink-stroke"></div>

            <!-- Account Section -->
            <div class="settings-subsection">
              <div class="section-header">
                <div class="section-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M9 9h6v6H9z"/>
                  </svg>
                </div>
                <h2>Konto</h2>
              </div>

              <div class="settings-card zen-card">
                <div class="account-info">
                  <div class="info-row">
                    <span class="info-label">E-Mail</span>
                    <span class="info-value">{{ authStore.user?.email }}</span>
                  </div>
                  <div class="info-divider"></div>
                  <div class="info-row">
                    <span class="info-label">Aktueller Plan</span>
                    <span class="info-value info-value-highlight">{{ getPlanLabel() }}</span>
                  </div>
                </div>

                <div class="account-actions">
                  <router-link to="/subscription" class="zen-btn zen-btn-ai">
                    Abo verwalten
                  </router-link>
                </div>
              </div>
            </div>
          </section>

          <!-- Security Section -->
          <section v-show="activeSection === 'security'" class="settings-section animate-fade-up">
            <div class="section-header">
              <div class="section-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </div>
              <h2>Passwort ändern</h2>
            </div>

            <div class="settings-card zen-card">
              <form @submit.prevent="changePassword" class="password-change-form">
                <!-- Hidden username field for accessibility and password manager support -->
                <input
                  type="text"
                  :value="authStore.user?.email"
                  autocomplete="username"
                  class="sr-only"
                  tabindex="-1"
                  aria-hidden="true"
                  readonly
                />
                <div class="form-group">
                  <label for="current-password" class="required">Aktuelles Passwort</label>
                  <input
                    id="current-password"
                    v-model="passwordForm.currentPassword"
                    type="password"
                    class="zen-input"
                    required
                    aria-required="true"
                    autocomplete="current-password"
                  />
                </div>

                <div class="form-group">
                  <label for="new-password" class="required">Neues Passwort</label>
                  <input
                    id="new-password"
                    v-model="passwordForm.newPassword"
                    type="password"
                    class="zen-input"
                    @input="validatePassword"
                    required
                    aria-required="true"
                    autocomplete="new-password"
                  />
                  <!-- Password Requirements -->
                  <div v-if="passwordForm.newPassword" class="password-requirements" aria-live="polite" aria-atomic="false">
                    <div
                      v-for="req in passwordRequirements"
                      :key="req.key"
                      class="requirement-item"
                      :class="{ 'met': passwordChecks[req.key] }"
                      :aria-label="passwordChecks[req.key] ? `Erfüllt: ${req.label}` : `Nicht erfüllt: ${req.label}`"
                    >
                      <svg v-if="passwordChecks[req.key]" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"/>
                      </svg>
                      <span>{{ req.label }}</span>
                    </div>
                  </div>
                </div>

                <div class="form-group">
                  <label for="confirm-password" class="required">Neues Passwort bestätigen</label>
                  <input
                    id="confirm-password"
                    v-model="passwordForm.confirmPassword"
                    type="password"
                    class="zen-input"
                    required
                    aria-required="true"
                    autocomplete="new-password"
                  />
                  <p v-if="passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword" class="form-error">
                    Passwörter stimmen nicht überein
                  </p>
                </div>

                <!-- General validation messages for when button is disabled -->
                <div v-if="showPasswordValidationMessages" class="password-validation-messages">
                  <p v-if="passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword" class="form-error">
                    Passwörter stimmen nicht überein
                  </p>
                  <p v-if="passwordForm.newPassword && !allPasswordRequirementsMet" class="form-error">
                    Passwort erfüllt nicht alle Anforderungen
                  </p>
                  <p v-if="(!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) && (passwordForm.currentPassword || passwordForm.newPassword || passwordForm.confirmPassword)" class="form-error">
                    Bitte füllen Sie alle Felder aus
                  </p>
                </div>

                <div v-if="passwordError" class="password-error-message">
                  {{ passwordError }}
                </div>

                <button
                  type="submit"
                  class="zen-btn"
                  :disabled="!canSubmitPassword || isChangingPassword"
                >
                  {{ isChangingPassword ? 'Wird geändert...' : 'Passwort ändern' }}
                </button>
              </form>
            </div>
          </section>

          <!-- Integrations Section -->
          <section v-show="activeSection === 'integrations'" class="settings-section animate-fade-up">
            <!-- Email Accounts -->
            <div class="section-header">
              <div class="section-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
              </div>
              <div>
                <h2>E-Mail-Konto verbinden</h2>
                <p class="section-description">Bewerbungen direkt aus der App versenden</p>
              </div>
            </div>

            <div class="settings-card zen-card">
              <!-- Connected Accounts -->
              <div v-if="emailAccounts.length" class="email-accounts-list">
                <div class="list-header">
                  <span>Verbundene Konten</span>
                </div>
                <div class="accounts-table">
                  <div v-for="account in emailAccounts" :key="account.id" class="account-row">
                    <div class="account-info">
                      <div class="provider-icon" :class="account.provider">
                        <!-- Gmail Icon -->
                        <svg v-if="account.provider === 'gmail'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M20 18h-2V9.25L12 13 6 9.25V18H4V6h1.2l6.8 4.25L18.8 6H20m0-2H4c-1.11 0-2 .89-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z"/>
                        </svg>
                        <!-- Outlook Icon -->
                        <svg v-else-if="account.provider === 'outlook'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M7.88 12.04q0 .45-.11.87-.1.41-.33.74-.22.33-.58.52-.37.2-.87.2t-.85-.2q-.35-.21-.57-.55-.22-.33-.33-.75-.1-.42-.1-.86t.1-.87q.1-.43.34-.76.22-.34.59-.54.36-.2.87-.2t.86.2q.35.21.57.55.22.34.31.77.1.43.1.88zM24 12v9.38q0 .46-.33.8-.33.32-.8.32H7.13q-.46 0-.8-.33-.32-.33-.32-.8V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h6.5V2.38q0-.46.33-.8.33-.32.8-.32h14.74q.46 0 .8.33.32.33.32.8V12zM7.5 18H1V7h6.5v11z"/>
                        </svg>
                      </div>
                      <div class="account-details">
                        <span class="account-email">{{ account.email }}</span>
                        <span class="account-provider">{{ account.provider === 'gmail' ? 'Gmail' : 'Outlook' }}</span>
                      </div>
                    </div>
                    <div class="account-status">
                      <span class="status-badge connected">Verbunden</span>
                      <button @click="disconnectAccount(account.id)" class="zen-btn zen-btn-sm zen-btn-danger">
                        Trennen
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- No accounts connected -->
              <div v-else class="no-accounts">
                <p>Noch kein E-Mail-Konto verbunden.</p>
              </div>

              <!-- Connect Buttons -->
              <div class="connect-buttons">
                <button @click="connectGmail" class="connect-btn gmail"
                  :disabled="isConnecting || !integrationStatus.gmail.configured"
                  :title="!integrationStatus.gmail.configured ? 'Gmail-Integration ist nicht konfiguriert' : 'Mit Gmail verbinden'">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20 18h-2V9.25L12 13 6 9.25V18H4V6h1.2l6.8 4.25L18.8 6H20m0-2H4c-1.11 0-2 .89-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z"/>
                  </svg>
                  <span>Mit Gmail verbinden</span>
                  <span v-if="!integrationStatus.gmail.configured" class="config-status">(nicht konfiguriert)</span>
                </button>
                <button @click="connectOutlook" class="connect-btn outlook"
                  :disabled="isConnecting || !integrationStatus.outlook.configured"
                  :title="!integrationStatus.outlook.configured ? 'Outlook-Integration ist nicht konfiguriert' : 'Mit Outlook verbinden'">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7.88 12.04q0 .45-.11.87-.1.41-.33.74-.22.33-.58.52-.37.2-.87.2t-.85-.2q-.35-.21-.57-.55-.22-.33-.33-.75-.1-.42-.1-.86t.1-.87q.1-.43.34-.76.22-.34.59-.54.36-.2.87-.2t.86.2q.35.21.57.55.22.34.31.77.1.43.1.88zM24 12v9.38q0 .46-.33.8-.33.32-.8.32H7.13q-.46 0-.8-.33-.32-.33-.32-.8V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h6.5V2.38q0-.46.33-.8.33-.32.8-.32h14.74q.46 0 .8.33.32.33.32.8V12z"/>
                  </svg>
                  <span>Mit Outlook verbinden</span>
                  <span v-if="!integrationStatus.outlook.configured" class="config-status">(nicht konfiguriert)</span>
                </button>
              </div>
            </div>

            <!-- Ink Stroke -->
            <div class="ink-stroke"></div>

            <!-- API Keys Section -->
            <div class="settings-subsection">
              <div class="section-header">
                <div class="section-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
                  </svg>
                </div>
                <div>
                  <h2>API Keys</h2>
                  <p class="section-description">Für die Chrome Extension</p>
                </div>
              </div>

              <div class="settings-card zen-card">
                <div class="api-key-header">
                  <p class="api-key-info">
                    Erstellen Sie einen API Key, um die Chrome Extension mit Ihrem Konto zu verbinden.
                  </p>
                  <button @click="generateKey" class="zen-btn" :disabled="isGeneratingKey">
                    {{ isGeneratingKey ? 'Wird generiert...' : 'Neuen Key generieren' }}
                  </button>
                </div>

                <!-- New Key Alert -->
                <div v-if="newKey" class="new-key-alert">
                  <div class="alert-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                      <line x1="12" y1="9" x2="12" y2="13"/>
                      <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    <strong>Speichern Sie diesen Key jetzt!</strong>
                  </div>
                  <p>Er wird nicht erneut angezeigt.</p>
                  <div class="key-display">
                    <code>{{ newKey }}</code>
                    <button @click="copyKey" class="copy-btn" title="Kopieren">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- Existing Keys -->
                <div v-if="apiKeys.length" class="api-keys-list">
                  <div class="list-header">
                    <span>Ihre API Keys</span>
                  </div>
                  <div class="keys-table">
                    <div v-for="key in apiKeys" :key="key.id" class="key-row">
                      <div class="key-info">
                        <span class="key-prefix">{{ key.key_prefix }}...</span>
                        <span class="key-meta">
                          <span class="key-name">{{ key.name }}</span>
                          <span class="key-date">{{ formatDate(key.created_at) }}</span>
                        </span>
                      </div>
                      <button @click="deleteKey(key.id)" class="zen-btn zen-btn-sm zen-btn-danger" aria-label="API Key löschen" title="API Key löschen">
                        Löschen
                      </button>
                    </div>
                  </div>
                </div>

                <div v-else class="no-keys">
                  <p>Sie haben noch keine API Keys erstellt.</p>
                </div>
              </div>

              <!-- Chrome Extension Info -->
              <div class="info-section">
                <div class="info-banner zen-card">
                  <div class="info-icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" y1="16" x2="12" y2="12"/>
                      <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                  </div>
                  <div class="info-content">
                    <h3>Chrome Extension einrichten</h3>
                    <ol class="setup-steps">
                      <li>Erstellen Sie einen API Key oben</li>
                      <li>Installieren Sie die Chrome Extension</li>
                      <li>Fügen Sie den API Key in der Extension ein</li>
                      <li>Besuchen Sie eine Stellenanzeige und klicken Sie auf "Bewerbung generieren"</li>
                    </ol>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Danger Zone Section -->
          <section v-show="activeSection === 'danger'" class="settings-section animate-fade-up">
            <div class="section-header">
              <div class="section-icon section-icon-danger">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div>
                <h2>Gefahrenzone</h2>
                <p class="section-description">Irreversible Aktionen</p>
              </div>
            </div>

            <div class="settings-card zen-card danger-card">
              <div class="danger-action">
                <div class="danger-info">
                  <h3>Konto löschen</h3>
                  <p>Löscht Ihr Konto und alle zugehörigen Daten unwiderruflich. Diese Aktion kann nicht rückgängig gemacht werden.</p>
                </div>
                <button class="zen-btn zen-btn-danger" @click="requestAccountDeletion">
                  Konto löschen
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import { authStore } from '../stores/auth'
import { confirm } from '../composables/useConfirm'
import { getFullLocale } from '../i18n'
import { validatePassword as validatePasswordUtil, isPasswordValid as isPasswordValidUtil } from '../utils/validation'

const _router = useRouter()

// Active settings section
const activeSection = ref('profile')

const apiKeys = ref([])
const newKey = ref('')

const getPlanLabel = () => {
  const subscription = authStore.user?.subscription
  if (!subscription) return 'Free'
  return subscription.plan?.charAt(0).toUpperCase() + subscription.plan?.slice(1) || 'Free'
}

// API Key generation state
const isGeneratingKey = ref(false)

// Email accounts state
const emailAccounts = ref([])
const isConnecting = ref(false)
const oauthPollTimer = ref(null)

// Integration status
const integrationStatus = ref({
  gmail: { configured: false },
  outlook: { configured: false }
})

// Profile field mapping: formKey -> API/user property key
const profileFieldMap = {
  fullName: 'full_name',
  displayName: 'display_name',
  phone: 'phone',
  address: 'address',
  city: 'city',
  postalCode: 'postal_code',
  website: 'website',
  preferredLocation: 'preferred_location',
  preferredWorkingTime: 'preferred_working_time'
}
const profileFieldKeys = Object.keys(profileFieldMap)

// Profile form state
const profileForm = reactive(Object.fromEntries(profileFieldKeys.map(k => [k, ''])))
const originalProfile = reactive(Object.fromEntries(profileFieldKeys.map(k => [k, ''])))
const isUpdatingProfile = ref(false)
const profileError = ref('')
const profileSuccess = ref('')

const hasProfileChanges = computed(() => {
  return profileFieldKeys.some(key => profileForm[key] !== originalProfile[key])
})

const initProfileForm = () => {
  const user = authStore.user
  for (const key of profileFieldKeys) {
    const apiKey = profileFieldMap[key]
    const value = user?.[apiKey] || ''
    profileForm[key] = value
    originalProfile[key] = value
  }
}

const updateProfile = async () => {
  if (!hasProfileChanges.value) return

  isUpdatingProfile.value = true
  profileError.value = ''
  profileSuccess.value = ''

  try {
    const payload = Object.fromEntries(
      profileFieldKeys.map(key => [profileFieldMap[key], profileForm[key]])
    )
    const { data } = await api.put('/auth/profile', payload)

    authStore.user = data.user
    localStorage.setItem('user', JSON.stringify(data.user))

    for (const key of profileFieldKeys) {
      originalProfile[key] = profileForm[key]
    }

    profileSuccess.value = 'Profil erfolgreich aktualisiert'

    setTimeout(() => {
      profileSuccess.value = ''
    }, 3000)
  } catch (e) {
    profileError.value = e.response?.data?.error || 'Fehler beim Aktualisieren des Profils'
  } finally {
    isUpdatingProfile.value = false
  }
}

// Password change form state
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordChecks = reactive({
  min_length: false,
  has_uppercase: false,
  has_lowercase: false,
  has_number: false
})
const passwordRequirements = ref([
  { key: 'min_length', label: 'Mindestens 8 Zeichen' },
  { key: 'has_uppercase', label: 'Mindestens ein Großbuchstabe (A-Z)' },
  { key: 'has_lowercase', label: 'Mindestens ein Kleinbuchstabe (a-z)' },
  { key: 'has_number', label: 'Mindestens eine Zahl (0-9)' }
])
const isChangingPassword = ref(false)
const passwordError = ref('')

const allPasswordRequirementsMet = computed(() => {
  return isPasswordValidUtil(passwordChecks)
})

const showPasswordValidationMessages = computed(() => {
  // Show validation messages when user has started entering data but button is disabled
  const hasAnyInput = passwordForm.currentPassword || passwordForm.newPassword || passwordForm.confirmPassword
  return hasAnyInput && !canSubmitPassword.value && !isChangingPassword.value
})

const canSubmitPassword = computed(() => {
  return (
    passwordForm.currentPassword &&
    passwordForm.newPassword &&
    passwordForm.confirmPassword &&
    passwordForm.newPassword === passwordForm.confirmPassword &&
    isPasswordValidUtil(passwordChecks)
  )
})

const validatePassword = () => {
  const validationResults = validatePasswordUtil(passwordForm.newPassword)
  Object.assign(passwordChecks, validationResults)
}

const changePassword = async () => {
  if (!canSubmitPassword.value) return

  isChangingPassword.value = true
  passwordError.value = ''

  try {
    await api.put('/auth/change-password', {
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    })

    // Reset form
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    Object.keys(passwordChecks).forEach(key => {
      passwordChecks[key] = false
    })

    if (window.$toast) {
      window.$toast('Passwort erfolgreich geändert!', 'success')
    }
  } catch (e) {
    passwordError.value = e.response?.data?.error || 'Fehler beim Ändern des Passworts'
  } finally {
    isChangingPassword.value = false
  }
}

const generateKey = async () => {
  if (isGeneratingKey.value) return

  isGeneratingKey.value = true
  try {
    const { data } = await api.post('/keys', { name: 'Chrome Extension' })
    newKey.value = data.api_key
    loadKeys()
  } catch (_e) {
    if (window.$toast) {
      window.$toast('Fehler beim Erstellen des Keys', 'error')
    }
  } finally {
    isGeneratingKey.value = false
  }
}

const copyKey = async () => {
  try {
    await navigator.clipboard.writeText(newKey.value)
    if (window.$toast) {
      window.$toast('API Key kopiert!', 'success')
    }
  } catch {
    if (window.$toast) {
      window.$toast('Kopieren fehlgeschlagen. Bitte manuell kopieren.', 'error')
    }
  }
}

const deleteKey = async (id) => {
  const confirmed = await confirm({
    title: 'API Key löschen',
    message: 'Möchten Sie den API Key wirklich löschen? Die Chrome Extension funktioniert dann nicht mehr.',
    confirmText: 'Löschen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/keys/${id}`)
    loadKeys()
  } catch (_e) {
    if (window.$toast) { window.$toast('Fehler beim Löschen', 'error') }
  }
}

const loadKeys = async () => {
  try {
    const { data } = await api.get('/keys')
    apiKeys.value = data.api_keys
  } catch { /* ignore */ }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

// Email account functions
const loadEmailAccounts = async () => {
  try {
    const { data } = await api.get('/email/accounts')
    emailAccounts.value = data.data
  } catch { /* ignore */ }
}

const loadIntegrationStatus = async () => {
  try {
    const { data } = await api.get('/email/integration-status')
    integrationStatus.value = data.data
  } catch { /* ignore */ }
}

const connectGmail = async () => {
  // Check if Gmail integration is configured
  if (!integrationStatus.value.gmail.configured) {
    if (window.$toast) {
      window.$toast('Gmail-Integration ist derzeit nicht konfiguriert.', 'warning')
    }
    return
  }

  isConnecting.value = true
  try {
    const { data } = await api.get('/email/gmail/auth-url')
    // Open OAuth popup
    const popup = window.open(
      data.authorization_url,
      'gmail-oauth',
      'width=600,height=700,scrollbars=yes'
    )
    // Poll for popup close and reload accounts
    oauthPollTimer.value = setInterval(() => {
      if (popup && popup.closed) {
        clearInterval(oauthPollTimer.value)
        oauthPollTimer.value = null
        isConnecting.value = false
        loadEmailAccounts()
      }
    }, 500)
  } catch (_err) {
    isConnecting.value = false
    // Error message is handled by api client interceptor
  }
}

const connectOutlook = async () => {
  // Check if Outlook integration is configured
  if (!integrationStatus.value.outlook.configured) {
    if (window.$toast) {
      window.$toast('Outlook-Integration ist derzeit nicht konfiguriert.', 'warning')
    }
    return
  }

  isConnecting.value = true
  try {
    const { data } = await api.get('/email/outlook/auth-url')
    // Open OAuth popup
    const popup = window.open(
      data.authorization_url,
      'outlook-oauth',
      'width=600,height=700,scrollbars=yes'
    )
    // Poll for popup close and reload accounts
    oauthPollTimer.value = setInterval(() => {
      if (popup && popup.closed) {
        clearInterval(oauthPollTimer.value)
        oauthPollTimer.value = null
        isConnecting.value = false
        loadEmailAccounts()
      }
    }, 500)
  } catch (_err) {
    isConnecting.value = false
    // Error message is handled by api client interceptor
  }
}

const disconnectAccount = async (accountId) => {
  const confirmed = await confirm({
    title: 'E-Mail-Konto trennen',
    message: 'Möchten Sie das E-Mail-Konto wirklich trennen? Sie können dann keine Bewerbungen mehr über dieses Konto versenden.',
    confirmText: 'Trennen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/email/accounts/${accountId}`)
    loadEmailAccounts()
    if (window.$toast) {
      window.$toast('E-Mail-Konto getrennt', 'success')
    }
  } catch (_err) {
    if (window.$toast) {
      window.$toast('Fehler beim Trennen des Kontos', 'error')
    }
  }
}

const requestAccountDeletion = async () => {
  const confirmed = await confirm({
    title: 'Konto löschen',
    message: 'Sind Sie sicher, dass Sie Ihr Konto und alle zugehörigen Daten unwiderruflich löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.',
    confirmText: 'Endgültig löschen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete('/auth/delete-account')

    // Account successfully deleted - user gets logged out automatically
    // Clear local storage and redirect
    localStorage.removeItem('token')
    authStore.logout()

    if (window.$toast) {
      window.$toast('Ihr Konto wurde erfolgreich gelöscht.', 'success')
    }

    // Redirect to home page after a brief delay
    setTimeout(() => {
      _router.push('/')
    }, 1000)

  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Fehler beim Löschen des Kontos'
    if (window.$toast) {
      window.$toast(errorMsg, 'error')
    }
  }
}

onMounted(async () => {
  loadKeys()
  loadEmailAccounts()
  loadIntegrationStatus()
  await authStore.fetchUser()
  initProfileForm()
})

onUnmounted(() => {
  // Clear OAuth poll timer to prevent memory leaks
  if (oauthPollTimer.value) {
    clearInterval(oauthPollTimer.value)
    oauthPollTimer.value = null
  }
})
</script>

<style scoped>
.settings-page {
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
   SETTINGS LAYOUT
   ======================================== */
.settings-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: var(--space-xl);
  align-items: start;
}

/* ========================================
   SETTINGS NAVIGATION
   ======================================== */
.settings-nav {
  position: sticky;
  top: calc(73px + var(--space-lg));
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  box-shadow: var(--shadow-paper);
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
  text-align: left;
}

.nav-item:hover {
  background: var(--color-washi);
  color: var(--color-sumi);
}

.nav-item.active {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.nav-item svg {
  flex-shrink: 0;
}

.nav-item-danger {
  color: var(--color-terra);
}

.nav-item-danger:hover {
  background: rgba(184, 122, 94, 0.1);
  color: var(--color-terra);
}

.nav-item-danger.active {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

/* ========================================
   SETTINGS CONTENT
   ======================================== */
.settings-content {
  min-width: 0;
}

/* ========================================
   SETTINGS SECTION
   ======================================== */
.settings-section {
  margin-bottom: var(--space-ma);
}

.settings-subsection {
  margin-top: var(--space-lg);
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.section-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
}

.section-description {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
  margin: var(--space-xs) 0 0 0;
}

.settings-card {
  padding: var(--space-xl);
}

/* ========================================
   ACCOUNT INFO
   ======================================== */
.account-info {
  margin-bottom: var(--space-lg);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) 0;
  gap: var(--space-md);
}

@media (max-width: 375px) {
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }
}

.info-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
  flex-shrink: 0;
}

.info-value {
  font-weight: 500;
  color: var(--color-sumi);
}

.info-value-highlight {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--color-ai);
}

.info-divider {
  height: 1px;
  background: var(--color-border-light);
  margin: var(--space-sm) 0;
}

.account-actions {
  display: flex;
  gap: var(--space-md);
}

/* ========================================
   API KEYS SECTION
   ======================================== */
.api-key-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.api-key-info {
  color: var(--color-text-secondary);
  margin: 0;
  flex: 1;
}

/* New Key Alert */
.new-key-alert {
  background: rgba(184, 122, 94, 0.1);
  border: 1px solid var(--color-terra);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.alert-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-terra);
  margin-bottom: var(--space-sm);
}

.new-key-alert p {
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-md) 0;
  font-size: 0.9375rem;
}

.key-display {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
}

.key-display code {
  flex: 1;
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--color-sumi);
  word-break: break-all;
}

.copy-btn {
  background: none;
  border: none;
  color: var(--color-ai);
  cursor: pointer;
  padding: var(--space-xs);
  transition: color var(--transition-base);
}

.copy-btn:hover {
  color: var(--color-ai-light);
}

/* Keys List */
.api-keys-list {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-lg);
}

.list-header {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-md);
}

.keys-table {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.key-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
}

.key-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.key-prefix {
  font-family: var(--font-mono);
  font-size: 0.9375rem;
  color: var(--color-sumi);
  font-weight: 500;
}

.key-meta {
  display: flex;
  gap: var(--space-md);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.no-keys {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-tertiary);
}

.no-keys p {
  margin: 0;
}

/* ========================================
   EMAIL ACCOUNTS SECTION
   ======================================== */
.email-accounts-list {
  margin-bottom: var(--space-lg);
}

.accounts-table {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.account-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
}

.account-info {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.provider-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.provider-icon.gmail {
  background: rgba(219, 68, 55, 0.1);
  color: #DB4437;
}

.provider-icon.outlook {
  background: rgba(0, 120, 212, 0.1);
  color: #0078D4;
}

.account-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.account-email {
  font-weight: 500;
  color: var(--color-sumi);
}

.account-provider {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.account-status {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.status-badge {
  font-size: 0.75rem;
  font-weight: 500;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

.status-badge.connected {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.no-accounts {
  text-align: center;
  padding: var(--space-lg);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-lg);
}

.no-accounts p {
  margin: 0;
}

.connect-buttons {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.connect-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-elevated);
  color: var(--color-sumi);
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
}

.connect-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lifted);
}

.connect-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.connect-btn.gmail:hover:not(:disabled) {
  border-color: #DB4437;
  color: #DB4437;
}

.connect-btn.outlook:hover:not(:disabled) {
  border-color: #0078D4;
  color: #0078D4;
}

.config-status {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-left: var(--space-xs);
}

/* ========================================
   PASSWORD CHANGE FORM
   ======================================== */
.password-change-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  max-width: 400px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.form-group label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.form-group label.required::after {
  content: ' *';
  color: #b45050;
}

.zen-input {
  width: 100%;
  padding: var(--space-md);
  font-size: 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-washi);
  color: var(--color-sumi);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.zen-input:focus {
  outline: none;
  border-color: var(--color-ai);
  box-shadow: 0 0 0 3px rgba(61, 90, 108, 0.1);
}

.password-requirements {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  transition: color var(--transition-base);
}

.requirement-item.met {
  color: var(--color-koke);
}

.requirement-item svg {
  flex-shrink: 0;
}

.form-error {
  font-size: 0.8125rem;
  color: var(--color-terra);
  margin: 0;
}

.password-error-message {
  padding: var(--space-md);
  background: rgba(184, 122, 94, 0.1);
  border: 1px solid var(--color-terra);
  border-radius: var(--radius-sm);
  color: var(--color-terra);
  font-size: 0.9375rem;
}

.password-change-form .zen-btn {
  align-self: flex-start;
  margin-top: var(--space-sm);
}

.password-change-form .zen-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.password-validation-messages {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.password-validation-messages .form-error {
  margin: 0;
}

/* ========================================
   PROFILE FORM
   ======================================== */
.profile-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  max-width: 400px;
}

.profile-form .form-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin: var(--space-xs) 0 0 0;
}

.form-divider {
  height: 1px;
  background: var(--color-border-light);
  margin: var(--space-sm) 0;
}

.form-section-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--space-md);
}

.profile-error-message {
  padding: var(--space-md);
  background: rgba(184, 122, 94, 0.1);
  border: 1px solid var(--color-terra);
  border-radius: var(--radius-sm);
  color: var(--color-terra);
  font-size: 0.9375rem;
}

.profile-success-message {
  padding: var(--space-md);
  background: rgba(122, 139, 110, 0.1);
  border: 1px solid var(--color-koke);
  border-radius: var(--radius-sm);
  color: var(--color-koke);
  font-size: 0.9375rem;
}

.profile-form .zen-btn {
  align-self: flex-start;
  margin-top: var(--space-sm);
}

.profile-form .zen-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ========================================
   INFO SECTION
   ======================================== */
.info-section {
  margin-top: var(--space-ma);
}

.info-banner {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-xl);
  background: var(--color-ai-subtle);
  border: 1px solid rgba(61, 90, 108, 0.15);
}

.info-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.info-content h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 var(--space-md) 0;
}

.setup-steps {
  margin: 0;
  padding-left: var(--space-lg);
  color: var(--color-text-secondary);
}

.setup-steps li {
  margin-bottom: var(--space-sm);
  line-height: var(--leading-relaxed);
}

.setup-steps li:last-child {
  margin-bottom: 0;
}

/* ========================================
   DANGER ZONE
   ======================================== */
.section-icon-danger {
  background: rgba(184, 122, 94, 0.1);
  color: var(--color-terra);
}

.danger-card {
  border: 1px solid rgba(184, 122, 94, 0.3);
}

.danger-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-lg);
}

.danger-info h3 {
  font-size: 1rem;
  font-weight: 500;
  margin: 0 0 var(--space-xs) 0;
  color: var(--color-sumi);
}

.danger-info p {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 900px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }

  .settings-nav {
    position: relative;
    top: 0;
  }

  .nav-list {
    flex-direction: row;
    flex-wrap: wrap;
    gap: var(--space-sm);
  }

  .nav-item {
    flex: 1 1 auto;
    min-width: fit-content;
    min-height: 44px;
    justify-content: center;
    padding: var(--space-sm) var(--space-md);
  }
}

@media (max-width: 768px) {
  .api-key-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .key-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .info-banner {
    flex-direction: column;
  }

  .account-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .account-status {
    width: 100%;
    justify-content: space-between;
  }

  .connect-buttons {
    flex-direction: column;
  }

  .connect-btn {
    width: 100%;
    justify-content: center;
  }

  .danger-action {
    flex-direction: column;
    align-items: flex-start;
  }

  .danger-action .zen-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .section-header {
    flex-direction: column;
  }

  .nav-item span {
    display: none;
  }

  .nav-item {
    padding: var(--space-sm);
    min-width: auto;
  }
}
</style>
