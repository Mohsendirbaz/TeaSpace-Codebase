import React, { useState, useEffect } from 'react';
import FactualPrecedenceBase from './FactualPrecedenceBase';
import { keyPointsData, formValueKeyPointRelevance } from '../../../data/keyPointsMapping';
import axios from 'axios';

/**
 * Enhanced filter panel with improved UX and intelligent filter suggestions
 */
const FilterPanel = ({ id, selectedFilters, onFilterChange, industryContext }) => {
  const [expandedCategories, setExpandedCategories] = useState({});
  const [suggestedFilters, setSuggestedFilters] = useState([]);

  // Get relevant categories for this parameter
  const relevantCategories = formValueKeyPointRelevance[id] || [];

  useEffect(() => {
    // Auto-expand first category
    if (relevantCategories.length > 0) {
      setExpandedCategories(prev => ({
        ...prev,
        [relevantCategories[0]]: true
      }));
    }

    // Generate suggested filters based on parameter context
    if (industryContext) {
      const suggestions = [];

      // Add relevant industry filters
      if (industryContext.includes('energy') || industryContext.includes('power')) {
        suggestions.push({ category: 'industryType', id: 'energy' });
      } else if (industryContext.includes('chemical')) {
        suggestions.push({ category: 'industryType', id: 'chemical' });
      } else if (industryContext.includes('manufacturing')) {
        suggestions.push({ category: 'industryType', id: 'manufacturing' });
      }

      // Add technology context if available
      if (relevantCategories.includes('technology')) {
        if (industryContext.includes('new') || industryContext.includes('innovative')) {
          suggestions.push({ category: 'technology', id: 'emerging' });
        } else if (industryContext.includes('standard') || industryContext.includes('traditional')) {
          suggestions.push({ category: 'technology', id: 'conventional' });
        }
      }

      // Add region context if available
      if (relevantCategories.includes('region')) {
        if (industryContext.includes('north america') || industryContext.includes('us ')) {
          suggestions.push({ category: 'region', id: 'north_america' });
        } else if (industryContext.includes('europe')) {
          suggestions.push({ category: 'region', id: 'europe' });
        } else if (industryContext.includes('asia')) {
          suggestions.push({ category: 'region', id: 'asia_pacific' });
        }
      }

      setSuggestedFilters(suggestions);
    }
  }, [id, relevantCategories, industryContext]);

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const handleFilterToggle = (category, filterId) => {
    onFilterChange(category, filterId);
  };

  const clearAllFilters = () => {
    relevantCategories.forEach(category => {
      const options = keyPointsData[category] || [];
      options.forEach(option => {
        if (selectedFilters[category]?.includes(option.id)) {
          onFilterChange(category, option.id);
        }
      });
    });
  };

  const applySuggestedFilters = () => {
    suggestedFilters.forEach(suggestion => {
      if (!selectedFilters[suggestion.category]?.includes(suggestion.id)) {
        onFilterChange(suggestion.category, suggestion.id);
      }
    });
  };

  // Count active filters
  const activeFilterCount = Object.values(selectedFilters)
      .reduce((count, filters) => count + (filters?.length || 0), 0);

  return (
      <div className="filter-panel">
        <div className="filter-panel-header">
          <h4>Refine Results</h4>

          <div className="filter-actions">
            {activeFilterCount > 0 && (
                <button
                    className="clear-filters-button"
                    onClick={clearAllFilters}
                    title="Clear all active filters"
                >
                  Clear All ({activeFilterCount})
                </button>
            )}

            {suggestedFilters.length > 0 && (
                <button
                    className="suggested-filters-button"
                    onClick={applySuggestedFilters}
                    title="Apply intelligent filter suggestions based on parameter context"
                >
                  Suggested Filters
                </button>
            )}
          </div>
        </div>

        {relevantCategories.map(category => (
            <div key={category} className="filter-category">
              <h5
                  onClick={() => toggleCategory(category)}
                  className={expandedCategories[category] ? 'expanded' : 'collapsed'}
              >
                {keyPointsData[category][0]?.label.split(' ')[0]}
                <span className="category-toggle">{expandedCategories[category] ? '−' : '+'}</span>
              </h5>

              {expandedCategories[category] && (
                  <div className="filter-options">
                    {keyPointsData[category].map(option => {
                      const isSuggested = suggestedFilters.some(
                          s => s.category === category && s.id === option.id
                      );

                      return (
                          <label
                              key={option.id}
                              className={`filter-checkbox ${isSuggested ? 'suggested' : ''}`}
                          >
                            <input
                                type="checkbox"
                                checked={selectedFilters[category]?.includes(option.id) || false}
                                onChange={() => handleFilterToggle(category, option.id)}
                            />
                            {option.label}
                            {isSuggested && <span className="suggested-badge">Suggested</span>}
                          </label>
                      );
                    })}
                  </div>
              )}
            </div>
        ))}
      </div>
  );
};

/**
 * Enhanced API client for filtered factual precedence data
 */
const getFilteredPrecedenceData = async (itemId, formValue, filters) => {
  // Create cache key based on item ID, form values and filters
  const cacheKey = `filtered-precedence-${itemId}-${JSON.stringify({
    form: {
      label: formValue?.label || '',
      value: formValue?.value || '',
      type: formValue?.type || '',
    },
    filters
  })}`;

  // Check cache first
  const cachedData = sessionStorage.getItem(cacheKey);
  if (cachedData) {
    try {
      const parsedData = JSON.parse(cachedData);
      const cacheTime = parsedData.timestamp;
      // Use cache if it's less than 30 minutes old
      if (Date.now() - cacheTime < 30 * 60 * 1000) {
        console.log('Using cached filtered precedence data');
        return parsedData.data;
      }
    } catch (e) {
      console.warn('Error parsing cached data:', e);
    }
  }

  try {
    const response = await axios.post('http://localhost:3060/api/factual-precedence/filtered', {
      itemId,
      formContext: {
        label: formValue?.label || '',
        value: formValue?.value || '',
        type: formValue?.type || '',
        remarks: formValue?.remarks || '',
      },
      filters
    }, {
      timeout: 8000
    });

    if (response.data.success) {
      // Cache the response
      sessionStorage.setItem(cacheKey, JSON.stringify({
        data: response.data.factualPrecedence,
        timestamp: Date.now()
      }));

      return response.data.factualPrecedence;
    }

    throw new Error(response.data.message || 'Failed to fetch filtered data');
  } catch (error) {
    console.error('API error:', error);

    // If we have stale cache, use it as fallback
    if (cachedData) {
      try {
        console.warn('Using stale cache as fallback');
        return JSON.parse(cachedData).data;
      } catch (e) {
        console.error('Failed to use cache fallback:', e);
      }
    }

    // If no filters are applied, try the non-filtered endpoint as fallback
    const hasActiveFilters = Object.values(filters).some(f => f.length > 0);
    if (!hasActiveFilters) {
      try {
        const fallbackResponse = await axios.post('http://localhost:3060/api/factual-precedence', {
          itemId,
          formContext: {
            label: formValue?.label || '',
            value: formValue?.value || '',
            type: formValue?.type || '',
          }
        });

        if (fallbackResponse.data.success) {
          return fallbackResponse.data.factualPrecedence;
        }
      } catch (fallbackError) {
        console.error('Fallback API error:', fallbackError);
      }
    }

    throw error;
  }
};

/**
 * Extract industry context from form values for smarter filtering
 */
const extractIndustryContext = (formValue) => {
  if (!formValue) return '';

  // Combine label and remarks to extract context
  const combinedText = `${formValue.label || ''} ${formValue.remarks || ''}`.toLowerCase();

  // Extract key industry terms
  const industryTerms = [];

  if (/energy|power|electricity|renewable/i.test(combinedText)) {
    industryTerms.push('energy');
  }

  if (/chemical|material|compound/i.test(combinedText)) {
    industryTerms.push('chemical');
  }

  if (/manufacture|production|assembly|factory/i.test(combinedText)) {
    industryTerms.push('manufacturing');
  }

  if (/health|medical|pharma|patient/i.test(combinedText)) {
    industryTerms.push('healthcare');
  }

  if (/emerging|innovative|new|novel/i.test(combinedText)) {
    industryTerms.push('emerging technology');
  }

  if (/conventional|traditional|established/i.test(combinedText)) {
    industryTerms.push('conventional technology');
  }

  return industryTerms.join(', ');
};

const FilteredFactualPrecedence = (props) => {
  const { id, formValues } = props;
  const [selectedFilters, setSelectedFilters] = useState({});
  const [industryContext, setIndustryContext] = useState('');

  useEffect(() => {
    if (id && formValues[id]) {
      // Initialize filter state
      const relevantCategories = formValueKeyPointRelevance[id] || [];
      const initialFilters = {};

      relevantCategories.forEach(category => {
        initialFilters[category] = [];
      });

      setSelectedFilters(initialFilters);

      // Extract industry context for smarter filtering
      setIndustryContext(extractIndustryContext(formValues[id]));
    }
  }, [id, formValues]);

  const handleFilterChange = (category, filterId) => {
    setSelectedFilters(prev => {
      const categoryFilters = [...(prev[category] || [])];
      const index = categoryFilters.indexOf(filterId);

      if (index >= 0) {
        categoryFilters.splice(index, 1);
      } else {
        categoryFilters.push(filterId);
      }

      return {
        ...prev,
        [category]: categoryFilters
      };
    });
  };

  const getPrecedenceData = async (itemId, formValue) => {
    const hasActiveFilters = Object.values(selectedFilters).some(filters => filters.length > 0);

    if (hasActiveFilters) {
      return getFilteredPrecedenceData(itemId, formValue, selectedFilters);
    } else {
      try {
        const response = await axios.post('http://localhost:3060/api/factual-precedence', {
          itemId,
          formContext: {
            label: formValue?.label || '',
            value: formValue?.value || '',
            type: formValue?.type || '',
          }
        });

        if (response.data.success) {
          return response.data.factualPrecedence;
        }
        throw new Error(response.data.message || 'Failed to fetch data');
      } catch (error) {
        console.error('API error:', error);
        throw error;
      }
    }
  };

  // Check if there are any active filters
  const hasActiveFilters = Object.values(selectedFilters).some(filters => filters.length > 0);
  const activeFilterCount = Object.values(selectedFilters)
      .reduce((count, filters) => count + (filters?.length || 0), 0);

  return (
      <div className="filtered-factual-precedence">
        <FilterPanel
            id={id}
            selectedFilters={selectedFilters}
            onFilterChange={handleFilterChange}
            industryContext={industryContext}
        />

        {activeFilterCount > 0 && (
            <div className="active-filters-bar">
          <span className="active-filters-count">
            {activeFilterCount} active {activeFilterCount === 1 ? 'filter' : 'filters'}
          </span>
              <span className="active-filters-info">
            Showing specialized data relevant to your selected criteria
          </span>
            </div>
        )}

        <FactualPrecedenceBase
            {...props}
            getPrecedenceData={getPrecedenceData}
        />
      </div>
  );
};

export default FilteredFactualPrecedence;