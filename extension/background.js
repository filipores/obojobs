// Context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'generateApp',
    title: 'Generate Application',
    contexts: ['selection']
  });
});

// --- Helpers ---

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function companyFromUrl(url) {
  try {
    const domain = new URL(url).hostname.replace(/^(www\.|careers\.|jobs\.)/, '');
    return capitalize(domain.split('.')[0]);
  } catch {
    return 'Unknown Company';
  }
}

async function getSettings(keys = ['serverUrl', 'apiKey']) {
  const settings = await chrome.storage.sync.get(keys);
  if (!settings.serverUrl || !settings.apiKey) return null;
  return settings;
}

function showSettingsRequiredNotification() {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icon48.png',
    title: 'Einstellungen fehlen',
    message: 'Bitte Server-URL und API-Key in den Einstellungen konfigurieren'
  });
  chrome.runtime.openOptionsPage();
}

// --- Context menu handler ---

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== 'generateApp') return;

  const settings = await getSettings();
  if (!settings) {
    showSettingsRequiredNotification();
    return;
  }

  chrome.tabs.sendMessage(tab.id, {
    action: 'showPopup',
    text: info.selectionText,
    url: info.pageUrl,
    company: companyFromUrl(info.pageUrl),
    title: '',
    source: 'selection'
  });
});

// --- Message handler ---

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (msg.action === 'extractAndGenerate') {
    handleExtractAndGenerate(respond);
    return true;
  }

  if (msg.action === 'generate') {
    handleGenerate(msg.data, respond);
    return true;
  }
});

async function handleExtractAndGenerate(respond) {
  try {
    const settings = await getSettings();
    if (!settings) {
      showSettingsRequiredNotification();
      respond({ success: false, error: 'Settings not configured' });
      return;
    }

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      respond({ success: false, error: 'No active tab' });
      return;
    }

    const extracted = await chrome.tabs.sendMessage(tab.id, { action: 'extractJobData' });

    chrome.tabs.sendMessage(tab.id, {
      action: 'showPopup',
      company: extracted.company || '',
      title: extracted.title || '',
      text: extracted.description || '',
      url: tab.url || '',
      source: extracted.source || 'generic'
    });

    respond({ success: true });
  } catch (err) {
    respond({ success: false, error: err.toString() });
  }
}

async function handleGenerate(data, respond) {
  try {
    const settings = await getSettings(['serverUrl', 'apiKey', 'selectedTemplateId']);
    if (!settings) {
      throw new Error('Settings not configured');
    }

    const requestData = { ...data };
    if (settings.selectedTemplateId) {
      requestData.template_id = settings.selectedTemplateId;
    }

    const response = await fetch(`${settings.serverUrl}/api/applications/generate`, {
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
        title: 'Bewerbung erstellt',
        message: `Bewerbung für ${data.company} erstellt! Credits: ${result.credits_remaining}`
      });
      respond({ success: true, data: result });
    } else {
      respond({ success: false, error: result.error });
    }
  } catch (err) {
    respond({ success: false, error: err.toString() });
  }
}
