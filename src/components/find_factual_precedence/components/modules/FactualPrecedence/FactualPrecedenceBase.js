import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faTimes,
  faInfoCircle,
  faCheckCircle,
  faLightbulb,
  faChartLine,
  faExternalLinkAlt,
  faBuilding,
  faHistory
} from '@fortawesome/free-solid-svg-icons';
import '../../../styles/FactualPrecedence.css';

// Advanced parameter context utility
const getParameterContext = (itemId, formValue) => {
  // Determine parameter type and context
  let paramType = 'general';
  if (itemId.includes('Amount1')) paramType = 'investment';
  else if (itemId.includes('Amount2')) paramType = 'loan';
  else if (itemId.includes('Amount3')) paramType = 'rate';
  else if (itemId.includes('Amount4')) paramType = 'quantity';
  else if (itemId.includes('Amount5')) paramType = 'process-cost';
  else if (itemId.includes('Amount6')) paramType = 'sales-volume';
  else if (itemId.includes('Amount7')) paramType = 'price';
  else if (itemId.includes('vAmount')) paramType = 'variable';
  else if (itemId.includes('rAmount')) paramType = 'revenue';

  // Generate industry insights based on parameter type and label
  let industryInsights = [];
  const formLabel = (formValue?.label || '').toLowerCase();

  if (paramType === 'investment') {
    industryInsights = [
      { company: "Amazon", insight: "Started with minimal infrastructure for selling books before scaling to broader retail", year: 1994 },
      { company: "Tesla", insight: "Began with low-volume Roadster before scaling to mass market vehicles", year: 2008 },
      { company: "Spotify", insight: "Launched with limited catalog and region restrictions to manage initial costs", year: 2008 }
    ];
  } else if (paramType === 'price') {
    industryInsights = [
      { company: "Apple", insight: "Consistently positioned products at premium pricing to build brand value", year: 2001 },
      { company: "Salesforce", insight: "Pioneered subscription model when perpetual licenses were standard", year: 1999 },
      { company: "IKEA", insight: "Reduced prices systematically each year through design and supply chain optimization", year: 1956 }
    ];
  } else if (paramType === 'process-cost') {
    industryInsights = [
      { company: "Toyota", insight: "Implemented continuous improvement (Kaizen) to gradually reduce production costs", year: 1950 },
      { company: "Dell", insight: "Built direct-to-consumer model eliminating reseller markups", year: 1984 },
      { company: "Southwest Airlines", insight: "Standardized on single aircraft type to reduce maintenance costs", year: 1971 }
    ];
  } else {
    industryInsights = [
      { company: "Google", insight: "Started with a single focus (search) before diversifying revenue streams", year: 1998 },
      { company: "Netflix", insight: "Evolved business model from DVD rental to streaming to content production", year: 1997 },
      { company: "Microsoft", insight: "Initially focused on programming languages before expanding to OS and productivity", year: 1975 }
    ];
  }

  // Determine industry from label
  let industry = 'general';
  if (formLabel.match(/energy|power|electricity|solar|wind/i)) industry = 'energy';
  else if (formLabel.match(/chemical|material|compound/i)) industry = 'chemical';
  else if (formLabel.match(/software|digital|tech|data/i)) industry = 'technology';
  else if (formLabel.match(/medicine|health|patient|medical/i)) industry = 'healthcare';

  return {
    paramType,
    industry,
    industryInsights
  };
};

// Corporate Evolution Insights component
const CorporateEvolutionInsights = ({ show, onClose, itemId, formValue, context }) => {
  if (!show) return null;

  const { industryInsights, paramType, industry } = context;

  // Get parameter type description
  const getParamTypeDescription = (type) => {
    switch(type) {
      case 'investment': return 'Initial capital investment and project setup costs';
      case 'loan': return 'Debt financing and loan structure parameters';
      case 'price': return 'Product or service pricing strategy';
      case 'process-cost': return 'Production and operational cost parameters';
      case 'quantity': return 'Production volume and capacity parameters';
      case 'sales-volume': return 'Sales volume and market penetration metrics';
      default: return 'General business parameters and metrics';
    }
  };

  // Get success strategies based on parameter type
  const getSuccessStrategies = (type) => {
    switch(type) {
      case 'investment':
        return [
          "Phase deployment to distribute capital requirements",
          "Strategic partnerships to share infrastructure costs",
          "Minimum viable product approach to validate before scaling"
        ];
      case 'price':
        return [
          "Value-based pricing over cost-plus approaches",
          "Tiered pricing strategies to capture different market segments",
          "Premium positioning through brand development"
        ];
      case 'process-cost':
        return [
          "Continuous improvement culture for cost reduction",
          "Supply chain innovation and vertical integration",
          "Technology leverage for operational efficiency"
        ];
      default:
        return [
          "Focus on core value proposition before diversification",
          "Data-driven decision making for resource allocation",
          "Adaptability in business model as market evolves"
        ];
    }
  };

  return (
      <div className="corporate-evolution-popup">
        <div className="evolution-header">
          <h3>
            <FontAwesomeIcon icon={faLightbulb} />
            Success Patterns: {formValue?.label}
          </h3>
          <button className="close-button" onClick={onClose}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="evolution-content">
          <div className="parameter-context">
            <div className="context-type">
              <span className="context-label">Parameter Type:</span>
              <span className="context-value">{paramType.replace('-', ' ')}</span>
              <p>{getParamTypeDescription(paramType)}</p>
            </div>
            <div className="context-industry">
              <span className="context-label">Industry Context:</span>
              <span className="context-value">{industry}</span>
            </div>
          </div>

          <div className="success-strategies">
            <h4><FontAwesomeIcon icon={faChartLine} /> Key Success Strategies</h4>
            <ul className="strategies-list">
              {getSuccessStrategies(paramType).map((strategy, index) => (
                  <li key={index} className="strategy-item">{strategy}</li>
              ))}
            </ul>
          </div>

          <div className="industry-examples">
            <h4><FontAwesomeIcon icon={faBuilding} /> How Leaders Evolved</h4>
            <div className="examples-list">
              {industryInsights.map((example, index) => (
                  <div key={index} className="example-card">
                    <div className="example-company">
                      <span className="company-name">{example.company}</span>
                      <span className="company-year">({example.year})</span>
                    </div>
                    <div className="example-text">{example.insight}</div>
                  </div>
              ))}
            </div>
          </div>

          {formValue?.value && (
              <div className="value-context">
                <h4><FontAwesomeIcon icon={faHistory} /> Value Context</h4>
                <p>
                  Your current value ({formValue.value}) would be considered {
                  formValue.value > 0 && formValue.value < 100 ? 'conservative in early-stage ventures' :
                      formValue.value >= 100 && formValue.value < 1000 ? 'typical for early-market entry' :
                          formValue.value >= 1000 ? 'ambitious, similar to scaled operations' : 'unusual'
                } for this parameter type.
                </p>
              </div>
          )}
        </div>
      </div>
  );
};

// Feedback form component
const FeedbackForm = ({ show, onClose, itemId, factualData }) => {
  const [feedbackType, setFeedbackType] = useState('helpful');
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  if (!show) return null;

  const handleSubmit = () => {
    setIsSubmitting(true);
    // Simulate API call
    setTimeout(() => {
      console.log('Feedback submitted:', { itemId, feedbackType, comment });
      setIsSubmitting(false);
      setIsSubmitted(true);

      // Reset form after a delay
      setTimeout(() => {
        setFeedbackType('helpful');
        setComment('');
        setIsSubmitted(false);
        onClose();
      }, 2000);
    }, 800);
  };

  return (
      <div className="feedback-form-popup">
        <div className="feedback-header">
          <h3>Provide Feedback</h3>
          <button className="close-button" onClick={onClose}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="feedback-content">
          {isSubmitted ? (
              <div className="feedback-success">
                <FontAwesomeIcon icon={faCheckCircle} />
                <p>Thank you for your feedback!</p>
              </div>
          ) : (
              <>
                <div className="feedback-type-selection">
                  <label>
                    <input
                        type="radio"
                        name="feedbackType"
                        value="helpful"
                        checked={feedbackType === 'helpful'}
                        onChange={() => setFeedbackType('helpful')}
                    />
                    This data was helpful
                  </label>
                  <label>
                    <input
                        type="radio"
                        name="feedbackType"
                        value="inaccurate"
                        checked={feedbackType === 'inaccurate'}
                        onChange={() => setFeedbackType('inaccurate')}
                    />
                    Data seems inaccurate
                  </label>
                  <label>
                    <input
                        type="radio"
                        name="feedbackType"
                        value="outdated"
                        checked={feedbackType === 'outdated'}
                        onChange={() => setFeedbackType('outdated')}
                    />
                    Data seems outdated
                  </label>
                  <label>
                    <input
                        type="radio"
                        name="feedbackType"
                        value="irrelevant"
                        checked={feedbackType === 'irrelevant'}
                        onChange={() => setFeedbackType('irrelevant')}
                    />
                    Not relevant to my case
                  </label>
                </div>

                <div className="feedback-comment">
                  <label htmlFor="feedback-comment">Additional comments (optional):</label>
                  <textarea
                      id="feedback-comment"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Please provide any specific feedback..."
                      rows={4}
                  />
                </div>

                <button
                    className="submit-feedback-button"
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </>
          )}
        </div>
      </div>
  );
};

const FactualPrecedenceBase = ({
                                 show,
                                 position,
                                 onClose,
                                 formValues,
                                 id,
                                 handleInputChange,
                                 getPrecedenceData
                               }) => {
  const [loading, setLoading] = useState(false);
  const [factualData, setFactualData] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [appliedValues, setAppliedValues] = useState([]);
  const [activeTab, setActiveTab] = useState('factual');
  const [showEvolutionInsights, setShowEvolutionInsights] = useState(false);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [parameterContext, setParameterContext] = useState(null);

  useEffect(() => {
    if (show && id) {
      fetchFactualPrecedence();
      // Get parameter context for evolution insights
      setParameterContext(getParameterContext(id, formValues[id]));
    }
  }, [show, id]);

  const fetchFactualPrecedence = async () => {
    setLoading(true);
    try {
      // getPrecedenceData is a function passed as prop - implementation varies based on data source
      const data = await getPrecedenceData(id, formValues[id]);
      setFactualData(data);
    } catch (error) {
      console.error('Error fetching factual precedence:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyValue = (value, source) => {
    if (value && id) {
      handleInputChange({ target: { value } }, id, 'value');

      // Add source to remarks if provided
      if (source) {
        const updatedRemarks = `${formValues[id].remarks || ''}\nSource: ${source}`;
        handleInputChange({ target: { value: updatedRemarks } }, id, 'remarks');
      }

      setAppliedValues([...appliedValues, { value, source }]);
    }
  };

  if (!show) return null;

  return (
      <div className="factual-precedence-popup" style={{ top: position.top, left: position.left }}>
        <div className="factual-precedence-header">
          <h3>Parameter Insights: {formValues[id]?.label}</h3>
          <div className="popup-tabs">
            <button
                className={`tab-button ${activeTab === 'factual' ? 'active' : ''}`}
                onClick={() => setActiveTab('factual')}
            >
              Factual Precedence
            </button>
            <button
                className={`tab-button ${activeTab === 'evolution' ? 'active' : ''}`}
                onClick={() => setActiveTab('evolution')}
            >
              Success Patterns
            </button>
          </div>
          <button className="close-button" onClick={onClose}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="factual-precedence-content">
          {activeTab === 'factual' && (
              loading ? (
                  <div className="loading-state">Loading factual data...</div>
              ) : factualData ? (
                  <>
                    {/* Show data status indicators */}
                    {(factualData.isStale || factualData.isFallback) && (
                      <div className="data-status-warning">
                        <FontAwesomeIcon icon={faInfoCircle} />
                        <span>
                          {factualData.isStale && `Using cached data: ${factualData.staleReason}`}
                          {factualData.isFallback && `Using default values: ${factualData.fallbackReason}`}
                        </span>
                      </div>
                    )}
                    
                    <div className="factual-summary">
                      <h4>Industry Standard Information</h4>
                      <p>{factualData.summary}</p>
                    </div>

                    <div className="factual-examples">
                      <h4>Reference Values</h4>
                      <table className="reference-table">
                        <thead>
                        <tr>
                          <th>Source</th>
                          <th>Value</th>
                          <th>Year</th>
                          <th>Action</th>
                        </tr>
                        </thead>
                        <tbody>
                        {factualData.examples.map((example, index) => (
                            <tr
                                key={index}
                                className={selectedSource === example.source ? 'selected-row' : ''}
                                onClick={() => setSelectedSource(example.source)}
                            >
                              <td>{example.entity}</td>
                              <td>{example.value}{example.unit ? ` ${example.unit}` : ''}</td>
                              <td>{example.year || 'N/A'}</td>
                              <td>
                                <button
                                    className="apply-value-button"
                                    onClick={() => applyValue(example.value, example.source)}
                                    disabled={appliedValues.some(item => item.value === example.value)}
                                >
                                  {appliedValues.some(item => item.value === example.value) ? (
                                      <><FontAwesomeIcon icon={faCheckCircle} /> Applied</>
                                  ) : (
                                      'Apply'
                                  )}
                                </button>
                              </td>
                            </tr>
                        ))}
                        </tbody>
                      </table>
                    </div>

                    {factualData.recommendedValue && (
                        <div className="factual-recommendation">
                          <h4>Recommended Value</h4>
                          <div className="recommendation-box">
                            <p>
                              <strong>{factualData.recommendedValue}</strong>
                              {factualData.recommendationRationale && (
                                  <span className="rationale"> - {factualData.recommendationRationale}</span>
                              )}
                            </p>
                            <button
                                className="apply-recommendation-button"
                                onClick={() => applyValue(factualData.recommendedValue, "Industry Recommendation")}
                            >
                              Apply Recommendation
                            </button>
                          </div>
                        </div>
                    )}

                    <div className="feedback-section">
                      <button
                          className="feedback-button"
                          onClick={() => setShowFeedbackForm(true)}
                      >
                        Provide Feedback on This Data
                      </button>
                    </div>
                  </>
              ) : (
                  <div className="no-data-message">
                    <FontAwesomeIcon icon={faInfoCircle} />
                    <p>No factual precedence data available for this parameter.</p>
                    <button onClick={fetchFactualPrecedence}>Retry</button>
                  </div>
              )
          )}

          {activeTab === 'evolution' && parameterContext && (
              <CorporateEvolutionInsights
                  show={activeTab === 'evolution'}
                  onClose={() => setActiveTab('factual')}
                  itemId={id}
                  formValue={formValues[id]}
                  context={parameterContext}
              />
          )}
        </div>

        {/* Feedback Form */}
        <FeedbackForm
            show={showFeedbackForm}
            onClose={() => setShowFeedbackForm(false)}
            itemId={id}
            factualData={factualData}
        />
      </div>
  );
};

export default FactualPrecedenceBase;