import React, { useState } from 'react';
import ThemeConfigurator from './ThemeConfigurator';
import '../../styles/HomePage.CSS/HCSS.css';

const ThemeButton = ({ theme, currentTheme, onThemeChange }) => {
  const [isConfiguratorOpen, setIsConfiguratorOpen] = useState(false);

  const handleButtonClick = () => {
    // Always change theme when button is clicked
    onThemeChange(theme);
  };

  const handleEditClick = (e) => {
    // Stop propagation to prevent theme change
    e.stopPropagation();
    setIsConfiguratorOpen(true);
  };

  return (
    <div className={`theme-button-container ${currentTheme === theme ? 'active' : ''}`}>
      <button
        className={`theme-button ${currentTheme === theme ? 'active' : ''}`}
        onClick={handleButtonClick}
      >
        {theme === 'creative' && currentTheme === 'creative' && (
          <span 
            className="edit-icon" 
            title="Edit Creative Theme"
            onClick={handleEditClick}
          >
            ✏️
          </span>
        )}
        {theme === 'dark' ? 'Dark' : theme === 'light' ? 'Light' : 'Creative'}
      </button>

      {isConfiguratorOpen && (
        <ThemeConfigurator onClose={() => setIsConfiguratorOpen(false)} />
      )}
    </div>
  );
};

export default ThemeButton;
