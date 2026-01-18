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

  // Find all inputs on register page
  const regInputs = await page.locator('input').all();
  console.log('[TEST] Found', regInputs.length, 'inputs on register page');

  for (let i = 0; i < regInputs.length; i++) {
    const type = await regInputs[i].getAttribute('type');
    const placeholder = await regInputs[i].getAttribute('placeholder');
    const name = await regInputs[i].getAttribute('name');
    console.log(`[TEST] Input ${i}: type="${type}" placeholder="${placeholder}" name="${name}"`);
  }

  // Generate unique email
  const timestamp = Math.floor(Math.random() * 1000000);
  const uniqueEmail = `ralph-test-${timestamp}@example.com`;
  console.log('[TEST] Using email:', uniqueEmail);

  // Try to register
  const emailInput = page.locator('input[type="email"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  const passwordConfirm = page.locator('input[type="password"]').nth(1);

  if (await emailInput.isVisible()) {
    await emailInput.fill(uniqueEmail);
  }
  if (await passwordInput.isVisible()) {
    await passwordInput.fill('TestPass123!');
  }
  if (await passwordConfirm.count() > 0 && await passwordConfirm.isVisible()) {
    await passwordConfirm.fill('TestPass123!');
  }

  // Click register button
  const registerBtn = page.locator('button[type="submit"], button:has-text("Registrieren")').first();
  if (await registerBtn.isVisible()) {
    console.log('[TEST] Clicking register button...');
    await registerBtn.click();
    await page.waitForTimeout(3000);
  }

  console.log('[TEST] After register URL:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-after-register.png', fullPage: true });

  // If redirected to login or verification, login
  if (page.url().includes('/login')) {
    console.log('[TEST] Redirected to login, logging in...');
    await page.locator('input[type="email"]').fill(uniqueEmail);
    await page.locator('input[type="password"]').fill('TestPass123!');
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
  }

  console.log('[TEST] Current URL:', page.url());

  // Navigate to new-application
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);

  console.log('[TEST] On new-application page, URL:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-newapp.png', fullPage: true });

  // If still on login, we have auth issues
  if (page.url().includes('/login')) {
    console.log('[TEST] Still on login page - authentication not working');
    // Check localStorage for token
    const token = await page.evaluate(() => localStorage.getItem('token'));
    console.log('[TEST] Token in localStorage:', token ? 'present' : 'absent');
  }

  // List all visible buttons
  const buttons = await page.locator('button:visible').all();
  console.log('[TEST] Found', buttons.length, 'visible buttons');
  for (let i = 0; i < Math.min(buttons.length, 10); i++) {
    const text = await buttons[i].textContent();
    console.log(`[TEST] Button ${i}: "${text?.trim().substring(0, 50)}"`);
  }

  await browser.close();
})();
