import { describe, it, expect, beforeEach, vi } from 'vitest'

// Store interceptor callbacks globally so they persist across module resets
let capturedRequestInterceptor = null
let capturedResponseInterceptor = null

// Mock axios with interceptor capture
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: {
          use: vi.fn((fn) => {
            capturedRequestInterceptor = fn
          })
        },
        response: {
          use: vi.fn((success, error) => {
            capturedResponseInterceptor = { success, error }
          })
        }
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn()
    }))
  }
}))

// Mock translateError utility
vi.mock('@/utils/errorTranslations', () => ({
  translateError: vi.fn((msg) => msg)
}))

// Mock i18n to return the key as-is
vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

describe('API Client', () => {
  let mockToast

  beforeEach(() => {
    // Reset captured interceptors
    capturedRequestInterceptor = null
    capturedResponseInterceptor = null

    // Setup mock toast
    mockToast = vi.fn()
    window.$toast = mockToast

    // Reset localStorage mock
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    })
  })

  describe('Request Interceptor', () => {
    it('should add Authorization header when token exists', async () => {
      localStorage.getItem.mockReturnValue('test-token')

      // Re-import to apply interceptors
      vi.resetModules()
      await import('../api/client.js')

      expect(capturedRequestInterceptor).toBeDefined()
      const config = { headers: {} }
      const result = capturedRequestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer test-token')
    })

    it('should not add Authorization header when no token', async () => {
      localStorage.getItem.mockReturnValue(null)

      vi.resetModules()
      await import('../api/client.js')

      expect(capturedRequestInterceptor).toBeDefined()
      const config = { headers: {} }
      const result = capturedRequestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('Response Interceptor Error Handling', () => {
    beforeEach(async () => {
      vi.resetModules()
      await import('../api/client.js')
    })

    it('should show toast for 403 Forbidden errors', async () => {
      expect(capturedResponseInterceptor).toBeDefined()
      expect(capturedResponseInterceptor.error).toBeDefined()

      const error = {
        response: { status: 403 },
        config: {}
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('errors.forbidden', 'error')
    })

    it('should show toast for 404 Not Found errors', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      const error = {
        response: { status: 404 },
        config: {}
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('errors.notFound', 'error')
    })

    it('should show toast for 500+ Server errors', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      const error = {
        response: { status: 500 },
        config: {}
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('errors.serverError', 'error')
    })

    it('should not show toast when suppressToast is true', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      const error = {
        response: { status: 500 },
        config: { suppressToast: true }
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).not.toHaveBeenCalled()
    })

    it('should handle validation errors (400/422)', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      const error = {
        response: {
          status: 400,
          data: { error: 'Ungültige E-Mail-Adresse' }
        },
        config: {}
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('Ungültige E-Mail-Adresse', 'error')
    })
  })

  describe('JWT Error Handling', () => {
    beforeEach(async () => {
      vi.resetModules()
      await import('../api/client.js')
    })

    it('should clear auth and redirect on 401 errors (non-login)', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      delete window.location
      window.location = { href: '' }

      const error = {
        response: { status: 401 },
        config: { url: '/some/endpoint' }
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('user')
      expect(window.location.href).toBe('/login')
    })

    it('should not redirect on 401 for login route', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      delete window.location
      window.location = { href: '' }

      const error = {
        response: { status: 401 },
        config: { url: '/auth/login' }
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(window.location.href).not.toBe('/login')
    })

    it('should handle 422 with JWT error message as auth error', async () => {
      expect(capturedResponseInterceptor?.error).toBeDefined()

      delete window.location
      window.location = { href: '' }

      const error = {
        response: { status: 422, data: { msg: 'Not enough segments' } },
        config: { url: '/some/endpoint' }
      }

      await expect(capturedResponseInterceptor.error(error)).rejects.toEqual(error)
      expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      expect(window.location.href).toBe('/login')
    })
  })

  describe('Silent API wrapper', () => {
    it('should pass suppressToast for all methods', async () => {
      vi.resetModules()
      const { default: apiClient } = await import('../api/client.js')

      // api.silent methods should exist
      expect(apiClient.silent.get).toBeDefined()
      expect(apiClient.silent.post).toBeDefined()
      expect(apiClient.silent.put).toBeDefined()
      expect(apiClient.silent.delete).toBeDefined()
      expect(apiClient.silent.patch).toBeDefined()

      // Call each and verify suppressToast is passed
      apiClient.silent.get('/test')
      expect(apiClient.get).toHaveBeenCalledWith('/test', { suppressToast: true })

      apiClient.silent.post('/test', { foo: 'bar' })
      expect(apiClient.post).toHaveBeenCalledWith('/test', { foo: 'bar' }, { suppressToast: true })

      apiClient.silent.put('/test', { foo: 'bar' })
      expect(apiClient.put).toHaveBeenCalledWith('/test', { foo: 'bar' }, { suppressToast: true })

      apiClient.silent.delete('/test')
      expect(apiClient.delete).toHaveBeenCalledWith('/test', { suppressToast: true })

      apiClient.silent.patch('/test', { foo: 'bar' })
      expect(apiClient.patch).toHaveBeenCalledWith('/test', { foo: 'bar' }, { suppressToast: true })
    })
  })
})
