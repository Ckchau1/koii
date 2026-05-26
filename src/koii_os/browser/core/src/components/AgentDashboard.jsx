import React, { useState } from 'react';
import '../styles/AgentDashboard.css';

const AGENTS = [
  {
    id: 'api-plugin',
    name: 'API Plugin Development Agent',
    icon: '🔌',
    status: 'ready',
    description: 'Dynamically creates, tests, and deploys third-party API plugins',
    capabilities: ['Code Generation', 'Automated Debugging', 'Version Control'],
  },
  {
    id: 'core-settings',
    name: 'Core Settings Agent',
    icon: '⚙️',
    status: 'ready',
    description: 'Manages kernel settings, resource allocation, and security policies',
    capabilities: ['System Config', 'Resource Mgmt', 'Security'],
  },
  {
    id: 'mode-settings',
    name: 'Mode Settings Agent',
    icon: '🎛️',
    status: 'ready',
    description: 'Switches between operating modes with semantic-driven control',
    capabilities: ['Mode Switching', 'Initiative Control', 'State Management'],
  },
  {
    id: 'task-execution',
    name: 'Task Execution Agent',
    icon: '✓',
    status: 'ready',
    description: 'Handles task breakdown, execution, and result reporting',
    capabilities: ['Task Breakdown', 'Execution', 'Reporting'],
  },
  {
    id: 'ai-browser',
    name: 'AI Browser Agent',
    icon: '🌐',
    status: 'ready',
    description: 'Controls webpage interaction, summarization, and semantic search',
    capabilities: ['Web Browsing', 'Summarization', 'Semantic Search'],
  },
  {
    id: 'orchestration',
    name: 'Orchestration Agent',
    icon: '🔀',
    status: 'ready',
    description: 'Allocates tasks and resolves conflicts among multiple agents',
    capabilities: ['Task Allocation', 'Conflict Resolution', 'Workflow Mgmt'],
  },
  {
    id: 'self-learning',
    name: 'Self-Learning Agent',
    icon: '📚',
    status: 'ready',
    description: 'Learns from usage history and optimizes decision-making',
    capabilities: ['Learning', 'Optimization', 'Improvement'],
  },
  {
    id: 'semantic-understanding',
    name: 'Semantic Understanding Agent',
    icon: '🧠',
    status: 'ready',
    description: 'Deep intent parsing and context maintenance for all agents',
    capabilities: ['Intent Parsing', 'Context Mgmt', 'Proactive Questions'],
  },
];

function AgentDashboard() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [initiativeLevel, setInitiativeLevel] = useState('balanced');
  const [operatingMode, setOperatingMode] = useState('production');

  return (
    <div className="agent-dashboard">
      <div className="dashboard-header">
        <h2>Agent System Dashboard</h2>
        <p>Semantic-driven multi-agent architecture with proactive capabilities</p>
      </div>

      <div className="dashboard-controls">
        <div className="control-group">
          <label htmlFor="initiative-level">Initiative Level:</label>
          <select
            id="initiative-level"
            value={initiativeLevel}
            onChange={(e) => setInitiativeLevel(e.target.value)}
          >
            <option value="passive">Passive</option>
            <option value="balanced">Balanced</option>
            <option value="highly-initiative">Highly Initiative</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="operating-mode">Operating Mode:</label>
          <select
            id="operating-mode"
            value={operatingMode}
            onChange={(e) => setOperatingMode(e.target.value)}
          >
            <option value="production">Production</option>
            <option value="development">Development</option>
            <option value="privacy">Privacy Mode</option>
            <option value="learning">Learning Mode</option>
          </select>
        </div>
      </div>

      <div className="agents-grid">
        {AGENTS.map(agent => (
          <div
            key={agent.id}
            className={`agent-card ${selectedAgent?.id === agent.id ? 'selected' : ''} ${agent.status}`}
            onClick={() => setSelectedAgent(agent)}
          >
            <div className="agent-icon">{agent.icon}</div>
            <h3>{agent.name}</h3>
            <p className="agent-description">{agent.description}</p>
            <div className="agent-status">
              <span className={`status-badge ${agent.status}`}>
                {agent.status === 'ready' ? '● Ready' : '● Initializing'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {selectedAgent && (
        <div className="agent-details">
          <div className="details-header">
            <h3>{selectedAgent.name}</h3>
            <button className="close-btn" onClick={() => setSelectedAgent(null)}>✕</button>
          </div>

          <div className="details-content">
            <p className="details-description">{selectedAgent.description}</p>

            <div className="capabilities-section">
              <h4>Capabilities</h4>
              <ul className="capabilities-list">
                {selectedAgent.capabilities.map(cap => (
                  <li key={cap}>✓ {cap}</li>
                ))}
              </ul>
            </div>

            <div className="agent-controls">
              <button className="control-btn activate">Activate</button>
              <button className="control-btn configure">Configure</button>
              <button className="control-btn test">Test Connection</button>
            </div>

            <div className="agent-metrics">
              <div className="metric">
                <label>Response Time</label>
                <p>~250ms avg</p>
              </div>
              <div className="metric">
                <label>Task Success Rate</label>
                <p>98.5%</p>
              </div>
              <div className="metric">
                <label>Initiative Usage</label>
                <p>{initiativeLevel}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="system-info">
        <h3>System Information</h3>
        <div className="info-grid">
          <div className="info-item">
            <label>Architecture</label>
            <p>Agent Mesh with Semantic Understanding</p>
          </div>
          <div className="info-item">
            <label>Operating Mode</label>
            <p>{operatingMode}</p>
          </div>
          <div className="info-item">
            <label>Initiative Level</label>
            <p>{initiativeLevel}</p>
          </div>
          <div className="info-item">
            <label>Total Agents</label>
            <p>{AGENTS.length}</p>
          </div>
          <div className="info-item">
            <label>Ready Agents</label>
            <p>{AGENTS.filter(a => a.status === 'ready').length}</p>
          </div>
          <div className="info-item">
            <label>State Management</label>
            <p>LSTM with Conversation Memory</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentDashboard;
