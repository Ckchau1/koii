const { contextBridge, ipcRenderer } = require('electron');

const trustedOrigins = new Set(
  (process.env.KOII_BROWSER_TRUSTED_ORIGINS || 'file://,http://localhost,https://localhost')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean)
);

function safeInvoke(action, payload) {
  return ipcRenderer.invoke('KoiiBrowserApi', { action, payload });
}

function isTrustedOrigin(origin) {
  return trustedOrigins.has(origin) || origin === 'file://' || origin === 'about:blank';
}

contextBridge.exposeInMainWorld('KoiiBrowserAPI', {
  navigate: (url, tabId) => safeInvoke('navigate', { url, tabId }),
  reload: (tabId) => safeInvoke('reload', { tabId }),
  click: (selector, tabId) => safeInvoke('click', { selector, tabId }),
  type: (selector, text, tabId) => safeInvoke('type', { selector, text, tabId }),
  select: (selector, value, tabId) => safeInvoke('select', { selector, value, tabId }),
  scroll: (options = {}) => safeInvoke('scroll', options),
  getText: (selector, tabId) => safeInvoke('getText', { selector, tabId }),
  getHtml: (selector, tabId) => safeInvoke('getHtml', { selector, tabId }),
  getStructuredData: (selector, tabId) => safeInvoke('getStructuredData', { selector, tabId }),
  screenshot: (options = {}) => safeInvoke('screenshot', options),
  createTab: (options = {}) => safeInvoke('createTab', options),
  switchTab: (tabId) => safeInvoke('switchTab', { tabId }),
  closeTab: (tabId) => safeInvoke('closeTab', { tabId }),
  getCookies: (options = {}) => safeInvoke('getCookies', options),
  setCookie: (cookie) => safeInvoke('setCookie', { cookie }),
  clearCookies: (url) => safeInvoke('clearCookies', { url }),
  execute: (script, tabId) => safeInvoke('execute', { script, tabId }),
  getTabs: () => safeInvoke('getTabs', {}),
  on: (eventName, callback) => {
    const channel = `KoiiBrowserEvent:${eventName}`;
    ipcRenderer.on(channel, (_event, payload) => callback(payload));
    return () => ipcRenderer.removeAllListeners(channel);
  },
  off: (eventName) => ipcRenderer.removeAllListeners(`KoiiBrowserEvent:${eventName}`),
});

window.addEventListener('message', async (event) => {
  if (!event.data || event.data.type !== 'KOII_BROWSER_COMMAND') {
    return;
  }
  if (!isTrustedOrigin(event.origin)) {
    return;
  }
  const { id, action, payload } = event.data;
  const result = await ipcRenderer.invoke('KoiiBrowserApi', { action, payload });
  event.source.postMessage({ type: 'KOII_BROWSER_RESPONSE', id, result }, event.origin);
});
