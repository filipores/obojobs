chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'showPopup') {
    showPopup(msg.company, msg.text, msg.url);
  }
});

function showPopup(company, text, url) {
  // Remove existing
  document.getElementById('obo-overlay')?.remove();

  // Create overlay
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
    box-shadow: 0 4px 12px rgba(0,0,0,0.3); max-width: 400px; width: 90%;
  `;

  popup.innerHTML = `
    <h2 style="margin: 0 0 16px; font-size: 18px;">Generate Application</h2>
    <p style="margin: 0 0 12px; font-size: 14px; color: #666;">Company:</p>
    <input id="obo-input" value="${company}" style="
      width: 100%; padding: 8px; border: 1px solid #ddd;
      border-radius: 4px; font-size: 14px; margin-bottom: 16px; box-sizing: border-box;
    "/>
    <div style="display: flex; gap: 8px; justify-content: flex-end;">
      <button id="obo-cancel" style="
        padding: 8px 16px; border: 1px solid #ddd; border-radius: 4px;
        background: white; cursor: pointer; font-size: 14px;
      ">Cancel</button>
      <button id="obo-confirm" style="
        padding: 8px 16px; border: none; border-radius: 4px;
        background: #007bff; color: white; cursor: pointer; font-size: 14px;
      ">Generate</button>
    </div>
    <div id="obo-status" style="
      margin-top: 12px; font-size: 12px; color: #666; display: none;
    "></div>
  `;

  overlay.appendChild(popup);
  document.body.appendChild(overlay);

  const input = document.getElementById('obo-input');
  input.focus();
  input.select();

  // Cancel
  document.getElementById('obo-cancel').onclick = () => overlay.remove();

  // Confirm
  document.getElementById('obo-confirm').onclick = () => {
    const companyName = input.value.trim();
    if (!companyName) return alert('Enter company name');

    const btn = document.getElementById('obo-confirm');
    const status = document.getElementById('obo-status');

    btn.disabled = true;
    btn.textContent = 'Generating...';
    status.textContent = 'Generating application... (10-30s)';
    status.style.display = 'block';

    chrome.runtime.sendMessage({
      action: 'generate',
      data: {company: companyName, text, url}
    }, (resp) => {
      if (resp.success) {
        status.textContent = 'Success!';
        status.style.color = '#28a745';
        setTimeout(() => overlay.remove(), 2000);
      } else {
        status.textContent = `Error: ${resp.error}`;
        status.style.color = '#dc3545';
        btn.disabled = false;
        btn.textContent = 'Generate';
      }
    });
  };

  // ESC to close
  overlay.onkeydown = (e) => e.key === 'Escape' && overlay.remove();
}
