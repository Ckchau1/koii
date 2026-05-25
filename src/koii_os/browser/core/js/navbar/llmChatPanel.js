// LLM Chat Panel - Slide-out chat sidebar for interacting with LLM
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

    // Always create the chat button and panel - show setup prompt if no API key
    this.createChatButton()
    this.createChatPanel()
    this.setupEventListeners()

    // Initialize database (best effort)
    this.initializeDatabase()
  },

  initializeDatabase: function() {
    database.browserData.table('llmChats').toArray().then(chats => {
      // Database ready for chat storage
    }).catch(err => {
      console.warn('LLM chats table not available:', err)
    })
  },

  createChatButton: function() {
    const chatButton = document.createElement('button')
    chatButton.id = 'llmChatButton'
    chatButton.className = 'navbar-action-button'
    chatButton.title = 'Chat with AI'
    chatButton.setAttribute('tabindex', '-1')
    chatButton.innerHTML = '<span style="font-size:16px">&#x1F4AC;</span>'

    chatButton.addEventListener('click', function(e) {
      e.stopPropagation()
      llmChatPanel.togglePanel()
    })

    // Insert AFTER add-tab button (between + and ≡ menu button)
    var addTabButton = document.getElementById('add-tab-button')
    if (addTabButton && addTabButton.parentNode) {
      addTabButton.parentNode.insertBefore(chatButton, addTabButton.nextSibling)
    } else {
      var navbar = document.getElementById('navbar')
      if (navbar) navbar.appendChild(chatButton)
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
    var self = this
    // Listen for LLM config changes
    llmSettings.listen('hasApiKey', function(hasKey) {
      // keep panel open even without key so user can see the setup message
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

    var self = this
    var electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      this.addSystemMessage('Error: Cannot connect to LLM service.')
      this.isLoading = false
      this.setStatus('')
      return
    }

    electron.ipcRenderer.invoke('chatWithLLM', {
      messages: self.currentMessages
    }).then(function(result) {
      if (!result.success) {
        self.addSystemMessage(result.error || 'LLM request failed.')
      } else {
        self.currentMessages.push({ role: 'assistant', content: result.content })
        self.renderMessages()
        self.scrollToBottom()
        self.saveChatHistory()
      }
      self.isLoading = false
      self.setStatus('')
    }).catch(function(err) {
      self.addSystemMessage('Error: ' + err.message)
      self.isLoading = false
      self.setStatus('')
    })
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
