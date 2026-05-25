/**
 * OrchestrationAgent
 *
 * The core of the Agent Mesh.
 * Responsibilities:
 *  - Receive structured intents from SemanticUnderstandingAgent
 *  - Build execution plans (DAG of steps)
 *  - Assign steps to the right agents
 *  - Enable parallel execution of independent steps
 *  - Detect and resolve conflicts (duplicate tasks, resource contention)
 *  - Track in-flight workflows and surface progress events
 */

'use strict'

const { BaseAgent } = require('./agentMesh')
const { INTENT_TYPES } = require('./semanticUnderstandingAgent')

// ─── Step status machine ──────────────────────────────────────────────────────
const STEP_STATUS = { PENDING: 'pending', RUNNING: 'running', DONE: 'done', FAILED: 'failed', SKIPPED: 'skipped' }

// ─── Agent routing table ──────────────────────────────────────────────────────
const STEP_ROUTING = {
  browse:    'AIBrowserAgent',
  search:    'AIBrowserAgent',
  summarize: 'AIBrowserAgent',
  extract:   'AIBrowserAgent',
  interact:  'AIBrowserAgent',
  analyze:   'TaskExecutionAgent',
  reason:    'TaskExecutionAgent',
  remember:  'TaskExecutionAgent',
  report:    'TaskExecutionAgent'
}

class OrchestrationAgent extends BaseAgent {
  constructor (bus) {
    super('OrchestrationAgent', bus)
    this._workflows = new Map()          // workflowId → WorkflowState
    this._runningTaskIds = new Set()     // prevent duplicate task submission
    this._conflictLog = []
  }

  async initialize () {
    this.subscribe('task.submitted', ({ payload }) => {
      this._checkDuplicateSubmission(payload.taskId, payload.userInput)
    })
    this.subscribe('agent.status', ({ payload }) => {
      this._handleAgentStatusChange(payload)
    })
    this.setStatus('idle')
  }

  /**
   * Convert an intent into an executable plan.
   *
   * @param {object} task  { taskId, intent, context }
   * @returns {object}     plan  { workflowId, steps[], parallelGroups[] }
   */
  async handle ({ taskId, intent, context = {} }) {
    this.setStatus('busy')
    const start = Date.now()

    const workflowId = `wf_${taskId}`

    try {
      const plan = this._buildPlan(workflowId, intent, context)
      this._workflows.set(workflowId, {
        id: workflowId,
        taskId,
        intent,
        plan,
        status: 'planned',
        startedAt: Date.now(),
        completedAt: null
      })

      this.publish('workflow.planned', { workflowId, taskId, stepCount: plan.steps.length })

      this._trackTiming(start)
      this.setStatus('idle')
      return plan
    } catch (err) {
      this._metrics.errors++
      this.setStatus('idle')
      throw err
    }
  }

  // ─── Plan builder ──────────────────────────────────────────────────────────

  _buildPlan (workflowId, intent, context) {
    if (!intent || !intent.steps || intent.steps.length === 0) {
      return this._defaultPlan(workflowId, intent)
    }

    const steps = intent.steps.map((s, idx) => ({
      id: `${workflowId}_step${idx}`,
      type: s.type || 'analyze',
      instruction: s.instruction,
      url: s.url || context.url,
      query: s.query,
      agent: STEP_ROUTING[s.type] || 'TaskExecutionAgent',
      status: STEP_STATUS.PENDING,
      dependsOn: idx > 0 ? [`${workflowId}_step${idx - 1}`] : [],
      result: null
    }))

    // Identify parallelizable groups — steps with same dependsOn set and different agents
    const parallelGroups = this._detectParallelGroups(steps)

    return {
      workflowId,
      intentType: intent.type,
      goal: intent.goal,
      steps,
      parallelGroups,
      priority: intent.priority || 'normal',
      estimatedSteps: steps.length
    }
  }

  _defaultPlan (workflowId, intent) {
    const stepType = this._inferDefaultStepType(intent)
    return {
      workflowId,
      intentType: intent ? intent.type : INTENT_TYPES.UNKNOWN,
      goal: intent ? intent.goal : 'Unknown goal',
      steps: [{
        id: `${workflowId}_step0`,
        type: stepType,
        instruction: intent ? intent.goal : '',
        agent: STEP_ROUTING[stepType] || 'TaskExecutionAgent',
        status: STEP_STATUS.PENDING,
        dependsOn: [],
        result: null
      }],
      parallelGroups: [['${workflowId}_step0']],
      priority: 'normal',
      estimatedSteps: 1
    }
  }

  _inferDefaultStepType (intent) {
    if (!intent) return 'analyze'
    switch (intent.type) {
      case INTENT_TYPES.BROWSE:    return 'browse'
      case INTENT_TYPES.SEARCH:    return 'search'
      case INTENT_TYPES.SUMMARIZE: return 'summarize'
      case INTENT_TYPES.EXTRACT:   return 'extract'
      case INTENT_TYPES.INTERACT:  return 'interact'
      default:                     return 'analyze'
    }
  }

  // ─── Parallel group detection ──────────────────────────────────────────────

  _detectParallelGroups (steps) {
    // Group steps that share the same dependency set — they can run in parallel
    const groups = new Map()
    for (const step of steps) {
      const key = step.dependsOn.sort().join(',') || '__root__'
      if (!groups.has(key)) groups.set(key, [])
      groups.get(key).push(step.id)
    }
    return [...groups.values()]
  }

  // ─── Conflict detection ────────────────────────────────────────────────────

  _checkDuplicateSubmission (taskId, userInput) {
    // Detect near-duplicate submissions within 3 seconds
    const recentInputs = [...this._runningTaskIds]
    const normalizedInput = userInput ? userInput.toLowerCase().trim() : ''

    for (const [rid, rdata] of (this._recentInputs || new Map()).entries()) {
      if (rdata.input === normalizedInput && Date.now() - rdata.ts < 3000) {
        const conflict = { taskId, duplicateOf: rid, input: userInput, ts: Date.now() }
        this._conflictLog.push(conflict)
        this.publish('workflow.conflict', conflict)
        return true
      }
    }

    if (!this._recentInputs) this._recentInputs = new Map()
    this._recentInputs.set(taskId, { input: normalizedInput, ts: Date.now() })
    if (this._recentInputs.size > 100) {
      const oldest = this._recentInputs.keys().next().value
      this._recentInputs.delete(oldest)
    }
    return false
  }

  _handleAgentStatusChange ({ agent, status }) {
    // If an agent goes into error state, re-route pending steps away from it
    if (status === 'error') {
      for (const [wfId, wf] of this._workflows) {
        if (wf.status !== 'planned') continue
        const affected = wf.plan.steps.filter(s => s.agent === agent && s.status === STEP_STATUS.PENDING)
        for (const step of affected) {
          // Fallback routing
          step.agent = agent === 'AIBrowserAgent' ? 'TaskExecutionAgent' : 'AIBrowserAgent'
          this.publish('workflow.step_rerouted', { workflowId: wfId, stepId: step.id, newAgent: step.agent })
        }
      }
    }
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  getWorkflow (workflowId) {
    return this._workflows.get(workflowId) || null
  }

  getActiveWorkflows () {
    return [...this._workflows.values()].filter(w => w.status === 'planned' || w.status === 'running')
  }

  getConflictLog () {
    return this._conflictLog.slice()
  }

  markWorkflowComplete (workflowId) {
    const wf = this._workflows.get(workflowId)
    if (wf) {
      wf.status = 'completed'
      wf.completedAt = Date.now()
    }
  }
}

module.exports = { OrchestrationAgent, STEP_STATUS, STEP_ROUTING }
