import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();

  // Enable console and network logging
  page.on('console', msg => console.log('[BROWSER]', msg.text()));

  console.log('[TEST] Starting CORE-012 test - Testing Loading State and Success Modal...');

  // Register new user
  await page.goto('http://localhost:3000/register');
  await page.waitForTimeout(2000);

  const timestamp = Math.floor(Math.random() * 1000000);
  const uniqueEmail = `ralph-test-${timestamp}@example.com`;
  console.log('[TEST] Registering with email:', uniqueEmail);

  await page.locator('input[type="text"]').first().fill('Test User');
  await page.locator('input[type="email"]').first().fill(uniqueEmail);
  await page.locator('input[type="password"]').first().fill('TestPass123!');

  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(4000);

  // Navigate to new-application
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);

  console.log('[TEST] On page:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-start.png', fullPage: true });

  // We need documents for generation to work - first upload a resume
  // Check if there's a warning about missing resume
  const hasResumeWarning = await page.locator('text=Lebenslauf').count() > 0;
  console.log('[TEST] Resume warning present:', hasResumeWarning);

  // Use manual fallback to test the generation flow
  const manualBtn = await page.locator('button:has-text("manuell")').first();
  if (await manualBtn.isVisible()) {
    console.log('[TEST] Clicking manual entry button...');
    await manualBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-screenshots/core012-manual-form.png', fullPage: true });
  }

  // Fill manual form
  const companyInput = await page.locator('input[placeholder*="Firma"], input[placeholder*="Company"], label:has-text("Firma") + input, #company').first();
  const titleInput = await page.locator('input[placeholder*="Position"], input[placeholder*="Title"], label:has-text("Position") + input, #title').first();
  const textArea = await page.locator('textarea').first();

  // List all inputs to find the right ones
  const allInputs = await page.locator('input:visible').all();
  console.log('[TEST] Found', allInputs.length, 'visible inputs');
  for (let i = 0; i < allInputs.length; i++) {
    const placeholder = await allInputs[i].getAttribute('placeholder');
    const type = await allInputs[i].getAttribute('type');
    console.log(`[TEST] Input ${i}: type="${type}" placeholder="${placeholder}"`);
  }

  // Find inputs by placeholder
  const firmaInput = await page.locator('input[placeholder*="irma"]').first();
  const positionInput = await page.locator('input[placeholder*="osition"]').first();

  if (await firmaInput.isVisible()) {
    await firmaInput.fill('Test GmbH');
    console.log('[TEST] Filled company input');
  }

  if (await positionInput.isVisible()) {
    await positionInput.fill('Software Developer');
    console.log('[TEST] Filled position input');
  }

  if (await textArea.isVisible()) {
    const jobText = `Test GmbH sucht einen erfahrenen Software Developer für unser Team in Berlin.

Ihre Aufgaben:
- Entwicklung von Web-Applikationen mit Vue.js und Python
- Code Reviews und Qualitätssicherung
- Zusammenarbeit im agilen Team

Ihr Profil:
- 3+ Jahre Erfahrung in der Softwareentwicklung
- Kenntnisse in JavaScript, TypeScript, Python
- Erfahrung mit REST APIs
- Teamfähigkeit und selbstständige Arbeitsweise

Wir bieten:
- Flexible Arbeitszeiten
- Home Office Möglichkeit
- Weiterbildungsbudget

Bitte senden Sie Ihre Bewerbung an hr@testgmbh.de`;

    await textArea.fill(jobText);
    console.log('[TEST] Filled job text');
  }

  await page.screenshot({ path: 'test-screenshots/core012-form-filled.png', fullPage: true });

  // Click analyze button
  const analyzeBtn = await page.locator('button:has-text("analysieren")').first();
  if (await analyzeBtn.isVisible()) {
    console.log('[TEST] Clicking analyze button...');
    await analyzeBtn.click();
    await page.waitForTimeout(8000);
    await page.screenshot({ path: 'test-screenshots/core012-after-analyze.png', fullPage: true });
  }

  // Now look for generate button
  const genBtn = await page.locator('button:has-text("generieren")').first();
  if (await genBtn.count() > 0 && await genBtn.isVisible()) {
    const isDisabled = await genBtn.isDisabled();
    console.log('[TEST] Generate button found, disabled:', isDisabled);

    if (!isDisabled) {
      console.log('[TEST] ======================================');
      console.log('[TEST] TESTING CORE-012: Loading State');
      console.log('[TEST] ======================================');

      // Record button text before click
      const btnTextBefore = await genBtn.textContent();
      console.log('[TEST] Button text BEFORE click:', btnTextBefore?.trim());

      // Click generate
      console.log('[TEST] Clicking generate...');
      genBtn.click(); // Don't await

      // Rapid checks for loading state
      const checks = [];
      for (let i = 0; i < 10; i++) {
        await page.waitForTimeout(150);

        const btnText = await genBtn.textContent().catch(() => 'error');
        const btnDisabled = await genBtn.isDisabled().catch(() => false);
        const spinnerCount = await page.locator('.loading-spinner').count();
        const hasLoadingText = btnText?.includes('Generiere') || false;

        checks.push({
          iteration: i,
          text: btnText?.trim()?.substring(0, 30),
          disabled: btnDisabled,
          spinners: spinnerCount,
          hasLoadingText
        });

        if (i === 0 || i === 2 || i === 5) {
          await page.screenshot({ path: `test-screenshots/core012-loading-${i}.png`, fullPage: true });
        }
      }

      console.log('[TEST] Loading state checks:');
      checks.forEach(c => {
        console.log(`  [${c.iteration}] text="${c.text}" disabled=${c.disabled} spinners=${c.spinners} loadingText=${c.hasLoadingText}`);
      });

      // Verify loading state was shown
      const loadingStateShown = checks.some(c => c.hasLoadingText || c.spinners > 0);
      const buttonWasDisabled = checks.some(c => c.disabled);
      console.log('[TEST] Loading state was shown:', loadingStateShown);
      console.log('[TEST] Button was disabled during generation:', buttonWasDisabled);

      // Wait for generation to complete
      console.log('[TEST] Waiting for generation to complete...');
      await page.waitForTimeout(20000);
      await page.screenshot({ path: 'test-screenshots/core012-after-generation.png', fullPage: true });

      // Check for success modal
      const modalOverlay = await page.locator('.modal-overlay').count();
      const successHeader = await page.locator('.success-header, .success-icon').count();
      console.log('[TEST] Modal overlay count:', modalOverlay);
      console.log('[TEST] Success header/icon count:', successHeader);

      if (modalOverlay > 0) {
        console.log('[TEST] ======================================');
        console.log('[TEST] SUCCESS MODAL APPEARED!');
        console.log('[TEST] ======================================');

        await page.screenshot({ path: 'test-screenshots/core012-success-modal.png', fullPage: true });

        // Get modal content
        const modalTitle = await page.locator('.modal h2, .modal-header h2').textContent().catch(() => 'N/A');
        const firma = await page.locator('.detail-value').first().textContent().catch(() => 'N/A');
        console.log('[TEST] Modal title:', modalTitle);
        console.log('[TEST] Firma in modal:', firma);

        // Check for PDF download button
        const pdfBtn = await page.locator('button:has-text("PDF")').count();
        const allAppsBtn = await page.locator('button:has-text("Bewerbungen")').count();
        console.log('[TEST] PDF download button present:', pdfBtn > 0);
        console.log('[TEST] All applications button present:', allAppsBtn > 0);
      } else {
        // Check for error
        const errorBox = await page.locator('.error-box, .error').textContent().catch(() => 'No error');
        console.log('[TEST] No modal found. Error:', errorBox?.substring(0, 200));
      }
    } else {
      console.log('[TEST] Generate button is disabled');

      // Check why
      const errorText = await page.locator('.error-box, [class*="error"], [class*="warning"]').textContent().catch(() => 'None');
      console.log('[TEST] Error/warning messages:', errorText?.substring(0, 200));
    }
  } else {
    console.log('[TEST] Generate button not found or not visible');

    // List buttons
    const buttons = await page.locator('button:visible').all();
    console.log('[TEST] Visible buttons:');
    for (const btn of buttons) {
      const text = await btn.textContent();
      console.log(`  - "${text?.trim().substring(0, 50)}"`);
    }
  }

  console.log('[TEST] ======================================');
  console.log('[TEST] TEST COMPLETE');
  console.log('[TEST] ======================================');

  await browser.close();
})();
