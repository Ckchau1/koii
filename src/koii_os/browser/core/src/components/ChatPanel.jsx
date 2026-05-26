import React, { useState, useRef, useEffect } from 'react';
import '../styles/ChatPanel.css';

function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hello! I\'m Koii Assistant. How can I help you today?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Simulate streaming response
    try {
      // Get LLM config if available
      const config = window.electronAPI
        ? await window.electronAPI.getConfigs()
        : null;

      // For now, simulate a response
      const assistantMessage = {
        id: messages.length + 2,
        type: 'assistant',
        content: await generateResponse(input, config),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error getting response:', error);
      const errorMessage = {
        id: messages.length + 2,
        type: 'assistant',
        content:
          'Sorry, I encountered an error. Please check your LLM settings.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateResponse = async (userInput, config) => {
    // This would integrate with the configured LLM
    // For now, return a mock response
    const responses = [
      `That's an interesting question about "${userInput}". I can help you explore this topic further.`,
      `I understand you're asking about "${userInput}". Here are some insights...`,
      `Great question! Regarding "${userInput}", let me provide you with some helpful information.`,
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  };

  return (
    <div className="chat-panel">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-title-section">
          <div className="chat-icon">💬</div>
          <div>
            <h2>Koii Assistant</h2>
            <p className="chat-subtitle">AI-powered semantic understanding</p>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message-group ${message.type === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            {message.type === 'assistant' && (
              <div className="message-avatar assistant-avatar">🤖</div>
            )}

            <div className={`message-bubble ${message.type}`}>
              <div className="message-content">{message.content}</div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>

            {message.type === 'user' && (
              <div className="message-avatar user-avatar">👤</div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="message-group assistant-message">
            <div className="message-avatar assistant-avatar">🤖</div>
            <div className="message-bubble assistant loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything... (supports streaming responses)"
            className="chat-input"
            disabled={isLoading}
            maxLength={500}
          />

          <div className="input-actions">
            <span className="char-count">{input.length}/500</span>
            <button
              type="submit"
              className="send-button"
              disabled={!input.trim() || isLoading}
              title="Send message (Enter)"
            >
              {isLoading ? '...' : '→'}
            </button>
          </div>
        </div>

        <div className="input-hints">
          <span className="hint">💡 Tip: Use @agents to invoke specific agents</span>
          <span className="hint">⚡ Streaming responses enabled when LLM configured</span>
        </div>
      </form>
    </div>
  );
}

export default ChatPanel;
