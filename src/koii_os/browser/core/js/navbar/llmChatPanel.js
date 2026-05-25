// LLM Chat Panel - Slide-out chat sidebar for interacting with LLM
var llmClient = require('util/llm/llmClient.js')
var llmSettings = require('util/llm/llmSettings.js')
var database = require('util/database.js')

var llmChatPanel = {
  isInitialized: false,
  isOpen: false,
  currentMessages: [],
  isLoading: false,

  initialize: function() {
    if (this.isInitialized) return
    this.isInitialized = true

    // Only initialize if chat is enabled
    if (!llmSettings.isChatEnabled()) {
      return
    }

    // Load configuration
    const config = llmSettings.get()
    if (!config || !config.hasApiKey) {
      return
    }

    // Initialize database for storing chats
    this.initializeDatabase()

    // Create UI elements
    this.createChatButton()
    this.createChatPanel()

    // Setup event listeners
    this.setupEventListeners()
  },

  initializeDatabase: function() {
    database.browserData.table('llmChats').toArray().then(chats => {
      // Database ready for chat storage
    }).catch(err => {
      console.warn('LLM chats table not available:', err)
    })
  },

  createChatButton: function() {
    // Create toggle button in navbar
    const navbar = document.querySelector('.navbar')
    if (!navbar) return

    const chatButton = document.createElement('div')
    chatButton.id = 'llmChatButton'
    chatButton.className = 'llm-chat-button'
    chatButton.title = 'Chat with AI'
    chatButton.innerHTML = '💬'

    chatButton.addEventListener('click', (e) => {
      e.stopPropagation()
      this.togglePanel()
    })

    // Insert before menu button
    const menuButton = navbar.querySelector('[aria-label="Menu"]')
    if (menuButton) {
      menuButton.parentNode.insertBefore(chatButton, menuButton)
    } else {
      navbar.appendChild(chatButton)
    }
  },

  createChatPanel: function() {
    // Create chat panel DOM structure
    const panel = document.createElement('div')
    panel.id = 'llmChatPanel'
    panel.className = 'llm-chat-panel'
    panel.innerHTML = `
      <div class="chat-header">
        <h2>Chat</h2>
        <div class="chat-controls">
          <button class="chat-clear-btn" title="Clear history">🗑️</button>
          <button class="chat-close-btn" title="Close">✕</button>
        </div>
      </div>

      <div class="chat-messages" id="chatMessages"></div>

      <div class="chat-input-area">
        <div class="chat-context-option">
          <label>
            <input type="checkbox" id="includePageContext" checked />
            <span>Include page context</span>
          </label>
        </div>

        <div class="chat-input-wrapper">
          <textarea
            id="chatInput"
            class="chat-input"
            placeholder="Ask AI about this page..."
            rows="3"
          ></textarea>
          <button class="chat-send-btn">Send</button>
        </div>
      </div>

      <div class="chat-status" id="chatStatus"></div>
    `

    document.body.appendChild(panel)
    this.setupPanelEventListeners()
  },

  setupPanelEventListeners: function() {
    const closeBtn = document.querySelector('.chat-close-btn')
    const clearBtn = document.querySelector('.chat-clear-btn')
    const sendBtn = document.querySelector('.chat-send-btn')
    const input = document.getElementById('chatInput')

    closeBtn?.addEventListener('click', () => this.closePanel())
    clearBtn?.addEventListener('click', () => this.clearHistory())
    sendBtn?.addEventListener('click', () => this.sendMessage())

    input?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        this.sendMessage()
      }
    })

    // Auto-resize textarea
    input?.addEventListener('input', () => {
      input.style.height = 'auto'
      input.style.height = Math.min(input.scrollHeight, 150) + 'px'
    })
  },

  setupEventListeners: function() {
    // Listen for LLM config changes
    llmSettings.listen('hasApiKey', (hasKey) => {
      if (!hasKey) {
        this.closePanel()
      }
    })

    // Load chat history on init
    this.loadChatHistory()
  },

  loadChatHistory: function() {
    if (!database.browserData) return

    database.browserData.table('llmChats')
      .orderBy('timestamp')
      .toArray()
      .then(chats => {
        if (chats && chats.length > 0) {
          this.currentMessages = chats[chats.length - 1].messages || []
          this.renderMessages()
        }
      })
      .catch(err => console.warn('Failed to load chat history:', err))
  },

  sendMessage: function() {
    if (this.isLoading) return

    const input = document.getElementById('chatInput')
    const message = input?.value.trim()

    if (!message) return

    // Add user message
    this.currentMessages.push({
      role: 'user',
      content: message
    })

    // Clear input
    input.value = ''
    input.style.height = 'auto'

    // Render messages
    this.renderMessages()

    // Show loading state
    this.isLoading = true
    this.setStatus('Thinking...')

    // Build context if enabled
    let contextPrompt = null
    if (document.getElementById('includePageContext')?.checked) {
      contextPrompt = llmClient.getPageContextPrompt()
    }

    // Get LLM config and key
    const config = llmSettings.get()
    const electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      this.setStatus('Error: Cannot connect to LLM')
      this.isLoading = false
      return
    }

    // Get the API key from main process
    electron.ipcRenderer.invoke('getLLMConfig').then(currentConfig => {
      // Get the actual API key (encrypted in main process)
      // For now, we'll need to implement a separate handler for this
      // or store it in a secure way

      // Use the llmClient to send message
      const callbacks = {
        onChunk: (text) => {
          // Update the last message as it streams
          if (this.currentMessages.length > 0) {
            const lastMsg = this.currentMessages[this.currentMessages.length - 1]
            if (lastMsg.role === 'assistant') {
              lastMsg.content += text
              this.renderMessages()
              this.scrollToBottom()
            }
          }
        },
        onComplete: (message) => {
          this.currentMessages.push(message)
          this.renderMessages()
          this.scrollToBottom()
          this.isLoading = false
          this.setStatus('')
          this.saveChatHistory()
        },
        onError: (error) => {
          this.addSystemMessage('Error: ' + error.message)
          this.isLoading = false
          this.setStatus('')
        }
      }

      // Note: We need to implement a way to securely get the API key
      // For now, we'll skip the actual LLM call and show a placeholder
      this.showPlaceholderResponse(contextPrompt)
    })
  },

  showPlaceholderResponse: function(contextPrompt) {
    // Placeholder response while we implement proper API key handling
    setTimeout(() => {
      const responses = [
        'I can see you\'re working on a web page. What would you like to know about it?',
        'Based on the current page, I\'m ready to help. What can I assist you with?',
        'I notice you\'re browsing. Feel free to ask me anything about the page content.',
      ]

      const response = responses[Math.floor(Math.random() * responses.length)]
      this.currentMessages.push({
        role: 'assistant',
        content: response
      })

      this.renderMessages()
      this.scrollToBottom()
      this.isLoading = false
      this.setStatus('')
      this.saveChatHistory()
    }, 800)
  },

  renderMessages: function() {
    const container = document.getElementById('chatMessages')
    if (!container) return

    container.innerHTML = ''

    this.currentMessages.forEach(msg => {
      const msgEl = document.createElement('div')
      msgEl.className = `chat-message ${msg.role === 'user' ? 'user' : 'assistant'}`

      // Simple HTML escape
      let content = msg.content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')

      msgEl.innerHTML = content
      container.appendChild(msgEl)
    })

    this.scrollToBottom()
  },

  scrollToBottom: function() {
    const container = document.getElementById('chatMessages')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  },

  setStatus: function(text) {
    const status = document.getElementById('chatStatus')
    if (status) {
      status.textContent = text
    }
  },

  addSystemMessage: function(text) {
    const msgEl = document.createElement('div')
    msgEl.className = 'chat-message system'
    msgEl.textContent = text

    const container = document.getElementById('chatMessages')
    if (container) {
      container.appendChild(msgEl)
      this.scrollToBottom()
    }
  },

  clearHistory: function() {
    if (confirm('Clear all chat history?')) {
      this.currentMessages = []
      this.renderMessages()

      if (database.browserData) {
        database.browserData.table('llmChats').clear().catch(err => {
          console.warn('Failed to clear chat history:', err)
        })
      }
    }
  },

  saveChatHistory: function() {
    if (!database.browserData || this.currentMessages.length === 0) return

    const chatData = {
      timestamp: Date.now(),
      messages: this.currentMessages,
      url: window.location.href
    }

    database.browserData.table('llmChats')
      .add(chatData)
      .catch(err => console.warn('Failed to save chat:', err))
  },

  togglePanel: function() {
    if (this.isOpen) {
      this.closePanel()
    } else {
      this.openPanel()
    }
  },

  openPanel: function() {
    const panel = document.getElementById('llmChatPanel')
    const button = document.getElementById('llmChatButton')

    if (panel) {
      panel.classList.add('open')
      this.isOpen = true
    }
    if (button) {
      button.classList.add('active')
    }

    // Focus input
    setTimeout(() => {
      document.getElementById('chatInput')?.focus()
    }, 100)
  },

  closePanel: function() {
    const panel = document.getElementById('llmChatPanel')
    const button = document.getElementById('llmChatButton')

    if (panel) {
      panel.classList.remove('open')
      this.isOpen = false
    }
    if (button) {
      button.classList.remove('active')
    }
  }
}

module.exports = llmChatPanel
