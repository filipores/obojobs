import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => console.log('[BROWSER]', msg.text()));
  
  console.log('[TEST] Starting CORE-012 test...');
  
  // Go to login
  await page.goto('http://localhost:3000/login');
  await page.waitForTimeout(2000);
  
  // Take screenshot of login
  await page.screenshot({ path: 'test-screenshots/core012-login.png', fullPage: true });
  
  // Try to get accessibility snapshot
  const loginSnapshot = await page.accessibility.snapshot();
  console.log('[TEST] Login page accessible elements:', JSON.stringify(loginSnapshot?.children?.slice(0, 5), null, 2));
  
  // Find inputs
  const emailInput = page.locator('input').first();
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
  
  // Get page content
  const pageContent = await page.content();
  const hasUrlInput = pageContent.includes('url') || pageContent.includes('URL');
  const hasGenerateBtn = pageContent.includes('generieren') || pageContent.includes('Bewerbung');
  console.log('[TEST] Page has URL-related content:', hasUrlInput);
  console.log('[TEST] Page has Generate-related content:', hasGenerateBtn);
  
  // List all buttons
  const buttons = await page.locator('button').all();
  console.log('[TEST] Found', buttons.length, 'buttons');
  for (let i = 0; i < Math.min(buttons.length, 10); i++) {
    const text = await buttons[i].textContent();
    console.log(`[TEST] Button ${i}: "${text?.trim().substring(0, 50)}"`);
  }
  
  await browser.close();
})();
