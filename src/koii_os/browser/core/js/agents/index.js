/**
 * agents/index.js
 *
 * Assembles the full Agent Mesh and exposes a singleton instance
 * for use anywhere in the Min browser renderer process.
 *
 * Usage (renderer):
 *   const mesh = require('agents/index')
 *   await mesh.initialize()
 *   const result = await mesh.submit('Summarize this page', { url: location.href })
 */

'use strict'

const { AgentMesh }                                   = require('./agentMesh')
const { SemanticUnderstandingAgent }                  = require('./semanticUnderstandingAgent')
const { OrchestrationAgent }                          = require('./orchestrationAgent')
const { TaskExecutionAgent }                          = require('./taskExecutionAgent')
const { AIBrowserAgent }                              = require('./aiBrowserAgent')
const { SelfLearningAgent }                           = require('./selfLearningAgent')

// LLM client adapter — wraps llmSettings + llmClient from the existing util layer
let llmClientAdapter = null

function buildLLMClientAdapter () {
  try {
    const llmSettings = require('util/llm/llmSettings')
    const llmClient   = require('util/llm/llmClient')

    return {
      isReady () {
        const cfg = llmSettings.get()
        return !!(cfg && cfg.hasApiKey)
      },
      async complete (systemPrompt, userPrompt) {
        return llmClient.complete({ systemPrompt, userPrompt })
      }
    }
  } catch (err) {
    console.warn('[AgentMesh] LLM client not available:', err.message)
    return { isReady: () => false, complete: async () => '' }
  }
}

// ─── Singleton assembly ────────────────────────────────────────────────────

function buildMesh () {
  llmClientAdapter = buildLLMClientAdapter()

  const mesh = new AgentMesh()

  mesh.register(new SemanticUnderstandingAgent(mesh.bus, llmClientAdapter))
  mesh.register(new OrchestrationAgent(mesh.bus))
  mesh.register(new TaskExecutionAgent(mesh.bus, llmClientAdapter))
  mesh.register(new AIBrowserAgent(mesh.bus, llmClientAdapter))
  mesh.register(new SelfLearningAgent(mesh.bus))

  return mesh
}

let _instance = null

function getInstance () {
  if (!_instance) _instance = buildMesh()
  return _instance
}

// Expose singleton mesh
module.exports = getInstance()

// Also export classes for testing / custom instantiation
module.exports.AgentMesh                  = AgentMesh
module.exports.SemanticUnderstandingAgent = SemanticUnderstandingAgent
module.exports.OrchestrationAgent         = OrchestrationAgent
module.exports.TaskExecutionAgent         = TaskExecutionAgent
module.exports.AIBrowserAgent             = AIBrowserAgent
module.exports.SelfLearningAgent          = SelfLearningAgent
module.exports.buildMesh                  = buildMesh
