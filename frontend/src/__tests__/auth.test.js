import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: () => { store = {} }
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock api client
vi.mock('../api/client', () => ({
  default: {
    silent: {
      post: vi.fn()
    },
    post: vi.fn(),
    get: vi.fn()
  }
}))

describe('Auth Store', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('safeParseUser', () => {
    it('should return null when no user is stored', async () => {
      localStorageMock.getItem.mockReturnValue(null)

      // Re-import to trigger safeParseUser
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      expect(authStore.user).toBeNull()
    })

    it('should parse valid JSON user data', async () => {
      const mockUser = { id: 1, email: 'test@example.com' }
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify(mockUser)
        return null
      })

      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      expect(authStore.user).toEqual(mockUser)
    })

    it('should handle corrupted JSON gracefully', async () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return 'invalid-json{'
        return null
      })

      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      expect(authStore.user).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    })
  })

  describe('isAuthenticated', () => {
    it('should return false when no token exists', async () => {
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')
      authStore.token = null

      expect(authStore.isAuthenticated()).toBe(false)
    })

    it('should return false for invalid token format (not 3 parts)', async () => {
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')
      authStore.token = 'invalid.token'

      expect(authStore.isAuthenticated()).toBe(false)
      expect(authStore.token).toBeNull()
    })

    it('should return false for expired token', async () => {
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      // Create an expired JWT (exp in the past)
      const payload = { exp: Math.floor(Date.now() / 1000) - 3600 } // 1 hour ago
      const encodedPayload = btoa(JSON.stringify(payload))
      authStore.token = `header.${encodedPayload}.signature`

      expect(authStore.isAuthenticated()).toBe(false)
      expect(authStore.token).toBeNull()
    })

    it('should return true for valid non-expired token', async () => {
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      // Create a valid JWT (exp in the future)
      const payload = { exp: Math.floor(Date.now() / 1000) + 3600 } // 1 hour from now
      const encodedPayload = btoa(JSON.stringify(payload))
      authStore.token = `header.${encodedPayload}.signature`

      expect(authStore.isAuthenticated()).toBe(true)
    })

    it('should return true for token without exp claim', async () => {
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      // Create a JWT without exp claim
      const payload = { sub: 'user123' }
      const encodedPayload = btoa(JSON.stringify(payload))
      authStore.token = `header.${encodedPayload}.signature`

      expect(authStore.isAuthenticated()).toBe(true)
    })
  })

  describe('clearAuthState', () => {
    it('should clear user and token from store and localStorage', async () => {
      vi.resetModules()
      const { authStore } = await import('../store/auth.js')

      authStore.user = { id: 1 }
      authStore.token = 'some-token'

      authStore.clearAuthState()

      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user')
    })
  })
})
