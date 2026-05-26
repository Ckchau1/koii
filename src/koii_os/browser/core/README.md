# Koii OS Browser

A lightweight Electron-based browser for Koii OS with semantic-driven agent system and LLM settings panel.

## Features

- 🌐 **Light Browser Interface** - Integrated web browser for seamless navigation
- 🤖 **Multi-Agent System** - Semantic-driven architecture with 8 specialized agents
- ⚙️ **LLM Settings Panel** - Configure multiple LLM providers with encrypted storage
- 🔐 **Secure Configuration** - AES-256 encryption for API keys and sensitive data
- 🎯 **Initiative-based Control** - Proactive/Balanced/Highly Initiative modes
- 📊 **Agent Dashboard** - Monitor and control agent systems in real-time

## Supported LLM Providers

### ✅ Configured Providers
- **OpenAI** - GPT-4, GPT-4 Turbo, GPT-3.5
- **Anthropic** - Claude Opus, Claude Sonnet, Claude Haiku
- **Local (Ollama)** - Run models locally
- **Custom** - Any API-compatible provider

## Project Structure

```
koii_os/browser/core/
├── electron/                    # Electron main process
│   ├── main.js                 # Main Electron app
│   ├── preload.js              # IPC bridge
│   └── utils/
│       ├── configManager.js    # Encrypted config storage
│       └── llmTester.js        # LLM connection tester
├── src/                        # React app
│   ├── App.jsx                 # Main app component
│   ├── components/
│   │   ├── LLMSettingsPanel.jsx
│   │   ├── BrowserInterface.jsx
│   │   ├── AgentDashboard.jsx
│   │   ├── providers/          # Provider-specific configs
│   │   │   ├── OpenAIConfig.jsx
│   │   │   ├── AnthropicConfig.jsx
│   │   │   ├── LocalConfig.jsx
│   │   │   ├── CustomConfig.jsx
│   │   │   └── ProviderConfigForm.jsx
│   │   └── styles/
│   ├── styles/                 # Global styles
│   ├── index.jsx               # React entry point
│   └── index.css               # Global styles
├── public/
│   └── index.html              # HTML entry point
├── package.json                # Dependencies
└── README.md
```

## Installation

### Prerequisites
- **Node.js** 16+ and npm
- **Ollama** (optional, for local LLM support) - [Download](https://ollama.ai)

### Setup

1. **Install dependencies:**
```bash
cd koii_os/browser/core
npm install
```

2. **Start development:**
```bash
npm run dev
```
This starts both the React dev server and Electron app.

3. **Build for production:**
```bash
npm run build
npm run electron
```

## Configuration

### LLM Configuration Files

Configurations are stored encrypted in:
```
~/.koii-configs/llm-configs.json
```

**Encryption Details:**
- Algorithm: AES-256-CBC
- Key: Auto-generated and stored securely
- IV: Random per encryption

### OpenAI Setup

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Create API key
3. In LLM Settings > OpenAI, enter:
   - API Key: `sk-...`
   - Model: Select from list or enter custom
   - Temperature: 0-2 (default: 0.7)
   - Max Tokens: Request limit (default: 2000)

### Anthropic Setup

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create API key
3. In LLM Settings > Anthropic, enter:
   - API Key: `sk-ant-...`
   - Model: Claude version
   - Temperature: 0-1 (default: 0.7)

### Local LLM Setup (Ollama)

1. **Install Ollama:**
   - Download from [ollama.ai](https://ollama.ai)
   - Run: `ollama serve`

2. **Pull a model:**
```bash
ollama pull llama2
ollama pull mistral
```

3. **In LLM Settings > Local:**
   - Base URL: `http://localhost:11434`
   - Click "Refresh Models" to list available models
   - Select model

### Custom Provider Setup

For any other LLM API:
1. In LLM Settings > Custom Provider
2. Enter:
   - Base URL: Your API endpoint
   - API Key: If authentication required
   - Model: Default model name
   - API Path: Endpoint path (default: `/health`)

## Agent System

### Core Agents

1. **API Plugin Development Agent** 🔌
   - Dynamically creates and deploys API plugins
   - Automated debugging and version control

2. **Core Settings Agent** ⚙️
   - Manages kernel settings
   - Resource allocation
   - Zero-trust security policies

3. **Mode Settings Agent** 🎛️
   - Development/Production/Privacy/Learning modes
   - Semantic-driven initiative control

4. **Task Execution Agent** ✓
   - Task breakdown and execution
   - Result reporting

5. **AI Browser Agent** 🌐
   - Webpage interaction
   - Real-time summarization
   - Semantic search

6. **Orchestration Agent** 🔀
   - Task allocation
   - Conflict resolution
   - Workflow management

7. **Self-Learning Agent** 📚
   - Learning from usage history
   - Prompt optimization
   - Model improvement

8. **Semantic Understanding Agent** 🧠
   - Intent parsing
   - Context maintenance
   - Proactive questioning

### Operating Modes

- **Production** - Optimized for reliability
- **Development** - Enhanced debugging
- **Privacy Mode** - Minimal data collection
- **Learning Mode** - Active optimization

### Initiative Levels

- **Passive** - Reactive only
- **Balanced** - Mix of reactive and proactive
- **Highly Initiative** - Proactive intervention

## API Reference

### Electron IPC API

```javascript
// Configuration Management
await window.electronAPI.getConfigs()
await window.electronAPI.getConfig(provider)
await window.electronAPI.saveConfig(provider, config)
await window.electronAPI.deleteConfig(provider)

// LLM Operations
await window.electronAPI.testConnection(provider, config)
await window.electronAPI.listModels(provider, apiKey, baseUrl)
```

## Troubleshooting

### API Connection Issues

1. **Check network connectivity**
```bash
ping api.openai.com
```

2. **Verify API keys**
   - Keys should be valid and not revoked
   - Check expiration dates

3. **Test connection**
   - Use "Test Connection" button in settings
   - Check error messages

### Local LLM Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Pull models if needed
ollama pull llama2
```

### Configuration Issues

1. **Reset configurations:**
```bash
rm ~/.koii-configs/llm-configs.json
```

2. **Check encryption key:**
```bash
ls -la ~/.koii-configs/.encryption-key
```

## Performance

- **App Size:** ~150MB (production build)
- **Memory Usage:** 150-300MB baseline
- **Startup Time:** ~2-3 seconds
- **API Response:** 250-500ms average

## Security

✅ **Security Features:**
- AES-256 encryption for sensitive data
- IPC context isolation
- No remote code execution
- Minimal API surface
- Secure credential storage

## Development

### Adding a New Provider

1. Create component in `src/components/providers/NewConfig.jsx`:
```jsx
import React, { useState } from 'react';
import ProviderConfigForm from './ProviderConfigForm';

function NewConfig({ config, onSave, onDelete, loading }) {
  const [formData, setFormData] = useState(config || {});
  
  const fields = [
    // Define form fields
  ];

  return (
    <ProviderConfigForm
      provider="New Provider"
      fields={fields}
      formData={formData}
      onFormChange={(e) => setFormData({ ...formData, [e.target.name]: e.target.value })}
      onSave={() => onSave(formData)}
      // ... other props
    />
  );
}
```

2. Update `electron/main.js` to add IPC handler
3. Import in `src/components/LLMSettingsPanel.jsx`

### Building Distribution

```bash
npm run build
npm run pack        # Create distributable
npm run dist        # Create installer
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

## License

MIT License - See LICENSE file

## Support

- 📖 [Documentation](./docs)
- 🐛 [Issue Tracker](./issues)
- 💬 [Discussions](./discussions)

## Roadmap

- [ ] Voice interaction support
- [ ] Advanced agent training
- [ ] Multi-provider load balancing
- [ ] Model fine-tuning interface
- [ ] Advanced analytics dashboard
- [ ] Plugin marketplace

## Credits

Built for Koii OS - Semantic-driven Agent Architecture
