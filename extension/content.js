// =============================================================================
// Helpers
// =============================================================================

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

/**
 * Copy non-empty values from source into target for any keys that are
 * empty/missing in target.
 */
function fillMissing(target, source, keys) {
  for (const key of keys) {
    if (!target[key] && source[key]) {
      target[key] = source[key];
    }
  }
}

// =============================================================================
// Job Extraction Engine
// =============================================================================

const JobExtractor = {
  // --- JSON-LD Extractor ---
  extractJsonLd() {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
      try {
        const data = JSON.parse(script.textContent);
        const result = this._findJobPosting(data);
        if (result) return result;
      } catch { /* ignore parse errors */ }
    }
    return null;
  },

  _findJobPosting(data) {
    if (!data || typeof data !== 'object') return null;

    if (Array.isArray(data)) {
      for (const item of data) {
        const found = this._findJobPosting(item);
        if (found) return found;
      }
      return null;
    }

    if (data['@type'] === 'JobPosting') return data;

    if (data['@graph']) {
      for (const entry of data['@graph']) {
        if (entry?.['@type'] === 'JobPosting') return entry;
      }
    }

    return null;
  },

  parseJsonLd(data) {
    const result = {};
    result.title = data.title || '';
    result.description = data.description || '';

    const org = data.hiringOrganization;
    if (org && typeof org === 'object') {
      result.company = org.name || '';
    } else if (typeof org === 'string') {
      result.company = org;
    }

    const loc = data.jobLocation;
    if (loc) {
      result.location = this._parseLocation(loc);
    }

    return result;
  },

  _parseLocation(loc) {
    if (typeof loc === 'string') return loc;

    if (Array.isArray(loc)) {
      return loc.map(l => this._parseLocation(l)).filter(Boolean).join(', ');
    }

    if (typeof loc === 'object') {
      const addr = loc.address;
      if (typeof addr === 'string') return addr;
      if (addr && typeof addr === 'object') {
        return [addr.postalCode, addr.addressLocality, addr.addressRegion]
          .filter(Boolean)
          .join(', ');
      }
    }

    return '';
  },

  // --- Site-Specific Extractors ---
  siteExtractors: [
    // StepStone
    {
      name: 'stepstone',
      matches: (url) => /stepstone\.de/i.test(url) && /\/stellenangebote--|\/offer\/|\/jobs--/i.test(url),
      extract(doc) {
        const result = {};
        const h1 = doc.querySelector('h1');
        if (h1) result.title = h1.textContent.trim();

        const company = doc.querySelector('[data-at="header-company-name"]');
        if (company) result.company = company.textContent.trim();

        const location = doc.querySelector('[data-at="header-job-location"]');
        if (location) result.location = location.textContent.trim();

        const content = doc.querySelector('[data-at="job-ad-content"]');
        if (content) result.description = content.innerText.trim();

        return result;
      }
    },
    // Indeed
    {
      name: 'indeed',
      matches: (url) => /indeed\.(de|com|at|ch)/i.test(url) && /(\/viewjob|\/job\/|jk=)/i.test(url),
      extract(doc) {
        const result = {};
        const title = doc.querySelector('[data-testid="jobsearch-JobInfoHeader-title"]')
          || doc.querySelector('h1');
        if (title) result.title = title.textContent.trim();

        const company = doc.querySelector('[data-testid="inlineHeader-companyName"]')
          || doc.querySelector('[data-testid="company-name"]');
        if (company) {
          const link = company.querySelector('a');
          result.company = (link || company).textContent.trim();
        }

        const location = doc.querySelector('[data-testid="inlineHeader-companyLocation"]')
          || doc.querySelector('[data-testid="job-location"]');
        if (location) result.location = location.textContent.trim();

        const desc = doc.querySelector('#jobDescriptionText')
          || doc.querySelector('[data-testid="jobDescriptionText"]');
        if (desc) result.description = desc.innerText.trim();

        return result;
      }
    },
    // LinkedIn
    {
      name: 'linkedin',
      matches: (url) => /linkedin\.com/i.test(url) && /\/jobs\/view\//i.test(url),
      extract(doc) {
        const result = {};
        const title = doc.querySelector('.job-details-jobs-unified-top-card__job-title')
          || doc.querySelector('.jobs-unified-top-card__job-title')
          || doc.querySelector('h1');
        if (title) result.title = title.textContent.trim();

        const company = doc.querySelector('.job-details-jobs-unified-top-card__company-name')
          || doc.querySelector('.jobs-unified-top-card__company-name');
        if (company) result.company = company.textContent.trim();

        const desc = doc.querySelector('#job-details')
          || doc.querySelector('.jobs-description__content');
        if (desc) result.description = desc.innerText.trim();

        return result;
      }
    },
    // XING
    {
      name: 'xing',
      matches: (url) => /xing\.com/i.test(url) && /\/jobs\//i.test(url),
      extract(doc) {
        const result = {};
        const titleEl = doc.querySelector('[class*="job-title"]')
          || doc.querySelector('[data-testid="job-title"]')
          || doc.querySelector('h1');
        if (titleEl) result.title = titleEl.textContent.trim();

        const companyEl = doc.querySelector('[class*="company-name"]')
          || doc.querySelector('[data-testid="company-name"]');
        if (companyEl) result.company = companyEl.textContent.trim();

        const descEl = doc.querySelector('[class*="job-description"]')
          || doc.querySelector('[data-testid="job-description"]');
        if (descEl) result.description = descEl.innerText.trim();

        return result;
      }
    },
    // Arbeitsagentur
    {
      name: 'arbeitsagentur',
      matches: (url) => /arbeitsagentur\.de/i.test(url)
        && /(\/jobsuche\/|\/stellenangebot\/|\/jobboerse\/)/i.test(url),
      extract(doc) {
        const result = {};
        const titleEl = doc.querySelector('[data-testid="job-title"]')
          || doc.querySelector('[class*="job-title"]')
          || doc.querySelector('[class*="stellentitel"]')
          || doc.querySelector('h1');
        if (titleEl) result.title = titleEl.textContent.trim();

        const companyEl = doc.querySelector('[data-testid="company-name"]')
          || doc.querySelector('[class*="arbeitgeber"]');
        if (companyEl) {
          result.company = companyEl.textContent.trim();
        } else {
          const match = doc.body.innerText.match(/Arbeitgeber\s*:\s*(.+)/i);
          if (match) result.company = match[1].split('\n')[0].trim();
        }

        const locationEl = doc.querySelector('[class*="arbeitsort"]');
        if (locationEl) {
          result.location = locationEl.textContent.trim();
        } else {
          const match = doc.body.innerText.match(/Arbeitsort\s*:\s*(.+)/i);
          if (match) result.location = match[1].split('\n')[0].trim();
        }

        const descEl = doc.querySelector('[class*="job-description"]')
          || doc.querySelector('article')
          || doc.querySelector('main');
        if (descEl) result.description = descEl.innerText.trim();

        return result;
      }
    },
    // Softgarden
    {
      name: 'softgarden',
      matches: (url) => /softgarden\.io/i.test(url) && /\/job\//i.test(url),
      extract(doc) {
        const result = {};
        const h1 = doc.querySelector('h1');
        if (h1) result.title = h1.textContent.trim();

        try {
          const subdomain = new URL(window.location.href).hostname.split('.')[0];
          if (subdomain && subdomain !== 'www' && subdomain !== 'softgarden') {
            result.company = capitalize(subdomain);
          }
        } catch { /* ignore */ }

        const descEl = doc.querySelector('[class*="job-description"]')
          || doc.querySelector('[class*="jobad"]')
          || doc.querySelector('article')
          || doc.querySelector('main');
        if (descEl) result.description = descEl.innerText.trim();

        return result;
      }
    }
  ],

  // --- Generic Fallback ---
  extractGeneric(doc) {
    const result = {};

    // OpenGraph metadata
    const ogTitle = doc.querySelector('meta[property="og:title"]');
    if (ogTitle) result.title = ogTitle.getAttribute('content') || '';

    const ogSiteName = doc.querySelector('meta[property="og:site_name"]');
    if (ogSiteName) result.company = ogSiteName.getAttribute('content') || '';

    const ogDesc = doc.querySelector('meta[property="og:description"]');
    if (ogDesc) result.description = ogDesc.getAttribute('content') || '';

    // Parse document.title (split on common separators)
    if (!result.title || !result.company) {
      const titleText = doc.title || '';
      const separators = [' - ', ' | ', ' bei ', ' at '];
      for (const sep of separators) {
        if (titleText.includes(sep)) {
          const parts = titleText.split(sep).map(s => s.trim());
          if (!result.title && parts[0]) result.title = parts[0];
          if (!result.company && parts.length > 1) result.company = parts[parts.length - 1];
          break;
        }
      }
    }

    // Fallback: h1 for title
    if (!result.title) {
      const h1 = doc.querySelector('h1');
      if (h1) result.title = h1.textContent.trim();
    }

    // Fallback: article/main for description
    if (!result.description) {
      const cleanDoc = doc.cloneNode(true);
      const removeSelectors = 'nav, header, footer, [role="navigation"], [class*="cookie"], [class*="consent"], [class*="sidebar"], [class*="menu"], [class*="banner"], script, style, noscript';
      cleanDoc.querySelectorAll(removeSelectors).forEach(el => el.remove());

      const main = cleanDoc.querySelector('article')
        || cleanDoc.querySelector('main')
        || cleanDoc.querySelector('[role="main"]');
      if (main) result.description = main.innerText.trim();
    }

    // Email extraction
    const bodyText = doc.body.innerText || '';
    const emails = bodyText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g) || [];
    const filtered = emails.filter(e =>
      !/(noreply|no-reply|newsletter|mailer|daemon|support@stepstone|info@indeed)/i.test(e)
    );
    if (filtered.length > 0) result.contactEmail = filtered[0];

    return result;
  },

  // --- Main extract() ---
  extract() {
    const url = window.location.href;
    const data = { title: '', company: '', description: '', location: '', contactEmail: '', source: 'generic' };
    const FIELD_KEYS = ['title', 'company', 'description', 'location', 'contactEmail'];

    // 1. Try JSON-LD first (works across all sites)
    const jsonLd = this.extractJsonLd();
    if (jsonLd) {
      Object.assign(data, this.parseJsonLd(jsonLd));
      data.source = 'json-ld';
    }

    // 2. Try site-specific extractor
    for (const ext of this.siteExtractors) {
      if (ext.matches(url)) {
        const siteData = ext.extract(document);
        fillMissing(data, siteData, FIELD_KEYS);
        // Prefer site-specific description over JSON-LD (usually richer)
        if (siteData.description && data.source === 'json-ld') {
          data.description = siteData.description;
        }
        data.source = ext.name;
        break;
      }
    }

    // 3. Generic fallback for remaining fields
    fillMissing(data, this.extractGeneric(document), FIELD_KEYS);

    // 4. Company fallback from URL domain
    if (!data.company) {
      try {
        const domain = new URL(url).hostname.replace(/^(www\.|careers\.|jobs\.)/, '');
        data.company = capitalize(domain.split('.')[0]);
      } catch { /* ignore */ }
    }

    // 5. Strip HTML from description and trim length
    if (data.description) {
      const tmp = document.createElement('div');
      tmp.innerHTML = data.description;
      data.description = tmp.innerText || tmp.textContent || data.description;
      if (data.description.length > 10000) {
        data.description = data.description.substring(0, 10000) + '...';
      }
    }

    return data;
  }
};

// =============================================================================
// Message Listeners
// =============================================================================

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'showPopup') {
    showPopup(msg);
  } else if (msg.action === 'extractJobData') {
    sendResponse(JobExtractor.extract());
    return true;
  }
});

// =============================================================================
// Modal UI
// =============================================================================

function showPopup(data) {
  document.getElementById('obo-overlay')?.remove();

  const company = data.company || '';
  const title = data.title || '';
  const text = data.text || '';
  const source = data.source || '';

  const charCount = text.length;
  const sourceLabel = (source && source !== 'generic' && source !== 'selection')
    ? capitalize(source)
    : '';

  const metaParts = [];
  if (charCount > 0) metaParts.push(`${charCount.toLocaleString('de-DE')} Zeichen`);
  if (sourceLabel) metaParts.push(sourceLabel);
  const metaText = metaParts.join(' \u00b7 ');

  const previewText = text.length > 500 ? text.substring(0, 500) + '...' : text;

  const overlay = document.createElement('div');
  overlay.id = 'obo-overlay';
  overlay.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5); z-index: 999999;
    display: flex; align-items: center; justify-content: center;
  `;

  const popup = document.createElement('div');
  popup.style.cssText = `
    background: white; padding: 24px; border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3); max-width: 440px; width: 90%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;

  popup.innerHTML = `
    <h2 style="margin: 0 0 16px; font-size: 18px; color: #1a1a1a;">Bewerbung erstellen</h2>

    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 4px;">Firma:</label>
    <input id="obo-company" value="${escapeHtml(company)}" placeholder="Firmenname eingeben" style="
      width: 100%; padding: 8px; border: 1px solid #ddd;
      border-radius: 4px; font-size: 14px; margin-bottom: 12px; box-sizing: border-box;
    "/>

    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 4px;">Position:</label>
    <input id="obo-title" value="${escapeHtml(title)}" placeholder="Positionsbezeichnung" style="
      width: 100%; padding: 8px; border: 1px solid #ddd;
      border-radius: 4px; font-size: 14px; margin-bottom: 12px; box-sizing: border-box;
    "/>

    ${text ? `
    <label style="display: block; font-size: 13px; color: #666; margin-bottom: 4px;">Stellenanzeige:</label>
    <div style="
      max-height: 100px; overflow-y: auto; padding: 8px;
      border: 1px solid #eee; border-radius: 4px;
      font-size: 12px; color: #444; line-height: 1.4;
      margin-bottom: 4px; background: #fafafa; white-space: pre-wrap;
    ">${escapeHtml(previewText)}</div>
    <div style="font-size: 11px; color: #999; margin-bottom: 12px;">${escapeHtml(metaText)}</div>
    ` : ''}

    <div style="display: flex; gap: 8px; justify-content: flex-end;">
      <button id="obo-cancel" style="
        padding: 8px 16px; border: 1px solid #ddd; border-radius: 4px;
        background: white; cursor: pointer; font-size: 14px;
      ">Abbrechen</button>
      <button id="obo-confirm" style="
        padding: 8px 16px; border: none; border-radius: 4px;
        background: #007bff; color: white; cursor: pointer; font-size: 14px;
      ">Erstellen</button>
    </div>
    <div id="obo-status" style="
      margin-top: 12px; font-size: 12px; color: #666; display: none;
    "></div>
  `;

  overlay.appendChild(popup);
  document.body.appendChild(overlay);

  const companyInput = document.getElementById('obo-company');
  companyInput.focus();
  companyInput.select();

  // Cancel
  document.getElementById('obo-cancel').onclick = () => overlay.remove();

  // Confirm
  document.getElementById('obo-confirm').onclick = () => {
    const companyName = companyInput.value.trim();
    if (!companyName) return alert('Bitte Firmennamen eingeben');

    const btn = document.getElementById('obo-confirm');
    const status = document.getElementById('obo-status');

    btn.disabled = true;
    btn.textContent = 'Wird erstellt...';
    btn.style.opacity = '0.7';
    status.textContent = 'Bewerbung wird generiert... (10-30s)';
    status.style.display = 'block';
    status.style.color = '#666';

    chrome.runtime.sendMessage({
      action: 'generate',
      data: { company: companyName, text, url: '' }
    }, (resp) => {
      if (resp?.success) {
        status.textContent = 'Bewerbung erstellt!';
        status.style.color = '#28a745';
        btn.textContent = 'Erstellt!';
        setTimeout(() => overlay.remove(), 2000);
      } else {
        status.textContent = `Fehler: ${resp?.error || 'Keine Antwort'}`;
        status.style.color = '#dc3545';
        btn.disabled = false;
        btn.textContent = 'Erstellen';
        btn.style.opacity = '1';
      }
    });
  };

  // ESC to close
  overlay.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') overlay.remove();
  });

  // Click outside to close
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.remove();
  });
}
