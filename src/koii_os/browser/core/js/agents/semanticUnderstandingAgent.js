/**
 * SemanticUnderstandingAgent
 *
 * The "brain" of the Agent Mesh.
 * Responsibilities:
 *  - Deep intent parsing from natural language
 *  - Proactive clarification question generation
 *  - Short-term & long-term context maintenance
 *  - Entity extraction (URLs, names, dates, actions)
 *  - Ambiguity detection and resolution
 */

'use strict'

const { BaseAgent } = require('./agentMesh')

// Intent category taxonomy
const INTENT_TYPES = {
  BROWSE:       'browse',        // navigate to a URL / open a page
  SEARCH:       'search',        // web search for information
  SUMMARIZE:    'summarize',     // summarize current page or URL
  EXTRACT:      'extract',       // extract specific data from page
  INTERACT:     'interact',      // click / fill / submit form elements
  ANALYZE:      'analyze',       // deep analysis, comparison, research
  REMEMBER:     'remember',      // save/recall something
  SCHEDULE:     'schedule',      // schedule a task / reminder
  CONVERSE:     'converse',      // general conversation / Q&A
  MULTI:        'multi',         // multiple intents combined
  UNKNOWN:      'unknown'
}

// Context window: last N messages kept per session
const CONTEXT_WINDOW = 20

class SemanticUnderstandingAgent extends BaseAgent {
  constructor (bus, llmClient) {
    super('SemanticUnderstandingAgent', bus)
    this.llmClient = llmClient   // may be null (fallback to heuristic)
    this._context = []           // conversation context
    this._entities = new Map()   // remembered entities across turns
    this._clarificationPending = null
  }

  async initialize () {
    this.subscribe('task.submitted', ({ payload }) => {
      this._maintainContext(payload.userInput, 'user')
    })
    this.subscribe('task.completed', ({ payload }) => {
      this._maintainContext(JSON.stringify(payload.results).slice(0, 200), 'assistant')
    })
    this.setStatus('idle')
  }

  /**
   * Main handler — parse a user message into a structured intent object.
   *
   * @param {object} task  { taskId, userInput, context }
   * @returns {object}     intent
   */
  async handle ({ taskId, userInput, context = {} }) {
    this.setStatus('busy')
    const start = Date.now()

    try {
      let intent

      if (this.llmClient && this.llmClient.isReady()) {
        intent = await this._parseWithLLM(userInput, context)
      } else {
        intent = this._parseHeuristic(userInput, context)
      }

      // Enrich with extracted entities
      intent.entities = this._extractEntities(userInput)
      intent.contextSnapshot = this.getContext()
      intent.ambiguous = this._detectAmbiguity(intent)

      if (intent.ambiguous && intent.clarificationQuestion) {
        this.publish('agent.clarification_needed', {
          taskId,
          question: intent.clarificationQuestion,
          intent
        })
      }

      // Persist new entities
      this._mergeEntities(intent.entities)

      this._trackTiming(start)
      this.setStatus('idle')
      return intent
    } catch (err) {
      this._metrics.errors++
      this.setStatus('error')
      this.setStatus('idle')
      return { type: INTENT_TYPES.UNKNOWN, raw: userInput, error: err.message }
    }
  }

  // ── LLM-based parsing ──────────────────────────────────────────────────────

  async _parseWithLLM (userInput, context) {
    const systemPrompt = `You are an intent parser for an AI browser assistant.
Given a user message, return a JSON object with:
{
  "type": one of ${JSON.stringify(Object.values(INTENT_TYPES))},
  "goal": concise summary of what the user wants,
  "steps": [{ "type": "browse"|"search"|"summarize"|"extract"|"interact"|"analyze", "instruction": "..." }],
  "entities": { "urls": [], "queries": [], "subjects": [] },
  "priority": "high"|"normal"|"low",
  "ambiguous": false,
  "clarificationQuestion": null
}
Current page: ${context.url || 'unknown'}
Page title: ${context.pageTitle || ''}
Conversation context: ${this._context.slice(-4).map(m => `${m.role}: ${m.content}`).join('\n')}
Respond with ONLY the JSON object.`

    const response = await this.llmClient.complete(systemPrompt, userInput)
    return this._safeParseJSON(response, userInput)
  }

  // ── Heuristic fallback ─────────────────────────────────────────────────────

  _parseHeuristic (userInput, context) {
    const lower = userInput.toLowerCase().trim()

    // URL detection
    const urlMatch = userInput.match(/https?:\/\/[^\s]+/)
    if (urlMatch || lower.startsWith('go to') || lower.startsWith('open ') || lower.startsWith('navigate to')) {
      const url = urlMatch ? urlMatch[0] : this._extractBareUrl(userInput)
      return {
        type: INTENT_TYPES.BROWSE,
        goal: `Navigate to ${url || userInput}`,
        steps: [{ type: 'browse', instruction: userInput, url }],
        priority: 'normal'
      }
    }

    // Summarization
    if (/summar|tldr|brief|overview|what('s| is) (this|the) page/i.test(lower)) {
      return {
        type: INTENT_TYPES.SUMMARIZE,
        goal: 'Summarize the current page',
        steps: [{ type: 'summarize', instruction: userInput, url: context.url }],
        priority: 'normal'
      }
    }

    // Search
    if (/search|find|look up|google|lookup|who is|what is|how (to|do)|when (did|is)/i.test(lower)) {
      const query = userInput.replace(/^(search for|find|look up|google)\s*/i, '').trim()
      return {
        type: INTENT_TYPES.SEARCH,
        goal: `Search for: ${query}`,
        steps: [{ type: 'search', instruction: userInput, query }],
        priority: 'normal'
      }
    }

    // Extraction
    if (/extract|get all|scrape|collect|list all|grab/i.test(lower)) {
      return {
        type: INTENT_TYPES.EXTRACT,
        goal: `Extract data: ${userInput}`,
        steps: [{ type: 'extract', instruction: userInput, url: context.url }],
        priority: 'normal'
      }
    }

    // Interaction
    if (/click|press|fill|submit|type|select|toggle|scroll/i.test(lower)) {
      return {
        type: INTENT_TYPES.INTERACT,
        goal: `Interact with page: ${userInput}`,
        steps: [{ type: 'interact', instruction: userInput, url: context.url }],
        priority: 'high'
      }
    }

    // Analysis
    if (/analyz|compar|research|review|evaluat|assess/i.test(lower)) {
      return {
        type: INTENT_TYPES.ANALYZE,
        goal: `Analyze: ${userInput}`,
        steps: [
          { type: 'search', instruction: `Search for information about: ${userInput}` },
          { type: 'analyze', instruction: userInput }
        ],
        priority: 'normal'
      }
    }

    // Default — treat as a conversational or general task
    return {
      type: INTENT_TYPES.CONVERSE,
      goal: userInput,
      steps: [{ type: 'analyze', instruction: userInput }],
      priority: 'normal'
    }
  }

  // ── Entity extraction ──────────────────────────────────────────────────────

  _extractEntities (text) {
    const entities = { urls: [], queries: [], subjects: [], dates: [] }

    // URLs
    const urlMatches = text.match(/https?:\/\/[^\s]+/g) || []
    entities.urls = urlMatches

    // Bare domain names
    const domainMatches = text.match(/\b[\w-]+\.(com|org|net|io|co|gov|edu)\b/g) || []
    entities.urls.push(...domainMatches.filter(d => !entities.urls.includes(d)))

    // Quoted strings — likely specific subjects
    const quoted = text.match(/"([^"]+)"|'([^']+)'/g) || []
    entities.subjects = quoted.map(q => q.replace(/['"]/g, ''))

    // Dates
    const dateMatches = text.match(/\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b|\b(today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/gi) || []
    entities.dates = dateMatches

    return entities
  }

  _extractBareUrl (text) {
    const words = text.split(/\s+/)
    for (const w of words) {
      if (w.includes('.') && !w.startsWith('.') && !w.endsWith('.')) {
        return w.startsWith('http') ? w : `https://${w}`
      }
    }
    return null
  }

  _detectAmbiguity (intent) {
    if (intent.type === INTENT_TYPES.UNKNOWN) return true
    if (intent.type === INTENT_TYPES.CONVERSE && intent.goal && intent.goal.length < 10) return true
    return false
  }

  _mergeEntities (entities) {
    for (const [key, values] of Object.entries(entities)) {
      if (Array.isArray(values)) {
        const existing = this._entities.get(key) || []
        this._entities.set(key, [...new Set([...existing, ...values])])
      }
    }
  }

  // ── Context maintenance ────────────────────────────────────────────────────

  _maintainContext (content, role) {
    this._context.push({ role, content, ts: Date.now() })
    if (this._context.length > CONTEXT_WINDOW) {
      this._context.shift()
    }
  }

  getContext () {
    return this._context.slice()
  }

  getEntities () {
    return Object.fromEntries(this._entities)
  }

  clearContext () {
    this._context = []
    this._entities.clear()
    this.publish('agent.context_cleared', { agent: this.name })
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  _safeParseJSON (raw, fallback) {
    try {
      let clean = raw.trim()
      if (clean.startsWith('```')) {
        const lines = clean.split('\n')
        clean = lines.slice(1, lines.length - 1).join('\n')
      }
      return JSON.parse(clean)
    } catch (_) {
      const match = raw.match(/\{[\s\S]+\}/)
      if (match) {
        try { return JSON.parse(match[0]) } catch (_2) {}
      }
      return this._parseHeuristic(fallback, {})
    }
  }
}

module.exports = { SemanticUnderstandingAgent, INTENT_TYPES }
