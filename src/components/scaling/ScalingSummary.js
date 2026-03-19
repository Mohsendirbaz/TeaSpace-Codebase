import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardContent } from '../ui/Card';

/**
 * @file ScalingSummary.js
 * @description Component that displays a summary of scaling values with cumulative calculation capabilities
 * @module components/scaling/ScalingSummary
 * @requires react, framer-motion, ../ui/Card
 */

/**
 * ScalingSummary Component
 * Displays a table of scaling values with filtering, search, and expandable details
 */
const ScalingSummary = ({
    items,
    tabConfigs,
    onExpressionChange,
    V,
    R,
    toggleV,
    toggleR
}) => {
    const [itemExpressions, setItemExpressions] = useState({});
    const [intermediateResults, setIntermediateResults] = useState({});
    const [lastUpdated, setLastUpdated] = useState(null);
    const [expandedRows, setExpandedRows] = useState({});
    const [filterOptions, setFilterOptions] = useState({
        showVItems: true,
        showRItems: true,
        showOtherItems: true,
        searchTerm: '',
    });

    // Process items with awareness of cumulative nature
    useEffect(() => {
        const newResults = {};

        items.forEach(item => {
            // Start with original value
            newResults[item.id] = {
                baseValue: item.originalValue,
                currentValue: item.originalValue,
                steps: []
            };

            // If there are scaledValues, process them in sequence to simulate the cumulative effect
            if (item.scaledValues) {
                const tabIds = Object.keys(item.scaledValues).sort((a, b) => {
                    // Sort based on the index provided in tabConfigs
                    const indexA = tabConfigs.findIndex(tab => tab.id === a);
                    const indexB = tabConfigs.findIndex(tab => tab.id === b);
                    return indexA - indexB;
                });

                // Track running value for cumulative calculation
                let cumulativeValue = item.originalValue;

                tabIds.forEach(tabId => {
                    const scaledValue = item.scaledValues[tabId];
                    const tabConfig = tabConfigs.find(tab => tab.id === tabId);

                    if (tabConfig) {
                        // Add a step showing how this tab's value affects the cumulative result
                        newResults[item.id].steps.push({
                            tabId,
                            tabName: tabConfig.label,
                            inputValue: cumulativeValue,
                            scaledValue,
                            resultValue: scaledValue // The next tab will use this as input
                        });

                        // Update the cumulative value for the next tab
                        cumulativeValue = scaledValue;
                    }
                });

                // Set the final cumulative value
                newResults[item.id].currentValue = cumulativeValue;
            }
        });

        setIntermediateResults(newResults);
        setLastUpdated(Date.now());
    }, [items, tabConfigs]);

    // Toggle row expansion
    const toggleRowExpansion = useCallback((itemId) => {
        setExpandedRows(prev => ({
            ...prev,
            [itemId]: !prev[itemId]
        }));
    }, []);

    // Handle expression change
    const handleExpressionChange = useCallback((itemId, expression) => {
        setItemExpressions(prev => ({
            ...prev,
            [itemId]: expression
        }));

        if (onExpressionChange) {
            onExpressionChange(itemId, expression);
        }
    }, [onExpressionChange]);

    // Check if column is within parentheses (for formatting)
    const isInParenthesis = useCallback((tabId) => {
        const tabIndex = tabConfigs.findIndex(tab => tab.id === tabId);
        return tabConfigs[tabIndex]?.isParenthesis || false;
    }, [tabConfigs]);

    // Handle filter change
    const handleFilterChange = useCallback((filterName, value) => {
        setFilterOptions(prev => ({
            ...prev,
            [filterName]: value
        }));
    }, []);

    // Filter items based on current filter options
    const filteredItems = useMemo(() => {
        return items.filter(item => {
            // Filter by V/R/Other categories
            const isVItem = !!item.vKey;
            const isRItem = !!item.rKey;

            if (isVItem && !filterOptions.showVItems) return false;
            if (isRItem && !filterOptions.showRItems) return false;
            if (!isVItem && !isRItem && !filterOptions.showOtherItems) return false;

            // Filter by search term
            if (filterOptions.searchTerm) {
                const searchLower = filterOptions.searchTerm.toLowerCase();
                const labelMatch = item.label.toLowerCase().includes(searchLower);
                const vKeyMatch = item.vKey && item.vKey.toLowerCase().includes(searchLower);
                const rKeyMatch = item.rKey && item.rKey.toLowerCase().includes(searchLower);

                return labelMatch || vKeyMatch || rKeyMatch;
            }

            return true;
        });
    }, [items, filterOptions]);

    return (
        <Card className="scaling-summary">
            <CardHeader>
                <div className="scaling-summary-header-container">
                    <h3 className="scaling-summary-title">Scaling Summary</h3>

                    <div className="scaling-summary-filters">
                        <div className="scaling-summary-filter-group">
                            <label className="scaling-filter-label">
                                <input
                                    type="checkbox"
                                    checked={filterOptions.showVItems}
                                    onChange={(e) => handleFilterChange('showVItems', e.target.checked)}
                                    className="scaling-filter-checkbox"
                                />
                                V Items
                            </label>

                            <label className="scaling-filter-label">
                                <input
                                    type="checkbox"
                                    checked={filterOptions.showRItems}
                                    onChange={(e) => handleFilterChange('showRItems', e.target.checked)}
                                    className="scaling-filter-checkbox"
                                />
                                R Items
                            </label>

                            <label className="scaling-filter-label">
                                <input
                                    type="checkbox"
                                    checked={filterOptions.showOtherItems}
                                    onChange={(e) => handleFilterChange('showOtherItems', e.target.checked)}
                                    className="scaling-filter-checkbox"
                                />
                                Other Items
                            </label>
                        </div>

                        <div className="scaling-summary-search">
                            <input
                                type="text"
                                value={filterOptions.searchTerm}
                                onChange={(e) => handleFilterChange('searchTerm', e.target.value)}
                                placeholder="Search items..."
                                className="scaling-summary-search-input"
                            />
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="scaling-summary-container">
                    <table className="scaling-summary-table">
                        <thead>
                        <tr className="scaling-summary-header">
                            <th className="scaling-summary-cell">Item</th>
                            <th className="scaling-summary-cell">V/R</th>
                            <th className="scaling-summary-cell scaling-summary-cell-right">Original</th>
                            {tabConfigs.map((tab) => (
                                <th
                                    key={tab.id}
                                    className={`scaling-summary-cell scaling-summary-cell-right ${
                                        isInParenthesis(tab.id) ? 'scaling-summary-parenthesis' : ''
                                    }`}
                                >
                                    {tab.label || `Scale ${tab.id}`}
                                </th>
                            ))}
                            <th className="scaling-summary-cell scaling-summary-cell-right">Expression</th>
                            <th className="scaling-summary-cell scaling-summary-cell-right scaling-summary-result">Final Result</th>
                        </tr>
                        </thead>
                        <tbody>
                        <AnimatePresence>
                            {filteredItems.map(item => (
                                <React.Fragment key={item.id}>
                                    <motion.tr
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        transition={{ duration: 0.2 }}
                                        className={`scaling-summary-row ${expandedRows[item.id] ? 'scaling-summary-row-expanded' : ''}`}
                                        onClick={() => toggleRowExpansion(item.id)}
                                    >
                                        <td className="scaling-summary-cell">{item.label}</td>

                                        <td className="scaling-summary-cell scaling-summary-vr-cell">
                                            {item.vKey && (
                                                <div className="summary-vr-checkbox">
                                                    <span className="summary-vr-label">{item.vKey}</span>
                                                    {V && toggleV && (
                                                        <input
                                                            type="checkbox"
                                                            checked={V[item.vKey] === 'on'}
                                                            onChange={() => toggleV(item.vKey)}
                                                            onClick={(e) => e.stopPropagation()}
                                                            className="summary-vr-toggle"
                                                        />
                                                    )}
                                                </div>
                                            )}

                                            {item.rKey && (
                                                <div className="summary-vr-checkbox">
                                                    <span className="summary-vr-label">{item.rKey}</span>
                                                    {R && toggleR && (
                                                        <input
                                                            type="checkbox"
                                                            checked={R[item.rKey] === 'on'}
                                                            onChange={() => toggleR(item.rKey)}
                                                            onClick={(e) => e.stopPropagation()}
                                                            className="summary-vr-toggle"
                                                        />
                                                    )}
                                                </div>
                                            )}
                                        </td>

                                        <td className="scaling-summary-cell scaling-summary-cell-right">
                                            <motion.span
                                                key={`${item.id}-original-${lastUpdated}`}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                            >
                                                {item.originalValue.toFixed(2)}
                                            </motion.span>
                                        </td>

                                        {tabConfigs.map((tab) => (
                                            <td
                                                key={tab.id}
                                                className={`scaling-summary-cell scaling-summary-cell-right ${
                                                    isInParenthesis(tab.id) ? 'scaling-summary-parenthesis' : ''
                                                }`}
                                            >
                                                <motion.span
                                                    key={`${item.id}-${tab.id}-${lastUpdated}`}
                                                    initial={{ opacity: 0, y: 10 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                >
                                                    {(item.scaledValues[tab.id] || item.originalValue).toFixed(2)}
                                                </motion.span>
                                            </td>
                                        ))}

                                        <td className="scaling-summary-cell">
                                            <input
                                                type="text"
                                                className="scaling-summary-expression-input"
                                                placeholder="Enter formula"
                                                value={itemExpressions[item.id] || ''}
                                                onChange={(e) => handleExpressionChange(item.id, e.target.value)}
                                                onClick={(e) => e.stopPropagation()} // Prevent row toggle when clicking input
                                            />
                                        </td>

                                        <td className="scaling-summary-cell scaling-summary-cell-right scaling-summary-result">
                                            <div className="scaling-summary-result-container">
                                                <motion.span
                                                    key={`${item.id}-result-${lastUpdated}`}
                                                    initial={{ opacity: 0, scale: 0.9 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                >
                                                    {(item.finalResult || intermediateResults[item.id]?.currentValue || item.originalValue).toFixed(2)}
                                                </motion.span>
                                            </div>
                                        </td>
                                    </motion.tr>

                                    {/* Expanded details row showing calculation steps */}
                                    {expandedRows[item.id] && intermediateResults[item.id]?.steps?.length > 0 && (
                                        <motion.tr
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="scaling-summary-steps-row"
                                        >
                                            <td colSpan={4 + tabConfigs.length} className="scaling-summary-steps-cell">
                                                <div className="scaling-summary-steps">
                                                    <h4>Calculation Steps for {item.label}</h4>
                                                    <div className="scaling-summary-steps-list">
                                                        <div className="scaling-summary-step scaling-summary-step-header">
                                                            <span>Tab</span>
                                                            <span>Input Value</span>
                                                            <span>→</span>
                                                            <span>Result</span>
                                                        </div>
                                                        {intermediateResults[item.id].steps.map((step, stepIndex) => (
                                                            <div key={stepIndex} className="scaling-summary-step">
                                                                <span>{step.tabName}</span>
                                                                <span>{step.inputValue.toFixed(2)}</span>
                                                                <span>→</span>
                                                                <span>{step.scaledValue.toFixed(2)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </AnimatePresence>

                        {filteredItems.length === 0 && (
                            <tr className="scaling-summary-no-results">
                                <td colSpan={4 + tabConfigs.length} className="scaling-summary-no-results-cell">
                                    No items match the current filters
                                </td>
                            </tr>
                        )}
                        </tbody>
                    </table>
                </div>
                <div className="scaling-summary-footer">
                    <div className="scaling-summary-footer-item">Base values are inherited from process costs</div>
                    <div className="scaling-summary-footer-item">Click on a row to show calculation steps</div>
                    <div className="scaling-summary-footer-item">Each column shows the result after applying that tab's scaling</div>
                </div>
            </CardContent>
        </Card>
    );
};

export default ScalingSummary;