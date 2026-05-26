import React, { useState, useRef } from 'react';
import '../styles/BrowserInterface.css';

function BrowserInterface() {
  const [url, setUrl] = useState('https://www.example.com');
  const [isLoading, setIsLoading] = useState(false);
  const iframeRef = useRef(null);

  const handleNavigate = (e) => {
    e.preventDefault();
    setIsLoading(true);

    // Simulate navigation - in production, this would use native browser capabilities
    let navigateUrl = url;
    if (!navigateUrl.startsWith('http://') && !navigateUrl.startsWith('https://')) {
      navigateUrl = 'https://' + navigateUrl;
    }

    if (iframeRef.current) {
      iframeRef.current.src = navigateUrl;
      iframeRef.current.onload = () => setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.history.back();
    }
  };

  const handleGoForward = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.history.forward();
    }
  };

  const handleRefresh = () => {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src;
    }
  };

  return (
    <div className="browser-interface">
      <div className="browser-toolbar">
        <div className="toolbar-buttons">
          <button className="toolbar-btn" onClick={handleGoBack} title="Back">
            ← Back
          </button>
          <button className="toolbar-btn" onClick={handleGoForward} title="Forward">
            Forward →
          </button>
          <button className="toolbar-btn" onClick={handleRefresh} title="Refresh">
            ↻ Refresh
          </button>
        </div>

        <form className="address-bar" onSubmit={handleNavigate}>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter URL..."
            className="url-input"
          />
          <button type="submit" className="navigate-btn">
            {isLoading ? 'Loading...' : '→'}
          </button>
        </form>

        <div className="toolbar-status">
          {isLoading && <span className="loading-indicator">● Loading</span>}
        </div>
      </div>

      <div className="browser-content">
        <iframe
          ref={iframeRef}
          src={url}
          className="browser-frame"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          title="Browser Content"
        />
      </div>

      <div className="browser-footer">
        <p>Light Browser • Ready for web integration</p>
      </div>
    </div>
  );
}

export default BrowserInterface;
