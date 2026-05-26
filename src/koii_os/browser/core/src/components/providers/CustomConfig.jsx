import React, { useState, useEffect } from 'react';
import ProviderConfigForm from './ProviderConfigForm';

function CustomConfig({ config, onSave, onDelete, loading }) {
  const [formData, setFormData] = useState({
    baseUrl: '',
    apiKey: '',
    model: '',
    customPath: '/api/chat',
    customHeaders: {},
  });

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
      [name]: value,
    }));
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await window.electronAPI.testConnection('custom', {
        baseUrl: formData.baseUrl,
        apiKey: formData.apiKey,
        model: formData.model,
        customPath: formData.customPath,
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
      name: 'baseUrl',
      label: 'Base URL',
      type: 'text',
      required: true,
      placeholder: 'https://api.example.com',
      help: 'Your custom LLM API endpoint',
    },
    {
      name: 'apiKey',
      label: 'API Key (Optional)',
      type: 'password',
      required: false,
      placeholder: 'Your API key if required',
      help: 'Leave blank if authentication not needed',
    },
    {
      name: 'model',
      label: 'Model Name',
      type: 'text',
      required: false,
      placeholder: 'e.g., my-model-v1',
      help: 'Default model to use',
    },
    {
      name: 'customPath',
      label: 'API Path',
      type: 'text',
      required: false,
      placeholder: '/api/chat',
      help: 'Endpoint path for API calls',
    },
  ];

  return (
    <ProviderConfigForm
      provider="Custom Provider"
      fields={fields}
      formData={formData}
      onFormChange={handleChange}
      onSave={() => onSave(formData)}
      onDelete={onDelete}
      onTest={handleTestConnection}
      testResult={testResult}
      testing={testing}
      loading={loading}
      configured={!!config && !!config.baseUrl}
      info="Configure a custom LLM provider with your own API endpoint"
    />
  );
}

export default CustomConfig;
