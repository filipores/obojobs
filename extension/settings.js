// Load saved settings
document.addEventListener('DOMContentLoaded', async () => {
  const settings = await chrome.storage.sync.get(['serverUrl', 'apiKey'])

  if (settings.serverUrl) {
    document.getElementById('server-url').value = settings.serverUrl
  }
  if (settings.apiKey) {
    document.getElementById('api-key').value = settings.apiKey
  }
})

// Save settings
document.getElementById('settings-form').addEventListener('submit', async (e) => {
  e.preventDefault()

  const serverUrl = document.getElementById('server-url').value
  const apiKey = document.getElementById('api-key').value
  const statusDiv = document.getElementById('status')

  try {
    // Test connection
    const response = await fetch(`${serverUrl}/api/health`, {
      headers: { 'X-API-Key': apiKey }
    })

    if (!response.ok) {
      throw new Error('Server not reachable')
    }

    // Save settings
    await chrome.storage.sync.set({ serverUrl, apiKey })

    statusDiv.className = 'status success'
    statusDiv.textContent = 'Settings saved successfully!'
  } catch (error) {
    statusDiv.className = 'status error'
    statusDiv.textContent = `Error: ${error.message}. Make sure the server is running.`
  }
})
