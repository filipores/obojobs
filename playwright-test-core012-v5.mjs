import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();

  // Enable console and network logging
  page.on('console', msg => console.log('[BROWSER]', msg.text()));

  console.log('[TEST] Starting CORE-012 test...');

  // First, try to register a new user
  await page.goto('http://localhost:3000/register');
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'test-screenshots/core012-register.png', fullPage: true });

  // Generate unique email
  const timestamp = Math.floor(Math.random() * 1000000);
  const uniqueEmail = `ralph-test-${timestamp}@example.com`;
  console.log('[TEST] Using email:', uniqueEmail);

  // Fill registration form properly
  // Input 0: name, Input 1: email, Input 2: password
  const nameInput = page.locator('input[type="text"]').first();
  const emailInput = page.locator('input[type="email"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  await nameInput.fill('Test User');
  await emailInput.fill(uniqueEmail);
  await passwordInput.fill('TestPass123!');

  await page.screenshot({ path: 'test-screenshots/core012-register-filled.png', fullPage: true });

  // Click register button
  const registerBtn = page.locator('button[type="submit"], button:has-text("Registrieren")').first();
  if (await registerBtn.isVisible()) {
    console.log('[TEST] Clicking register button...');
    await registerBtn.click();
    await page.waitForTimeout(4000);
  }

  console.log('[TEST] After register URL:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-after-register.png', fullPage: true });

  // Check if we got redirected somewhere
  const afterRegisterUrl = page.url();

  // If still on register, check for error messages
  if (afterRegisterUrl.includes('/register')) {
    const errorMsg = await page.locator('.error, .toast-error, [class*="error"]').textContent().catch(() => 'No error found');
    console.log('[TEST] Error message:', errorMsg);
  }

  // If redirected to login, login
  if (afterRegisterUrl.includes('/login')) {
    console.log('[TEST] Redirected to login, logging in...');
    await page.locator('input[type="email"]').fill(uniqueEmail);
    await page.locator('input[type="password"]').fill('TestPass123!');
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    console.log('[TEST] After login URL:', page.url());
  }

  // If we're on dashboard or another page, try to go to new-application
  const currentUrl = page.url();
  console.log('[TEST] Current URL before nav:', currentUrl);

  // Navigate to new-application
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);

  console.log('[TEST] On new-application page, URL:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-newapp.png', fullPage: true });

  // Check token
  const token = await page.evaluate(() => localStorage.getItem('token'));
  console.log('[TEST] Token in localStorage:', token ? 'present (' + token.substring(0, 20) + '...)' : 'absent');

  // If we're on the new-application page, test the feature
  if (page.url().includes('/new-application')) {
    console.log('[TEST] Successfully on new-application page!');

    // Look for URL input
    const urlInput = await page.locator('input[type="url"], input[placeholder*="URL"], input[placeholder*="http"]').first();
    if (await urlInput.isVisible()) {
      console.log('[TEST] URL input found');

      // Enter test URL
      await urlInput.fill('https://www.stepstone.de/stellenangebote--Software-Developer-Berlin--12345.html');
      await page.waitForTimeout(500);

      // Find load button
      const loadBtn = await page.locator('button:has-text("laden")').first();
      if (await loadBtn.isVisible()) {
        console.log('[TEST] Clicking load button...');
        await loadBtn.click();
        await page.waitForTimeout(8000);
        await page.screenshot({ path: 'test-screenshots/core012-after-load.png', fullPage: true });
      }
    }

    // Check for generate button
    const genBtn = await page.locator('button:has-text("generieren")').first();
    if (await genBtn.count() > 0) {
      const btnText = await genBtn.textContent();
      const isDisabled = await genBtn.isDisabled();
      console.log('[TEST] Generate button: "' + btnText.trim() + '", disabled:', isDisabled);

      if (!isDisabled) {
        console.log('[TEST] === TESTING LOADING STATE ===');

        // Click and immediately check loading state
        const clickPromise = genBtn.click();

        // Rapid screenshots
        for (let i = 0; i < 5; i++) {
          await page.waitForTimeout(200);
          await page.screenshot({ path: `test-screenshots/core012-loading-${i}.png`, fullPage: true });

          const btnTextNow = await genBtn.textContent().catch(() => 'error');
          const isDisabledNow = await genBtn.isDisabled().catch(() => false);
          const hasSpinner = await page.locator('.loading-spinner').count();

          console.log(`[TEST] Loading check ${i}: text="${btnTextNow?.trim()}", disabled=${isDisabledNow}, spinners=${hasSpinner}`);
        }

        // Wait for completion
        await page.waitForTimeout(15000);
        await page.screenshot({ path: 'test-screenshots/core012-after-gen.png', fullPage: true });

        // Check for modal
        const hasModal = await page.locator('.modal-overlay').count() > 0;
        console.log('[TEST] Modal present after generation:', hasModal);

        if (hasModal) {
          await page.screenshot({ path: 'test-screenshots/core012-success-modal.png', fullPage: true });

          const modalContent = await page.locator('.modal').textContent().catch(() => '');
          console.log('[TEST] Modal content:', modalContent?.substring(0, 200));

          // Check for success icon
          const hasSuccessIcon = await page.locator('.success-icon, .success-header').count() > 0;
          console.log('[TEST] Has success icon:', hasSuccessIcon);
        }
      }
    } else {
      console.log('[TEST] Generate button not found');

      // List all buttons
      const buttons = await page.locator('button:visible').all();
      console.log('[TEST] Visible buttons:');
      for (let i = 0; i < buttons.length; i++) {
        const text = await buttons[i].textContent();
        console.log(`  - "${text?.trim().substring(0, 50)}"`);
      }
    }
  }

  console.log('[TEST] Test complete!');
  await browser.close();
})();
