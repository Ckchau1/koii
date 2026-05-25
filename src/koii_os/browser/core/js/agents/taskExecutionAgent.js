/**
 * TaskExecutionAgent
 *
 * The most frequently invoked agent.
 * Responsibilities:
 *  - Break complex tasks into atomic sub-steps
 *  - Execute non-browser steps (reasoning, analysis, memory, reporting)
 *  - Aggregate and synthesize results from multiple steps
 *  - Emit granular progress events for UI feedback
 *  - Handle retries, timeouts, and graceful degradation
 */

'use strict'

const { BaseAgent } = require('./agentMesh')

const MAX_RETRIES = 2
const STEP_TIMEOUT_MS = 30_000

class TaskExecutionAgent extends BaseAgent {
  constructor (bus, llmClient) {
    super('TaskExecutionAgent', bus)
    this.llmClient = llmClient
    this._activeSteps = new Map()   // stepId → { promise, startedAt }
    this._resultCache = new Map()   // cacheKey → result (TTL 5 min)
    this._TTL = 5 * 60 * 1000
  }

  async initialize () {
    this.subscribe('task.submitted', () => {})  // warming hook
    this.setStatus('idle')
  }

  /**
   * @param {object} task  { taskId, steps[], context }
   * @returns {object}     { taskId, results[], summary }
   */
  async handle ({ taskId, steps = [], context = {} }) {
    this.setStatus('busy')
    const start = Date.now()

    this.publish('execution.started', { taskId, stepCount: steps.length })

    const results = []

    try {
      for (const step of steps) {
        const result = await this._executeStepWithRetry(taskId, step, context)
        results.push(result)

        this.publish('execution.step_done', {
          taskId,
          stepId: step.id,
          type: step.type,
          status: result.status
        })

        // Short-circuit on fatal error if step was critical
        if (result.status === 'error' && step.critical) {
          break
        }
      }

      const summary = await this._synthesizeResults(results, context)

      this.publish('execution.completed', { taskId, stepCount: results.length, summary })
      this._trackTiming(start)
      this.setStatus('idle')
      return { taskId, results, summary, status: 'ok' }
    } catch (err) {
      this._metrics.errors++
      this.publish('execution.error', { taskId, error: err.message })
      this.setStatus('idle')
      return { taskId, results, status: 'error', error: err.message }
    }
  }

  // ─── Step execution ────────────────────────────────────────────────────────

  async _executeStepWithRetry (taskId, step, context, attempt = 0) {
    const cacheKey = `${step.type}:${step.instruction}`
    const cached = this._getCached(cacheKey)
    if (cached) return { ...cached, fromCache: true }

    try {
      const result = await Promise.race([
        this._executeStep(taskId, step, context),
        this._timeout(STEP_TIMEOUT_MS, `Step '${step.type}' timed out`)
      ])

      this._setCache(cacheKey, result)
      return result
    } catch (err) {
      if (attempt < MAX_RETRIES) {
        await this._sleep(500 * (attempt + 1))
        return this._executeStepWithRetry(taskId, step, context, attempt + 1)
      }
      return { stepId: step.id, type: step.type, status: 'error', error: err.message }
    }
  }

  async _executeStep (taskId, step, context) {
    const type = step.type || 'analyze'

    switch (type) {
      case 'analyze':
        return this._stepAnalyze(step, context)
      case 'reason':
        return this._stepReason(step, context)
      case 'remember':
        return this._stepRemember(step, context)
      case 'report':
        return this._stepReport(step, context)
      case 'decompose':
        return this._stepDecompose(step, context)
      default:
        return this._stepGeneric(step, context)
    }
  }

  // ─── Individual step handlers ──────────────────────────────────────────────

  async _stepAnalyze (step, context) {
    if (this.llmClient && this.llmClient.isReady()) {
      const prompt = `Analyze the following task and provide a clear, concise answer.
Context URL: ${context.url || 'none'}
Page title: ${context.pageTitle || ''}
Page text (excerpt): ${(context.pageText || '').slice(0, 1000)}

Task: ${step.instruction}`

      const output = await this.llmClient.complete(null, prompt)
      return { stepId: step.id, type: 'analyze', status: 'ok', output }
    }

    // Heuristic fallback
    return {
      stepId: step.id,
      type: 'analyze',
      status: 'ok',
      output: `[Analysis] Task: "${step.instruction}". Context: ${context.url || 'no URL'}. (LLM not configured — enable in Settings for full analysis.)`,
      heuristic: true
    }
  }

  async _stepReason (step, context) {
    if (this.llmClient && this.llmClient.isReady()) {
      const prompt = `Think step-by-step to reason about: ${step.instruction}
Context: ${context.url || ''}
Provide your reasoning and final conclusion.`
      const output = await this.llmClient.complete(null, prompt)
      return { stepId: step.id, type: 'reason', status: 'ok', output }
    }

    return {
      stepId: step.id,
      type: 'reason',
      status: 'ok',
      output: `[Reasoning] "${step.instruction}" — LLM required for full reasoning.`,
      heuristic: true
    }
  }

  async _stepRemember (step, context) {
    // Persist to localStorage (available in renderer)
    try {
      const memories = JSON.parse(localStorage.getItem('aios_memories') || '[]')
      memories.push({
        content: step.instruction,
        url: context.url,
        ts: Date.now()
      })
      if (memories.length > 200) memories.shift()
      localStorage.setItem('aios_memories', JSON.stringify(memories))
      return { stepId: step.id, type: 'remember', status: 'ok', output: 'Saved to memory.' }
    } catch (err) {
      return { stepId: step.id, type: 'remember', status: 'error', error: err.message }
    }
  }

  async _stepReport (step, context) {
    // Build a markdown report from prior step results
    const output = `## Task Report\n\n**Goal:** ${step.instruction}\n\n**Page:** ${context.url || 'N/A'}\n\n**Completed at:** ${new Date().toLocaleString()}\n`
    return { stepId: step.id, type: 'report', status: 'ok', output }
  }

  async _stepDecompose (step, context) {
    // Break a complex instruction into sub-steps
    const subSteps = step.instruction
      .split(/\band\b|\bthen\b|,\s*/i)
      .map(s => s.trim())
      .filter(Boolean)
      .map((s, i) => ({ id: `${step.id}_sub${i}`, type: 'analyze', instruction: s }))

    return { stepId: step.id, type: 'decompose', status: 'ok', subSteps }
  }

  async _stepGeneric (step, context) {
    return { stepId: step.id, type: step.type, status: 'ok', output: `Executed: ${step.instruction}` }
  }

  // ─── Result synthesis ──────────────────────────────────────────────────────

  async _synthesizeResults (results, context) {
    const successful = results.filter(r => r.status === 'ok')
    const outputs = successful.map(r => r.output || r.subSteps).filter(Boolean)

    if (outputs.length === 0) return 'No results to synthesize.'

    if (this.llmClient && this.llmClient.isReady() && outputs.length > 1) {
      const prompt = `Synthesize these results into a clear, concise summary:
${outputs.map((o, i) => `Result ${i + 1}: ${typeof o === 'string' ? o.slice(0, 500) : JSON.stringify(o).slice(0, 500)}`).join('\n\n')}`
      return this.llmClient.complete(null, prompt)
    }

    return outputs.join('\n\n')
  }

  // ─── Cache helpers ─────────────────────────────────────────────────────────

  _getCached (key) {
    const entry = this._resultCache.get(key)
    if (!entry) return null
    if (Date.now() - entry.ts > this._TTL) {
      this._resultCache.delete(key)
      return null
    }
    return entry.value
  }

  _setCache (key, value) {
    this._resultCache.set(key, { value, ts: Date.now() })
    if (this._resultCache.size > 200) {
      const oldest = this._resultCache.keys().next().value
      this._resultCache.delete(oldest)
    }
  }

  clearCache () {
    this._resultCache.clear()
  }

  // ─── Utilities ─────────────────────────────────────────────────────────────

  _timeout (ms, message) {
    return new Promise((_, reject) => setTimeout(() => reject(new Error(message)), ms))
  }

  _sleep (ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

module.exports = { TaskExecutionAgent }
