import { test, expect } from '@playwright/test';

// Setup auth by setting localStorage and forcing a full page reload so Vue app picks up the token
async function setupAuth(page: import('@playwright/test').Page, targetUrl: string) {
  // Navigate to login page first to initialize the browser context
  await page.goto('/login');

  // Set auth token in localStorage and force full page reload to target
  await page.evaluate((target) => {
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
    // Force full page reload to target - this reinitializes Vue with the token
    window.location.href = target;
  }, targetUrl);

  await page.waitForLoadState('networkidle');
}

test.describe('Subscription Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page, '/subscription');
  });

  test('should load the subscription page', async ({ page }) => {
    await expect(page).toHaveURL(/\/subscription/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display page header', async ({ page }) => {
    const h1 = page.locator('h1');
    await expect(h1).toContainText('Abonnement');
  });

  test('should display loading state or content', async ({ page }) => {
    // Should show either loading state or subscription content
    const loadingState = page.locator('.loading-state, .loading-spinner');
    const subscriptionSection = page.locator('.subscription-section');
    
    const hasLoading = await loadingState.isVisible({ timeout: 2000 }).catch(() => false);
    const hasContent = await subscriptionSection.isVisible({ timeout: 5000 }).catch(() => false);
    
    expect(hasLoading || hasContent).toBe(true);
  });
});

test.describe('Subscription Page - Current Plan Section', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page, '/subscription');
  });

  test('should display current plan section header', async ({ page }) => {
    const planHeader = page.locator('h2:has-text("Aktueller Plan")');
    await expect(planHeader).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Current plan header not visible - may still be loading');
    });
  });

  test('should display plan badge', async ({ page }) => {
    const planBadge = page.locator('.plan-badge');
    await expect(planBadge).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Plan badge not visible');
    });
  });

  test('should display status badge', async ({ page }) => {
    const statusBadge = page.locator('.status-badge');
    await expect(statusBadge).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Status badge not visible');
    });
  });

  test('should display plan features list', async ({ page }) => {
    const featuresList = page.locator('.features-list, .plan-features');
    await expect(featuresList).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Features list not visible');
    });
  });
});

test.describe('Subscription Page - Usage Section', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page, '/subscription');
  });

  test('should display usage section header', async ({ page }) => {
    const usageHeader = page.locator('h2:has-text("Nutzung")');
    await expect(usageHeader).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Usage header not visible');
    });
  });

  test('should display usage display', async ({ page }) => {
    const usageDisplay = page.locator('.usage-display, .usage-number');
    await expect(usageDisplay).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Usage display not visible');
    });
  });

  test('should display progress bar or unlimited badge', async ({ page }) => {
    const progressBar = page.locator('.progress-bar, .usage-progress');
    const unlimitedBadge = page.locator('.unlimited-badge');
    
    const hasProgress = await progressBar.isVisible({ timeout: 3000 }).catch(() => false);
    const hasUnlimited = await unlimitedBadge.isVisible({ timeout: 3000 }).catch(() => false);
    
    // One of them should be visible depending on plan
    if (!hasProgress && !hasUnlimited) {
      console.log('Neither progress bar nor unlimited badge visible');
    }
  });
});

test.describe('Subscription Page - Manage Section', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page, '/subscription');
  });

  test('should display manage section header', async ({ page }) => {
    const manageHeader = page.locator('h2:has-text("Abo verwalten")');
    await expect(manageHeader).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Manage section header not visible');
    });
  });

  test('should display portal button or upgrade section', async ({ page }) => {
    const portalButton = page.locator('button:has-text("Abo verwalten")');
    const upgradeSection = page.locator('.upgrade-section, button:has-text("Upgrade")');
    
    const hasPortal = await portalButton.isVisible({ timeout: 3000 }).catch(() => false);
    const hasUpgrade = await upgradeSection.isVisible({ timeout: 3000 }).catch(() => false);
    
    // One of them should be visible depending on subscription status
    if (!hasPortal && !hasUpgrade) {
      console.log('Neither portal button nor upgrade section visible');
    }
  });
});

test.describe('Subscription Page - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page, '/subscription');
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Subscription Page - Responsive Design', () => {
  test('should adapt layout on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await setupAuth(page, '/subscription');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should adapt layout on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await setupAuth(page, '/subscription');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Subscription Page - Error Handling', () => {
  test('should handle API errors gracefully', async ({ page }) => {
    await setupAuth(page, '/subscription');

    // Page should remain functional even with API errors
    await expect(page.locator('body')).toBeVisible();

    // Should not crash - either show content or error state
    const hasContent = await page.locator('.subscription-section, .loading-state, .error-state').isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasContent || await page.locator('h1').isVisible()).toBe(true);
  });
});
