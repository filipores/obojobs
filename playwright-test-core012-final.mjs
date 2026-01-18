import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 30 });
  const page = await browser.newPage();

  page.on('console', msg => console.log('[BROWSER]', msg.text()));

  console.log('[TEST] ======================================');
  console.log('[TEST] CORE-012: Loading State und Erfolg');
  console.log('[TEST] ======================================');

  // Register new user
  await page.goto('http://localhost:3000/register');
  await page.waitForTimeout(2000);

  const timestamp = Math.floor(Math.random() * 1000000);
  const uniqueEmail = `ralph-core012-${timestamp}@example.com`;
  console.log('[TEST] Registering:', uniqueEmail);

  await page.locator('input[type="text"]').first().fill('Test User');
  await page.locator('input[type="email"]').first().fill(uniqueEmail);
  await page.locator('input[type="password"]').first().fill('TestPass123!');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(4000);

  // Go to new-application
  await page.goto('http://localhost:3000/new-application');
  await page.waitForTimeout(2000);

  console.log('[TEST] On:', page.url());
  await page.screenshot({ path: 'test-screenshots/core012-01-initial.png', fullPage: true });

  // Check for Lebenslauf warning
  const hasLebenslaufWarning = await page.locator('text=Lebenslauf').count() > 0;
  console.log('[TEST] Lebenslauf warning:', hasLebenslaufWarning);

  // First, trigger an error by using a blocked URL
  const urlInput = await page.locator('input[type="url"]').first();
  await urlInput.fill('https://www.linkedin.com/jobs/view/blocked-job-12345');
  await page.waitForTimeout(500);

  const loadBtn = await page.locator('button:has-text("laden")').first();
  console.log('[TEST] Clicking load to trigger error...');
  await loadBtn.click();
  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'test-screenshots/core012-02-error.png', fullPage: true });

  // Now click manual fallback button
  const manualBtn = await page.locator('button:has-text("manuell")').first();
  if (await manualBtn.isVisible()) {
    console.log('[TEST] Clicking manual entry button...');
    await manualBtn.click();
    await page.waitForTimeout(500);
  }

  await page.screenshot({ path: 'test-screenshots/core012-03-manual-form.png', fullPage: true });

  // Fill manual form
  await page.locator('input[placeholder*="Beispiel"]').fill('Test Software GmbH');
  await page.locator('input[placeholder*="Entwickler"]').fill('Senior Software Developer');

  const jobText = `Die Test Software GmbH sucht zum nächstmöglichen Zeitpunkt einen erfahrenen Senior Software Developer (m/w/d) für unser Team in Berlin.

Wir sind ein innovatives Technologie-Unternehmen mit Fokus auf moderne Web-Applikationen und Cloud-Lösungen.

Ihre Aufgaben:
- Entwicklung und Wartung von Web-Applikationen mit Vue.js und Python
- Design und Implementierung von RESTful APIs
- Code Reviews und technische Dokumentation
- Zusammenarbeit mit Product Ownern und UX Designern
- Mentoring von Junior Entwicklern

Ihr Profil:
- Mindestens 5 Jahre Berufserfahrung in der Softwareentwicklung
- Fundierte Kenntnisse in JavaScript/TypeScript und einem Backend-Framework
- Erfahrung mit relationalen Datenbanken (PostgreSQL, MySQL)
- Erfahrung mit Git und CI/CD Pipelines
- Gute Deutsch- und Englischkenntnisse

Wir bieten:
- Ein modernes Büro in Berlin Mitte
- Flexible Arbeitszeiten und Home Office
- Weiterbildungsbudget von 2.000€ pro Jahr
- 30 Tage Urlaub
- Regelmäßige Team-Events

Ansprechpartner: Frau Maria Schmidt, HR
E-Mail: jobs@test-software.de`;

  await page.locator('textarea').fill(jobText);
  await page.screenshot({ path: 'test-screenshots/core012-04-filled.png', fullPage: true });

  // Click analyze
  console.log('[TEST] Clicking analyze...');
  await page.locator('button:has-text("analysieren")').click();
  await page.waitForTimeout(8000);

  await page.screenshot({ path: 'test-screenshots/core012-05-analyzed.png', fullPage: true });

  // Check for preview section
  const hasPreview = await page.locator('text=Preview, .preview, section:has-text("Preview")').count() > 0;
  console.log('[TEST] Preview section found:', hasPreview);

  // Look for generate button
  let genBtn = await page.locator('button:has-text("generieren")').first();

  // If not found directly, scroll and wait
  if (await genBtn.count() === 0) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    genBtn = await page.locator('button:has-text("generieren")').first();
  }

  if (await genBtn.count() > 0 && await genBtn.isVisible()) {
    const isDisabled = await genBtn.isDisabled();
    console.log('[TEST] Generate button found, disabled:', isDisabled);

    if (isDisabled) {
      // Check why - maybe missing lebenslauf
      const errorText = await page.locator('.error-box, .alert, [class*="warning"]').textContent().catch(() => 'none');
      console.log('[TEST] Warning/Error:', errorText?.substring(0, 150));
      console.log('[TEST] Button disabled - likely due to missing Lebenslauf (expected for new user)');
      console.log('[TEST] Skipping generation test - would need document upload first');
    } else {
      console.log('[TEST] ======================================');
      console.log('[TEST] TESTING LOADING STATE');
      console.log('[TEST] ======================================');

      // Get button state before
      const btnTextBefore = await genBtn.textContent();
      console.log('[TEST] Button before:', btnTextBefore?.trim());

      // Click and check loading state
      genBtn.click();

      const loadingChecks = [];
      for (let i = 0; i < 15; i++) {
        await page.waitForTimeout(100);

        try {
          const btnText = await genBtn.textContent();
          const btnDisabled = await genBtn.isDisabled();
          const spinnerVisible = await page.locator('.loading-spinner').count() > 0;
          const hasLoadingText = btnText?.includes('Generiere') || btnText?.includes('...') || false;

          loadingChecks.push({
            i,
            text: btnText?.trim().substring(0, 25),
            disabled: btnDisabled,
            spinner: spinnerVisible,
            loading: hasLoadingText
          });
        } catch (e) {
          // Button might have changed
        }
      }

      console.log('[TEST] Loading state observations:');
      loadingChecks.forEach(c => {
        const indicator = (c.loading || c.spinner) ? '✓' : ' ';
        console.log(`  [${c.i.toString().padStart(2)}] ${indicator} text="${c.text}" disabled=${c.disabled} spinner=${c.spinner}`);
      });

      // Verify requirements
      const showedLoadingState = loadingChecks.some(c => c.loading || c.spinner);
      const buttonWasDisabled = loadingChecks.some(c => c.disabled);

      console.log('[TEST] ======================================');
      console.log('[TEST] LOADING STATE RESULTS:');
      console.log('[TEST] - Showed loading spinner/text:', showedLoadingState ? 'PASS ✓' : 'FAIL ✗');
      console.log('[TEST] - Button was disabled:', buttonWasDisabled ? 'PASS ✓' : 'FAIL ✗');
      console.log('[TEST] ======================================');

      // Wait for completion
      await page.waitForTimeout(20000);
      await page.screenshot({ path: 'test-screenshots/core012-06-after-gen.png', fullPage: true });

      // Check for success modal
      const modalCount = await page.locator('.modal-overlay').count();
      console.log('[TEST] Modal overlays found:', modalCount);

      if (modalCount > 0) {
        console.log('[TEST] ======================================');
        console.log('[TEST] SUCCESS MODAL RESULTS:');
        console.log('[TEST] - Modal appeared: PASS ✓');

        await page.screenshot({ path: 'test-screenshots/core012-07-modal.png', fullPage: true });

        // Check modal content
        const hasSuccessIcon = await page.locator('.success-icon, .success-header').count() > 0;
        const modalTitle = await page.locator('.modal h2').textContent().catch(() => 'N/A');
        const hasPdfBtn = await page.locator('button:has-text("PDF")').count() > 0;
        const hasAllAppsBtn = await page.locator('button:has-text("Bewerbungen")').count() > 0;

        console.log('[TEST] - Has success icon:', hasSuccessIcon ? 'PASS ✓' : 'FAIL ✗');
        console.log('[TEST] - Modal title:', modalTitle);
        console.log('[TEST] - PDF download button:', hasPdfBtn ? 'PASS ✓' : 'FAIL ✗');
        console.log('[TEST] - All applications button:', hasAllAppsBtn ? 'PASS ✓' : 'FAIL ✗');
        console.log('[TEST] ======================================');
      } else {
        // Check for error
        const errorBox = await page.locator('.error-box').textContent().catch(() => 'none');
        console.log('[TEST] No modal - Error:', errorBox?.substring(0, 200));
      }
    }
  } else {
    console.log('[TEST] Generate button not found');

    // Debug: list all buttons
    const buttons = await page.locator('button:visible').all();
    console.log('[TEST] Visible buttons:', buttons.length);
    for (const btn of buttons.slice(0, 10)) {
      console.log('  -', (await btn.textContent())?.trim().substring(0, 40));
    }
  }

  console.log('[TEST] ======================================');
  console.log('[TEST] TEST COMPLETE');
  console.log('[TEST] ======================================');

  await browser.close();
})();
