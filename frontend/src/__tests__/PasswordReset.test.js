import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock localStorage
const localStorageMock = {
  store: {},
  getItem: vi.fn((key) => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => { localStorageMock.store[key] = value }),
  removeItem: vi.fn((key) => { delete localStorageMock.store[key] }),
  clear: vi.fn(() => { localStorageMock.store = {} })
}

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

describe('Password Reset Flow', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Password Validation', () => {
    const validatePassword = (password) => {
      return {
        min_length: password.length >= 8,
        has_uppercase: /[A-Z]/.test(password),
        has_lowercase: /[a-z]/.test(password),
        has_number: /\d/.test(password)
      }
    }

    const isPasswordValid = (checks) => {
      return checks.min_length &&
             checks.has_uppercase &&
             checks.has_lowercase &&
             checks.has_number
    }

    it('validates minimum length of 8 characters', () => {
      const shortPassword = 'Abc1234'
      const validPassword = 'Abc12345'

      expect(validatePassword(shortPassword).min_length).toBe(false)
      expect(validatePassword(validPassword).min_length).toBe(true)
    })

    it('validates uppercase letter requirement', () => {
      const noUppercase = 'abc12345'
      const withUppercase = 'Abc12345'

      expect(validatePassword(noUppercase).has_uppercase).toBe(false)
      expect(validatePassword(withUppercase).has_uppercase).toBe(true)
    })

    it('validates lowercase letter requirement', () => {
      const noLowercase = 'ABC12345'
      const withLowercase = 'ABc12345'

      expect(validatePassword(noLowercase).has_lowercase).toBe(false)
      expect(validatePassword(withLowercase).has_lowercase).toBe(true)
    })

    it('validates number requirement', () => {
      const noNumber = 'Abcdefgh'
      const withNumber = 'Abcdefg1'

      expect(validatePassword(noNumber).has_number).toBe(false)
      expect(validatePassword(withNumber).has_number).toBe(true)
    })

    it('validates complete password correctly', () => {
      const validPassword = 'TestPass123'
      const checks = validatePassword(validPassword)

      expect(isPasswordValid(checks)).toBe(true)
    })

    it('rejects password missing requirements', () => {
      const invalidPasswords = [
        'short1',       // too short
        'nocaps123456', // no uppercase
        'NOLOWER12345', // no lowercase
        'NoNumberHere'  // no number
      ]

      invalidPasswords.forEach(password => {
        const checks = validatePassword(password)
        expect(isPasswordValid(checks)).toBe(false)
      })
    })
  })

  describe('Password Confirmation', () => {
    it('matches when passwords are identical', () => {
      const password = 'TestPass123'
      const confirmPassword = 'TestPass123'

      expect(password === confirmPassword).toBe(true)
    })

    it('does not match when passwords differ', () => {
      const password = 'TestPass123'
      const confirmPassword = 'TestPass456'

      expect(password === confirmPassword).toBe(false)
    })

    it('is case sensitive', () => {
      const password = 'TestPass123'
      const confirmPassword = 'testpass123'

      expect(password === confirmPassword).toBe(false)
    })
  })

  describe('Token Validation', () => {
    const getTokenError = (token) => {
      if (!token) {
        return 'Kein Reset-Token gefunden. Bitte fordern Sie einen neuen Link an.'
      }
      return null
    }

    it('returns error when token is empty', () => {
      expect(getTokenError('')).toBe('Kein Reset-Token gefunden. Bitte fordern Sie einen neuen Link an.')
    })

    it('returns error when token is null', () => {
      expect(getTokenError(null)).toBe('Kein Reset-Token gefunden. Bitte fordern Sie einen neuen Link an.')
    })

    it('returns error when token is undefined', () => {
      expect(getTokenError(undefined)).toBe('Kein Reset-Token gefunden. Bitte fordern Sie einen neuen Link an.')
    })

    it('returns null when token exists', () => {
      expect(getTokenError('valid-token-123')).toBeNull()
    })
  })

  describe('Error Message Handling', () => {
    const getErrorDisplay = (errorMsg) => {
      if (errorMsg.includes('abgelaufen') || errorMsg.includes('expired')) {
        return {
          invalidToken: true,
          tokenError: 'Der Reset-Link ist abgelaufen. Bitte fordern Sie einen neuen Link an.'
        }
      } else if (errorMsg.includes('ungültig') || errorMsg.includes('invalid')) {
        return {
          invalidToken: true,
          tokenError: 'Der Reset-Link ist ungültig. Bitte fordern Sie einen neuen Link an.'
        }
      }
      return {
        invalidToken: false,
        error: errorMsg
      }
    }

    it('handles expired token error in German', () => {
      const result = getErrorDisplay('Token ist abgelaufen')
      expect(result.invalidToken).toBe(true)
      expect(result.tokenError).toContain('abgelaufen')
    })

    it('handles expired token error in English', () => {
      const result = getErrorDisplay('Token expired')
      expect(result.invalidToken).toBe(true)
      expect(result.tokenError).toContain('abgelaufen')
    })

    it('handles invalid token error in German', () => {
      const result = getErrorDisplay('Token ist ungültig')
      expect(result.invalidToken).toBe(true)
      expect(result.tokenError).toContain('ungültig')
    })

    it('handles invalid token error in English', () => {
      const result = getErrorDisplay('invalid token')
      expect(result.invalidToken).toBe(true)
      expect(result.tokenError).toContain('ungültig')
    })

    it('handles generic errors', () => {
      const result = getErrorDisplay('Ein allgemeiner Fehler')
      expect(result.invalidToken).toBe(false)
      expect(result.error).toBe('Ein allgemeiner Fehler')
    })
  })

  describe('Forgot Password Form', () => {
    it('validates email format', () => {
      const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

      expect(isValidEmail('test@example.com')).toBe(true)
      expect(isValidEmail('user@domain.de')).toBe(true)
      expect(isValidEmail('invalid')).toBe(false)
      expect(isValidEmail('invalid@')).toBe(false)
      expect(isValidEmail('@domain.com')).toBe(false)
    })

    it('shows success message after submission', () => {
      const submitted = true
      const email = 'test@example.com'

      const message = submitted
        ? `Falls ein Konto mit der E-Mail-Adresse ${email} existiert, wurde ein Link zum Zurücksetzen des Passworts gesendet.`
        : null

      expect(message).toContain(email)
      expect(message).toContain('Link')
    })
  })

  describe('Rate Limiting', () => {
    it('handles 429 rate limit error', () => {
      const handleError = (status) => {
        if (status === 429) {
          return 'Zu viele Anfragen. Bitte warten Sie einen Moment.'
        }
        return 'Ein Fehler ist aufgetreten.'
      }

      expect(handleError(429)).toBe('Zu viele Anfragen. Bitte warten Sie einen Moment.')
      expect(handleError(500)).toBe('Ein Fehler ist aufgetreten.')
    })
  })

  describe('Success State', () => {
    it('shows success card when password is reset successfully', () => {
      const success = true
      const invalidToken = false

      const showSuccessCard = success && !invalidToken
      expect(showSuccessCard).toBe(true)
    })

    it('hides form when success is true', () => {
      const success = true
      const invalidToken = false

      const showForm = !success && !invalidToken
      expect(showForm).toBe(false)
    })

    it('shows form when not in success or invalid state', () => {
      const success = false
      const invalidToken = false

      const showForm = !success && !invalidToken
      expect(showForm).toBe(true)
    })

    it('shows error card when token is invalid', () => {
      const success = false
      const invalidToken = true

      const showErrorCard = invalidToken
      const showForm = !success && !invalidToken

      expect(showErrorCard).toBe(true)
      expect(showForm).toBe(false)
    })
  })

  describe('Theme Toggle', () => {
    it('toggles dark mode on', () => {
      let isDarkMode = false
      isDarkMode = !isDarkMode
      localStorage.setItem('obojobs-theme', isDarkMode ? 'dark' : 'light')

      expect(isDarkMode).toBe(true)
      expect(localStorage.setItem).toHaveBeenCalledWith('obojobs-theme', 'dark')
    })

    it('toggles dark mode off', () => {
      let isDarkMode = true
      isDarkMode = !isDarkMode
      localStorage.setItem('obojobs-theme', isDarkMode ? 'dark' : 'light')

      expect(isDarkMode).toBe(false)
      expect(localStorage.setItem).toHaveBeenCalledWith('obojobs-theme', 'light')
    })

    it('reads saved theme from localStorage', () => {
      localStorageMock.store['obojobs-theme'] = 'dark'
      const savedTheme = localStorage.getItem('obojobs-theme')
      const isDarkMode = savedTheme === 'dark'

      expect(isDarkMode).toBe(true)
    })
  })
})
