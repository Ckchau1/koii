const path = require('path');
const { app, BrowserWindow, ipcMain, session } = require('electron');
const express = require('express');
const bodyParser = require('body-parser');
const { EventEmitter } = require('events');

const PORT = Number(process.env.KOII_BROWSER_PORT || 43210);
const DEFAULT_TOKEN = process.env.KOII_BROWSER_DEFAULT_TOKEN || 'koii-default-token';
const TRUSTED_ORIGINS = new Set(
  (process.env.KOII_BROWSER_TRUSTED_ORIGINS || 'file://,http://localhost,https://localhost')
    .split(',')
    .map((raw) => raw.trim())
    .filter(Boolean)
);

const tokenCapabilities = new Map();
const agentTokensJson = process.env.KOII_BROWSER_AGENT_TOKENS || '';
try {
  const parsed = agentTokensJson ? JSON.parse(agentTokensJson) : {};
  Object.entries(parsed).forEach(([token, caps]) => {
    tokenCapabilities.set(token, new Set((caps || '').split(',').map((c) => c.trim()).filter(Boolean)));
  });
} catch (err) {
  console.warn('KOII_BROWSER_AGENT_TOKENS is invalid JSON, falling back to default token');
}

if (!tokenCapabilities.has(DEFAULT_TOKEN)) {
  tokenCapabilities.set(DEFAULT_TOKEN, new Set(['browser.read', 'browser.interact', 'browser.tabs', 'browser.cookies', 'browser.execute', 'browser.events']));
}

const browserInstances = new Map();
let nextTabId = 1;
const events = new EventEmitter();

function authorizeRequest(token, action) {
  if (!token) {
    return { authorized: false, reason: 'missing auth token' };
  }
  const caps = tokenCapabilities.get(token);
  if (!caps) {
    return { authorized: false, reason: 'unknown auth token' };
  }

  const required = {
    status: 'browser.read',
    createTab: 'browser.tabs',
    switchTab: 'browser.tabs',
    closeTab: 'browser.tabs',
    navigate: 'browser.interact',
    reload: 'browser.interact',
    click: 'browser.interact',
    type: 'browser.interact',
    select: 'browser.interact',
    scroll: 'browser.interact',
    getText: 'browser.read',
    getHtml: 'browser.read',
    getStructuredData: 'browser.read',
    screenshot: 'browser.read',
    getCookies: 'browser.cookies',
    setCookie: 'browser.cookies',
    clearCookies: 'browser.cookies',
    execute: 'browser.execute',
    getTabs: 'browser.read',
    injectAgentBridge: 'browser.execute',
  }[action];

  if (!required) {
    return { authorized: false, reason: `unsupported action: ${action}` };
  }
  if (!caps.has(required) && !caps.has('browser.admin')) {
    return { authorized: false, reason: `missing capability ${required}` };
  }
  return { authorized: true };
}

function createBrowserWindow({ url = 'about:blank', visible = true, width = 1280, height = 900 }) {
  const win = new BrowserWindow({
    width,
    height,
    show: visible,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      enableRemoteModule: false,
      webSecurity: true,
      nativeWindowOpen: false,
    },
  });

  win.loadURL(url);
  win.webContents.on('did-finish-load', () => {
    const tabId = win.koiiTabId;
    events.emit('page-loaded', { tabId, url: win.webContents.getURL() });
  });
  win.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    const tabId = win.koiiTabId;
    events.emit('page-load-failed', { tabId, url: validatedURL, errorCode, errorDescription });
  });
  return win;
}

function buildResponse(status, payload = {}) {
  return { status, ...payload };
}

function getTab(tabId) {
  return browserInstances.get(Number(tabId)) || null;
}

async function executeBrowserScript(win, script) {
  if (!win || win.isDestroyed()) {
    throw new Error('tab not available');
  }
  return win.webContents.executeJavaScript(script, true);
}

async function buildStructuredData(win, selector) {
  const target = selector ? `document.querySelector('${selector.replace(/'/g, "\\'")}')` : 'document.body';
  return executeBrowserScript(win, `(() => {
    const root = ${target};
    if (!root) return null;
    const walk = (node) => {
      const children = [];
      node.childNodes.forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const text = child.textContent.trim();
          if (text) children.push({ type: 'text', text });
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          children.push({
            type: 'element',
            tag: child.tagName.toLowerCase(),
            id: child.id || null,
            classes: Array.from(child.classList || []),
            text: child.innerText ? child.innerText.trim().slice(0, 500) : '',
            children: walk(child),
          });
        }
      });
      return children;
    };
    return { tag: root.tagName.toLowerCase(), html: root.outerHTML, structured: walk(root) };
  })()`);
}

async function captureScreenshot(win, target, fullPage = false) {
  if (!win || win.isDestroyed()) {
    throw new Error('tab not available');
  }
  const image = await win.webContents.capturePage();
  const buffer = image.toPNG();
  const screenshotDir = path.join(app.getPath('userData'), 'browser-screenshots');
  const filename = `${Date.now()}_${target || 'screenshot'}.png`;
  const filepath = path.join(screenshotDir, filename);
  const fs = require('fs');
  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.writeFileSync(filepath, buffer);
  return { path: filepath, base64: buffer.toString('base64') };
}

async function runAction(request) {
  const { action, payload = {}, token } = request;
  const auth = authorizeRequest(token, action);
  if (!auth.authorized) {
    return buildResponse('error', { reason: auth.reason });
  }

  try {
    switch (action) {
      case 'status': {
        return buildResponse('ok', { status: 'running', tabs: Array.from(browserInstances.keys()) });
      }
      case 'createTab': {
        const tabId = nextTabId++;
        const win = createBrowserWindow({ url: payload.url || 'about:blank', visible: payload.visible !== false });
        win.koiiTabId = tabId;
        browserInstances.set(tabId, win);
        return buildResponse('ok', { tabId, url: win.webContents.getURL() });
      }
      case 'closeTab': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        win.close();
        browserInstances.delete(Number(payload.tabId));
        return buildResponse('ok', { tabId: payload.tabId });
      }
      case 'switchTab': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        if (!win.isVisible()) win.show();
        win.focus();
        return buildResponse('ok', { tabId: payload.tabId });
      }
      case 'navigate': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        await win.loadURL(payload.url);
        return buildResponse('ok', { tabId: payload.tabId, url: win.webContents.getURL() });
      }
      case 'reload': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        win.webContents.reload();
        return buildResponse('ok', { tabId: payload.tabId });
      }
      case 'click': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const selector = payload.selector || null;
        if (!selector) return buildResponse('error', { reason: 'selector required' });
        await executeBrowserScript(win, `(() => {
          const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
          if (!el) throw new Error('element not found');
          el.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });
          el.click();
          return { success: true, href: el.href || null };
        })()`);
        return buildResponse('ok', { tabId: payload.tabId, selector });
      }
      case 'type': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const selector = payload.selector;
        const text = payload.text || '';
        if (!selector) return buildResponse('error', { reason: 'selector required' });
        await executeBrowserScript(win, `(() => {
          const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
          if (!el) throw new Error('element not found');
          el.focus();
          if ('value' in el) el.value = ${JSON.stringify(text)};
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        })()`);
        return buildResponse('ok', { tabId: payload.tabId, selector, text });
      }
      case 'select': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const selector = payload.selector;
        const value = payload.value;
        if (!selector || typeof value === 'undefined') {
          return buildResponse('error', { reason: 'selector and value required' });
        }
        await executeBrowserScript(win, `(() => {
          const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
          if (!el) throw new Error('element not found');
          el.value = ${JSON.stringify(value)};
          el.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        })()`);
        return buildResponse('ok', { tabId: payload.tabId, selector, value });
      }
      case 'scroll': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const script = payload.selector
          ? `(() => { const el = document.querySelector('${payload.selector.replace(/'/g, "\\'")}'); if (!el) throw new Error('element not found'); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); return true; })()`
          : `window.scrollBy(${Number(payload.dx || 0)}, ${Number(payload.dy || 0)}); true;`;
        await executeBrowserScript(win, script);
        return buildResponse('ok', { tabId: payload.tabId });
      }
      case 'getText': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const selector = payload.selector || 'body';
        const text = await executeBrowserScript(win, `(() => {
          const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
          return el ? el.innerText.trim().slice(0, 12000) : null;
        })()`);
        return buildResponse('ok', { tabId: payload.tabId, text, url: win.webContents.getURL() });
      }
      case 'getHtml': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const selector = payload.selector || 'html';
        const html = await executeBrowserScript(win, `(() => {
          const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
          return el ? el.outerHTML : null;
        })()`);
        return buildResponse('ok', { tabId: payload.tabId, html, url: win.webContents.getURL() });
      }
      case 'getStructuredData': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const data = await buildStructuredData(win, payload.selector || null);
        return buildResponse('ok', { tabId: payload.tabId, data, url: win.webContents.getURL() });
      }
      case 'screenshot': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const snapshot = await captureScreenshot(win, payload.label || 'page', Boolean(payload.fullPage));
        return buildResponse('ok', { tabId: payload.tabId, ...snapshot, url: win.webContents.getURL() });
      }
      case 'getCookies': {
        const cookieUrl = payload.url || getTab(payload.tabId)?.webContents.getURL();
        if (!cookieUrl) return buildResponse('error', { reason: 'url or tabId required' });
        const cookies = await session.defaultSession.cookies.get({ url: cookieUrl });
        return buildResponse('ok', { cookies });
      }
      case 'setCookie': {
        const cookie = payload.cookie;
        if (!cookie || !cookie.url) return buildResponse('error', { reason: 'cookie url required' });
        await session.defaultSession.cookies.set(cookie);
        return buildResponse('ok', { cookie });
      }
      case 'clearCookies': {
        const cookieUrl = payload.url;
        if (!cookieUrl) return buildResponse('error', { reason: 'url required' });
        const cookies = await session.defaultSession.cookies.get({ url: cookieUrl });
        await Promise.all(cookies.map((cookie) => session.defaultSession.cookies.remove(cookieUrl, cookie.name)));
        return buildResponse('ok', { cleared: cookies.length });
      }
      case 'execute': {
        const win = getTab(payload.tabId);
        if (!win) return buildResponse('error', { reason: 'tab not found' });
        const result = await executeBrowserScript(win, payload.script || 'null');
        return buildResponse('ok', { result });
      }
      case 'getTabs': {
        return buildResponse('ok', { tabs: Array.from(browserInstances.entries()).map(([id, win]) => ({ tabId: id, url: win.webContents.getURL(), visible: win.isVisible() })) });
      }
      default:
        return buildResponse('error', { reason: `unsupported action: ${action}` });
    }
  } catch (err) {
    return buildResponse('error', { reason: err.message || String(err) });
  }
}

ipcMain.handle('KoiiBrowserApi', async (_event, request) => {
  const result = await runAction(request);
  if (result.status === 'ok' && request.action) {
    events.emit('action-executed', { action: request.action, payload: request.payload, result });
  }
  return result;
});

function createExpressServer() {
  const server = express();
  server.use(bodyParser.json());
  server.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Koii-Agent-Token');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    next();
  });

  server.post('/api/v1/browser', async (req, res) => {
    const token = req.headers['x-koii-agent-token'] || req.body?.token || DEFAULT_TOKEN;
    const request = { action: req.body.action, payload: req.body.payload || {}, token };
    const result = await runAction(request);
    res.json(result);
  });

  server.get('/api/v1/browser/status', async (req, res) => {
    const token = req.headers['x-koii-agent-token'] || DEFAULT_TOKEN;
    const result = await runAction({ action: 'status', payload: {}, token });
    res.json(result);
  });

  server.listen(PORT, () => {
    console.log(`Koii Min Browser API available at http://127.0.0.1:${PORT}/api/v1/browser`);
  });
}

function createControlWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 800,
    show: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });
  win.loadFile(path.join(__dirname, 'ui.html'));
  return win;
}

app.whenReady().then(() => {
  createControlWindow();
  createExpressServer();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createControlWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
