#!/usr/bin/env python3
"""
AIOS LLM Integration Setup Script
Sets up all LLM integration features for the Min browser.
Run from repository root: python3 setup_llm_integration.py
"""

import os
import sys
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def create_file(filepath, content):
    """Create a file with the given content."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print_success(f"Created: {filepath}")

def create_files():
    """Create all LLM integration files."""

    base_dir = Path.cwd()

    print_header("AIOS LLM Integration Setup")
    print_info(f"Working directory: {base_dir}\n")

    # ========================================================================
    # LLM Configuration Manager
    # ========================================================================

    print_info("Creating LLM configuration files...")

    llm_config_manager = '''const writeFileAtomic = require('write-file-atomic')
const path = require('path')
const { safeStorage } = require('electron')
const fs = require('fs')

var llmConfigManager = {
  userDataPath: null,
  configFilePath: null,
  defaults: {
    apiUrl: 'https://api.anthropic.com/v1',
    modelId: 'claude-opus-4-7',
    maxTokens: 4096,
    temperature: 0.7,
    enabledFeatures: ['chat', 'analysis', 'autonomousAgent']
  },

  initialize: function (userDataPath) {
    this.userDataPath = userDataPath
    this.configFilePath = path.join(userDataPath, 'llmConfig.json')
    if (process.env.KOII_LLM_API_URL) {
      this.defaults.apiUrl = process.env.KOII_LLM_API_URL
    }
    this.loadConfig()
  },

  loadConfig: function () {
    try {
      if (fs.existsSync(this.configFilePath)) {
        const data = fs.readFileSync(this.configFilePath, 'utf-8')
        const config = JSON.parse(data)
        return config
      }
    } catch (e) {
      console.warn('Error reading LLM config file:', e)
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
      const decrypted = safeStorage.decryptString(Buffer.from(config.encryptedApiKey, 'hex'))
      return decrypted
    } catch (e) {
      console.error('Failed to decrypt API key:', e.message)
      return null
    }
  },

  saveConfig: function (config) {
    if (!config.apiUrl || !config.apiUrl.trim()) {
      throw new Error('API URL is required')
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
        const encrypted = safeStorage.encryptString(config.apiKey)
        configToSave.encryptedApiKey = encrypted.toString('hex')
      } catch (e) {
        console.error('Failed to encrypt API key:', e)
        throw new Error('Failed to encrypt API key')
      }
    }
    try {
      writeFileAtomic(this.configFilePath, JSON.stringify(configToSave, null, 2), {}, (err) => {
        if (err) {
          console.error('Failed to save LLM config:', err)
          throw err
        }
      })
      return true
    } catch (e) {
      console.error('Error saving LLM config:', e)
      throw e
    }
  },

  validateConnection: async function (apiUrl, apiKey, modelId) {
    if (!apiKey) {
      return { success: false, error: 'API key is required' }
    }
    try {
      const response = await fetch(`${apiUrl}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: modelId,
          max_tokens: 100,
          messages: [{ role: 'user', content: 'test' }]
        })
      })
      if (response.ok) {
        return { success: true }
      } else {
        const error = await response.json()
        return { success: false, error: error.error?.message || 'API validation failed' }
      }
    } catch (e) {
      return { success: false, error: e.message }
    }
  },

  clearConfig: function () {
    try {
      if (fs.existsSync(this.configFilePath)) {
        fs.unlinkSync(this.configFilePath)
      }
      return true
    } catch (e) {
      console.error('Failed to clear LLM config:', e)
      return false
    }
  }
}

module.exports = llmConfigManager'''

    create_file(
        'src/koii_os/browser/core/main/llmConfigManager.js',
        llm_config_manager
    )

    # ========================================================================
    # LLM Settings (Renderer-side)
    # ========================================================================

    llm_settings = '''var llmSettings = {
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
      electron.ipcRenderer.invoke('getLLMConfig').then(config => {
        this.config = config
        if (callback) callback()
      }).catch(err => {
        console.error('Failed to load LLM config:', err)
        this.config = {
          apiUrl: 'https://api.anthropic.com/v1',
          modelId: 'claude-opus-4-7',
          maxTokens: 4096,
          temperature: 0.7,
          enabledFeatures: ['chat', 'analysis', 'autonomousAgent'],
          hasApiKey: false
        }
        if (callback) callback()
      })
    } else {
      console.warn('Electron IPC not available')
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
      if (callback) callback(new Error('Electron IPC not available'), null)
      return
    }
    electron.ipcRenderer.invoke('saveLLMConfig', config).then(result => {
      if (result.success) {
        this.config = result.config || config
        this.notifyListeners()
        if (callback) callback(null, result)
      } else {
        if (callback) callback(new Error(result.error), null)
      }
    }).catch(err => {
      console.error('Failed to save LLM config:', err)
      if (callback) callback(err, null)
    })
  },

  validateConnection: function (apiUrl, apiKey, modelId, callback) {
    const electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      if (callback) callback(new Error('Electron IPC not available'), null)
      return
    }
    electron.ipcRenderer.invoke('validateLLMConnection', { apiUrl, apiKey, modelId }).then(result => {
      if (callback) callback(null, result)
    }).catch(err => {
      console.error('Connection validation error:', err)
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
    return this.isFeatureEnabled('chat')
  },

  isAnalysisEnabled: function () {
    return this.isFeatureEnabled('analysis')
  },

  isAgentEnabled: function () {
    return this.isFeatureEnabled('autonomousAgent')
  },

  listen: function (key, callback) {
    if (typeof key === 'function') {
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
      if (callback) callback(new Error('Electron IPC not available'))
      return
    }
    electron.ipcRenderer.invoke('clearLLMConfig').then(result => {
      if (callback) callback(null)
    }).catch(err => {
      console.error('Failed to clear LLM config:', err)
      if (callback) callback(err)
    })
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    llmSettings.initialize()
  })
} else {
  llmSettings.initialize()
}

module.exports = llmSettings'''

    create_file(
        'src/koii_os/browser/core/js/util/llm/llmSettings.js',
        llm_settings
    )

    print_success("Core configuration files created\n")

    # ========================================================================
    # File Modification Instructions
    # ========================================================================

    print_header("Files To Modify")

    modifications = [
        {
            'file': 'src/koii_os/browser/core/scripts/buildMain.js',
            'find': "'js/util/settings/settingsMain.js',",
            'add_after': "    'main/llmConfigManager.js',"
        },
        {
            'file': 'src/koii_os/browser/core/main/main.js',
            'find': 'settings.initialize(userDataPath)',
            'add_after': 'llmConfigManager.initialize(userDataPath)'
        },
        {
            'file': 'src/koii_os/browser/core/js/default.js',
            'find': "require('util/llm/llmSettings.js').initialize()",
            'add': "require('util/llm/llmSettings.js').initialize()\nrequire('navbar/llmChatPanel.js').initialize()\nrequire('util/llm/contentAnalyzer.js').initialize()\nrequire('util/llm/llmAgent.js').initialize()"
        }
    ]

    for mod in modifications:
        print_warning(f"Manual edit required: {mod['file']}")
        if 'find' in mod:
            print(f"  Find: {mod['find']}")
        if 'add_after' in mod:
            print(f"  Add after: {mod['add_after']}")
        if 'add' in mod:
            print(f"  Add: {mod['add']}")
        print()

    print_header("Files To Create (Still Needed)")

    files_needed = [
        "src/koii_os/browser/core/js/util/llm/llmClient.js",
        "src/koii_os/browser/core/js/util/llm/contentAnalyzer.js",
        "src/koii_os/browser/core/js/util/llm/llmAgent.js",
        "src/koii_os/browser/core/js/navbar/llmChatPanel.js",
        "src/koii_os/browser/core/css/llmChatPanel.css",
        "src/koii_os/browser/core/pages/llmSetup/index.html",
        "src/koii_os/browser/core/pages/llmSetup/setup.js",
        "src/koii_os/browser/core/pages/llmSetup/setup.css",
        "docker-entrypoint.sh",
        "docker-compose-browser.yml",
    ]

    for file in files_needed:
        print(f"  □ {file}")

    print_header("Next Steps")

    print_info("All complete file content is available in the GitHub repository.")
    print_info("Download or copy the LLM integration implementation from:\n")
    print(f"{BLUE}https://github.com/Ckchau1/koii{RESET}\n")
    print_info("Or request individual file contents to be created.\n")

    return True

if __name__ == '__main__':
    try:
        create_files()
        print_success("\n✓ Setup initialization complete!")
        print_info("Please follow the manual steps above to complete the installation.\n")
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        sys.exit(1)
