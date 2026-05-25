// Renderer-side API for LLM settings configuration
// This provides a clean interface for UI components to interact with LLM configuration

var llmSettings = {
  config: null,
  listeners: [],
  isInitialized: false,

  initialize: function () {
    if (this.isInitialized) return
    this.isInitialized = true

    // Setup IPC listener for config changes from main process
    if (window.llmSettingsPreload) {
      window.llmSettingsPreload.initialize()
    }

    // Load initial config
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
      // Global listener
      this.listeners.push({ key: null, callback: key })
    } else {
      this.listeners.push({ key, callback })
    }
    // Call immediately with current value
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
    if (!window.llmSettingsPreload) {
      if (callback) callback(new Error('LLM settings preload not available'))
      return
    }

    window.llmSettingsPreload.clearConfig((err, result) => {
      if (err) {
        console.error('Failed to clear LLM config:', err)
        if (callback) callback(err)
      } else {
        this.config = null
        this.notifyListeners()
        if (callback) callback(null)
      }
    })
  }
}

// Auto-initialize when settings module is first accessed
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function () {
    llmSettings.initialize()
  })
} else {
  llmSettings.initialize()
}

module.exports = llmSettings
