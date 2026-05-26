import React, { useState, useEffect } from 'react';
import OpenAIConfig from './providers/OpenAIConfig';
import AnthropicConfig from './providers/AnthropicConfig';
import LocalConfig from './providers/LocalConfig';
import CustomConfig from './providers/CustomConfig';
import '../styles/LLMSettingsPanel.css';

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', icon: '🔵' },
  { id: 'anthropic', name: 'Anthropic', icon: '🟣' },
  { id: 'local', name: 'Local (Ollama)', icon: '💻' },
  { id: 'custom', name: 'Custom Provider', icon: '🔧' },
];

function LLMSettingsPanel() {
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [configs, setConfigs] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const allConfigs = await window.electronAPI.getConfigs();
      setConfigs(allConfigs);
      setError(null);
    } catch (err) {
      console.error('Failed to load configs:', err);
      setError('Failed to load configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (provider, config) => {
    try {
      setLoading(true);
      await window.electronAPI.saveConfig(provider, config);
      setConfigs(prev => ({ ...prev, [provider]: config }));
      setSuccessMessage(`${provider} configuration saved successfully!`);
      setTimeout(() => setSuccessMessage(null), 3000);
      setError(null);
    } catch (err) {
      console.error('Failed to save config:', err);
      setError(`Failed to save ${provider} configuration`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfig = async (provider) => {
    if (window.confirm(`Are you sure you want to delete ${provider} configuration?`)) {
      try {
        setLoading(true);
        await window.electronAPI.deleteConfig(provider);
        setConfigs(prev => {
          const updated = { ...prev };
          delete updated[provider];
          return updated;
        });
        setSuccessMessage(`${provider} configuration deleted`);
        setTimeout(() => setSuccessMessage(null), 3000);
        setError(null);
      } catch (err) {
        console.error('Failed to delete config:', err);
        setError(`Failed to delete ${provider} configuration`);
      } finally {
        setLoading(false);
      }
    }
  };

  const renderProviderConfig = () => {
    const currentConfig = configs[selectedProvider] || {};

    switch (selectedProvider) {
      case 'openai':
        return (
          <OpenAIConfig
            config={currentConfig}
            onSave={(config) => handleSaveConfig('openai', config)}
            onDelete={() => handleDeleteConfig('openai')}
            loading={loading}
          />
        );
      case 'anthropic':
        return (
          <AnthropicConfig
            config={currentConfig}
            onSave={(config) => handleSaveConfig('anthropic', config)}
            onDelete={() => handleDeleteConfig('anthropic')}
            loading={loading}
          />
        );
      case 'local':
        return (
          <LocalConfig
            config={currentConfig}
            onSave={(config) => handleSaveConfig('local', config)}
            onDelete={() => handleDeleteConfig('local')}
            loading={loading}
          />
        );
      case 'custom':
        return (
          <CustomConfig
            config={currentConfig}
            onSave={(config) => handleSaveConfig('custom', config)}
            onDelete={() => handleDeleteConfig('custom')}
            loading={loading}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="llm-settings-panel">
      <div className="settings-container">
        <div className="settings-header">
          <h2>LLM Configuration</h2>
          <p>Configure API keys, models, and endpoints for your AI agents</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {successMessage && <div className="alert alert-success">{successMessage}</div>}

        <div className="settings-layout">
          {/* Provider Selection */}
          <div className="provider-selector">
            <h3>Providers</h3>
            <div className="provider-list">
              {PROVIDERS.map(provider => (
                <button
                  key={provider.id}
                  className={`provider-button ${selectedProvider === provider.id ? 'active' : ''} ${configs[provider.id] ? 'configured' : ''}`}
                  onClick={() => setSelectedProvider(provider.id)}
                  disabled={loading}
                >
                  <span className="provider-icon">{provider.icon}</span>
                  <span className="provider-name">{provider.name}</span>
                  {configs[provider.id] && <span className="configured-badge">✓</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Configuration Form */}
          <div className="config-panel">
            {loading && !successMessage ? (
              <div className="loading-spinner">
                <p>Loading...</p>
              </div>
            ) : (
              renderProviderConfig()
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="settings-stats">
          <div className="stat-card">
            <h4>Configured Providers</h4>
            <p className="stat-value">{Object.keys(configs).length} / {PROVIDERS.length}</p>
          </div>
          <div className="stat-card">
            <h4>Active Provider</h4>
            <p className="stat-value">
              {PROVIDERS.find(p => p.id === selectedProvider)?.name || 'None'}
            </p>
          </div>
          <div className="stat-card">
            <h4>Status</h4>
            <p className="stat-value">
              {configs[selectedProvider] ? '✓ Configured' : '⚠ Not Configured'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LLMSettingsPanel;
