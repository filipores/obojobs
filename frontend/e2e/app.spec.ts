import { test, expect } from '@playwright/test';

test.describe('Application', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/obo/i);
  });

  test('should have the app container', async ({ page }) => {
    await page.goto('/');
    const app = page.locator('#app').first();
    await expect(app).toBeVisible();
  });

  test('should navigate to login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('body')).toBeVisible();
  });
});
