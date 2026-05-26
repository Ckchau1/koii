import React, { useState, useRef } from 'react';
import BrowserHeader from './BrowserHeader';
import AddressBar from './AddressBar';
import ChatPanel from './ChatPanel';
import LLMSettingsPanel from './LLMSettingsPanel';
import AgentDashboard from './AgentDashboard';
import '../styles/ModernBrowserInterface.css';

function ModernBrowserInterface() {
  const [url, setUrl] = useState('https://www.google.com');
  const [activeTab, setActiveTab] = useState('browser');
  const [isLoading, setIsLoading] = useState(false);
  const iframeRef = useRef(null);

  const handleNavigate = (newUrl) => {
    setIsLoading(true);

    let navigateUrl = newUrl;
    if (!navigateUrl.startsWith('http://') && !navigateUrl.startsWith('https://')) {
      navigateUrl = 'https://' + navigateUrl;
    }

    setUrl(navigateUrl);

    if (iframeRef.current) {
      iframeRef.current.src = navigateUrl;
      iframeRef.current.onload = () => setIsLoading(false);
      iframeRef.current.onerror = () => setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      try {
        iframeRef.current.contentWindow.history.back();
      } catch (e) {
        console.log('Cannot go back');
      }
    }
  };

  const handleGoForward = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      try {
        iframeRef.current.contentWindow.history.forward();
      } catch (e) {
        console.log('Cannot go forward');
      }
    }
  };

  return (
    <div className="modern-browser-container">
      {/* Header with Navigation */}
      <BrowserHeader activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Address Bar */}
      <AddressBar
        url={url}
        onNavigate={handleNavigate}
        onBack={handleGoBack}
        onForward={handleGoForward}
        isLoading={isLoading}
      />

      {/* Main Content Area */}
      <div className="browser-main">
        {activeTab === 'browser' && (
          <div className="browser-content">
            {isLoading && (
              <div className="loading-overlay">
                <div className="loading-spinner"></div>
                <p>Loading...</p>
              </div>
            )}
            <iframe
              ref={iframeRef}
              src={url}
              className="browser-frame"
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-presentation"
              title="Browser Content"
            />
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="tab-content chat-tab" style={{ padding: 0 }}>
            <ChatPanel />
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="tab-content agents-tab" style={{ padding: 0 }}>
            <AgentDashboard />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="tab-content settings-tab" style={{ padding: 0 }}>
            <LLMSettingsPanel />
          </div>
        )}
      </div>
    </div>
  );
}

export default ModernBrowserInterface;
