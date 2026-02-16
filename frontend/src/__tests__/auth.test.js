import { describe, it, expect, beforeEach, vi } from 'vitest'

/* eslint-disable no-undef */
// Polyfill btoa for Node.js test environment (Buffer is a Node.js global)
const btoa = (str) => Buffer.from(str, 'utf-8').toString('base64')
/* eslint-enable no-undef */

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
      const { authStore } = await import('../stores/auth.js')

      expect(authStore.user).toBeNull()
    })

    it('should parse valid JSON user data', async () => {
      const mockUser = { id: 1, email: 'test@example.com' }
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify(mockUser)
        return null
      })

      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')

      expect(authStore.user).toEqual(mockUser)
    })

    it('should handle corrupted JSON gracefully', async () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return 'invalid-json{'
        return null
      })

      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')

      expect(authStore.user).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    })
  })

  describe('isAuthenticated', () => {
    it('should return false when no token exists', async () => {
      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')
      authStore.token = null

      expect(authStore.isAuthenticated()).toBe(false)
    })

    it('should return false for invalid token format (not 3 parts)', async () => {
      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')
      authStore.token = 'invalid.token'

      expect(authStore.isAuthenticated()).toBe(false)
      expect(authStore.token).toBeNull()
    })

    it('should return false for expired token', async () => {
      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')

      // Create an expired JWT (exp in the past)
      const payload = { exp: Math.floor(Date.now() / 1000) - 3600 } // 1 hour ago
      const encodedPayload = btoa(JSON.stringify(payload))
      authStore.token = `header.${encodedPayload}.signature`

      expect(authStore.isAuthenticated()).toBe(false)
      expect(authStore.token).toBeNull()
    })

    it('should return true for valid non-expired token', async () => {
      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')

      // Create a valid JWT (exp in the future)
      const payload = { exp: Math.floor(Date.now() / 1000) + 3600 } // 1 hour from now
      const encodedPayload = btoa(JSON.stringify(payload))
      authStore.token = `header.${encodedPayload}.signature`

      expect(authStore.isAuthenticated()).toBe(true)
    })

    it('should return true for token without exp claim', async () => {
      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')

      // Create a JWT without exp claim
      const payload = { sub: 'user123' }
      const encodedPayload = btoa(JSON.stringify(payload))
      authStore.token = `header.${encodedPayload}.signature`

      expect(authStore.isAuthenticated()).toBe(true)
    })
  })

  describe('login', () => {
    it('should store token and user on successful login', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      const mockResponse = {
        data: {
          access_token: 'new-token',
          user: { id: 1, email: 'test@example.com' }
        }
      }
      api.silent.post.mockResolvedValue(mockResponse)

      await authStore.login('test@example.com', 'password')

      expect(api.silent.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password'
      })
      expect(authStore.token).toBe('new-token')
      expect(authStore.user).toEqual({ id: 1, email: 'test@example.com' })
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'new-token')
    })
  })

  describe('register', () => {
    it('should call register endpoint and store pending email', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      api.post.mockResolvedValue({ data: { message: 'ok' } })

      const result = await authStore.register('test@example.com', 'pass', 'Test User')

      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'test@example.com',
        password: 'pass',
        full_name: 'Test User'
      })
      expect(localStorageMock.setItem).toHaveBeenCalledWith('pendingVerificationEmail', 'test@example.com')
      expect(result).toEqual({ message: 'ok' })
    })
  })

  describe('loginWithGoogle', () => {
    it('should store token and user from Google auth', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      const mockResponse = {
        data: {
          access_token: 'google-token',
          user: { id: 2, email: 'google@example.com' }
        }
      }
      api.silent.post.mockResolvedValue(mockResponse)

      await authStore.loginWithGoogle('google-credential')

      expect(api.silent.post).toHaveBeenCalledWith('/auth/google', { credential: 'google-credential' })
      expect(authStore.token).toBe('google-token')
      expect(authStore.user).toEqual({ id: 2, email: 'google@example.com' })
    })
  })

  describe('sendVerificationEmail', () => {
    it('should call send-verification endpoint', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      api.post.mockResolvedValue({})

      await authStore.sendVerificationEmail()

      expect(api.post).toHaveBeenCalledWith('/auth/send-verification')
    })
  })

  describe('fetchUser', () => {
    it('should fetch and store user data', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      const userData = { id: 1, email: 'test@example.com', full_name: 'Test' }
      api.get.mockResolvedValue({ data: userData })

      await authStore.fetchUser()

      expect(api.get).toHaveBeenCalledWith('/auth/me')
      expect(authStore.user).toEqual(userData)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(userData))
    })
  })

  describe('logout', () => {
    it('should call logout endpoint and clear state', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      authStore.token = 'some-token'
      authStore.user = { id: 1 }
      api.post.mockResolvedValue({})

      await authStore.logout()

      expect(api.post).toHaveBeenCalledWith('/auth/logout')
      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
    })

    it('should clear state even if server logout fails', async () => {
      vi.resetModules()
      const api = (await import('../api/client')).default
      const { authStore } = await import('../stores/auth.js')

      authStore.token = 'some-token'
      authStore.user = { id: 1 }
      api.post.mockRejectedValue(new Error('Network error'))

      await authStore.logout()

      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
    })
  })

  describe('clearAuthState', () => {
    it('should clear user and token from store and localStorage', async () => {
      vi.resetModules()
      const { authStore } = await import('../stores/auth.js')

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
