import React, { useState } from 'react';
import FactualPrecedenceBase from './FactualPrecedenceBase';
import axiosInstance, { apiCircuitBreaker, makeRequestWithFallback } from '../../../../../utils/axiosConfig';

/**
 * Enhanced API client for Factual Precedence data with improved caching and error handling
 */
const getAPIPrecedenceData = async (itemId, formValue, retryCount = 0) => {
  // Create a cache key based on the item ID and relevant form properties
  const cacheKey = `factual-precedence-${itemId}-${JSON.stringify({
    label: formValue?.label || '',
    value: formValue?.value || '',
    type: formValue?.type || '',
  })}`;

  // Check for cached data
  const cachedData = sessionStorage.getItem(cacheKey);
  if (cachedData) {
    try {
      const parsedData = JSON.parse(cachedData);
      const cacheTime = parsedData.timestamp;
      // Use cache if it's less than 30 minutes old
      if (Date.now() - cacheTime < 30 * 60 * 1000) {
        console.log('Using cached factual precedence data');
        return parsedData.data;
      }
    } catch (e) {
      console.warn('Error parsing cached data:', e);
    }
  }

  // Max retry attempts
  const MAX_RETRIES = 3;
  const RETRY_DELAY = 1000; // Start with 1 second delay

  try {
    // Use circuit breaker pattern
    const response = await apiCircuitBreaker.call(async () => {
      return await axiosInstance.post('http://localhost:3060/api/factual-precedence', {
        itemId,
        formContext: {
          label: formValue?.label || '',
          value: formValue?.value || '',
          type: formValue?.type || '',
          // Include any additional context to help with data relevance
          remarks: formValue?.remarks || '',
        }
      }, {
        // Set timeout to ensure UI responsiveness
        timeout: 8000,
        headers: {
          'Content-Type': 'application/json',
        },
        // Add retry configuration
        validateStatus: function (status) {
          return status >= 200 && status < 500; // Don't reject if server returns 4xx
        },
        _retryCount: retryCount // Pass retry count to axios config
      });
    });

    if (response.data.success) {
      // Process and enhance the data
      const enhancedData = enhancePrecedenceData(response.data.factualPrecedence, formValue);

      // Cache the enhanced data
      sessionStorage.setItem(cacheKey, JSON.stringify({
        data: enhancedData,
        timestamp: Date.now()
      }));

      return enhancedData;
    }

    throw new Error(response.data.message || 'Failed to fetch data');
  } catch (error) {
    console.error('API error:', error);

    // Check if it's a network error and we should retry
    if (error.code === 'ERR_NETWORK' && retryCount < MAX_RETRIES) {
      console.log(`Network error detected. Retrying... (attempt ${retryCount + 1}/${MAX_RETRIES})`);
      
      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * Math.pow(2, retryCount)));
      
      // Retry the request
      return getAPIPrecedenceData(itemId, formValue, retryCount + 1);
    }

    // If we have stale cache, use it as fallback
    if (cachedData) {
      try {
        console.warn('Using stale cache as fallback due to network error');
        const parsedData = JSON.parse(cachedData);
        // Mark it as stale so UI can show appropriate warning
        parsedData.data.isStale = true;
        parsedData.data.staleReason = 'Network error - using cached data';
        return parsedData.data;
      } catch (e) {
        console.error('Failed to use cache fallback:', e);
      }
    }

    // Create emergency fallback data based on parameter type
    const fallbackData = generateFallbackData(itemId, formValue);
    if (fallbackData) {
      // Mark as fallback data
      fallbackData.isFallback = true;
      fallbackData.fallbackReason = error.code === 'ERR_NETWORK' 
        ? 'Network connection error - using default values' 
        : 'Service unavailable - using default values';
      return fallbackData;
    }

    // If all else fails, return a minimal fallback
    return {
      summary: "Service temporarily unavailable. Using default values.",
      examples: [],
      confidenceLevel: "low",
      isFallback: true,
      fallbackReason: error.message || 'Unknown error'
    };
  }
};

/**
 * Enhance the precedence data with additional insights and context
 */
const enhancePrecedenceData = (data, formValue) => {
  if (!data) return null;

  // Copy data to avoid mutation
  const enhancedData = { ...data };

  // Sort examples by relevance and recency
  if (enhancedData.examples && enhancedData.examples.length > 0) {
    enhancedData.examples.sort((a, b) => {
      // Prioritize by year if available (more recent first)
      if (a.year && b.year) {
        return b.year - a.year;
      }
      return 0;
    });
  }

  // Add confidence level if not present
  if (!enhancedData.confidenceLevel) {
    enhancedData.confidenceLevel = calculateConfidenceLevel(enhancedData);
  }

  // Add contextual note if the value is significantly different from recommendation
  if (enhancedData.recommendedValue && formValue?.value) {
    const recommendedVal = parseFloat(enhancedData.recommendedValue);
    const currentVal = parseFloat(formValue.value);

    if (!isNaN(recommendedVal) && !isNaN(currentVal)) {
      const percentDiff = Math.abs((currentVal - recommendedVal) / recommendedVal) * 100;

      if (percentDiff > 30) {
        enhancedData.contextualNote = currentVal > recommendedVal
            ? "Your value is significantly higher than typical industry standards. Consider reviewing your assumptions or documenting your rationale."
            : "Your value is significantly lower than typical industry standards. Ensure this reflects realistic conditions for your specific case.";
      }
    }
  }

  return enhancedData;
};

/**
 * Calculate a confidence level for the precedence data
 */
const calculateConfidenceLevel = (data) => {
  if (!data || !data.examples) return "low";

  // Base confidence on number of examples, recency, and source diversity
  const exampleCount = data.examples.length;

  if (exampleCount === 0) return "low";
  if (exampleCount < 3) return "medium";

  // Check for recency
  const currentYear = new Date().getFullYear();
  const recentExamples = data.examples.filter(ex => ex.year && ex.year >= currentYear - 5);

  // Check for source diversity
  const uniqueSources = new Set(data.examples.map(ex => ex.entity)).size;

  if (recentExamples.length >= 2 && uniqueSources >= 3) {
    return "high";
  } else if (recentExamples.length >= 1 && uniqueSources >= 2) {
    return "medium-high";
  }

  return "medium";
};

/**
 * Generate fallback data if API fails and no cache is available
 */
const generateFallbackData = (itemId, formValue) => {
  const label = formValue?.label || 'parameter';
  const type = formValue?.type || '';

  // Check if this is a lifetime-related parameter
  if (itemId.includes('lifetime') || label.toLowerCase().includes('lifetime')) {
    return {
      summary: "Industrial equipment and facility lifetimes vary by sector, technology type, and maintenance practices. Typical designs aim for 20-40 year operational periods.",
      examples: [
        { entity: "General Industry", value: 25, unit: "years", year: 2023, source: "Industrial Engineering Handbook" },
        { entity: "Best Practice", value: 30, unit: "years", year: 2022, source: "Industry Standards" }
      ],
      recommendedValue: 25,
      recommendationRationale: "Balance of typical industry averages accounting for technological obsolescence",
      confidenceLevel: "medium"
    };
  }

  // Check if this is a price-related parameter
  if (itemId.includes('price') || label.toLowerCase().includes('price')) {
    // This is just a generic fallback
    return {
      summary: "Pricing strategies vary based on market position, production costs, and competitive landscape. Historical trends should inform projections.",
      examples: [
        { entity: "Market Average", value: 2.50, unit: "$/unit", year: 2023, source: "Market Analysis" },
        { entity: "Premium Segment", value: 3.75, unit: "$/unit", year: 2023, source: "Industry Report" }
      ],
      recommendedValue: 2.75,
      recommendationRationale: "Competitive positioning with slight premium over market average",
      confidenceLevel: "low"
    };
  }

  // Check for carbon-related parameters
  if (itemId.includes('carbon') || type.includes('carbon') || label.toLowerCase().includes('carbon')) {
    return {
      summary: "Carbon emissions and incentives vary by region, industry, and regulatory framework. Values depend on local policies and carbon markets.",
      examples: [
        { entity: "EU ETS", value: 85, unit: "€/tCO2", year: 2023, source: "Carbon Market Report" },
        { entity: "California", value: 30, unit: "$/tCO2", year: 2023, source: "CARB" }
      ],
      recommendedValue: 50,
      recommendationRationale: "Mid-range carbon price accounting for global variations",
      confidenceLevel: "low"
    };
  }

  // Check for location/coordinate-based parameters
  if (itemId.includes('location') || itemId.includes('coordinate') || type.includes('coordinate')) {
    return {
      summary: "Location-specific data unavailable. Regional characteristics may vary significantly based on local conditions.",
      examples: [
        { entity: "Similar Regions", value: "Variable", unit: "varies", year: 2023, source: "Regional Studies" }
      ],
      recommendedValue: null,
      recommendationRationale: "Location-specific analysis required",
      confidenceLevel: "low"
    };
  }

  // Check for efficiency-related parameters
  if (itemId.includes('efficiency') || label.toLowerCase().includes('efficiency')) {
    return {
      summary: "Process efficiency depends on technology maturity, operational conditions, and maintenance practices.",
      examples: [
        { entity: "Industry Average", value: 85, unit: "%", year: 2023, source: "Process Engineering Guide" },
        { entity: "Best-in-Class", value: 95, unit: "%", year: 2023, source: "Technology Review" }
      ],
      recommendedValue: 85,
      recommendationRationale: "Conservative estimate based on typical industrial performance",
      confidenceLevel: "medium"
    };
  }

  // Check for capacity-related parameters
  if (itemId.includes('capacity') || label.toLowerCase().includes('capacity')) {
    return {
      summary: "Capacity parameters should align with project scale and market demand projections.",
      examples: [
        { entity: "Small Scale", value: 1000, unit: "units/year", year: 2023, source: "Industry Survey" },
        { entity: "Large Scale", value: 10000, unit: "units/year", year: 2023, source: "Market Analysis" }
      ],
      recommendedValue: 5000,
      recommendationRationale: "Mid-scale operation balancing efficiency and market risk",
      confidenceLevel: "low"
    };
  }

  // Generic fallback for other cases
  return {
    summary: `No specific data available for ${label}. Consider industry benchmarks or consulting with domain experts.`,
    examples: [],
    confidenceLevel: "low"
  };
};

/**
 * Submit user feedback about factual precedence data quality
 */
const submitFeedback = async (itemId, feedbackType, comment) => {
  try {
    const response = await makeRequestWithFallback({
      method: 'post',
      url: 'http://localhost:3060/api/factual-precedence/feedback',
      data: {
        itemId,
        feedbackType,
        comment,
        timestamp: new Date().toISOString()
      },
      timeout: 5000 // Shorter timeout for feedback
    }, (error) => {
      // Fallback: store feedback locally for later submission
      const localFeedback = JSON.parse(localStorage.getItem('pendingFeedback') || '[]');
      localFeedback.push({
        itemId,
        feedbackType,
        comment,
        timestamp: new Date().toISOString(),
        error: error.message
      });
      localStorage.setItem('pendingFeedback', JSON.stringify(localFeedback));
      console.log('Feedback stored locally for later submission');
      return { success: true, offline: true };
    });

    return response.success;
  } catch (error) {
    console.error('Error submitting feedback:', error);
    return false;
  }
};

const APIFactualPrecedence = (props) => {
  const [feedbackStatus, setFeedbackStatus] = useState(null);

  const handleFeedbackSubmit = async (itemId, feedback) => {
    const success = await submitFeedback(
        itemId,
        feedback.type,
        feedback.comment
    );

    setFeedbackStatus({
      success,
      message: success
          ? 'Thank you for your feedback!'
          : 'Failed to submit feedback. Please try again.'
    });

    // Clear status after 3 seconds
    setTimeout(() => {
      setFeedbackStatus(null);
    }, 3000);
  };

  return (
      <FactualPrecedenceBase
          {...props}
          getPrecedenceData={getAPIPrecedenceData}
          onFeedbackSubmit={handleFeedbackSubmit}
          feedbackStatus={feedbackStatus}
      />
  );
};

export { getAPIPrecedenceData };
export default APIFactualPrecedence;
