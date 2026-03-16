import React, { useState, useEffect, useCallback, useMemo } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';
import '../../styles/HomePage.CSS/SensitivityMonitor.css';
import { useMatrixFormValues } from '../../Consolidated2';
import capacityTracker from '../../services/CapacityTrackingService';

/**
 * SensitivityMonitor component for configuring and managing sensitivity analysis parameters
 *
 * @param {Object} props
 * @param {Object} props.S - Sensitivity parameters state object
 * @param {Function} props.setS - Function to update sensitivity parameters
 * @param {string} props.version - Current version number
 * @param {string} props.activeTab - Currently active application tab
 */
// Create a ref to store the parameter actions for external access
const sensitivityActionRef = { current: null };

const SensitivityMonitor = ({ S, setS, version, activeTab }) => {
  // Get form values
  const { formMatrix: formValues } = useMatrixFormValues();

  // Component state
  const [isExpanded, setIsExpanded] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMode, setFilterMode] = useState('all');
  const [selectedParameter, setSelectedParameter] = useState(null);
  const [parameterDetails, setParameterDetails] = useState(null);
  const [usagePercentage, setUsagePercentage] = useState(0);

  // Mode color mapping for visual indication
  const modeColorMap = {
    percentage: 'mode-percentage',
    directvalue: 'mode-directvalue',
    absolutedeparture: 'mode-absolutedeparture',
    monteCarlo: 'mode-montecarlo'
  };

  // Modes available for sensitivity analysis
  const sensitivityModes = [
    { id: 'percentage', label: 'Percentage Change' },
    { id: 'directvalue', label: 'Direct Values - used directly for calculation and visualization'},
    { id: 'absolutedeparture', label: 'Absolute Departure - added to and subtracted from base values' },
    { id: 'monteCarlo', label: 'Monte Carlo - Coming Soon!' }
  ];

  // Comparison types for parameter relationships
  const comparisonTypes = [
    { id: 'primary', label: 'As primary (x axis)' },
    { id: 'As primary (y axis)', label: 'As primary (y axis)' },
    { id: 'none', label: 'No Comparison' },
    { id: 'ratio', label: 'Ratio (A:B)' },
    { id: 'difference', label: 'Difference (A-B)' },
    { id: 'product', label: 'Product (A×B)' }
  ];

  // Filter parameters based on search term and filter mode
  const filteredParameters = useMemo(() => {
    // Check if search term contains comma-separated values
    if (searchTerm.includes(',')) {
      // Split by comma and clean each term (trim whitespace, remove 'S' if present)
      const searchTerms = searchTerm.split(',').map(term => {
        const cleanTerm = term.trim().toUpperCase();
        return cleanTerm.startsWith('S') ? cleanTerm : `S${cleanTerm}`;
      });

      // Filter parameters that match any of the search terms
      return Object.entries(S).filter(([key]) => {
        return searchTerms.some(term => key.toUpperCase() === term);
      });
    }

    // Default search behavior (single term)
    return Object.entries(S).filter(([key, value]) => {
      // Extract parameter number for categorization
      const paramNumber = parseInt(key.replace('S', ''), 10);

      // Match search term - case insensitive
      const matchesSearch = searchTerm === '' ||
          key.toUpperCase().includes(searchTerm.toUpperCase()) ||
          (searchTerm.toUpperCase().startsWith('S') ?
              key.toUpperCase().includes(searchTerm.toUpperCase()) :
              key.toUpperCase().includes(`S${searchTerm.toUpperCase()}`));

      // Match filter mode
      let matchesFilter = filterMode === 'all';

      if (filterMode === 'enabled' && value.enabled) {
        matchesFilter = true;
      } else if (filterMode === 'disabled' && !value.enabled) {
        matchesFilter = true;
      } else if (filterMode === 'project' && paramNumber >= 10 && paramNumber <= 19) {
        matchesFilter = true;
      } else if (filterMode === 'loan' && paramNumber >= 20 && paramNumber <= 29) {
        matchesFilter = true;
      } else if (filterMode === 'rates' && paramNumber >= 30 && paramNumber <= 39) {
        matchesFilter = true;
      } else if (filterMode === 'quantities' && paramNumber >= 40 && paramNumber <= 49) {
        matchesFilter = true;
      } else if (filterMode === 'costs' && paramNumber >= 50 && paramNumber <= 59) {
        matchesFilter = true;
      }

      return matchesSearch && matchesFilter;
    });
  }, [S, searchTerm, filterMode]);

  // Update the formatParameterValues function to apply mode-specific styling
  const formatParameterValues = useCallback((values, mode) => {
    if (!values || values.length === 0) return null;

    // Handle both numeric and string values (like F/V boxes)
    return values.map(v => {
      if (typeof v === 'number' || !isNaN(v)) {
        return Number(v).toFixed(2);
      }
      return v;
    }).join(', ');
  }, []);

  // Get parameter name from key using formValues mapping
  const getParameterName = useCallback((key) => {
    if (!key) return '';

    const numericPart = key.replace(/\D/g, '');

    // Try property names from different sources based on numeric part
    for (const formKey in formValues) {
      if (formKey.includes(`Amount${numericPart}`)) {
        return formValues[formKey].label || key;
      }
    }

    return key;
  }, [formValues]);

  // Handle enabling/disabling a parameter
  const toggleParameterEnabled = useCallback((key) => {
    setS(prevS => ({
      ...prevS,
      [key]: {
        ...prevS[key],
        enabled: !prevS[key].enabled
      }
    }));
  }, [setS]);

  // Open parameter details panel
  const openParameterDetails = useCallback((key) => {
    setSelectedParameter(key);
    setParameterDetails({...S[key]});
  }, [S]);

  // Update parameter details and reflect changes in main display
  const updateParameterDetails = useCallback((field, value) => {
    setParameterDetails(prev => ({
      ...prev,
      [field]: value
    }));

    // Instantly reflect changes in main display if selectedParameter exists
    if (selectedParameter) {
      setS(prevS => ({
        ...prevS,
        [selectedParameter]: {
          ...prevS[selectedParameter],
          [field]: value
        }
      }));
    }
  }, [selectedParameter, setS]);

  // Save parameter changes
  const saveParameterChanges = useCallback(() => {
    if (!selectedParameter || !parameterDetails) return;

    setS(prevS => ({
      ...prevS,
      [selectedParameter]: {
        ...parameterDetails
      }
    }));

    // Close the details panel
    setSelectedParameter(null);
    setParameterDetails(null);
  }, [selectedParameter, parameterDetails, setS]);

  // Cancel parameter editing
  const cancelParameterEditing = useCallback(() => {
    // Revert changes
    if (selectedParameter) {
      setS(prevS => ({
        ...prevS,
        [selectedParameter]: {
          ...prevS[selectedParameter]
        }
      }));
    }

    // Close the details panel
    setSelectedParameter(null);
    setParameterDetails(null);
  }, [selectedParameter, setS]);

  // Helper to add a value to a parameter's values array
  const addParameterValue = useCallback(() => {
    if (!parameterDetails || !selectedParameter) return;

    const newValues = [...parameterDetails.values, 0];

    // Update both parameter details and main state
    setParameterDetails(prev => ({
      ...prev,
      values: newValues
    }));

    setS(prevS => ({
      ...prevS,
      [selectedParameter]: {
        ...prevS[selectedParameter],
        values: newValues
      }
    }));
  }, [parameterDetails, selectedParameter, setS]);

  // Helper to remove a value from a parameter's values array
  const removeParameterValue = useCallback((index) => {
    if (!parameterDetails || !selectedParameter) return;

    const newValues = parameterDetails.values.filter((_, i) => i !== index);

    // Update both parameter details and main state
    setParameterDetails(prev => ({
      ...prev,
      values: newValues
    }));

    setS(prevS => ({
      ...prevS,
      [selectedParameter]: {
        ...prevS[selectedParameter],
        values: newValues
      }
    }));
  }, [parameterDetails, selectedParameter, setS]);

  // Update a specific value in the values array
  const updateParameterValue = useCallback((index, value) => {
    if (!parameterDetails || !selectedParameter) return;

    const newValue = parseFloat(value);
    if (isNaN(newValue)) return;

    const newValues = [...parameterDetails.values];
    newValues[index] = newValue;

    // Update both parameter details and main state
    setParameterDetails(prev => ({
      ...prev,
      values: newValues
    }));

    setS(prevS => ({
      ...prevS,
      [selectedParameter]: {
        ...prevS[selectedParameter],
        values: newValues
      }
    }));
  }, [parameterDetails, selectedParameter, setS]);

  // Reset a single parameter to initial state
  const resetParameter = useCallback((key) => {
    setS(prevS => ({
      ...prevS,
      [key]: {
        mode: null,
        values: [],
        compareToKey: '',
        comparisonType: null,
        waterfall: false,
        bar: false,
        point: false,
        enabled: false
      }
    }));
  }, [setS]);

  // Reset all sensitivity parameters to initial state
  const resetAllParameters = useCallback(() => {
    setS(prevS => {
      const newS = {};
      // Reset all S parameters to initial state
      for (let i = 10; i <= 84; i++) {
        const key = `S${i}`;
        newS[key] = {
          mode: null,
          values: [],
          compareToKey: '',
          comparisonType: null,
          waterfall: false,
          bar: false,
          point: false,
          enabled: false
        };
      }
      return newS;
    });
  }, [setS]);

  // Determine if the component should be visible based on activeTab
  const isVisible = useMemo(() => {
    return ['Input', 'Case1', 'Case2', 'Case3', 'Scaling'].includes(activeTab);
  }, [activeTab]);

  // Store actions in the ref for external access
  useEffect(() => {
    sensitivityActionRef.current = {
      toggleParameterEnabled,
      openParameterDetails
    };
  }, [toggleParameterEnabled, openParameterDetails]);

  // Update usage percentage whenever S changes
  useEffect(() => {
    const percentage = capacityTracker.updateSensitivityUsage(S);
    setUsagePercentage(percentage);
  }, [S]);

  // If not visible, don't render anything
  if (!isVisible) return null;

  return (
      <div className={`sensitivity-monitor-s ${isExpanded ? 'expanded' : 'collapsed'}`}>
        <div className="monitor-header-s">
          {isExpanded ? (
              <>
                <div className="header-content">
                  <h3>Sensitivity Analysis</h3>
                  <div className="usage-indicator">
                    <div className="usage-label">
                      Usage: {usagePercentage}% of capacity
                    </div>
                    <div className="usage-bar">
                      <div 
                        className="usage-fill" 
                        style={{ 
                          width: `${usagePercentage}%`,
                          backgroundColor: usagePercentage > 90 ? '#ff4d4d' : 
                                          usagePercentage > 70 ? '#ffaa33' : 
                                          '#4caf50'
                        }}
                      ></div>
                    </div>
                    <div className="usage-details">
                      {capacityTracker.getUsageCount('sensitivityVariables')} of {capacityTracker.getCapacityLimit('sensitivityVariables')} variables enabled
                    </div>
                  </div>
                </div>
                <button
                    className="collapse-button"
                    onClick={() => setIsExpanded(false)}
                    aria-label="Collapse panel"
                >
                  ◀
                </button>
              </>
          ) : (
              <button
                  className="expand-button"
                  onClick={() => setIsExpanded(true)}
                  aria-label="Expand panel"
              >
                <span className="vertical-text"></span>
              </button>
          )}
        </div>

        {isExpanded && (
            <div className="monitor-content-s">
              <div className="monitor-toolbar-s">
                <input
                    type="text"
                    placeholder="Search parameters..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                />

                <select
                    value={filterMode}
                    onChange={(e) => setFilterMode(e.target.value)}
                    className="filter-select"
                >
                  <option value="all">All Parameters</option>
                  <option value="enabled">Enabled</option>
                  <option value="disabled">Disabled</option>
                  <option value="project">Project Settings (10-19)</option>
                  <option value="loan">Loan Settings (20-29)</option>
                  <option value="rates">Rate Settings (30-39)</option>
                  <option value="quantities">Process Quantities (40-49)</option>
                  <option value="costs">Process Costs (50-59)</option>
                </select>

                <button
                    className="reset-button"
                    onClick={resetAllParameters}
                    title="Reset all sensitivity parameters"
                >
                  Reset All
                </button>
              </div>

              <div className="parameters-container-s">
                {filteredParameters.length === 0 ? (
                    <div className="empty-state">
                      No sensitivity parameters match your criteria
                    </div>
                ) : (
                    <ul className="parameters-list">
                      {filteredParameters.map(([key, value]) => (
                          <li key={key} className={`parameter-item-s ${value.enabled ? 'enabled' : 'disabled'}`}>
                            <div className="parameter-header-s">
                              <div className="parameter-info">
                                <span className="parameter-key">{key}</span> <br />
                                <span className="parameter-name">{getParameterName(key)}</span>
                              </div>

                              <div className="parameter-controls-s">
                                <label className="toggle-label">
                                  <input
                                      type="checkbox"
                                      checked={value.enabled}
                                      onChange={() => toggleParameterEnabled(key)}
                                      className="toggle-checkbox"
                                  />
                                  <span className="toggle-slider"></span>
                                </label>

                                <div className="parameter-actions">
                                  <button
                                      className="edit-button"
                                      onClick={() => openParameterDetails(key)}
                                      disabled={!value.enabled}
                                      title="Configure parameter"
                                  >
                                    Configure
                                  </button>
                                  <button
                                      className="parameter-reset-button"
                                      onClick={() => resetParameter(key)}
                                      disabled={!value.enabled}
                                      title="Reset parameter"
                                  >
                                    Reset
                                  </button>
                                </div>
                              </div>
                            </div>

                            {value.enabled && (
                                <div className="parameter-summary-s">
                                  <div className="parameter-mode">
                                    <span className="label">Mode:</span>
                                    <span className={`value ${value.mode ? modeColorMap[value.mode] : ''}`}>
                            {value.mode ?
                                sensitivityModes.find(m => m.id === value.mode)?.label || value.mode
                                : 'Not configured'}
                          </span>
                                  </div>

                                  {value.values.length > 0 && (
                                      <div className="parameter-values">
                                        <span className="label">Values:</span>
                                        <span className={`value values-display ${value.mode ? `mode-${value.mode}` : ''}`}>
      {formatParameterValues(value.values)}
    </span>
                                      </div>
                                  )}

                                  {value.compareToKey && (
                                      <div className="parameter-comparison">
                                        <span className="label">Compared to:</span>
                                        <span className="value">
                              {getParameterName(value.compareToKey)}
                            </span>
                                      </div>
                                  )}

                                  {value.comparisonType && value.comparisonType !== 'none' && (
                                      <div className="parameter-comparison">
                                        <span className="label">Comparison Type:</span>
                                        <span className="value">
                              {comparisonTypes.find(t => t.id === value.comparisonType)?.label || value.comparisonType}
                            </span>
                                      </div>
                                  )}

                                  <div className="parameter-plots">
                                    <div className="plot-indicators">
                                      {value.waterfall && (
                                          <div className="plot-item">
                                            <span className="plot-box waterfall"></span>
                                            <span className="plot-label">Waterfall</span>
                                          </div>
                                      )}
                                      {value.bar && (
                                          <div className="plot-item">
                                            <span className="plot-box bar"></span>
                                            <span className="plot-label">Bar</span>
                                          </div>
                                      )}
                                      {value.point && (
                                          <div className="plot-item">
                                            <span className="plot-box point"></span>
                                            <span className="plot-label">Point</span>
                                          </div>
                                      )}
                                      {!value.waterfall && !value.bar && !value.point && (
                                          <span className="no-plots"></span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                            )}
                          </li>
                      ))}
                    </ul>
                )}
              </div>

              {/* Parameter details modal */}
              {selectedParameter && parameterDetails && (
                  <div className="parameter-modal">
                    <div className="modal-content">
                      <div className="modal-header">
                        <h4>Configure {getParameterName(selectedParameter)}</h4>
                        <button
                            className="close-button"
                            onClick={cancelParameterEditing}
                            aria-label="Close"
                        >
                          ×
                        </button>
                      </div>

                      <div className="modal-body">
                        <div className="form-group">
                          <label htmlFor="sensitivity-mode">Sensitivity Mode</label>
                          <select
                              id="sensitivity-mode"
                              value={parameterDetails.mode || ''}
                              onChange={(e) => updateParameterDetails('mode', e.target.value)}
                              className="form-control"
                          >
                            <option value="">Select a mode</option>
                            {sensitivityModes.map(mode => (
                                <option
                                    key={mode.id}
                                    value={mode.id}
                                    className={`mode-${mode.id}`}
                                >
                                  {mode.label}
                                </option>
                            ))}
                          </select>
                        </div>

                        {parameterDetails.mode && (
                            <>
                              <div className="form-group plot-controls">
                                <label>Plot Types</label>
                                <div className="plot-selection">
                                  {parameterDetails.waterfall && (
                                      <div className="plot-selection-item waterfall">
                                        Waterfall
                                      </div>
                                  )}
                                  {parameterDetails.bar && (
                                      <div className="plot-selection-item bar">
                                        Bar
                                      </div>
                                  )}
                                  {parameterDetails.point && (
                                      <div className="plot-selection-item point">
                                        Point
                                      </div>
                                  )}
                                </div>
                                <div className="plot-checkbox-group">
                                  <label className="toggle-label">
                                    <input
                                        type="checkbox"
                                        checked={parameterDetails.waterfall}
                                        onChange={(e) => updateParameterDetails('waterfall', e.target.checked)}
                                        className="toggle-checkbox"
                                    />
                                    <span className="toggle-slider"></span>
                                    Waterfall
                                  </label>
                                  <label className="toggle-label">
                                    <input
                                        type="checkbox"
                                        checked={parameterDetails.bar}
                                        onChange={(e) => updateParameterDetails('bar', e.target.checked)}
                                        className="toggle-checkbox"
                                    />
                                    <span className="toggle-slider"></span>
                                    Bar
                                  </label>
                                  <label className="toggle-label">
                                    <input
                                        type="checkbox"
                                        checked={parameterDetails.point}
                                        onChange={(e) => updateParameterDetails('point', e.target.checked)}
                                        className="toggle-checkbox"
                                    />
                                    <span className="toggle-slider"></span>
                                    Point
                                  </label>
                                </div>
                              </div>

                              <div className="form-group">
                                <label>Parameter Values</label>
                                <div className="values-container">
                                  {parameterDetails.values.length === 0 ? (
                                      <div className="empty-values">No values configured</div>
                                  ) : (
                                      <ul className="values-list">
                                        {parameterDetails.values.map((value, index) => (
                                            <li key={index} className="value-item">
                                              <input
                                                  type="number"
                                                  value={value}
                                                  onChange={(e) => updateParameterValue(index, e.target.value)}
                                                  className="value-input"
                                                  step="0.01"
                                              />
                                              <button
                                                  className="remove-value-button"
                                                  onClick={() => removeParameterValue(index)}
                                                  aria-label="Remove value"
                                              >
                                                -
                                              </button>
                                            </li>
                                        ))}
                                      </ul>
                                  )}

                                  <button
                                      className="add-value-button"
                                      onClick={addParameterValue}
                                  >
                                    Add Value
                                  </button>
                                </div>
                              </div>

                              <div className="form-group">
                                <label htmlFor="comparison-parameter">Compare To Parameter</label>
                                <select
                                    id="comparison-parameter"
                                    value={parameterDetails.compareToKey || ''}
                                    onChange={(e) => updateParameterDetails('compareToKey', e.target.value)}
                                    className="form-control"
                                >
                                  <option value="">No comparison</option>
                                  {Object.keys(S)
                                      .filter(key => key !== selectedParameter)
                                      .map(key => {
                                        // Get the numeric part of the key (e.g., "10" from "S10")
                                        const numericPart = key.replace(/\D/g, '');

                                        // Find the matching form value with the label
                                        let label = key;
                                        for (const formKey in formValues) {
                                          if (formKey.includes(`Amount${numericPart}`)) {
                                            label = formValues[formKey].label || key;
                                            break;
                                          }
                                        }

                                        return (
                                            <option key={key} value={key}>
                                              {key} - {label}
                                            </option>
                                        );
                                      })
                                  }

                                  {/* Manually append S80 to S89 */}
                                  {[...Array(10)].map((_, i) => {
                                    const key = `S${80 + i}`;
                                    return (
                                        <option key={key} value={key}>
                                          {key}
                                        </option>
                                    );
                                  })}
                                </select>
                              </div>


                              {parameterDetails.compareToKey && (
                                  <div className="form-group">
                                    <label htmlFor="comparison-type">Comparison Type</label>
                                    <select
                                        id="comparison-type"
                                        value={parameterDetails.comparisonType || 'none'}
                                        onChange={(e) => updateParameterDetails('comparisonType', e.target.value)}
                                        className="form-control"
                                    >
                                      {comparisonTypes.map(type => (
                                          <option key={type.id} value={type.id}>
                                            {type.label}
                                          </option>
                                      ))}
                                    </select>
                                  </div>
                              )}
                            </>
                        )}
                      </div>

                      <div className="modal-footer">
                        <button
                            className="cancel-button"
                            onClick={cancelParameterEditing}
                        >
                          Cancel
                        </button>
                        <button
                            className="save-button"
                            onClick={saveParameterChanges}
                        >
                          Save Changes
                        </button>
                      </div>
                    </div>
                  </div>
              )}
            </div>
        )}
      </div>
  );
};

export { SensitivityMonitor as default, sensitivityActionRef };
