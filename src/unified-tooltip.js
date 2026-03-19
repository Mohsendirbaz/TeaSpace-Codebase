// UnifiedTooltip.js
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAtom } from 'jotai';
import { efficacyAwareScalingGroupsAtom } from './atoms/efficacyMatrix';
import { versionsAtom } from './atoms/matrixFormValues';
import './UnifiedTooltip.css';

/**
 * UnifiedTooltip - A versatile tooltip component supporting various data types
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child elements that trigger the tooltip
 * @param {string} [props.type] - Type of data to display ('emissionFactor', 'regulatoryThreshold', 'assetCarbonIntensity', etc.)
 * @param {Object} [props.data] - Data to display in the tooltip for climate-related types
 * @param {string} [props.itemId] - ID for value-based tooltips that will look up data from Jotai state
 * @param {boolean} [props.showMatrix=false] - Whether to show matrix information (for value tooltips)
 * @param {boolean} [props.showDetails=true] - Whether to show detailed information (for value tooltips)
 * @param {string} [props.position='top'] - Position of tooltip relative to children ('top', 'bottom', 'left', 'right')
 * @param {number} [props.width=320] - Width of tooltip in pixels
 * @param {number} [props.maxHeight=400] - Maximum height of tooltip in pixels
 * @param {number} [props.showDelay=300] - Delay before showing tooltip (ms)
 * @param {number} [props.hideDelay=100] - Delay before hiding tooltip (ms)
 */
const UnifiedTooltip = ({
  children,
  type,
  data,
  itemId,
  showMatrix = false,
  showDetails = true,
  position = 'top',
  width = 320,
  maxHeight = 400,
  showDelay = 300,
  hideDelay = 100
}) => {
  // State
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const [tooltipContent, setTooltipContent] = useState(null);

  // Refs
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);
  const showTimerRef = useRef(null);
  const hideTimerRef = useRef(null);

  // Value tooltip state (only used if itemId is provided)
  const [versions] = useAtom(versionsAtom);
  const [efficacyGroups] = useAtom(efficacyAwareScalingGroupsAtom);

  // Find the item in the efficacy groups for value tooltips
  useEffect(() => {
    if (!itemId) return;

    let foundItem = null;
    let foundGroup = null;

    efficacyGroups.forEach(group => {
      group.items.forEach(item => {
        if (item.id === itemId) {
          foundItem = item;
          foundGroup = group;
        }
      });
    });

    if (!foundItem) {
      setTooltipContent(null);
      return;
    }

    // Calculate percentage change
    const percentChange = foundItem.baseValue !== 0
      ? ((foundItem.scaledValue - foundItem.baseValue) / Math.abs(foundItem.baseValue)) * 100
      : 0;

    setTooltipContent({
      item: foundItem,
      group: foundGroup,
      percentChange,
    });
  }, [itemId, efficacyGroups]);

  // Handle mouse events for trigger element
  const handleMouseEnter = () => {
    clearTimeout(hideTimerRef.current);
    showTimerRef.current = setTimeout(() => {
      calculatePosition();
      setIsVisible(true);
    }, showDelay);
  };

  const handleMouseLeave = () => {
    clearTimeout(showTimerRef.current);
    hideTimerRef.current = setTimeout(() => {
      setIsVisible(false);
    }, hideDelay);
  };

  // Calculate tooltip position
  const calculatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Calculate initial position based on preference
    let top = 0;
    let left = 0;

    switch (position) {
      case 'top':
        top = triggerRect.top - tooltipRect.height - 10;
        left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
        break;
      case 'bottom':
        top = triggerRect.bottom + 10;
        left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
        break;
      case 'left':
        top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2);
        left = triggerRect.left - tooltipRect.width - 10;
        break;
      case 'right':
        top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2);
        left = triggerRect.right + 10;
        break;
      default:
        top = triggerRect.top - tooltipRect.height - 10;
        left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
    }

    // Adjust to keep tooltip within viewport
    if (left < 10) left = 10;
    if (left + tooltipRect.width > viewportWidth - 10) left = viewportWidth - tooltipRect.width - 10;
    if (top < 10) top = 10;
    if (top + tooltipRect.height > viewportHeight - 10) top = viewportHeight - tooltipRect.height - 10;

    // Set position state
    setTooltipPosition({ top, left });
  };

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      clearTimeout(showTimerRef.current);
      clearTimeout(hideTimerRef.current);
    };
  }, []);

  // ===== Helper Functions =====

  // Format date display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Format number for value tooltip displays
  const formatNumber = (num) => {
    if (typeof num !== 'number') return 'N/A';

    if (Math.abs(num) >= 1000000) {
      return (num / 1000000).toFixed(2) + 'M';
    } else if (Math.abs(num) >= 1000) {
      return (num / 1000).toFixed(2) + 'K';
    } else {
      return num.toFixed(2);
    }
  };

  // Helper function to format risk names
  const formatRiskName = (risk) => {
    return risk
      .replace(/([A-Z])/g, ' $1') // Add space before capital letters
      .replace(/^./, str => str.toUpperCase()) // Capitalize first letter
      .replace(/Risk$/, '') // Remove "Risk" suffix
      .trim();
  };

  // Helper function to get risk description
  const getRiskDescription = (risk, level) => {
    const descriptions = {
      floodRisk: {
        High: "High likelihood of significant flooding events that may disrupt operations and damage infrastructure.",
        Medium: "Moderate flood risk with occasional flooding events possible.",
        Low: "Minimal flood risk with infrequent minor flooding."
      },
      droughtRisk: {
        High: "Severe water scarcity likely, potentially impacting operations and water-dependent processes.",
        Medium: "Moderate drought conditions possible, requiring water management planning.",
        Low: "Minimal drought risk with reliable water availability."
      },
      extremeHeatRisk: {
        High: "Frequent extreme heat events likely, impacting cooling systems, worker safety, and energy costs.",
        Medium: "Occasional extreme heat events expected, requiring adaptation measures.",
        Low: "Few extreme heat events expected with minimal operational impact."
      },
      seaLevelRiseRisk: {
        High: "Significant sea level rise projected, with high risk of coastal flooding and infrastructure damage.",
        Medium: "Moderate sea level rise expected, potentially affecting coastal operations.",
        Low: "Minimal sea level rise impact expected at this location."
      }
    };

    return descriptions[risk]?.[level] || "No detailed information available.";
  };

  // Helper function to get risk recommendations
  const getRiskRecommendation = (risk, level) => {
    if (level === "Low") {
      return "Standard precautions sufficient. Monitor for changes in risk profile.";
    }

    const recommendations = {
      floodRisk: {
        High: "Implement flood protection barriers, elevate critical equipment, develop emergency response protocols.",
        Medium: "Develop flood-resistant design, improve drainage systems, create continuity plans."
      },
      droughtRisk: {
        High: "Implement water recycling systems, reduce water consumption, secure alternative water sources.",
        Medium: "Optimize water usage, install low-flow fixtures, develop water shortage contingency plans."
      },
      extremeHeatRisk: {
        High: "Upgrade cooling systems, implement heat-resistant infrastructure, create extreme heat protocols.",
        Medium: "Improve insulation, optimize HVAC systems, implement flexible work schedules during heat events."
      },
      seaLevelRiseRisk: {
        High: "Consider facility relocation, install coastal barriers, elevate critical infrastructure.",
        Medium: "Plan for potential flooding, install check valves, implement regular maintenance protocols."
      }
    };

    return recommendations[risk]?.[level] || "Implement industry-standard adaptation measures.";
  };

  // Helper function to format energy source names
  const formatEnergySource = (source) => {
    const sourceNames = {
      coal: "Coal",
      naturalGas: "Natural Gas",
      nuclear: "Nuclear",
      hydro: "Hydroelectric",
      solar: "Solar",
      wind: "Wind",
      biomass: "Biomass",
      geothermal: "Geothermal",
      other: "Other"
    };

    return sourceNames[source] || source;
  };

  // ===== Climate Tooltip Content Renderers =====

  // Render emission factor tooltip content
  const renderEmissionFactorTooltip = () => {
    const { itemType, value, source, metadata } = data;

    return (
      <div className="tooltip-emission-factor">
        <div className="tooltip-header">
          <h4>{itemType} Emission Factor</h4>
          {metadata?.confidenceLevel && (
            <span className={`confidence-badge ${metadata.confidenceLevel}`}>
              {metadata.confidenceLevel}
            </span>
          )}
        </div>

        <div className="tooltip-value-section">
          <div className="tooltip-primary-value">
            {value.toFixed(2)} kg CO₂e/unit
          </div>
          {metadata?.industryBenchmarks && (
            <div className="tooltip-benchmarks">
              <div className="benchmark-item">
                <span className="benchmark-label">Industry Avg:</span>
                <span className="benchmark-value">
                  {metadata.industryBenchmarks.average.toFixed(2)}
                </span>
              </div>
              <div className="benchmark-item">
                <span className="benchmark-label">Best Practice:</span>
                <span className="benchmark-value">
                  {metadata.industryBenchmarks.bestPractice.toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="tooltip-metadata">
          <div className="metadata-row">
            <span className="metadata-label">Source:</span>
            <span className="metadata-value">{source || 'Unknown'}</span>
          </div>
          {metadata?.lastUpdated && (
            <div className="metadata-row">
              <span className="metadata-label">Last Updated:</span>
              <span className="metadata-value">{formatDate(metadata.lastUpdated)}</span>
            </div>
          )}
          {metadata?.applicableRegions && (
            <div className="metadata-row">
              <span className="metadata-label">Applicable Regions:</span>
              <span className="metadata-value">
                {metadata.applicableRegions.join(', ')}
              </span>
            </div>
          )}
        </div>

        {metadata?.description && (
          <div className="tooltip-description">
            {metadata.description}
          </div>
        )}

        {metadata?.examples && metadata.examples.length > 0 && (
          <div className="tooltip-examples">
            <h5>Reference Values</h5>
            <div className="examples-list">
              {metadata.examples.slice(0, 3).map((example, index) => (
                <div key={index} className="example-item">
                  <span className="example-entity">{example.entity}:</span>
                  <span className="example-value">
                    {parseFloat(example.value).toFixed(2)}
                    {example.unit ? ` ${example.unit}` : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render regulatory threshold tooltip content
  const renderRegulatoryThresholdTooltip = () => {
    const { level, threshold, name, description, authority, source, complianceStatus, lastUpdated } = data;

    return (
      <div className="tooltip-regulatory-threshold">
        <div className="tooltip-header">
          <h4>{name}</h4>
          <span className={`compliance-badge ${complianceStatus}`}>
            {complianceStatus === 'compliant' ? 'Compliant' : 
             complianceStatus === 'warning' ? 'Warning' : 'Non-Compliant'}
          </span>
        </div>

        <div className="tooltip-value-section">
          <div className="tooltip-primary-value">
            Threshold: {threshold.toLocaleString()} kg CO₂e
          </div>
        </div>

        <div className="tooltip-metadata">
          <div className="metadata-row">
            <span className="metadata-label">Jurisdiction:</span>
            <span className="metadata-value">{level.charAt(0).toUpperCase() + level.slice(1)}</span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Authority:</span>
            <span className="metadata-value">{authority || 'Unknown'}</span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Source:</span>
            <span className="metadata-value">{source || 'Unknown'}</span>
          </div>
          {lastUpdated && (
            <div className="metadata-row">
              <span className="metadata-label">Last Verified:</span>
              <span className="metadata-value">{formatDate(lastUpdated)}</span>
            </div>
          )}
        </div>

        {description && (
          <div className="tooltip-description">
            {description}
          </div>
        )}

        <div className="tooltip-compliance-info">
          <h5>Compliance Status</h5>
          <div className={`compliance-status-detail ${complianceStatus}`}>
            {complianceStatus === 'compliant' ? (
              <p>Your current emissions are below the regulatory threshold.</p>
            ) : complianceStatus === 'warning' ? (
              <p>Your emissions are approaching the regulatory threshold. Consider reduction strategies.</p>
            ) : (
              <p>Your emissions exceed the regulatory threshold. Action required for compliance.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Render asset carbon intensity tooltip content
  const renderAssetCarbonIntensityTooltip = () => {
    const { asset, benchmarks, alternatives, decarbonizationPathway } = data;

    return (
      <div className="tooltip-asset-carbon-intensity">
        <div className="tooltip-header">
          <h4>{asset.name}</h4>
          <span className={`asset-type-badge ${asset.isHardToDecarbonize ? 'hard-to-decarbonize' : 'standard'}`}>
            {asset.type}
          </span>
        </div>

        <div className="tooltip-value-section">
          <div className="tooltip-primary-value">
            {asset.carbonIntensity.toFixed(2)} kg CO₂e/unit
          </div>

          {benchmarks && (
            <div className="tooltip-benchmarks">
              <div className="tooltip-benchmark-bar">
                <div 
                  className="benchmark-indicator best-practice"
                  style={{ left: `${(benchmarks.bestPractice / benchmarks.average) * 100}%` }}
                  title={`Best Practice: ${benchmarks.bestPractice.toFixed(2)}`}
                ></div>
                <div 
                  className="benchmark-indicator average"
                  style={{ left: '100%' }}
                  title={`Industry Average: ${benchmarks.average.toFixed(2)}`}
                ></div>
                <div 
                  className="benchmark-indicator current"
                  style={{ left: `${(asset.carbonIntensity / benchmarks.average) * 100}%` }}
                  title={`Current: ${asset.carbonIntensity.toFixed(2)}`}
                ></div>
                <div 
                  className="benchmark-indicator innovation"
                  style={{ left: `${(benchmarks.innovationTarget / benchmarks.average) * 100}%` }}
                  title={`Innovation Target: ${benchmarks.innovationTarget.toFixed(2)}`}
                ></div>
              </div>

              <div className="benchmark-labels">
                <span>Better</span>
                <span>Industry Avg</span>
              </div>
            </div>
          )}
        </div>

        <div className="tooltip-metadata">
          <div className="metadata-row">
            <span className="metadata-label">Source:</span>
            <span className="metadata-value">{asset.carbonIntensitySource || 'Unknown'}</span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Confidence:</span>
            <span className={`metadata-value confidence-${asset.confidenceLevel}`}>
              {asset.confidenceLevel || 'medium'}
            </span>
          </div>
          {asset.lastUpdated && (
            <div className="metadata-row">
              <span className="metadata-label">Last Updated:</span>
              <span className="metadata-value">{formatDate(asset.lastUpdated)}</span>
            </div>
          )}
        </div>

        {alternatives && alternatives.length > 0 && (
          <div className="tooltip-alternatives">
            <h5>Low-Carbon Alternatives</h5>
            <div className="alternatives-list">
              {alternatives.map((alt, index) => (
                <div key={index} className="alternative-item">
                  <div className="alternative-header">
                    <span className="alternative-name">{alt.name}</span>
                    <span className="alternative-intensity">
                      {alt.carbonIntensity.toFixed(2)} kg CO₂e/unit
                    </span>
                  </div>
                  <div className="alternative-details">
                    <span className="alternative-cost">
                      Cost: {alt.costDifferential}
                    </span>
                    <span className="alternative-maturity">
                      {alt.maturityLevel}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {decarbonizationPathway && (
          <div className="tooltip-decarbonization">
            <h5>Decarbonization Pathway</h5>
            <div className="pathway-visualization">
              <div className="pathway-point current">
                <div className="point-label">Current</div>
                <div className="point-value">{decarbonizationPathway.current.toFixed(1)}</div>
              </div>
              <div className="pathway-line"></div>
              <div className="pathway-point mid">
                <div className="point-label">2030</div>
                <div className="point-value">{decarbonizationPathway.target2030.toFixed(1)}</div>
              </div>
              <div className="pathway-line"></div>
              <div className="pathway-point end">
                <div className="point-label">2050</div>
                <div className="point-value">{decarbonizationPathway.target2050.toFixed(1)}</div>
              </div>
            </div>
            <div className="pathway-reduction">
              Potential Reduction: {decarbonizationPathway.potentialReduction}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render geographic context tooltip content
  const renderGeographicContextTooltip = () => {
    const { coordinates, geographicContext, environmentalRisks, climateProjections } = data;

    return (
      <div className="tooltip-geographic-context">
        <div className="tooltip-header">
          <h4>Geographic Context</h4>
        </div>

        <div className="tooltip-coordinates">
          <div className="coordinate-row">
            <span className="coordinate-label">Latitude:</span>
            <span className="coordinate-value">{coordinates.latitude.toFixed(6)}°</span>
          </div>
          <div className="coordinate-row">
            <span className="coordinate-label">Longitude:</span>
            <span className="coordinate-value">{coordinates.longitude.toFixed(6)}°</span>
          </div>
        </div>

        {geographicContext && (
          <div className="tooltip-location-details">
            <div className="location-primary">
              {[
                geographicContext.city,
                geographicContext.state,
                geographicContext.country
              ].filter(Boolean).join(', ')}
            </div>

            <div className="location-metadata">
              <div className="metadata-item">
                <span className="metadata-label">Climate:</span>
                <span className="metadata-value">{geographicContext.climate || 'Unknown'}</span>
              </div>
              {geographicContext.elevation && (
                <div className="metadata-item">
                  <span className="metadata-label">Elevation:</span>
                  <span className="metadata-value">{geographicContext.elevation} m</span>
                </div>
              )}
              {geographicContext.populationDensity && (
                <div className="metadata-item">
                  <span className="metadata-label">Population:</span>
                  <span className="metadata-value">
                    {geographicContext.population?.toLocaleString() || 'Unknown'} 
                    ({geographicContext.populationDensity})
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {geographicContext?.energyGrid && (
          <div className="tooltip-energy-grid">
            <h5>Energy Grid</h5>
            <div className="grid-details">
              <div className="grid-name">{geographicContext.energyGrid.name}</div>
              <div className="grid-metrics">
                <div className="grid-metric">
                  <span className="metric-label">Carbon Intensity:</span>
                  <span className="metric-value">
                    {geographicContext.energyGrid.carbonIntensity.toFixed(2)} kg CO₂e/kWh
                  </span>
                </div>
                <div className="grid-metric">
                  <span className="metric-label">Renewable Energy:</span>
                  <span className="metric-value">
                    {geographicContext.energyGrid.renewablePercentage}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {environmentalRisks && Object.keys(environmentalRisks).length > 0 && (
          <div className="tooltip-risks">
            <h5>Environmental Risks</h5>
            <div className="risks-grid">
              {Object.entries(environmentalRisks).map(([risk, level]) => (
                <div key={risk} className={`risk-indicator ${level.toLowerCase()}`}>
                  <div className="risk-name">{formatRiskName(risk)}</div>
                  <div className="risk-level">{level}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {climateProjections && (
          <div className="tooltip-climate-projections">
            <h5>Climate Projections (2050)</h5>
            <div className="projections-list">
              <div className="projection-item">
                <span className="projection-label">Temperature Change:</span>
                <span className="projection-value">+{climateProjections.temperatureIncrease2050}°C</span>
              </div>
              <div className="projection-item">
                <span className="projection-label">Precipitation:</span>
                <span className="projection-value">
                  {climateProjections.precipitationChange2050 > 0 ? '+' : ''}
                  {climateProjections.precipitationChange2050}%
                </span>
              </div>
              <div className="projection-item">
                <span className="projection-label">Extreme Weather:</span>
                <span className="projection-value">{climateProjections.extremeWeatherTrend}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render environmental risks tooltip content
  const renderEnvironmentalRisksTooltip = () => {
    const risks = data;
    if (!risks || Object.keys(risks).length === 0) {
      return (
        <div className="tooltip-environmental-risks">
          <div className="tooltip-header">
            <h4>Environmental Risks</h4>
          </div>
          <p>No environmental risk data available for this location.</p>
        </div>
      );
    }

    return (
      <div className="tooltip-environmental-risks">
        <div className="tooltip-header">
          <h4>Environmental Risks</h4>
        </div>

        <div className="tooltip-risks-detailed">
          {Object.entries(risks).map(([risk, level]) => (
            <div key={risk} className="risk-detail-item">
              <div className="risk-header">
                <span className="risk-name">{formatRiskName(risk)}</span>
                <span className={`risk-level-badge ${level.toLowerCase()}`}>
                  {level}
                </span>
              </div>
              <div className="risk-description">
                {getRiskDescription(risk, level)}
              </div>
              <div className="risk-recommendation">
                {getRiskRecommendation(risk, level)}
              </div>
            </div>
          ))}
        </div>

        <div className="tooltip-risk-footer">
          <p>Risk assessments based on current climate data and projections.</p>
        </div>
      </div>
    );
  };

  // Render energy grid tooltip content
  const renderEnergyGridTooltip = () => {
    const grid = data;
    if (!grid) {
      return (
        <div className="tooltip-energy-grid">
          <div className="tooltip-header">
            <h4>Energy Grid</h4>
          </div>
          <p>No energy grid data available for this location.</p>
        </div>
      );
    }

    return (
      <div className="tooltip-energy-grid-detail">
        <div className="tooltip-header">
          <h4>{grid.name} Energy Grid</h4>
        </div>

        <div className="tooltip-grid-metrics">
          <div className="grid-carbon-intensity">
            <div className="metric-header">
              <span className="metric-label">Carbon Intensity</span>
              <span className="metric-value">
                {grid.carbonIntensity.toFixed(2)} kg CO₂e/kWh
              </span>
            </div>
            <div className="intensity-scale">
              <div className="scale-markers">
                <span className="scale-marker low">0.1</span>
                <span className="scale-marker medium">0.5</span>
                <span className="scale-marker high">0.9</span>
              </div>
              <div className="scale-bar">
                <div 
                  className="scale-position"
                  style={{ 
                    left: `${Math.min(100, Math.max(0, grid.carbonIntensity / 1.0 * 100))}%` 
                  }}
                ></div>
              </div>
              <div className="scale-labels">
                <span>Clean</span>
                <span>Carbon Intensive</span>
              </div>
            </div>
          </div>

          <div className="grid-renewable-percentage">
            <div className="metric-header">
              <span className="metric-label">Renewable Energy</span>
              <span className="metric-value">{grid.renewablePercentage}%</span>
            </div>
            <div className="renewable-pie-chart">
              <svg viewBox="0 0 36 36">
                <path
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#e6e6e6"
                  strokeWidth="3"
                  strokeDasharray="100, 100"
                />
                <path
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#4caf50"
                  strokeWidth="3"
                  strokeDasharray={`${grid.renewablePercentage}, 100`}
                />
                <text x="18" y="21" textAnchor="middle" fill="#333" fontSize="8px">
                  {grid.renewablePercentage}%
                </text>
              </svg>
            </div>
          </div>
        </div>

        <div className="tooltip-grid-sources">
          <h5>Energy Mix</h5>
          <div className="sources-bars">
            {grid.energySources ? (
              Object.entries(grid.energySources).map(([source, percentage]) => (
                <div key={source} className="source-bar-container">
                  <div className="source-name">{formatEnergySource(source)}</div>
                  <div className="source-bar-wrapper">
                    <div 
                      className={`source-bar ${source.toLowerCase()}`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                    <span className="source-percentage">{percentage}%</span>
                  </div>
                </div>
              ))
            ) : (
              <p>Detailed energy mix not available.</p>
            )}
          </div>
        </div>

        <div className="tooltip-grid-footer">
          <p>Lower carbon intensity indicates cleaner electricity generation.</p>
        </div>
      </div>
    );
  };

  // Render value tooltip content
  const renderValueTooltip = () => {
    if (!tooltipContent) return null;

    return (
      <div className="tooltip-value">
        <div className="tooltip-header">
          <h4>{tooltipContent.item.label || tooltipContent.item.id}</h4>
          <span className={`status-indicator ${tooltipContent.item.isActive ? 'active' : 'inactive'}`}>
            {tooltipContent.item.isActive ? 'Active' : 'Inactive'}
          </span>
        </div>

        {tooltipContent.group && (
          <div className="tooltip-group">
            <span className="group-label">Group:</span>
            <span className="group-name">{tooltipContent.group.name}</span>
          </div>
        )}

        {showDetails && (
          <div className="tooltip-details">
            <div className="detail-row">
              <span className="detail-label">Base Value:</span>
              <span className="detail-value">{formatNumber(tooltipContent.item.baseValue)}</span>
            </div>

            <div className="detail-row">
              <span className="detail-label">Scaled Value:</span>
              <span className="detail-value">{formatNumber(tooltipContent.item.scaledValue)}</span>
            </div>

            <div className="detail-row highlight">
              <span className="detail-label">Effective Value:</span>
              <span className="detail-value highlight">{formatNumber(tooltipContent.item.effectiveValue)}</span>
            </div>

            <div className="detail-row">
              <span className="detail-label">Change:</span>
              <span className={`detail-value ${tooltipContent.item.scaledValue > tooltipContent.item.baseValue ? 'positive' : tooltipContent.item.scaledValue < tooltipContent.item.baseValue ? 'negative' : ''}`}>
                {formatNumber(tooltipContent.item.scaledValue - tooltipContent.item.baseValue)}
                {tooltipContent.percentChange !== 0 && (
                  <span className="percent-change">
                    ({tooltipContent.percentChange > 0 ? '+' : ''}{tooltipContent.percentChange.toFixed(2)}%)
                  </span>
                )}
              </span>
            </div>

            {tooltipContent.item.efficacyPeriod && (
              <div className="detail-row">
                <span className="detail-label">Efficacy Period:</span>
                <span className="detail-value">
                  Years {tooltipContent.item.efficacyPeriod.start} - {tooltipContent.item.efficacyPeriod.end}
                </span>
              </div>
            )}
          </div>
        )}

        {showMatrix && (
          <div className="tooltip-matrix">
            <h5>Matrix Values</h5>
            <div className="matrix-info">
              <div className="matrix-row">
                <span className="matrix-label">Version:</span>
                <span className="matrix-value">{versions.metadata[versions.active]?.label || versions.active}</span>
              </div>

            </div>
          </div>
        )}
      </div>
    );
  };

  // Render generic tooltip content
  const renderGenericTooltip = () => {
    return (
      <div className="tooltip-generic-content">
        <h4>Information</h4>
        <p>Hover for additional details about this element.</p>
      </div>
    );
  };

  // Render hierarchy level tooltip content (used by HierarchyShelfComponent)
  const renderHierarchyLevelTooltip = () => {
    if (!data) return renderGenericTooltip();
    const { level, color, position, positionLabel, value, breadcrumb, groupLabel } = data;

    // Depth-progress bar: filled fraction = depth / 14
    const depthPct = Math.round((level.depth / 14) * 100);

    return (
      <div className="tooltip-hierarchy-level">

        {/* Header: level name + depth badge */}
        <div className="tooltip-header">
          <h4 style={{ color: color || 'inherit' }}>{level.name}</h4>
          <span className="hierarchy-depth-pill" style={{ background: color || '#6366f1' }}>
            {level.depth}/14
          </span>
        </div>

        {/* Symbol + core metrics row */}
        <div className="hierarchy-symbol-row">
          <span className="hierarchy-big-symbol" style={{ color: color || 'inherit' }}>
            {level.symbol}
          </span>
          <div className="hierarchy-metrics">
            <div className="hm-item">
              <span className="hm-key">Duration</span>
              <span className="hm-val">{level.duration}</span>
            </div>
            <div className="hm-item">
              <span className="hm-key">Fanout</span>
              <span className="hm-val">{level.fanout} children</span>
            </div>
            <div className="hm-item">
              <span className="hm-key">Group</span>
              <span className="hm-val">{groupLabel || level.group}</span>
            </div>
          </div>
        </div>

        {/* Depth progress bar */}
        <div className="hierarchy-depth-bar-wrap">
          <span className="hm-key">Depth</span>
          <div className="hierarchy-depth-bar">
            <div
              className="hierarchy-depth-fill"
              style={{ width: `${depthPct}%`, background: color || '#6366f1' }}
            />
          </div>
          <span className="hm-key">{depthPct}%</span>
        </div>

        {/* Current position + value */}
        <div className="hierarchy-pv-row">
          <div className="hpv-cell">
            <span className="hm-key">Position</span>
            <span className="hpv-val" style={{ color: color || 'inherit' }}>{positionLabel}</span>
          </div>
          <div className="hpv-divider" />
          <div className="hpv-cell">
            <span className="hm-key">Cell Value</span>
            <span className="hpv-val">{value}</span>
          </div>
        </div>

        {/* Breadcrumb path */}
        <div className="hierarchy-path-row">
          <span className="hm-key">Path</span>
          <span className="hierarchy-path-text">{breadcrumb}</span>
        </div>

        {/* Hint */}
        <div className="hierarchy-tooltip-hint">
          ◀ ▶ navigate · double-click to edit · click tile to expand
        </div>

      </div>
    );
  };

  // Render tooltip content based on type
  const renderTooltipContent = () => {
    // If itemId is provided, use Value tooltip
    if (itemId) {
      return renderValueTooltip();
    }

    // Otherwise, use Climate / Hierarchy tooltips based on type
    switch (type) {
      case 'emissionFactor':
        return renderEmissionFactorTooltip();
      case 'regulatoryThreshold':
        return renderRegulatoryThresholdTooltip();
      case 'assetCarbonIntensity':
        return renderAssetCarbonIntensityTooltip();
      case 'geographicContext':
        return renderGeographicContextTooltip();
      case 'environmentalRisks':
        return renderEnvironmentalRisksTooltip();
      case 'energyGrid':
        return renderEnergyGridTooltip();
      case 'hierarchyLevel':
        return renderHierarchyLevelTooltip();
      default:
        return renderGenericTooltip();
    }
  };

  return (
    <div 
      ref={triggerRef}
      className="unified-tooltip-container"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}

      <AnimatePresence>
        {isVisible && (
          <motion.div
            ref={tooltipRef}
            className={`unified-tooltip ${itemId ? 'tooltip-value' : `tooltip-${type || 'generic'}`} tooltip-${position}`}
            style={{
              position: 'fixed',
              top: tooltipPosition.top,
              left: tooltipPosition.left,
              width: width,
              maxHeight: maxHeight,
              zIndex: 9999
            }}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            onMouseEnter={() => clearTimeout(hideTimerRef.current)}
            onMouseLeave={handleMouseLeave}
          >
            {renderTooltipContent()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * SimpleTooltip - A controlled tooltip component for external positioning
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.show - Whether to show the tooltip
 * @param {Object} props.position - Position object with x, y coordinates
 * @param {React.ReactNode} props.content - Content to display
 * @param {number} [props.width=320] - Width of tooltip in pixels
 */
export const SimpleTooltip = ({
  show,
  position,
  content,
  width = 320
}) => {
  if (!show || !content) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="unified-tooltip-container"
        style={{
          position: 'absolute',
          top: position.y + 10,
          left: position.x + 10,
          width: width,
          zIndex: 9999,
          background: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          padding: '1rem',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(20px)'
        }}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.2 }}
      >
        {content}
      </motion.div>
    </AnimatePresence>
  );
};

export default UnifiedTooltip;
