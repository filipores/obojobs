/**
 * Error message translation utility using vue-i18n
 * Translates common backend error messages based on current locale
 * Falls back to the original message if no translation is found
 */

import i18n from '@/i18n'

// Helper to get t function from i18n instance
const t = (key, params = {}) => {
  return i18n.global.t(key, params)
}

// Regex patterns for dynamic error messages
const dynamicPatterns = [
  {
    pattern: /^Account is temporarily locked\. Try again in (\d+) minutes\.$/,
    translate: (match) => t('errors.Account locked', { minutes: match[1] })
  },
  {
    pattern: /^Account locked due to too many failed login attempts\. Try again in (\d+) minutes\.$/,
    translate: (match) => t('errors.Too many failed logins', { minutes: match[1] })
  },
  {
    pattern: /^OAuth error: (.+) - (.+)$/,
    translate: (match) => t('errors.OAuth error', { error: match[1], description: match[2] })
  },
  {
    pattern: /^Failed to (generate authorization URL|complete OAuth flow|send email): (.+)$/,
    translate: (match) => {
      const actionKey = {
        'generate authorization URL': 'Failed to generate authorization URL',
        'complete OAuth flow': 'Failed to complete OAuth flow',
        'send email': 'Failed to send email'
      }
      return t(`errors.${actionKey[match[1]]}`, { details: match[2] })
    }
  },
  {
    pattern: /^Total attachment size exceeds 10MB limit \((.+)MB\)$/,
    translate: (match) => t('errors.Attachment size exceeds limit', { size: match[1] })
  },
  {
    pattern: /^Unknown provider: (.+)$/,
    translate: (match) => t('errors.Unknown provider', { provider: match[1] })
  },
  {
    pattern: /^Name too long \(max (\d+) chars\)$/,
    translate: (match) => t('errors.Name too long', { max: match[1] })
  },
  {
    pattern: /^Content too long \(max (\d+) chars\)$/,
    translate: (match) => t('errors.Content too long', { max: match[1] })
  },
]

/**
 * Translates a backend error message using vue-i18n
 * @param {string} message - The error message to translate
 * @returns {string} - The translated message or the original if no translation found
 */
export function translateError(message) {
  if (!message || typeof message !== 'string') {
    return message || t('errors.Unknown error occurred')
  }

  // Check dynamic patterns first (they have regex matching)
  for (const { pattern, translate } of dynamicPatterns) {
    const match = message.match(pattern)
    if (match) {
      return translate(match)
    }
  }

  // Try to find translation by key in errors namespace
  const translationKey = `errors.${message}`
  const translated = t(translationKey)

  // If translation exists (not equal to key), return it
  if (translated !== translationKey) {
    return translated
  }

  // Return original message if no translation found
  return message
}

/**
 * Translates error response data from backend
 * @param {object} errorData - The error data object from API response
 * @returns {object} - The error data with translated message
 */
export function translateErrorResponse(errorData) {
  if (!errorData) {
    return { error: t('errors.Unknown error occurred') }
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
