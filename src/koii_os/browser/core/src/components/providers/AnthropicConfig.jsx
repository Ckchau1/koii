import React, { useState, useEffect } from 'react';
import ProviderConfigForm from './ProviderConfigForm';

function AnthropicConfig({ config, onSave, onDelete, loading }) {
  const [formData, setFormData] = useState({
    apiKey: '',
    model: 'claude-opus-4-6',
    temperature: 0.7,
    maxTokens: 2000,
  });

  const [models] = useState([
    { id: 'claude-opus-4-6', name: 'Claude Opus 4.6 (Latest)' },
    { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6' },
    { id: 'claude-haiku-4-5', name: 'Claude Haiku 4.5' },
  ]);

  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    if (config && Object.keys(config).length > 0) {
      setFormData(config);
    }
  }, [config]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'temperature' || name === 'maxTokens' ? parseFloat(value) : value,
    }));
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await window.electronAPI.testConnection('anthropic', {
        apiKey: formData.apiKey,
        model: formData.model,
      });
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setTesting(false);
    }
  };

  const fields = [
    {
      name: 'apiKey',
      label: 'API Key',
      type: 'password',
      required: true,
      placeholder: 'sk-ant-...',
      help: 'Get your API key from https://console.anthropic.com',
    },
    {
      name: 'model',
      label: 'Model',
      type: 'select',
      required: true,
      options: models,
      help: 'Select default Claude model',
    },
    {
      name: 'temperature',
      label: 'Temperature',
      type: 'range',
      min: 0,
      max: 1,
      step: 0.1,
      required: false,
      help: 'Creativity level (0-1)',
    },
    {
      name: 'maxTokens',
      label: 'Max Tokens',
      type: 'number',
      required: false,
      placeholder: '2000',
      help: 'Maximum tokens per request',
    },
  ];

  return (
    <ProviderConfigForm
      provider="Anthropic"
      fields={fields}
      formData={formData}
      onFormChange={handleChange}
      onSave={() => onSave(formData)}
      onDelete={onDelete}
      onTest={handleTestConnection}
      testResult={testResult}
      testing={testing}
      loading={loading}
      configured={!!config && !!config.apiKey}
    />
  );
}

export default AnthropicConfig;
