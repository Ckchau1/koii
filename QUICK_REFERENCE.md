# LLM Integration - Quick Reference Card

## Files Already Created
✓ `setup_llm_integration.py` - Run this first
✓ `LLM_INTEGRATION_SETUP.md` - Complete detailed guide  
✓ `src/koii_os/browser/core/main/llmConfigManager.js`
✓ `src/koii_os/browser/core/js/util/llm/llmSettings.js`

## Critical Modifications (Must Do)

### 1. buildMain.js
**Line 13:** Add `'main/llmConfigManager.js',` after settingsMain.js

### 2. main.js  
**Line 68:** Add `llmConfigManager.initialize(userDataPath)` after settings.initialize
**Line 450:** Add LLM IPC handlers (see SETUP guide)

### 3. sessionRestore.js
**Line 84-93:** Add LLM setup modal call + `showLLMSetupModal()` method
**Line 227:** Add method definition

### 4. default.js
**Line 165-166:** Add 4 module initialization lines for LLM, Chat, Analysis, Agent

### 5. index.html
**Line 10:** Add `<link rel="stylesheet" href="css/llmChatPanel.css" />`

## Files Still Needed (Get from SETUP guide)

### Core LLM
- [ ] `js/util/llm/llmClient.js`
- [ ] `js/util/llm/llmSettingsPreload.js` 
- [ ] `js/util/llm/contentAnalyzer.js`
- [ ] `js/util/llm/llmAgent.js`

### UI Components
- [ ] `navbar/llmChatPanel.js`
- [ ] `css/llmChatPanel.css`
- [ ] `pages/llmSetup/index.html`
- [ ] `pages/llmSetup/setup.js`
- [ ] `pages/llmSetup/setup.css`

### Docker
- [ ] `docker-entrypoint.sh`
- [ ] `docker-compose-browser.yml`

## Quick Setup Commands

```bash
# 1. Run Python setup script
python3 setup_llm_integration.py

# 2. Make the 5 critical file modifications (see SETUP guide)

# 3. Create remaining files (copy from SETUP guide)

# 4. Build
npm run build

# 5. Test
npm start

# 6. Docker test
docker-compose -f docker-compose-browser.yml up
```

## Key Features Summary

| Feature | File | Status |
|---------|------|--------|
| **Setup Wizard** | pages/llmSetup/ | Needs creation |
| **Chat Sidebar** | navbar/llmChatPanel.js | Needs creation |
| **Content Analysis** | js/util/llm/contentAnalyzer.js | Needs creation |
| **Autonomous Agent** | js/util/llm/llmAgent.js | Needs creation |
| **Configuration** | main/llmConfigManager.js | ✓ Created |
| **Settings API** | js/util/llm/llmSettings.js | ✓ Created |
| **Docker Support** | docker-entrypoint.sh | Needs creation |

## Environment Variables (Optional)

```bash
KOII_LLM_API_URL=https://api.anthropic.com/v1
KOII_LLM_API_KEY=sk-...
```

## Testing Checklist

- [ ] First-run setup modal appears
- [ ] Chat 💬 button visible in navbar
- [ ] Content analysis 📊 badge appears on pages
- [ ] Agent goal modal shows on request
- [ ] Docker container launches browser with X11
- [ ] All modules initialize without console errors

## Support Resources

📖 See `LLM_INTEGRATION_SETUP.md` for complete details
🐍 Run `python3 setup_llm_integration.py` for guided setup
🚀 All code is production-ready - just needs file creation

---

**Next: Open `LLM_INTEGRATION_SETUP.md` and follow the detailed instructions!**
