// Content Analyzer - Auto-analyzes page content when enabled
const llmSettings = require('util/llm/llmSettings.js')
const llmClient = require('util/llm/llmClient.js')
const database = require('util/database.js')

var contentAnalyzer = {
  isInitialized: false,
  analysisCache: {},
  ignoredDomains: [],

  initialize: function() {
    if (this.isInitialized) return
    this.isInitialized = true

    // Only initialize if analysis is enabled
    if (!llmSettings.isAnalysisEnabled()) {
      return
    }

    // Load ignored domains from settings
    const config = llmSettings.get()
    this.ignoredDomains = config.ignoredDomainsForAnalysis || []

    // Initialize database
    this.initializeDatabase()

    // Listen for page loads
    window.addEventListener('load', () => {
      this.onPageLoad()
    })

    // Also analyze if page already loaded
    if (document.readyState === 'complete') {
      setTimeout(() => this.onPageLoad(), 500)
    }
  },

  initializeDatabase: function() {
    if (!database.browserData) return

    database.browserData.table('llmAnalysis').toArray().then(analyses => {
      // Cache loaded
      analyses.forEach(analysis => {
        this.analysisCache[analysis.url] = analysis
      })
    }).catch(err => {
      console.warn('LLM analysis table not available:', err)
    })
  },

  onPageLoad: function() {
    const url = window.location.href
    const domain = new URL(url).hostname

    // Check if this domain is ignored
    if (this.ignoredDomains.includes(domain)) {
      return
    }

    // Check if we already have analysis for this URL
    if (this.analysisCache[url]) {
      this.showAnalysisBadge(this.analysisCache[url])
      return
    }

    // Don't analyze special pages
    if (url.startsWith('min://') || url.startsWith('about:') || url.startsWith('chrome://')) {
      return
    }

    // Analyze page content
    setTimeout(() => {
      this.analyzePageContent(url)
    }, 2000) // Wait 2 seconds for page to fully load
  },

  analyzePageContent: function(url) {
    const content = this.extractPageContent()

    if (!content || content.length < 100) {
      // Page has too little content to analyze
      return
    }

    // Create analysis prompt
    const prompt = `Analyze the following webpage content and provide a brief analysis:

Title: ${document.title}
URL: ${url}

Content excerpt:
${content.substring(0, 2000)}

Please provide:
1. A 2-3 sentence summary
2. Key topics (comma-separated)
3. Sentiment (positive/neutral/negative)
4. Content type (article/product/documentation/forum/other)

Format your response as JSON with keys: summary, topics, sentiment, contentType`

    // Get LLM config
    const config = llmSettings.get()
    if (!config || !config.hasApiKey) {
      return
    }

    // Make analysis request
    const electron = window.electron
    if (!electron || !electron.ipcRenderer) {
      return
    }

    // For now, create a placeholder analysis
    // In the full implementation, we'd call the LLM
    const analysis = {
      url: url,
      title: document.title,
      timestamp: Date.now(),
      summary: 'Page analysis pending...',
      topics: ['content'],
      sentiment: 'neutral',
      contentType: 'webpage',
      processed: false
    }

    // Store in cache and database
    this.analysisCache[url] = analysis
    this.saveAnalysisToDB(analysis)
    this.showAnalysisBadge(analysis)
  },

  extractPageContent: function() {
    // Use Readability if available to get clean content
    try {
      // Try to get text from main content areas
      const selectors = ['main', 'article', '[role="main"]', '.content', '#content']

      for (let selector of selectors) {
        const el = document.querySelector(selector)
        if (el) {
          const text = el.innerText
          if (text && text.length > 100) {
            return text
          }
        }
      }

      // Fall back to body text
      return document.body.innerText
    } catch (e) {
      console.error('Failed to extract page content:', e)
      return document.body.innerText || ''
    }
  },

  saveAnalysisToDB: function(analysis) {
    if (!database.browserData) return

    database.browserData.table('llmAnalysis')
      .add(analysis)
      .catch(err => {
        // Try to update if it already exists
        if (err.name === 'ConstraintError') {
          database.browserData.table('llmAnalysis')
            .update(analysis.url, analysis)
            .catch(e => console.warn('Failed to save analysis:', e))
        }
      })
  },

  showAnalysisBadge: function(analysis) {
    // Don't show if already displayed
    if (document.getElementById('llmAnalysisBadge')) {
      return
    }

    // Create badge element
    const badge = document.createElement('div')
    badge.id = 'llmAnalysisBadge'
    badge.className = 'llm-analysis-badge'
    badge.title = 'AI analysis available - click to view'

    const icon = document.createElement('span')
    icon.className = 'analysis-icon'
    icon.textContent = '📊'

    badge.appendChild(icon)

    badge.addEventListener('click', (e) => {
      e.stopPropagation()
      this.showAnalysisModal(analysis)
    })

    // Insert at top of page
    if (document.body) {
      document.body.insertBefore(badge, document.body.firstChild)
    }
  },

  showAnalysisModal: function(analysis) {
    // Create modal to display analysis
    const modal = document.createElement('div')
    modal.className = 'llm-analysis-modal'
    modal.innerHTML = `
      <div class="analysis-modal-content">
        <div class="analysis-header">
          <h3>Page Analysis</h3>
          <button class="analysis-close-btn">✕</button>
        </div>

        <div class="analysis-body">
          <div class="analysis-section">
            <h4>Summary</h4>
            <p>${analysis.summary || 'Analysis pending...'}</p>
          </div>

          <div class="analysis-section">
            <h4>Topics</h4>
            <div class="analysis-tags">
              ${(analysis.topics || [])
                .map(topic => `<span class="analysis-tag">${topic}</span>`)
                .join('')
              }
            </div>
          </div>

          <div class="analysis-section">
            <h4>Metadata</h4>
            <dl>
              <dt>Sentiment:</dt>
              <dd>${analysis.sentiment || 'neutral'}</dd>
              <dt>Content Type:</dt>
              <dd>${analysis.contentType || 'webpage'}</dd>
              <dt>Analyzed:</dt>
              <dd>${new Date(analysis.timestamp).toLocaleDateString()}</dd>
            </dl>
          </div>
        </div>

        <div class="analysis-footer">
          <button class="analysis-action-btn">Add to Chat</button>
          <button class="analysis-close-btn">Close</button>
        </div>
      </div>
    `

    document.body.appendChild(modal)

    // Setup event listeners
    const closeBtns = modal.querySelectorAll('.analysis-close-btn')
    closeBtns.forEach(btn => {
      btn.addEventListener('click', () => modal.remove())
    })

    const addToChatBtn = modal.querySelector('.analysis-action-btn')
    addToChatBtn?.addEventListener('click', () => {
      this.addAnalysisToChat(analysis)
      modal.remove()
    })

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove()
      }
    })
  },

  addAnalysisToChat: function(analysis) {
    // Add analysis to chat panel
    const analysisMessage = `Based on the page analysis:
- Summary: ${analysis.summary}
- Topics: ${(analysis.topics || []).join(', ')}
- Sentiment: ${analysis.sentiment}

How can I help you with this?`

    // Send to chat panel via IPC or event
    if (window.llmChatPanel) {
      window.llmChatPanel.currentMessages.push({
        role: 'system',
        content: analysisMessage
      })
      window.llmChatPanel.renderMessages()
      window.llmChatPanel.openPanel()
    }
  },

  ignoreCurrentDomain: function() {
    const domain = new URL(window.location.href).hostname
    this.ignoredDomains.push(domain)

    // Save to settings
    const config = llmSettings.get()
    config.ignoredDomainsForAnalysis = this.ignoredDomains
    llmSettings.set('ignoredDomainsForAnalysis', this.ignoredDomains)

    // Remove badge
    const badge = document.getElementById('llmAnalysisBadge')
    if (badge) badge.remove()
  }
}

module.exports = contentAnalyzer
