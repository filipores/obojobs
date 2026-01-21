/**
 * Error message translation utility
 * Uses vue-i18n for translations with fallback support
 */

import i18n from '../i18n'

const { t } = i18n.global

// Mapping from backend error messages to i18n keys
const errorKeyMap = {
  // Auth errors
  'Invalid email or password': 'errors.auth.invalidCredentials',
  'User with this email already exists': 'errors.auth.emailExists',
  'Account is disabled': 'errors.auth.accountDisabled',
  'Invalid or inactive user': 'errors.auth.invalidUser',
  'User not found': 'errors.auth.userNotFound',
  'Token is required': 'errors.auth.tokenRequired',
  'Email and password are required': 'errors.auth.emailPasswordRequired',
  'Email is already verified': 'errors.auth.emailAlreadyVerified',
  'Too many verification requests. Please try again later.': 'errors.auth.tooManyVerificationRequests',
  'New password is required': 'errors.auth.newPasswordRequired',
  'Password does not meet requirements': 'errors.auth.passwordRequirements',
  'Token has been revoked': 'errors.auth.tokenRevoked',

  // Email verification errors
  'Invalid verification token': 'errors.auth.invalidVerificationToken',
  'Verification token has expired': 'errors.auth.verificationTokenExpired',

  // Password reset errors
  'Invalid or expired reset token': 'errors.auth.invalidResetToken',
  'Reset token has expired': 'errors.auth.resetTokenExpired',

  // API key errors
  'API key required': 'errors.apiKey.required',
  'Invalid API key': 'errors.apiKey.invalid',
  'API key not found': 'errors.apiKey.notFound',

  // Email service errors
  'Email account not found': 'errors.email.accountNotFound',
  'Authorization code is required': 'errors.email.authCodeRequired',
  'Invalid state parameter': 'errors.email.invalidState',
  'application_id is required': 'errors.email.applicationIdRequired',
  'email_account_id is required': 'errors.email.emailAccountIdRequired',
  'subject is required': 'errors.email.subjectRequired',
  'body is required': 'errors.email.bodyRequired',
  'to_email is required': 'errors.email.toEmailRequired',
  'Application not found': 'errors.email.applicationNotFound',
  'GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set': 'errors.email.googleNotConfigured',
  'MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET must be set': 'errors.email.microsoftNotConfigured',
  'GOOGLE_REDIRECT_URI must be set': 'errors.email.googleNotConfigured',
  'MICROSOFT_REDIRECT_URI must be set': 'errors.email.microsoftNotConfigured',

  // Subscription errors
  'No active subscription. Please subscribe first.': 'errors.subscription.noActiveSubscription',
  'return_url is required': 'errors.subscription.returnUrlRequired',
  'success_url and cancel_url are required': 'errors.subscription.urlsRequired',
  "Invalid plan. Must be 'basic' or 'pro'": 'errors.subscription.invalidPlan',
  'Plan not configured': 'errors.subscription.planNotConfigured',
  'Failed to create checkout session': 'errors.subscription.checkoutFailed',
  'Failed to create portal session': 'errors.subscription.portalFailed',

  // Template errors
  'Template not found': 'errors.template.notFound',
  'Name and content are required': 'errors.template.nameContentRequired',
  'Name cannot be empty': 'errors.template.nameEmpty',
  'Content cannot be empty': 'errors.template.contentEmpty',
  'Failed to create template': 'errors.template.createFailed',
  'Failed to update template': 'errors.template.updateFailed',

  // Document errors
  'Document not found': 'errors.document.notFound',
  'File not found': 'errors.document.fileNotFound',

  // Generic errors
  'Not found': 'errors.generic.notFound',
  'Bad request': 'errors.generic.badRequest',
  'Unauthorized': 'errors.generic.unauthorized',
  'Forbidden': 'errors.generic.forbidden',
  'Internal server error': 'errors.generic.serverError',
}

// Regex patterns for dynamic error messages
const dynamicPatterns = [
  {
    pattern: /^Account is temporarily locked\. Try again in (\d+) minutes\.$/,
    key: 'errors.auth.accountLocked',
    extractParams: (match) => ({ minutes: match[1] })
  },
  {
    pattern: /^Account locked due to too many failed login attempts\. Try again in (\d+) minutes\.$/,
    key: 'errors.auth.accountLockedFailedAttempts',
    extractParams: (match) => ({ minutes: match[1] })
  },
  {
    pattern: /^OAuth error: (.+) - (.+)$/,
    key: 'errors.email.oauthError',
    extractParams: (match) => ({ error: match[1], description: match[2] })
  },
  {
    pattern: /^Failed to generate authorization URL: (.+)$/,
    key: 'errors.email.failedGenerateAuthUrl',
    extractParams: (match) => ({ details: match[1] })
  },
  {
    pattern: /^Failed to complete OAuth flow: (.+)$/,
    key: 'errors.email.failedCompleteOAuth',
    extractParams: (match) => ({ details: match[1] })
  },
  {
    pattern: /^Failed to send email: (.+)$/,
    key: 'errors.email.failedSendEmail',
    extractParams: (match) => ({ details: match[1] })
  },
  {
    pattern: /^Total attachment size exceeds 10MB limit \((.+)MB\)$/,
    key: 'errors.email.attachmentSizeExceeded',
    extractParams: (match) => ({ size: match[1] })
  },
  {
    pattern: /^Unknown provider: (.+)$/,
    key: 'errors.email.unknownProvider',
    extractParams: (match) => ({ provider: match[1] })
  },
  {
    pattern: /^Name too long \(max (\d+) chars\)$/,
    key: 'errors.template.nameTooLong',
    extractParams: (match) => ({ max: match[1] })
  },
  {
    pattern: /^Content too long \(max (\d+) chars\)$/,
    key: 'errors.template.contentTooLong',
    extractParams: (match) => ({ max: match[1] })
  },
]

/**
 * Translates a backend error message using vue-i18n
 * @param {string} message - The error message to translate
 * @returns {string} - The translated message or the original if no translation found
 */
export function translateError(message) {
  if (!message || typeof message !== 'string') {
    return message || t('errors.unknown')
  }

  // Check exact matches first
  const key = errorKeyMap[message]
  if (key) {
    return t(key)
  }

  // Check dynamic patterns
  for (const { pattern, key: translationKey, extractParams } of dynamicPatterns) {
    const match = message.match(pattern)
    if (match) {
      return t(translationKey, extractParams(match))
    }
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
    return { error: t('errors.unknown') }
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
