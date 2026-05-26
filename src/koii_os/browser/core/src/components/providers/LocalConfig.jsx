import React, { useState, useEffect } from 'react';
import ProviderConfigForm from './ProviderConfigForm';

function LocalConfig({ config, onSave, onDelete, loading }) {
  const [formData, setFormData] = useState({
    baseUrl: 'http://localhost:11434',
    model: 'llama2',
  });

  const [models, setModels] = useState([
    { id: 'llama2', name: 'Llama 2' },
    { id: 'mistral', name: 'Mistral' },
    { id: 'neural-chat', name: 'Neural Chat' },
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
      [name]: value,
    }));
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await window.electronAPI.testConnection('local', {
        baseUrl: formData.baseUrl,
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
    if (!formData.baseUrl) {
      setTestResult({ success: false, error: 'Base URL required' });
      return;
    }

    setFetchingModels(true);
    try {
      const fetchedModels = await window.electronAPI.listModels('local', '', formData.baseUrl);
      setModels(fetchedModels);
      setTestResult({ success: true, message: `Fetched ${fetchedModels.length} available models` });
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setFetchingModels(false);
    }
  };

  const fields = [
    {
      name: 'baseUrl',
      label: 'Base URL',
      type: 'text',
      required: true,
      placeholder: 'http://localhost:11434',
      help: 'Ollama server endpoint (default: localhost:11434)',
    },
    {
      name: 'model',
      label: 'Model',
      type: 'select',
      required: true,
      options: models,
      help: 'Select default model to use',
    },
  ];

  return (
    <ProviderConfigForm
      provider="Local LLM (Ollama)"
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
      configured={!!config && !!config.baseUrl}
      info="Requires Ollama to be installed and running. Download from https://ollama.ai"
    />
  );
}

export default LocalConfig;
