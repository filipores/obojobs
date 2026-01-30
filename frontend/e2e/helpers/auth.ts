import { Page } from '@playwright/test';

/**
 * Creates a valid JWT token for testing.
 * The token has a proper format and non-expired exp claim.
 */
export function createTestToken(): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    sub: '1',
    email: 'test@example.com',
    exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
  }));
  return `${header}.${payload}.test-signature`;
}

/**
 * Test user data for mocking authentication.
 */
export const testUser = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User'
};

/**
 * Sets up authentication for a Playwright page.
 * 
 * IMPORTANT: This must be called BEFORE navigating to any page.
 * It uses addInitScript to inject auth data before Vue's auth store initializes.
 * 
 * @param page - The Playwright page object
 */
export async function setupAuth(page: Page): Promise<void> {
  const token = createTestToken();
  const user = JSON.stringify(testUser);
  
  // addInitScript runs BEFORE any page scripts, so the auth store
  // will read the correct values when it initializes
  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', user);
  }, { token, user });
}

/**
 * Navigates to a protected page with authentication.
 * Sets up auth before navigation to ensure Vue's auth store is properly initialized.
 * 
 * @param page - The Playwright page object
 * @param path - The path to navigate to (e.g., '/settings')
 */
export async function gotoWithAuth(page: Page, path: string): Promise<void> {
  await setupAuth(page);
  await page.goto(path);
  await page.waitForLoadState('networkidle');
}
