/**
 * Classify error messages to determine contextual actions.
 * Used by JobPreview and QuickExtract to show relevant recovery links.
 */

const DOCUMENT_KEYWORDS = ['lebenslauf', 'resume', 'cv']
const SUBSCRIPTION_KEYWORDS = ['limit', 'subscription', 'abonnement', 'kontingent']

/**
 * @param {string} error
 * @param {string[]} keywords
 * @returns {boolean}
 */
function errorContainsAny(error, keywords) {
  if (!error) return false
  const lower = error.toLowerCase()
  return keywords.some((keyword) => lower.includes(keyword))
}

/**
 * Check if the error indicates a missing document (CV/resume).
 * @param {string} error
 * @returns {boolean}
 */
export function isDocumentMissingError(error) {
  return errorContainsAny(error, DOCUMENT_KEYWORDS)
}

/**
 * Check if the error indicates a subscription limit was reached.
 * @param {string} error
 * @returns {boolean}
 */
export function isSubscriptionLimitError(error) {
  return errorContainsAny(error, SUBSCRIPTION_KEYWORDS)
}
