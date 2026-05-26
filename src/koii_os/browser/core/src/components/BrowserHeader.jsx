import React from 'react';
import '../styles/BrowserHeader.css';

function BrowserHeader({ activeTab, onTabChange }) {
  return (
    <div className="browser-header">
      {/* Logo and Branding */}
      <div className="header-brand">
        <div className="logo-container">
          <svg className="logo-icon" viewBox="0 0 40 40" width="28" height="28">
            <defs>
              <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#9d4edd" />
                <stop offset="100%" stopColor="#7209b7" />
              </linearGradient>
            </defs>
            <circle cx="20" cy="20" r="18" fill="url(#logoGradient)" opacity="0.9" />
            <text x="20" y="24" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold" fontFamily="Arial">K</text>
          </svg>
        </div>
        <span className="brand-text">Koii OS Browser</span>
      </div>

      {/* Navigation Tabs */}
      <nav className="header-nav">
        <button
          className={`nav-tab ${activeTab === 'browser' ? 'active' : ''}`}
          onClick={() => onTabChange('browser')}
        >
          <span className="nav-icon">🌐</span>
          Browser
        </button>
        <button
          className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => onTabChange('chat')}
        >
          <span className="nav-icon">💬</span>
          Chat
        </button>
        <button
          className={`nav-tab ${activeTab === 'agents' ? 'active' : ''}`}
          onClick={() => onTabChange('agents')}
        >
          <span className="nav-icon">🤖</span>
          Agents
        </button>
        <button
          className={`nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => onTabChange('settings')}
        >
          <span className="nav-icon">⚙️</span>
          Settings
        </button>
      </nav>

      {/* Header Actions */}
      <div className="header-actions">
        <button className="action-btn" title="Open in window">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
            <polyline points="13 2 13 9 20 9" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default BrowserHeader;
