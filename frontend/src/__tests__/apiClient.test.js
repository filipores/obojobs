import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
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

describe('API Client', () => {
  let mockAxiosInstance
  let requestInterceptor
  let responseInterceptor
  let mockToast

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup mock toast
    mockToast = vi.fn()
    window.$toast = mockToast

    // Reset localStorage mock
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })

    // Get mock axios instance
    mockAxiosInstance = axios.create()

    // Capture interceptors
    mockAxiosInstance.interceptors.request.use.mockImplementation((fn) => {
      requestInterceptor = fn
    })
    mockAxiosInstance.interceptors.response.use.mockImplementation((success, error) => {
      responseInterceptor = { success, error }
    })
  })

  describe('Request Interceptor', () => {
    it('should add Authorization header when token exists', async () => {
      localStorage.getItem.mockReturnValue('test-token')

      // Re-import to apply interceptors
      vi.resetModules()
      await import('../api/client.js')

      const config = { headers: {} }
      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer test-token')
    })

    it('should not add Authorization header when no token', async () => {
      localStorage.getItem.mockReturnValue(null)

      vi.resetModules()
      await import('../api/client.js')

      const config = { headers: {} }
      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('Response Interceptor Error Handling', () => {
    beforeEach(async () => {
      vi.resetModules()
      await import('../api/client.js')
    })

    it('should show toast for 403 Forbidden errors', async () => {
      const error = {
        response: { status: 403 },
        config: {}
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('Keine Berechtigung', 'error')
    })

    it('should show toast for 404 Not Found errors', async () => {
      const error = {
        response: { status: 404 },
        config: {}
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('Nicht gefunden', 'error')
    })

    it('should show toast for 500+ Server errors', async () => {
      const error = {
        response: { status: 500 },
        config: {}
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('Serverfehler. Bitte später erneut versuchen.', 'error')
    })

    it('should not show toast when suppressToast is true', async () => {
      const error = {
        response: { status: 500 },
        config: { suppressToast: true }
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).not.toHaveBeenCalled()
    })

    it('should handle validation errors (400/422)', async () => {
      const error = {
        response: {
          status: 400,
          data: { error: 'Ungültige E-Mail-Adresse' }
        },
        config: {}
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(mockToast).toHaveBeenCalledWith('Ungültige E-Mail-Adresse', 'error')
    })
  })

  describe('JWT Error Handling', () => {
    beforeEach(async () => {
      vi.resetModules()
      await import('../api/client.js')
    })

    it('should clear auth and redirect on 401 errors (non-login)', async () => {
      delete window.location
      window.location = { href: '' }

      const error = {
        response: { status: 401 },
        config: { url: '/some/endpoint' }
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('user')
      expect(window.location.href).toBe('/login')
    })

    it('should not redirect on 401 for login route', async () => {
      delete window.location
      window.location = { href: '' }

      const error = {
        response: { status: 401 },
        config: { url: '/auth/login' }
      }

      await expect(responseInterceptor.error(error)).rejects.toEqual(error)
      expect(window.location.href).not.toBe('/login')
    })
  })
})
