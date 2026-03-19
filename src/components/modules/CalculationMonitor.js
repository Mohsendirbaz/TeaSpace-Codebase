import React, { useState, useEffect, useRef } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';

/**
 * Enhanced CalculationMonitor component that displays real-time updates during price optimization
 * and sensitivity analysis with support for matrix-based formulation
 *
 * @param {Object} props
 * @param {Array} props.selectedVersions - Array of versions being processed
 * @param {Function} props.updatePrice - Function to update price in parent component
 * @param {Boolean} props.isActive - Whether the monitor is active/visible
 * @param {Object} props.versionsInfo - Object containing version information (from matrix)
 * @param {Object} props.zonesInfo - Object containing zone information (from matrix)
 * @param {String} props.currentVersion - Current version number or ID
 * @param {Boolean} props.isSensitivity - Whether this is a sensitivity analysis or regular calculation
 * @param {Function} props.onComplete - Callback when calculation completes
 */
const CalculationMonitor = ({
                              selectedVersions,
                              updatePrice,
                              isActive,
                              currentVersion,
                              versionsInfo = {},
                              zonesInfo = {},
                              isSensitivity = false,
                              onComplete = () => {}
                            }) => {
  // State for storing monitoring data for each version
  const [monitorData, setMonitorData] = useState({});

  // State for tracking matrix-specific information
  const [matrixInfo, setMatrixInfo] = useState({
    activeVersions: [],
    activeZones: [],
    parameterUpdates: {}
  });

  // Refs to store EventSource connections
  const eventSourcesRef = useRef({});

  // Track completed calculations for callback
  const completedCalculationsRef = useRef({});

  useEffect(() => {
    // Only set up monitoring if component is active
    if (!isActive) return;

    // Define versions to monitor - use matrix version IDs if available
    let versionsToMonitor = [];

    if (selectedVersions && selectedVersions.length > 0) {
      versionsToMonitor = selectedVersions;
    } else if (versionsInfo && versionsInfo.list && versionsInfo.list.length > 0) {
      // Use active version from matrix if available
      versionsToMonitor = [versionsInfo.active || versionsInfo.list[0]];
    } else {
      // Fallback to numeric version
      versionsToMonitor = [parseInt(currentVersion, 10)];
    }

    console.log('Setting up monitoring for versions:', versionsToMonitor);

    // Extract version labels from matrix versionsInfo if available
    const versionLabels = {};
    if (versionsInfo && versionsInfo.metadata) {
      Object.keys(versionsInfo.metadata).forEach(vId => {
        versionLabels[vId] = versionsInfo.metadata[vId].label || vId;
      });
    }

    // Update matrix info state
    setMatrixInfo(prev => ({
      ...prev,
      activeVersions: versionsToMonitor,
      activeZones: zonesInfo?.list || []
    }));

    // Set up event sources for each version
    versionsToMonitor.forEach(version => {
      // Determine version ID format - numeric vs matrix ID (v1, v2, etc.)
      const versionParam = version.toString().startsWith('v')
          ? version.toString().substring(1) // Extract numeric part from matrix ID
          : version;

      // Close existing connection if any
      if (eventSourcesRef.current[version]) {
        eventSourcesRef.current[version].close();
      }

      // Create new EventSource connection
      const endpoint = isSensitivity ? 'stream_sensitivity' : 'stream_price';
      const port = isSensitivity ? 2500 : 5007; // Use port 2500 for sensitivity, 5007 for price
      console.log(`Creating EventSource connection to http://127.0.0.1:${port}/${endpoint}/${versionParam}`);
      const eventSource = new EventSource(`http://127.0.0.1:${port}/${endpoint}/${versionParam}`);
      eventSourcesRef.current[version] = eventSource;

      // Initialize monitoring data for this version
      setMonitorData(prev => ({
        ...prev,
        [version]: {
          status: 'connecting',
          currentPrice: null,
          iterations: 0,
          npv: null,
          complete: false,
          error: null,
          lastUpdated: new Date().toISOString(),
          versionLabel: versionLabels[version] || `Version ${version}`,
          matrixParameters: {}
        }
      }));

      console.log(`Initialized monitoring data for version ${version} with label ${versionLabels[version] || version}`);

      // Handle incoming messages
      eventSource.onmessage = (event) => {
        try {
          console.log(`[Version ${version}] Raw event data:`, event.data);
          const data = JSON.parse(event.data);
          console.log(`[Version ${version}] Parsed update:`, data);

          // Check for heartbeat
          if (data.heartbeat) {
            console.log(`[Version ${version}] Received heartbeat at ${data.timestamp}`);
            return; // Skip further processing for heartbeats
          }

          // Extract matrix-specific data if available
          const matrixParameters = data.matrixParameters || data.parameters || {};
          const parameterChanges = data.parameterChanges || {};
          const zoneUpdates = data.zoneUpdates || {};

          // Update monitoring data
          setMonitorData(prev => {
            const updatedData = {
              ...prev,
              [version]: {
                ...prev[version],
                status: 'active',
                currentPrice: data.price || prev[version]?.currentPrice,
                iterations: data.iteration || prev[version]?.iterations,
                npv: data.npv !== undefined ? data.npv : prev[version]?.npv,
                complete: data.complete || prev[version]?.complete,
                error: data.error || prev[version]?.error,
                lastUpdated: new Date().toISOString(),

                // Enhanced information
                calculationStep: data.calculationStep || prev[version]?.calculationStep,
                calculationDetails: data.calculationDetails || prev[version]?.calculationDetails,
                payloadDetails: data.payloadDetails || prev[version]?.payloadDetails,
                progressPercentage: data.progressPercentage || prev[version]?.progressPercentage || 0,

                // Sensitivity specific information
                logEntries: data.logEntries || prev[version]?.logEntries || [],
                isSensitivity: isSensitivity,

                // Matrix-specific information
                matrixParameters,
                parameterChanges,
                zoneUpdates,
                versionLabel: prev[version]?.versionLabel || `Version ${version}`
              }
            };
            console.log(`[Version ${version}] Updated monitor data:`, updatedData[version]);
            return updatedData;
          });

          // Update price in parent component
          if (data.price) {
            updatePrice(version, data.price);
          }

          // Track if calculation is complete
          if (data.complete && !completedCalculationsRef.current[version]) {
            completedCalculationsRef.current[version] = true;

            // Check if all calculations are complete
            const allComplete = versionsToMonitor.every(v => completedCalculationsRef.current[v]);
            if (allComplete) {
              console.log('All calculations complete, triggering onComplete callback');
              onComplete(monitorData);
            }

            // Close the connection
            console.log(`[Version ${version}] Calculation complete, closing connection`);
            eventSource.close();
          }
        } catch (error) {
          console.error(`[Version ${version}] Error processing stream data:`, error);

          // Update with error state
          setMonitorData(prev => ({
            ...prev,
            [version]: {
              ...prev[version],
              status: 'error',
              error: error.message,
              lastUpdated: new Date().toISOString()
            }
          }));
        }
      };

      // Handle connection open
      eventSource.onopen = () => {
        console.log(`[Version ${version}] Stream connection opened`);
        setMonitorData(prev => ({
          ...prev,
          [version]: {
            ...prev[version],
            status: 'connected',
            lastUpdated: new Date().toISOString()
          }
        }));
      };

      // Handle errors
      eventSource.onerror = (error) => {
        console.error(`[Version ${version}] Stream error:`, error);
        setMonitorData(prev => ({
          ...prev,
          [version]: {
            ...prev[version],
            status: 'error',
            error: 'Connection error',
            lastUpdated: new Date().toISOString()
          }
        }));

        // Close the connection on error
        eventSource.close();
      };
    });

    // Reset completed calculations when setting up new monitoring
    completedCalculationsRef.current = {};

    // Cleanup function to close all connections when component unmounts
    return () => {
      console.log('Cleaning up event sources');
      Object.values(eventSourcesRef.current).forEach(es => {
        if (es && es.readyState !== 2) { // 2 = CLOSED
          es.close();
        }
      });
    };
  }, [isActive, selectedVersions, currentVersion, updatePrice, versionsInfo, zonesInfo, onComplete]);

  // Helper to format status
  const getStatusDisplay = (statusData) => {
    if (!statusData) return 'Unknown';

    switch (statusData.status) {
      case 'connecting':
        return 'Connecting...';
      case 'connected':
        return 'Connected, waiting for data...';
      case 'active':
        return statusData.complete
            ? 'Calculation complete'
            : `Processing (Iteration ${statusData.iterations})`;
      case 'error':
        return `Error: ${statusData.error}`;
      default:
        return statusData.status || 'Unknown';
    }
  };

  // Helper to render parameter updates for matrix-based model
  const renderParameterUpdates = (data) => {
    if (!data.matrixParameters || Object.keys(data.matrixParameters).length === 0) {
      return null;
    }

    return (
        <div className="matrix-parameter-updates">
          <h5>Parameter Updates</h5>
          <div className="parameter-list">
            {Object.entries(data.matrixParameters).slice(0, 5).map(([paramId, value]) => (
                <div key={paramId} className="parameter-update">
                  <span className="parameter-id">{paramId}:</span>
                  <span className="parameter-value">
                {typeof value === 'number' ? value.toFixed(2) : value.toString()}
              </span>
                </div>
            ))}
            {Object.keys(data.matrixParameters).length > 5 && (
                <div className="more-parameters">
                  +{Object.keys(data.matrixParameters).length - 5} more parameters
                </div>
            )}
          </div>
        </div>
    );
  };

  // Helper to render zone-specific updates
  const renderZoneUpdates = (data) => {
    if (!data.zoneUpdates || Object.keys(data.zoneUpdates).length === 0) {
      return null;
    }

    return (
        <div className="zone-updates">
          <h5>Zone Updates</h5>
          <div className="zone-list">
            {Object.entries(data.zoneUpdates).map(([zoneId, updates]) => (
                <div key={zoneId} className="zone-update">
                  <span className="zone-id">{zoneId}:</span>
                  <span className="update-count">{Object.keys(updates).length} parameters</span>
                </div>
            ))}
          </div>
        </div>
    );
  };

  // If component is not active, don't render anything
  if (!isActive) return null;

  // Get versions to display
  const versionsToDisplay = Object.keys(monitorData).map(v => v);

  return (
      <div className="calculation-monitor">
        <h3>Real-time Calculation Monitor</h3>

        {versionsToDisplay.length === 0 ? (
            <p className="no-data">No active calculations</p>
        ) : (
            <div className="monitor-data">
              {versionsToDisplay.map(version => {
                const data = monitorData[version];
                if (!data) return null;

                return (
                    <div
                        key={version}
                        className={`version-monitor ${data.status} ${data.complete ? 'complete' : ''} ${isSensitivity ? 'sensitivity' : ''}`}
                    >
                      <h4>{data.versionLabel || `Version ${version}`}</h4>
                      <div className="monitor-status">
                        <span className="status-indicator"></span>
                        <span className="status-text">{getStatusDisplay(data)}</span>
                      </div>
                      <div className="monitor-details">
                        {data.currentPrice !== null && (
                            <div className="detail-row">
                              <strong>Current Price:</strong> ${data.currentPrice?.toFixed(2)}
                            </div>
                        )}
                        {data.npv !== null && (
                            <div className="detail-row">
                              <strong>Current NPV:</strong> ${data.npv?.toFixed(2)}
                            </div>
                        )}

                        {/* Enhanced information - Calculation Step */}
                        {data.calculationStep && (
                            <div className="detail-row calculation-step">
                              <strong>Current Step:</strong> {data.calculationStep}
                            </div>
                        )}

                        {/* Progress bar if progress percentage is available */}
                        {data.progressPercentage > 0 && (
                            <div className="progress-container">
                              <div className="progress-label">Progress: {data.progressPercentage}%</div>
                              <div className="progress-bar">
                                <div
                                    className="progress-bar-fill"
                                    style={{ width: `${data.progressPercentage}%` }}
                                ></div>
                              </div>
                            </div>
                        )}

                        {/* Matrix-specific parameter updates */}
                        {renderParameterUpdates(data)}

                        {/* Zone-specific updates */}
                        {renderZoneUpdates(data)}

                        {/* Enhanced information - Calculation Details */}
                        {data.calculationDetails && Object.keys(data.calculationDetails).length > 0 && (
                            <div className="calculation-details">
                              <h5>Calculation Details</h5>
                              <div className="details-container">
                                {Object.entries(data.calculationDetails).map(([key, value]) => (
                                    <div key={key} className="detail-row">
                                      <strong>{key}:</strong> {typeof value === 'number' ? value.toFixed(2) : value.toString()}
                                    </div>
                                ))}
                              </div>
                            </div>
                        )}

                        {/* Enhanced information - Payload Details */}
                        {data.payloadDetails && Object.keys(data.payloadDetails).length > 0 && (
                            <div className="payload-details">
                              <h5>Payload Details</h5>
                              <div className="details-container">
                                {Object.entries(data.payloadDetails).map(([key, value]) => (
                                    <div key={key} className="detail-row">
                                      <strong>{key}:</strong> {typeof value === 'number' ? value.toFixed(2) : value.toString()}
                                    </div>
                                ))}
                              </div>
                            </div>
                        )}

                        {/* Display log entries for sensitivity analysis */}
                        {data.isSensitivity && data.logEntries && data.logEntries.length > 0 && (
                            <div className="sensitivity-log">
                              <h5>Sensitivity Log Entries</h5>
                              <div className="log-container">
                                {data.logEntries.slice(-5).map((entry, index) => (
                                    <div key={index} className={`log-entry ${entry.level.toLowerCase()}`}>
                                      <span className="log-timestamp">{entry.timestamp}</span>
                                      <span className="log-level">{entry.level}</span>
                                      <span className="log-message">{entry.message}</span>
                                    </div>
                                ))}
                              </div>
                            </div>
                        )}

                        {data.complete && (
                            <div className="success-message">
                              ✓ {data.isSensitivity ? 'Sensitivity analysis' : 'Price optimization'} successful
                            </div>
                        )}
                      </div>
                    </div>
                );
              })}
            </div>
        )}
      </div>
  );
};

export default CalculationMonitor;
