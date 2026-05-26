const { contextBridge, ipcRenderer } = require('electron');

// Expose IPC methods to React app
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuration management
  getConfigs: () => ipcRenderer.invoke('config:get-all'),
  getConfig: (provider) => ipcRenderer.invoke('config:get', provider),
  saveConfig: (provider, config) => ipcRenderer.invoke('config:save', provider, config),
  deleteConfig: (provider) => ipcRenderer.invoke('config:delete', provider),

  // LLM testing and model retrieval
  testConnection: (provider, config) => ipcRenderer.invoke('llm:test-connection', provider, config),
  listModels: (provider, apiKey, baseUrl) => ipcRenderer.invoke('llm:list-models', provider, apiKey, baseUrl),

  // System info
  getPlatform: () => process.platform,
  getAppVersion: () => require('electron').app.getVersion(),
});
