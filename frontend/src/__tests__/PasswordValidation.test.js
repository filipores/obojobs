import { describe, it, expect } from 'vitest'

// Helper function that mirrors the frontend validation logic
const validatePassword = (password) => {
  const checks = {
    min_length: password.length >= 8,
    has_uppercase: /[A-Z]/.test(password),
    has_lowercase: /[a-z]/.test(password),
    has_number: /\d/.test(password),
  }

  const isValid = checks.min_length &&
                  checks.has_uppercase &&
                  checks.has_lowercase &&
                  checks.has_number

  return { valid: isValid, checks }
}

describe('Password Validation', () => {
  describe('validatePassword', () => {
    it('accepts a strong password that meets all requirements', () => {
      const result = validatePassword('SecurePass123')

      expect(result.valid).toBe(true)
      expect(result.checks.min_length).toBe(true)
      expect(result.checks.has_uppercase).toBe(true)
      expect(result.checks.has_lowercase).toBe(true)
      expect(result.checks.has_number).toBe(true)
    })

    it('rejects password shorter than 8 characters', () => {
      const result = validatePassword('Pass1')

      expect(result.valid).toBe(false)
      expect(result.checks.min_length).toBe(false)
    })

    it('rejects password without uppercase letters', () => {
      const result = validatePassword('lowercase123')

      expect(result.valid).toBe(false)
      expect(result.checks.has_uppercase).toBe(false)
    })

    it('rejects password without lowercase letters', () => {
      const result = validatePassword('UPPERCASE123')

      expect(result.valid).toBe(false)
      expect(result.checks.has_lowercase).toBe(false)
    })

    it('rejects password without numbers', () => {
      const result = validatePassword('PasswordNoNum')

      expect(result.valid).toBe(false)
      expect(result.checks.has_number).toBe(false)
    })

    it('accepts password with exactly 8 characters', () => {
      const result = validatePassword('Abcdef1!')

      expect(result.checks.min_length).toBe(true)
    })

    it('rejects empty password', () => {
      const result = validatePassword('')

      expect(result.valid).toBe(false)
      expect(result.checks.min_length).toBe(false)
      expect(result.checks.has_uppercase).toBe(false)
      expect(result.checks.has_lowercase).toBe(false)
      expect(result.checks.has_number).toBe(false)
    })

    it('handles password with special characters', () => {
      const result = validatePassword('Pass123!@#')

      expect(result.valid).toBe(true)
    })

    it('handles password with spaces', () => {
      const result = validatePassword('Pass 123')

      expect(result.valid).toBe(true)
      expect(result.checks.min_length).toBe(true)
    })
  })
})
