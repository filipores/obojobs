/**
 * Capitalize the first letter of a string.
 * @param {string} str
 * @returns {string}
 */
export function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Format an ISO date string as dd.mm.yyyy (German locale).
 * Returns an en-dash for falsy values.
 * @param {string|null|undefined} iso
 * @returns {string}
 */
export function formatDateDE(iso) {
  if (!iso) return '\u2013'
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
