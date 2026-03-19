import React, { useEffect, useState, useRef } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';

const Popup = ({ show, position, onClose, formValues, handleInputChange, id, version, itemId, onVersionChange}) => {
  const [sliderValues, setSliderValues] = useState([1, 40]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const popupRef = useRef(null);

  const getPlantLifetime = () => {
    const plantLifetimeItem = Object.values(formValues)
      .find(item => item.id === 'plantLifetimeAmount10');
    const value = plantLifetimeItem?.value;
    return value !== undefined && value !== null && !isNaN(value) 
      ? Math.max(1, parseInt(value)) 
      : 40;
  };

  // Add click outside handler
  useEffect(() => {
    if (show) {
      const handleClickOutside = (event) => {
        if (popupRef.current && !popupRef.current.contains(event.target)) {
          onClose();
        }
      };

      document.addEventListener('mousedown', handleClickOutside);

      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [show, onClose]);

  useEffect(() => {
    const currentPlantLifetime = getPlantLifetime();

    setSliderValues(prev => {
      const newEnd = Math.min(prev[1], currentPlantLifetime);
      const newStart = Math.min(prev[0], newEnd);

      handleInputChange(
        { target: { value: newStart } },
        id,
        'efficacyPeriod',
        'start'
      );
      handleInputChange(
        { target: { value: newEnd } },
        id,
        'efficacyPeriod',
        'end'
      );

      return [newStart, newEnd];
    });
  }, [formValues['plantLifetimeAmount10']?.value]);

  useEffect(() => {
    const currentPlantLifetime = getPlantLifetime();
    const efficacyPeriod = formValues[id]?.efficacyPeriod || {};

    const start = efficacyPeriod.start?.value;
    const end = efficacyPeriod.end?.value;

    const newEnd = end !== undefined 
      ? Math.min(end, currentPlantLifetime) 
      : currentPlantLifetime;
    const newStart = start !== undefined 
      ? Math.max(1, Math.min(start, newEnd)) 
      : 1;

    setSliderValues([newStart, newEnd]);
  }, [id]);

  const handleSliderChange = (index, value) => {
    const currentPlantLifetime = getPlantLifetime();
    const newValue = Math.min(
      Math.max(1, parseInt(value) || 1),
      currentPlantLifetime
    );

    setSliderValues(prev => {
      const newValues = [...prev];
      if (index === 0) {
        newValues[0] = Math.min(newValue, newValues[1]);
      } else {
        newValues[1] = Math.max(newValue, newValues[0]);
      }

      handleInputChange(
        { target: { value: newValues[0] } },
        id,
        'efficacyPeriod',
        'start'
      );
      handleInputChange(
        { target: { value: newValues[1] } },
        id,
        'efficacyPeriod',
        'end'
      );

      return newValues;
    });
  };

  const handleSubmitParameter = async (itemId) => {
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    const item = formValues[itemId];
    if (!item || !item.value) {
      setSubmitError('Parameter value is required');
      setIsSubmitting(false);
      return;
    }

    const filteredValue = {
      id: item.id,
      value: item.value,
      start: sliderValues[0],
      end: sliderValues[1],
      remarks: item.remarks || '',

    };

    try {
      const response = await fetch(`http://127.0.0.1:3040/append/${version}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filteredValue }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const result = await response.text();
      console.log('Parameter submitted successfully:', result);
      setSubmitSuccess(true);

      setTimeout(() => {
        const successMessage = document.querySelector('.success-message');
        if (successMessage) {
            successMessage.classList.add('fading');
        }
    }, 500);
    setTimeout(() => {
      onClose();
  }, 1500);
    } catch (error) {
      console.error('Error submitting parameter:', error);
      setSubmitError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    const currentPlantLifetime = getPlantLifetime();
    const newValues = [1, currentPlantLifetime];

    setSliderValues(newValues);
    handleInputChange(
      { target: { value: 1 } },
      id,
      'efficacyPeriod',
      'start'
    );
    handleInputChange(
      { target: { value: currentPlantLifetime } },
      id,
      'efficacyPeriod',
      'end'
    );
  };

  const getPercentages = () => {
    const currentPlantLifetime = getPlantLifetime();
    const rangeSize = currentPlantLifetime - 1;

    const adjustedEnd = Math.min(sliderValues[1], currentPlantLifetime);
    const adjustedStart = Math.min(sliderValues[0], adjustedEnd);

    const startPercent = ((adjustedStart - 1) / rangeSize) * 100;
    const widthPercent = ((adjustedEnd - adjustedStart) / rangeSize) * 100;

    return {
      startPercent: Math.max(0, Math.min(100, startPercent)),
      widthPercent: Math.max(0, Math.min(100 - startPercent, widthPercent))
    };
  };

  if (!show) return null;

  const currentPlantLifetime = getPlantLifetime();
  const { startPercent, widthPercent } = getPercentages();

  // Calculate adjusted position (move left by 3x the popup width)
  const adjustedPosition = {
    top: position.top,
    left: position.left - 1200 // 3 * 400px (popup width from CSS)
  };

  return (
    <div 
      ref={popupRef}
      className={`popup-container ${show ? 'active-popup' : ''} ${isClosing ? 'closing' : ''}`} 
      style={{
          top: adjustedPosition.top,
          left: adjustedPosition.left
      }}
    >
      <div className="popup-content">
        <button className="popup-close" onClick={onClose}>×</button>
        <div className="duration-display">
          Duration: {sliderValues[1] - sliderValues[0] + 1} years
          <div className="plant-lifetime">Plant Lifetime: {currentPlantLifetime} years</div>  
        </div>

        <div className="slider-container">
          <div>
            <label className="slider-label">Start Year</label>
            <input
              type="range"
              min="1"
              max={currentPlantLifetime}
              value={sliderValues[0]}
              onChange={(e) => handleSliderChange(0, e.target.value)}
              className="slider-input"
            />
            <div className="slider-value">{sliderValues[0]}</div>
          </div>

          <div>
            <label className="slider-label">End Year (Exclusive)</label>
            <input
              type="range"
              min="1"
              max={currentPlantLifetime}
              value={sliderValues[1]}
              onChange={(e) => handleSliderChange(1, e.target.value)}
              className="slider-input"
            />
            <div className="slider-value">{sliderValues[1]}</div>
          </div>
        </div>

        <div className="timeline-bar">
          <div
            className="timeline-highlight"
            style={{
              left: `${startPercent}%`,
              width: `${widthPercent}%`
            }}
          >
            <span className="timeline-marker" style={{ left: '7px' }}>
              {sliderValues[0]}
            </span>
            <span className="timeline-marker" style={{ right: 0 }}>
              {sliderValues[1]}
            </span>
          </div>

        </div>

        {submitSuccess && (
          <div className="success-message">
            Parameter submitted successfully
          </div>
        )}

        {submitError && (
          <div className="error-message">
            Error: {submitError}
          </div>
        )}
      </div>

      <div className="popup-footer">
      <div className="version-input-container">
        <input
          type="text"
          value={version}
          onChange={(e) => onVersionChange(e.target.value)}
          className="version-input"
          placeholder="Enter version"
        />
      </div>
        <button
  onClick={() => handleSubmitParameter(itemId)}
  disabled={isSubmitting}
          className="button button-primary"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Parameter'}
        </button>
        <button
          onClick={handleReset}
          className="button button-secondary"
          disabled={isSubmitting}
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default Popup;
