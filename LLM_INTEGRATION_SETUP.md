# AIOS Min Browser - LLM Integration Setup Guide

This guide provides all the code and instructions needed to set up the complete LLM integration system for the AIOS Min browser.

## Quick Start

### Option 1: Run Python Setup Script (Recommended)
```bash
python3 setup_llm_integration.py
```

This creates the initial configuration files and provides guided instructions for the remaining setup.

### Option 2: Manual Setup
Follow the detailed instructions below to create and modify files manually.

---

## Phase 1: LLM Configuration Module ✓

### Files Created by Script
- `src/koii_os/browser/core/main/llmConfigManager.js` - Handles encrypted API key storage
- `src/koii_os/browser/core/js/util/llm/llmSettings.js` - Renderer-side configuration API

### Files Still Needed

#### 1. `src/koii_os/browser/core/js/util/llm/llmSettingsPreload.js`
```javascript
// Preload script bridge for LLM settings communication
const { ipcRenderer } = require('electron')

var llmSettingsPreload = {
  initialize: function () {
    ipcRenderer.on('llmConfigChanged', (event, config) => {
      if (window.llmSettings && window.llmSettings.onConfigChanged) {
        window.llmSettings.onConfigChanged(config)
      }
    })
  },

  getConfig: function (callback) {
    ipcRenderer.invoke('getLLMConfig').then(config => {
      if (callback) callback(null, config)
    }).catch(err => {
      if (callback) callback(err, null)
    })
  },

  saveConfig: function (config, callback) {
    ipcRenderer.invoke('saveLLMConfig', config).then(result => {
      if (callback) callback(null, result)
    }).catch(err => {
      if (callback) callback(err, null)
    })
  },

  validateConnection: function (apiUrl, apiKey, modelId, callback) {
    ipcRenderer.invoke('validateLLMConnection', { apiUrl, apiKey, modelId }).then(result => {
      if (callback) callback(null, result)
    }).catch(err => {
      if (callback) callback(err, null)
    })
  },

  clearConfig: function (callback) {
    ipcRenderer.invoke('clearLLMConfig').then(result => {
      if (callback) callback(null, result)
    }).catch(err => {
      if (callback) callback(err, null)
    })
  }
}

module.exports = llmSettingsPreload
```

---

## Phase 2: File Modifications

### 1. Modify: `src/koii_os/browser/core/scripts/buildMain.js`

**Find this line (around line 13):**
```javascript
  'js/util/settings/settingsMain.js',
```

**Add after it:**
```javascript
  'main/llmConfigManager.js',
```

### 2. Modify: `src/koii_os/browser/core/main/main.js`

**Find this line (around line 68):**
```javascript
settings.initialize(userDataPath)
```

**Add after it:**
```javascript
llmConfigManager.initialize(userDataPath)
```

**Then find this section (around line 450):**
```javascript
ipc.on('handoffUpdate', function(e, data) {
  // ...
})

ipc.on('quit', function () {
```

**Add this before `ipc.on('quit',...)`:**
```javascript
// LLM Configuration IPC Handlers
ipc.handle('getLLMConfig', function(e) {
  return llmConfigManager.getConfig()
})

ipc.handle('saveLLMConfig', function(e, config) {
  try {
    llmConfigManager.saveConfig(config)
    windows.getAll().forEach(function (win) {
      getWindowWebContents(win).send('llmConfigChanged', llmConfigManager.getConfig())
    })
    return { success: true, config: llmConfigManager.getConfig() }
  } catch (err) {
    console.error('Error saving LLM config:', err)
    return { success: false, error: err.message }
  }
})

ipc.handle('validateLLMConnection', async function(e, params) {
  try {
    const result = await llmConfigManager.validateConnection(params.apiUrl, params.apiKey, params.modelId)
    return result
  } catch (err) {
    console.error('Error validating LLM connection:', err)
    return { success: false, error: err.message }
  }
})

ipc.handle('clearLLMConfig', function(e) {
  try {
    llmConfigManager.clearConfig()
    windows.getAll().forEach(function (win) {
      getWindowWebContents(win).send('llmConfigChanged', llmConfigManager.getConfig())
    })
    return { success: true }
  } catch (err) {
    console.error('Error clearing LLM config:', err)
    return { success: false, error: err.message }
  }
})
```

### 3. Modify: `src/koii_os/browser/core/js/sessionRestore.js`

**Find this section (around line 84):**
```javascript
      // first run, show the tour
      if (!savedStringData) {
        tasks.setSelected(tasks.add()) // create a new task

        var newTab = tasks.getSelected().tabs.add({
            url: 'https://minbrowser.github.io/min/tour'
        })
        browserUI.addTab(newTab, {
         enterEditMode: false
        })
        return
      }
```

**Change to:**
```javascript
      // first run, show the tour and LLM setup
      if (!savedStringData) {
        tasks.setSelected(tasks.add()) // create a new task

        var newTab = tasks.getSelected().tabs.add({
            url: 'https://minbrowser.github.io/min/tour'
        })
        browserUI.addTab(newTab, {
         enterEditMode: false
        })

        // Show LLM setup modal on first run
        setTimeout(function() {
          sessionRestore.showLLMSetupModal()
        }, 500)

        return
      }
```

**Then find the `restore: function ()` section (around line 227) and add this method after it:**
```javascript
  showLLMSetupModal: function () {
    // Skip if user has already completed setup or skipped it
    if (localStorage.getItem('llmSetupComplete') || localStorage.getItem('llmSetupSkipped')) {
      return
    }

    // Create a modal overlay for LLM setup
    var modal = document.createElement('div')
    modal.id = 'llmSetupModal'
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
    `

    var iframe = document.createElement('iframe')
    iframe.src = 'min://app/pages/llmSetup/index.html'
    iframe.style.cssText = `
      width: 600px;
      height: 90vh;
      max-width: 90vw;
      border: none;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    `

    modal.appendChild(iframe)
    document.body.appendChild(modal)

    // Listen for close message from iframe
    window.addEventListener('message', function handleClose(e) {
      if (e.data && e.data.type === 'closeModal' && e.data.name === 'llmSetup') {
        modal.remove()
        window.removeEventListener('message', handleClose)
      }
    })
  },
```

### 4. Modify: `src/koii_os/browser/core/js/default.js`

**Find this section (around line 165-166):**
```javascript
require('taskOverlay/taskOverlay.js').initialize()
require('sessionRestore.js').initialize()
```

**Add these lines between them:**
```javascript
require('util/llm/llmSettings.js').initialize()
require('navbar/llmChatPanel.js').initialize()
require('util/llm/contentAnalyzer.js').initialize()
require('util/llm/llmAgent.js').initialize()
```

### 5. Modify: `src/koii_os/browser/core/index.html`

**Find this section (around line 9):**
```html
    <link rel="stylesheet" href="dist/bundle.css" />
    <link rel="stylesheet" href="ext/icons/iconfont.css" />
```

**Add after it:**
```html
    <link rel="stylesheet" href="css/llmChatPanel.css" />
```

---

## Phase 3-6: Remaining Implementation Files

Due to length, the remaining complete file contents are available in the GitHub repository:

**Files to create (with full content available on request):**

### LLM Core
- `src/koii_os/browser/core/js/util/llm/llmClient.js` - API client with streaming
- `src/koii_os/browser/core/js/util/llm/contentAnalyzer.js` - Page analysis engine
- `src/koii_os/browser/core/js/util/llm/llmAgent.js` - Autonomous task execution

### UI Components  
- `src/koii_os/browser/core/navbar/llmChatPanel.js` - Chat sidebar component
- `src/koii_os/browser/core/css/llmChatPanel.css` - Comprehensive styling
- `src/koii_os/browser/core/pages/llmSetup/index.html` - Setup wizard UI
- `src/koii_os/browser/core/pages/llmSetup/setup.js` - Wizard logic
- `src/koii_os/browser/core/pages/llmSetup/setup.css` - Wizard styling

### Docker
- `docker-entrypoint.sh` - Smart Docker entry point
- `docker-compose-browser.yml` - Compose configuration for browser mode

---

## Getting Complete File Contents

To get the complete, properly formatted content for all remaining files, you can:

1. **Clone from GitHub** (if PR is merged):
   ```bash
   git clone https://github.com/Ckchau1/koii.git
   ```

2. **Request individual files**: Ask me to provide the complete content for any specific file

3. **Use the comprehensive script**: I can create a more complete setup script that generates all files at once

---

## Testing the Integration

### Test First-Run Setup
1. Delete `sessionRestore.json` from your user data directory
2. Start the browser
3. You should see the LLM setup modal

### Test Chat Sidebar
1. Look for the 💬 button in the navbar
2. Click to open the chat panel
3. Messages should appear with proper styling

### Test Content Analysis  
1. Navigate to a website
2. A 📊 analysis badge should appear at bottom-left
3. Click it to see page analysis

### Test Docker
```bash
docker-compose -f docker-compose-browser.yml up
```

---

## Troubleshooting

### Files not appearing after creation
- Check file paths use forward slashes in code
- Verify parent directories exist
- Ensure proper permissions on the file system

### Build errors
- Run `npm run build` to rebuild the main bundle
- Check buildMain.js includes llmConfigManager

### Module not found errors
- Verify require statements use correct paths
- Check that files are in the correct directories
- Look for typos in filenames

---

## Support

For issues or questions about the LLM integration:
1. Check the complete implementation in the PR
2. Review the code comments for each module
3. Verify all modifications were applied correctly

---

## Next Steps

After setup is complete:

1. **Build the project**:
   ```bash
   npm run build
   ```

2. **Test the implementation**:
   ```bash
   npm start
   ```

3. **Deploy via Docker**:
   ```bash
   docker-compose -f docker-compose-browser.yml up
   ```

4. **Configure LLM**:
   - On first run, complete the setup wizard
   - Or set environment variables: `KOII_LLM_API_URL`, `KOII_LLM_API_KEY`

---

Good luck with the implementation! 🚀
