const urlInput = document.getElementById('urlInput');
const goButton = document.getElementById('goButton');
const newTabButton = document.getElementById('newTabButton');
const refreshButton = document.getElementById('refreshButton');
const tabsButton = document.getElementById('tabsButton');
const status = document.getElementById('status');

let activeTabId = null;

async function updateStatus(message) {
  status.textContent = message;
}

async function ensureTab() {
  if (activeTabId !== null) {
    return activeTabId;
  }
  const result = await window.KoiiBrowserAPI.createTab({ url: 'https://example.com', visible: true });
  if (result.status === 'ok') {
    activeTabId = result.tabId;
    await updateStatus(`Created tab ${activeTabId} at ${result.url}`);
    return activeTabId;
  }
  await updateStatus(`Error creating tab: ${result.reason}`);
  return null;
}

goButton.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  if (!url) {
    await updateStatus('Please enter a URL or search string.');
    return;
  }
  const tabId = await ensureTab();
  if (!tabId) {
    return;
  }
  const normalizedUrl = url.startsWith('http') ? url : `https://${url}`;
  const result = await window.KoiiBrowserAPI.navigate(normalizedUrl, tabId);
  if (result.status === 'ok') {
    await updateStatus(`Navigated to ${result.url}`);
  } else {
    await updateStatus(`Navigate error: ${result.reason}`);
  }
});

newTabButton.addEventListener('click', async () => {
  const result = await window.KoiiBrowserAPI.createTab({ url: 'about:blank', visible: true });
  if (result.status === 'ok') {
    activeTabId = result.tabId;
    await updateStatus(`New tab ${activeTabId} created`);
  } else {
    await updateStatus(`Error creating tab: ${result.reason}`);
  }
});

refreshButton.addEventListener('click', async () => {
  const tabId = await ensureTab();
  if (!tabId) return;
  const result = await window.KoiiBrowserAPI.reload(tabId);
  if (result.status === 'ok') {
    await updateStatus(`Refreshed tab ${tabId}`);
  } else {
    await updateStatus(`Refresh error: ${result.reason}`);
  }
});

tabsButton.addEventListener('click', async () => {
  const result = await window.KoiiBrowserAPI.getTabs();
  if (result.status === 'ok') {
    await updateStatus(`Open tabs: ${result.tabs.map((tab) => `${tab.tabId}:${tab.url}`).join(', ')}`);
  } else {
    await updateStatus(`Error listing tabs: ${result.reason}`);
  }
});

window.KoiiBrowserAPI.on('page-loaded', (payload) => {
  console.log('Browser event page-loaded', payload);
});
