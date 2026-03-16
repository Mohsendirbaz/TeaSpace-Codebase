/**
 * MatrixApp.js
 * 
 * Integrated MatrixApp Component that combines all matrix-based functionality in a single component.
 * Provides a tabbed interface for input configuration and results visualization.
 * Handles form submission, scaling groups, and matrix-based processing.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Tab, TabList, TabPanel, Tabs } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import MatrixSubmissionService from '../../services/MatrixSubmissionService';
import SimpleScalingEditor from '../scaling/SimpleScalingEditor';
import GeneralFormConfig from '../forms/GeneralFormConfig';
import '../../styles/HomePage.CSS/HCSS.css';

/**
 * Integrated MatrixApp Component
 * Combines all functionality in a single component
 */
const MatrixApp = ({
                       formValues,
                       handleInputChange,
                       version = "1",
                       S, setS,
                       F, toggleF,
                       V, setV, toggleV,
                       R, setR, toggleR,
                       RF, setRF, toggleRF,
                       subDynamicPlots, setSubDynamicPlots, toggleSubDynamicPlot,
                       scalingGroups, setScalingGroups,
                       finalResults, setFinalResults,
                   }) => {
    // Matrix Service
    const matrixService = useMemo(() => new MatrixSubmissionService(), []);

    // Tab state
    const [activeTab, setActiveTab] = useState('input');
    const [activeSubTab, setActiveSubTab] = useState('ProjectConfig');

    // Scaling states
    const [activeScalingGroups, setActiveScalingGroups] = useState({
        Amount4: 0,
        Amount5: 0,
        Amount6: 0,
        Amount7: 0
    });

    // Scaling base costs
    const [scalingBaseCosts, setScalingBaseCosts] = useState({});

    // Matrix-based processing
    useEffect(() => {
        // Create a mapping of all four Amount categories
        const amountCategories = ['Amount4', 'Amount5', 'Amount6', 'Amount7'];

        // Generate scalingBaseCosts with the same structure for all categories
        const updatedScalingBaseCosts = amountCategories.reduce((result, category) => {
            // Extract entries for this category
            const categoryEntries = Object.entries(formValues?.formMatrix || formValues || {})
                .filter(([key]) => key.includes(category));

            // Sort entries based on their numeric suffix
            categoryEntries.sort(([keyA], [keyB]) => {
                // Extract the numeric part after the category (e.g., "Amount40" -> "40")
                const suffixA = keyA.replace(category, '');
                const suffixB = keyB.replace(category, '');
                return parseInt(suffixA) - parseInt(suffixB);
            });

            // Map sorted entries to scaling items
            result[category] = categoryEntries.map(([key, value]) => {
                let paramValue;

                // Handle matrix-based values
                if (formValues?.versions?.active && formValues?.zones?.active) {
                    const activeVersion = formValues?.versions?.active;
                    const activeZone = formValues?.zones?.active;
                    paramValue = value.matrix?.[activeVersion]?.[activeZone] || 0;
                } else {
                    // Handle regular values
                    paramValue = value.value || 0;
                }

                return {
                    id: key,
                    label: value.label || `Unnamed ${category}`,
                    value: parseFloat(paramValue) || 0,
                    baseValue: parseFloat(paramValue) || 0,
                    vKey: value.dynamicAppendix?.itemState?.vKey || null,
                    rKey: value.dynamicAppendix?.itemState?.rKey || null
                };
            });

            return result;
        }, {});

        // Update state
        setScalingBaseCosts(updatedScalingBaseCosts);
    }, [formValues]);

    // Handle active group change
    const handleActiveGroupChange = (groupIndex, filterKeyword) => {
        setActiveScalingGroups(prev => ({
            ...prev,
            [filterKeyword]: groupIndex
        }));
    };

    // Handle final results generated
    const handleFinalResultsGenerated = (summaryItems, filterKeyword) => {
        setFinalResults(prev => ({
            ...prev,
            [filterKeyword]: summaryItems
        }));
    };

    // Handle form submission
    const handleSubmitCompleteSet = async () => {
        try {
            // Get the active version from matrix state
            const activeVersion = formValues?.versions?.active || "v1";
            const numericVersion = activeVersion.replace(/\D/g, '');

            // Use MatrixSubmissionService to submit form values
            const submissionResult = await matrixService.submitMatrixFormValues(
                formValues,
                numericVersion
            );

            console.log('Submission result:', submissionResult);
            alert('Form values submitted successfully');
        } catch (error) {
            console.error('Error during form submission:', error);
            alert(`Error submitting form values: ${error.message}`);
        }
    };

    // Process scaling groups for various categories
    const getFilteredScalingGroups = (filterKeyword) => {
        return scalingGroups.filter(g => g._scalingType === filterKeyword);
    };

    return (
        <div className="matrix-app">
            <Tabs selectedIndex={activeTab === 'input' ? 0 : 1} onSelect={index => setActiveTab(index === 0 ? 'input' : 'results')}>
                <TabList className="main-tabs">
                    <Tab>Input Configuration</Tab>
                    <Tab>Results & Visualization</Tab>
                </TabList>

                <TabPanel>
                    {/* Input Configuration Panel */}
                    <div className="input-panel">
                        {/* Sub-tab buttons */}
                        <div className="sub-tab-buttons">
                            <button
                                className={`sub-tab-button ${activeSubTab === 'ProjectConfig' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('ProjectConfig')}
                            >
                                Project Configuration
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'LoanConfig' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('LoanConfig')}
                            >
                                Loan Configuration
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'RatesConfig' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('RatesConfig')}
                            >
                                Rates & Fixed Costs
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'Process1Config' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('Process1Config')}
                            >
                                Process Quantities (Vs, units)
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'Process2Config' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('Process2Config')}
                            >
                                Process Costs <br /> (Vs, $ / unit)
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'Revenue1Config' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('Revenue1Config')}
                            >
                                Additional Revenue Quantities<br /> (Rs, units)
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'Revenue2Config' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('Revenue2Config')}
                            >
                                Additional Revenue Prices <br /> (Rs, $ / unit)
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'Scaling' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('Scaling')}
                            >
                                + Scaling
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'FixedRevenueConfig' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('FixedRevenueConfig')}
                            >
                                Fixed Revenue Components <br /> (RFs, $)
                            </button>
                        </div>

                        {/* Sub-tab content */}
                        <div className="sub-tab-content">
                            {/* Version and Zone Management - Only show with matrix-based form values */}
                            {formValues?.versions && formValues?.zones && (
                                <div className="matrix-selectors">
                                    <div className="version-selector">
                                        <h3>Version</h3>
                                        <select
                                            value={formValues?.versions?.active || 'v1'}
                                            onChange={e => formValues?.setActiveVersion?.(e.target.value)}
                                        >
                                            {formValues?.versions?.list?.map(version => (
                                                <option key={version} value={version}>
                                                    {formValues?.versions?.metadata?.[version]?.label || version}
                                                </option>
                                            ))}
                                        </select>
                                        <button onClick={() => {
                                            const label = prompt("Enter name for new version:", `Version ${(formValues?.versions?.list?.length || 0) + 1}`);
                                            if (label) formValues?.createVersion?.(label);
                                        }}>+ New Version</button>
                                    </div>
                                    <div className="zone-selector">
                                        <h3>Zone</h3>
                                        <select
                                            value={formValues?.zones?.active || 'z1'}
                                            onChange={e => formValues?.setActiveZone?.(e.target.value)}
                                        >
                                            {formValues?.zones?.list?.map(zone => (
                                                <option key={zone} value={zone}>
                                                    {formValues?.zones?.metadata?.[zone]?.label || zone}
                                                </option>
                                            ))}
                                        </select>
                                        <button onClick={() => {
                                            const label = prompt("Enter name for new zone:", `Zone ${(formValues?.zones?.list?.length || 0) + 1}`);
                                            if (label) formValues?.createZone?.(label);
                                        }}>+ New Zone</button>
                                    </div>
                                </div>
                            )}

                            {/* Project Config */}
                            {activeSubTab === 'ProjectConfig' && (
                                <GeneralFormConfig
                                    formValues={formValues}
                                    handleInputChange={handleInputChange}
                                    version={version}
                                    filterKeyword="Amount1"
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={version => {/* Version update handler */}}
                                />
                            )}

                            {/* Loan Config */}
                            {activeSubTab === 'LoanConfig' && (
                                <GeneralFormConfig
                                    formValues={formValues}
                                    handleInputChange={handleInputChange}
                                    version={version}
                                    filterKeyword="Amount2"
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={version => {/* Version update handler */}}
                                />
                            )}

                            {/* Rates Config */}
                            {activeSubTab === 'RatesConfig' && (
                                <GeneralFormConfig
                                    formValues={formValues}
                                    handleInputChange={handleInputChange}
                                    version={version}
                                    filterKeyword="Amount3"
                                    F={F}
                                    toggleF={toggleF}
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={version => {/* Version update handler */}}
                                />
                            )}

                            {/* Process1 Config */}
                            {activeSubTab === 'Process1Config' && (
                                <>
                                    <GeneralFormConfig
                                        formValues={formValues}
                                        handleInputChange={handleInputChange}
                                        version={version}
                                        filterKeyword="Amount4"
                                        V={V}
                                        setV={setV}
                                        R={R}
                                        setR={setR}
                                        toggleR={toggleR}
                                        toggleV={toggleV}
                                        S={S || {}}
                                        setS={setS}
                                        setVersion={version => {/* Version update handler */}}
                                        summaryItems={finalResults.Amount4}
                                    />
                                    <SimpleScalingEditor
                                        baseCosts={scalingBaseCosts.Amount4 || []}
                                        onScaledValuesChange={(scaledValues) => {/* Scaled values handler */}}
                                        initialScalingGroups={getFilteredScalingGroups('Amount4')}
                                        onScalingGroupsChange={(newGroups) => {
                                            const otherGroups = scalingGroups.filter(g => g._scalingType !== 'Amount4');
                                            const updatedGroups = newGroups.map(g => ({...g, _scalingType: 'Amount4'}));
                                            setScalingGroups([...otherGroups, ...updatedGroups]);
                                        }}
                                        filterKeyword="Amount4"
                                        V={V}
                                        R={R}
                                        toggleV={toggleV}
                                        toggleR={toggleR}
                                        onFinalResultsGenerated={handleFinalResultsGenerated}
                                        activeGroupIndex={activeScalingGroups.Amount4 || 0}
                                        onActiveGroupChange={handleActiveGroupChange}
                                    />
                                </>
                            )}

                            {/* Process2 Config */}
                            {activeSubTab === 'Process2Config' && (
                                <>
                                    <GeneralFormConfig
                                        formValues={formValues}
                                        handleInputChange={handleInputChange}
                                        version={version}
                                        filterKeyword="Amount5"
                                        V={V}
                                        setV={setV}
                                        R={R}
                                        setR={setR}
                                        toggleR={toggleR}
                                        toggleV={toggleV}
                                        S={S || {}}
                                        setS={setS}
                                        setVersion={version => {/* Version update handler */}}
                                        summaryItems={finalResults.Amount5}
                                    />
                                    <SimpleScalingEditor
                                        baseCosts={scalingBaseCosts.Amount5 || []}
                                        onScaledValuesChange={(scaledValues) => {/* Scaled values handler */}}
                                        initialScalingGroups={getFilteredScalingGroups('Amount5')}
                                        onScalingGroupsChange={(newGroups) => {
                                            const otherGroups = scalingGroups.filter(g => g._scalingType !== 'Amount5');
                                            const updatedGroups = newGroups.map(g => ({...g, _scalingType: 'Amount5'}));
                                            setScalingGroups([...otherGroups, ...updatedGroups]);
                                        }}
                                        filterKeyword="Amount5"
                                        V={V}
                                        R={R}
                                        toggleV={toggleV}
                                        toggleR={toggleR}
                                        onFinalResultsGenerated={handleFinalResultsGenerated}
                                        activeGroupIndex={activeScalingGroups.Amount5 || 0}
                                        onActiveGroupChange={handleActiveGroupChange}
                                    />
                                </>
                            )}

                            {/* Other config tabs would follow the same pattern */}

                            {/* Add buttons section */}
                            <div className="form-actions">
                                <button
                                    className="submit-button"
                                    onClick={handleSubmitCompleteSet}
                                >
                                    Submit Complete Set
                                </button>
                                <button
                                    className="sync-button"
                                    onClick={() => formValues.syncWithBackend && formValues.syncWithBackend()}
                                >
                                    Sync with Backend
                                </button>
                            </div>
                        </div>
                    </div>
                </TabPanel>

                <TabPanel>
                    {/* Results & Visualization Panel */}
                    <div className="results-panel">
                        <h2>Results & Visualization</h2>
                        <p>This panel would contain charts, tables, and visualization of calculation results.</p>
                    </div>
                </TabPanel>
            </Tabs>
        </div>
    );
};

export default MatrixApp;
