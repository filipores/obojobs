import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => console.log('[BROWSER]', msg.text()));
  
  console.log('[TEST] Starting CORE-012 test...');
  
  // Go to login
  await page.goto('http://localhost:3000/login');
  await page.waitForTimeout(2000);
  
  // Take screenshot of login
  await page.screenshot({ path: 'test-screenshots/core012-login.png', fullPage: true });
  
  // Find inputs
  const allInputs = await page.locator('input').all();
  console.log('[TEST] Found', allInputs.length, 'inputs on login page');
  
  for (let i = 0; i < allInputs.length; i++) {
    const type = await allInputs[i].getAttribute('type');
    const placeholder = await allInputs[i].getAttribute('placeholder');
    console.log(`[TEST] Input ${i}: type="${type}" placeholder="${placeholder}"`);
  }
  
  // Fill login form
  if (allInputs.length >= 2) {
    await allInputs[0].fill('test@example.com');
    await allInputs[1].fill('Test123!');
    
    // Find and click submit button
    const submitBtn = page.locator('button[type="submit"], button:has-text("Anmelden"), button:has-text("Login")').first();
    if (await submitBtn.isVisible()) {
      console.log('[TEST] Clicking login button...');
      await submitBtn.click();
      await page.waitForTimeout(3000);
    }
  }
  
  // Check current URL
  console.log('[TEST] After login URL:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-after-login.png', fullPage: true });
  
  // Navigate to new-application
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);
  
  console.log('[TEST] On new-application page, URL:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-newapp.png', fullPage: true });
  
  // List all buttons
  const buttons = await page.locator('button').all();
  console.log('[TEST] Found', buttons.length, 'buttons');
  for (let i = 0; i < Math.min(buttons.length, 10); i++) {
    const text = await buttons[i].textContent();
    const isDisabled = await buttons[i].isDisabled();
    console.log(`[TEST] Button ${i}: "${text?.trim().substring(0, 50)}" (disabled: ${isDisabled})`);
  }
  
  // Look for URL input
  const urlInputs = await page.locator('input[type="url"], input[placeholder*="URL"], input[placeholder*="http"]').all();
  console.log('[TEST] Found', urlInputs.length, 'URL inputs');
  
  if (urlInputs.length > 0) {
    // Enter test URL
    await urlInputs[0].fill('https://www.stepstone.de/stellenangebote--Test-Job-Berlin--12345.html');
    await page.waitForTimeout(500);
    
    // Find load button
    const loadBtn = await page.locator('button').filter({ hasText: /laden/i }).first();
    if (await loadBtn.isVisible()) {
      console.log('[TEST] Clicking load button...');
      await loadBtn.click();
      await page.waitForTimeout(5000);
      await page.screenshot({ path: 'test-screenshots/core012-after-load.png', fullPage: true });
    }
  }
  
  // Check for generate button now
  const genBtn = await page.locator('button').filter({ hasText: /generieren/i }).first();
  if (await genBtn.count() > 0 && await genBtn.isVisible()) {
    console.log('[TEST] Generate button found');
    
    // Check initial disabled state
    const initialDisabled = await genBtn.isDisabled();
    console.log('[TEST] Generate button initially disabled:', initialDisabled);
    
    // If not disabled, click it
    if (!initialDisabled) {
      console.log('[TEST] Clicking generate button...');
      
      // Create a promise to catch the loading state
      const clickPromise = genBtn.click();
      
      // Take rapid screenshots to catch loading state
      await page.waitForTimeout(100);
      await page.screenshot({ path: 'test-screenshots/core012-loading-1.png', fullPage: true });
      
      await page.waitForTimeout(200);
      await page.screenshot({ path: 'test-screenshots/core012-loading-2.png', fullPage: true });
      
      // Check for loading spinner
      const hasLoadingSpinner = await page.locator('.loading-spinner').count() > 0;
      const hasLoadingText = await page.locator('text=Generiere').count() > 0;
      console.log('[TEST] Loading spinner present:', hasLoadingSpinner);
      console.log('[TEST] Loading text present:', hasLoadingText);
      
      // Check button is disabled during loading
      const disabledDuring = await genBtn.isDisabled();
      console.log('[TEST] Button disabled during generation:', disabledDuring);
      
      // Wait for completion
      await page.waitForTimeout(15000);
      await page.screenshot({ path: 'test-screenshots/core012-after-gen.png', fullPage: true });
      
      // Check for success modal
      const hasModal = await page.locator('.modal-overlay, .modal').count() > 0;
      const hasSuccessIcon = await page.locator('.success-icon').count() > 0;
      console.log('[TEST] Modal present:', hasModal);
      console.log('[TEST] Success icon present:', hasSuccessIcon);
      
      if (hasModal) {
        // Get modal content
        const modalText = await page.locator('.modal').textContent().catch(() => 'N/A');
        console.log('[TEST] Modal text:', modalText?.substring(0, 200));
        
        await page.screenshot({ path: 'test-screenshots/core012-success-modal.png', fullPage: true });
      }
    }
  } else {
    console.log('[TEST] Generate button not found or not visible');
  }
  
  console.log('[TEST] Test complete!');
  await browser.close();
})();
