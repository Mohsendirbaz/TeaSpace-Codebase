import React, { useState, useEffect, useCallback, useMemo } from 'react';
import TimeParameterMatrix from './TimeParameterMatrix';
import ConflictResolutionPanel from './ConflictResolutionPanel';
import CapacityMapPanel from './CapacityMapPanel';
import capacityTracker from '../../services/CapacityTrackingService';
import '../../styles/HomePage.CSS/EfficacyMapContainer.css';

/**
 * EfficacyMapContainer component
 * 
 * Main container for the efficacy time and degree of freedom visualization
 * Integrates the TimeParameterMatrix, ConflictResolutionPanel, and CapacityMapPanel components
 * 
 * @param {Object} props
 * @param {Object} props.parameters - Object containing parameters with efficacy periods
 * @param {Object} props.scalingGroups - Object containing scaling groups for each parameter
 * @param {number} props.plantLifetime - The plant lifetime in years (default: 20)
 * @param {number} props.configurableVersions - The number of configurable versions (default: 20)
 * @param {number} props.maxScalingGroups - The maximum number of scaling groups per parameter (default: 5)
 * @param {number} props.maxSensitivityVariations - The maximum sensitivity variations per parameter-scaling group (default: 6)
 * @param {Function} props.onParameterUpdate - Function to call when parameters are updated
 * @param {Function} props.onCapacityConfigChange - Function to call when capacity configuration changes
 */
const EfficacyMapContainer = ({
  parameters = {},
  scalingGroups = {},
  plantLifetime = 20,
  configurableVersions = 20,
  maxScalingGroups = 5,
  maxSensitivityVariations = 6,
  onParameterUpdate,
  onCapacityConfigChange
}) => {
  const [showConflictPanel, setShowConflictPanel] = useState(false);
  const [showCapacityPanel, setShowCapacityPanel] = useState(false);
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [conflictingPeriods, setConflictingPeriods] = useState([]);
  const [usageStats, setUsageStats] = useState({});
  const [currentState, setCurrentState] = useState({
    usedParameters: 0,
    scalingGroupsPerParameter: {},
    variationsPerParameterScalingGroup: {},
    usedVersions: configurableVersions,
    yearsConfigured: plantLifetime
  });

  // Update capacity limits and usage
  useEffect(() => {
    // Set capacity limits
    capacityTracker.setCapacityLimit('plantLifetime', plantLifetime);
    capacityTracker.setCapacityLimit('configurableVersions', configurableVersions);
    capacityTracker.setCapacityLimit('maxScalingGroups', maxScalingGroups);
    capacityTracker.setCapacityLimit('maxSensitivityVariations', maxSensitivityVariations);

    // Update usage
    capacityTracker.updatePlantLifetimeUsage(plantLifetime);
    capacityTracker.updateConfigurableVersionsUsage(configurableVersions);

    // Get all usage stats
    setUsageStats(capacityTracker.getAllUsageStats());
  }, [plantLifetime, configurableVersions, maxScalingGroups, maxSensitivityVariations]);

  // Update current state for CapacityMapPanel
  useEffect(() => {
    const usedParameters = Object.keys(parameters).length;

    // Count scaling groups per parameter
    const scalingGroupsPerParameter = {};
    Object.keys(parameters).forEach(paramId => {
      const paramScalingGroups = scalingGroups[paramId] || [];
      scalingGroupsPerParameter[paramId] = paramScalingGroups.length;
    });

    // Count sensitivity variations per parameter-scaling group
    const variationsPerParameterScalingGroup = {};
    Object.keys(parameters).forEach(paramId => {
      const paramScalingGroups = scalingGroups[paramId] || [];

      paramScalingGroups.forEach(sgId => {
        const key = `${paramId}_${sgId}`;
        // Assume each parameter-scaling group can have up to maxSensitivityVariations variations
        // In a real app, this would be determined from actual data
        variationsPerParameterScalingGroup[key] = Math.floor(Math.random() * maxSensitivityVariations) + 1;
      });
    });

    setCurrentState({
      usedParameters,
      scalingGroupsPerParameter,
      variationsPerParameterScalingGroup,
      usedVersions: configurableVersions,
      yearsConfigured: plantLifetime
    });

    // Update capacity tracker with actual usage
    capacityTracker.updateParametersUsage(usedParameters);
    capacityTracker.updateScalingGroupsUsage(Object.values(scalingGroupsPerParameter).reduce((sum, count) => sum + count, 0));
    capacityTracker.updateSensitivityVariationsUsage(Object.values(variationsPerParameterScalingGroup).reduce((sum, count) => sum + count, 0));

    // Get updated usage stats
    setUsageStats(capacityTracker.getAllUsageStats());
  }, [parameters, scalingGroups, plantLifetime, configurableVersions, maxScalingGroups, maxSensitivityVariations]);

  // Handle conflict click in the matrix
  const handleConflictClick = useCallback((paramId, scalingGroupId, year) => {
    // Find the conflicting periods for this parameter-scaling group-year combination
    const param = parameters[paramId];
    if (!param) return;

    // In a real app, we would check the efficacy periods specific to this parameter-scaling group combination
    // For this example, we're using the parameter's efficacy periods
    const periods = param.efficacyPeriods?.filter(period => 
      year >= period.start && year <= period.end
    ) || [];

    if (periods.length > 1) {
      setSelectedConflict({ paramId, scalingGroupId, year });
      setConflictingPeriods(periods);
      setShowConflictPanel(true);
    }
  }, [parameters]);

  // Handle conflict resolution
  const handleResolveConflict = useCallback((resolution) => {
    if (!resolution || !selectedConflict || !onParameterUpdate) return;

    const { paramId, scalingGroupId, year } = selectedConflict;
    const param = parameters[paramId];
    if (!param || !param.efficacyPeriods) return;

    let updatedPeriods = [...param.efficacyPeriods];

    // Apply resolution based on type
    if (resolution.type === 'select') {
      // Keep only the selected period
      updatedPeriods = [param.efficacyPeriods[resolution.keepPeriodIndex]];
    } 
    else if (resolution.type === 'adjust') {
      // Apply adjustments to each period
      updatedPeriods = resolution.adjustments.map(adjustment => {
        if (adjustment.split) {
          // Split the period into two
          const { split, ...periodData } = adjustment;
          return [
            { ...periodData, end: split - 1 },
            { ...periodData, start: split + 1 }
          ];
        }
        return adjustment;
      }).flat();
    } 
    else if (resolution.type === 'custom') {
      // Replace all conflicting periods with a custom one
      const conflictingIndices = param.efficacyPeriods.map((period, index) => 
        year >= period.start && year <= period.end ? index : -1
      ).filter(index => index !== -1);

      // Remove conflicting periods
      updatedPeriods = param.efficacyPeriods.filter((_, index) => 
        !conflictingIndices.includes(index)
      );

      // Add custom period
      updatedPeriods.push({
        start: resolution.customStart,
        end: resolution.customEnd,
        value: param.efficacyPeriods[0].value // Use value from first period
      });
    }

    // Update the parameter
    const updatedParam = {
      ...param,
      efficacyPeriods: updatedPeriods
    };

    // Call the update function
    onParameterUpdate(paramId, updatedParam);

    // Close the panel
    setShowConflictPanel(false);
    setSelectedConflict(null);
    setConflictingPeriods([]);
  }, [selectedConflict, parameters, onParameterUpdate]);

  // Handle cancel conflict resolution
  const handleCancelResolution = useCallback(() => {
    setShowConflictPanel(false);
    setSelectedConflict(null);
    setConflictingPeriods([]);
  }, []);

  // Handle capacity config change
  const handleCapacityConfigChange = useCallback((newConfig) => {
    if (onCapacityConfigChange) {
      onCapacityConfigChange(newConfig);
    }
  }, [onCapacityConfigChange]);

  return (
    <div className="efficacy-map-container">
      {/*
      <div className="map-header">
        <h2>Efficacy Time and Degree of Freedom Map</h2>
        <p className="map-description">
          This map visualizes parameter efficacy periods across the plant lifetime.
          The degree of freedom constraint allows only one value per parameter per scaling group per time unit (year).
        </p>

        <div className="capacity-summary">
          <h3>Capacity Settings <button className="capacity-button" onClick={() => setShowCapacityPanel(true)}>View Detailed Capacity Map</button></h3>
          <div className="capacity-items">
            <div className="capacity-item">
              <div className="capacity-label">Plant Lifetime:</div>
              <div className="capacity-value">{plantLifetime} years</div>
              <div className="capacity-bar">
                <div 
                  className="capacity-fill" 
                  style={{ 
                    width: `${usageStats.plantLifetime?.percentage || 0}%`,
                    backgroundColor: getColorForPercentage(usageStats.plantLifetime?.percentage || 0)
                  }}
                ></div>
              </div>
            </div>

            <div className="capacity-item">
              <div className="capacity-label">Configurable Versions:</div>
              <div className="capacity-value">{configurableVersions}</div>
              <div className="capacity-bar">
                <div 
                  className="capacity-fill" 
                  style={{ 
                    width: `${usageStats.configurableVersions?.percentage || 0}%`,
                    backgroundColor: getColorForPercentage(usageStats.configurableVersions?.percentage || 0)
                  }}
                ></div>
              </div>
            </div>

            <div className="capacity-item">
              <div className="capacity-label">Max Scaling Groups:</div>
              <div className="capacity-value">{maxScalingGroups} per parameter</div>
              <div className="capacity-bar">
                <div 
                  className="capacity-fill" 
                  style={{ 
                    width: `${usageStats.maxScalingGroups?.percentage || 0}%`,
                    backgroundColor: getColorForPercentage(usageStats.maxScalingGroups?.percentage || 0)
                  }}
                ></div>
              </div>
            </div>

            <div className="capacity-item">
              <div className="capacity-label">Sensitivity Variations:</div>
              <div className="capacity-value">{maxSensitivityVariations} per param-scaling group</div>
              <div className="capacity-bar">
                <div 
                  className="capacity-fill" 
                  style={{ 
                    width: `${usageStats.maxSensitivityVariations?.percentage || 0}%`,
                    backgroundColor: getColorForPercentage(usageStats.maxSensitivityVariations?.percentage || 0)
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="configuration-space-info">
          <h4>Configuration Space</h4>
          <p>
            Your current capacity settings create a theoretical configuration space of:
          </p>
          <div className="configuration-formula">
            {Object.keys(parameters).length} Parameters × 
            {maxScalingGroups} Scaling Groups × 
            {maxSensitivityVariations} Sensitivity Variations × 
            {plantLifetime} Years × 
            {configurableVersions} Versions = 
            <span className="total-space">
              {formatLargeNumber(
                Object.keys(parameters).length * 
                maxScalingGroups * 
                maxSensitivityVariations * 
                plantLifetime * 
                configurableVersions
              )}
            </span> distinct values
          </div>
        </div>

        <div className="exclusion-note">
          <h4>Exclusions from Combinatorial Calculations</h4>
          <p>
            The following elements are excluded from combinatorial calculations to maintain focus on the core parameters:
          </p>
          <ul>
            <li><strong>Number of plots</strong> - These are considered trivial multipliers and are excluded from capacity calculations</li>
            <li><strong>Interchangeable x and y axes</strong> - These are treated as a single configuration option</li>
            <li><strong>Zones</strong> - Currently only one area is considered for calculations</li>
          </ul>
          <p>
            These exclusions help maintain a clear focus on the degree of freedom constraint: one value per parameter per scaling group per time unit (year).
          </p>
        </div>
      </div>
*/}
      <div className="map-content">
        <TimeParameterMatrix 
          parameters={parameters}
          scalingGroups={scalingGroups}
          plantLifetime={plantLifetime}
          onConflictClick={handleConflictClick}
        />
      </div>

      {showConflictPanel && (
        <div className="conflict-panel-overlay">
          <ConflictResolutionPanel 
            paramId={selectedConflict?.paramId}
            scalingGroupId={selectedConflict?.scalingGroupId}
            year={selectedConflict?.year}
            conflictingPeriods={conflictingPeriods}
            onResolve={handleResolveConflict}
            onCancel={handleCancelResolution}
          />
        </div>
      )}

      {showCapacityPanel && (
        <div className="capacity-panel-overlay">
          <CapacityMapPanel 
            currentState={currentState}
            onCapacityConfigChange={handleCapacityConfigChange}
            onClose={() => setShowCapacityPanel(false)}
          />
        </div>
      )}
    </div>
  );
};

// Helper function to get color based on percentage
const getColorForPercentage = (percentage) => {
  if (percentage > 90) return '#ff4d4d'; // Red
  if (percentage > 70) return '#ffaa33'; // Orange
  return '#4caf50'; // Green
};

// Helper function to format large numbers
const formatLargeNumber = (num) => {
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(1) + 'B';
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

export default EfficacyMapContainer;
