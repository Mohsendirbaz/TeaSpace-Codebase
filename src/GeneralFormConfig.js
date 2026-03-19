import React, { useState, useEffect, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useMatrixFormValues } from './Consolidated2';
import { faEdit, faCheck, faTimes, faSave, faUndo } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';
import { sensitivityActionRef } from './components/modules/SensitivityMonitor';
import FactualPrecedence from './components/find_factual_precedence/components/modules/FactualPrecedence/index';
// Import label references for reset functionality
import * as labelReferences from './utils/labelReferences';
import Popup from './components/modules/Efficacy';

/**
 * GeneralFormConfig Component
 * Handles configuration of form values, labels, and related settings
 * Compatible with matrix-based state management from Consolidated2.js
 */
const GeneralFormConfig = ({
                             formValues: propFormValues,
                             handleInputChange: propHandleInputChange,
                             version,
                             filterKeyword,
                             V: propV, toggleV: propToggleV,
                             R: propR, toggleR: propToggleR,
                             F: propF, toggleF: propToggleF,
                             RF: propRF, toggleRF: propToggleRF,
                             setVersion,
                             summaryItems,
                           }) => {
  const matrixFormValues = useMatrixFormValues();

  // Use matrix-based state management or props
  const formValues = propFormValues || (matrixFormValues && matrixFormValues.formMatrix) || {};
  const handleInputChange = propHandleInputChange || (matrixFormValues && matrixFormValues.handleInputChange);
  const V = propV || (matrixFormValues && matrixFormValues.V) || {};
  const R = propR || (matrixFormValues && matrixFormValues.R) || {};
  const F = propF || (matrixFormValues && matrixFormValues.F) || {};
  const RF = propRF || (matrixFormValues && matrixFormValues.RF) || {};
  const toggleV = propToggleV || (matrixFormValues && matrixFormValues.toggleV);
  const toggleR = propToggleR || (matrixFormValues && matrixFormValues.toggleR);
  const toggleF = propToggleF || (matrixFormValues && matrixFormValues.toggleF);
  const toggleRF = propToggleRF || (matrixFormValues && matrixFormValues.toggleRF);

  //--------------------------------------------------------------------------
  // STATE MANAGEMENT
  //--------------------------------------------------------------------------
  const [showPopup, setShowPopup] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ top: 0, left: 0 });
  const [selectedItemId, setSelectedItemId] = useState();
  const [updateStatus, setUpdateStatus] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Factual Precedence state
  const [showFactualPrecedence, setShowFactualPrecedence] = useState(false);
  const [factualPrecedencePosition, setFactualPrecedencePosition] = useState({ top: 0, left: 0 });
  const [factualItemId, setFactualItemId] = useState(null);

  // Label management state
  const [editingLabel, setEditingLabel] = useState(null);
  const [tempLabel, setTempLabel] = useState('');
  const [originalLabels, setOriginalLabels] = useState({});
  const [editedLabels, setEditedLabels] = useState({});

  //--------------------------------------------------------------------------
  // HELPER FUNCTIONS - Convert keys to specific numbering schemes
  //--------------------------------------------------------------------------
  // Get plant lifetime value for efficacy calculations
  const getLatestPlantLifetime = (formValues) => {
    if (!formValues) return 40;
    const filteredValues = Object.values(formValues).filter(item => item && item.id === 'plantLifetimeAmount10');
    return filteredValues.length > 0 ? filteredValues[0].value : 40;
  };

  // Get S parameter number (used for sensitivity analysis)
  const getSNumber = (key) => {
    const match = key.match(/Amount(\d+)/);
    if (!match) return null;

    const num = parseInt(match[1]);
    if (num >= 10 && num <= 84) return `S${num}`; // S10-S79
    return null;
  };

  // Get V parameter number (variable parameters)
  const getVNumber = (vAmountNum) => {
    const num = parseInt(vAmountNum);
    if (num >= 40 && num <= 49) return `V${num - 39}`;
    if (num >= 50 && num <= 59) return `V${num - 49}`;
    return null;
  };

  // Get R parameter number (rate parameters)
  const getRNumber = (rAmountNum) => {
    const num = parseInt(rAmountNum);
    if (num >= 50 && num <= 69) return `R${num - 59}`;
    if (num >= 50 && num <= 79) return `R${num - 69}`;
    return null;
  };

  // Get F parameter number (factor parameters)
  const getFNumber = (key) => {
    const match = key.match(/Amount(\d+)/);
    if (!match) return null;

    const num = parseInt(match[1]);
    if (num >= 34 && num <= 38) return `F${num - 33}`;
    return null;
  };

  // Get RF parameter number (fixed revenue parameters)
  const getRFNumber = (key) => {
    const match = key.match(/Amount(\d+)/);
    if (!match) return null;

    const num = parseInt(match[1]);
    if (num >= 80 && num <= 84) return `RF${num - 79}`;
    return null;
  };

  //--------------------------------------------------------------------------
  // SUMMARY ITEM HANDLING
  //--------------------------------------------------------------------------
  // Get final calculated value from summary items
  const getFinalResultValue = (itemId) => {
    if (!summaryItems || summaryItems.length === 0) return null;

    const summaryItem = summaryItems.find(item => item.id === itemId);
    return summaryItem ? summaryItem.finalResult : null;
  };

  //--------------------------------------------------------------------------
  // FORM ITEM PROCESSING
  //--------------------------------------------------------------------------
  // Transform form values into displayable items with appropriate metadata
  const formItems = formValues ? Object.keys(formValues)
      .filter((key) => key.includes(filterKeyword))
      .map((key) => {
        const vKey = key.includes('vAmount') ? getVNumber(key.replace('vAmount', '')) : null;
        const rKey = key.includes('rAmount') ? getRNumber(key.replace('rAmount', '')) : null;
        const fKey = getFNumber(key);
        const rfKey = getRFNumber(key);
        const sKey = getSNumber(key);
        return {
          id: key,
          vKey,
          rKey,
          fKey,
          rfKey,
          sKey,
          ...formValues[key]
        };
      }) : [];

  //--------------------------------------------------------------------------
  // LABEL MANAGEMENT FUNCTIONS
  //--------------------------------------------------------------------------
  // Store original labels when component mounts
  useEffect(() => {
    if (Object.keys(originalLabels).length === 0 && formValues) {
      const labels = {};
      Object.entries(formValues || {}).forEach(([key, value]) => {
        if (value && value.label) {
          labels[key] = value.label;
        }
      });
      setOriginalLabels(labels);
    }
  }, [formValues]);

  // Begin editing a label
  const handleLabelEdit = (itemId) => {
    setEditingLabel(itemId);
    setTempLabel(formValues && formValues[itemId] ? formValues[itemId].label : '');
  };

  // Cancel label editing
  const handleCancelEdit = () => {
    setEditingLabel(null);
    setTempLabel('');
  };

  // Save edited label locally
  const handleLabelSave = (itemId) => {
    handleInputChange({ target: { value: tempLabel } }, itemId, 'label');
    setEditedLabels(prev => ({ ...prev, [itemId]: true }));
    setEditingLabel(null);
    setUpdateStatus('Label saved locally - remember to update form');
    setTimeout(() => setUpdateStatus(''), 3000);
  };
  const [tempLabel_container] = useState({});
  // useEffect to be notified everytime handleLabelSave is called update tempLabel_container
  useEffect(() => {
    // This effect runs whenever editedLabels changes (from handleLabelSave)
    if (Object.keys(editedLabels).length > 0) {
      // Store the saved label in tempLabel_container
      const itemId = Object.keys(editedLabels).find(id => editedLabels[id]);
      if (itemId && tempLabel_container.current) {
        tempLabel_container.current[itemId] = tempLabel;
      }
    }
  }, [editedLabels, tempLabel, tempLabel_container]);
  // Update all edited labels to server
  const handleUpdateFormLabels = async () => {
    try {
      setIsUpdating(true);
      setUpdateStatus('Updating form labels...');

      const updates = {};
      if (formValues) {
        Object.keys(editedLabels).forEach(key => {
          if (formValues[key]) {
            updates[key] = {
              label: formValues[key].label,
              value: formValues[key].value,
              labelEdited: true // Flag to indicate the label was edited
            };
          }
        });
      }

      if (Object.keys(updates).length === 0) {
        setUpdateStatus('No edited labels to update');
        setIsUpdating(false);
        setTimeout(() => setUpdateStatus(''), 3000);
        return;
      }

      // Use matrix API if available, otherwise use direct axios call
      if (matrixFormValues && matrixFormValues.syncWithBackend) {
        const success = await matrixFormValues.syncWithBackend({ updates });
        if (success) {
          setEditedLabels({});
          setUpdateStatus(`${Object.keys(updates).length} labels updated successfully`);
          setTimeout(() => setUpdateStatus(''), 3000);
        } else {
          throw new Error('Matrix sync failed');
        }
      } else {
        const response = await axios.post('http://localhost:3060/api/update-form-values', { updates });

        if (response.data.success) {
          // Clear tracking after successful update
          setEditedLabels({});
          setUpdateStatus(`${Object.keys(updates).length} labels updated successfully`);
          setTimeout(() => setUpdateStatus(''), 3000);
        } else {
          throw new Error(response.data.message);
        }
      }
    } catch (error) {
      console.error('Update failed:', error);
      setUpdateStatus(`Update failed: ${error.message}`);
      setTimeout(() => setUpdateStatus(''), 3000);
    } finally {
      setIsUpdating(false);
    }
  };

  // Reset all labels to original values using labelReferences
  const handleResetLabels = async () => {
    if (window.confirm('Reset all labels and default values to original values?')) {
      // Check if matrix-based reset is available
      if (matrixFormValues && matrixFormValues.handleReset) {
        try {
          setIsUpdating(true);
          setUpdateStatus('Resetting form values using matrix state management...');

          // Use matrix-based reset
          await matrixFormValues.handleReset();

          setUpdateStatus('Reset complete: All items restored to original values');
          setIsUpdating(false);
          setEditedLabels({});
          setTimeout(() => setUpdateStatus(''), 3000);
        } catch (error) {
          console.error('Matrix reset failed:', error);
          setUpdateStatus(`Reset failed: ${error.message}`);
          setIsUpdating(false);
          setTimeout(() => setUpdateStatus(''), 3000);
        }
        return;
      }

      // Fallback to original reset method
      // First, reset labels locally
      const updatedLabels = {};
      if (formValues) {
        Object.entries(labelReferences.propertyMapping || {}).forEach(([key, label]) => {
          if (formValues[key]) {
            handleInputChange({ target: { value: label } }, key, 'label');

            // Also reset default values if available
            if (labelReferences.defaultValues && labelReferences.defaultValues[key] !== undefined) {
              handleInputChange({ target: { value: labelReferences.defaultValues[key] } }, key, 'value');
            }

            // Mark this label as edited so we can update the server
            updatedLabels[key] = true;
          }
        });
      }

      // Update the server with all reset values
      try {
        setIsUpdating(true);
        setUpdateStatus('Updating form with original values...');

        const updates = {};
        if (formValues) {
          Object.keys(updatedLabels).forEach(key => {
            if (formValues[key]) {
              updates[key] = {
                label: formValues[key].label,
                value: formValues[key].value,
                labelEdited: true // Flag to indicate the label was reset
              };
            }
          });
        }

        if (Object.keys(updates).length > 0) {
          // Use matrix API if available, otherwise use direct axios call
          if (matrixFormValues && matrixFormValues.syncWithBackend) {
            const success = await matrixFormValues.syncWithBackend({ updates });
            if (success) {
              setUpdateStatus(`Reset complete: ${Object.keys(updates).length} items restored to original values`);
            } else {
              throw new Error('Matrix sync failed');
            }
          } else {
            const response = await axios.post('http://localhost:3060/api/update-form-values', { updates });

            if (response.data.success) {
              setUpdateStatus(`Reset complete: ${Object.keys(updates).length} items restored to original values`);
            } else {
              throw new Error(response.data.message);
            }
          }
        } else {
          setUpdateStatus('No items to reset');
        }
      } catch (error) {
        console.error('Reset failed:', error);
        setUpdateStatus(`Reset failed: ${error.message}`);
      } finally {
        setIsUpdating(false);
        setEditedLabels({});
        setTimeout(() => setUpdateStatus(''), 3000);
      }
    }
  };

  //--------------------------------------------------------------------------
  // INPUT HANDLERS
  //--------------------------------------------------------------------------
  // Handle increment button click
  const handleIncrement = (itemId) => {
    if (!formValues || !formValues[itemId]) return;
    const item = formValues[itemId];
    const newValue = parseFloat(item.value) + parseFloat(item.step || 1);
    handleInputChange({ target: { value: newValue } }, itemId, 'value');
  };

  // Handle decrement button click
  const handleDecrement = (itemId) => {
    if (!formValues || !formValues[itemId]) return;
    const item = formValues[itemId];
    const newValue = parseFloat(item.value) - parseFloat(item.step || 1);
    handleInputChange({ target: { value: newValue } }, itemId, 'value');
  };

  // Handle schedule/efficacy button click
  const handleScheduleClick = (e, itemId) => {
    if (!formValues || !formValues[itemId]) return;

    const rect = e.target.getBoundingClientRect();
    setPopupPosition({
      top: rect.top + window.scrollY + 61.8,
      left: rect.left + rect.width + 1000,
    });
    setSelectedItemId(itemId);

    const latestPlantLifetime = getLatestPlantLifetime(formValues);
    const efficacyPeriod = formValues[itemId].efficacyPeriod || {};
    handleInputChange({ target: { value: latestPlantLifetime } }, itemId, 'efficacyPeriod', 'end');

    setShowPopup(true);
  };

  // FIXED: Factual precedence handlers
  const handleFactualPrecedenceClick = (event, itemId) => {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    // Calculate position relative to viewport with offset and boundary checking
    setFactualPrecedencePosition(() => {
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      // Default position (below the element)
      let top = rect.bottom + window.scrollY + 10; // 10px padding
      let left = rect.left + window.scrollX;

      // Right offset (add 300px to the right)
      left += 300;

      // Boundary checking (keep popup within viewport)
      const popupWidth = 550; // From CSS width
      const popupHeight = 400; // Estimated height

      // Adjust if would go off right edge
      if (left + popupWidth > viewportWidth) {
        left = viewportWidth - popupWidth - 20; // 20px margin
      }

      // Adjust if would go off bottom edge
      if (top + popupHeight > viewportHeight) {
        top = rect.top + window.scrollY - popupHeight - 10; // Show above instead
      }

      return { top, left };
    });
    // Set factual item ID separately from selected item ID
    setFactualItemId(itemId);
    setShowFactualPrecedence(true);
  };

  const handleCloseFactualPrecedence = () => {
    setShowFactualPrecedence(false);
    setFactualItemId(null);
  };

  //--------------------------------------------------------------------------
  // COMPONENT RENDERING
  //--------------------------------------------------------------------------
  return (
      <>
        {/* Label Management Section */}
        <div className="labels-section">
          <button
              className="update-button"
              onClick={handleUpdateFormLabels}
              disabled={isUpdating}
          >
            <FontAwesomeIcon icon={faSave} /> {isUpdating ? 'Updating...' : 'Update Form Labels'}
          </button>
          <button
              className="reset-button"
              onClick={handleResetLabels}
          >
            <FontAwesomeIcon icon={faUndo} /> Reset Labels
          </button>
          {updateStatus && <span className="update-status">{updateStatus}</span>}
        </div>

        {/* Form Items Display */}
        {formItems.map((item) => (
            <div key={item.id} className={`form-item-container ${item.id === selectedItemId ? 'highlighted-container' : ''}`}>

              {/* Parameter Type Checkboxes (V/R/F) */}
              <div className="checkbox-section">
                {item.vKey && (
                    <div className="checkbox-group">
                      <span className="checkbox-label">{item.vKey}</span>
                      <input
                          type="checkbox"
                          className="custom-checkbox"
                          checked={V[item.vKey] === 'on'}
                          onChange={() => toggleV(item.vKey)}
                      />
                    </div>
                )}
                {item.rKey && (
                    <div className="checkbox-group">
                      <span className="checkbox-label">{item.rKey}</span>
                      <input
                          type="checkbox"
                          className="custom-checkbox"
                          checked={R[item.rKey] === 'on'}
                          onChange={() => toggleR(item.rKey)}
                      />
                    </div>
                )}
                {item.fKey && (
                    <div className="checkbox-group">
                      <span className="checkbox-label">{item.fKey}</span>
                      <input
                          type="checkbox"
                          className="custom-checkbox"
                          checked={F[item.fKey] === 'on'}
                          onChange={() => toggleF(item.fKey)}
                      />
                    </div>
                )}
                {item.rfKey && (
                    <div className="checkbox-group">
                      <span className="checkbox-label">{item.rfKey}</span>
                      <input
                          type="checkbox"
                          className="custom-checkbox"
                          checked={RF[item.rfKey] === 'on'}
                          onChange={() => toggleRF(item.rfKey)}
                      />
                    </div>
                )}
              </div>

              {/* Main Input Section */}
              <div className="main-input-section">
                {/* Label and Icon */}
                <div className="label-container">
                  {matrixFormValues && matrixFormValues.iconMapping && matrixFormValues.iconMapping[item.id] && (
                      <FontAwesomeIcon icon={matrixFormValues.iconMapping[item.id]} className="input-icon" />
                  )}
                  {editingLabel === item.id ? (
                      <div className="edit-label-container">
                        <input
                            type="text"
                            value={tempLabel}
                            onChange={(e) => setTempLabel(e.target.value)}
                            className="label-edit-input"
                        />
                        <div className="edit-actions">
                          <FontAwesomeIcon
                              icon={faCheck}
                              onClick={() => handleLabelSave(item.id)}
                              className="edit-icon save"
                          />
                          <FontAwesomeIcon
                              icon={faTimes}
                              onClick={handleCancelEdit}
                              className="edit-icon cancel"
                          />
                        </div>
                      </div>
                  ) : (
                      <div className="label-text">
                        <FontAwesomeIcon
                            icon={faEdit}
                            onClick={() => handleLabelEdit(item.id)}
                            className="edit-icon"
                        />
                        <span>{item.label}</span>
                      </div>
                  )}
                </div>

                {/* Numeric Input Controls */}
                {item.type === 'number' && (
                    <div className="input-controls-section">
                      <div className="value-container">
                        <input
                            type="number"
                            id={item.id}
                            value={item.value !== undefined && item.value !== null && !isNaN(item.value) ? item.value : ''}
                            onChange={(e) => {
                              let value = parseFloat(e.target.value);
                              value = isNaN(value) ? null : value;
                              handleInputChange({ target: { value } }, item.id, 'value');
                            }}
                            className="value-input"
                            placeholder={item.placeholder}
                            step={item.step}
                        />

                        {/* Summary Results Display */}
                        {getFinalResultValue(item.id) !== null && (
                            <div className="final-result-container">
                      <span className="final-result-value">
                        Final: {getFinalResultValue(item.id).toFixed(2)}
                      </span>
                              <span className="final-result-indicator">
                        ← Summary Result
                      </span>
                            </div>
                        )}

                        <div className="increment-controls">
                          <button className="control-button1" onClick={() => handleDecrement(item.id)}>-</button>
                          <button className="control-button2" onClick={() => handleIncrement(item.id)}>+</button>
                        </div>
                      </div>

                      {/* Step Value Input */}
                      <div className="step-container">
                        <input
                            type="number"
                            id={`${item.id}-step`}
                            value={item.step !== undefined && item.step !== null && !isNaN(item.step) ? item.step : ''}
                            onChange={(e) => {
                              let step = parseFloat(e.target.value);
                              step = isNaN(step) ? '' : step;
                              handleInputChange({ target: { value: step } }, item.id, 'step');
                            }}
                            className="step-input"
                            placeholder="Step Value"
                        />
                      </div>

                      {/* Remarks Field */}
                      <div className="remarks-container">
                        <input
                            type="text"
                            id={`${item.id}-remarks`}
                            value={item.remarks || ''}
                            onChange={(e) => handleInputChange({ target: { value: e.target.value } }, item.id, 'remarks')}
                            placeholder="Add remarks"
                            className="remarks-input remarks-important"
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="action-buttons">
                        {/* Sensitivity Configuration */}
                        {item.sKey && (
                            <button
                                className="action-button-sensitivity"
                                onClick={() => {
                                  if (sensitivityActionRef.current) {
                                    // First enable the parameter
                                    sensitivityActionRef.current.toggleParameterEnabled(item.sKey);

                                    // Then open configuration panel with a slight delay to ensure state updates
                                    setTimeout(() => {
                                      sensitivityActionRef.current.openParameterDetails(item.sKey);
                                    }, 50);
                                  } else {
                                    console.warn("Sensitivity configuration is not available");
                                  }
                                }}
                            >
                              Configure Sensitivity
                            </button>
                        )}
                        <button
                            className="action-button-efficacy"
                            onClick={(e) => handleScheduleClick(e, item.id)}
                        >
                          Specify Efficacy Period
                        </button>
                        <button
                            className="action-button-factual"
                            onClick={(e) => handleFactualPrecedenceClick(e, item.id)}
                        >
                          Find Factual Precedence
                        </button>
                      </div>
                    </div>
                )}

                {/* Select Input Controls */}
                {item.type === 'select' && (
                    <div className="input-controls-section">
                      <div className="value-container">
                        <select
                            id={item.id}
                            value={item.value || ''}
                            onChange={(e) => handleInputChange(e, item.id, 'value')}
                            className="select-input"
                        >
                          {item.options.map((option, index) => (
                              <option key={index} value={option}>{option}</option>
                          ))}
                        </select>
                      </div>

                      {/* Remarks Field */}
                      <div className="remarks-container">
                        <input
                            type="text"
                            id={`${item.id}-remarks`}
                            value={item.remarks || ''}
                            onChange={(e) => handleInputChange({ target: { value: e.target.value } }, item.id, 'remarks')}
                            placeholder="Add remarks"
                            className="remarks-input remarks-important"
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="action-buttons">
                        {/* Sensitivity Configuration */}
                        {item.sKey && (
                            <button
                                className="action-button-sensitivity"
                                onClick={() => {
                                  if (sensitivityActionRef.current) {
                                    // First enable the parameter
                                    sensitivityActionRef.current.toggleParameterEnabled(item.sKey);

                                    // Then open configuration panel with a slight delay to ensure state updates
                                    setTimeout(() => {
                                      sensitivityActionRef.current.openParameterDetails(item.sKey);
                                    }, 50);
                                  } else {
                                    console.warn("Sensitivity configuration is not available");
                                  }
                                }}
                            >
                              Configure Sensitivity
                            </button>
                        )}
                        <button
                            className="action-button-efficacy"
                            onClick={(e) => handleScheduleClick(e, item.id)}
                        >
                          Specify Efficacy Period
                        </button>
                        <button
                            className="action-button-factual"
                            onClick={(e) => handleFactualPrecedenceClick(e, item.id)}
                        >
                          Find Factual Precedence
                        </button>
                      </div>
                    </div>
                )}
              </div>
            </div>
        ))}

        {/* Efficacy Popup */}
        {selectedItemId && (
            <Popup
                show={showPopup}
                position={popupPosition}
                onClose={() => {
                  setShowPopup(false);
                  setSelectedItemId(null); // Reset the selectedItemId to remove highlighting
                }}
                formValues={formValues}
                handleInputChange={handleInputChange}
                id={selectedItemId}
                onVersionChange={(newVersion) => setVersion(newVersion)}
                version={version}
                itemId={selectedItemId}
            />
        )}

        {/* Factual Precedence Popup - Moved outside the loop */}
        {showFactualPrecedence && (
            <FactualPrecedence
                show={showFactualPrecedence}
                position={factualPrecedencePosition}
                onClose={handleCloseFactualPrecedence}
                formValues={formValues}
                id={factualItemId}
                handleInputChange={handleInputChange}
            />
        )}
      </>
  );
};

export default GeneralFormConfig;
