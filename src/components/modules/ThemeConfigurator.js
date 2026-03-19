import React, { useState, useEffect, useRef } from 'react';
import ThemeGenerator from './ThemeGenerator';
import '../../styles/HomePage.CSS/HCSS.css';

const ThemeConfigurator = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('colors');
  const [colors, setColors] = useState({
    primary: '',
    secondary: '',
    text: '',
    background: '',
    card: '',
    border: '',
    success: '',
    danger: '',
    warning: '',
    info: '',
    textSecondary: ''
  });

  const [gradients, setGradients] = useState({
    color1: '#9333ea',
    color2: '#7928ca',
    angle: '145deg',
    extraColor: '',
    extraPosition: '50%',
    useExtraColor: false
  });

  const [cssRegistry, setCssRegistry] = useState({
    selectedFiles: [],
    cssCode: '',
    status: ''
  });

  const [colorsChanged, setColorsChanged] = useState([]);
  const [saveStatus, setSaveStatus] = useState(null);

  const themeGenerator = useRef(new ThemeGenerator());
  const availableCssFiles = [
    'HomePage_AboutUs.css',
    'HomePage_buttons.css',
    'HomePage_FactAdmin.css',
    'HomePage_monitoring.css',
    'HomePage_selectors.css',
    'HomePage1.css',
    'HomePage2.css',
    'HomePage3.css',
    'HomePage4.css',
    'HomePage5.css',
    'HomePage6.css'
  ];

  // Load current theme colors on component mount
  useEffect(() => {
    loadThemeColors();
  }, []);

  // Load theme colors from current theme
  const loadThemeColors = () => {
    const themeColors = themeGenerator.current.loadCurrentThemeColors();
    setColors({
    primary: themeColors['--primary-color'],
    secondary: themeColors['--secondary-color'],
    text: themeColors['--text-color'],
    background: themeColors['--background-color'],
    card: themeColors['--card-background'],
    border: themeColors['--border-color'],
    success: themeColors['--success-color'],
    danger: themeColors['--danger-color'],
    warning: themeColors['--warning-color'],
    info: themeColors['--info-color'],
    textSecondary: themeColors['--text-secondary']
    });

    // Parse gradient if present
    const gradientString = themeColors['--gradient-primary'] || '';
    if (gradientString.includes('linear-gradient')) {
      try {
        const angle = gradientString.match(/(\d+)deg/) ? gradientString.match(/(\d+)deg/)[1] + 'deg' : '145deg';
        const colorMatches = gradientString.match(/#[a-f0-9]{6}/gi);

        if (colorMatches && colorMatches.length >= 2) {
          setGradients({
            ...gradients,
            color1: colorMatches[0],
            color2: colorMatches[1],
            angle: angle,
            extraColor: colorMatches[2] || '',
            useExtraColor: colorMatches.length > 2
          });
        }
      } catch (error) {
        console.log('Error parsing gradient', error);
      }
    }

    setColorsChanged([]);
  };

  // Handle color change
  const handleColorChange = (colorKey, value) => {
    // If the value is a linear gradient, it should be processed differently
    if (typeof value === 'string' && value.trim().startsWith('linear-gradient(')) {
      console.log(`Processing gradient for ${colorKey}: ${value.substring(0, 30)}...`);

      // For primary color, we can directly apply the gradient to the gradient-primary variable
      if (colorKey === 'primary') {
        // Set gradient-primary and keep the extracted color for the primary color
        themeGenerator.current.applyGradientToCurrentTheme(value);

        // Extract the first color for the actual primary color
        const colorMatch = value.match(/#[a-f0-9]{3,8}|rgba?\([^)]+\)/i);
        if (colorMatch && colorMatch[0]) {
          const processedValue = colorMatch[0];

          // Update the state
          setColors(prevColors => ({
            ...prevColors,
            [colorKey]: processedValue
          }));

          // Apply the color-only version to the primary color variable
          themeGenerator.current.applyColorToCurrentTheme(colorKey, processedValue);
        }
      } else {
        // For other colors, extract the first color from the gradient
        const colorMatch = value.match(/#[a-f0-9]{3,8}|rgba?\([^)]+\)/i);
        if (colorMatch && colorMatch[0]) {
          const processedValue = colorMatch[0];

          // Update the state
          setColors(prevColors => ({
            ...prevColors,
            [colorKey]: processedValue
          }));

          // Apply the extracted color
          themeGenerator.current.applyColorToCurrentTheme(colorKey, processedValue);
        }
      }
    } else {
      // Regular color value - process normally
      setColors(prevColors => ({
        ...prevColors,
        [colorKey]: value
      }));

      // Apply the color change in real-time
      themeGenerator.current.applyColorToCurrentTheme(colorKey, value);
    }

    // Track changed colors
    if (!colorsChanged.includes(colorKey)) {
      setColorsChanged(prev => [...prev, colorKey]);
    }
  };

  // Handle gradient change
  const handleGradientChange = (key, value) => {
    setGradients(prev => ({
      ...prev,
      [key]: value
    }));

    // Generate and apply gradient in real-time
    const newGradient = generateGradientString({
      ...gradients,
      [key]: value
    });

    themeGenerator.current.applyGradientToCurrentTheme(newGradient);
  };

  // Generate gradient string from gradient object
  const generateGradientString = (gradientObj) => {
    const { color1, color2, angle, extraColor, extraPosition, useExtraColor } = gradientObj || gradients;

    if (useExtraColor && extraColor) {
      return `linear-gradient(${angle}, ${color1}, ${extraColor} ${extraPosition}, ${color2})`;
    } else {
      return `linear-gradient(${angle}, ${color1}, ${color2})`;
    }
  };

  // Apply all theme changes
  const applyTheme = async () => {
    setSaveStatus({ state: 'saving', message: 'Applying theme...' });

    try {
      // Create theme data for saving
      const themeData = {
        colors: colors,
        gradients: {
          primary: generateGradientString()
        }
      };

      // Save theme
      const result = await themeGenerator.current.saveToCreativeTheme(themeData);

      if (result.success) {
        setSaveStatus({ state: 'success', message: 'Theme applied successfully!' });
        setColorsChanged([]);
      } else {
        // If server save failed but client download succeeded
        if (result.clientFallback) {
          setSaveStatus({ 
            state: 'warning', 
            message: 'Server save failed, but theme file was downloaded. Please add it to your styles folder.' 
          });
        } else {
          throw new Error(result.message || 'Unknown error');
        }
      }
    } catch (error) {
      setSaveStatus({ 
        state: 'error', 
        message: `Failed to apply theme: ${error.message}` 
      });
    }

    // Clear status after 3 seconds
    setTimeout(() => {
      setSaveStatus(null);
    }, 3000);
  };

  // Reset all color changes
  const resetAllColors = () => {
    loadThemeColors();
    themeGenerator.current.resetTheme();
  };

  // Reset a specific color
  const resetColor = (colorKey) => {
    const originalColor = themeGenerator.current.getOriginalColor(colorKey);
    handleColorChange(colorKey, originalColor);

    // Remove from changed colors list
    setColorsChanged(prev => prev.filter(key => key !== colorKey));
  };

  // Toggle CSS file selection
  const toggleCssFile = (filename) => {
    setCssRegistry(prev => {
      const isSelected = prev.selectedFiles.includes(filename);
      return {
        ...prev,
        selectedFiles: isSelected 
          ? prev.selectedFiles.filter(f => f !== filename)
          : [...prev.selectedFiles, filename]
      };
    });
  };

  // Handle CSS code input
  const handleCssCodeChange = (e) => {
    setCssRegistry(prev => ({
      ...prev,
      cssCode: e.target.value
    }));
  };

  // Apply CSS to selected files
  const applyCssToFiles = async () => {
    if (cssRegistry.selectedFiles.length === 0 || !cssRegistry.cssCode.trim()) {
      setCssRegistry(prev => ({
        ...prev,
        status: 'Please select files and provide CSS code'
      }));
      return;
    }

    try {
      setCssRegistry(prev => ({
        ...prev,
        status: 'Applying CSS...'
      }));

      const result = await themeGenerator.current.applyCssToFiles(
        cssRegistry.selectedFiles,
        cssRegistry.cssCode
      );

      if (result.success) {
        setCssRegistry(prev => ({
          ...prev,
          status: 'CSS applied successfully!'
        }));
      } else {
        throw new Error(result.message || 'Unknown error');
      }
    } catch (error) {
      setCssRegistry(prev => ({
        ...prev,
        status: `Error: ${error.message}`
      }));
    }

    // Clear status after 3 seconds
    setTimeout(() => {
      setCssRegistry(prev => ({
        ...prev,
        status: ''
      }));
    }, 3000);
  };

  return (
    <div className="theme-configurator">
      <div className="theme-configurator-header">
        <h2>Theme Customization</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="tab-buttons">
        <button 
          className={`tab-button ${activeTab === 'colors' ? 'active' : ''}`}
          onClick={() => setActiveTab('colors')}
        >
          Colors
        </button>
        <button 
          className={`tab-button ${activeTab === 'gradients' ? 'active' : ''}`}
          onClick={() => setActiveTab('gradients')}
        >
          Gradients
        </button>
        <button 
          className={`tab-button ${activeTab === 'css' ? 'active' : ''}`}
          onClick={() => setActiveTab('css')}
        >
          CSS Registry
        </button>
      </div>

      {activeTab === 'colors' && (
        <div className="color-pickers-container">
          <h3>Primary & Secondary Colors</h3>
          <div className="color-picker-row">
            <div className="color-picker-item">
              <label>Primary Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.primary }}
                  onClick={() => document.getElementById('primary-color-input').click()}
                ></div>
                <input
                  id="primary-color-input"
                  type="color"
                  value={colors.primary}
                  onChange={(e) => handleColorChange('primary', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.primary}
                  onChange={(e) => handleColorChange('primary', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('primary') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('primary')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Secondary Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.secondary }}
                  onClick={() => document.getElementById('secondary-color-input').click()}
                ></div>
                <input
                  id="secondary-color-input"
                  type="color"
                  value={colors.secondary}
                  onChange={(e) => handleColorChange('secondary', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.secondary}
                  onChange={(e) => handleColorChange('secondary', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('secondary') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('secondary')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>
          </div>

          <h3>Text & Background</h3>
          <div className="color-picker-row">
            <div className="color-picker-item">
              <label>Text Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.text }}
                  onClick={() => document.getElementById('text-color-input').click()}
                ></div>
                <input
                  id="text-color-input"
                  type="color"
                  value={colors.text}
                  onChange={(e) => handleColorChange('text', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.text}
                  onChange={(e) => handleColorChange('text', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('text') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('text')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Text Secondary</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.textSecondary }}
                  onClick={() => document.getElementById('text-secondary-input').click()}
                ></div>
                <input
                  id="text-secondary-input"
                  type="color"
                  value={colors.textSecondary}
                  onChange={(e) => handleColorChange('textSecondary', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.textSecondary}
                  onChange={(e) => handleColorChange('textSecondary', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('textSecondary') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('textSecondary')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Background Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.background }}
                  onClick={() => document.getElementById('background-color-input').click()}
                ></div>
                <input
                  id="background-color-input"
                  type="color"
                  value={colors.background}
                  onChange={(e) => handleColorChange('background', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.background}
                  onChange={(e) => handleColorChange('background', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('background') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('background')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>
          </div>

          <h3>Component Colors</h3>
          <div className="color-picker-row">
            <div className="color-picker-item">
              <label>Card Background</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.card }}
                  onClick={() => document.getElementById('card-color-input').click()}
                ></div>
                <input
                  id="card-color-input"
                  type="color"
                  value={colors.card}
                  onChange={(e) => handleColorChange('card', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.card}
                  onChange={(e) => handleColorChange('card', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('card') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('card')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Border Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.border }}
                  onClick={() => document.getElementById('border-color-input').click()}
                ></div>
                <input
                  id="border-color-input"
                  type="color"
                  value={colors.border}
                  onChange={(e) => handleColorChange('border', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.border}
                  onChange={(e) => handleColorChange('border', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('border') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('border')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>
          </div>

          <h3>State Colors</h3>
          <div className="color-picker-row">
            <div className="color-picker-item">
              <label>Success Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.success }}
                  onClick={() => document.getElementById('success-color-input').click()}
                ></div>
                <input
                  id="success-color-input"
                  type="color"
                  value={colors.success}
                  onChange={(e) => handleColorChange('success', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.success}
                  onChange={(e) => handleColorChange('success', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('success') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('success')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Danger Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.danger }}
                  onClick={() => document.getElementById('danger-color-input').click()}
                ></div>
                <input
                  id="danger-color-input"
                  type="color"
                  value={colors.danger}
                  onChange={(e) => handleColorChange('danger', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.danger}
                  onChange={(e) => handleColorChange('danger', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('danger') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('danger')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Warning Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.warning }}
                  onClick={() => document.getElementById('warning-color-input').click()}
                ></div>
                <input
                  id="warning-color-input"
                  type="color"
                  value={colors.warning}
                  onChange={(e) => handleColorChange('warning', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.warning}
                  onChange={(e) => handleColorChange('warning', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('warning') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('warning')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>

            <div className="color-picker-item">
              <label>Info Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: colors.info }}
                  onClick={() => document.getElementById('info-color-input').click()}
                ></div>
                <input
                  id="info-color-input"
                  type="color"
                  value={colors.info}
                  onChange={(e) => handleColorChange('info', e.target.value)}
                />
                <input
                  type="text"
                  value={colors.info}
                  onChange={(e) => handleColorChange('info', e.target.value)}
                  className="color-text-input"
                />
                {colorsChanged.includes('info') && (
                  <button 
                    className="reset-color-button" 
                    onClick={() => resetColor('info')}
                    title="Reset to original"
                  >↺</button>
                )}
              </div>
            </div>
          </div>

          <div className="reset-section">
            <button 
              className="reset-all-colors-button"
              onClick={() => {
                resetAllColors();
              }}
              disabled={colorsChanged.length === 0}
            >
              Reset All Colors
            </button>
          </div>
        </div>
      )}

      {activeTab === 'gradients' && (
        <div className="gradients-container">
          <h3>Gradient Generator</h3>

          <div className="gradient-preview" style={{ 
            background: generateGradientString(),
            height: '100px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <div 
              className="gradient-code"
              title="Click to copy gradient" 
              onClick={() => {
                // Copy the gradient string to clipboard
                const gradientString = generateGradientString();
                navigator.clipboard.writeText(gradientString)
                  .then(() => {
                    // Show temporary tooltip or message
                    const gradientPreview = document.querySelector('.gradient-preview');
                    if (gradientPreview) {
                      const tooltip = document.createElement('div');
                      tooltip.className = 'copy-tooltip';
                      tooltip.innerText = 'Copied to clipboard!';
                      gradientPreview.appendChild(tooltip);

                      // Remove after 2 seconds
                      setTimeout(() => {
                        if (tooltip.parentNode) {
                          tooltip.parentNode.removeChild(tooltip);
                        }
                      }, 2000);
                    }
                  })
                  .catch(err => console.error('Could not copy text: ', err));
              }}
            >
              {generateGradientString()} <span className="click-to-copy">(Click to copy)</span>
            </div>
          </div>

          <div className="gradient-controls">
            <div className="gradient-color-picker">
              <label>Start Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: gradients.color1 }}
                  onClick={() => document.getElementById('gradient-color1-input').click()}
                ></div>
                <input
                  id="gradient-color1-input"
                  type="color"
                  value={gradients.color1}
                  onChange={(e) => handleGradientChange('color1', e.target.value)}
                />
                <input
                  type="text"
                  value={gradients.color1}
                  onChange={(e) => handleGradientChange('color1', e.target.value)}
                  className="color-text-input"
                />
              </div>
            </div>

            <div className="gradient-color-picker">
              <label>End Color</label>
              <div className="color-input-group">
                <div 
                  className="color-swatch" 
                  style={{ backgroundColor: gradients.color2 }}
                  onClick={() => document.getElementById('gradient-color2-input').click()}
                ></div>
                <input
                  id="gradient-color2-input"
                  type="color"
                  value={gradients.color2}
                  onChange={(e) => handleGradientChange('color2', e.target.value)}
                />
                <input
                  type="text"
                  value={gradients.color2}
                  onChange={(e) => handleGradientChange('color2', e.target.value)}
                  className="color-text-input"
                />
              </div>
            </div>

            <div className="gradient-angle-picker">
              <label>Angle ({gradients.angle})</label>
              <input
                type="range"
                min="0"
                max="360"
                value={parseInt(gradients.angle)}
                onChange={(e) => handleGradientChange('angle', `${e.target.value}deg`)}
                className="angle-slider"
              />
            </div>

            <div className="extra-color-option">
              <label>
                <input
                  type="checkbox"
                  checked={gradients.useExtraColor}
                  onChange={(e) => handleGradientChange('useExtraColor', e.target.checked)}
                />
                Add intermediate color
              </label>

              {gradients.useExtraColor && (
                <>
                  <div className="gradient-color-picker">
                    <label>Middle Color</label>
                    <div className="color-input-group">
                      <div 
                        className="color-swatch" 
                        style={{ backgroundColor: gradients.extraColor || '#8a2be2' }}
                        onClick={() => document.getElementById('gradient-extra-color-input').click()}
                      ></div>
                      <input
                        id="gradient-extra-color-input"
                        type="color"
                        value={gradients.extraColor || '#8a2be2'}
                        onChange={(e) => handleGradientChange('extraColor', e.target.value)}
                      />
                      <input
                        type="text"
                        value={gradients.extraColor || '#8a2be2'}
                        onChange={(e) => handleGradientChange('extraColor', e.target.value)}
                        className="color-text-input"
                      />
                    </div>
                  </div>

                  <div className="gradient-position-picker">
                    <label>Position ({gradients.extraPosition})</label>
                    <input
                      type="range"
                      min="1"
                      max="99"
                      value={parseInt(gradients.extraPosition)}
                      onChange={(e) => handleGradientChange('extraPosition', `${e.target.value}%`)}
                      className="position-slider"
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="gradient-apply">
            <button 
              className="apply-gradient-button"
              onClick={() => {
                // Apply gradient to primary gradient and handle as a color change
                const gradientString = generateGradientString();
                themeGenerator.current.applyGradientToCurrentTheme(gradientString);

                // Mark primary as changed
                if (!colorsChanged.includes('primary')) {
                  setColorsChanged(prev => [...prev, 'primary']);
                }
              }}
            >
              Apply Gradient to Theme
            </button>
          </div>
        </div>
      )}

      {activeTab === 'css' && (
        <div className="css-registry-container">
          <h3>CSS Registry</h3>
          <p className="css-registry-description">
            Add custom CSS to selected files. Variables will be substituted across themes.
          </p>

          <div className="css-file-selector">
            <h4>Select CSS Files</h4>
            <div className="css-files-list">
              {availableCssFiles.map(file => (
                <div key={file} className="css-file-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={cssRegistry.selectedFiles.includes(file)}
                      onChange={() => toggleCssFile(file)}
                    />
                    {file}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="css-code-editor">
            <h4>CSS Code</h4>
            <p className="css-code-hint">
              Use var(--variable-name) for theme compatibility. Paste gradients directly from the Gradients tab.
            </p>
            <div className="css-available-variables">
              <details>
                <summary>Available Theme Variables</summary>
                <div className="variables-list">
                  <code>--primary-color</code>
                  <code>--secondary-color</code>
                  <code>--text-color</code>
                  <code>--background-color</code>
                  <code>--card-background</code>
                  <code>--border-color</code>
                  <code>--success-color</code>
                  <code>--danger-color</code>
                  <code>--warning-color</code>
                  <code>--info-color</code>
                  <code>--text-secondary</code>
                  <code>--gradient-primary</code>
                </div>
              </details>
            </div>
            <textarea
              value={cssRegistry.cssCode}
              onChange={handleCssCodeChange}
              placeholder=".my-class {
  color: var(--primary-color);
  background-color: var(--background-color);
  border: 1px solid var(--border-color);
}"
              rows={10}
              className="css-code-textarea"
            ></textarea>
          </div>

          <div className="css-registry-actions">
            <button 
              className="apply-css-button"
              onClick={applyCssToFiles}
              disabled={cssRegistry.selectedFiles.length === 0 || !cssRegistry.cssCode.trim()}
            >
              Apply CSS to Selected Files
            </button>

            {cssRegistry.status && (
              <div className="css-registry-status">
                {cssRegistry.status}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="theme-actions">
        {colorsChanged.length > 0 && (
          <button 
            className="apply-theme-button"
            onClick={applyTheme}
          >
            Apply New Theme
          </button>
        )}

        <button 
          className="reset-theme-button"
          onClick={resetAllColors}
          disabled={colorsChanged.length === 0}
        >
          Reset All Changes
        </button>
      </div>

      {saveStatus && (
        <div className={`save-status ${saveStatus.state}`}>
          {saveStatus.message}
        </div>
      )}
    </div>
  );
};

export default ThemeConfigurator;
