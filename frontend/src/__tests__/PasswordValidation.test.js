import { describe, it, expect } from 'vitest'
import { validatePassword, isPasswordValid } from '../utils/validation'

describe('Password Validation', () => {
  describe('validatePassword', () => {
    it('accepts a strong password that meets all requirements', () => {
      const checks = validatePassword('SecurePass123')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(true)
      expect(checks.min_length).toBe(true)
      expect(checks.has_uppercase).toBe(true)
      expect(checks.has_lowercase).toBe(true)
      expect(checks.has_number).toBe(true)
    })

    it('rejects password shorter than 8 characters', () => {
      const checks = validatePassword('Pass1')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(false)
      expect(checks.min_length).toBe(false)
    })

    it('rejects password without uppercase letters', () => {
      const checks = validatePassword('lowercase123')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(false)
      expect(checks.has_uppercase).toBe(false)
    })

    it('rejects password without lowercase letters', () => {
      const checks = validatePassword('UPPERCASE123')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(false)
      expect(checks.has_lowercase).toBe(false)
    })

    it('rejects password without numbers', () => {
      const checks = validatePassword('PasswordNoNum')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(false)
      expect(checks.has_number).toBe(false)
    })

    it('accepts password with exactly 8 characters', () => {
      const checks = validatePassword('Abcdef1!')

      expect(checks.min_length).toBe(true)
    })

    it('rejects empty password', () => {
      const checks = validatePassword('')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(false)
      expect(checks.min_length).toBe(false)
      expect(checks.has_uppercase).toBe(false)
      expect(checks.has_lowercase).toBe(false)
      expect(checks.has_number).toBe(false)
    })

    it('handles password with special characters', () => {
      const checks = validatePassword('Pass123!@#')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(true)
    })

    it('handles password with spaces', () => {
      const checks = validatePassword('Pass 123')
      const isValid = isPasswordValid(checks)

      expect(isValid).toBe(true)
      expect(checks.min_length).toBe(true)
    })
  })
})
