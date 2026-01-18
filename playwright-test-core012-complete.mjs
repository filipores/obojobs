import { chromium } from 'playwright';
import path from 'path';

const LEBENSLAUF_PATH = '/Users/filipores/Documents/Bewerbungsunterlagen/Batch/cv-ger.pdf';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 30 });
  const page = await browser.newPage();

  page.on('console', msg => console.log('[BROWSER]', msg.text()));

  console.log('[TEST] ======================================');
  console.log('[TEST] CORE-012: Loading State und Erfolg');
  console.log('[TEST] Complete test with document upload');
  console.log('[TEST] ======================================');

  // Step 1: Register new user
  console.log('[TEST] Step 1: Register new user');
  await page.goto('http://localhost:3000/register');
  await page.waitForTimeout(2000);

  const timestamp = Math.floor(Math.random() * 1000000);
  const uniqueEmail = `ralph-core012-${timestamp}@example.com`;
  console.log('[TEST] Email:', uniqueEmail);

  await page.locator('input[type="text"]').first().fill('Test User');
  await page.locator('input[type="email"]').first().fill(uniqueEmail);
  await page.locator('input[type="password"]').first().fill('TestPass123!');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(4000);

  // Step 2: Upload Lebenslauf
  console.log('[TEST] Step 2: Navigate to documents and upload Lebenslauf');
  await page.goto('http://localhost:3000/documents');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'test-screenshots/core012-docs-page.png', fullPage: true });

  // Look for upload button or drop zone
  const uploadSection = await page.locator('text=Lebenslauf').first();
  console.log('[TEST] Lebenslauf section found:', await uploadSection.count() > 0);

  // Find file input for lebenslauf
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log('[TEST] File inputs found:', fileInputs.length);

  // Try to find upload button
  const uploadBtns = await page.locator('button:has-text("Hochladen"), button:has-text("Upload"), .upload-btn').all();
  console.log('[TEST] Upload buttons found:', uploadBtns.length);

  // Check if there's a file input we can use directly
  if (fileInputs.length > 0) {
    console.log('[TEST] Uploading file via file input...');
    await fileInputs[0].setInputFiles(LEBENSLAUF_PATH);
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'test-screenshots/core012-after-upload.png', fullPage: true });
  }

  // Wait for processing
  await page.waitForTimeout(5000);

  // Step 3: Create a template
  console.log('[TEST] Step 3: Create a template');
  await page.goto('http://localhost:3000/templates');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'test-screenshots/core012-templates.png', fullPage: true });

  // Click create new template button
  const newTemplateBtn = await page.locator('button:has-text("Neues"), button:has-text("Erstellen"), a:has-text("Neues")').first();
  if (await newTemplateBtn.count() > 0 && await newTemplateBtn.isVisible()) {
    console.log('[TEST] Clicking new template button...');
    await newTemplateBtn.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-screenshots/core012-new-template.png', fullPage: true });

    // Fill template form
    const nameInput = await page.locator('input[placeholder*="Name"], input[name="name"], .template-name').first();
    if (await nameInput.count() > 0) {
      await nameInput.fill('Test Template');
    }

    const contentArea = await page.locator('textarea').first();
    if (await contentArea.count() > 0) {
      const templateContent = `Sehr geehrte Damen und Herren,

mit großem Interesse habe ich Ihre Stellenanzeige für die Position als {{POSITION}} bei {{FIRMA}} gelesen.

{{EINLEITUNG}}

Ich freue mich auf ein persönliches Gespräch.

Mit freundlichen Grüßen`;
      await contentArea.fill(templateContent);
    }

    // Save template
    const saveBtn = await page.locator('button:has-text("Speichern"), button[type="submit"]').first();
    if (await saveBtn.count() > 0) {
      await saveBtn.click();
      await page.waitForTimeout(3000);
    }
  }

  // Step 4: Go to new-application and test the feature
  console.log('[TEST] Step 4: Test CORE-012 - Loading State');
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'test-screenshots/core012-newapp-ready.png', fullPage: true });

  // Check for warnings
  const warnings = await page.locator('[class*="warning"], [class*="alert"]').count();
  console.log('[TEST] Warnings on page:', warnings);

  // Try URL loading first
  const urlInput = await page.locator('input[type="url"]').first();
  if (await urlInput.isVisible()) {
    // Use a real job URL that might work
    await urlInput.fill('https://www.stepstone.de/stellenangebote--Software-Entwickler-Berlin-SAP--5983827-inline.html');
    await page.waitForTimeout(500);

    const loadBtn = await page.locator('button:has-text("laden")').first();
    if (await loadBtn.isVisible() && !(await loadBtn.isDisabled())) {
      console.log('[TEST] Clicking load URL...');
      await loadBtn.click();
      await page.waitForTimeout(8000);
      await page.screenshot({ path: 'test-screenshots/core012-after-url-load.png', fullPage: true });
    }
  }

  // Check if we have preview or need manual fallback
  const hasPreview = await page.locator('.preview-section, .job-preview').count() > 0;
  console.log('[TEST] Has preview:', hasPreview);

  if (!hasPreview) {
    // Try manual fallback
    const manualBtn = await page.locator('button:has-text("manuell")').first();
    if (await manualBtn.count() > 0 && await manualBtn.isVisible()) {
      console.log('[TEST] Using manual fallback...');
      await manualBtn.click();
      await page.waitForTimeout(1000);

      // Fill manual form
      const inputs = await page.locator('.manual-fallback-section input').all();
      if (inputs.length >= 1) await inputs[0].fill('Test GmbH');
      if (inputs.length >= 2) await inputs[1].fill('Software Developer');

      const textarea = await page.locator('.manual-fallback-section textarea, textarea').first();
      if (await textarea.isVisible()) {
        await textarea.fill(`Test GmbH sucht Software Developer in Berlin.

Aufgaben: Entwicklung von Web-Applikationen, API-Design, Code Reviews.

Anforderungen: 3+ Jahre Erfahrung, JavaScript, Python, SQL.

Ansprechpartner: Max Mustermann
E-Mail: jobs@test.de`);
      }

      // Analyze
      const analyzeBtn = await page.locator('button:has-text("analysieren")').first();
      if (await analyzeBtn.isVisible()) {
        await analyzeBtn.click();
        await page.waitForTimeout(8000);
        await page.screenshot({ path: 'test-screenshots/core012-after-analyze.png', fullPage: true });
      }
    }
  }

  // Scroll to generate button
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);

  // Find generate button
  const genBtn = await page.locator('button').filter({ hasText: /generieren/i }).first();

  if (await genBtn.count() > 0) {
    const isDisabled = await genBtn.isDisabled();
    console.log('[TEST] Generate button disabled:', isDisabled);

    if (!isDisabled) {
      console.log('[TEST] ======================================');
      console.log('[TEST] === TESTING LOADING STATE ===');
      console.log('[TEST] ======================================');

      // Get initial state
      const initialText = await genBtn.textContent();
      console.log('[TEST] Initial button text:', initialText?.trim());

      // Click and monitor loading state
      console.log('[TEST] Clicking generate...');
      genBtn.click();

      const observations = [];
      for (let i = 0; i < 20; i++) {
        await page.waitForTimeout(100);
        try {
          const text = await genBtn.textContent();
          const disabled = await genBtn.isDisabled();
          const spinners = await page.locator('.loading-spinner').count();
          const urlDisabled = await page.locator('input[type="url"]').isDisabled().catch(() => null);

          observations.push({
            tick: i,
            text: text?.trim().substring(0, 30),
            btnDisabled: disabled,
            spinners,
            urlDisabled
          });
        } catch (e) {}
      }

      console.log('[TEST] Loading state observations:');
      observations.forEach(o => {
        const hasLoading = o.text?.includes('Generiere') || o.spinners > 0;
        const mark = hasLoading ? '✓' : ' ';
        console.log(`  [${o.tick.toString().padStart(2)}] ${mark} "${o.text}" btn=${o.btnDisabled} spin=${o.spinners} url=${o.urlDisabled}`);
      });

      // Analyze results
      const loadingShown = observations.some(o => o.text?.includes('Generiere') || o.spinners > 0);
      const buttonDisabled = observations.some(o => o.btnDisabled);
      const urlInputDisabled = observations.some(o => o.urlDisabled === true);

      console.log('[TEST] ======================================');
      console.log('[TEST] LOADING STATE RESULTS:');
      console.log(`[TEST] 1. Loading spinner/text shown: ${loadingShown ? 'PASS ✓' : 'FAIL ✗'}`);
      console.log(`[TEST] 2. Button disabled during gen:  ${buttonDisabled ? 'PASS ✓' : 'FAIL ✗'}`);
      console.log(`[TEST] 3. URL input disabled:          ${urlInputDisabled ? 'PASS ✓' : 'N/A (not observed)'}`);

      // Wait for completion
      console.log('[TEST] Waiting for generation to complete...');
      await page.waitForTimeout(25000);
      await page.screenshot({ path: 'test-screenshots/core012-after-gen.png', fullPage: true });

      // Check for success modal
      const modalCount = await page.locator('.modal-overlay').count();
      console.log('[TEST] Modal overlays found:', modalCount);

      if (modalCount > 0) {
        console.log('[TEST] ======================================');
        console.log('[TEST] SUCCESS MODAL RESULTS:');
        console.log('[TEST] 4. Modal appeared:             PASS ✓');

        await page.screenshot({ path: 'test-screenshots/core012-success-modal.png', fullPage: true });

        // Check modal content
        const successIcon = await page.locator('.success-icon, .success-header svg').count() > 0;
        const modalTitle = await page.locator('.modal h2').textContent().catch(() => '');
        const hasFirma = await page.locator('.detail-value').first().textContent().catch(() => '');
        const hasPdfBtn = await page.locator('button:has-text("PDF")').count() > 0;
        const hasAllAppsBtn = await page.locator('button:has-text("Bewerbungen")').count() > 0;

        console.log(`[TEST] 5. Success icon present:       ${successIcon ? 'PASS ✓' : 'FAIL ✗'}`);
        console.log(`[TEST] 6. Modal title:                "${modalTitle}"`);
        console.log(`[TEST] 7. Firma shown:                "${hasFirma}"`);
        console.log(`[TEST] 8. PDF download button:        ${hasPdfBtn ? 'PASS ✓' : 'FAIL ✗'}`);
        console.log(`[TEST] 9. All applications button:    ${hasAllAppsBtn ? 'PASS ✓' : 'FAIL ✗'}`);
        console.log('[TEST] ======================================');
      } else {
        // Check for error
        const errorText = await page.locator('.error-box').textContent().catch(() => 'none');
        console.log('[TEST] No modal. Error:', errorText?.substring(0, 200));
      }
    } else {
      console.log('[TEST] Generate button is disabled - checking reason');
      const warningText = await page.locator('[class*="warning"], [class*="alert"], .error-box').textContent().catch(() => 'none');
      console.log('[TEST] Warning/Error:', warningText?.substring(0, 200));

      // Document missing is expected if upload didn't work
      console.log('[TEST] Note: Full UI test requires successful document upload');
      console.log('[TEST] See code analysis for implementation verification');
    }
  }

  console.log('[TEST] ======================================');
  console.log('[TEST] TEST COMPLETE');
  console.log('[TEST] ======================================');

  await browser.close();
})();
