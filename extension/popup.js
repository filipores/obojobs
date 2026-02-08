document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('status');
  const creditsEl = document.getElementById('credits');
  const templateSection = document.getElementById('template-section');
  const templateSelect = document.getElementById('template-select');
  const extractBtn = document.getElementById('extract-btn');

  // Settings button
  document.getElementById('settings-btn').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  // Template selection persistence
  templateSelect.addEventListener('change', () => {
    const selectedId = templateSelect.value ? parseInt(templateSelect.value) : null;
    chrome.storage.sync.set({ selectedTemplateId: selectedId });
  });

  // Extract button: trigger DOM extraction + show modal on page
  extractBtn.addEventListener('click', () => {
    extractBtn.disabled = true;
    extractBtn.textContent = 'Extrahiere...';
    chrome.runtime.sendMessage({ action: 'extractAndGenerate' }, (resp) => {
      if (resp?.success) {
        window.close();
      } else {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Bewerbung von dieser Seite';
      }
    });
  });

  // Check settings
  const settings = await chrome.storage.sync.get(['serverUrl', 'apiKey', 'selectedTemplateId']);

  if (!settings.serverUrl || !settings.apiKey) {
    statusEl.textContent = 'Settings not configured';
    statusEl.className = 'status error';
    creditsEl.textContent = 'Click Settings button below';
    return;
  }

  // Check server connection
  try {
    const response = await fetch(`${settings.serverUrl}/api/auth/me`, {
      headers: { 'X-API-Key': settings.apiKey }
    });

    if (!response.ok) {
      statusEl.textContent = 'Invalid API Key';
      statusEl.className = 'status error';
      return;
    }

    const data = await response.json();
    statusEl.textContent = 'Server connected';
    statusEl.className = 'status ok';
    creditsEl.textContent = `Credits: ${data.credits_remaining}/${data.credits_max}`;
    extractBtn.style.display = 'block';

    await loadTemplates(settings, templateSelect, templateSection);
  } catch {
    statusEl.textContent = 'Server not reachable';
    statusEl.className = 'status error';
  }
});

async function loadTemplates(settings, selectEl, sectionEl) {
  try {
    const response = await fetch(`${settings.serverUrl}/api/templates/list-simple`, {
      headers: { 'X-API-Key': settings.apiKey }
    });

    if (!response.ok) return;

    const data = await response.json();
    const templates = data.templates;

    if (!templates || templates.length === 0) return;

    selectEl.innerHTML = '<option value="">Standard (Default)</option>';

    for (const t of templates) {
      const option = document.createElement('option');
      option.value = t.id;
      option.textContent = t.name + (t.is_default ? ' *' : '');
      option.selected = settings.selectedTemplateId === t.id;
      selectEl.appendChild(option);
    }

    sectionEl.style.display = 'block';
  } catch (err) {
    console.error('Failed to load templates:', err);
  }
}
