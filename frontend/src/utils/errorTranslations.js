/**
 * Error message translation utility using vue-i18n
 * Maps backend error messages to i18n translation keys
 * Falls back to the original message if no translation is found
 */

import { t } from '../i18n'

// Map of exact error messages to i18n keys
const errorKeyMap = {
  // Auth errors
  'Invalid email or password': 'errors.auth.invalidEmailOrPassword',
  'User with this email already exists': 'errors.auth.userExists',
  'Account is disabled': 'errors.auth.accountDisabled',
  'Invalid or inactive user': 'errors.auth.invalidOrInactiveUser',
  'User not found': 'errors.auth.userNotFound',
  'Token is required': 'errors.auth.tokenRequired',
  'Email and password are required': 'errors.auth.emailAndPasswordRequired',
  'Email is already verified': 'errors.auth.emailAlreadyVerified',
  'Too many verification requests. Please try again later.': 'errors.auth.tooManyVerificationRequests',
  'New password is required': 'errors.auth.newPasswordRequired',
  'Password does not meet requirements': 'errors.auth.passwordNotMeetRequirements',
  'Token has been revoked': 'errors.auth.tokenRevoked',

  // Email verification errors
  'Invalid verification token': 'errors.emailVerification.invalidToken',
  'Verification token has expired': 'errors.emailVerification.tokenExpired',

  // Password reset errors
  'Invalid or expired reset token': 'errors.passwordReset.invalidOrExpiredToken',
  'Reset token has expired': 'errors.passwordReset.tokenExpired',

  // API key errors
  'API key required': 'errors.apiKey.required',
  'Invalid API key': 'errors.apiKey.invalid',
  'API key not found': 'errors.apiKey.notFound',

  // Email service errors
  'Email account not found': 'errors.email.accountNotFound',
  'Authorization code is required': 'errors.email.authorizationCodeRequired',
  'Invalid state parameter': 'errors.email.invalidStateParameter',
  'application_id is required': 'errors.email.applicationIdRequired',
  'email_account_id is required': 'errors.email.emailAccountIdRequired',
  'subject is required': 'errors.email.subjectRequired',
  'body is required': 'errors.email.bodyRequired',
  'to_email is required': 'errors.email.toEmailRequired',
  'Application not found': 'errors.email.applicationNotFound',
  'GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set': 'errors.email.gmailNotConfigured',
  'MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET must be set': 'errors.email.outlookNotConfigured',
  'GOOGLE_REDIRECT_URI must be set': 'errors.email.gmailNotConfigured',
  'MICROSOFT_REDIRECT_URI must be set': 'errors.email.outlookNotConfigured',

  // Subscription errors
  'No active subscription. Please subscribe first.': 'errors.subscription.noActiveSubscription',
  'return_url is required': 'errors.subscription.returnUrlRequired',
  'success_url and cancel_url are required': 'errors.subscription.successAndCancelUrlRequired',
  "Invalid plan. Must be 'basic' or 'pro'": 'errors.subscription.invalidPlan',
  'Plan not configured': 'errors.subscription.planNotConfigured',
  'Failed to create checkout session': 'errors.subscription.failedCreateCheckout',
  'Failed to create portal session': 'errors.subscription.failedCreatePortal',

  // Template errors
  'Template not found': 'errors.template.notFound',
  'Name and content are required': 'errors.template.nameAndContentRequired',
  'Name cannot be empty': 'errors.template.nameCannotBeEmpty',
  'Content cannot be empty': 'errors.template.contentCannotBeEmpty',
  'Failed to create template': 'errors.template.failedCreate',
  'Failed to update template': 'errors.template.failedUpdate',

  // Document errors
  'Document not found': 'errors.document.notFound',
  'File not found': 'errors.document.fileNotFound',

  // Generic errors
  'Not found': 'errors.generic.notFound',
  'Bad request': 'errors.generic.badRequest',
  'Unauthorized': 'errors.generic.unauthorized',
  'Forbidden': 'errors.generic.forbidden',
  'Internal server error': 'errors.generic.internalServerError',
}

// Regex patterns for dynamic error messages with i18n keys and param extractors
const dynamicPatterns = [
  {
    pattern: /^Account is temporarily locked\. Try again in (\d+) minutes\.$/,
    key: 'errors.auth.accountLockedMinutes',
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
    extractParams: (match) => ({ error: match[1] })
  },
  {
    pattern: /^Failed to complete OAuth flow: (.+)$/,
    key: 'errors.email.failedCompleteOauth',
    extractParams: (match) => ({ error: match[1] })
  },
  {
    pattern: /^Failed to send email: (.+)$/,
    key: 'errors.email.failedSendEmail',
    extractParams: (match) => ({ error: match[1] })
  },
  {
    pattern: /^Total attachment size exceeds 10MB limit \((.+)MB\)$/,
    key: 'errors.email.attachmentSizeExceeds',
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
    return message || t('errors.generic.unknownError')
  }

  // Check exact matches first
  const i18nKey = errorKeyMap[message]
  if (i18nKey) {
    return t(i18nKey)
  }

  // Check dynamic patterns
  for (const { pattern, key, extractParams } of dynamicPatterns) {
    const match = message.match(pattern)
    if (match) {
      return t(key, extractParams(match))
    }
  }

  // Return original message if no translation found
  // (Backend may already return translated messages)
  return message
}

/**
 * Translates error response data from backend
 * @param {object} errorData - The error data object from API response
 * @returns {object} - The error data with translated message
 */
export function translateErrorResponse(errorData) {
  if (!errorData) {
    return { error: t('errors.generic.unknownError') }
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
