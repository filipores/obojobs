// Context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'generateApp',
    title: 'Generate Application',
    contexts: ['selection']
  });
});

// Handle click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'generateApp') {
    // Check if settings configured
    const settings = await chrome.storage.sync.get(['serverUrl', 'apiKey']);
    if (!settings.serverUrl || !settings.apiKey) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon48.png',
        title: 'Settings Required',
        message: 'Please configure Server URL and API Key in extension settings'
      });
      chrome.runtime.openOptionsPage();
      return;
    }

    chrome.tabs.sendMessage(tab.id, {
      action: 'showPopup',
      text: info.selectionText,
      url: info.pageUrl,
      company: extractCompany(info.pageUrl)
    });
  }
});

// Extract company from URL
function extractCompany(url) {
  try {
    const domain = new URL(url).hostname.replace(/^(www\.|careers\.|jobs\.)/, '');
    const name = domain.split('.')[0];
    return name.charAt(0).toUpperCase() + name.slice(1);
  } catch {
    return 'Unknown Company';
  }
}

// Generate application
chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (msg.action === 'generate') {
    (async () => {
      try {
        // Get settings including selected template
        const settings = await chrome.storage.sync.get(['serverUrl', 'apiKey', 'selectedTemplateId']);
        if (!settings.serverUrl || !settings.apiKey) {
          throw new Error('Settings not configured');
        }

        const API = settings.serverUrl;

        // Add template_id to request data if selected
        const requestData = { ...msg.data };
        if (settings.selectedTemplateId) {
          requestData.template_id = settings.selectedTemplateId;
        }

        // Generate application
        const response = await fetch(`${API}/api/applications/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': settings.apiKey
          },
          body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (result.success) {
          chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icon48.png',
            title: 'Application Generated',
            message: `Application for ${msg.data.company} created! Credits: ${result.credits_remaining}`
          });
          respond({ success: true, data: result });
        } else {
          respond({ success: false, error: result.error });
        }
      } catch (err) {
        respond({ success: false, error: err.toString() });
      }
    })();
    return true; // async
  }
});
