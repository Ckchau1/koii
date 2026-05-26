const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { ConfigManager } = require('./utils/configManager');
const { testLLMConnection } = require('./utils/llmTester');

let mainWindow;
const configManager = new ConfigManager();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
    },
    icon: path.join(__dirname, '../public/koii.png'),
  });

  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../build/index.html')}`;

  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC Handlers for LLM Configuration
ipcMain.handle('config:get-all', async () => {
  try {
    return configManager.getAllConfigs();
  } catch (error) {
    console.error('Error getting configs:', error);
    throw error;
  }
});

ipcMain.handle('config:get', async (event, provider) => {
  try {
    return configManager.getConfig(provider);
  } catch (error) {
    console.error('Error getting config:', error);
    throw error;
  }
});

ipcMain.handle('config:save', async (event, provider, config) => {
  try {
    configManager.saveConfig(provider, config);
    return { success: true, message: `${provider} configuration saved` };
  } catch (error) {
    console.error('Error saving config:', error);
    throw error;
  }
});

ipcMain.handle('config:delete', async (event, provider) => {
  try {
    configManager.deleteConfig(provider);
    return { success: true, message: `${provider} configuration deleted` };
  } catch (error) {
    console.error('Error deleting config:', error);
    throw error;
  }
});

ipcMain.handle('llm:test-connection', async (event, provider, config) => {
  try {
    const result = await testLLMConnection(provider, config);
    return result;
  } catch (error) {
    console.error('Error testing connection:', error);
    throw error;
  }
});

ipcMain.handle('llm:list-models', async (event, provider, apiKey, baseUrl) => {
  try {
    // This would call the actual API to list available models
    const models = await getModelsForProvider(provider, apiKey, baseUrl);
    return models;
  } catch (error) {
    console.error('Error listing models:', error);
    throw error;
  }
});

// Helper function to get models for different providers
async function getModelsForProvider(provider, apiKey, baseUrl) {
  const axios = require('axios');

  switch (provider) {
    case 'openai':
      try {
        const response = await axios.get('https://api.openai.com/v1/models', {
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
        return response.data.data.map(m => ({ id: m.id, name: m.id }));
      } catch (error) {
        throw new Error('Failed to fetch OpenAI models');
      }

    case 'anthropic':
      return [
        { id: 'claude-opus-4-6', name: 'Claude Opus 4.6' },
        { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6' },
        { id: 'claude-haiku-4-5', name: 'Claude Haiku 4.5' },
      ];

    case 'local':
      try {
        const response = await axios.get(`${baseUrl}/api/tags`);
        return response.data.models.map(m => ({ id: m.name, name: m.name }));
      } catch (error) {
        throw new Error('Failed to fetch local models. Ensure Ollama is running.');
      }

    default:
      return [];
  }
}

// Handle app ready event
if (require('electron-squirrel-startup')) app.quit();
