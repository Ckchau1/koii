import React, { useState } from 'react';
import '../styles/AddressBar.css';

function AddressBar({ url, onNavigate, onBack, onForward, isLoading }) {
  const [inputValue, setInputValue] = useState(url);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);

    // Show suggestions if input looks like search
    if (value.length > 2) {
      setShowSuggestions(true);
      // Mock suggestions
      setSuggestions([
        `Search: "${value}"`,
        `${value}.com`,
        `www.${value}.com`,
      ]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowSuggestions(false);
    onNavigate(inputValue);
  };

  const handleSuggestionClick = (suggestion) => {
    if (suggestion.startsWith('Search:')) {
      const query = suggestion.replace('Search: "', '').replace('"', '');
      onNavigate(`https://www.google.com/search?q=${encodeURIComponent(query)}`);
    } else {
      const url = suggestion.includes('://') ? suggestion : `https://${suggestion}`;
      onNavigate(url);
    }
    setShowSuggestions(false);
  };

  return (
    <div className="address-bar-container">
      {/* Navigation Buttons */}
      <div className="nav-buttons">
        <button
          className="nav-btn"
          onClick={onBack}
          title="Back"
          disabled={isLoading}
        >
          ←
        </button>
        <button
          className="nav-btn"
          onClick={onForward}
          title="Forward"
          disabled={isLoading}
        >
          →
        </button>
      </div>

      {/* Address Bar */}
      <form className="address-bar" onSubmit={handleSubmit}>
        <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>

        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setShowSuggestions(inputValue.length > 2)}
          placeholder="Search with AI or enter URL..."
          className="address-input"
        />

        {/* Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="suggestions-dropdown">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="suggestion-item"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
                <span>{suggestion}</span>
              </div>
            ))}
          </div>
        )}

        <button
          type="button"
          className="voice-btn"
          title="Search by voice"
        >
          🎤
        </button>
      </form>

      {/* Menu Button */}
      <button className="menu-btn" title="Menu">
        ⋮
      </button>
    </div>
  );
}

export default AddressBar;
