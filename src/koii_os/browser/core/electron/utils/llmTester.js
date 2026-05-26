const axios = require('axios');

async function testLLMConnection(provider, config) {
  try {
    switch (provider) {
      case 'openai':
        return await testOpenAI(config);
      case 'anthropic':
        return await testAnthropic(config);
      case 'local':
        return await testLocal(config);
      case 'custom':
        return await testCustom(config);
      default:
        throw new Error(`Unknown provider: ${provider}`);
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
      provider: provider,
    };
  }
}

async function testOpenAI(config) {
  const { apiKey, model } = config;

  if (!apiKey) {
    throw new Error('API Key is required');
  }

  try {
    const response = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: model || 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: 'Say "Connection successful"' }],
        max_tokens: 10,
      },
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        timeout: 10000,
      }
    );

    return {
      success: true,
      provider: 'openai',
      message: 'Successfully connected to OpenAI',
      model: response.data.model,
    };
  } catch (error) {
    const errorMsg = error.response?.data?.error?.message || error.message;
    throw new Error(`OpenAI connection failed: ${errorMsg}`);
  }
}

async function testAnthropic(config) {
  const { apiKey, model } = config;

  if (!apiKey) {
    throw new Error('API Key is required');
  }

  try {
    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      {
        model: model || 'claude-opus-4-6',
        max_tokens: 10,
        messages: [{ role: 'user', content: 'Say "Connection successful"' }],
      },
      {
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'Content-Type': 'application/json',
        },
        timeout: 10000,
      }
    );

    return {
      success: true,
      provider: 'anthropic',
      message: 'Successfully connected to Anthropic',
      model: response.data.model,
    };
  } catch (error) {
    const errorMsg = error.response?.data?.error?.message || error.message;
    throw new Error(`Anthropic connection failed: ${errorMsg}`);
  }
}

async function testLocal(config) {
  const { baseUrl, model } = config;

  if (!baseUrl) {
    throw new Error('Base URL is required');
  }

  try {
    const response = await axios.post(
      `${baseUrl}/api/generate`,
      {
        model: model || 'llama2',
        prompt: 'Connection test',
        stream: false,
      },
      {
        timeout: 10000,
      }
    );

    return {
      success: true,
      provider: 'local',
      message: `Successfully connected to local LLM at ${baseUrl}`,
      model: model,
    };
  } catch (error) {
    const errorMsg = error.message;
    throw new Error(`Local LLM connection failed: ${errorMsg}. Make sure Ollama or your local server is running.`);
  }
}

async function testCustom(config) {
  const { baseUrl, apiKey, model, customPath } = config;

  if (!baseUrl) {
    throw new Error('Base URL is required');
  }

  try {
    const headers = {};
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    const response = await axios.get(
      `${baseUrl}${customPath || '/health'}`,
      { headers, timeout: 10000 }
    );

    return {
      success: true,
      provider: 'custom',
      message: `Successfully connected to custom LLM at ${baseUrl}`,
      model: model,
    };
  } catch (error) {
    const errorMsg = error.message;
    throw new Error(`Custom LLM connection failed: ${errorMsg}`);
  }
}

module.exports = { testLLMConnection };
