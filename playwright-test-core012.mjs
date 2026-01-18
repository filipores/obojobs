import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Test setup - navigate and login
  console.log('[TEST] Starting CORE-012 test...');
  
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(1000);
  
  // Check if logged in by looking for dashboard or login page
  const currentUrl = page.url();
  console.log('[TEST] Current URL:', currentUrl);
  
  if (currentUrl.includes('/login') || currentUrl.includes('/register')) {
    console.log('[TEST] Not logged in, performing login...');
    await page.goto('http://localhost:3000/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'Test123!');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  }
  
  // Navigate to new-application
  console.log('[TEST] Navigating to /new-application...');
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);
  
  // Take screenshot of initial state
  await page.screenshot({ path: 'test-screenshots/core012-initial.png', fullPage: true });
  console.log('[TEST] Took initial screenshot');
  
  // Check for URL input field
  const urlInput = await page.locator('input[type="url"], input[placeholder*="URL"]').first();
  if (await urlInput.isVisible()) {
    console.log('[TEST] URL input found');
    
    // Enter a test URL
    await urlInput.fill('https://www.stepstone.de/stellenangebote--Software-Developer-Berlin--12345678.html');
    await page.waitForTimeout(500);
    
    // Click load button
    const loadBtn = await page.locator('button:has-text("Stellenanzeige laden")').first();
    if (await loadBtn.isVisible()) {
      console.log('[TEST] Clicking load button...');
      await loadBtn.click();
      await page.waitForTimeout(3000);
      
      // Take screenshot after loading
      await page.screenshot({ path: 'test-screenshots/core012-after-load.png', fullPage: true });
      console.log('[TEST] Took screenshot after URL load');
    }
  }
  
  // Check for generate button
  const genBtn = await page.locator('button:has-text("Bewerbung generieren")').first();
  if (await genBtn.isVisible()) {
    console.log('[TEST] Generate button found');
    
    // Check if button is disabled
    const isDisabled = await genBtn.isDisabled();
    console.log('[TEST] Generate button disabled state:', isDisabled);
    
    // Click generate button
    console.log('[TEST] Clicking generate button...');
    await genBtn.click();
    
    // Immediately check for loading state
    await page.waitForTimeout(100);
    const loadingText = await page.locator('text=Generiere Bewerbung').isVisible();
    console.log('[TEST] Loading text visible:', loadingText);
    
    const spinner = await page.locator('.loading-spinner').first();
    const spinnerVisible = await spinner.isVisible().catch(() => false);
    console.log('[TEST] Loading spinner visible:', spinnerVisible);
    
    // Take screenshot during loading
    await page.screenshot({ path: 'test-screenshots/core012-loading.png', fullPage: true });
    console.log('[TEST] Took screenshot during loading');
    
    // Check button is disabled during generation
    const btnDisabledDuring = await genBtn.isDisabled();
    console.log('[TEST] Button disabled during generation:', btnDisabledDuring);
    
    // Wait for completion
    await page.waitForTimeout(10000);
    
    // Check for success modal
    const modal = await page.locator('.modal-overlay').first();
    const modalVisible = await modal.isVisible().catch(() => false);
    console.log('[TEST] Success modal visible:', modalVisible);
    
    // Take final screenshot
    await page.screenshot({ path: 'test-screenshots/core012-final.png', fullPage: true });
    console.log('[TEST] Took final screenshot');
    
    // Check modal content
    if (modalVisible) {
      const successIcon = await page.locator('.success-icon').isVisible().catch(() => false);
      const firma = await page.locator('.modal-content').textContent().catch(() => '');
      console.log('[TEST] Success icon visible:', successIcon);
      console.log('[TEST] Modal content:', firma.substring(0, 100));
    }
  }
  
  console.log('[TEST] Test complete!');
  await browser.close();
})();
