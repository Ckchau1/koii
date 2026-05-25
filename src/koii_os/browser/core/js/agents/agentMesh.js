/**
 * AgentMesh — Central orchestration hub for all AIOS browser agents.
 *
 * Architecture:
 *   AgentMesh
 *   ├── SemanticUnderstandingAgent  (intent parsing, context, "brain")
 *   ├── OrchestrationAgent          (task routing, parallel execution, conflict resolution)
 *   ├── TaskExecutionAgent          (breakdown, execution, result reporting)
 *   ├── AIBrowserAgent              (navigation, summarization, semantic search)
 *   └── SelfLearningAgent           (usage history, prompt optimization, model improvement)
 *
 * All inter-agent communication goes through the mesh event bus.
 * Agents never call each other directly — they emit events and subscribe to results.
 */

'use strict'

const EventEmitter = require('events')

// ─── Event Bus ───────────────────────────────────────────────────────────────

class AgentEventBus extends EventEmitter {
  constructor () {
    super()
    this.setMaxListeners(50)
    this._history = []
  }

  publish (topic, payload, source) {
    const event = {
      id: `evt_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      topic,
      payload,
      source,
      ts: Date.now()
    }
    this._history.push(event)
    if (this._history.length > 500) this._history.shift()
    this.emit(topic, event)
    this.emit('*', event)
    return event.id
  }

  subscribe (topic, handler) {
    this.on(topic, handler)
    return () => this.off(topic, handler)
  }

  getHistory (topic, limit = 50) {
    const filtered = topic
      ? this._history.filter(e => e.topic === topic)
      : this._history
    return filtered.slice(-limit)
  }
}

// ─── Base Agent ───────────────────────────────────────────────────────────────

class BaseAgent {
  constructor (name, bus) {
    this.name = name
    this.bus = bus
    this.status = 'idle'   // idle | busy | error | paused
    this.enabled = true
    this._taskQueue = []
    this._currentTask = null
    this._metrics = { handled: 0, errors: 0, avgMs: 0 }
  }

  publish (topic, payload) {
    return this.bus.publish(topic, payload, this.name)
  }

  subscribe (topic, handler) {
    return this.bus.subscribe(topic, handler.bind(this))
  }

  setStatus (s) {
    this.status = s
    this.publish('agent.status', { agent: this.name, status: s })
  }

  getMetrics () {
    return { ...this._metrics, status: this.status, enabled: this.enabled }
  }

  _trackTiming (start) {
    const ms = Date.now() - start
    const n = this._metrics.handled
    this._metrics.avgMs = Math.round((this._metrics.avgMs * n + ms) / (n + 1))
    this._metrics.handled++
  }

  // Override in subclasses
  async handle (task) { throw new Error(`${this.name}.handle() not implemented`) }

  async initialize () {}
  async shutdown () {}
}

// ─── AgentMesh ────────────────────────────────────────────────────────────────

class AgentMesh {
  constructor () {
    this.bus = new AgentEventBus()
    this.agents = new Map()
    this._initialized = false
    this._taskRegistry = new Map()   // taskId → { task, status, results }
    this._sessionId = `session_${Date.now()}`
  }

  register (agent) {
    if (!(agent instanceof BaseAgent)) {
      throw new TypeError(`Expected BaseAgent, got ${typeof agent}`)
    }
    agent.bus = this.bus
    this.agents.set(agent.name, agent)
    return this
  }

  getAgent (name) {
    const agent = this.agents.get(name)
    if (!agent) throw new Error(`Agent '${name}' not registered`)
    return agent
  }

  async initialize () {
    if (this._initialized) return
    for (const [name, agent] of this.agents) {
      try {
        await agent.initialize()
        console.log(`[AgentMesh] ${name} initialized`)
      } catch (err) {
        console.error(`[AgentMesh] Failed to init ${name}:`, err)
      }
    }
    this._initialized = true
    this.bus.publish('mesh.ready', { sessionId: this._sessionId, agents: [...this.agents.keys()] }, 'AgentMesh')
  }

  async shutdown () {
    for (const [, agent] of this.agents) {
      try { await agent.shutdown() } catch (_) {}
    }
    this._initialized = false
  }

  /**
   * Primary entry point — submit a user request to the mesh.
   * The SemanticUnderstandingAgent parses intent, then OrchestrationAgent routes.
   *
   * @param {string} userInput
   * @param {object} context  — { url, pageText, pageTitle, ... }
   * @returns {Promise<object>}
   */
  async submit (userInput, context = {}) {
    const taskId = `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`

    const record = {
      id: taskId,
      input: userInput,
      context,
      status: 'submitted',
      createdAt: Date.now(),
      steps: [],
      result: null
    }
    this._taskRegistry.set(taskId, record)

    this.bus.publish('task.submitted', { taskId, userInput, context }, 'AgentMesh')

    try {
      // 1. Semantic understanding
      const semantic = this.getAgent('SemanticUnderstandingAgent')
      const intent = await semantic.handle({ taskId, userInput, context })
      record.steps.push({ agent: 'SemanticUnderstandingAgent', result: intent })

      // 2. Orchestration
      const orchestrator = this.getAgent('OrchestrationAgent')
      const plan = await orchestrator.handle({ taskId, intent, context })
      record.steps.push({ agent: 'OrchestrationAgent', result: plan })

      // 3. Execute plan steps (may involve TaskExecution + AIBrowser in parallel)
      const results = await this._executePlan(taskId, plan, context)
      record.steps.push({ agent: 'Execution', result: results })

      // 4. Self-learning: record this interaction
      const learner = this.getAgent('SelfLearningAgent')
      learner.handle({ taskId, userInput, intent, plan, results }).catch(() => {})

      record.status = 'completed'
      record.result = results
      this.bus.publish('task.completed', { taskId, results }, 'AgentMesh')
      return { taskId, status: 'completed', results }
    } catch (err) {
      record.status = 'error'
      record.error = err.message
      this.bus.publish('task.error', { taskId, error: err.message }, 'AgentMesh')
      return { taskId, status: 'error', error: err.message }
    }
  }

  async _executePlan (taskId, plan, context) {
    const taskAgent = this.getAgent('TaskExecutionAgent')
    const browserAgent = this.getAgent('AIBrowserAgent')

    if (!plan || !plan.steps || plan.steps.length === 0) {
      return taskAgent.handle({ taskId, steps: [], context })
    }

    // Partition steps — browser steps go to AIBrowserAgent, rest to TaskExecutionAgent
    const browserSteps = plan.steps.filter(s => s.type === 'browse' || s.type === 'search' || s.type === 'summarize')
    const execSteps = plan.steps.filter(s => !browserSteps.includes(s))

    const promises = []
    if (browserSteps.length > 0) {
      promises.push(browserAgent.handle({ taskId, steps: browserSteps, context }))
    }
    if (execSteps.length > 0) {
      promises.push(taskAgent.handle({ taskId, steps: execSteps, context }))
    }

    const settled = await Promise.allSettled(promises)
    return settled.map(r => r.status === 'fulfilled' ? r.value : { error: r.reason?.message })
  }

  getTask (taskId) {
    return this._taskRegistry.get(taskId) || null
  }

  getStatus () {
    const agentStatuses = {}
    for (const [name, agent] of this.agents) {
      agentStatuses[name] = agent.getMetrics()
    }
    return {
      sessionId: this._sessionId,
      initialized: this._initialized,
      agents: agentStatuses,
      taskCount: this._taskRegistry.size
    }
  }
}

module.exports = { AgentMesh, AgentEventBus, BaseAgent }
