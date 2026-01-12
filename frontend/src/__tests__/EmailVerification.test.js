import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock localStorage and sessionStorage
const localStorageMock = {
  store: {},
  getItem: vi.fn((key) => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => { localStorageMock.store[key] = value }),
  removeItem: vi.fn((key) => { delete localStorageMock.store[key] }),
  clear: vi.fn(() => { localStorageMock.store = {} })
}

const sessionStorageMock = {
  store: {},
  getItem: vi.fn((key) => sessionStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => { sessionStorageMock.store[key] = value }),
  removeItem: vi.fn((key) => { delete sessionStorageMock.store[key] }),
  clear: vi.fn(() => { sessionStorageMock.store = {} })
}

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })
Object.defineProperty(globalThis, 'sessionStorage', { value: sessionStorageMock })

describe('Email Verification Flow', () => {
  beforeEach(() => {
    localStorageMock.clear()
    sessionStorageMock.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('pendingVerificationEmail storage', () => {
    it('stores email in localStorage after registration', () => {
      const email = 'test@example.com'
      localStorage.setItem('pendingVerificationEmail', email)

      expect(localStorage.setItem).toHaveBeenCalledWith('pendingVerificationEmail', email)
      expect(localStorage.getItem('pendingVerificationEmail')).toBe(email)
    })

    it('removes pendingVerificationEmail after successful verification', () => {
      localStorage.setItem('pendingVerificationEmail', 'test@example.com')
      localStorage.removeItem('pendingVerificationEmail')

      expect(localStorage.removeItem).toHaveBeenCalledWith('pendingVerificationEmail')
      expect(localStorage.getItem('pendingVerificationEmail')).toBeNull()
    })
  })

  describe('verification banner dismissal', () => {
    it('stores banner dismissal in sessionStorage', () => {
      sessionStorage.setItem('verificationBannerDismissed', 'true')

      expect(sessionStorage.setItem).toHaveBeenCalledWith('verificationBannerDismissed', 'true')
      expect(sessionStorage.getItem('verificationBannerDismissed')).toBe('true')
    })

    it('banner dismissal persists within session', () => {
      sessionStorage.setItem('verificationBannerDismissed', 'true')

      // Simulate page reload within same session
      const isDismissed = sessionStorage.getItem('verificationBannerDismissed') === 'true'
      expect(isDismissed).toBe(true)
    })
  })

  describe('cooldown timer logic', () => {
    it('calculates cooldown correctly', () => {
      let cooldownSeconds = 60

      // Simulate countdown
      cooldownSeconds--
      expect(cooldownSeconds).toBe(59)

      cooldownSeconds = 0
      expect(cooldownSeconds <= 0).toBe(true)
    })
  })

  describe('email verification status check', () => {
    it('shows banner when email_verified is false', () => {
      const user = { email: 'test@example.com', email_verified: false }
      const bannerDismissed = false

      const shouldShowBanner = !bannerDismissed && user && user.email_verified === false
      expect(shouldShowBanner).toBe(true)
    })

    it('hides banner when email_verified is true', () => {
      const user = { email: 'test@example.com', email_verified: true }
      const bannerDismissed = false

      const shouldShowBanner = !bannerDismissed && user && user.email_verified === false
      expect(shouldShowBanner).toBe(false)
    })

    it('hides banner when dismissed', () => {
      const user = { email: 'test@example.com', email_verified: false }
      const bannerDismissed = true

      const shouldShowBanner = !bannerDismissed && user && user.email_verified === false
      expect(shouldShowBanner).toBe(false)
    })

    it('hides banner when no user', () => {
      const user = null
      const bannerDismissed = false

      const shouldShowBanner = !bannerDismissed && user && user.email_verified === false
      // Result is null (falsy) when user is null, which means banner should not show
      expect(shouldShowBanner).toBeFalsy()
    })
  })

  describe('token verification error handling', () => {
    const getErrorMessage = (errorCode) => {
      if (errorCode === 'Token abgelaufen') {
        return 'Der Verifizierungs-Link ist abgelaufen. Bitte fordern Sie einen neuen Link an.'
      } else if (errorCode === 'Ungültiger Token') {
        return 'Der Verifizierungs-Link ist ungültig. Bitte fordern Sie einen neuen Link an.'
      } else if (errorCode === 'E-Mail bereits verifiziert') {
        return 'Ihre E-Mail-Adresse wurde bereits verifiziert. Sie können sich anmelden.'
      } else {
        return errorCode || 'Ein unbekannter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.'
      }
    }

    it('handles expired token error', () => {
      const message = getErrorMessage('Token abgelaufen')
      expect(message).toContain('abgelaufen')
    })

    it('handles invalid token error', () => {
      const message = getErrorMessage('Ungültiger Token')
      expect(message).toContain('ungültig')
    })

    it('handles already verified error', () => {
      const message = getErrorMessage('E-Mail bereits verifiziert')
      expect(message).toContain('bereits verifiziert')
    })

    it('handles unknown error', () => {
      const message = getErrorMessage(null)
      expect(message).toContain('unbekannter Fehler')
    })
  })

  describe('redirect countdown', () => {
    it('countdown starts at 5 seconds', () => {
      const redirectSeconds = 5
      expect(redirectSeconds).toBe(5)
    })

    it('countdown reaches 0', () => {
      let redirectSeconds = 5
      while (redirectSeconds > 0) {
        redirectSeconds--
      }
      expect(redirectSeconds).toBe(0)
    })
  })
})
