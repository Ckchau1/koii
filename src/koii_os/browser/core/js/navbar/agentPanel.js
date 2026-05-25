/**
 * agentPanel.js — AI Agent Panel (navbar button + slide-out sidebar)
 * Uses ES5-compatible syntax throughout for electron-renderify compatibility.
 */
'use strict'

var mesh = null

function getMesh () {
  if (!mesh) {
    try { mesh = require('agents/index') } catch (e) {
      console.warn('[AgentPanel] Mesh not available:', e.message)
    }
  }
  return mesh
}

function qs (panel, id) { return panel.querySelector('#' + id) }
function safeEl (id) { return document.getElementById(id) }

var agentPanel = {
  isOpen: false,
  isInitialized: false,
  _activeTaskId: null,
  _logLines: [],

  initialize: function () {
    if (this.isInitialized) return
    this.isInitialized = true
    try {
      this._createButton()
      this._createPanel()
      this._initMesh()
    } catch (e) {
      console.error('[AgentPanel] init failed:', e.message)
    }
  },

  _createButton: function () {
    var self = this
    var btn = document.createElement('button')
    btn.id = 'agentPanelButton'
    btn.className = 'navbar-action-button agent-panel-btn'
    btn.title = 'AI Agents'
    btn.setAttribute('tabindex', '-1')
    btn.innerHTML = '<span class="agent-btn-icon">&#x2B21;</span>'
    btn.onclick = function () { self.toggle() }

    var anchor = document.getElementById('llmChatButton') || document.getElementById('add-tab-button')
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(btn, anchor)
  },

  _agentDefs: [
    { id: 'SemanticUnderstandingAgent', label: 'Semantic',     icon: '&#x1F9E0;', desc: 'Intent &amp; context' },
    { id: 'OrchestrationAgent',         label: 'Orchestrator', icon: '&#x2B21;',  desc: 'Routing &amp; planning' },
    { id: 'TaskExecutionAgent',         label: 'Executor',     icon: '&#x26A1;',  desc: 'Breakdown &amp; results' },
    { id: 'AIBrowserAgent',             label: 'Browser',      icon: '&#x1F310;', desc: 'Navigation &amp; search' },
    { id: 'SelfLearningAgent',          label: 'Learner',      icon: '&#x1F4C8;', desc: 'Prompt optimization' }
  ],

  _createPanel: function () {
    var self = this
    var panel = document.createElement('div')
    panel.id = 'agentMeshPanel'

    var agentCards = this._agentDefs.map(function (a) {
      return '<div class="amp-agent-card" id="card_' + a.id + '">' +
        '<div class="amp-agent-icon">' + a.icon + '</div>' +
        '<div class="amp-agent-info">' +
          '<div class="amp-agent-name">' + a.label + '</div>' +
          '<div class="amp-agent-desc">' + a.desc + '</div>' +
        '</div>' +
        '<div class="amp-agent-status-dot idle" id="dot_' + a.id + '" title="idle"></div>' +
        '</div>'
    }).join('')

    panel.innerHTML =
      '<div class="amp-header">' +
        '<div class="amp-title"><span class="amp-icon">&#x2B21;</span> Agent Mesh</div>' +
        '<div class="amp-header-actions">' +
          '<button class="amp-icon-btn" id="ampSettingsBtn" title="LLM Settings">&#x2699;</button>' +
          '<button class="amp-icon-btn" id="ampCloseBtn" title="Close">&#x2715;</button>' +
        '</div>' +
      '</div>' +
      '<div class="amp-tabs">' +
        '<button class="amp-tab active" data-tab="agents">Agents</button>' +
        '<button class="amp-tab" data-tab="task">Task</button>' +
        '<button class="amp-tab" data-tab="log">Log</button>' +
        '<button class="amp-tab" data-tab="insights">Insights</button>' +
      '</div>' +
      '<div class="amp-tab-content active" id="ampTabAgents">' +
        '<div class="amp-agents-grid" id="ampAgentsGrid">' + agentCards + '</div>' +
        '<div class="amp-mesh-status" id="ampMeshStatus"><span class="amp-dot idle"></span> Initializing...</div>' +
      '</div>' +
      '<div class="amp-tab-content" id="ampTabTask">' +
        '<div class="amp-task-area">' +
          '<label class="amp-label">Goal</label>' +
          '<textarea id="ampGoalInput" class="amp-textarea" rows="4"' +
            ' placeholder="e.g. Summarize this page, search for X, click the Login button..."></textarea>' +
          '<div class="amp-task-options">' +
            '<label class="amp-label">Priority</label>' +
            '<select id="ampPriority" class="amp-select">' +
              '<option value="normal">Normal</option>' +
              '<option value="high">High</option>' +
              '<option value="low">Low</option>' +
            '</select>' +
          '</div>' +
          '<button id="ampRunBtn" class="amp-run-btn">&#x25B6; Run Task</button>' +
          '<button id="ampStopBtn" class="amp-run-btn amp-stop-btn" style="display:none">&#x25A0; Stop</button>' +
          '<div class="amp-task-result" id="ampTaskResult" style="display:none"></div>' +
        '</div>' +
      '</div>' +
      '<div class="amp-tab-content" id="ampTabLog">' +
        '<div class="amp-log-toolbar">' +
          '<button class="amp-icon-btn" id="ampClearLog" title="Clear">&#x1F5D1;</button>' +
          '<span id="ampLogCount" class="amp-log-count">0 events</span>' +
        '</div>' +
        '<div class="amp-log" id="ampLog"></div>' +
      '</div>' +
      '<div class="amp-tab-content" id="ampTabInsights">' +
        '<div class="amp-insights" id="ampInsights"><p class="amp-muted">Run tasks to see insights.</p></div>' +
        '<button class="amp-clear-btn" id="ampClearLearning">Clear Learning Data</button>' +
      '</div>'

    document.body.appendChild(panel)

    // Bind tabs — use panel.querySelector so we don't depend on global document indexing
    panel.querySelectorAll('.amp-tab').forEach(function (btn) {
      btn.addEventListener('click', function () {
        panel.querySelectorAll('.amp-tab').forEach(function (t) { t.classList.remove('active') })
        panel.querySelectorAll('.amp-tab-content').forEach(function (c) { c.classList.remove('active') })
        btn.classList.add('active')
        var tabId = 'ampTab' + btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1)
        var content = panel.querySelector('#' + tabId)
        if (content) content.classList.add('active')
      })
    })

    var closeBtn      = qs(panel, 'ampCloseBtn')
    var settingsBtn   = qs(panel, 'ampSettingsBtn')
    var runBtn        = qs(panel, 'ampRunBtn')
    var stopBtn       = qs(panel, 'ampStopBtn')
    var clearLogBtn   = qs(panel, 'ampClearLog')
    var clearLearnBtn = qs(panel, 'ampClearLearning')
    var goalInput     = qs(panel, 'ampGoalInput')

    if (closeBtn)      closeBtn.onclick      = function () { self.close() }
    if (settingsBtn)   settingsBtn.onclick   = function () { self._openLLMSettings() }
    if (runBtn)        runBtn.onclick        = function () { self._runTask() }
    if (stopBtn)       stopBtn.onclick       = function () { self._stopTask() }
    if (clearLogBtn)   clearLogBtn.onclick   = function () { self._clearLog() }
    if (clearLearnBtn) clearLearnBtn.onclick = function () { self._clearLearning() }
    if (goalInput) {
      goalInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) self._runTask()
      })
    }
  },

  _initMesh: function () {
    var self = this
    var m = getMesh()
    if (!m) { this._setMeshStatus('error', 'Mesh unavailable'); return }

    m.initialize().then(function () {
      self._setMeshStatus('ready', 'All agents ready')
      var bus = m.bus
      bus.subscribe('agent.status', function (e) { self._onAgentStatus(e.payload) })
      bus.subscribe('execution.step_done', function (e) {
        self._log('step', '[' + e.payload.type + '] step done')
      })
      bus.subscribe('browser_agent.step_done', function (e) {
        self._log('browse', '[browser:' + e.payload.type + '] done')
      })
      bus.subscribe('task.completed',  function (e) { self._onTaskComplete(e.payload) })
      bus.subscribe('task.error',      function (e) { self._onTaskError(e.payload) })
      bus.subscribe('workflow.planned', function (e) {
        self._log('plan', 'Planned ' + e.payload.stepCount + ' steps')
      })
      bus.subscribe('workflow.conflict', function (e) {
        self._log('warn', 'Duplicate task: ' + e.payload.taskId)
      })
      bus.subscribe('agent.clarification_needed', function (e) {
        self._showResult('&#x1F914; ' + e.payload.question, 'clarify')
      })
    }).catch(function (e) {
      self._setMeshStatus('error', 'Init failed: ' + e.message)
    })
  },

  _runTask: function () {
    var self = this
    var inputEl = safeEl('ampGoalInput')
    var input = inputEl ? inputEl.value.trim() : ''
    if (!input) return

    var m = getMesh()
    if (!m) { this._showResult('Agent Mesh not initialized.', 'error'); return }

    var llmCfg = this._tryGetLLMSettings()
    if (!llmCfg || !llmCfg.hasApiKey) {
      this._showResult('No API key — <a href="#" id="ampGoSetup">Open Settings</a>', 'warn')
      var self2 = this
      setTimeout(function () {
        var lnk = safeEl('ampGoSetup')
        if (lnk) lnk.onclick = function (e) { e.preventDefault(); self2._openLLMSettings() }
      }, 50)
      return
    }

    var runBtn  = safeEl('ampRunBtn')
    var stopBtn = safeEl('ampStopBtn')
    var resEl   = safeEl('ampTaskResult')
    if (runBtn)  runBtn.style.display  = 'none'
    if (stopBtn) stopBtn.style.display = ''
    if (resEl)   resEl.style.display   = 'none'

    this._log('submit', 'Goal: ' + input)

    var ctx = { url: this._getCurrentPageUrl(), pageTitle: document.title }
    m.submit(input, ctx).then(function (r) {
      self._activeTaskId = r.taskId
    }).catch(function (e) {
      self._onTaskError({ error: e.message })
    })
  },

  _stopTask: function () {
    this._activeTaskId = null
    var runBtn  = safeEl('ampRunBtn')
    var stopBtn = safeEl('ampStopBtn')
    if (runBtn)  runBtn.style.display  = ''
    if (stopBtn) stopBtn.style.display = 'none'
    this._log('stop', 'Stopped by user')
  },

  _onAgentStatus: function (payload) {
    var dot  = safeEl('dot_' + payload.agent)
    var card = safeEl('card_' + payload.agent)
    if (dot) { dot.className = 'amp-agent-status-dot ' + payload.status; dot.title = payload.status }
    if (card) {
      card.classList.toggle('busy', payload.status === 'busy')
      card.classList.toggle('error', payload.status === 'error')
    }
  },

  _onTaskComplete: function (payload) {
    var runBtn  = safeEl('ampRunBtn')
    var stopBtn = safeEl('ampStopBtn')
    if (runBtn)  runBtn.style.display  = ''
    if (stopBtn) stopBtn.style.display = 'none'

    var text = 'Task complete.'
    var results = payload.results
    if (Array.isArray(results)) {
      var parts = []
      results.forEach(function (r) {
        var items = Array.isArray(r) ? r : [r]
        items.forEach(function (item) {
          var s = item.summary || item.output || item.error || ''
          if (s) parts.push(s)
        })
      })
      if (parts.length) text = parts.join('\n\n')
    }
    this._showResult(text, 'ok')
    this._log('done', 'Task ' + payload.taskId + ' completed')
    this._refreshInsights()
  },

  _onTaskError: function (payload) {
    var runBtn  = safeEl('ampRunBtn')
    var stopBtn = safeEl('ampStopBtn')
    if (runBtn)  runBtn.style.display  = ''
    if (stopBtn) stopBtn.style.display = 'none'
    this._showResult('Error: ' + payload.error, 'error')
    this._log('error', payload.error)
  },

  _refreshInsights: function () {
    var m = getMesh()
    if (!m) return
    try {
      var insights = m.getAgent('SelfLearningAgent').getInsights()
      var el = safeEl('ampInsights')
      if (!el) return
      var sr = (insights.successRate * 100).toFixed(0)
      var patterns = insights.topPatterns.map(function (p) {
        return '<li><code>' + p.pattern + '</code> &times; ' + p.count + '</li>'
      }).join('')
      var intents = Object.keys(insights.intentDistribution).sort(function (a, b) {
        return insights.intentDistribution[b] - insights.intentDistribution[a]
      }).map(function (k) {
        return '<li>' + k + ': ' + insights.intentDistribution[k] + '</li>'
      }).join('')
      el.innerHTML =
        '<div class="amp-stat-row">' +
          '<div class="amp-stat"><div class="amp-stat-val">' + insights.totalTasks + '</div><div class="amp-stat-lbl">Tasks</div></div>' +
          '<div class="amp-stat"><div class="amp-stat-val">' + sr + '%</div><div class="amp-stat-lbl">Success</div></div>' +
          '<div class="amp-stat"><div class="amp-stat-val">' + insights.failureCount + '</div><div class="amp-stat-lbl">Errors</div></div>' +
        '</div>' +
        '<div class="amp-insight-section"><div class="amp-insight-title">Top Patterns</div>' +
          '<ul class="amp-insight-list">' + (patterns || '<li>None yet</li>') + '</ul></div>' +
        '<div class="amp-insight-section"><div class="amp-insight-title">Intents</div>' +
          '<ul class="amp-insight-list">' + (intents || '<li>None yet</li>') + '</ul></div>' +
        (insights.bestModel ? '<div class="amp-insight-section"><div class="amp-insight-title">Best Model</div><code>' + insights.bestModel + '</code></div>' : '')
    } catch (e) { console.warn('[AgentPanel] insights error:', e) }
  },

  _clearLearning: function () {
    if (!confirm('Clear all learning data?')) return
    var m = getMesh()
    if (m) { try { m.getAgent('SelfLearningAgent').clearAllData() } catch (e) {} }
    var el = safeEl('ampInsights')
    if (el) el.innerHTML = '<p class="amp-muted">Learning data cleared.</p>'
  },

  _log: function (type, message) {
    var entry = { type: type, message: message, ts: Date.now() }
    this._logLines.push(entry)
    if (this._logLines.length > 200) this._logLines.shift()
    var logEl = safeEl('ampLog')
    if (logEl) {
      var line = document.createElement('div')
      line.className = 'amp-log-line amp-log-' + type
      line.textContent = new Date(entry.ts).toLocaleTimeString() + ' [' + type.toUpperCase() + '] ' + message
      logEl.appendChild(line)
      logEl.scrollTop = logEl.scrollHeight
    }
    var countEl = safeEl('ampLogCount')
    if (countEl) countEl.textContent = this._logLines.length + ' events'
  },

  _clearLog: function () {
    this._logLines = []
    var logEl = safeEl('ampLog')
    if (logEl) logEl.innerHTML = ''
    var countEl = safeEl('ampLogCount')
    if (countEl) countEl.textContent = '0 events'
  },

  _setMeshStatus: function (state, message) {
    var el = safeEl('ampMeshStatus')
    if (el) el.innerHTML = '<span class="amp-dot ' + state + '"></span> ' + message
  },

  _showResult: function (html, type) {
    var el = safeEl('ampTaskResult')
    if (!el) return
    el.style.display = ''
    el.className = 'amp-task-result amp-result-' + type
    el.innerHTML = html
  },

  toggle: function () { if (this.isOpen) this.close(); else this.open() },

  open: function () {
    var panel = safeEl('agentMeshPanel')
    var btn   = safeEl('agentPanelButton')
    if (panel) panel.classList.add('open')
    if (btn)   btn.classList.add('active')
    this.isOpen = true
    this._refreshInsights()
  },

  close: function () {
    var panel = safeEl('agentMeshPanel')
    var btn   = safeEl('agentPanelButton')
    if (panel) panel.classList.remove('open')
    if (btn)   btn.classList.remove('active')
    this.isOpen = false
  },

  _openLLMSettings: function () {
    try {
      if (typeof browserUI !== 'undefined' && typeof tabs !== 'undefined') {
        browserUI.addTab(tabs.add({ url: 'min://app/pages/llmSettings/index.html' }))
        this.close()
        return
      }
    } catch (e) {}
    window.location.href = 'min://app/pages/llmSettings/index.html'
  },

  _tryGetLLMSettings: function () {
    try { return require('util/llm/llmSettings').get() } catch (e) { return null }
  },

  _getCurrentPageUrl: function () {
    try {
      if (typeof tabs !== 'undefined' && typeof webviews !== 'undefined') {
        var wv = webviews.get(tabs.getSelected())
        if (wv) return wv.getURL ? wv.getURL() : (wv.src || '')
      }
    } catch (e) {}
    return ''
  }
}

module.exports = agentPanel
