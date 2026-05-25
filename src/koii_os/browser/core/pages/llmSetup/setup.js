// LLM Setup Wizard
const setupWizard = {
  currentStep: 'welcome',
  formData: {
    apiUrl: 'https://api.anthropic.com/v1',
    apiKey: '',
    modelId: 'claude-opus-4-7',
    maxTokens: 4096,
    temperature: 0.7,
    enabledFeatures: ['chat', 'analysis', 'autonomousAgent']
  },

  initialize: function() {
    // Check if LLM is already configured
    const electron = window.electron || (window.parent && window.parent.electron)
    if (electron && electron.ipcRenderer) {
      electron.ipcRenderer.invoke('getLLMConfig').then(config => {
        if (config && config.hasApiKey) {
          // Already configured, close this modal
          this.closeSetup()
          return
        }
        this.setupEventListeners()
        this.loadFormData()
      })
    } else {
      this.setupEventListeners()
      this.loadFormData()
    }
  },

  setupEventListeners: function() {
    // API URL input
    const apiUrlInput = document.getElementById('apiUrl')
    if (apiUrlInput) {
      apiUrlInput.addEventListener('change', (e) => {
        this.formData.apiUrl = e.target.value
      })
    }

    // API Key input
    const apiKeyInput = document.getElementById('apiKey')
    if (apiKeyInput) {
      apiKeyInput.addEventListener('change', (e) => {
        this.formData.apiKey = e.target.value
      })
    }

    // Model ID input
    const modelInput = document.getElementById('modelId')
    if (modelInput) {
      modelInput.addEventListener('change', (e) => {
        this.formData.modelId = e.target.value
      })
    }

    // Max tokens input
    const maxTokensInput = document.getElementById('maxTokens')
    if (maxTokensInput) {
      maxTokensInput.addEventListener('change', (e) => {
        this.formData.maxTokens = parseInt(e.target.value) || 4096
      })
    }

    // Temperature input
    const tempInput = document.getElementById('temperature')
    if (tempInput) {
      tempInput.addEventListener('change', (e) => {
        this.formData.temperature = parseFloat(e.target.value) || 0.7
      })
    }

    // Feature checkboxes
    document.getElementById('enableChat')?.addEventListener('change', (e) => {
      this.updateFeatures()
    })
    document.getElementById('enableAnalysis')?.addEventListener('change', (e) => {
      this.updateFeatures()
    })
    document.getElementById('enableAgent')?.addEventListener('change', (e) => {
      this.updateFeatures()
    })
  },

  loadFormData: function() {
    document.getElementById('apiUrl').value = this.formData.apiUrl
    document.getElementById('modelId').value = this.formData.modelId
    document.getElementById('maxTokens').value = this.formData.maxTokens
    document.getElementById('temperature').value = this.formData.temperature

    document.getElementById('enableChat').checked = this.formData.enabledFeatures.includes('chat')
    document.getElementById('enableAnalysis').checked = this.formData.enabledFeatures.includes('analysis')
    document.getElementById('enableAgent').checked = this.formData.enabledFeatures.includes('autonomousAgent')
  },

  updateFeatures: function() {
    this.formData.enabledFeatures = []
    if (document.getElementById('enableChat').checked) {
      this.formData.enabledFeatures.push('chat')
    }
    if (document.getElementById('enableAnalysis').checked) {
      this.formData.enabledFeatures.push('analysis')
    }
    if (document.getElementById('enableAgent').checked) {
      this.formData.enabledFeatures.push('autonomousAgent')
    }
  },

  goToStep: function(stepName) {
    // Hide current step
    const currentStepEl = document.getElementById(`step-${this.currentStep}`)
    if (currentStepEl) {
      currentStepEl.classList.remove('active')
    }

    // Show new step
    this.currentStep = stepName
    const newStepEl = document.getElementById(`step-${stepName}`)
    if (newStepEl) {
      newStepEl.classList.add('active')
    }

    // Update progress indicator
    this.updateProgress()

    // Scroll to top
    document.querySelector('.llm-setup-content').scrollTop = 0
  },

  updateProgress: function() {
    const steps = document.querySelectorAll('.progress-step')
    const stepOrder = ['welcome', 'api-url', 'api-key', 'model-selection', 'features', 'confirmation']
    const currentIndex = stepOrder.indexOf(this.currentStep)

    steps.forEach((step, index) => {
      step.classList.remove('active', 'completed')
      if (index < currentIndex) {
        step.classList.add('completed')
      } else if (index === currentIndex) {
        step.classList.add('active')
      }
    })
  },

  testAndContinue: function() {
    // Validate form
    if (!this.formData.apiUrl.trim() || !this.formData.apiKey.trim() || !this.formData.modelId.trim()) {
      alert('Please fill in all required fields')
      return
    }

    // Show loading state
    const testBtn = event.target
    const originalText = testBtn.textContent
    testBtn.disabled = true
    testBtn.textContent = 'Testing...'

    // Validate connection via IPC
    const electron = window.electron || (window.parent && window.parent.electron)
    if (electron && electron.ipcRenderer) {
      electron.ipcRenderer.invoke('validateLLMConnection', {
        apiUrl: this.formData.apiUrl,
        apiKey: this.formData.apiKey,
        modelId: this.formData.modelId
      }).then(result => {
        testBtn.disabled = false
        testBtn.textContent = originalText

        if (!result.success) {
          this.showError(result.error)
        } else {
          // Connection successful, go to features step
          this.goToStep('features')
        }
      }).catch(err => {
        testBtn.disabled = false
        testBtn.textContent = originalText
        this.showError(err.message)
      })
    } else {
      testBtn.disabled = false
      testBtn.textContent = originalText
      console.error('Electron IPC not available')
      alert('Cannot validate connection: Electron IPC not available')
    }
  },

  showError: function(errorMessage) {
    document.getElementById('errorMessage').textContent = errorMessage || 'Connection failed. Please check your API key and URL.'
    document.getElementById('errorDetails').textContent = ''
    this.goToStep('error')
  },

  finishSetup: function() {
    // Update features
    this.updateFeatures()

    // Prepare config
    const config = {
      apiUrl: this.formData.apiUrl,
      apiKey: this.formData.apiKey,
      modelId: this.formData.modelId,
      maxTokens: this.formData.maxTokens,
      temperature: this.formData.temperature,
      enabledFeatures: this.formData.enabledFeatures
    }

    // Save via IPC
    const electron = window.electron || (window.parent && window.parent.electron)
    if (electron && electron.ipcRenderer) {
      electron.ipcRenderer.invoke('saveLLMConfig', config).then(result => {
        if (result.success) {
          // Mark setup as complete and close
          localStorage.setItem('llmSetupComplete', 'true')
          this.closeSetup()
        } else {
          alert('Failed to save configuration: ' + result.error)
        }
      }).catch(err => {
        console.error('Failed to save LLM config:', err)
        alert('Failed to save configuration: ' + err.message)
      })
    } else {
      console.error('Electron IPC not available')
      alert('Cannot save configuration: Electron IPC not available')
    }
  },

  skipSetup: function() {
    // Mark as skipped
    localStorage.setItem('llmSetupSkipped', 'true')
    this.closeSetup()
  },

  closeSetup: function() {
    // Close the setup modal
    if (window.parent && window.parent !== window) {
      // If in iframe, signal parent to close
      window.parent.postMessage({ type: 'closeModal', name: 'llmSetup' }, '*')
    } else {
      // Direct navigation
      window.location.href = 'min://app/index.html'
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    setupWizard.initialize()
  })
} else {
  setupWizard.initialize()
}
