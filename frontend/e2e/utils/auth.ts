import { Page } from '@playwright/test';

/**
 * Setup authentication by setting localStorage and forcing a full page reload.
 * This works with Vue's reactive auth store which reads localStorage at initialization.
 *
 * The approach:
 * 1. Navigate to login page to initialize browser context
 * 2. Set auth tokens in localStorage
 * 3. Add script to intercept XMLHttpRequest and mock API responses (axios uses XHR)
 * 4. Navigate to target URL (this reinitializes Vue with the token in place)
 */
export async function setupAuthWithMocks(page: Page, targetUrl: string) {
  // Navigate to any page first to initialize the browser context
  await page.goto('/login');

  // Wait for initial page load
  await page.waitForLoadState('domcontentloaded');

  // Set auth token in localStorage
  await page.evaluate(() => {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      sub: '1',
      email: 'test@example.com',
      exp: Math.floor(Date.now() / 1000) + 3600
    }));
    localStorage.setItem('token', `${header}.${payload}.test-signature`);
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User'
    }));
  });

  // Add a script that will run on each new document to intercept XHR responses
  // This prevents the axios interceptor from redirecting on 401
  // Axios uses XMLHttpRequest internally
  await page.addInitScript(() => {
    // Mock responses for API calls - matching the actual API response structure
    const mockResponses: Record<string, unknown> = {
      // Dashboard stats - expects { stats: {...}, usage: {...} }
      '/api/stats': {
        stats: {
          total_applications: 5,
          interviews_scheduled: 2,
          offers_received: 1,
          this_month: 3
        },
        usage: {
          applications_limit: 10,
          applications_used: 3,
          plan_name: 'Free'
        }
      },
      // User info
      '/api/users/me': {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        display_name: 'Test',
        email_verified: true
      },
      '/api/auth/me': {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        display_name: 'Test',
        email_verified: true
      },
      // Skills
      '/api/users/me/skills': {
        skills: []
      },
      // Interview stats
      '/api/applications/interview-stats': {
        success: true,
        data: {
          total: 0,
          scheduled: 0,
          completed: 0,
          cancelled: 0
        }
      },
      // Subscription endpoints
      '/api/subscriptions/current': {
        success: true,
        data: {
          plan: 'free',
          status: 'active',
          applications_used: 3,
          applications_limit: 10,
          features: ['Basic templates', 'Job tracking']
        }
      },
      '/api/subscriptions/plans': {
        success: true,
        data: [
          { id: 'basic', name: 'Basic', price: 9.99, features: ['10 applications/month'] },
          { id: 'pro', name: 'Pro', price: 19.99, features: ['Unlimited applications'] }
        ]
      },
      '/api/subscription': {
        plan: 'free',
        status: 'active',
        applications_used: 3,
        applications_limit: 10,
        features: ['Basic templates', 'Job tracking']
      },
      // Templates
      '/api/templates': [],
      // Applications
      '/api/applications': [],
      // Documents - expects { documents: [...] }
      '/api/documents': { documents: [] },
      // Settings / Profile
      '/api/settings': {
        full_name: 'Max Mustermann',
        display_name: 'Max',
        email: 'test@example.com'
      },
      '/api/profile': {
        full_name: 'Max Mustermann',
        display_name: 'Max',
        email: 'test@example.com'
      },
      // Weekly goal
      '/api/weekly-goal': {
        target: 5,
        current: 2
      },
      // Recommendations
      '/api/recommendations': []
    };

    // Find matching mock response
    function getMockResponse(url: string): unknown {
      for (const [path, data] of Object.entries(mockResponses)) {
        if (url.includes(path)) {
          return data;
        }
      }
      return { success: true };
    }

    // Override XMLHttpRequest to mock API responses (axios uses XHR)
    const OriginalXHR = window.XMLHttpRequest;
    class MockXHR extends OriginalXHR {
      private _url: string = '';
      private _mockResponse: string | null = null;

      open(method: string, url: string | URL, async: boolean = true, user?: string | null, password?: string | null): void {
        this._url = url.toString();

        // Check if this is an API request we should mock
        if (this._url.includes('/api/')) {
          const mockData = getMockResponse(this._url);
          this._mockResponse = JSON.stringify(mockData);
        }

        return super.open(method, url, async, user, password);
      }

      send(body?: Document | XMLHttpRequestBodyInit | null): void {
        if (this._mockResponse !== null) {
          // Mock the response
          setTimeout(() => {
            Object.defineProperty(this, 'status', { value: 200, writable: false });
            Object.defineProperty(this, 'statusText', { value: 'OK', writable: false });
            Object.defineProperty(this, 'responseText', { value: this._mockResponse, writable: false });
            Object.defineProperty(this, 'response', { value: this._mockResponse, writable: false });
            Object.defineProperty(this, 'readyState', { value: 4, writable: false });

            // Trigger load event
            this.dispatchEvent(new Event('load'));
            this.dispatchEvent(new Event('loadend'));
            if (this.onload) {
              this.onload(new ProgressEvent('load'));
            }
            if (this.onreadystatechange) {
              this.onreadystatechange(new Event('readystatechange'));
            }
          }, 0);
        } else {
          return super.send(body);
        }
      }
    }

    // Replace XMLHttpRequest globally
    (window as unknown as { XMLHttpRequest: typeof MockXHR }).XMLHttpRequest = MockXHR;

    // Also override fetch for any non-axios calls
    const originalFetch = window.fetch;
    window.fetch = async function(input: RequestInfo | URL, init?: RequestInit) {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;

      if (url.includes('/api/')) {
        const mockData = getMockResponse(url);
        return new Response(JSON.stringify(mockData), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      return originalFetch.call(window, input, init);
    };
  });

  // Navigate to target URL - this will trigger a full page load with auth token in place
  await page.goto(targetUrl);

  // Wait for the page to be fully loaded and network idle
  // Using 'networkidle' instead of 'domcontentloaded' to ensure all async
  // mock XHR responses have triggered Vue re-renders before interacting
  await page.waitForLoadState('networkidle');
}
