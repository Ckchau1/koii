// LLM API Client for making requests to the LLM service
// Handles streaming, retries, and error handling

var llmClient = {
  config: null,
  apiKey: null,
  requestTimeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second

  initialize: function(config, apiKey) {
    this.config = config
    this.apiKey = apiKey
  },

  buildHeaders: function() {
    const headers = {
      'Content-Type': 'application/json',
      'x-api-key': this.apiKey,
      'anthropic-version': '2023-06-01'
    }
    return headers
  },

  buildMessageRequest: function(messages, systemPrompt) {
    const formattedMessages = messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }))

    return {
      model: this.config.modelId,
      max_tokens: this.config.maxTokens,
      temperature: this.config.temperature,
      system: systemPrompt || 'You are a helpful AI assistant integrated into a web browser. Help the user with their browsing tasks.',
      messages: formattedMessages
    }
  },

  chat: function(messages, systemPrompt, callbacks) {
    if (!this.apiKey || !this.config) {
      if (callbacks && callbacks.onError) {
        callbacks.onError(new Error('LLM not configured'))
      }
      return
    }

    const url = `${this.config.apiUrl}/messages`
    const body = this.buildMessageRequest(messages, systemPrompt)

    const makeRequest = (attempt = 0) => {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout)

      fetch(url, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify(body),
        signal: controller.signal
      }).then(response => {
        clearTimeout(timeoutId)

        if (!response.ok) {
          if (response.status === 429 && attempt < this.retryAttempts) {
            // Rate limited, retry with backoff
            setTimeout(() => {
              makeRequest(attempt + 1)
            }, this.retryDelay * Math.pow(2, attempt))
            return
          }

          return response.json().then(err => {
            throw new Error(err.error?.message || `API Error: ${response.status}`)
          })
        }

        // Handle streaming response
        if (callbacks && callbacks.onStream) {
          this.handleStreamResponse(response, callbacks)
        } else {
          // Non-streaming response
          response.json().then(data => {
            clearTimeout(timeoutId)
            if (callbacks && callbacks.onComplete) {
              const content = data.content && data.content.length > 0 ? data.content[0].text : ''
              callbacks.onComplete({
                role: 'assistant',
                content: content,
                stopReason: data.stop_reason
              })
            }
          })
        }
      }).catch(err => {
        clearTimeout(timeoutId)

        if (err.name === 'AbortError') {
          if (callbacks && callbacks.onError) {
            callbacks.onError(new Error('Request timeout'))
          }
        } else if (attempt < this.retryAttempts && err.message.includes('Failed to fetch')) {
          // Network error, retry
          setTimeout(() => {
            makeRequest(attempt + 1)
          }, this.retryDelay * Math.pow(2, attempt))
        } else {
          if (callbacks && callbacks.onError) {
            callbacks.onError(err)
          }
        }
      })
    }

    makeRequest()
  },

  handleStreamResponse: function(response, callbacks) {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let completeMessage = ''

    const readChunk = () => {
      reader.read().then(({ done, value }) => {
        if (done) {
          // Stream complete
          if (callbacks && callbacks.onComplete) {
            callbacks.onComplete({
              role: 'assistant',
              content: completeMessage,
              stopReason: 'end_turn'
            })
          }
          return
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Process complete lines
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim()
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'content_block_delta' && event.delta && event.delta.type === 'text_delta') {
                const text = event.delta.text
                completeMessage += text
                if (callbacks && callbacks.onChunk) {
                  callbacks.onChunk(text)
                }
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e)
            }
          }
        }

        // Keep incomplete line in buffer
        buffer = lines[lines.length - 1]
        readChunk()
      }).catch(err => {
        if (callbacks && callbacks.onError) {
          callbacks.onError(err)
        }
      })
    }

    readChunk()
  },

  getPageContext: function() {
    // Extract meaningful context from the current page
    const title = document.title || ''
    const url = window.location.href
    const selection = window.getSelection().toString().trim()

    // Extract visible text snippet (first 500 chars of body text)
    let bodyText = document.body.innerText || ''
    bodyText = bodyText.slice(0, 500).trim()

    return {
      title,
      url,
      selection,
      snippet: bodyText,
      timestamp: new Date().toISOString()
    }
  },

  getPageContextPrompt: function() {
    const context = this.getPageContext()
    const parts = []

    if (context.title) {
      parts.push(`Page title: ${context.title}`)
    }
    if (context.url) {
      parts.push(`Page URL: ${context.url}`)
    }
    if (context.selection) {
      parts.push(`Selected text: "${context.selection}"`)
    }
    if (context.snippet) {
      parts.push(`Page content (excerpt): ${context.snippet}...`)
    }

    if (parts.length === 0) {
      return null
    }

    return `\nCurrent browsing context:\n${parts.join('\n')}`
  }
}

module.exports = llmClient
