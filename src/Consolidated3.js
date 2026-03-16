import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Tab, TabList, TabPanel, Tabs } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faEdit, faCheck, faTimes, faSave, faUndo,
    faArrowLeft, faArrowRight, faLock, faLockOpen,
    faPlus, faTrash, faQuestion, faSync,
    faClock, faHammer, faIndustry, faPercentage, faMoneyBillWave,
    faCalendarAlt, faChartLine, faFileInvoiceDollar, faCoins,
    faCog, faBoxes, faDollarSign, faMoneyCheckAlt
} from '@fortawesome/free-solid-svg-icons';
import * as math from 'mathjs';

// Import from consolidated.js and consolidated2.js
import {
    MatrixSubmissionService,
    ExtendedScaling,
    GeneralFormConfig
} from './Consolidated';

import {
    useMatrixFormValues,
    EfficacyManager,
    VersionZoneManager,
    MatrixValueEditor,
    EfficacyPeriodEditor,
    MatrixConfigExporter,
    MatrixHistoryManager,
    MatrixInheritanceManager,
    MatrixValidator,
    MatrixSummaryGenerator,
    SensitivityConfigGenerator,
    MatrixSyncService,
    MatrixScalingManager
} from './Consolidated2';

// Import CFA components
import CFAConsolidationUI from './components/cfa/CFAConsolidationUI';
import SelectionPanel from './components/cfa/SelectionPanel';
import ProcessingPanel from './components/cfa/ProcessingPanel';
import ResultsPanel from './components/cfa/ResultsPanel';
import IndividualResultsPanel from './components/cfa/IndividualResultsPanel';

// Import modules
import CalculationMonitor from './components/modules/CalculationMonitor';
import ConfigurationMonitor from './components/modules/ConfigurationMonitor';
import CustomizableImage from './components/modules/CustomizableImage';
import CustomizableTable from './components/modules/CustomizableTable';
import Popup from './components/modules/Efficacy';
import SensitivityMonitor, { sensitivityActionRef } from './components/modules/SensitivityMonitor';
import EfficacyMapContainer from './components/modules/EfficacyMapContainer';

// Import styling
import './styles/HomePage.CSS/HCSS.css';
import './styles/HomePage.CSS/Consolidated.css';
import './styles/HomePage.CSS/VersionSelector.css';

// Import label references for reset functionality
import * as labelReferences from './utils/labelReferences';

/**
 * PropertySelector Component
 * Allows selecting properties from available form values
 */
const PropertySelector = ({ selectedProperties, setSelectedProperties, formValues }) => {
    const handlePropertyChange = (event) => {
        const selectedOptions = Array.from(event.target.selectedOptions, (option) => option.value);
        const originalProperties = selectedOptions.map(displayProp =>
            Object.keys(formValues).find(key => formValues[key].label === displayProp));
        setSelectedProperties(originalProperties);
    };

    return (
        <div className="version-selector-container">
            <label htmlFor="property-selector" className="label-common"></label>
            <select
                id="property-selector"
                multiple
                value={selectedProperties.map(prop => formValues[prop].label)}
                onChange={handlePropertyChange}
                className="form-item"
            >
                {Object.keys(formValues).map((key) => (
                    <option key={key} value={formValues[key].label}>
                        {formValues[key].label}
                    </option>
                ))}
            </select>
        </div>
    );
};

/**
 * VersionSelector Component
 * Allows selecting versions from a grouped list
 */
const VersionSelector = ({ maxVersions = 20, batchInfo = {} }) => {
    // Get state and setters from context
    const [selectedVersions, setSelectedVersions] = useState([]);

    // Group versions into batches
    const batchGroups = useMemo(() => {
        const groups = {};
        Array.from({ length: maxVersions }, (_, i) => i + 1).forEach(version => {
            const batchId = batchInfo[version]?.batchId || Math.ceil(version / 5); // Group every 5 versions by default
            if (!groups[batchId]) {
                groups[batchId] = {
                    id: batchId,
                    name: batchInfo[version]?.batchName || `Batch ${batchId}`,
                    versions: []
                };
            }
            groups[batchId].versions.push(version);
        });
        return Object.values(groups);
    }, [maxVersions, batchInfo]);

    // Toggle a single version selection
    const handleVersionToggle = (version) => {
        setSelectedVersions(prev =>
            prev.includes(version)
                ? prev.filter(v => v !== version)
                : [...prev, version]
        );
    };

    // Toggle all versions in a batch
    const handleBatchSelect = (batchId) => {
        const group = batchGroups.find(g => g.id === batchId);
        if (!group) return;

        const allSelected = group.versions.every(v => selectedVersions.includes(v));
        if (allSelected) {
            setSelectedVersions(prev => prev.filter(v => !group.versions.includes(v)));
        } else {
            setSelectedVersions(prev => [...new Set([...prev, ...group.versions])]);
        }
    };

    // Handle keyboard navigation
    const handleKeyDown = (e, action, type = 'item') => {
        // Enter or Space for selection
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            action();
            return;
        }

        // Batch shortcuts (only when focused on group header)
        if (type === 'header') {
            if (e.key === 'a' && e.ctrlKey) {
                // Ctrl+A to select all in group
                e.preventDefault();
                action();
                return;
            }
        }

        // Navigation shortcuts
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                const next = e.target.nextElementSibling;
                if (next && next.tabIndex === 0) next.focus();
                break;
            case 'ArrowUp':
                e.preventDefault();
                const prev = e.target.previousElementSibling;
                if (prev && prev.tabIndex === 0) prev.focus();
                break;
            case 'Home':
                e.preventDefault();
                e.target.parentElement.firstElementChild.focus();
                break;
            case 'End':
                e.preventDefault();
                e.target.parentElement.lastElementChild.focus();
                break;
            default:
                break;
        }
    };

    return (
        <div
            className="version-selector"
            role="region"
            aria-label="Version Selection"
        >
            {batchGroups.map(group => (
                <div key={group.id} className="version-group">
                    <div
                        className={`group-header ${
                            group.versions.every(v => selectedVersions.includes(v)) ? 'all-selected' : ''
                        }`}
                        onClick={() => handleBatchSelect(group.id)}
                        onKeyDown={(e) => handleKeyDown(e, () => handleBatchSelect(group.id), 'header')}
                        role="button"
                        tabIndex={0}
                        aria-expanded="true"
                        aria-controls={`version-list-${group.id}`}
                    >
                        <div className="group-title">
                            <span className="group-name">{group.name}</span>
                            <span className="group-count">
                {group.versions.filter(v => selectedVersions.includes(v)).length}
                                / {group.versions.length}
              </span>
                        </div>
                    </div>
                    <div
                        className="version-list"
                        id={`version-list-${group.id}`}
                        role="list"
                    >
                        {group.versions.map(version => (
                            <div
                                key={version}
                                className={`version-item ${
                                    selectedVersions.includes(version) ? 'selected' : ''
                                }`}
                                onClick={() => handleVersionToggle(version)}
                                onKeyDown={(e) => handleKeyDown(e, () => handleVersionToggle(version), 'item')}
                                role="listitem"
                                tabIndex={0}
                                aria-selected={selectedVersions.includes(version)}
                            >
                                <div className="version-info">
                                    <span className="version-number">Model {version}</span>
                                    {batchInfo[version]?.description && (
                                        <span className="version-description">
                      {batchInfo[version].description}
                    </span>
                                    )}
                                </div>
                                <div className={`version-checkbox ${selectedVersions.includes(version) ? 'checked' : ''}`}>
                                    <input
                                        type="checkbox"
                                        checked={selectedVersions.includes(version)}
                                        onChange={() => {}}
                                        onClick={e => {}}
                                        style={{
                                            appearance: 'none',
                                            WebkitAppearance: 'none',
                                            MozAppearance: 'none'
                                        }}
                                        aria-label={`Select Version ${version}`}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

/**
 * PlotsTabs Component
 * Displays tabs for different plot categories
 */
const PlotsTabs = ({ version, sensitivity = false }) => {
    const [plotCategories, setPlotCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [plotGroups, setPlotGroups] = useState({});
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [plots, setPlots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [imagesLoaded, setImagesLoaded] = useState({});

    useEffect(() => {
        const fetchPlots = async () => {
            setLoading(true);
            setError(null);

            try {
                // Determine which API endpoint to use based on sensitivity flag
                const endpoint = sensitivity
                    ? `http://localhost:5008/api/sensitivity-plots/${version}`
                    : `http://localhost:5008/api/plots/${version}`;

                const response = await fetch(endpoint);

                if (!response.ok) {
                    throw new Error(`HTTP error: ${response.status}`);
                }

                const data = await response.json();

                if (!data || data.length === 0) {
                    setPlotCategories([]);
                    setPlotGroups({});
                    setPlots([]);
                    setError("No plots available for this version");
                    setLoading(false);
                    return;
                }

                // Organize plots by category and group
                const categories = [...new Set(data.map(plot => plot.category))];

                // Create groups within each category
                const groupsByCategory = {};
                categories.forEach(category => {
                    const categoryPlots = data.filter(plot => plot.category === category);
                    const groups = [...new Set(categoryPlots.map(plot => plot.group))];
                    groupsByCategory[category] = groups;
                });

                setPlotCategories(categories);
                setPlotGroups(groupsByCategory);

                // Set initial selections
                if (categories.length > 0) {
                    setSelectedCategory(categories[0]);

                    if (groupsByCategory[categories[0]].length > 0) {
                        setSelectedGroup(groupsByCategory[categories[0]][0]);

                        // Set initial plots
                        const initialPlots = data.filter(
                            plot => plot.category === categories[0] &&
                                plot.group === groupsByCategory[categories[0]][0]
                        );
                        setPlots(initialPlots);
                    }
                }
            } catch (err) {
                console.error('Error fetching plots:', err);
                setError(`Failed to load plots: ${err.message}`);
            } finally {
                setLoading(false);
            }
        };

        // Skip API call if version is empty (during refresh)
        if (!version) {
            console.log('Skipping plot fetch - version is empty');
            return;
        }

        fetchPlots();
    }, [version, sensitivity]);

    // Update plots when category or group changes
    useEffect(() => {
        if (selectedCategory && selectedGroup) {
            // Fetch plots for the selected category and group
            const fetchPlotsByGroup = async () => {
                setLoading(true);

                try {
                    const endpoint = sensitivity
                        ? `http://localhost:5008/api/sensitivity-plots/${version}/${selectedCategory}/${selectedGroup}`
                        : `http://localhost:5008/api/plots/${version}/${selectedCategory}/${selectedGroup}`;

                    const response = await fetch(endpoint);

                    if (!response.ok) {
                        throw new Error(`HTTP error: ${response.status}`);
                    }

                    const data = await response.json();
                    setPlots(data);
                } catch (err) {
                    console.error('Error fetching plots by group:', err);
                    setError(`Failed to load plots: ${err.message}`);
                } finally {
                    setLoading(false);
                }
            };

            fetchPlotsByGroup();
        }
    }, [selectedCategory, selectedGroup, version, sensitivity]);

    const handleCategoryChange = (category) => {
        setSelectedCategory(category);

        // Reset group selection to the first group in the new category
        if (plotGroups[category] && plotGroups[category].length > 0) {
            setSelectedGroup(plotGroups[category][0]);
        } else {
            setSelectedGroup(null);
            setPlots([]);
        }
    };

    const handleGroupChange = (group) => {
        setSelectedGroup(group);
    };

    const transformPath = (path) => {
        // Normalize the file path to replace backslashes with forward slashes
        const normalizedPath = path.replace(/\\/g, '/');

        // Extract the batch version
        const batchMatch = normalizedPath.match(/Batch\((\d+)\)/);
        if (!batchMatch) return normalizedPath; // If no batch number found, return original path

        const batchVersion = batchMatch[1];

        // Construct the URL using the extracted parts
        return `http://localhost:5008/images/Batch(${batchVersion})/Results(${batchVersion})/${normalizedPath.split('Results(')[1]}`;
    };

    const handleImageLoad = (index) => {
        setImagesLoaded(prev => ({ ...prev, [index]: true }));
    };

    return (
        <div className="plots-tabs-container">
            {/* Main category tabs */}
            <div className="plots-category-tabs">
                {plotCategories.map(category => (
                    <button
                        key={category}
                        className={`category-tab ${selectedCategory === category ? 'active' : ''}`}
                        onClick={() => handleCategoryChange(category)}
                    >
                        {category}
                    </button>
                ))}
            </div>

            {/* Group tabs for selected category */}
            <div className="plots-group-tabs">
                {selectedCategory && plotGroups[selectedCategory] &&
                    plotGroups[selectedCategory].map(group => (
                        <button
                            key={group}
                            className={`group-tab ${selectedGroup === group ? 'active' : ''}`}
                            onClick={() => handleGroupChange(group)}
                        >
                            {group}
                        </button>
                    ))
                }
            </div>

            {/* Plot display area */}
            <div className="plots-display-area">
                {loading ? (
                    <div className="plots-loading">Loading plots...</div>
                ) : error ? (
                    <div className="plots-error">{error}</div>
                ) : plots.length === 0 ? (
                    <div className="plots-empty">No plots available for this selection</div>
                ) : (
                    <div className="plots-grid">
                        {plots.map((plot, index) => (
                            <div
                                key={index}
                                className={`plot-container ${imagesLoaded[index] ? 'loaded' : ''}`}
                            >
                                <h3 className="plot-title">{plot.title || `Plot ${index + 1}`}</h3>
                                <CustomizableImage
                                    src={transformPath(plot.path)}
                                    alt={plot.title || `Plot ${index + 1}`}
                                    width="100%"
                                    height="auto"
                                    onLoad={() => handleImageLoad(index)}
                                    className={imagesLoaded[index] ? 'loaded' : ''}
                                />
                                {plot.description && (
                                    <p className="plot-description">{plot.description}</p>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};


/**
 * Integrated MatrixApp Component
 * Combines all functionality in a single component
 */
const MatrixApp = () => {
    // Use the matrix form values hook
    const matrixFormValues = useMatrixFormValues();

    const {
        formMatrix,
        versions,
        zones,
        getParameterValue,
        updateParameterValue,
        handleInputChange,
        S, setS,
        F, setF, toggleF,
        V, setV, toggleV,
        R, setR, toggleR,
        RF, setRF, toggleRF,
        subDynamicPlots, setSubDynamicPlots, toggleSubDynamicPlot,
        scalingGroups, setScalingGroups,
        finalResults, setFinalResults,
        syncWithBackend,
        createVersion,
        setActiveVersion,
        createZone,
        setActiveZone,
        updateEfficacyPeriod,
        getEffectiveValue,
        handleReset,
        propertyMapping,
        iconMapping
    } = matrixFormValues;

    // Matrix Service
    const matrixService = useMemo(() => new MatrixSubmissionService(), []);

    // Tab state
    const [activeTab, setActiveTab] = useState('input');
    const [activeSubTab, setActiveSubTab] = useState('ProjectConfig');

    // Calculation monitor state
    const [monitorActive, setMonitorActive] = useState(false);
    const [selectedRunVersions, setSelectedRunVersions] = useState([]);
    const [currentRunVersion, setCurrentRunVersion] = useState('1');

    // Efficacy popup state
    const [showEfficacyPopup, setShowEfficacyPopup] = useState(false);
    const [efficacyPopupPosition, setEfficacyPopupPosition] = useState({ top: 0, left: 0 });
    const [efficacyItemId, setEfficacyItemId] = useState(null);

    // Scaling states
    const [activeScalingGroups, setActiveScalingGroups] = useState({
        Amount4: 0,
        Amount5: 0,
        Amount6: 0,
        Amount7: 0
    });

    // Initialize window.sensitivityActionRef for the SensitivityMonitor
    useEffect(() => {
        window.sensitivityActionRef = sensitivityActionRef;
    }, []);

    // Scaling base costs
    const [scalingBaseCosts, setScalingBaseCosts] = useState({});

    // Matrix-based processing
    useEffect(() => {
        // Create a mapping of all four Amount categories
        const amountCategories = ['Amount4', 'Amount5', 'Amount6', 'Amount7'];

        // Generate scalingBaseCosts with the same structure for all categories
        const updatedScalingBaseCosts = amountCategories.reduce((result, category) => {
            // Extract entries for this category
            const categoryEntries = Object.entries(formMatrix || {})
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
                if (versions && zones) {
                    const activeVersion = versions?.active || 'v1';
                    const activeZone = zones?.active || 'z1';
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
    }, [formMatrix, versions, zones]);

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
            const activeVersion = versions?.active || "v1";
            const numericVersion = activeVersion.replace(/\D/g, '');

            // Use MatrixSubmissionService to submit form values
            const submissionResult = await matrixService.submitMatrixFormValues(
                matrixFormValues,
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

    // Handle efficacy period button click
    const handleEfficacyClick = (e, itemId) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setEfficacyPopupPosition({
            top: rect.bottom + window.scrollY,
            left: rect.left + window.scrollX
        });
        setEfficacyItemId(itemId);
        setShowEfficacyPopup(true);
    };

    // Update price callback for CalculationMonitor
    const handleUpdatePrice = useCallback((version, price) => {
        // Find the initialSellingPriceAmount13 parameter
        if (formMatrix && formMatrix.initialSellingPriceAmount13) {
            updateParameterValue('initialSellingPriceAmount13', price, versions?.active || 'v1', zones?.active || 'z1');
        }
    }, [formMatrix, updateParameterValue, versions?.active, zones?.active]);

    // Update version number for efficacy popup
    const handleVersionChange = (newVersion) => {
        setCurrentRunVersion(newVersion);
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
                        {/* Version and Zone Management */}
                        {formMatrix && versions && zones && (
                            <VersionZoneManager
                                versions={versions || {}}
                                zones={zones || {}}
                                createVersion={createVersion}
                                setActiveVersion={setActiveVersion}
                                createZone={createZone}
                                setActiveZone={setActiveZone}
                            />
                        )}

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
                            <button
                                className={`sub-tab-button ${activeSubTab === 'CFAConfig' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('CFAConfig')}
                            >
                                CFA Consolidation
                            </button>
                            <button
                                className={`sub-tab-button ${activeSubTab === 'CalculationConfig' ? 'active' : ''}`}
                                onClick={() => setActiveSubTab('CalculationConfig')}
                            >
                                Calculation Monitor
                            </button>
                        </div>

                        {/* Sub-tab content */}
                        <div className="sub-tab-content">
                            {/* Project Config */}
                            {activeSubTab === 'ProjectConfig' && (
                                <GeneralFormConfig
                                    formValues={{formMatrix, versions, zones, iconMapping}}
                                    handleInputChange={handleInputChange}
                                    version={versions?.active || '1'}
                                    filterKeyword="Amount1"
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={setActiveVersion}
                                />
                            )}

                            {/* Loan Config */}
                            {activeSubTab === 'LoanConfig' && (
                                <GeneralFormConfig
                                    formValues={{formMatrix, versions, zones, iconMapping}}
                                    handleInputChange={handleInputChange}
                                    version={versions?.active || '1'}
                                    filterKeyword="Amount2"
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={setActiveVersion}
                                />
                            )}

                            {/* Rates Config */}
                            {activeSubTab === 'RatesConfig' && (
                                <GeneralFormConfig
                                    formValues={{formMatrix, versions, zones, iconMapping}}
                                    handleInputChange={handleInputChange}
                                    version={versions?.active || '1'}
                                    filterKeyword="Amount3"
                                    F={F}
                                    toggleF={toggleF}
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={setActiveVersion}
                                />
                            )}

                            {/* Process1 Config */}
                            {activeSubTab === 'Process1Config' && (
                                <>
                                    <GeneralFormConfig
                                        formValues={{formMatrix, versions, zones, iconMapping}}
                                        handleInputChange={handleInputChange}
                                        version={versions?.active || '1'}
                                        filterKeyword="Amount4"
                                        V={V}
                                        setV={setV}
                                        R={R}
                                        setR={setR}
                                        toggleR={toggleR}
                                        toggleV={toggleV}
                                        S={S || {}}
                                        setS={setS}
                                        setVersion={setActiveVersion}
                                        summaryItems={finalResults.Amount4}
                                        onEfficacyClick={handleEfficacyClick}
                                    />
                                    <ExtendedScaling
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
                                        formValues={{formMatrix, versions, zones, iconMapping}}
                                        handleInputChange={handleInputChange}
                                        version={versions?.active || '1'}
                                        filterKeyword="Amount5"
                                        V={V}
                                        setV={setV}
                                        R={R}
                                        setR={setR}
                                        toggleR={toggleR}
                                        toggleV={toggleV}
                                        S={S || {}}
                                        setS={setS}
                                        setVersion={setActiveVersion}
                                        summaryItems={finalResults.Amount5}
                                        onEfficacyClick={handleEfficacyClick}
                                    />
                                    <ExtendedScaling
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

                            {/* Revenue1 Config */}
                            {activeSubTab === 'Revenue1Config' && (
                                <>
                                    <GeneralFormConfig
                                        formValues={{formMatrix, versions, zones, iconMapping}}
                                        handleInputChange={handleInputChange}
                                        version={versions?.active || '1'}
                                        filterKeyword="Amount6"
                                        V={V}
                                        setV={setV}
                                        R={R}
                                        setR={setR}
                                        toggleR={toggleR}
                                        toggleV={toggleV}
                                        S={S || {}}
                                        setS={setS}
                                        setVersion={setActiveVersion}
                                        summaryItems={finalResults.Amount6}
                                        onEfficacyClick={handleEfficacyClick}
                                    />
                                    <ExtendedScaling
                                        baseCosts={scalingBaseCosts.Amount6 || []}
                                        onScaledValuesChange={(scaledValues) => {/* Scaled values handler */}}
                                        initialScalingGroups={getFilteredScalingGroups('Amount6')}
                                        onScalingGroupsChange={(newGroups) => {
                                            const otherGroups = scalingGroups.filter(g => g._scalingType !== 'Amount6');
                                            const updatedGroups = newGroups.map(g => ({...g, _scalingType: 'Amount6'}));
                                            setScalingGroups([...otherGroups, ...updatedGroups]);
                                        }}
                                        filterKeyword="Amount6"
                                        V={V}
                                        R={R}
                                        toggleV={toggleV}
                                        toggleR={toggleR}
                                        onFinalResultsGenerated={handleFinalResultsGenerated}
                                        activeGroupIndex={activeScalingGroups.Amount6 || 0}
                                        onActiveGroupChange={handleActiveGroupChange}
                                    />
                                </>
                            )}

                            {/* Revenue2 Config */}
                            {activeSubTab === 'Revenue2Config' && (
                                <>
                                    <GeneralFormConfig
                                        formValues={{formMatrix, versions, zones, iconMapping}}
                                        handleInputChange={handleInputChange}
                                        version={versions?.active || '1'}
                                        filterKeyword="Amount7"
                                        V={V}
                                        setV={setV}
                                        R={R}
                                        setR={setR}
                                        toggleR={toggleR}
                                        toggleV={toggleV}
                                        S={S || {}}
                                        setS={setS}
                                        setVersion={setActiveVersion}
                                        summaryItems={finalResults.Amount7}
                                        onEfficacyClick={handleEfficacyClick}
                                    />
                                    <ExtendedScaling
                                        baseCosts={scalingBaseCosts.Amount7 || []}
                                        onScaledValuesChange={(scaledValues) => {/* Scaled values handler */}}
                                        initialScalingGroups={getFilteredScalingGroups('Amount7')}
                                        onScalingGroupsChange={(newGroups) => {
                                            const otherGroups = scalingGroups.filter(g => g._scalingType !== 'Amount7');
                                            const updatedGroups = newGroups.map(g => ({...g, _scalingType: 'Amount7'}));
                                            setScalingGroups([...otherGroups, ...updatedGroups]);
                                        }}
                                        filterKeyword="Amount7"
                                        V={V}
                                        R={R}
                                        toggleV={toggleV}
                                        toggleR={toggleR}
                                        onFinalResultsGenerated={handleFinalResultsGenerated}
                                        activeGroupIndex={activeScalingGroups.Amount7 || 0}
                                        onActiveGroupChange={handleActiveGroupChange}
                                    />
                                </>
                            )}

                            {/* Scaling Tab */}
                            {activeSubTab === 'Scaling' && (
                                <>
                                    {/* Integrate EfficacyMapContainer */}
                                    <EfficacyMapContainer
                                        parameters={formMatrix}
                                        plantLifetime={formMatrix?.plantLifetimeAmount10?.value || 20}
                                        configurableVersions={20}
                                        scalingGroups={scalingGroups.length || 5}
                                        onParameterUpdate={(paramId, updatedParam) => {
                                            handleInputChange(
                                                { target: { value: updatedParam.value } },
                                                paramId
                                            );
                                        }}
                                    />
                                </>
                            )}

                            {/* Fixed Revenue Config */}
                            {activeSubTab === 'FixedRevenueConfig' && (
                                <GeneralFormConfig
                                    formValues={{formMatrix, versions, zones, iconMapping}}
                                    handleInputChange={handleInputChange}
                                    version={versions?.active || '1'}
                                    filterKeyword="Amount8"
                                    RF={RF}
                                    setRF={setRF}
                                    toggleRF={toggleRF}
                                    S={S || {}}
                                    setS={setS}
                                    setVersion={setActiveVersion}
                                    onEfficacyClick={handleEfficacyClick}
                                />
                            )}

                            {/* CFA Consolidation UI */}
                            {activeSubTab === 'CFAConfig' && (
                                <CFAConsolidationUI />
                            )}

                            {/* Calculation Monitor */}
                            {activeSubTab === 'CalculationConfig' && (
                                <div className="calculation-configuration">
                                    <div className="calculation-header">
                                        <h2>Calculation Monitoring</h2>
                                        <div className="calculation-controls">
                                            <div className="version-selector">
                                                <label>Version:</label>
                                                <input
                                                    type="text"
                                                    value={currentRunVersion}
                                                    onChange={(e) => setCurrentRunVersion(e.target.value)}
                                                />
                                            </div>
                                            <button
                                                className={`monitor-toggle ${monitorActive ? 'active' : ''}`}
                                                onClick={() => setMonitorActive(!monitorActive)}
                                            >
                                                {monitorActive ? 'Hide Monitor' : 'Show Monitor'}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="calculation-content">
                                        <CalculationMonitor
                                            selectedVersions={selectedRunVersions}
                                            updatePrice={handleUpdatePrice}
                                            isActive={monitorActive}
                                            currentVersion={currentRunVersion}
                                            isSensitivity={false}
                                        />

                                        <ConfigurationMonitor
                                            version={currentRunVersion}
                                        />

                                        <SensitivityMonitor
                                            S={S}
                                            setS={setS}
                                            version={currentRunVersion}
                                            activeTab={activeSubTab}
                                        />
                                    </div>
                                </div>
                            )}

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
                                    onClick={syncWithBackend}
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
                        <div className="results-tabs">
                            <div className="results-tab-buttons">
                                <button className="results-tab-button active">Charts</button>
                                <button className="results-tab-button">Tables</button>
                                <button className="results-tab-button">Analysis</button>
                            </div>

                            <div className="results-tab-content">
                                <div className="plots-container">
                                    <PlotsTabs
                                        version={versions?.active?.replace(/\D/g, '') || '1'}
                                        sensitivity={false}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </TabPanel>
            </Tabs>

            {/* Efficacy Period Popup */}
            {showEfficacyPopup && efficacyItemId && (
                <Popup
                    show={showEfficacyPopup}
                    position={efficacyPopupPosition}
                    onClose={() => setShowEfficacyPopup(false)}
                    formValues={formMatrix}
                    handleInputChange={handleInputChange}
                    id={efficacyItemId}
                    version={currentRunVersion}
                    itemId={efficacyItemId}
                    onVersionChange={handleVersionChange}
                />
            )}
        </div>
    );
};

export {
    MatrixApp,
    PropertySelector,
    VersionSelector,
    PlotsTabs,
    CalculationMonitor,
    ConfigurationMonitor,
    CustomizableImage,
    CustomizableTable,
    SensitivityMonitor,
    sensitivityActionRef,
    CFAConsolidationUI,
    SelectionPanel,
    ProcessingPanel,
    ResultsPanel,
    IndividualResultsPanel
};

export default MatrixApp;




