import React from 'react';
import '../styles/ProviderConfigForm.css';

function ProviderConfigForm({
  provider,
  fields,
  formData,
  onFormChange,
  onSave,
  onDelete,
  onTest,
  onFetchModels,
  testResult,
  testing,
  fetchingModels,
  loading,
  configured,
  info,
}) {
  return (
    <div className="provider-config-form">
      <div className="form-header">
        <h3>{provider} Configuration</h3>
        {configured && <span className="configured-badge">Configured</span>}
      </div>

      {info && <div className="info-box">{info}</div>}

      <form className="config-form">
        {fields.map(field => (
          <div key={field.name} className="form-group">
            <label htmlFor={field.name}>
              {field.label}
              {field.required && <span className="required">*</span>}
            </label>

            {field.type === 'select' ? (
              <select
                id={field.name}
                name={field.name}
                value={formData[field.name] || ''}
                onChange={onFormChange}
                disabled={loading}
                required={field.required}
              >
                <option value="">Select {field.label}</option>
                {field.options?.map(option => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </select>
            ) : field.type === 'range' ? (
              <div className="range-group">
                <input
                  type="range"
                  id={field.name}
                  name={field.name}
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={formData[field.name] || 0}
                  onChange={onFormChange}
                  disabled={loading}
                />
                <span className="range-value">{formData[field.name]?.toFixed(1)}</span>
              </div>
            ) : (
              <input
                type={field.type}
                id={field.name}
                name={field.name}
                placeholder={field.placeholder}
                value={formData[field.name] || ''}
                onChange={onFormChange}
                disabled={loading}
                required={field.required}
              />
            )}

            {field.help && <p className="form-help">{field.help}</p>}
          </div>
        ))}
      </form>

      {/* Test Result */}
      {testResult && (
        <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
          <div className="result-icon">{testResult.success ? '✓' : '✕'}</div>
          <div className="result-content">
            <p className="result-message">
              {testResult.message || testResult.error}
            </p>
            {testResult.model && (
              <p className="result-detail">Model: {testResult.model}</p>
            )}
          </div>
        </div>
      )}

      {/* Form Actions */}
      <div className="form-actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onSave}
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Save Configuration'}
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={onTest}
          disabled={loading || testing}
        >
          {testing ? 'Testing...' : 'Test Connection'}
        </button>

        {onFetchModels && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onFetchModels}
            disabled={loading || fetchingModels}
          >
            {fetchingModels ? 'Fetching...' : 'Refresh Models'}
          </button>
        )}

        {configured && (
          <button
            type="button"
            className="btn btn-danger"
            onClick={onDelete}
            disabled={loading}
          >
            Delete Configuration
          </button>
        )}
      </div>
    </div>
  );
}

export default ProviderConfigForm;
