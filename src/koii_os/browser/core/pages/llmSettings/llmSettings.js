'use strict'

// Get electron reference - works in both direct page load and iframe contexts
const electron = (() => {
  if (typeof window.electron !== 'undefined') return window.electron
  if (typeof window.parent !== 'undefined' && window.parent.electron) return window.parent.electron
  try {
    return require('electron')
  } catch (e) {
    console.warn('Electron not available:', e)
    return null
  }
})()

// ── Provider presets ────────────────────────────────────────────────────────

const PROVIDERS = {
  anthropic: {
    label: 'Anthropic',
    apiUrl: 'https://api.anthropic.com/v1',
    models: [
      { id: 'claude-opus-4-6',    label: 'Claude Opus 4.6 (Most capable)' },
      { id: 'claude-sonnet-4-6',  label: 'Claude Sonnet 4.6 (Balanced)' },
      { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5 (Fast)' }
    ]
  },
  openai: {
    label: 'OpenAI',
    apiUrl: 'https://api.openai.com/v1',
    models: [
      { id: 'gpt-4o',         label: 'GPT-4o (Best)' },
      { id: 'gpt-4o-mini',    label: 'GPT-4o mini (Fast)' },
      { id: 'gpt-4-turbo',    label: 'GPT-4 Turbo' },
      { id: 'gpt-3.5-turbo',  label: 'GPT-3.5 Turbo (Economy)' }
    ]
  },
  openai_compat: {
    label: 'OpenAI-Compatible',
    apiUrl: 'http://localhost:11434/v1',
    models: [
      { id: 'llama3',           label: 'Llama 3 (Ollama)' },
      { id: 'mistral',          label: 'Mistral (Ollama)' },
      { id: 'mixtral',          label: 'Mixtral (Ollama)' },
      { id: 'codellama',        label: 'CodeLlama (Ollama)' },
      { id: 'gemma',            label: 'Gemma (Ollama)' }
    ]
  },
  custom: {
    label: 'Custom',
    apiUrl: '',
    models: []
  }
}

// ── DOM helpers ─────────────────────────────────────────────────────────────

const $  = id => document.getElementById(id)
const el = sel => document.querySelector(sel)

// ── State ───────────────────────────────────────────────────────────────────

let currentConfig = {
  provider: 'anthropic',
  apiUrl: PROVIDERS.anthropic.apiUrl,
  modelId: 'claude-opus-4-6',
  maxTokens: 4096,
  temperature: 0.7,
  timeout: 60,
  enabledFeatures: ['chat', 'analysis', 'autonomousAgent', 'semanticSearch', 'selfLearning'],
  agents: {
    OrchestrationAgent:  true,
    TaskExecutionAgent:  true,
    AIBrowserAgent:      true,
    SelfLearningAgent:   true
  }
}

// ── Initialization ───────────────────────────────────────────────────────────

async function init () {
  // Load saved config via IPC
  if (electron && electron.ipcRenderer) {
    try {
      const saved = await electron.ipcRenderer.invoke('getLLMConfig')
      if (saved) mergeConfig(saved)
    } catch (err) {
      console.warn('Could not load config via IPC, using defaults:', err)
    }
  } else {
    console.warn('Electron IPC not available - running in limited mode')
  }

  renderUI()
  bindEvents()
}

function mergeConfig (saved) {
  if (saved.apiUrl) currentConfig.apiUrl = saved.apiUrl
  if (saved.modelId) currentConfig.modelId = saved.modelId
  if (saved.maxTokens) currentConfig.maxTokens = saved.maxTokens
  if (saved.temperature !== undefined) currentConfig.temperature = saved.temperature
  if (saved.enabledFeatures) currentConfig.enabledFeatures = saved.enabledFeatures
  if (saved.agents) currentConfig.agents = { ...currentConfig.agents, ...saved.agents }
  currentConfig.hasApiKey = !!saved.hasApiKey

  // Detect provider from URL
  if (saved.apiUrl) {
    if (saved.apiUrl.includes('anthropic.com'))  currentConfig.provider = 'anthropic'
    else if (saved.apiUrl.includes('openai.com'))currentConfig.provider = 'openai'
    else if (saved.apiUrl.includes('localhost')) currentConfig.provider = 'openai_compat'
    else currentConfig.provider = 'custom'
  }
}

// ── Render ───────────────────────────────────────────────────────────────────

function renderUI () {
  // Provider select
  $('apiProvider').value = currentConfig.provider

  // URL and model
  $('apiUrl').value   = currentConfig.apiUrl
  $('modelId').value  = currentConfig.modelId

  // Advanced
  $('maxTokens').value  = currentConfig.maxTokens
  $('temperature').value = currentConfig.temperature
  $('timeout').value    = currentConfig.timeout || 60

  // Show masked placeholder for key if saved
  if (currentConfig.hasApiKey) {
    $('apiKey').placeholder = '••••••••••••••••  (saved — leave blank to keep)'
  }

  // Model presets
  renderModelPresets(currentConfig.provider)

  // Feature checkboxes
  document.querySelectorAll('[data-feature]').forEach(cb => {
    cb.checked = currentConfig.enabledFeatures.includes(cb.dataset.feature)
  })

  // Agent toggles
  const agentMap = {
    toggle_orchestration: 'OrchestrationAgent',
    toggle_execution:     'TaskExecutionAgent',
    toggle_browser:       'AIBrowserAgent',
    toggle_learning:      'SelfLearningAgent'
  }
  for (const [id, name] of Object.entries(agentMap)) {
    const cb = $(id)
    if (cb) cb.checked = currentConfig.agents[name] !== false
  }
}

function renderModelPresets (provider) {
  const preset = PROVIDERS[provider] || PROVIDERS.custom
  const grid   = $('modelPresetGrid')
  const select = $('modelPreset')

  // Update select options
  select.innerHTML = '<option value="">— Presets —</option>'
  preset.models.forEach(m => {
    const opt = document.createElement('option')
    opt.value = m.id
    opt.textContent = m.label
    select.appendChild(opt)
  })

  // Render chip grid
  grid.innerHTML = ''
  preset.models.forEach(m => {
    const chip = document.createElement('button')
    chip.className = 'ls-model-chip' + (m.id === currentConfig.modelId ? ' active' : '')
    chip.textContent = m.id
    chip.title = m.label
    chip.type = 'button'
    chip.onclick = () => {
      $('modelId').value = m.id
      grid.querySelectorAll('.ls-model-chip').forEach(c => c.classList.remove('active'))
      chip.classList.add('active')
    }
    grid.appendChild(chip)
  })
}

// ── Event bindings ────────────────────────────────────────────────────────────

function bindEvents () {
  // Provider change
  $('apiProvider').addEventListener('change', () => {
    const p = $('apiProvider').value
    const preset = PROVIDERS[p] || PROVIDERS.custom
    if (preset.apiUrl) $('apiUrl').value = preset.apiUrl
    if (preset.models.length > 0) $('modelId').value = preset.models[0].id
    renderModelPresets(p)
  })

  // Model preset select
  $('modelPreset').addEventListener('change', () => {
    const val = $('modelPreset').value
    if (val) {
      $('modelId').value = val
      $('modelPresetGrid').querySelectorAll('.ls-model-chip').forEach(c => {
        c.classList.toggle('active', c.textContent === val)
      })
    }
  })

  // Toggle key visibility
  $('toggleKeyBtn').addEventListener('click', () => {
    const inp = $('apiKey')
    inp.type = inp.type === 'password' ? 'text' : 'password'
    $('toggleKeyBtn').textContent = inp.type === 'password' ? '👁' : '🙈'
  })

  // Test connection
  $('testConnectionBtn').addEventListener('click', testConnection)

  // Save
  $('saveBtn').addEventListener('click', saveConfig)

  // Clear / reset
  $('clearBtn').addEventListener('click', clearConfig)
}

// ── Test connection ───────────────────────────────────────────────────────────

async function testConnection () {
  const btn = $('testConnectionBtn')
  const result = $('testResult')

  const apiUrl = $('apiUrl').value.trim()
  const apiKey = $('apiKey').value.trim()
  const modelId = $('modelId').value.trim()

  if (!apiUrl) { showTestResult('Enter an API URL first.', 'error'); return }

  btn.disabled = true
  btn.textContent = '⏳ Testing…'
  showTestResult('Connecting to API…', 'loading')

  try {
    const response = await fetch(`${apiUrl}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'Authorization': apiKey ? `Bearer ${apiKey}` : undefined
      },
      body: JSON.stringify({
        model: modelId || 'claude-opus-4-6',
        max_tokens: 10,
        messages: [{ role: 'user', content: 'ping' }]
      }),
      signal: AbortSignal.timeout(15000)
    })

    if (response.ok || response.status === 400) {
      // 400 can mean the model exists but params are wrong — still means API is alive
      showTestResult('✅ Connection successful! API is reachable.', 'ok')
    } else {
      const body = await response.json().catch(() => ({}))
      showTestResult(`❌ API error ${response.status}: ${body.error?.message || response.statusText}`, 'error')
    }
  } catch (err) {
    if (err.name === 'TimeoutError') {
      showTestResult('❌ Connection timed out. Check the URL.', 'error')
    } else {
      showTestResult(`❌ ${err.message}`, 'error')
    }
  } finally {
    btn.disabled = false
    btn.textContent = '⚡ Test Connection'
  }
}

function showTestResult (message, type) {
  const el = $('testResult')
  el.style.display = ''
  el.className = `ls-test-result ls-test-${type}`
  el.textContent = message
}

// ── Save ─────────────────────────────────────────────────────────────────────

async function saveConfig () {
  const config = readFormValues()

  if (!electron || !electron.ipcRenderer) {
    showSaveStatus('❌ Electron IPC not available. Cannot save settings.', 'error')
    return
  }

  try {
    await electron.ipcRenderer.invoke('saveLLMConfig', config)
    showSaveStatus('✅ Settings saved successfully!', 'ok')

    // Also trigger an in-process update if llmSettings module is available
    try {
      const llmSettings = require('util/llm/llmSettings')
      llmSettings.initialize()
    } catch (_) {}

  } catch (err) {
    showSaveStatus(`❌ Failed to save: ${err.message}`, 'error')
  }
}

function readFormValues () {
  const apiKey = $('apiKey').value.trim()

  // Collect enabled features
  const features = []
  document.querySelectorAll('[data-feature]').forEach(cb => {
    if (cb.checked) features.push(cb.dataset.feature)
  })

  // Collect agent states
  const agents = {
    SemanticUnderstandingAgent: true,  // always on
    OrchestrationAgent:  $('toggle_orchestration').checked,
    TaskExecutionAgent:  $('toggle_execution').checked,
    AIBrowserAgent:      $('toggle_browser').checked,
    SelfLearningAgent:   $('toggle_learning').checked
  }

  const config = {
    provider:        $('apiProvider').value,
    apiUrl:          $('apiUrl').value.trim(),
    modelId:         $('modelId').value.trim(),
    maxTokens:       parseInt($('maxTokens').value, 10) || 4096,
    temperature:     parseFloat($('temperature').value) || 0.7,
    timeout:         parseInt($('timeout').value, 10) || 60,
    enabledFeatures: features,
    agents
  }

  if (apiKey) config.apiKey = apiKey

  return config
}

function showSaveStatus (message, type) {
  const el = $('saveStatus')
  el.style.display = ''
  el.className = `ls-save-status ls-save-${type}`
  el.textContent = message
  setTimeout(() => { el.style.display = 'none' }, 4000)
}

// ── Clear ─────────────────────────────────────────────────────────────────────

async function clearConfig () {
  if (!confirm('Clear all LLM settings? This will remove your API key and reset all options.')) return

  if (!electron || !electron.ipcRenderer) {
    showSaveStatus('❌ Electron IPC not available. Cannot clear settings.', 'error')
    return
  }

  try {
    await electron.ipcRenderer.invoke('clearLLMConfig')
    currentConfig = {
      provider: 'anthropic',
      apiUrl: PROVIDERS.anthropic.apiUrl,
      modelId: 'claude-opus-4-6',
      maxTokens: 4096,
      temperature: 0.7,
      timeout: 60,
      enabledFeatures: ['chat', 'analysis', 'autonomousAgent', 'semanticSearch', 'selfLearning'],
      agents: { OrchestrationAgent: true, TaskExecutionAgent: true, AIBrowserAgent: true, SelfLearningAgent: true }
    }
    renderUI()
    showSaveStatus('Settings cleared and reset to defaults.', 'ok')
  } catch (err) {
    showSaveStatus(`❌ ${err.message}`, 'error')
  }
}

// ── Boot ───────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', init)
