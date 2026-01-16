<template>
  <div class="settings-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>Einstellungen</h1>
        <p class="page-subtitle">Verwalten Sie Ihr Konto und API-Zugang</p>
      </section>

      <!-- Profile Section -->
      <section class="settings-section animate-fade-up" style="animation-delay: 100ms;">
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
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Account Section -->
      <section class="settings-section animate-fade-up" style="animation-delay: 125ms;">
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
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Email Accounts Section -->
      <section class="settings-section animate-fade-up" style="animation-delay: 125ms;">
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
                      <path d="M7.88 12.04q0 .45-.11.87-.1.41-.33.74-.22.33-.58.52-.37.2-.87.2t-.85-.2q-.35-.21-.57-.55-.22-.33-.33-.75-.1-.42-.1-.86t.1-.87q.1-.43.34-.76.22-.34.59-.54.36-.2.87-.2t.86.2q.35.21.57.55.22.34.31.77.1.43.1.88zM24 12v9.38q0 .46-.33.8-.33.32-.8.32H7.13q-.46 0-.8-.33-.32-.33-.32-.8V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h6.5V2.38q0-.46.33-.8.33-.32.8-.32h14.74q.46 0 .8.33.32.33.32.8V12zM7.5 18H1V7h6.5v11zm-5.65-6q0 .28.06.55.08.27.22.51.15.24.38.44.24.2.57.35-.2.3-.41.62-.22.32-.41.62-.2.32-.34.61-.14.3-.15.55-.01.25.17.47.2.22.46.22.39 0 .55-.36.1-.24.19-.5.1-.24.19-.46.1-.22.15-.37.05-.16.05-.19h-.02q.09.08.21.17.1.09.2.17l.03.02q.18.16.32.26.1.09.2.14.13.07.24.07.21 0 .37-.16.17-.17.17-.37 0-.16-.08-.27-.08-.12-.23-.21-.15-.1-.36-.17-.21-.08-.47-.12-.15-.02-.24-.04-.1-.03-.17-.07-.08-.05-.14-.13-.06-.09-.06-.22 0-.13.06-.23.06-.11.14-.2.09-.09.2-.17.1-.09.19-.17-.2 0-.32-.01-.12-.02-.23-.07-.1-.06-.18-.16-.09-.1-.14-.25-.04-.15-.04-.35 0-.26.08-.51.09-.26.26-.48.17-.23.43-.39.26-.16.61-.2l-.04-.27q-.04-.27-.04-.52 0-.26.06-.51.05-.25.17-.47t.31-.38q.19-.17.46-.24l-.03-.03zm.58 4.62q-.02.06-.04.13-.03.09-.03.2 0 .19.1.29.11.1.28.1.15 0 .27-.06.12-.07.23-.16.1-.09.18-.18.09-.09.14-.16l.05-.05-.06-.06-.15-.11q-.11-.08-.22-.13-.11-.07-.24-.09-.14-.02-.31 0z"/>
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
            <button @click="connectGmail" class="connect-btn gmail" :disabled="isConnecting">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 18h-2V9.25L12 13 6 9.25V18H4V6h1.2l6.8 4.25L18.8 6H20m0-2H4c-1.11 0-2 .89-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z"/>
              </svg>
              <span>Mit Gmail verbinden</span>
            </button>
            <button @click="connectOutlook" class="connect-btn outlook" :disabled="isConnecting">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7.88 12.04q0 .45-.11.87-.1.41-.33.74-.22.33-.58.52-.37.2-.87.2t-.85-.2q-.35-.21-.57-.55-.22-.33-.33-.75-.1-.42-.1-.86t.1-.87q.1-.43.34-.76.22-.34.59-.54.36-.2.87-.2t.86.2q.35.21.57.55.22.34.31.77.1.43.1.88zM24 12v9.38q0 .46-.33.8-.33.32-.8.32H7.13q-.46 0-.8-.33-.32-.33-.32-.8V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h6.5V2.38q0-.46.33-.8.33-.32.8-.32h14.74q.46 0 .8.33.32.33.32.8V12z"/>
              </svg>
              <span>Mit Outlook verbinden</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Password Change Section -->
      <section class="settings-section animate-fade-up" style="animation-delay: 150ms;">
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

            <div v-if="passwordError" class="password-error-message">
              {{ passwordError }}
            </div>

            <button
              type="submit"
              class="zen-btn zen-btn-filled"
              :disabled="!canSubmitPassword || isChangingPassword"
            >
              {{ isChangingPassword ? 'Wird geändert...' : 'Passwort ändern' }}
            </button>
          </form>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- API Keys Section -->
      <section class="settings-section animate-fade-up" style="animation-delay: 200ms;">
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
            <button @click="generateKey" class="zen-btn zen-btn-filled" :disabled="isGeneratingKey">
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
      </section>

      <!-- Chrome Extension Info -->
      <section class="info-section animate-fade-up" style="animation-delay: 300ms;">
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
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import { authStore } from '../store/auth'
import { confirm } from '../composables/useConfirm'

const _router = useRouter()

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

// Profile form state
const profileForm = reactive({
  fullName: '',
  displayName: ''
})
const originalProfile = reactive({
  fullName: '',
  displayName: ''
})
const isUpdatingProfile = ref(false)
const profileError = ref('')
const profileSuccess = ref('')

const hasProfileChanges = computed(() => {
  return (
    profileForm.fullName !== originalProfile.fullName ||
    profileForm.displayName !== originalProfile.displayName
  )
})

const initProfileForm = () => {
  const user = authStore.user
  profileForm.fullName = user?.full_name || ''
  profileForm.displayName = user?.display_name || ''
  originalProfile.fullName = user?.full_name || ''
  originalProfile.displayName = user?.display_name || ''
}

const updateProfile = async () => {
  if (!hasProfileChanges.value) return

  isUpdatingProfile.value = true
  profileError.value = ''
  profileSuccess.value = ''

  try {
    const { data } = await api.put('/auth/profile', {
      full_name: profileForm.fullName,
      display_name: profileForm.displayName
    })

    // Update auth store with new user data
    authStore.user = data.user

    // Update original values to match current
    originalProfile.fullName = profileForm.fullName
    originalProfile.displayName = profileForm.displayName

    profileSuccess.value = 'Profil erfolgreich aktualisiert'

    // Clear success message after 3 seconds
    setTimeout(() => {
      profileSuccess.value = ''
    }, 3000)
  } catch (err) {
    profileError.value = err.response?.data?.error || 'Fehler beim Aktualisieren des Profils'
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

const canSubmitPassword = computed(() => {
  return (
    passwordForm.currentPassword &&
    passwordForm.newPassword &&
    passwordForm.confirmPassword &&
    passwordForm.newPassword === passwordForm.confirmPassword &&
    Object.values(passwordChecks).every(v => v)
  )
})

const validatePassword = () => {
  const pw = passwordForm.newPassword
  passwordChecks.min_length = pw.length >= 8
  passwordChecks.has_uppercase = /[A-Z]/.test(pw)
  passwordChecks.has_lowercase = /[a-z]/.test(pw)
  passwordChecks.has_number = /\d/.test(pw)
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
  } catch (err) {
    passwordError.value = err.response?.data?.error || 'Fehler beim Ändern des Passworts'
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

const copyKey = () => {
  navigator.clipboard.writeText(newKey.value)
  if (window.$toast) {
    window.$toast('API Key kopiert!', 'success')
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
    alert('Fehler beim Löschen')
  }
}

const loadKeys = async () => {
  try {
    const { data } = await api.get('/keys')
    apiKeys.value = data.api_keys
  } catch (err) {
    console.error('Fehler beim Laden:', err)
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('de-DE', {
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
  } catch (err) {
    console.error('Fehler beim Laden der Email-Konten:', err)
  }
}

const connectGmail = async () => {
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
    const pollTimer = setInterval(() => {
      if (popup && popup.closed) {
        clearInterval(pollTimer)
        isConnecting.value = false
        loadEmailAccounts()
      }
    }, 500)
  } catch (_err) {
    isConnecting.value = false
    if (window.$toast) {
      window.$toast('Fehler beim Verbinden mit Gmail', 'error')
    }
  }
}

const connectOutlook = async () => {
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
    const pollTimer = setInterval(() => {
      if (popup && popup.closed) {
        clearInterval(pollTimer)
        isConnecting.value = false
        loadEmailAccounts()
      }
    }, 500)
  } catch (_err) {
    isConnecting.value = false
    if (window.$toast) {
      window.$toast('Fehler beim Verbinden mit Outlook', 'error')
    }
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

onMounted(() => {
  loadKeys()
  loadEmailAccounts()
  initProfileForm()
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
   SETTINGS SECTION
   ======================================== */
.settings-section {
  margin-bottom: var(--space-ma);
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
}

.info-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
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
   RESPONSIVE
   ======================================== */
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
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .section-header {
    flex-direction: column;
  }
}
</style>
