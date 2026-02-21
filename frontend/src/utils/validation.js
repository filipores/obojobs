/**
 * Validates a password against security requirements.
 *
 * @param {string} password - The password to validate.
 * @returns {object} An object containing the validation results for each requirement.
 */
export const validatePassword = (password) => {
  return {
    min_length: password.length >= 8,
    has_uppercase: /[A-Z]/.test(password),
    has_lowercase: /[a-z]/.test(password),
    has_number: /\d/.test(password),
  }
}

/**
 * Checks if all password requirements are met.
 *
 * @param {object} checks - The validation results object returned by validatePassword.
 * @returns {boolean} True if all requirements are met, false otherwise.
 */
export const isPasswordValid = (checks) => {
  return Object.values(checks).every(Boolean)
}
