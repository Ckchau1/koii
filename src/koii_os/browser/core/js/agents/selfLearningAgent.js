/**
 * SelfLearningAgent
 *
 * Automatically learns from usage history to improve long-term performance.
 * Responsibilities:
 *  - Record every completed task interaction (input, intent, steps, outcome)
 *  - Identify patterns: common queries, frequent errors, preferred phrasings
 *  - Optimize prompts: store successful prompt patterns, surface them to other agents
 *  - Score model performance: track which LLM settings produce best results
 *  - Suggest improvements to the user (periodic digest)
 *  - Prune stale patterns automatically
 */

'use strict'

const { BaseAgent } = require('./agentMesh')

const DB_KEY_HISTORY    = 'aios_sla_history'
const DB_KEY_PATTERNS   = 'aios_sla_patterns'
const DB_KEY_PROMPT_OPT = 'aios_sla_prompt_opts'
const DB_KEY_SCORES     = 'aios_sla_model_scores'

const MAX_HISTORY   = 500
const MAX_PATTERNS  = 100
const PRUNE_AFTER_DAYS = 30

class SelfLearningAgent extends BaseAgent {
  constructor (bus) {
    super('SelfLearningAgent', bus)
    this._history    = []          // interaction records
    this._patterns   = new Map()   // pattern key → { count, successRate, examples }
    this._promptOpts = new Map()   // intentType → best prompt template
    this._modelScores= new Map()   // modelId → { score, samples }
    this._dirty      = false
    this._flushTimer = null
  }

  async initialize () {
    this._loadFromStorage()
    this._startPeriodicFlush()

    this.subscribe('task.completed', ({ payload }) => {
      const record = this._findHistoryRecord(payload.taskId)
      if (record) this._markSuccess(record)
    })

    this.subscribe('task.error', ({ payload }) => {
      const record = this._findHistoryRecord(payload.taskId)
      if (record) this._markFailure(record, payload.error)
    })

    this.setStatus('idle')
  }

  async shutdown () {
    this._flushToStorage()
    if (this._flushTimer) clearInterval(this._flushTimer)
  }

  /**
   * Record an interaction and update all learning models.
   *
   * @param {object} task  { taskId, userInput, intent, plan, results }
   */
  async handle ({ taskId, userInput, intent, plan, results }) {
    const start = Date.now()
    this.setStatus('busy')

    const record = {
      id: taskId,
      userInput,
      intentType: intent ? intent.type : 'unknown',
      goal: intent ? intent.goal : '',
      stepCount: plan ? (plan.steps || []).length : 0,
      success: null,   // filled in by task.completed / task.error subscriptions
      ts: Date.now(),
      durationMs: null
    }

    this._history.push(record)
    if (this._history.length > MAX_HISTORY) this._history.shift()

    // Update pattern index
    this._updatePatterns(record)

    // Score the model used (if results contain model metadata)
    if (results && Array.isArray(results)) {
      for (const r of results) {
        if (r.modelId && r.status === 'ok') {
          this._updateModelScore(r.modelId, true)
        }
      }
    }

    this._dirty = true
    this._trackTiming(start)
    this.setStatus('idle')
    return { status: 'ok', recorded: taskId }
  }

  // ─── Pattern learning ──────────────────────────────────────────────────────

  _updatePatterns (record) {
    const keys = this._extractPatternKeys(record.userInput)
    for (const key of keys) {
      if (!this._patterns.has(key)) {
        this._patterns.set(key, { key, count: 0, successes: 0, examples: [], lastSeen: 0 })
      }
      const p = this._patterns.get(key)
      p.count++
      p.lastSeen = Date.now()
      if (p.examples.length < 3) p.examples.push(record.userInput)
    }

    // Prune to max
    if (this._patterns.size > MAX_PATTERNS) {
      // Remove least-seen patterns
      const sorted = [...this._patterns.entries()].sort((a, b) => a[1].count - b[1].count)
      for (let i = 0; i < sorted.length - MAX_PATTERNS; i++) {
        this._patterns.delete(sorted[i][0])
      }
    }
  }

  _extractPatternKeys (text) {
    if (!text) return []
    const lower = text.toLowerCase()
    const keys = []

    // Intent prefix keywords
    const prefixes = ['search for', 'find', 'open', 'go to', 'summarize', 'click', 'extract', 'analyze', 'what is', 'how to']
    for (const p of prefixes) {
      if (lower.startsWith(p)) keys.push(p)
    }

    // Domain keywords
    const domains = lower.match(/\b[\w-]+\.(com|org|net|io)\b/g) || []
    keys.push(...domains)

    // First 3 words as a fingerprint
    const fingerprint = lower.split(/\s+/).slice(0, 3).join(' ')
    if (fingerprint.length > 5) keys.push(fingerprint)

    return keys
  }

  // ─── Prompt optimization ───────────────────────────────────────────────────

  /**
   * Get the best known prompt template for an intent type.
   * If none recorded yet, returns null (agents use their built-in prompts).
   */
  getOptimizedPrompt (intentType) {
    return this._promptOpts.get(intentType) || null
  }

  recordPromptOutcome (intentType, promptTemplate, success) {
    const key = intentType
    const existing = this._promptOpts.get(key)
    if (!existing) {
      this._promptOpts.set(key, { template: promptTemplate, score: success ? 1 : 0, trials: 1 })
    } else {
      existing.trials++
      existing.score = (existing.score * (existing.trials - 1) + (success ? 1 : 0)) / existing.trials
      // Only promote if new template is significantly better
      if (success && existing.score < 0.5) {
        existing.template = promptTemplate
      }
    }
    this._dirty = true
  }

  // ─── Model scoring ─────────────────────────────────────────────────────────

  _updateModelScore (modelId, success) {
    if (!this._modelScores.has(modelId)) {
      this._modelScores.set(modelId, { score: 0, samples: 0 })
    }
    const m = this._modelScores.get(modelId)
    m.score = (m.score * m.samples + (success ? 1 : 0)) / (m.samples + 1)
    m.samples++
  }

  getBestModel () {
    if (this._modelScores.size === 0) return null
    let best = null, bestScore = -1
    for (const [modelId, data] of this._modelScores) {
      if (data.samples >= 3 && data.score > bestScore) {
        bestScore = data.score
        best = modelId
      }
    }
    return best
  }

  getModelScores () {
    return Object.fromEntries(this._modelScores)
  }

  // ─── Usage insights ────────────────────────────────────────────────────────

  getInsights () {
    const total = this._history.length
    const successes = this._history.filter(r => r.success === true).length
    const failures  = this._history.filter(r => r.success === false).length

    // Top patterns
    const topPatterns = [...this._patterns.values()]
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)
      .map(p => ({ pattern: p.key, count: p.count, successRate: p.successes / (p.count || 1) }))

    // Intent distribution
    const intentDist = {}
    for (const r of this._history) {
      intentDist[r.intentType] = (intentDist[r.intentType] || 0) + 1
    }

    return {
      totalTasks: total,
      successRate: total > 0 ? (successes / total) : 0,
      failureCount: failures,
      topPatterns,
      intentDistribution: intentDist,
      bestModel: this.getBestModel(),
      modelScores: this.getModelScores()
    }
  }

  // ─── Record helpers ────────────────────────────────────────────────────────

  _findHistoryRecord (taskId) {
    return this._history.find(r => r.id === taskId) || null
  }

  _markSuccess (record) {
    record.success = true
    record.durationMs = Date.now() - record.ts
    const keys = this._extractPatternKeys(record.userInput)
    for (const key of keys) {
      const p = this._patterns.get(key)
      if (p) p.successes++
    }
    this._dirty = true
  }

  _markFailure (record, error) {
    record.success = false
    record.error = error
    record.durationMs = Date.now() - record.ts
    this._dirty = true
  }

  // ─── Persistence ───────────────────────────────────────────────────────────

  _loadFromStorage () {
    try {
      const raw = localStorage.getItem(DB_KEY_HISTORY)
      if (raw) this._history = JSON.parse(raw)
    } catch (_) {}

    try {
      const raw = localStorage.getItem(DB_KEY_PATTERNS)
      if (raw) this._patterns = new Map(JSON.parse(raw))
    } catch (_) {}

    try {
      const raw = localStorage.getItem(DB_KEY_PROMPT_OPT)
      if (raw) this._promptOpts = new Map(JSON.parse(raw))
    } catch (_) {}

    try {
      const raw = localStorage.getItem(DB_KEY_SCORES)
      if (raw) this._modelScores = new Map(JSON.parse(raw))
    } catch (_) {}

    this._pruneOldData()
  }

  _flushToStorage () {
    if (!this._dirty) return
    try {
      localStorage.setItem(DB_KEY_HISTORY,    JSON.stringify(this._history))
      localStorage.setItem(DB_KEY_PATTERNS,   JSON.stringify([...this._patterns.entries()]))
      localStorage.setItem(DB_KEY_PROMPT_OPT, JSON.stringify([...this._promptOpts.entries()]))
      localStorage.setItem(DB_KEY_SCORES,     JSON.stringify([...this._modelScores.entries()]))
      this._dirty = false
    } catch (err) {
      console.warn('[SelfLearningAgent] Could not flush to storage:', err)
    }
  }

  _startPeriodicFlush () {
    this._flushTimer = setInterval(() => this._flushToStorage(), 30_000)
  }

  _pruneOldData () {
    const cutoff = Date.now() - PRUNE_AFTER_DAYS * 24 * 3600 * 1000
    this._history = this._history.filter(r => r.ts > cutoff)
    for (const [key, p] of this._patterns) {
      if (p.lastSeen < cutoff) this._patterns.delete(key)
    }
  }

  clearAllData () {
    this._history = []
    this._patterns.clear()
    this._promptOpts.clear()
    this._modelScores.clear()
    try {
      localStorage.removeItem(DB_KEY_HISTORY)
      localStorage.removeItem(DB_KEY_PATTERNS)
      localStorage.removeItem(DB_KEY_PROMPT_OPT)
      localStorage.removeItem(DB_KEY_SCORES)
    } catch (_) {}
    this.publish('agent.data_cleared', { agent: this.name })
  }
}

module.exports = { SelfLearningAgent }
