document.addEventListener('DOMContentLoaded', async () => {
  const status = document.getElementById('status');
  const credits = document.getElementById('credits');
  const templateSection = document.getElementById('template-section');
  const templateSelect = document.getElementById('template-select');

  // Get settings
  const settings = await chrome.storage.sync.get(['serverUrl', 'apiKey', 'selectedTemplateId']);

  if (!settings.serverUrl || !settings.apiKey) {
    status.textContent = 'Settings not configured';
    status.className = 'status error';
    credits.textContent = 'Click Settings button below';
    return;
  }

  // Check server
  try {
    const response = await fetch(`${settings.serverUrl}/api/auth/me`, {
      headers: { 'X-API-Key': settings.apiKey }
    });

    if (response.ok) {
      const data = await response.json();
      status.textContent = 'Server connected';
      status.className = 'status ok';
      credits.textContent = `Credits: ${data.credits_remaining}/${data.credits_max}`;

      // Fetch and display templates
      await loadTemplates(settings.serverUrl, settings.apiKey, settings.selectedTemplateId);
    } else {
      status.textContent = 'Invalid API Key';
      status.className = 'status error';
    }
  } catch {
    status.textContent = 'Server not reachable';
    status.className = 'status error';
  }

  // Handle template selection
  templateSelect.addEventListener('change', async () => {
    const selectedId = templateSelect.value ? parseInt(templateSelect.value) : null;
    await chrome.storage.sync.set({ selectedTemplateId: selectedId });
  });
});

// Load templates
async function loadTemplates(serverUrl, apiKey, selectedTemplateId) {
  try {
    const response = await fetch(`${serverUrl}/api/templates/list-simple`, {
      headers: { 'X-API-Key': apiKey }
    });

    if (response.ok) {
      const data = await response.json();
      const templates = data.templates;

      if (templates && templates.length > 0) {
        const templateSelect = document.getElementById('template-select');
        const templateSection = document.getElementById('template-section');

        // Clear existing options (except first)
        templateSelect.innerHTML = '<option value="">Standard (Default)</option>';

        // Add templates
        templates.forEach(t => {
          const option = document.createElement('option');
          option.value = t.id;
          option.textContent = t.name + (t.is_default ? ' ⭐' : '');
          if (selectedTemplateId && selectedTemplateId === t.id) {
            option.selected = true;
          }
          templateSelect.appendChild(option);
        });

        // Show template section
        templateSection.style.display = 'block';
      }
    }
  } catch (err) {
    console.error('Failed to load templates:', err);
  }
}

// Settings button
document.getElementById('settings-btn').addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});
