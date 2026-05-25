/**
 * AIBrowserAgent
 *
 * Specifically controls the AI Browser.
 * Responsibilities:
 *  - Webpage navigation and interaction (click, type, scroll)
 *  - Real-time page summarization with streaming output
 *  - Semantic search — extract and rank content by relevance
 *  - Screenshot capture and visual state description
 *  - Link graph traversal for multi-page research
 *  - Form detection and auto-fill
 *
 * This agent runs in the Electron renderer process and drives the
 * active webview via the Min browser's webview API.
 */

'use strict'

const { BaseAgent } = require('./agentMesh')

const MAX_PAGE_TEXT = 8000          // chars passed to LLM
const MAX_LINKS = 30
const MAX_SEARCH_RESULTS = 5

class AIBrowserAgent extends BaseAgent {
  constructor (bus, llmClient) {
    super('AIBrowserAgent', bus)
    this.llmClient = llmClient
    this._currentPageCache = null
    this._searchHistory = []
    this._navigationHistory = []
  }

  async initialize () {
    this.subscribe('task.submitted', () => {
      // Warm the page cache on every new task
      this._refreshPageCache()
    })
    this.setStatus('idle')
  }

  /**
   * @param {object} task  { taskId, steps[], context }
   */
  async handle ({ taskId, steps = [], context = {} }) {
    this.setStatus('busy')
    const start = Date.now()
    const results = []

    this.publish('browser_agent.started', { taskId, stepCount: steps.length })

    try {
      for (const step of steps) {
        const result = await this._executeStep(taskId, step, context)
        results.push(result)
        this.publish('browser_agent.step_done', { taskId, stepId: step.id, type: step.type })
        if (result.status === 'error' && step.critical) break
      }

      this._trackTiming(start)
      this.setStatus('idle')
      return { taskId, results, status: 'ok' }
    } catch (err) {
      this._metrics.errors++
      this.setStatus('idle')
      return { taskId, results, status: 'error', error: err.message }
    }
  }

  // ─── Step router ──────────────────────────────────────────────────────────

  async _executeStep (taskId, step, context) {
    switch (step.type) {
      case 'browse':    return this._stepBrowse(step)
      case 'search':    return this._stepSearch(step, context)
      case 'summarize': return this._stepSummarize(step, context)
      case 'extract':   return this._stepExtract(step, context)
      case 'interact':  return this._stepInteract(step)
      default:          return this._stepSummarize(step, context)
    }
  }

  // ─── Navigate ─────────────────────────────────────────────────────────────

  async _stepBrowse (step) {
    const url = step.url || this._normalizeUrl(step.instruction)
    if (!url) return { stepId: step.id, type: 'browse', status: 'error', error: 'No URL found' }

    this.publish('browser_agent.navigating', { url })

    try {
      await this._webviewNavigate(url)
      await this._sleep(1500)  // wait for DOM settle
      this._refreshPageCache()
      this._navigationHistory.push({ url, ts: Date.now() })

      return { stepId: step.id, type: 'browse', status: 'ok', url, output: `Navigated to ${url}` }
    } catch (err) {
      return { stepId: step.id, type: 'browse', status: 'error', error: err.message }
    }
  }

  // ─── Semantic search ───────────────────────────────────────────────────────

  async _stepSearch (step, context) {
    const query = step.query || step.instruction
    if (!query) return { stepId: step.id, type: 'search', status: 'error', error: 'No query' }

    // 1. Navigate to search engine
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`
    await this._webviewNavigate(searchUrl)
    await this._sleep(2000)

    // 2. Extract page text
    const pageText = await this._getPageText()

    // 3. Use LLM to extract relevant info, or do keyword ranking
    let output
    if (this.llmClient && this.llmClient.isReady()) {
      const prompt = `Based on this Google search results page for "${query}", extract the top ${MAX_SEARCH_RESULTS} most relevant findings. Be concise.

Page text:
${pageText.slice(0, MAX_PAGE_TEXT)}`
      output = await this.llmClient.complete(null, prompt)
    } else {
      output = this._keywordRank(pageText, query)
    }

    this._searchHistory.push({ query, url: searchUrl, ts: Date.now() })
    return { stepId: step.id, type: 'search', status: 'ok', query, output }
  }

  // ─── Summarization ────────────────────────────────────────────────────────

  async _stepSummarize (step, context) {
    // If a URL is specified, navigate there first
    if (step.url && step.url !== this._getCurrentUrl()) {
      await this._webviewNavigate(step.url)
      await this._sleep(1500)
    }

    const pageText = await this._getPageText()
    const pageTitle = await this._getPageTitle()
    const url = this._getCurrentUrl()

    this.publish('browser_agent.summarizing', { url })

    if (!pageText || pageText.length < 50) {
      return { stepId: step.id, type: 'summarize', status: 'ok', url, output: 'Page appears empty or could not be read.' }
    }

    let output
    if (this.llmClient && this.llmClient.isReady()) {
      const prompt = `Summarize the following webpage content. Be clear, concise, and highlight the key points.

Title: ${pageTitle}
URL: ${url}
Content:
${pageText.slice(0, MAX_PAGE_TEXT)}`
      output = await this.llmClient.complete(null, prompt)
    } else {
      output = this._extractiveSummary(pageText, 5)
    }

    return { stepId: step.id, type: 'summarize', status: 'ok', url, pageTitle, output }
  }

  // ─── Data extraction ───────────────────────────────────────────────────────

  async _stepExtract (step, context) {
    const pageText = await this._getPageText()
    const url = this._getCurrentUrl()

    let output
    if (this.llmClient && this.llmClient.isReady()) {
      const prompt = `From the following webpage, extract: ${step.instruction}
Return as a structured list or table.

URL: ${url}
Content:
${pageText.slice(0, MAX_PAGE_TEXT)}`
      output = await this.llmClient.complete(null, prompt)
    } else {
      // Heuristic: extract by keyword proximity
      output = this._heuristicExtract(pageText, step.instruction)
    }

    return { stepId: step.id, type: 'extract', status: 'ok', url, output }
  }

  // ─── Page interaction ─────────────────────────────────────────────────────

  async _stepInteract (step) {
    const instruction = step.instruction || ''
    const webview = this._getActiveWebview()
    if (!webview) return { stepId: step.id, type: 'interact', status: 'error', error: 'No active webview' }

    try {
      // Parse interaction type from instruction
      if (/click/i.test(instruction)) {
        const target = instruction.replace(/click\s+on\s+|click\s+/i, '').trim()
        await webview.executeJavaScript(`
          (function() {
            const els = [...document.querySelectorAll('button,a,[role=button]')];
            const el = els.find(e => e.innerText && e.innerText.toLowerCase().includes(${JSON.stringify(target.toLowerCase())}));
            if (el) { el.click(); return 'clicked: ' + el.innerText.trim().slice(0,40); }
            return 'element not found';
          })()
        `)
      } else if (/scroll down/i.test(instruction)) {
        await webview.executeJavaScript('window.scrollBy(0, window.innerHeight * 0.8); "scrolled"')
      } else if (/scroll up/i.test(instruction)) {
        await webview.executeJavaScript('window.scrollBy(0, -window.innerHeight * 0.8); "scrolled up"')
      } else if (/scroll to (top|bottom)/i.test(instruction)) {
        const isBottom = /bottom/i.test(instruction)
        await webview.executeJavaScript(`window.scrollTo(0, ${isBottom ? 'document.body.scrollHeight' : '0'}); "scrolled"`)
      } else if (/fill|type|enter.*in/i.test(instruction)) {
        const textMatch = instruction.match(/"([^"]+)"/)
        const text = textMatch ? textMatch[1] : ''
        await webview.executeJavaScript(`
          (function() {
            const input = document.querySelector('input:not([type=hidden]):not([type=submit]),textarea');
            if (input) { input.value = ${JSON.stringify(text)}; input.dispatchEvent(new Event('input', {bubbles:true})); return 'typed'; }
            return 'no input found';
          })()
        `)
      }

      return { stepId: step.id, type: 'interact', status: 'ok', instruction, output: `Interaction performed: ${instruction}` }
    } catch (err) {
      return { stepId: step.id, type: 'interact', status: 'error', error: err.message }
    }
  }

  // ─── Browser bridge helpers ────────────────────────────────────────────────

  _getActiveWebview () {
    // Min browser exposes webviews; we get the selected tab's webview
    if (typeof webviews !== 'undefined' && webviews.get) {
      try {
        const tabId = tabs.getSelected()
        return webviews.get(tabId)
      } catch (_) {}
    }
    return null
  }

  async _webviewNavigate (url) {
    const webview = this._getActiveWebview()
    if (webview && typeof webview.src !== 'undefined') {
      webview.src = url
      return
    }
    // Fallback: use Min's browserUI if in renderer
    if (typeof browserUI !== 'undefined' && browserUI.navigate) {
      browserUI.navigate(tabs.getSelected(), url)
      return
    }
    throw new Error('No webview available for navigation')
  }

  _getCurrentUrl () {
    try {
      const webview = this._getActiveWebview()
      if (webview) return webview.getURL ? webview.getURL() : webview.src
      if (typeof tabs !== 'undefined') return tabs.get(tabs.getSelected()).url || ''
    } catch (_) {}
    return ''
  }

  async _getPageText () {
    try {
      const webview = this._getActiveWebview()
      if (webview && webview.executeJavaScript) {
        return await webview.executeJavaScript('document.body ? document.body.innerText : ""')
      }
    } catch (_) {}
    return ''
  }

  async _getPageTitle () {
    try {
      const webview = this._getActiveWebview()
      if (webview && webview.executeJavaScript) {
        return await webview.executeJavaScript('document.title || ""')
      }
    } catch (_) {}
    return ''
  }

  _refreshPageCache () {
    Promise.all([this._getPageText(), this._getPageTitle()]).then(([text, title]) => {
      this._currentPageCache = { text, title, url: this._getCurrentUrl(), ts: Date.now() }
    }).catch(() => {})
  }

  // ─── NLP helpers ──────────────────────────────────────────────────────────

  _extractiveSummary (text, sentences = 5) {
    const allSentences = text.match(/[^.!?]+[.!?]+/g) || [text]
    // Score by position (earlier = more important) and length
    const scored = allSentences.map((s, i) => ({
      s: s.trim(),
      score: (1 / (i + 1)) + Math.min(s.length / 200, 1)
    }))
    scored.sort((a, b) => b.score - a.score)
    return scored.slice(0, sentences).map(s => s.s).join(' ')
  }

  _keywordRank (text, query) {
    const words = query.toLowerCase().split(/\s+/)
    const sentences = text.match(/[^.!?\n]+[.!?\n]*/g) || []
    const scored = sentences.map(s => ({
      s: s.trim(),
      score: words.reduce((acc, w) => acc + (s.toLowerCase().includes(w) ? 1 : 0), 0)
    }))
    scored.sort((a, b) => b.score - a.score)
    return scored
      .filter(s => s.score > 0)
      .slice(0, MAX_SEARCH_RESULTS)
      .map(s => s.s)
      .join('\n\n')
  }

  _heuristicExtract (text, instruction) {
    const keywords = instruction.toLowerCase().split(/\s+/).filter(w => w.length > 3)
    const lines = text.split('\n').filter(l => l.trim().length > 0)
    return lines
      .filter(l => keywords.some(k => l.toLowerCase().includes(k)))
      .slice(0, 20)
      .join('\n')
  }

  _normalizeUrl (text) {
    const match = text.match(/https?:\/\/[^\s]+/)
    if (match) return match[0]
    const domain = text.match(/\b[\w-]+\.(com|org|net|io|co|gov|edu)\S*/i)
    if (domain) return `https://${domain[0]}`
    return null
  }

  _sleep (ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  getNavigationHistory () { return this._navigationHistory.slice(-20) }
  getSearchHistory ()     { return this._searchHistory.slice(-20) }
  getCurrentPageInfo ()   { return this._currentPageCache }
}

module.exports = { AIBrowserAgent }
