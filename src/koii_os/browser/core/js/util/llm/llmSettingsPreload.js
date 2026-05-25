// Preload script bridge for LLM settings communication between renderer and main process
const { ipcRenderer } = require('electron')

// This module is injected in the preload script
// It provides a secure bridge between the renderer process and main process for LLM configuration

var llmSettingsPreload = {
  initialize: function () {
    // Listen for config changes from main process
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
