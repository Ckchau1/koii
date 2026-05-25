#!/bin/bash
# AIOS LLM Integration Setup Script
# This script sets up all the LLM integration features for the Min browser
# Run from the repository root: bash setup-llm-integration.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "=================================================="
echo "AIOS LLM Integration Setup"
echo "=================================================="
echo "Working directory: $SCRIPT_DIR"
echo ""

# Function to create file with content
create_file() {
    local filepath="$1"
    local content="$2"
    local dir=$(dirname "$filepath")

    mkdir -p "$dir"
    echo "$content" > "$filepath"
    echo "✓ Created: $filepath"
}

echo "Creating LLM configuration files..."
echo ""

# ============================================================================
# Phase 1: LLM Configuration Files
# ============================================================================

create_file "src/koii_os/browser/core/main/llmConfigManager.js" 'const writeFileAtomic = require('"'"'write-file-atomic'"'"')

var llmConfigManager = {
  userDataPath: null,
  configFilePath: null,
  defaults: {
    apiUrl: '"'"'https://api.anthropic.com/v1'"'"',
    modelId: '"'"'claude-opus-4-7'"'"',
    maxTokens: 4096,
    temperature: 0.7,
    enabledFeatures: ['"'"'chat'"'"', '"'"'analysis'"'"', '"'"'autonomousAgent'"'"']
  },

  initialize: function (userDataPath) {
    this.userDataPath = userDataPath
    this.configFilePath = userDataPath + (process.platform === '"'"'win32'"'"' ? '"'"'\\'"'"' : '"'"'/'"'"') + '"'"'llmConfig.json'"'"'

    if (process.env.KOII_LLM_API_URL) {
      this.defaults.apiUrl = process.env.KOII_LLM_API_URL
    }

    this.loadConfig()
  },

  loadConfig: function () {
    try {
      const fs = require('"'"'fs'"'"')
      if (fs.existsSync(this.configFilePath)) {
        const data = fs.readFileSync(this.configFilePath, '"'"'utf-8'"'"')
        const config = JSON.parse(data)
        return config
      }
    } catch (e) {
      console.warn('"'"'Error reading LLM config file:'"'"', e)
    }
    return null
  },

  getConfig: function () {
    const config = this.loadConfig()
    if (!config) {
      return {
        apiUrl: this.defaults.apiUrl,
        modelId: this.defaults.modelId,
        maxTokens: this.defaults.maxTokens,
        temperature: this.defaults.temperature,
        enabledFeatures: [...this.defaults.enabledFeatures],
        hasApiKey: false
      }
    }

    return {
      apiUrl: config.apiUrl || this.defaults.apiUrl,
      modelId: config.modelId || this.defaults.modelId,
      maxTokens: config.maxTokens || this.defaults.maxTokens,
      temperature: config.temperature || this.defaults.temperature,
      enabledFeatures: config.enabledFeatures || [...this.defaults.enabledFeatures],
      hasApiKey: !!config.encryptedApiKey
    }
  },

  getApiKey: function () {
    const config = this.loadConfig()
    if (!config || !config.encryptedApiKey) {
      if (process.env.KOII_LLM_API_KEY) {
        return process.env.KOII_LLM_API_KEY
      }
      return null
    }

    try {
      const { safeStorage } = require('"'"'electron'"'"')
      const decrypted = safeStorage.decryptString(Buffer.from(config.encryptedApiKey, '"'"'hex'"'"'))
      return decrypted
    } catch (e) {
      console.error('"'"'Failed to decrypt API key:'"'"', e.message)
      return null
    }
  },

  saveConfig: function (config) {
    if (!config.apiUrl || !config.apiUrl.trim()) {
      throw new Error('"'"'API URL is required'"'"')
    }

    const configToSave = {
      apiUrl: config.apiUrl,
      modelId: config.modelId || this.defaults.modelId,
      maxTokens: config.maxTokens || this.defaults.maxTokens,
      temperature: config.temperature || this.defaults.temperature,
      enabledFeatures: config.enabledFeatures || [...this.defaults.enabledFeatures]
    }

    if (config.apiKey && config.apiKey.trim()) {
      try {
        const { safeStorage } = require('"'"'electron'"'"')
        const encrypted = safeStorage.encryptString(config.apiKey)
        configToSave.encryptedApiKey = encrypted.toString('"'"'hex'"'"')
      } catch (e) {
        console.error('"'"'Failed to encrypt API key:'"'"', e)
        throw new Error('"'"'Failed to encrypt API key'"'"')
      }
    }

    try {
      writeFileAtomic(this.configFilePath, JSON.stringify(configToSave, null, 2), {}, (err) => {
        if (err) {
          console.error('"'"'Failed to save LLM config:'"'"', err)
          throw err
        }
      })
      return true
    } catch (e) {
      console.error('"'"'Error saving LLM config:'"'"', e)
      throw e
    }
  },

  validateConnection: async function (apiUrl, apiKey, modelId) {
    if (!apiKey) {
      return { success: false, error: '"'"'API key is required'"'"' }
    }

    try {
      const response = await fetch(`${apiUrl}/messages`, {
        method: '"'"'POST'"'"',
        headers: {
          '"'"'Content-Type'"'"': '"'"'application/json'"'"',
          '"'"'x-api-key'"'"': apiKey,
          '"'"'anthropic-version'"'"': '"'"'2023-06-01'"'"'
        },
        body: JSON.stringify({
          model: modelId,
          max_tokens: 100,
          messages: [{ role: '"'"'user'"'"', content: '"'"'test'"'"' }]
        })
      })

      if (response.ok) {
        return { success: true }
      } else {
        const error = await response.json()
        return { success: false, error: error.error?.message || '"'"'API validation failed'"'"' }
      }
    } catch (e) {
      return { success: false, error: e.message }
    }
  },

  clearConfig: function () {
    try {
      const fs = require('"'"'fs'"'"')
      if (fs.existsSync(this.configFilePath)) {
        fs.unlinkSync(this.configFilePath)
      }
      return true
    } catch (e) {
      console.error('"'"'Failed to clear LLM config:'"'"', e)
      return false
    }
  }
}

module.exports = llmConfigManager'

create_file "src/koii_os/browser/core/js/util/llm/llmSettings.js" 'var llmSettings = {
  config: null,
  listeners: [],
  isInitialized: false,

  initialize: function () {
    if (this.isInitialized) return
    this.isInitialized = true

    this.loadConfig(() => {
      this.notifyListeners()
    })
  },

  loadConfig: function (callback) {
    const electron = window.electron
    if (electron && electron.ipcRenderer) {
      electron.ipcRenderer.invoke('"'"'getLLMConfig'"'"').then(config => {
        this.config = config
        if (callback) callback()
      }).catch(err => {
        console.error('"'"'Failed to load LLM config:'"'"', err)
        this.config = {
          apiUrl: '"'"'https://api.anthropic.com/v1'"'"',
          modelId: '"'"'claude-opus-4-7'"'"',
          maxTokens: 4096,
          temperature: 0.7,
          enabledFeatures: ['"'"'chat'"'"', '"'"'analysis'"'"', '"'"'autonomousAgent'"'"'],
          hasApiKey: false
        }
        if (callback) callback()
      })
    } else {
      console.warn('"'"'Electron IPC not available'"'"')
      if (callback) callback()
    }
  },

  get: function (key) {
    if (!this.config) {
      this.initialize()
    }
    if (key) {
      return this.config[key]
    }
    return this.config
  },

  set: function (key, value) {
    if (!this.config) {
      this.config = {}
    }
    this.config[key] = value
  },

  save: function (config, callback) {
    const electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      if (callback) callback(new Error('"'"'Electron IPC not available'"'"'), null)
      return
    }

    electron.ipcRenderer.invoke('"'"'saveLLMConfig'"'"', config).then(result => {
      if (result.success) {
        this.config = result.config || config
        this.notifyListeners()
        if (callback) callback(null, result)
      } else {
        if (callback) callback(new Error(result.error), null)
      }
    }).catch(err => {
      console.error('"'"'Failed to save LLM config:'"'"', err)
      if (callback) callback(err, null)
    })
  },

  validateConnection: function (apiUrl, apiKey, modelId, callback) {
    const electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      if (callback) callback(new Error('"'"'Electron IPC not available'"'"'), null)
      return
    }

    electron.ipcRenderer.invoke('"'"'validateLLMConnection'"'"', { apiUrl, apiKey, modelId }).then(result => {
      if (callback) callback(null, result)
    }).catch(err => {
      console.error('"'"'Connection validation error:'"'"', err)
      if (callback) callback(err, null)
    })
  },

  isConfigured: function () {
    return this.config && this.config.hasApiKey
  },

  isFeatureEnabled: function (feature) {
    return this.config && this.config.enabledFeatures && this.config.enabledFeatures.includes(feature)
  },

  isChatEnabled: function () {
    return this.isFeatureEnabled('"'"'chat'"'"')
  },

  isAnalysisEnabled: function () {
    return this.isFeatureEnabled('"'"'analysis'"'"')
  },

  isAgentEnabled: function () {
    return this.isFeatureEnabled('"'"'autonomousAgent'"'"')
  },

  listen: function (key, callback) {
    if (typeof key === '"'"'function'"'"') {
      this.listeners.push({ key: null, callback: key })
    } else {
      this.listeners.push({ key, callback })
    }
    if (this.config) {
      if (key) {
        callback(this.config[key])
      } else {
        callback(this.config)
      }
    }
  },

  notifyListeners: function () {
    this.listeners.forEach((listener) => {
      if (listener.key) {
        listener.callback(this.config[listener.key])
      } else {
        listener.callback(this.config)
      }
    })
  },

  onConfigChanged: function (config) {
    this.config = config
    this.notifyListeners()
  },

  clear: function (callback) {
    const electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      if (callback) callback(new Error('"'"'Electron IPC not available'"'"'))
      return
    }

    electron.ipcRenderer.invoke('"'"'clearLLMConfig'"'"').then(result => {
      if (callback) callback(null)
    }).catch(err => {
      console.error('"'"'Failed to clear LLM config:'"'"', err)
      if (callback) callback(err)
    })
  }
}

if (document.readyState === '"'"'loading'"'"') {
  document.addEventListener('"'"'DOMContentLoaded'"'"', function() {
    llmSettings.initialize()
  })
} else {
  llmSettings.initialize()
}

module.exports = llmSettings'

echo ""
echo "✓ LLM configuration files created"
echo ""
echo "Now you need to manually:"
echo ""
echo "1. Copy the remaining files from this script"
echo "2. Or download the complete implementation from GitHub"
echo ""
echo "Remaining files to create:"
echo "  - js/util/llm/llmSettingsPreload.js"
echo "  - js/util/llm/llmClient.js"
echo "  - js/util/llm/contentAnalyzer.js"
echo "  - js/util/llm/llmAgent.js"
echo "  - js/navbar/llmChatPanel.js"
echo "  - css/llmChatPanel.css"
echo "  - pages/llmSetup/index.html"
echo "  - pages/llmSetup/setup.js"
echo "  - pages/llmSetup/setup.css"
echo ""
echo "Files to modify:"
echo "  - scripts/buildMain.js"
echo "  - main/main.js"
echo "  - js/sessionRestore.js"
echo "  - js/default.js"
echo "  - Dockerfile"
echo "  - index.html"
echo ""
echo "Docker files to create:"
echo "  - docker-entrypoint.sh"
echo "  - docker-compose-browser.yml"
echo ""
echo "=================================================="
echo "Setup completed!"
echo "=================================================="
