import React, { useState, useEffect } from 'react';
import ProviderConfigForm from './ProviderConfigForm';

function OpenAIConfig({ config, onSave, onDelete, loading }) {
  const [formData, setFormData] = useState({
    apiKey: '',
    model: 'gpt-4o',
    baseUrl: 'https://api.openai.com/v1',
    temperature: 0.7,
    maxTokens: 2000,
  });

  const [models, setModels] = useState([
    { id: 'gpt-4o', name: 'GPT-4o' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  ]);

  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [fetchingModels, setFetchingModels] = useState(false);

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
      const result = await window.electronAPI.testConnection('openai', {
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

  const handleFetchModels = async () => {
    if (!formData.apiKey) {
      setTestResult({ success: false, error: 'API Key required to fetch models' });
      return;
    }

    setFetchingModels(true);
    try {
      const fetchedModels = await window.electronAPI.listModels('openai', formData.apiKey);
      setModels(fetchedModels.slice(0, 20)); // Limit to 20 models
      setTestResult({ success: true, message: `Fetched ${fetchedModels.length} available models` });
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setFetchingModels(false);
    }
  };

  const fields = [
    {
      name: 'apiKey',
      label: 'API Key',
      type: 'password',
      required: true,
      placeholder: 'sk-...',
      help: 'Get your API key from https://platform.openai.com/account/api-keys',
    },
    {
      name: 'baseUrl',
      label: 'Base URL',
      type: 'text',
      required: false,
      placeholder: 'https://api.openai.com/v1',
      help: 'Default OpenAI API endpoint',
    },
    {
      name: 'model',
      label: 'Model',
      type: 'select',
      required: true,
      options: models,
      help: 'Select default model for requests',
    },
    {
      name: 'temperature',
      label: 'Temperature',
      type: 'range',
      min: 0,
      max: 2,
      step: 0.1,
      required: false,
      help: 'Creativity level (0-2)',
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
      provider="OpenAI"
      fields={fields}
      formData={formData}
      onFormChange={handleChange}
      onSave={() => onSave(formData)}
      onDelete={onDelete}
      onTest={handleTestConnection}
      onFetchModels={handleFetchModels}
      testResult={testResult}
      testing={testing}
      fetchingModels={fetchingModels}
      loading={loading}
      configured={!!config && !!config.apiKey}
    />
  );
}

export default OpenAIConfig;
