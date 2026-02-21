/**
 * Error message translation utility
 * Translates common backend error messages to German
 * Falls back to the original message if no translation is found
 */

// Known error message translations (English -> German)
const errorTranslations = {
  // Auth errors
  'Invalid email or password': 'Ungültige E-Mail oder Passwort',
  'User with this email already exists': 'Ein Benutzer mit dieser E-Mail existiert bereits',
  'Account is disabled': 'Konto ist deaktiviert',
  'Invalid or inactive user': 'Ungültiger oder inaktiver Benutzer',
  'User not found': 'Benutzer nicht gefunden',
  'Token is required': 'Token ist erforderlich',
  'Email and password are required': 'E-Mail und Passwort sind erforderlich',
  'Email is already verified': 'E-Mail ist bereits bestätigt',
  'Too many verification requests. Please try again later.': 'Zu viele Bestätigungsanfragen. Bitte später erneut versuchen.',
  'New password is required': 'Neues Passwort ist erforderlich',
  'Password does not meet requirements': 'Passwort erfüllt nicht die Anforderungen',
  'Token has been revoked': 'Token wurde widerrufen',

  // Email verification errors
  'Invalid verification token': 'Ungültiger Bestätigungstoken',
  'Verification token has expired': 'Bestätigungstoken ist abgelaufen',

  // Password reset errors
  'Invalid or expired reset token': 'Ungültiger oder abgelaufener Reset-Token',
  'Reset token has expired': 'Reset-Token ist abgelaufen',

  // API key errors
  'API key required': 'API-Schlüssel erforderlich',
  'Invalid API key': 'Ungültiger API-Schlüssel',
  'API key not found': 'API-Schlüssel nicht gefunden',

  // Email service errors
  'Email account not found': 'E-Mail-Konto nicht gefunden',
  'Authorization code is required': 'Autorisierungscode ist erforderlich',
  'Invalid state parameter': 'Ungültiger State-Parameter',
  'application_id is required': 'Bewerbungs-ID ist erforderlich',
  'email_account_id is required': 'E-Mail-Konto-ID ist erforderlich',
  'subject is required': 'Betreff ist erforderlich',
  'body is required': 'Nachrichtentext ist erforderlich',
  'to_email is required': 'Empfänger-E-Mail ist erforderlich',
  'Application not found': 'Bewerbung nicht gefunden',
  'GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set': 'Gmail-Integration ist derzeit nicht konfiguriert.',
  'MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET must be set': 'Outlook-Integration ist derzeit nicht konfiguriert.',
  'GOOGLE_REDIRECT_URI must be set': 'Gmail-Integration ist derzeit nicht konfiguriert.',
  'MICROSOFT_REDIRECT_URI must be set': 'Outlook-Integration ist derzeit nicht konfiguriert.',

  // Subscription errors
  'No active subscription. Please subscribe first.': 'Kein aktives Abonnement. Bitte abonniere zuerst einen Plan.',
  'return_url is required': 'return_url ist erforderlich',
  'success_url and cancel_url are required': 'success_url und cancel_url sind erforderlich',
  "Invalid plan. Must be 'starter' or 'pro'": "Ungültiger Plan. Muss 'starter' oder 'pro' sein.",
  'Plan not configured': 'Plan nicht konfiguriert',
  'Failed to create checkout session': 'Fehler beim Erstellen der Checkout-Sitzung',
  'Failed to create portal session': 'Fehler beim Erstellen der Portal-Sitzung',

  // Template errors
  'Template not found': 'Template nicht gefunden',
  'Name and content are required': 'Name und Inhalt sind erforderlich',
  'Name cannot be empty': 'Name darf nicht leer sein',
  'Content cannot be empty': 'Inhalt darf nicht leer sein',
  'Failed to create template': 'Fehler beim Erstellen des Templates',
  'Failed to update template': 'Fehler beim Aktualisieren des Templates',

  // Document errors
  'Document not found': 'Dokument nicht gefunden',
  'File not found': 'Datei nicht gefunden',

  // Generic errors
  'Not found': 'Nicht gefunden',
  'Bad request': 'Ungültige Anfrage',
  'Unauthorized': 'Nicht autorisiert',
  'Forbidden': 'Zugriff verweigert',
  'Internal server error': 'Interner Serverfehler',
}

// Regex patterns for dynamic error messages
const dynamicPatterns = [
  {
    pattern: /^Account is temporarily locked\. Try again in (\d+) minutes\.$/,
    translate: (match) => `Konto vorübergehend gesperrt. Versuche es in ${match[1]} Minuten erneut.`
  },
  {
    pattern: /^Account locked due to too many failed login attempts\. Try again in (\d+) minutes\.$/,
    translate: (match) => `Konto wegen zu vieler fehlgeschlagener Anmeldeversuche gesperrt. Versuche es in ${match[1]} Minuten erneut.`
  },
  {
    pattern: /^OAuth error: (.+) - (.+)$/,
    translate: (match) => `OAuth-Fehler: ${match[1]} - ${match[2]}`
  },
  {
    pattern: /^Failed to (generate authorization URL|complete OAuth flow|send email): (.+)$/,
    translate: (match) => {
      const actionMap = {
        'generate authorization URL': 'Erstellen der Autorisierungs-URL',
        'complete OAuth flow': 'Abschluss des OAuth-Prozesses',
        'send email': 'Senden der E-Mail'
      }
      return `Fehler beim ${actionMap[match[1]] || match[1]}: ${match[2]}`
    }
  },
  {
    pattern: /^Total attachment size exceeds 10MB limit \((.+)MB\)$/,
    translate: (match) => `Gesamtgröße der Anhänge überschreitet 10MB Limit (${match[1]}MB)`
  },
  {
    pattern: /^Unknown provider: (.+)$/,
    translate: (match) => `Unbekannter Anbieter: ${match[1]}`
  },
  {
    pattern: /^Name too long \(max (\d+) chars\)$/,
    translate: (match) => `Name zu lang (max. ${match[1]} Zeichen)`
  },
  {
    pattern: /^Content too long \(max (\d+) chars\)$/,
    translate: (match) => `Inhalt zu lang (max. ${match[1]} Zeichen)`
  },
]

/**
 * Translates a backend error message to German
 * @param {string} message - The error message to translate
 * @returns {string} - The translated message or the original if no translation found
 */
export function translateError(message) {
  if (!message || typeof message !== 'string') {
    return message || 'Ein unbekannter Fehler ist aufgetreten'
  }

  // Check exact matches first
  if (errorTranslations[message]) {
    return errorTranslations[message]
  }

  // Check dynamic patterns
  for (const { pattern, translate } of dynamicPatterns) {
    const match = message.match(pattern)
    if (match) {
      return translate(match)
    }
  }

  // Return original message if no translation found
  // (Backend should already return German messages, this is a fallback)
  return message
}

/**
 * Translates error response data from backend
 * @param {object} errorData - The error data object from API response
 * @returns {object} - The error data with translated message
 */
export function translateErrorResponse(errorData) {
  if (!errorData) {
    return { error: 'Ein unbekannter Fehler ist aufgetreten' }
  }

  return {
    ...errorData,
    error: errorData.error ? translateError(errorData.error) : errorData.error,
    message: errorData.message ? translateError(errorData.message) : errorData.message,
  }
}

export default {
  translateError,
  translateErrorResponse,
}
