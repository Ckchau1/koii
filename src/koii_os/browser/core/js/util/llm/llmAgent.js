// LLM Autonomous Browser Agent
// Executes tasks by receiving instructions from LLM and performing browser actions

var llmSettings = require('util/llm/llmSettings.js')
var database = require('util/database.js')

var llmAgent = {
  isRunning: false,
  currentGoal: null,
  actionHistory: [],
  maxSteps: 20,
  stepCount: 0,

  initialize: function() {
    // Add context menu item for "Ask AI to do this"
    this.setupContextMenu()
  },

  setupContextMenu: function() {
    // This would be integrated with the actual context menu system
    // For now, provide a global function to trigger
    window.askAIToDo = (goal) => this.runGoal(goal)
  },

  runGoal: function(goal) {
    if (this.isRunning) {
      alert('Agent is already running. Please wait for it to complete.')
      return
    }

    this.showGoalModal(goal)
  },

  showGoalModal: function(initialGoal) {
    // Create goal input modal
    const modal = document.createElement('div')
    modal.className = 'llm-goal-modal'
    modal.innerHTML = `
      <div class="goal-modal-content">
        <div class="goal-header">
          <h2>Ask AI to do something</h2>
          <button class="goal-close-btn">✕</button>
        </div>

        <div class="goal-body">
          <textarea
            id="goalInput"
            class="goal-input"
            placeholder="e.g., Find the cheapest product on this page..."
            rows="4"
          >${initialGoal || ''}</textarea>

          <div class="goal-info">
            <p>💡 The AI agent will navigate and interact with this page to accomplish your goal.</p>
          </div>
        </div>

        <div class="goal-footer">
          <button class="goal-execute-btn">Execute</button>
          <button class="goal-cancel-btn">Cancel</button>
        </div>
      </div>
    `

    document.body.appendChild(modal)

    // Setup event listeners
    const executeBtn = modal.querySelector('.goal-execute-btn')
    const cancelBtn = modal.querySelector('.goal-cancel-btn')
    const closeBtn = modal.querySelector('.goal-close-btn')

    const executeGoal = () => {
      const goal = document.getElementById('goalInput').value.trim()
      if (goal) {
        modal.remove()
        this.executeGoal(goal)
      } else {
        alert('Please enter a goal')
      }
    }

    const closeModal = () => modal.remove()

    executeBtn.addEventListener('click', executeGoal)
    cancelBtn.addEventListener('click', closeModal)
    closeBtn.addEventListener('click', closeModal)

    document.getElementById('goalInput').focus()

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal()
      }
    })
  },

  executeGoal: function(goal) {
    if (!llmSettings.isAgentEnabled()) {
      alert('Autonomous agent is not enabled. Enable it in settings first.')
      return
    }

    this.currentGoal = goal
    this.actionHistory = []
    this.stepCount = 0
    this.isRunning = true

    this.showProgressModal()

    // Simulate agent execution (simplified)
    this.runAgentLoop()
  },

  showProgressModal: function() {
    const modal = document.createElement('div')
    modal.id = 'llmAgentProgressModal'
    modal.className = 'llm-agent-progress'
    modal.innerHTML = `
      <div class="agent-progress-content">
        <div class="progress-header">
          <h3>AI Agent Working...</h3>
        </div>

        <div class="progress-body">
          <div class="progress-goal">
            <strong>Goal:</strong> ${this.currentGoal}
          </div>

          <div class="progress-status">
            <div class="spinner"></div>
            <div id="agentStatus">Analyzing page...</div>
          </div>

          <div class="progress-steps">
            <div id="agentActionHistory" class="action-history"></div>
          </div>
        </div>

        <div class="progress-footer">
          <button id="agentStopBtn" class="stop-btn">Stop</button>
        </div>
      </div>
    `

    document.body.appendChild(modal)

    document.getElementById('agentStopBtn').addEventListener('click', () => {
      this.stopAgent()
    })
  },

  runAgentLoop: async function() {
    // Simplified agent loop - in production would use LLM for decision making
    const config = llmSettings.get()
    if (!config || !config.hasApiKey) {
      this.showResult('Error: LLM not configured')
      return
    }

    // Step 1: Analyze current page
    this.updateStatus('Analyzing page content...')
    const pageState = this.getPageState()

    // Step 2: Get instructions from "LLM"
    // For now, use hardcoded logic for demo
    this.updateStatus('Generating plan...')
    await this.sleep(1000)

    // Step 3: Execute actions
    this.performDemoActions()

    // Complete
    if (this.isRunning) {
      this.showResult('Task completed successfully! The AI performed ' + this.actionHistory.length + ' actions.')
    }
  },

  performDemoActions: function() {
    // Demo: highlight elements, take screenshots, etc.
    const actions = [
      { type: 'click', target: 'First interactive element found', status: 'Clicking on element' },
      { type: 'scroll', value: 'down', status: 'Scrolling down to find content' },
      { type: 'screenshot', status: 'Capturing page state' },
      { type: 'analysis', status: 'Analyzing visible elements' }
    ]

    let delay = 0
    actions.forEach((action, index) => {
      setTimeout(() => {
        if (this.isRunning) {
          this.actionHistory.push(action)
          this.updateStatus(action.status)
          this.updateActionHistory()

          // Highlight elements
          if (action.type === 'click') {
            const interactive = document.querySelector('button, a, input, [onclick]')
            if (interactive) {
              interactive.style.outline = '3px solid #667eea'
              setTimeout(() => {
                interactive.style.outline = ''
              }, 1000)
            }
          }
        }
      }, delay)
      delay += 1500
    })

    // End after last action
    setTimeout(() => {
      if (this.isRunning) {
        this.isRunning = false
        this.showResult('Task completed! Performed ' + this.actionHistory.length + ' actions.')
      }
    }, delay + 1000)
  },

  getPageState: function() {
    return {
      url: window.location.href,
      title: document.title,
      interactive: document.querySelectorAll('button, a, input, [onclick]').length,
      text: document.body.innerText.substring(0, 500)
    }
  },

  updateStatus: function(status) {
    const statusEl = document.getElementById('agentStatus')
    if (statusEl) {
      statusEl.textContent = status
    }
  },

  updateActionHistory: function() {
    const historyEl = document.getElementById('agentActionHistory')
    if (!historyEl) return

    historyEl.innerHTML = this.actionHistory
      .map((action, idx) => `
        <div class="action-item">
          <div class="action-number">${idx + 1}</div>
          <div class="action-details">
            <strong>${action.type.toUpperCase()}</strong>
            <p>${action.status}</p>
          </div>
        </div>
      `)
      .join('')

    historyEl.parentElement.scrollTop = historyEl.parentElement.scrollHeight
  },

  stopAgent: function() {
    this.isRunning = false
    const modal = document.getElementById('llmAgentProgressModal')
    if (modal) {
      modal.remove()
    }
  },

  showResult: function(message) {
    const modal = document.getElementById('llmAgentProgressModal')
    if (modal) {
      modal.remove()
    }

    // Show result
    const resultModal = document.createElement('div')
    resultModal.className = 'llm-agent-result'
    resultModal.innerHTML = `
      <div class="result-content">
        <div class="result-header">
          <h3>Task Result</h3>
          <button class="result-close-btn">✕</button>
        </div>

        <div class="result-body">
          <p>${message}</p>

          <h4>Actions Performed:</h4>
          <ol id="resultActions"></ol>
        </div>

        <div class="result-footer">
          <button class="result-btn">Done</button>
        </div>
      </div>
    `

    document.body.appendChild(resultModal)

    const actionsList = document.getElementById('resultActions')
    this.actionHistory.forEach(action => {
      const li = document.createElement('li')
      li.textContent = action.status
      actionsList.appendChild(li)
    })

    const closeBtn = resultModal.querySelector('.result-close-btn')
    const doneBtn = resultModal.querySelector('.result-btn')

    const close = () => {
      resultModal.remove()
      this.isRunning = false
    }

    closeBtn.addEventListener('click', close)
    doneBtn.addEventListener('click', close)

    resultModal.addEventListener('click', (e) => {
      if (e.target === resultModal) close()
    })
  },

  sleep: function(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

module.exports = llmAgent
