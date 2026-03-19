import React, { useCallback } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';

const ProcessingPanel = ({
  status,
  progress,
  messages,
  error,
  onStart,
  onCancel,
  onReset,
  disabled,
  showReset
}) => {
  const renderStatusIndicator = useCallback(() => {
    const statusConfig = {
      idle: {
        label: 'Ready',
        className: 'status-indicator--idle'
      },
      processing: {
        label: 'Processing...',
        className: 'status-indicator--processing'
      },
      complete: {
        label: 'Complete',
        className: 'status-indicator--complete'
      },
      error: {
        label: 'Error',
        className: 'status-indicator--error'
      }
    };

    const config = statusConfig[status] || statusConfig.idle;

    return (
      <div className={`status-indicator ${config.className}`}>
        <span className="status-indicator__label">{config.label}</span>
        {status === 'processing' && (
          <span className="status-indicator__progress">
            {Math.round(progress)}%
          </span>
        )}
      </div>
    );
  }, [status, progress]);

  const renderProgressBar = useCallback(() => {
    if (status !== 'processing') return null;

    return (
      <div className="processing-panel__progress">
        <div 
          className="processing-panel__progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
    );
  }, [status, progress]);

  const renderMessages = useCallback(() => {
    return (
      <div className="processing-panel__messages" role="log">
        {messages.map((message, index) => (
          <div 
            key={index}
            className={`processing-panel__message ${
              message.includes('Error') ? 'error' : ''
            }`}
          >
            <span className="message-timestamp">
              {new Date().toLocaleTimeString()}
            </span>
            <span className="message-text">{message}</span>
          </div>
        ))}
        {error && (
          <div className="processing-panel__error">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error}</span>
          </div>
        )}
      </div>
    );
  }, [messages, error]);

  const isProcessing = status === 'processing';

  return (
    <div className="processing-panel">
      <div className="processing-panel__header">
        <h3 className="processing-status-title">Processing Status</h3>
        {renderStatusIndicator()}
      </div>

      {renderProgressBar()}

      <div className="processing-panel__content">
        {renderMessages()}
      </div>

      <div className="processing-panel__actions">
        <button
          className={`action-button-pp ${isProcessing ? 'cancel' : 'start'}`}
          onClick={isProcessing ? onCancel : onStart}
          disabled={disabled || (isProcessing && status === 'complete')}
        >
          {isProcessing ? 'Cancel' : 'Start Consolidation'}
        </button>

        {status === 'complete' && (
          <div className="processing-panel__summary">
            <span className="summary-icon">✓</span>
            <span className="summary-text">
              Successfully consolidated {messages.length} CFA versions
            </span>
          </div>
        )}

        {error && (
          <div className="processing-panel__retry">
            <button
              className="retry-button"
              onClick={onStart}
              disabled={isProcessing}
            >
              Retry
            </button>
          </div>
        )}

        {showReset && (
          <button
            className="action-button-pp reset"
            onClick={onReset}
            disabled={isProcessing}
          >
            Reset
          </button>
        )}
      </div>

      {status === 'processing' && (
        <div className="processing-panel__info">
          <div className="info-item">
            <span className="info-label">Elapsed Time:</span>
            <span className="info-value">00:00:00</span>
          </div>
          <div className="info-item">
            <span className="info-label">Estimated Time:</span>
            <span className="info-value">Calculating...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessingPanel;
