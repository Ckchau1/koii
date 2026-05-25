const fs = require('fs')
const path = require('path')
const { safeStorage } = require('electron')

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

    // Check for environment variable overrides
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
      // Try environment variable as fallback
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
    // Validate required fields
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

    // Encrypt API key if provided
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
      const writeFileAtomic = require('write-file-atomic')
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
    // Test the API connection by making a simple request
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

module.exports = llmConfigManager
