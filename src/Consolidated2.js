import React, { useState, useEffect, useCallback } from 'react';
import { atom, useAtom } from 'jotai';
import axios from 'axios';
import * as math from 'mathjs';
import './styles/HomePage.CSS/HCSS.css';
import './styles/HomePage.CSS/Consolidated.css';
// Import shared utilities.
import { propertyMapping, defaultValues } from './utils/labelReferences';

// ─── Phase 1 Overhaul: New model imports ─────────────────────────────────────
import {
  createVersionSlot,
  createBaselineAssembly,
  createDerivedSummaryFact,
  versionSlotFromLegacy,
} from './model/coreTypes';
// Phase 4: Mutation ledger
import { sStateToScopedMutations, buildMutationLedger } from './model/mutationLedger';
// Phase 5: Agent candidate
import { agentProposalToMutations, applyAgentMutations } from './model/agentCandidate';
// ─────────────────────────────────────────────────────────────────────────────

// Parameter groupings used for baseline assembly (Phase 1 + Phase 3)
const BASELINE_DIRECT_INPUT_PREFIXES = [
  // Project config: Amount1x
  'plantLifetimeAmount10', 'constructionTimeAmount11',
  'plantCapacityAmount12', 'plantCapacityFactorAmount13',
  // Loan config: Amount2x
  'debtRatioAmount20', 'interestRateAmount21', 'loanTermAmount22',
  // Rates & fixed costs: Amount3x
  'inflationRateAmount30', 'discountRateAmount31', 'taxRateAmount32',
  'costOfCapitalAmount33',
  'F1Amount34', 'F2Amount35', 'F3Amount36', 'F4Amount37', 'F5Amount38',
];

const SCALING_OUTPUT_WORKSPACES = ['Amount4', 'Amount5', 'Amount6', 'Amount7'];

/**
 * useMatrixFormValues - Matrix-Based Form Values Hook
 * Provides comprehensive matrix-based form values management with version support.
 *
 * Phase 1 Overhaul: The hook now also exports the new version-centric model
 * surface (versionSlots, assembleBaseline) alongside the existing API.
 * Zone state is preserved internally for backward compat but is quarantined:
 * all new code uses resolveValue() from legacyZoneAdapter rather than
 * accessing matrix[vId][zId] directly.
 *
 * @deprecated zone - zones state and zone-aware methods are deprecated.
 *   Use the VersionSlot model instead.
 */
export function useMatrixFormValues() {
  //=========================================================================
  // STATE DEFINITIONS
  //=========================================================================

  // Version and zone state atoms
  const [versions, setVersions] = useState({
    list: ["v1"],
    active: "v1",
    metadata: {
      "v1": {
        label: "Base Case",
        description: "Default financial case",
        created: Date.now(),
        modified: Date.now()
      }
    }
  });


  // Main form matrix state - replaces original formValues with matrix structure
  const [formMatrix, setFormMatrix] = useState({});

  // Track special parameter states (sensitivity, factors, etc.)
  const [S, setS] = useState({});
  const [F, setF] = useState({});
  const [V, setV] = useState({});
  const [R, setR] = useState({});
  const [RF, setRF] = useState({});
  const [subDynamicPlots, setSubDynamicPlots] = useState({
    SP1: "off",
    SP2: "off",
    SP3: "off",
    SP4: "off",
    SP5: "off",
    SP6: "off",
    SP7: "off",
    SP8: "off",
    SP9: "off"
  });

  // Scaling-related state
  const [scalingGroups, setScalingGroups] = useState([]);
  const [scalingBaseCosts, setScalingBaseCosts] = useState({});
  const [finalResults, setFinalResults] = useState({});

  /**
   * derivedFacts — Phase 3: typed DerivedSummaryFact[] per workspace.
   * This is the canonical scaling output for baseline assembly.
   * { 'Amount4': DerivedSummaryFact[], 'Amount5': ..., 'Amount6': ..., 'Amount7': ... }
   */
  const [derivedFacts, setDerivedFacts] = useState({});

  /**
   * scopedMutations — Phase 4: ScopedMutation[] derived from S state.
   * These are the unified mutation representations for branch/version differences.
   * S is kept as the operational authoring surface; scopedMutations is its typed form.
   */
  const [scopedMutations, setScopedMutations] = useState([]);

  // Reset options popup state
  const [showResetOptions, setShowResetOptions] = useState(false);
  const [resetOptions, setResetOptions] = useState({
    S: true,
    F: true,
    V: true,
    R: true
  });

  // Dynamic plots options popup state
  const [showDynamicPlotsOptions, setShowDynamicPlotsOptions] = useState(false);

  // Run options popup state
  const [showRunOptions, setShowRunOptions] = useState(false);
  const [runOptions, setRunOptions] = useState({
    useSummaryItems: true,
    includeRemarks: false,
    includeCustomFeatures: false
  });

  // Synchronization state
  const [isSyncing, setIsSyncing] = useState(false);

  // Icons mapping for UI enhancement
  const iconMapping = {
    // Project configuration icons
    plantLifetimeAmount10: 'clock',
    constructionTimeAmount11: 'hammer',
    plantCapacityAmount12: 'industry',
    plantCapacityFactorAmount13: 'percentage',

    // Loan configuration icons
    debtRatioAmount20: 'money-bill-wave',
    interestRateAmount21: 'percentage',
    loanTermAmount22: 'calendar-alt',

    // Rates & Fixed costs icons
    inflationRateAmount30: 'chart-line',
    discountRateAmount31: 'percentage',
    taxRateAmount32: 'file-invoice-dollar',
    costOfCapitalAmount33: 'coins',
    F1Amount34: 'cog',
    F2Amount35: 'cog',
    F3Amount36: 'cog',
    F4Amount37: 'cog',
    F5Amount38: 'cog',

    // Process quantities icons (V parameters)
    vAmount40: 'boxes',
    vAmount41: 'boxes',
    vAmount42: 'boxes',
    vAmount43: 'boxes',
    vAmount44: 'boxes',
    vAmount45: 'boxes',
    vAmount46: 'boxes',
    vAmount47: 'boxes',
    vAmount48: 'boxes',
    vAmount49: 'boxes',

    // Process costs icons (V parameters)
    rAmount60: 'dollar-sign',
    rAmount61: 'dollar-sign',
    rAmount62: 'dollar-sign',
    rAmount63: 'dollar-sign',
    rAmount64: 'dollar-sign',
    rAmount65: 'dollar-sign',
    rAmount66: 'dollar-sign',
    rAmount67: 'dollar-sign',
    rAmount68: 'dollar-sign',
    rAmount69: 'dollar-sign',

    // Fixed revenue components icons (RF parameters)
    RF1Amount80: 'money-check-alt',
    RF2Amount81: 'money-check-alt',
    RF3Amount82: 'money-check-alt',
    RF4Amount83: 'money-check-alt',
    RF5Amount84: 'money-check-alt'
  };

  //=========================================================================
  // INITIALIZATION
  //=========================================================================

  // Initialize form matrix with default values
  useEffect(() => {
    // Skip if already initialized
    if (Object.keys(formMatrix).length > 0) return;

    // Create initial form matrix
    const initialFormMatrix = {};

    // For each parameter in property mapping
    Object.keys(propertyMapping).forEach(paramId => {
      const isNumber = typeof defaultValues[paramId] === 'number';
      const defaultValue = defaultValues[paramId] !== undefined ? defaultValues[paramId] : '';

      // Get parameter type (V, R, F, RF, S) for dynamic appendix
      let vKey = null, rKey = null, fKey = null, rfKey = null, sKey = null;

      // Determine V parameter keys
      if (paramId.includes('vAmount')) {
        const num = parseInt(paramId.replace('vAmount', ''));
        if (num >= 40 && num <= 49) vKey = `V${num - 39}`;
        else if (num >= 50 && num <= 59) vKey = `V${num - 49}`;
      }

      // Determine R parameter keys
      if (paramId.includes('rAmount')) {
        const num = parseInt(paramId.replace('rAmount', ''));
        if (num >= 60 && num <= 69) rKey = `R${num - 59}`;
        else if (num >= 70 && num <= 79) rKey = `R${num - 69}`;
      }

      // Determine F parameter keys
      if (paramId.includes('Amount')) {
        const num = parseInt(paramId.replace(/\D/g, ''));
        if (num >= 34 && num <= 38) fKey = `F${num - 33}`;
      }

      // Determine RF parameter keys
      if (paramId.includes('Amount')) {
        const num = parseInt(paramId.replace(/\D/g, ''));
        if (num >= 80 && num <= 84) rfKey = `RF${num - 79}`;
      }

      // Determine S parameter keys
      if (paramId.includes('Amount')) {
        const num = parseInt(paramId.replace(/\D/g, ''));
        if (num >= 10 && num <= 84) sKey = `S${num}`;
      }

      // Initialize matrix structure for this parameter
      initialFormMatrix[paramId] = {
        id: paramId,
        label: propertyMapping[paramId],
        type: isNumber ? 'number' : 'text',
        step: isNumber ? 1 : undefined,
        placeholder: isNumber ? '0' : '',
        remarks: '',
        versions: {},
        matrix: {},
        inheritance: {},
        efficacyPeriod: {
          start: { value: 0 },
          end: { value: defaultValues['plantLifetimeAmount10'] || 20 }
        },
        dynamicAppendix: {
          scaling: {
            type: null,
            factor: 1,
            operation: 'multiply',
            enabled: false,
            baseValue: defaultValue,
            scaledValue: defaultValue,
            notes: ''
          },
          group: { id: null, name: null, isProtected: false },
          itemState: {
            vKey: vKey,
            rKey: rKey,
            fKey: fKey,
            rfKey: rfKey,
            sKey: sKey,
            status: vKey || rKey || fKey || rfKey ? 'off' : undefined
          }
        }
      };

      // Initialize versions — matrix[versionId] holds the direct value (no zone dimension)
      versions.list.forEach(versionId => {
        initialFormMatrix[paramId].versions[versionId] = {
          label: versions.metadata[versionId].label,
          isActive: versionId === versions.active
        };

        initialFormMatrix[paramId].matrix[versionId] = defaultValue;
        initialFormMatrix[paramId].inheritance[versionId] = {
          source: null,
          percentage: 100
        };
      });
    });

    // Set the initial form matrix
    setFormMatrix(initialFormMatrix);

    // Initialize special parameter states (V, R, F, RF, S)
    const initialV = {};
    const initialR = {};
    const initialF = {};
    const initialRF = {};
    const initialS = {};

    Object.entries(initialFormMatrix).forEach(([paramId, param]) => {
      const { dynamicAppendix } = param;

      if (dynamicAppendix.itemState.vKey) {
        initialV[dynamicAppendix.itemState.vKey] = 'off';
      }

      if (dynamicAppendix.itemState.rKey) {
        initialR[dynamicAppendix.itemState.rKey] = 'off';
      }

      if (dynamicAppendix.itemState.fKey) {
        initialF[dynamicAppendix.itemState.fKey] = 'off';
      }

      if (dynamicAppendix.itemState.rfKey) {
        initialRF[dynamicAppendix.itemState.rfKey] = 'off';
      }

      if (dynamicAppendix.itemState.sKey) {
        initialS[dynamicAppendix.itemState.sKey] = {
          status: 'off',
          mode: 'percentage',
          variation: 10,
          values: []
        };
      }
    });

    // Set initial states
    setV(initialV);
    setR(initialR);
    setF(initialF);
    setRF(initialRF);
    setS(initialS);

  }, []);

  //=========================================================================
  // PHASE 4 — S → ScopedMutation bridge
  // Keep scopedMutations in sync whenever S changes.
  //=========================================================================
  useEffect(() => {
    const activeVersionId = versions.active;
    const mutations = sStateToScopedMutations(S, activeVersionId, activeVersionId);
    setScopedMutations(mutations);
  }, [S, versions.active]);

  //=========================================================================
  // VERSION & ZONE MANAGEMENT
  //=========================================================================

  /**
   * Create a new version
   * @param {string} label - Display label for the version
   * @param {string} description - Optional description for the version
   * @param {string} baseVersion - Optional base version to inherit from
   * @returns {string} Created version ID
   */
  const createVersion = useCallback((label, description = null, baseVersion = null) => {
    // Generate version ID
    const versionId = `v${versions.list.length + 1}`;

    // Update versions state
    setVersions(prevVersions => {
      const newVersions = {
        ...prevVersions,
        list: [...prevVersions.list, versionId],
        metadata: {
          ...prevVersions.metadata,
          [versionId]: {
            label,
            description: description || `Version created on ${new Date().toLocaleString()}`,
            created: Date.now(),
            modified: Date.now(),
            baseVersion
          }
        }
      };

      return newVersions;
    });

    // Update form matrix to include the new version
    setFormMatrix(prevMatrix => {
      const newMatrix = { ...prevMatrix };

      // For each parameter in the matrix
      Object.keys(newMatrix).forEach(paramId => {
        const param = { ...newMatrix[paramId] };

        // Add version to versions object
        param.versions[versionId] = {
          label,
          isActive: false
        };

        // Set inheritance configuration and initialize matrix value
        if (baseVersion) {
          param.inheritance[versionId] = {
            source: baseVersion,
            percentage: 70
          };
          // Copy value from base version directly
          param.matrix[versionId] = param.matrix[baseVersion] ?? (defaultValues[paramId] ?? '');
        } else {
          param.inheritance[versionId] = {
            source: null,
            percentage: 100
          };
          param.matrix[versionId] = defaultValues[paramId] ?? '';
        }

        newMatrix[paramId] = param;
      });

      return newMatrix;
    });

    return versionId;
  }, [versions]);

  /**
   * Set the active version
   * @param {string} versionId - ID of the version to activate
   */
  const setActiveVersion = useCallback((versionId) => {
    // Skip if version doesn't exist
    if (!versions.list.includes(versionId)) return;

    // Update versions state
    setVersions(prevVersions => ({
      ...prevVersions,
      active: versionId
    }));

    // Update active state in form matrix
    setFormMatrix(prevMatrix => {
      const newMatrix = { ...prevMatrix };

      // For each parameter in the matrix
      Object.keys(newMatrix).forEach(paramId => {
        const param = { ...newMatrix[paramId] };

        // Update active state for all versions
        Object.keys(param.versions).forEach(ver => {
          param.versions[ver] = {
            ...param.versions[ver],
            isActive: ver === versionId
          };
        });

        newMatrix[paramId] = param;
      });

      return newMatrix;
    });
  }, [versions.list]);

  //=========================================================================
  // PARAMETER VALUE MANAGEMENT
  //=========================================================================

  /**
   * Get parameter value for specified version and zone
   * @param {string} paramId - Parameter ID
   * @param {string} versionId - Optional version ID (defaults to active)
   * @param {string} zoneId - Optional zone ID (defaults to active)
   * @returns {any} Parameter value
   */
  const getParameterValue = useCallback((paramId, versionId = null) => {
    if (!formMatrix[paramId]) return null;

    const param = formMatrix[paramId];
    const targetVersion = versionId || versions.active;

    const val = param.matrix[targetVersion];
    return val === undefined ? null : val;
  }, [formMatrix, versions.active]);

  /**
   * Update parameter value for specified version and zone
   * @param {string} paramId - Parameter ID
   * @param {any} value - New parameter value
   * @param {string} versionId - Optional version ID (defaults to active)
   * @param {string} zoneId - Optional zone ID (defaults to active)
   * @returns {boolean} Success indicator
   */
  const updateParameterValue = useCallback((paramId, value, versionId = null) => {
    if (!formMatrix[paramId]) return false;

    const targetVersion = versionId || versions.active;

    setFormMatrix(prevMatrix => {
      const newMatrix = { ...prevMatrix };
      const param = { ...newMatrix[paramId] };

      param.matrix[targetVersion] = value;

      // Apply inheritance to child versions
      Object.keys(param.inheritance).forEach(ver => {
        const inheritance = param.inheritance[ver];
        if (inheritance.source === targetVersion && inheritance.percentage < 100) {
          const currentValue = param.matrix[ver];
          if (currentValue === undefined) return;
          const inheritPercent = inheritance.percentage / 100;
          param.matrix[ver] = typeof currentValue === 'number' && typeof value === 'number'
            ? (currentValue * (1 - inheritPercent)) + (value * inheritPercent)
            : value;
        }
      });

      newMatrix[paramId] = param;
      return newMatrix;
    });

    return true;
  }, [formMatrix, versions.active]);

  /**
   * Get effective value based on parameter status
   * @param {string} paramId - Parameter ID
   * @param {string} versionId - Optional version ID (defaults to active)
   * @param {string} zoneId - Optional zone ID (defaults to active)
   * @returns {any} Effective parameter value (considering active/inactive status)
   */
  const getEffectiveValue = useCallback((paramId, versionId = null) => {
    if (!formMatrix[paramId]) return null;

    const param = formMatrix[paramId];
    const targetVersion = versionId || versions.active;

    const baseValue = param.matrix[targetVersion];
    if (baseValue === undefined) return null;

    // Check if parameter is active
    if (!isParameterActive(paramId)) {
      return baseValue;
    }

    // Get scaling info
    const { scaling } = param.dynamicAppendix;

    // If scaling is enabled, apply it
    if (scaling.enabled) {
      switch (scaling.operation) {
        case 'multiply':
          return typeof baseValue === 'number' ? baseValue * scaling.factor : baseValue;
        case 'add':
          return typeof baseValue === 'number' ? baseValue + scaling.factor : baseValue;
        case 'subtract':
          return typeof baseValue === 'number' ? baseValue - scaling.factor : baseValue;
        case 'divide':
          return typeof baseValue === 'number' && scaling.factor !== 0 
            ? baseValue / scaling.factor 
            : baseValue;
        case 'power':
          return typeof baseValue === 'number' 
            ? Math.pow(baseValue, scaling.factor) 
            : baseValue;
        case 'log':
          return typeof baseValue === 'number' && baseValue > 0 
            ? Math.log(baseValue) * scaling.factor 
            : baseValue;
        case 'exponential':
          return typeof baseValue === 'number' && baseValue > 0 
            ? Math.exp(Math.log(baseValue) * scaling.factor) 
            : baseValue;
        default:
          return baseValue;
      }
    }

    return baseValue;
  }, [formMatrix, versions.active]);

  /**
   * Check if parameter is active based on state (V, R, F, RF)
   * @param {string} paramId - Parameter ID
   * @returns {boolean} True if parameter is active
   */
  const isParameterActive = useCallback((paramId) => {
    if (!formMatrix[paramId]) return false;

    const { dynamicAppendix } = formMatrix[paramId];

    // Check V parameter status
    if (dynamicAppendix.itemState.vKey && V[dynamicAppendix.itemState.vKey] === 'off') {
      return false;
    }

    // Check R parameter status
    if (dynamicAppendix.itemState.rKey && R[dynamicAppendix.itemState.rKey] === 'off') {
      return false;
    }

    // Check F parameter status
    if (dynamicAppendix.itemState.fKey && F[dynamicAppendix.itemState.fKey] === 'off') {
      return false;
    }

    // Check RF parameter status
    if (dynamicAppendix.itemState.rfKey && RF[dynamicAppendix.itemState.rfKey] === 'off') {
      return false;
    }

    return true;
  }, [formMatrix, V, R, F, RF]);

  /**
   * Update efficacy period for a parameter
   * @param {string} paramId - Parameter ID
   * @param {number} start - Start year
   * @param {number} end - End year
   * @returns {boolean} Success indicator
   */
  const updateEfficacyPeriod = useCallback((paramId, start, end) => {
    if (!formMatrix[paramId]) return false;

    // Get plant lifetime for validation
    const plantLifetime = formMatrix['plantLifetimeAmount10']?.matrix[versions.active] || 20;

    // Validate start and end values
    const validStart = Math.max(0, Math.min(start, end, plantLifetime));
    const validEnd = Math.max(validStart, Math.min(end, plantLifetime));

    // Update efficacy period
    setFormMatrix(prevMatrix => {
      const newMatrix = { ...prevMatrix };
      const param = { ...newMatrix[paramId] };

      param.efficacyPeriod = {
        start: { value: validStart },
        end: { value: validEnd }
      };

      newMatrix[paramId] = param;
      return newMatrix;
    });

    return true;
  }, [formMatrix, versions.active]);

  //=========================================================================
  // INPUT HANDLERS
  //=========================================================================

  /**
   * Generic input change handler for form values
   * @param {Event} event - Input change event
   * @param {string} itemId - Parameter ID
   * @param {string} fieldType - Field type ('value', 'label', 'step', etc.)
   * @param {string} subField - Optional sub-field for nested properties
   */
  const handleInputChange = useCallback((event, itemId, fieldType, subField = null) => {
    const value = event.target?.value;

    // Skip if parameter doesn't exist
    if (!formMatrix[itemId]) return;

    setFormMatrix(prevMatrix => {
      const newMatrix = { ...prevMatrix };
      const item = { ...newMatrix[itemId] };

      // Handle different field types
      switch (fieldType) {
        case 'value':
          item.matrix[versions.active] = value;
          break;

        case 'label':
          item.label = value;
          break;

        case 'step':
          item.step = value;
          break;

        case 'remarks':
          item.remarks = value;
          break;

        case 'efficacyPeriod':
          // Handle nested efficacy period updates
          if (!item.efficacyPeriod) {
            item.efficacyPeriod = {
              start: { value: 0 },
              end: { value: 20 }
            };
          }

          if (subField) {
            if (!item.efficacyPeriod[subField]) {
              item.efficacyPeriod[subField] = { value: 0 };
            }

            item.efficacyPeriod[subField].value = value;
          }
          break;

        default:
          // No action for unknown field types
          break;
      }

      newMatrix[itemId] = item;
      return newMatrix;
    });
  }, [formMatrix, versions.active]);

  /**
   * Toggle V parameter status (on/off)
   * @param {string} key - V parameter key (e.g., 'V1')
   */
  const toggleV = useCallback((key) => {
    setV(prev => ({
      ...prev,
      [key]: prev[key] === 'on' ? 'off' : 'on'
    }));
  }, []);

  /**
   * Toggle R parameter status (on/off)
   * @param {string} key - R parameter key (e.g., 'R1')
   */
  const toggleR = useCallback((key) => {
    setR(prev => ({
      ...prev,
      [key]: prev[key] === 'on' ? 'off' : 'on'
    }));
  }, []);

  /**
   * Toggle F parameter status (on/off)
   * @param {string} key - F parameter key (e.g., 'F1')
   */
  const toggleF = useCallback((key) => {
    setF(prev => ({
      ...prev,
      [key]: prev[key] === 'on' ? 'off' : 'on'
    }));
  }, []);

  /**
   * Toggle RF parameter status (on/off)
   * @param {string} key - RF parameter key (e.g., 'RF1')
   */
  const toggleRF = useCallback((key) => {
    setRF(prev => ({
      ...prev,
      [key]: prev[key] === 'on' ? 'off' : 'on'
    }));
  }, []);

  /**
   * Toggle dynamic plot status (on/off)
   * @param {string} key - Dynamic plot key (e.g., 'SP1')
   */
  const toggleSubDynamicPlot = useCallback((key) => {
    setSubDynamicPlots(prev => ({
      ...prev,
      [key]: prev[key] === 'on' ? 'off' : 'on'
    }));
  }, []);

  //=========================================================================
  // RESET & OPTIONS HANDLERS
  //=========================================================================

  /**
   * Handle reset button click
   */
  const handleReset = useCallback(() => {
    // Show reset options popup
    setShowResetOptions(true);
  }, []);

  /**
   * Handle reset option toggle
   * @param {string} option - Option to toggle ('S', 'F', 'V', 'R')
   */
  const handleResetOptionChange = useCallback((option) => {
    setResetOptions(prev => ({
      ...prev,
      [option]: !prev[option]
    }));
  }, []);

  /**
   * Handle reset confirmation
   */
  const handleResetConfirm = useCallback(() => {
    // Reset S parameters
    if (resetOptions.S) {
      setS(prev => {
        const newS = { ...prev };
        Object.keys(newS).forEach(key => {
          newS[key] = {
            ...newS[key],
            status: 'off'
          };
        });
        return newS;
      });
    }

    // Reset F parameters
    if (resetOptions.F) {
      setF(prev => {
        const newF = { ...prev };
        Object.keys(newF).forEach(key => {
          newF[key] = 'off';
        });
        return newF;
      });
    }

    // Reset V parameters
    if (resetOptions.V) {
      setV(prev => {
        const newV = { ...prev };
        Object.keys(newV).forEach(key => {
          newV[key] = 'off';
        });
        return newV;
      });
    }

    // Reset R parameters
    if (resetOptions.R) {
      setR(prev => {
        const newR = { ...prev };
        Object.keys(newR).forEach(key => {
          newR[key] = 'off';
        });
        return newR;
      });
    }

    // Close popup
    setShowResetOptions(false);
  }, [resetOptions]);

  /**
   * Handle reset cancellation
   */
  const handleResetCancel = useCallback(() => {
    // Close popup
    setShowResetOptions(false);
  }, []);

  /**
   * Handle dynamic plots options
   */
  const handleDynamicPlots = useCallback(() => {
    // Show dynamic plots options popup
    setShowDynamicPlotsOptions(true);
  }, []);

  /**
   * Handle dynamic plots option change
   * @param {string} option - Option to toggle (e.g., 'SP1')
   */
  const handleDynamicPlotsOptionChange = useCallback((option) => {
    setSubDynamicPlots(prev => ({
      ...prev,
      [option]: prev[option] === 'on' ? 'off' : 'on'
    }));
  }, []);

  /**
   * Handle dynamic plots confirmation
   */
  const handleDynamicPlotsConfirm = useCallback(() => {
    // Close popup
    setShowDynamicPlotsOptions(false);
  }, []);

  /**
   * Handle dynamic plots cancellation
   */
  const handleDynamicPlotsCancel = useCallback(() => {
    // Close popup
    setShowDynamicPlotsOptions(false);
  }, []);

  /**
   * Handle run options
   */
  const handleRun = useCallback(() => {
    // Show run options popup
    setShowRunOptions(true);
  }, []);

  /**
   * Handle run option change
   * @param {string} option - Option to toggle
   */
  const handleRunOptionChange = useCallback((option) => {
    setRunOptions(prev => ({
      ...prev,
      [option]: !prev[option]
    }));
  }, []);

  /**
   * Handle run confirmation
   */
  const handleRunConfirm = useCallback(() => {
    // Close popup
    setShowRunOptions(false);

    // Run calculations would be implemented separately
  }, []);

  /**
   * Handle run cancellation
   */
  const handleRunCancel = useCallback(() => {
    // Close popup
    setShowRunOptions(false);
  }, []);

  //=========================================================================
  // SCALING & RESULTS HANDLERS
  //=========================================================================

  /**
   * Handle scaling items final results
   * @param {Array} summaryItems - Summary items with results
   * @param {string} filterKeyword - Filter keyword (Amount4, Amount5, etc.)
   */
  /**
   * handleFinalResultsGenerated — Phase 3 refactored
   *
   * Previously: stored raw summaryItems only.
   * Now: stores raw summaryItems (backward compat) AND produces typed
   * DerivedSummaryFact[] objects stored in derivedFacts state.
   *
   * The derivedFacts map is the canonical scaling output for baseline assembly.
   *
   * @param {Array}  summaryItems  - raw items from SimpleScalingEditor
   * @param {string} filterKeyword - 'Amount4' | 'Amount5' | 'Amount6' | 'Amount7'
   */
  const handleFinalResultsGenerated = useCallback((summaryItems, filterKeyword) => {
    // 1. Keep existing raw storage (backward compat — SensitivityMonitor, etc. may read this)
    setFinalResults(prev => ({
      ...prev,
      [filterKeyword]: summaryItems
    }));

    // 2. Produce typed DerivedSummaryFact[] objects
    const activeVersionId = versions.active;
    const isAmount4or5 = filterKeyword === 'Amount4' || filterKeyword === 'Amount5';

    const facts = (summaryItems ?? []).map((item, idx) => {
      // Determine participation from V/R toggle state
      const toggleKey = isAmount4or5
        ? (item.vKey ?? `V${idx + 1}`)
        : (item.rKey ?? `R${idx + 1}`);
      const toggleState = isAmount4or5
        ? V[toggleKey]
        : R[toggleKey];
      const isAdmitted = toggleState === 'on';

      return createDerivedSummaryFact({
        paramId:            item.id ?? `${filterKeyword}_${idx}`,
        versionId:          activeVersionId,
        sourceWorkspace:    filterKeyword,
        label:              item.label ?? item.id ?? `${filterKeyword}[${idx}]`,
        resolvedValue:      item.finalResult ?? item.scaledValue ?? item.value ?? null,
        participationState: isAdmitted ? 'admitted' : 'excluded',
        sourceType:         'scaling_output',
        provenance: {
          scalingGroupId:  item.groupId ?? null,
          operation:       item.operation ?? null,
          scalingLineage:  item.scalingLineage ?? null,
        },
      });
    });

    setDerivedFacts(prev => ({
      ...prev,
      [filterKeyword]: facts,
    }));
  }, [versions.active, V, R]);

  //=========================================================================
  // BACKEND SYNCHRONIZATION
  //=========================================================================

  /**
   * Synchronize with backend services
   */
  const syncWithBackend = useCallback(async () => {
    setIsSyncing(true);

    try {
      // Prepare payload
      const payload = {
        formMatrix,
        versions,
        V, R, F, RF, S,
        subDynamicPlots,
        scalingGroups,
        finalResults
      };

      // Make API request
      const response = await axios.post('http://localhost:3060/api/sync-matrix-state', payload);

      if (response.data.success) {
        console.log('Synchronized with backend successfully');
      } else {
        console.error('Synchronization failed:', response.data.message);
      }
    } catch (error) {
      console.error('Error synchronizing with backend:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [formMatrix, versions, V, R, F, RF, S, subDynamicPlots, scalingGroups, finalResults]);

  /**
   * Load state from backend services
   */
  const loadFromBackend = useCallback(async () => {
    setIsSyncing(true);

    try {
      // Make API request
      const response = await axios.get('http://localhost:3060/api/load-matrix-state');

      if (response.data.success) {
        // Update state with loaded data
        const {
          formMatrix: loadedFormMatrix,
          versions: loadedVersions,
          V: loadedV,
          R: loadedR,
          F: loadedF,
          RF: loadedRF,
          S: loadedS,
          subDynamicPlots: loadedSubDynamicPlots,
          scalingGroups: loadedScalingGroups,
          finalResults: loadedFinalResults
        } = response.data.state;

        setFormMatrix(loadedFormMatrix || {});
        setVersions(loadedVersions || {
          list: ["v1"],
          active: "v1",
          metadata: { "v1": { label: "Base Case", description: "Default financial case", created: Date.now(), modified: Date.now() } }
        });
        setV(loadedV || {});
        setR(loadedR || {});
        setF(loadedF || {});
        setRF(loadedRF || {});
        setS(loadedS || {});
        setSubDynamicPlots(loadedSubDynamicPlots || {
          SP1: "off", SP2: "off", SP3: "off", SP4: "off", SP5: "off", SP6: "off", SP7: "off", SP8: "off", SP9: "off"
        });
        setScalingGroups(loadedScalingGroups || []);
        setFinalResults(loadedFinalResults || {});

        console.log('Loaded state from backend successfully');
      } else {
        console.error('Loading state failed:', response.data.message);
      }
    } catch (error) {
      console.error('Error loading state from backend:', error);
    } finally {
      setIsSyncing(false);
    }
  }, []);

  /**
   * Export matrix state to JSON file
   */
  const exportMatrixState = useCallback(() => {
    try {
      // Prepare export data
      const exportData = {
        version: "1.0.0",
        timestamp: Date.now(),
        state: {
          formMatrix,
          versions,
          V, R, F, RF, S,
          subDynamicPlots,
          scalingGroups,
          finalResults
        }
      };

      // Convert to JSON string
      const jsonString = JSON.stringify(exportData, null, 2);

      // Create blob and download link
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `matrix-state-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log('Matrix state exported successfully');
    } catch (error) {
      console.error('Error exporting matrix state:', error);
    }
  }, [formMatrix, versions, V, R, F, RF, S, subDynamicPlots, scalingGroups, finalResults]);

  /**
   * Import matrix state from JSON file
   * @param {File} file - JSON file to import
   */
  const importMatrixState = useCallback(async (file) => {
    try {
      // Read file as text
      const text = await file.text();

      // Parse JSON
      const importData = JSON.parse(text);

      // Validate structure
      if (!importData.state || !importData.version) {
        throw new Error('Invalid import file format');
      }

      // Extract state
      const {
        formMatrix: importedFormMatrix,
        versions: importedVersions,
        V: importedV,
        R: importedR,
        F: importedF,
        RF: importedRF,
        S: importedS,
        subDynamicPlots: importedSubDynamicPlots,
        scalingGroups: importedScalingGroups,
        finalResults: importedFinalResults
      } = importData.state;

      setFormMatrix(importedFormMatrix || {});
      setVersions(importedVersions || {
        list: ["v1"],
        active: "v1",
        metadata: { "v1": { label: "Base Case", description: "Default financial case", created: Date.now(), modified: Date.now() } }
      });
      setV(importedV || {});
      setR(importedR || {});
      setF(importedF || {});
      setRF(importedRF || {});
      setS(importedS || {});
      setSubDynamicPlots(importedSubDynamicPlots || {
        SP1: "off", SP2: "off", SP3: "off", SP4: "off", SP5: "off", SP6: "off", SP7: "off", SP8: "off", SP9: "off"
      });
      setScalingGroups(importedScalingGroups || []);
      setFinalResults(importedFinalResults || {});

      console.log('Matrix state imported successfully');
    } catch (error) {
      console.error('Error importing matrix state:', error);
    }
  }, []);

  //=========================================================================
  // PHASE 3 — EXPLICIT RUN PAYLOAD BUILDER
  // Replaces the ad-hoc useSummaryItems late-mutation pattern in handleRun.
  //=========================================================================

  /**
   * buildRunPayload — explicit, deterministic CFA run payload builder.
   *
   * Previously: handleRun() in HomePage.js silently patched formValues by
   * iterating finalResults and overwriting parameter entries when
   * useSummaryItems was enabled.  This was opaque and untestable.
   *
   * Now: this function calls assembleBaseline() (defined below) to get an
   * explicit BaselineAssembly, then builds the payload from:
   *  - directInputs (project/loan/rates) + all other formMatrix values
   *  - admittedDerivedFacts (Amount4/5/6/7 with participationState 'admitted')
   *
   * The backend payload shape is PRESERVED for backward compatibility:
   *  { formValues, summaryItems, selectedV, selectedF, selectedR, selectedRF, ... }
   *
   * @param {string} versionId         - version to run for
   * @param {Object} extraParams       - { selectedVersions, V, F, R, RF, S, targetRow, etc. }
   * @returns {{ payload: Object, assembly: import('./model/coreTypes').BaselineAssembly }}
   */
  const buildRunPayload = useCallback((versionId, extraParams = {}) => {
    // 1. Assemble the baseline (calls assembleBaseline defined in Phase 1 section)
    // We call it inline here since assembleBaseline is defined later in the same hook scope.
    // The assembly is also stored in versionSlots by assembleBaseline().
    const flatValues = {};
    Object.entries(formMatrix).forEach(([pid, p]) => { flatValues[pid] = p.matrix?.[versionId] ?? null; });

    // Partition direct inputs
    const projectConfig = {};
    const loanConfig = {};
    const ratesFixedCosts = {};
    BASELINE_DIRECT_INPUT_PREFIXES.forEach(paramId => {
      const val = flatValues[paramId];
      if (val === undefined || val === null) return;
      if (paramId.includes('Amount1')) projectConfig[paramId] = val;
      else if (paramId.includes('Amount2')) loanConfig[paramId] = val;
      else ratesFixedCosts[paramId] = val;
    });

    // Admitted derived facts from derivedFacts (typed) or fall back to finalResults (raw)
    const admittedFacts = [];
    const excludedFacts = [];
    SCALING_OUTPUT_WORKSPACES.forEach(workspace => {
      const typed = derivedFacts[workspace];
      if (typed && typed.length > 0) {
        typed.forEach(f => {
          if (f.participationState === 'admitted') admittedFacts.push(f);
          else excludedFacts.push(f);
        });
      } else {
        // Fall back to raw finalResults with V/R state check (same as assembleBaseline)
        const raw = finalResults[workspace] ?? [];
        const isAmount4or5 = workspace === 'Amount4' || workspace === 'Amount5';
        raw.forEach((item, idx) => {
          const toggleKey = isAmount4or5
            ? (item.vKey ?? `V${idx + 1}`)
            : (item.rKey ?? `R${idx + 1}`);
          const isAdmitted = (isAmount4or5 ? V[toggleKey] : R[toggleKey]) === 'on';
          const fact = createDerivedSummaryFact({
            paramId:            item.id ?? `${workspace}_${idx}`,
            versionId,
            sourceWorkspace:    workspace,
            label:              item.label ?? item.id ?? '',
            resolvedValue:      item.finalResult ?? item.scaledValue ?? item.value ?? null,
            participationState: isAdmitted ? 'admitted' : 'excluded',
            sourceType:         'scaling_output',
          });
          if (isAdmitted) admittedFacts.push(fact);
          else excludedFacts.push(fact);
        });
      }
    });

    const assembly = createBaselineAssembly({
      versionId,
      directInputs: { projectConfig, loanConfig, ratesFixedCosts },
      admittedDerivedFacts:  admittedFacts,
      excludedDerivedFacts:  excludedFacts,
    });

    // 2. Build the run-ready formValues:
    //    start with all formMatrix values (flat), then overlay admitted derived facts
    const runFormValues = { ...formMatrix };
    admittedFacts.forEach(fact => {
      if (runFormValues[fact.paramId]) {
        runFormValues[fact.paramId] = {
          ...runFormValues[fact.paramId],
          value: fact.resolvedValue,
          // Tag so the backend can identify this as an assembled derived fact
          _derivedFact: true,
          _participationState: 'admitted',
        };
      }
    });

    // 3. Build summaryItems in the legacy format the backend expects
    const summaryItems = {};
    SCALING_OUTPUT_WORKSPACES.forEach(workspace => {
      summaryItems[workspace] = admittedFacts
        .filter(f => f.sourceWorkspace === workspace)
        .map(f => ({
          id:          f.paramId,
          label:       f.label,
          finalResult: f.resolvedValue,
          // Preserve any extra fields from the original raw item
          ...(finalResults[workspace]?.find(r => r.id === f.paramId) ?? {}),
        }));
    });

    const payload = {
      selectedVersions: extraParams.selectedVersions ?? [versionId],
      selectedV:        extraParams.V ?? V,
      selectedF:        extraParams.F ?? F,
      selectedR:        extraParams.R ?? R,
      selectedRF:       extraParams.RF ?? RF,
      selectedCalculationOption: extraParams.selectedCalculationOption,
      targetRow:        extraParams.targetRow,
      SenParameters:    extraParams.S ?? S,
      formValues:       runFormValues,
      summaryItems,
      includeRemarks:       extraParams.includeRemarks ?? false,
      includeCustomFeatures: extraParams.includeCustomFeatures ?? false,
      // Phase 3: explicit assembly metadata for traceability
      _baselineAssembly: {
        versionId,
        assembledAt:           assembly.assembledAt,
        admittedCount:         admittedFacts.length,
        excludedCount:         excludedFacts.length,
        directInputParamCount: BASELINE_DIRECT_INPUT_PREFIXES.length,
      },
    };

    return { payload, assembly };
  }, [formMatrix, finalResults, derivedFacts, V, R, F, RF, S, versions.active]);

  //=========================================================================
  // PHASE 1 — VERSION-CENTRIC MODEL SURFACE
  // New state and functions introduced by the TEA-MD Overhaul.
  // These live alongside the existing API without breaking it.
  //=========================================================================

  /**
   * VersionSlot registry.
   * Map<slotId, VersionSlot> — the canonical version container.
   * Initialised from the legacy `versions` metadata so it stays in sync.
   */
  const [versionSlots, setVersionSlots] = useState(() => {
    const map = new Map();
    ['v1'].forEach(id => {
      map.set(id, createVersionSlot({
        id,
        label: 'Base Case',
        description: 'Default financial case',
      }));
    });
    return map;
  });

  /**
   * Sync a new version into the VersionSlot registry when one is created
   * through the legacy createVersion() path.
   * @param {string} id
   * @param {Object} meta - legacy metadata object
   */
  const registerVersionSlotFromLegacy = useCallback((id, meta) => {
    setVersionSlots(prev => {
      const next = new Map(prev);
      if (!next.has(id)) {
        next.set(id, versionSlotFromLegacy(id, meta));
      }
      return next;
    });
  }, []);

  /**
   * assembleBaseline — explicit, deterministic baseline assembly.
   *
   * Builds a BaselineAssembly for the given version from:
   *  1. Direct inputs (project config, loan config, rates & fixed costs)
   *  2. Enabled (admitted) derived results from Amount4/5/6/7 only
   *
   * This replaces the ad-hoc `useSummaryItems` payload mutation pattern.
   * Phase 3 will refine this further with full scaling-lineage provenance.
   *
   * @param {string} versionId - The version slot to assemble for
   * @returns {import('./model/coreTypes').BaselineAssembly}
   */
  const assembleBaseline = useCallback((versionId) => {
    // 1. Extract all flat values for this version
    const flatValues = {};
    Object.entries(formMatrix).forEach(([pid, p]) => { flatValues[pid] = p.matrix?.[versionId] ?? null; });

    // 2. Partition into direct inputs
    const projectConfig = {};
    const loanConfig = {};
    const ratesFixedCosts = {};

    BASELINE_DIRECT_INPUT_PREFIXES.forEach(paramId => {
      const val = flatValues[paramId];
      if (val === undefined || val === null) return;
      if (paramId.includes('Amount1')) {
        projectConfig[paramId] = val;
      } else if (paramId.includes('Amount2')) {
        loanConfig[paramId] = val;
      } else if (paramId.includes('Amount3') || paramId.startsWith('F')) {
        ratesFixedCosts[paramId] = val;
      }
    });

    // 3. Partition finalResults into admitted / excluded derived facts
    const admittedDerivedFacts = [];
    const excludedDerivedFacts = [];

    SCALING_OUTPUT_WORKSPACES.forEach(workspace => {
      const results = finalResults[workspace] ?? [];
      results.forEach((result, idx) => {
        // Determine participation from V/R toggle state
        // For Amount4/5 → V keys; for Amount6/7 → R keys
        const paramId = result.id ?? result.paramId ?? `${workspace}_${idx}`;
        const isAmount4or5 = workspace === 'Amount4' || workspace === 'Amount5';
        const toggleState = isAmount4or5
          ? V[result.vKey ?? `V${idx + 1}`]
          : R[result.rKey ?? `R${idx + 1}`];
        const isAdmitted = toggleState === 'on';

        const fact = createDerivedSummaryFact({
          paramId,
          versionId,
          sourceWorkspace: workspace,
          label: result.label ?? paramId,
          resolvedValue: result.value ?? result.scaledValue ?? null,
          participationState: isAdmitted ? 'admitted' : 'excluded',
          sourceType: 'scaling_output',
          provenance: {
            scalingGroupId: result.groupId ?? null,
            operation: result.operation ?? null,
            scalingLineage: result.scalingLineage ?? null,
          },
        });

        if (isAdmitted) {
          admittedDerivedFacts.push(fact);
        } else {
          excludedDerivedFacts.push(fact);
        }
      });
    });

    const assembly = createBaselineAssembly({
      versionId,
      directInputs: { projectConfig, loanConfig, ratesFixedCosts },
      admittedDerivedFacts,
      excludedDerivedFacts,
    });

    // 4. Attach assembly to the corresponding VersionSlot
    setVersionSlots(prev => {
      const next = new Map(prev);
      const slotId = `v${versionId}`;
      const slot = next.get(slotId) ?? next.get(versionId);
      if (slot) {
        next.set(slot.id, { ...slot, baselineAssembly: assembly, modified: Date.now() });
      }
      return next;
    });

    return assembly;
  }, [formMatrix, finalResults, V, R]);

  //=========================================================================
  // RETURN VALUES FOR HOOK
  //=========================================================================

  return {
    // Core matrix structures
    formMatrix,
    setFormMatrix,
    versions,

    // Value accessors
    getParameterValue,
    updateParameterValue,
    handleInputChange,

    // Reset functionality
    handleReset,

    // Special parameters
    S, setS,
    F, setF, toggleF,
    V, setV, toggleV,
    R, setR, toggleR,
    RF, setRF, toggleRF,

    // Dynamic plots
    subDynamicPlots, setSubDynamicPlots, toggleSubDynamicPlot,

    // Scaling
    scalingGroups, setScalingGroups,
    scalingBaseCosts, setScalingBaseCosts,
    finalResults, setFinalResults,
    handleFinalResultsGenerated,

    // Reset options popup
    showResetOptions,
    resetOptions, setResetOptions,
    handleResetOptionChange,
    handleResetConfirm,
    handleResetCancel,

    // Dynamic plots popup
    showDynamicPlotsOptions,
    handleDynamicPlots,
    handleDynamicPlotsOptionChange,
    handleDynamicPlotsConfirm,
    handleDynamicPlotsCancel,

    // Run options popup
    showRunOptions,
    runOptions, setRunOptions,
    handleRun,
    handleRunOptionChange,
    handleRunConfirm,
    handleRunCancel,

    // Matrix-specific methods
    getEffectiveValue,
    isParameterActive,
    createVersion,
    setActiveVersion,
    updateEfficacyPeriod,

    // Backend synchronization
    syncWithBackend,
    loadFromBackend,
    isSyncing,
    exportMatrixState,
    importMatrixState,

    // Icon mapping for UI
    propertyMapping,
    iconMapping,

    // ── Phase 1: New version-centric model surface ──────────────────────────
    /**
     * VersionSlot registry.  Map<slotId, VersionSlot>.
     * Canonical version containers for the new model.
     */
    versionSlots,

    /**
     * Explicitly assembles a BaselineAssembly for the given versionId.
     * Returns the assembled object and attaches it to the VersionSlot.
     *
     * @param {string} versionId
     * @returns {import('./model/coreTypes').BaselineAssembly}
     */
    assembleBaseline,

    /**
     * Register a version that was created through the legacy createVersion()
     * path into the new VersionSlot registry.
     *
     * @param {string} id
     * @param {Object} legacyMeta
     */
    registerVersionSlotFromLegacy,

    // ── Phase 3: Scaling → derived facts → baseline assembly ────────────────
    /**
     * Typed DerivedSummaryFact[] per workspace.
     * { 'Amount4': DerivedSummaryFact[], ... }
     * Canonical scaling output for baseline assembly and comparison.
     */
    derivedFacts,

    /**
     * buildRunPayload — builds an explicit, deterministic CFA run payload.
     * Replaces the useSummaryItems ad-hoc patch in handleRun.
     *
     * @param {string} versionId
     * @param {Object} extraParams - { selectedVersions, V, F, R, RF, S, targetRow, ... }
     * @returns {{ payload: Object, assembly: BaselineAssembly }}
     */
    buildRunPayload,

    // ── Phase 4: Unified mutation model ──────────────────────────────────────
    /**
     * scopedMutations — ScopedMutation[] bridged from S state.
     * Updated automatically whenever S changes.
     * This is the unified representation of branch/version differences.
     * @type {import('./model/coreTypes').ScopedMutation[]}
     */
    scopedMutations,

    /**
     * Get the linear mutation ledger for the current scopedMutations.
     * The ledger explains what changed, where, and whether it won/was suppressed.
     *
     * @param {Object} [labelMap] - optional { paramId → label }
     * @returns {import('./model/mutationLedger').LedgerEntry[]}
     */
    getMutationLedger: (labelMap = {}) => buildMutationLedger(scopedMutations, labelMap),

    /**
     * Phase 5: Build a patched formMatrix representing an agent candidate.
     *
     * @param {object[]} proposal         — array of { targetId, mutationType, value, rationale, durationPath? }
     * @param {string}   candidateId      — slot id for the agent candidate (e.g. 'agent-v1')
     * @param {string}   [referenceId]    — version to read reference values from (defaults to activeVersionId)
     * @returns {{ patchedFormMatrix: object, mutations: ScopedMutation[] }}
     */
    buildAgentCandidatePatch: (proposal, candidateId, referenceId) => {
      const refId = referenceId ?? activeVersionId;
      const mutations = agentProposalToMutations(proposal, candidateId, refId);
      const patchedFormMatrix = applyAgentMutations(formValues, mutations, candidateId, refId, CANONICAL_ZONE);
      return { patchedFormMatrix, mutations };
    },
  };
}

/**
 * Efficacy Module - Provides time-based efficacy management
 * This extends the matrix form values with efficacy-aware calculations
 */
export class EfficacyManager {
  /**
   * Constructor
   * @param {Object} matrixFormValues - Matrix form values object
   */
  constructor(matrixFormValues) {
    this.formMatrix = matrixFormValues?.formMatrix || {};
    this.versions = matrixFormValues?.versions || { active: 'v1' };
    this.zones = matrixFormValues?.zones || { active: 'z1' };
    this.efficacyPeriods = {};
    this.simulationTime = 0;

    // Initialize efficacy periods
    this.initializeEfficacyPeriods();
  }

  /**
   * Initialize efficacy periods based on form matrix
   */
  initializeEfficacyPeriods() {
    this.efficacyPeriods = {};

    // Get plant lifetime for default end time
    const plantLifetime = this.getPlantLifetime();

    // For each parameter in form matrix
    Object.keys(this.formMatrix).forEach(paramId => {
      const param = this.formMatrix[paramId];

      if (param.efficacyPeriod) {
        this.efficacyPeriods[paramId] = {
          start: param.efficacyPeriod.start?.value || 0,
          end: param.efficacyPeriod.end?.value || plantLifetime,
          isCustomized: (param.efficacyPeriod.start?.value > 0 || 
                         param.efficacyPeriod.end?.value < plantLifetime)
        };
      } else {
        // Default efficacy period
        this.efficacyPeriods[paramId] = {
          start: 0,
          end: plantLifetime,
          isCustomized: false
        };
      }
    });
  }

  /**
   * Get plant lifetime value
   * @returns {number} Plant lifetime value
   */
  getPlantLifetime() {
    const activeVersion = this.versions?.active || 'v1';
    const activeZone = this.zones?.active || 'z1';

    if (this.formMatrix['plantLifetimeAmount10']) {
      return this.formMatrix['plantLifetimeAmount10'].matrix?.[activeVersion]?.[activeZone] || 20;
    }

    return 20; // Default plant lifetime
  }

  /**
   * Set simulation time
   * @param {number} time - Simulation time (year)
   */
  setSimulationTime(time) {
    this.simulationTime = time;
  }

  /**
   * Check if parameter is active at current simulation time
   * @param {string} paramId - Parameter ID
   * @returns {boolean} True if parameter is active
   */
  isParameterActive(paramId) {
    if (!this.efficacyPeriods[paramId]) return true;

    const { start, end } = this.efficacyPeriods[paramId];
    return this.simulationTime >= start && this.simulationTime <= end;
  }

  /**
   * Get effective value for parameter at current simulation time
   * @param {string} paramId - Parameter ID
   * @param {any} baseValue - Base parameter value
   * @param {any} scaledValue - Scaled parameter value
   * @returns {any} Effective value based on active status
   */
  getEffectiveValue(paramId, baseValue, scaledValue) {
    if (!this.isParameterActive(paramId)) {
      return baseValue;
    }

    return scaledValue;
  }

  /**
   * Update efficacy period for parameter
   * @param {string} paramId - Parameter ID
   * @param {number} start - Start year
   * @param {number} end - End year
   * @returns {boolean} Success indicator
   */
  updateEfficacyPeriod(paramId, start, end) {
    if (!this.efficacyPeriods[paramId]) {
      this.efficacyPeriods[paramId] = { start: 0, end: this.getPlantLifetime(), isCustomized: false };
    }

    // Validate start/end
    const plantLifetime = this.getPlantLifetime();
    const validStart = Math.max(0, Math.min(start, end, plantLifetime));
    const validEnd = Math.max(validStart, Math.min(end, plantLifetime));

    // Update efficacy period
    this.efficacyPeriods[paramId] = {
      start: validStart,
      end: validEnd,
      isCustomized: validStart > 0 || validEnd < plantLifetime
    };

    return true;
  }

  /**
   * Generate configuration matrix for time periods
   * @returns {Array} Configuration matrix
   */
  generateConfigurationMatrix() {
    const plantLifetime = this.getPlantLifetime();

    // Find all break points (unique start/end years)
    const breakPoints = new Set();
    breakPoints.add(0);
    breakPoints.add(plantLifetime);

    Object.values(this.efficacyPeriods).forEach(efficacy => {
      if (efficacy.start > 0) breakPoints.add(efficacy.start);
      if (efficacy.end < plantLifetime) breakPoints.add(efficacy.end + 1);
    });

    // Sort break points
    const sortedBreaks = Array.from(breakPoints).sort((a, b) => a - b);

    // Generate time periods
    const timePeriods = [];
    for (let i = 0; i < sortedBreaks.length - 1; i++) {
      const start = sortedBreaks[i];
      const end = sortedBreaks[i + 1] - 1;

      if (start <= end) {
        timePeriods.push({ start, end, length: end - start + 1 });
      }
    }

    // Create matrix rows
    const matrix = timePeriods.map(period => {
      const row = {
        start: period.start,
        end: period.end,
        length: period.length
      };

      // For each parameter, check if it's active during this period
      Object.keys(this.efficacyPeriods).forEach(paramId => {
        const efficacy = this.efficacyPeriods[paramId];
        const isActive = period.start >= efficacy.start && period.end <= efficacy.end;
        row[paramId] = isActive ? 1 : 0;
      });

      return row;
    });

    return matrix;
  }

  /**
   * Apply efficacy periods to scaling groups
   * @param {Array} scalingGroups - Scaling groups
   * @returns {Array} Efficacy-aware scaling groups
   */
  applyEfficacyToScalingGroups(scalingGroups) {
    return scalingGroups.map(group => {
      // Apply efficacy to each item in group
      const efficacyItems = group.items.map(item => {
        const isActive = this.isParameterActive(item.id);

        return {
          ...item,
          isActive,
          effectiveValue: isActive ? item.scaledValue : item.baseValue,
          efficacyPeriod: this.efficacyPeriods[item.id]
        };
      });

      return {
        ...group,
        items: efficacyItems
      };
    });
  }
}

/**
 * Matrix Value Editor Component
 * Provides UI for editing matrix values for a specific parameter
 */
export function MatrixValueEditor({ paramId, formMatrix, versions, zones, updateParameterValue, onClose }) {
  const [selectedVersion, setSelectedVersion] = useState(versions.active);
  const [selectedZone, setSelectedZone] = useState(zones.active);
  const [currentValue, setCurrentValue] = useState('');
  const [editing, setEditing] = useState(false);

  // Get parameter from form matrix
  const parameter = formMatrix[paramId];

  // Set initial value based on selected version and zone
  useEffect(() => {
    if (parameter &&
        parameter.matrix[selectedVersion] &&
        parameter.matrix[selectedVersion][selectedZone] !== undefined) {
      setCurrentValue(parameter.matrix[selectedVersion][selectedZone]);
    } else {
      setCurrentValue('');
    }
  }, [parameter, selectedVersion, selectedZone]);

  // Handle value change
  const handleValueChange = (e) => {
    setCurrentValue(e.target.value);
  };

  // Handle save
  const handleSave = () => {
    // Parse numeric values
    let valueToSave = currentValue;
    if (parameter.type === 'number' && currentValue !== '') {
      valueToSave = parseFloat(currentValue);
      if (isNaN(valueToSave)) valueToSave = 0;
    }

    // Update parameter value
    updateParameterValue(paramId, valueToSave, selectedVersion, selectedZone);

    // Exit edit mode
    setEditing(false);
  };

  // Get inheritance info
  const getInheritanceInfo = () => {
    if (!parameter.inheritance[selectedVersion]) {
      return null;
    }

    const inheritance = parameter.inheritance[selectedVersion];
    if (!inheritance.source) {
      return null;
    }

    return {
      source: inheritance.source,
      sourceLabel: versions.metadata[inheritance.source]?.label || inheritance.source,
      percentage: inheritance.percentage
    };
  };

  const inheritanceInfo = getInheritanceInfo();

  return (
    <div className="matrix-editor">
      <div className="editor-header">
        <h3>Edit Matrix Values: {parameter.label}</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="editor-content">
        <div className="selector-group">
          <label>Version:</label>
          <select
            value={selectedVersion}
            onChange={e => setSelectedVersion(e.target.value)}
          >
            {versions.list.map(version => (
              <option key={version} value={version}>
                {versions.metadata[version]?.label || version}
              </option>
            ))}
          </select>
        </div>

        <div className="selector-group">
          <label>Zone:</label>
          <select
            value={selectedZone}
            onChange={e => setSelectedZone(e.target.value)}
          >
            {zones.list.map(zone => (
              <option key={zone} value={zone}>
                {zones.metadata[zone]?.label || zone}
              </option>
            ))}
          </select>
        </div>

        {inheritanceInfo && (
          <div className="inheritance-info">
            <span>Inherits {inheritanceInfo.percentage}% from {inheritanceInfo.sourceLabel}</span>
          </div>
        )}

        <div className="value-editor">
          {editing ? (
            <>
              <input
                type={parameter.type === 'number' ? 'number' : 'text'}
                value={currentValue}
                onChange={handleValueChange}
                className="value-input"
              />
              <div className="editor-actions">
                <button onClick={handleSave}>Save</button>
                <button onClick={() => setEditing(false)}>Cancel</button>
              </div>
            </>
          ) : (
            <>
              <div className="current-value">
                <span>Current Value: {currentValue}</span>
              </div>
              <button onClick={() => setEditing(true)}>Edit</button>
            </>
          )}
        </div>

        <div className="matrix-preview">
          <h4>Matrix Values Preview</h4>
          <table>
            <thead>
              <tr>
                <th>Zone / Version</th>
                {versions.list.map(version => (
                  <th key={version} className={version === selectedVersion ? 'selected' : ''}>
                    {versions.metadata[version]?.label || version}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {zones.list.map(zone => (
                <tr key={zone}>
                  <td className={zone === selectedZone ? 'selected' : ''}>
                    {zones.metadata[zone]?.label || zone}
                  </td>
                  {versions.list.map(version => (
                    <td
                      key={version}
                      className={version === selectedVersion && zone === selectedZone ? 'selected' : ''}
                      onClick={() => {
                        setSelectedVersion(version);
                        setSelectedZone(zone);
                      }}
                    >
                      {parameter.matrix[version]?.[zone]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/**
 * Efficacy Period Editor Component
 * Provides UI for editing efficacy periods
 */
export function EfficacyPeriodEditor({ paramId, formMatrix, updateEfficacyPeriod, onClose }) {
  const parameter = formMatrix[paramId];

  // Get plant lifetime for max end value
  const getPlantLifetime = () => {
    const versions = Object.keys(parameter.matrix)[0];
    const zones = Object.keys(parameter.matrix[versions] || {})[0];

    if (formMatrix['plantLifetimeAmount10']) {
      return formMatrix['plantLifetimeAmount10'].matrix[versions]?.[zones] || 20;
    }

    return 20; // Default
  };

  const plantLifetime = getPlantLifetime();
  const [startYear, setStartYear] = useState(parameter.efficacyPeriod?.start?.value || 0);
  const [endYear, setEndYear] = useState(parameter.efficacyPeriod?.end?.value || plantLifetime);

  // Handle save
  const handleSave = () => {
    // Validate values
    const validStart = Math.max(0, Math.min(startYear, endYear, plantLifetime));
    const validEnd = Math.max(validStart, Math.min(endYear, plantLifetime));

    // Update efficacy period
    updateEfficacyPeriod(paramId, validStart, validEnd);

    // Close editor
    onClose();
  };

  // Handle reset
  const handleReset = () => {
    setStartYear(0);
    setEndYear(plantLifetime);
  };

  return (
    <div className="efficacy-editor">
      <div className="editor-header">
        <h3>Edit Efficacy Period: {parameter.label}</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="editor-content">
        <div className="efficacy-range">
          <label>Start Year:</label>
          <input
            type="number"
            min="0"
            max={endYear}
            value={startYear}
            onChange={e => setStartYear(parseInt(e.target.value) || 0)}
          />
        </div>

        <div className="efficacy-range">
          <label>End Year:</label>
          <input
            type="number"
            min={startYear}
            max={plantLifetime}
            value={endYear}
            onChange={e => setEndYear(parseInt(e.target.value) || 0)}
          />
        </div>

        <div className="plant-lifetime">
          <span>Plant Lifetime: {plantLifetime} years</span>
        </div>

        <div className="efficacy-indicators">
          <div className="timeline">
            {Array.from({ length: plantLifetime + 1 }).map((_, i) => (
              <div
                key={i}
                className={`timeline-year ${i >= startYear && i <= endYear ? 'active' : ''}`}
                title={`Year ${i}`}
              >
                {i % 5 === 0 ? i : ''}
              </div>
            ))}
          </div>
        </div>

        <div className="editor-actions">
          <button onClick={handleSave}>Save</button>
          <button onClick={handleReset}>Reset to Full Lifetime</button>
          <button onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

/**
 * Matrix Configuration Exporter
 * Handles exporting matrix configuration to backends
 */
export class MatrixConfigExporter {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || 'http://localhost:3060';
    this.endpoints = {
      export: config.endpoints?.export || '/api/export-matrix-config',
      configMatrix: config.endpoints?.configMatrix || '/api/generate-config-matrix',
      paths: config.endpoints?.paths || '/api/export-paths'
    };
  }

  /**
   * Export matrix configuration to backend
   * @param {Object} matrixState - Complete matrix state
   * @returns {Promise<Object>} Export result
   */
  async exportConfiguration(matrixState) {
    try {
      const response = await fetch(`${this.baseUrl}${this.endpoints.export}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(matrixState)
      });

      if (!response.ok) {
        throw new Error(`Failed to export configuration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error exporting matrix configuration:', error);
      throw error;
    }
  }

  /**
   * Generate configuration matrix file
   * @param {string} version - Version ID (numeric part)
   * @param {Object} efficacyPeriods - Efficacy periods for parameters
   * @returns {Promise<Object>} Generation result
   */
  async generateConfigMatrix(version, efficacyPeriods) {
    try {
      // Extract numeric version ID
      const numericVersion = version.replace(/\D/g, '');

      const response = await fetch(`${this.baseUrl}${this.endpoints.configMatrix}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          version: numericVersion,
          efficacyPeriods
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to generate configuration matrix: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating configuration matrix:', error);
      throw error;
    }
  }

  /**
   * Export paths for calculation
   * @param {string} version - Version ID (numeric part)
   * @param {Object} state - State object with sensitivity parameters
   * @returns {Promise<Object>} Paths export result
   */
  async exportPaths(version, state) {
    try {
      // Extract numeric version ID
      const numericVersion = version.replace(/\D/g, '');

      const response = await fetch(`${this.baseUrl}${this.endpoints.paths}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          version: numericVersion,
          S: state.S,
          selectedV: state.V,
          selectedF: state.F,
          selectedR: state.R,
          selectedRF: state.RF
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to export paths: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error exporting paths:', error);
      throw error;
    }
  }
}

/**
 * Matrix History Manager
 * Handles tracking history of matrix state changes with undo/redo functionality
 */
export class MatrixHistoryManager {
  /**
   * Constructor
   * @param {Object} initialState - Initial matrix state
   */
  constructor(initialState) {
    this.history = [this.createSnapshot(initialState)];
    this.currentIndex = 0;
    this.maxHistorySize = 50; // Maximum number of history entries to keep
  }

  /**
   * Create a snapshot of the current state
   * @param {Object} state - Current state
   * @returns {Object} Snapshot object
   */
  createSnapshot(state) {
    return {
      id: `snapshot_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      timestamp: Date.now(),
      state: JSON.parse(JSON.stringify(state)) // Deep clone
    };
  }

  /**
   * Add a new history entry
   * @param {Object} state - Current state
   * @param {string} action - Action description
   * @returns {number} New history index
   */
  addEntry(state, action) {
    // Truncate history if not at the latest entry
    if (this.currentIndex < this.history.length - 1) {
      this.history = this.history.slice(0, this.currentIndex + 1);
    }

    // Create new snapshot
    const snapshot = this.createSnapshot(state);
    snapshot.action = action;

    // Add to history
    this.history.push(snapshot);
    this.currentIndex = this.history.length - 1;

    // Limit history size
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
      this.currentIndex--;
    }

    return this.currentIndex;
  }

  /**
   * Get current state snapshot
   * @returns {Object} Current state snapshot
   */
  getCurrentSnapshot() {
    return this.history[this.currentIndex];
  }

  /**
   * Undo last action
   * @returns {Object|null} Previous state or null if at beginning
   */
  undo() {
    if (this.currentIndex <= 0) {
      return null;
    }

    this.currentIndex--;
    return this.history[this.currentIndex];
  }

  /**
   * Redo previously undone action
   * @returns {Object|null} Next state or null if at end
   */
  redo() {
    if (this.currentIndex >= this.history.length - 1) {
      return null;
    }

    this.currentIndex++;
    return this.history[this.currentIndex];
  }

  /**
   * Check if undo is available
   * @returns {boolean} True if undo is available
   */
  canUndo() {
    return this.currentIndex > 0;
  }

  /**
   * Check if redo is available
   * @returns {boolean} True if redo is available
   */
  canRedo() {
    return this.currentIndex < this.history.length - 1;
  }

  /**
   * Get history entries
   * @returns {Array} History entries
   */
  getHistory() {
    return this.history.map((entry, index) => ({
      id: entry.id,
      timestamp: entry.timestamp,
      action: entry.action || `State change ${index + 1}`,
      isCurrent: index === this.currentIndex
    }));
  }

  /**
   * Export history
   * @returns {Object} Exportable history object
   */
  exportHistory() {
    return {
      history: this.history,
      currentIndex: this.currentIndex
    };
  }

  /**
   * Import history
   * @param {Object} historyData - History data to import
   * @returns {boolean} Success indicator
   */
  importHistory(historyData) {
    if (!historyData || !Array.isArray(historyData.history) || historyData.history.length === 0) {
      return false;
    }

    this.history = historyData.history;
    this.currentIndex = historyData.currentIndex || 0;

    // Ensure currentIndex is valid
    if (this.currentIndex >= this.history.length) {
      this.currentIndex = this.history.length - 1;
    }

    return true;
  }
}

/**
 * Matrix Inheritance Manager
 * Handles inheritance relationships between versions
 */
export class MatrixInheritanceManager {
  /**
   * Constructor
   * @param {Object} versions - Versions state object
   * @param {Object} formMatrix - Form matrix object
   */
  constructor(versions, formMatrix) {
    this.versions = versions;
    this.formMatrix = formMatrix;
    this.inheritanceGraph = this.buildInheritanceGraph();
  }

  /**
   * Build inheritance graph from matrix state
   * @returns {Object} Inheritance graph
   */
  buildInheritanceGraph() {
    const graph = {};

    // Initialize graph nodes
    this.versions.list.forEach(version => {
      graph[version] = {
        sources: [],
        targets: []
      };
    });

    // For each parameter, analyze inheritance relationships
    Object.values(this.formMatrix).forEach(param => {
      if (!param.inheritance) return;

      // For each version that inherits from another
      Object.entries(param.inheritance).forEach(([version, inheritance]) => {
        if (inheritance.source && inheritance.percentage < 100) {
          // Add source -> target relationship
          if (!graph[version].sources.includes(inheritance.source)) {
            graph[version].sources.push({
              version: inheritance.source,
              percentage: inheritance.percentage
            });
          }

          // Add target relationship to source
          if (!graph[inheritance.source].targets.includes(version)) {
            graph[inheritance.source].targets.push({
              version,
              percentage: inheritance.percentage
            });
          }
        }
      });
    });

    return graph;
  }

  /**
   * Get inheritance sources for a version
   * @param {string} version - Version ID
   * @returns {Array} Source versions with inheritance percentages
   */
  getInheritanceSources(version) {
    if (!this.inheritanceGraph[version]) return [];
    return this.inheritanceGraph[version].sources;
  }

  /**
   * Get inheritance targets for a version
   * @param {string} version - Version ID
   * @returns {Array} Target versions with inheritance percentages
   */
  getInheritanceTargets(version) {
    if (!this.inheritanceGraph[version]) return [];
    return this.inheritanceGraph[version].targets;
  }

  /**
   * Configure inheritance relationship
   * @param {string} paramId - Parameter ID
   * @param {string} version - Target version ID
   * @param {string} sourceVersion - Source version ID
   * @param {number} percentage - Inheritance percentage (0-100)
   * @returns {Object} Updated form matrix
   */
  configureInheritance(paramId, version, sourceVersion, percentage) {
    // Skip if parameter doesn't exist
    if (!this.formMatrix[paramId]) return this.formMatrix;

    // Create a copy of form matrix
    const newFormMatrix = { ...this.formMatrix };
    const param = { ...newFormMatrix[paramId] };

    // Update inheritance configuration
    if (!param.inheritance) {
      param.inheritance = {};
    }

    param.inheritance[version] = {
      source: sourceVersion,
      percentage: Math.min(100, Math.max(0, percentage))
    };

    // Update parameter in form matrix
    newFormMatrix[paramId] = param;

    // Update inheritance graph
    this.formMatrix = newFormMatrix;
    this.inheritanceGraph = this.buildInheritanceGraph();

    return newFormMatrix;
  }

  /**
   * Apply inheritance to parameter values
   * @param {Object} updates - Parameter updates
   * @returns {Object} Complete updates with inheritance applied
   */
  applyInheritance(updates) {
    const result = { ...updates };

    // For each parameter that was updated
    Object.keys(updates).forEach(paramId => {
      if (!this.formMatrix[paramId]?.inheritance) return;

      const paramUpdate = updates[paramId];
      const param = this.formMatrix[paramId];

      // For each affected version and zone
      Object.keys(paramUpdate).forEach(version => {
        Object.keys(paramUpdate[version]).forEach(zone => {
          const sourceValue = paramUpdate[version][zone];

          // Find all versions that inherit from this version
          this.getInheritanceTargets(version).forEach(target => {
            const { version: targetVersion, percentage } = target;

            // Skip if target version not initialized
            if (!param.matrix[targetVersion] || !param.matrix[targetVersion][zone]) return;

            const currentValue = param.matrix[targetVersion][zone];
            const inheritPercent = percentage / 100;

            // Calculate inherited value
            const newValue = typeof currentValue === 'number' && typeof sourceValue === 'number'
              ? (currentValue * (1 - inheritPercent)) + (sourceValue * inheritPercent)
              : sourceValue;

            // Add to result
            if (!result[paramId]) result[paramId] = {};
            if (!result[paramId][targetVersion]) result[paramId][targetVersion] = {};

            result[paramId][targetVersion][zone] = newValue;
          });
        });
      });
    });

    return result;
  }
}

/**
 * Matrix Validation Module
 * Provides validation functions for matrix-based form values
 */
export class MatrixValidator {
  /**
   * Constructor
   * @param {Object} validationRules - Validation rules configuration
   */
  constructor(validationRules = {}) {
    this.rules = validationRules;
    this.errors = {};
  }

  /**
   * Set validation rules
   * @param {Object} rules - Validation rules configuration
   */
  setRules(rules) {
    this.rules = rules;
  }

  /**
   * Validate parameter value
   * @param {string} paramId - Parameter ID
   * @param {any} value - Parameter value
   * @returns {boolean} True if valid
   */
  validateParameter(paramId, value) {
    // Skip if no rules for this parameter
    if (!this.rules[paramId]) return true;

    const rules = this.rules[paramId];
    let isValid = true;
    const errors = [];

    // Required rule
    if (rules.required && (value === undefined || value === null || value === '')) {
      errors.push('This field is required');
      isValid = false;
    }

    // Type rule
    if (rules.type) {
      switch (rules.type) {
        case 'number':
          if (typeof value !== 'number' && !(typeof value === 'string' && !isNaN(parseFloat(value)))) {
            errors.push('Must be a number');
            isValid = false;
          }
          break;
        case 'integer':
          if (typeof value !== 'number' || Math.floor(value) !== value) {
            errors.push('Must be an integer');
            isValid = false;
          }
          break;
        case 'string':
          if (typeof value !== 'string') {
            errors.push('Must be a string');
            isValid = false;
          }
          break;
        case 'boolean':
          if (typeof value !== 'boolean') {
            errors.push('Must be a boolean');
            isValid = false;
          }
          break;
        default:
          break;
      }
    }

    // Min/max rules for numbers
    if ((rules.type === 'number' || rules.type === 'integer') && typeof value === 'number') {
      if (rules.min !== undefined && value < rules.min) {
        errors.push(`Must be at least ${rules.min}`);
        isValid = false;
      }

      if (rules.max !== undefined && value > rules.max) {
        errors.push(`Must be at most ${rules.max}`);
        isValid = false;
      }
    }

    // Min/max length rules for strings
    if (rules.type === 'string' && typeof value === 'string') {
      if (rules.minLength !== undefined && value.length < rules.minLength) {
        errors.push(`Must be at least ${rules.minLength} characters`);
        isValid = false;
      }

      if (rules.maxLength !== undefined && value.length > rules.maxLength) {
        errors.push(`Must be at most ${rules.maxLength} characters`);
        isValid = false;
      }
    }

    // Pattern rule for strings
    if (rules.type === 'string' && rules.pattern && typeof value === 'string') {
      const regex = new RegExp(rules.pattern);
      if (!regex.test(value)) {
        errors.push(rules.patternMessage || 'Invalid format');
        isValid = false;
      }
    }

    // Custom validation function
    if (rules.validate && typeof rules.validate === 'function') {
      const customResult = rules.validate(value);
      if (customResult !== true) {
        errors.push(customResult || 'Invalid value');
        isValid = false;
      }
    }

    // Store errors
    this.errors[paramId] = errors;

    return isValid;
  }

  /**
   * Validate multiple parameters
   * @param {Object} formMatrix - Form matrix object
   * @param {string} version - Version ID
   * @param {string} zone - Zone ID
   * @returns {boolean} True if all parameters are valid
   */
  validateMatrix(formMatrix, version, zone) {
    let isValid = true;
    this.errors = {};

    // Validate each parameter
    Object.keys(formMatrix).forEach(paramId => {
      const param = formMatrix[paramId];
      const value = param.matrix[version]?.[zone];

      if (!this.validateParameter(paramId, value)) {
        isValid = false;
      }
    });

    return isValid;
  }

  /**
   * Get validation errors
   * @param {string} paramId - Optional parameter ID to get errors for
   * @returns {Object|Array} Validation errors
   */
  getErrors(paramId) {
    if (paramId) {
      return this.errors[paramId] || [];
    }

    return this.errors;
  }

  /**
   * Check if parameter has errors
   * @param {string} paramId - Parameter ID
   * @returns {boolean} True if parameter has errors
   */
  hasErrors(paramId) {
    return Array.isArray(this.errors[paramId]) && this.errors[paramId].length > 0;
  }
}

/**
 * Matrix Form Summary Generator
 * Creates summary data from matrix form values
 */
export class MatrixSummaryGenerator {
  /**
   * Constructor
   * @param {Object} formMatrix - Form matrix object
   * @param {Object} versions - Versions state object
   * @param {Object} zones - Zones state object
   */
  constructor(formMatrix, versions, zones) {
    this.formMatrix = formMatrix;
    this.versions = versions;
    this.zones = zones;
  }

  /**
   * Generate summary for specific parameter categories
   * @param {string} category - Parameter category (e.g., 'Amount4')
   * @param {Object} scaling - Scaling results for parameters
   * @returns {Array} Summary items
   */
  generateCategorySummary(category, scaling = {}) {
    const summaryItems = [];

    // Get active version and zone
    const activeVersion = this.versions?.active || 'v1';
    const activeZone = this.zones?.active || 'z1';

    // Filter parameters by category
    const categoryParams = Object.entries(this.formMatrix)
      .filter(([paramId]) => paramId.includes(category))
      .map(([paramId, param]) => ({
        id: paramId,
        label: param.label,
        value: param.matrix?.[activeVersion]?.[activeZone],
        vKey: param.dynamicAppendix?.itemState?.vKey,
        rKey: param.dynamicAppendix?.itemState?.rKey,
        fKey: param.dynamicAppendix?.itemState?.fKey,
        rfKey: param.dynamicAppendix?.itemState?.rfKey,
        sKey: param.dynamicAppendix?.itemState?.sKey,
        efficacyPeriod: param.efficacyPeriod
      }));

    // Process each parameter
    categoryParams.forEach(param => {
      // Get base value (current matrix value)
      const baseValue = param.value || 0;

      // Get scaled value from scaling results if available
      const scaledValue = scaling[param.id]?.scaledValue || baseValue;

      // Calculate percentage change
      const percentChange = baseValue !== 0
        ? ((scaledValue - baseValue) / Math.abs(baseValue)) * 100
        : 0;

      // Add to summary items
      summaryItems.push({
        id: param.id,
        label: param.label,
        originalValue: baseValue,
        scaledValue: scaledValue,
        finalResult: scaledValue, // Default to scaled value
        percentChange,
        absImpact: Math.abs(scaledValue - baseValue),
        vKey: param.vKey,
        rKey: param.rKey,
        fKey: param.fKey,
        rfKey: param.rfKey,
        efficacyPeriod: param.efficacyPeriod
      });
    });

    // Sort by absolute impact
    summaryItems.sort((a, b) => b.absImpact - a.absImpact);

    return summaryItems;
  }

  /**
   * Generate complete summary for all categories
   * @param {Object} scaling - Scaling results for all categories
   * @returns {Object} Complete summary
   */
  generateCompleteSummary(scaling = {}) {
    const categories = ['Amount1', 'Amount2', 'Amount3', 'Amount4', 'Amount5', 'Amount6', 'Amount7'];
    const summary = {};

    categories.forEach(category => {
      summary[category] = this.generateCategorySummary(category, scaling[category] || {});
    });

    return summary;
  }

  /**
   * Generate statistics from summary items
   * @param {Array} summaryItems - Summary items
   * @returns {Object} Statistics
   */
  generateStats(summaryItems) {
    const activeItems = summaryItems.filter(item => item.isActive !== false);

    // Skip if no active items
    if (activeItems.length === 0) {
      return {
        totalCount: summaryItems.length,
        activeCount: 0,
        totalChange: 0,
        averageChange: 0,
        totalPercentChange: 0,
        averagePercentChange: 0,
        maxImpactItem: null
      };
    }

    // Calculate total change
    const totalChange = activeItems.reduce((sum, item) => sum + (item.scaledValue - item.originalValue), 0);

    // Calculate average change
    const averageChange = totalChange / activeItems.length;

    // Calculate total percent change
    const totalPercentChange = activeItems.reduce((sum, item) => sum + item.percentChange, 0);

    // Calculate average percent change
    const averagePercentChange = totalPercentChange / activeItems.length;

    // Find item with maximum impact
    const maxImpactItem = [...activeItems].sort((a, b) => b.absImpact - a.absImpact)[0];

    return {
      totalCount: summaryItems.length,
      activeCount: activeItems.length,
      totalChange,
      averageChange,
      totalPercentChange,
      averagePercentChange,
      maxImpactItem
    };
  }
}

/**
 * Sensitivity Configuration Generator
 * Creates sensitivity configurations from matrix form values
 */
export class SensitivityConfigGenerator {
  /**
   * Constructor
   * @param {Object} S - Sensitivity parameters state
   * @param {Object} formMatrix - Form matrix object
   */
  constructor(S, formMatrix) {
    this.S = S;
    this.formMatrix = formMatrix;
  }

  /**
   * Generate sensitivity variations for parameter
   * @param {string} paramId - Parameter ID
   * @param {string} sKey - S parameter key
   * @returns {Array} Sensitivity variations
   */
  generateVariations(paramId, sKey) {
    // Skip if S parameter not enabled
    if (!this.S[sKey] || this.S[sKey].status === 'off') {
      return [];
    }

    // Get parameter from form matrix
    const param = this.formMatrix[paramId];
    if (!param) return [];

    // Get sensitivity configuration
    const senConfig = this.S[sKey];
    const mode = senConfig.mode || 'percentage';
    const baseValue = param.matrix[param.versions.active]?.[param.zones.active] || 0;

    // Generate variations based on mode
    const variations = [];

    switch (mode) {
      case 'percentage':
        // Percentage variations
        const percents = senConfig.values || [-20, -10, 10, 20];

        percents.forEach(percent => {
          const value = baseValue * (1 + percent / 100);
          variations.push({
            mode: 'percentage',
            percent,
            value,
            label: `${percent > 0 ? '+' : ''}${percent}%`
          });
        });
        break;

      case 'directvalue':
        // Direct value variations
        const values = senConfig.values || [baseValue * 0.8, baseValue * 0.9, baseValue * 1.1, baseValue * 1.2];

        values.forEach(value => {
          const percent = baseValue !== 0 ? ((value / baseValue) - 1) * 100 : 0;
          variations.push({
            mode: 'directvalue',
            percent,
            value,
            label: value.toFixed(2)
          });
        });
        break;

      case 'absolutedeparture':
        // Absolute departure variations
        const departures = senConfig.values || [-20, -10, 10, 20];

        departures.forEach(departure => {
          const value = baseValue + departure;
          const percent = baseValue !== 0 ? (departure / baseValue) * 100 : 0;
          variations.push({
            mode: 'absolutedeparture',
            percent,
            value,
            label: `${departure > 0 ? '+' : ''}${departure}`
          });
        });
        break;

      case 'montecarlo':
        // Monte Carlo variations
        const count = senConfig.count || 5;
        const range = senConfig.range || 20;

        for (let i = 0; i < count; i++) {
          // Generate random variation between -range% and +range%
          const percent = (Math.random() * 2 - 1) * range;
          const value = baseValue * (1 + percent / 100);

          variations.push({
            mode: 'montecarlo',
            percent,
            value,
            label: `MC-${i+1}: ${percent.toFixed(1)}%`
          });
        }
        break;

      default:
        break;
    }

    return variations;
  }

  /**
   * Generate complete sensitivity configuration
   * @returns {Object} Sensitivity configuration
   */
  generateConfiguration() {
    const configuration = {};

    // Process each S parameter
    Object.entries(this.S).forEach(([sKey, config]) => {
      // Skip if not enabled
      if (config.status === 'off') return;

      // Find corresponding parameter ID
      const paramId = Object.keys(this.formMatrix).find(id => {
        return this.formMatrix[id].dynamicAppendix?.itemState?.sKey === sKey;
      });

      if (!paramId) return;

      // Generate variations
      const variations = this.generateVariations(paramId, sKey);

      // Add to configuration
      configuration[sKey] = {
        paramId,
        label: this.formMatrix[paramId]?.label || sKey,
        mode: config.mode || 'percentage',
        baseValue: this.formMatrix[paramId]?.matrix[this.formMatrix[paramId]?.versions.active]?.[this.formMatrix[paramId]?.zones.active] || 0,
        variations
      };
    });

    return configuration;
  }

  /**
   * Generate paths for sensitivity configuration
   * @param {string} version - Version ID (numeric part)
   * @returns {Object} Sensitivity paths
   */
  generatePaths(version) {
    // Extract numeric version
    const numericVersion = version.replace(/\D/g, '');

    const paths = {
      version: numericVersion,
      parameters: {}
    };

    // Generate configuration
    const configuration = this.generateConfiguration();

    // Build paths for each parameter
    Object.entries(configuration).forEach(([sKey, config]) => {
      const paramPaths = {
        paramId: config.paramId,
        label: config.label,
        mode: config.mode,
        baseValue: config.baseValue,
        variations: {}
      };

      // Build paths for each variation
      config.variations.forEach(variation => {
        const varKey = variation.label.replace(/[^\w-]/g, '_');

        paramPaths.variations[varKey] = {
          label: variation.label,
          percent: variation.percent,
          value: variation.value,
          paths: {
            param: `Batch(${numericVersion})/Results(${numericVersion})/Sensitivity/${sKey}/${config.mode}/${varKey}`,
            config: `Batch(${numericVersion})/ConfigurationPlotSpec(${numericVersion})/configurations(${numericVersion}).py`
          }
        };
      });

      paths.parameters[sKey] = paramPaths;
    });

    return paths;
  }
}

/**
 * Matrix Form Value Sync Service
 * Handles synchronization of matrix form values with external systems
 */
export class MatrixSyncService {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || 'http://localhost:3060';
    this.endpoints = {
      sync: config.endpoints?.sync || '/api/sync-matrix',
      load: config.endpoints?.load || '/api/load-matrix',
      updateLabels: config.endpoints?.updateLabels || '/api/update-form-labels',
      submitValues: config.endpoints?.submitValues || '/api/submit-values'
    };
  }

  /**
   * Synchronize matrix state with backend
   * @param {Object} state - Complete matrix state
   * @returns {Promise<Object>} Synchronization result
   */
  async synchronize(state) {
    try {
      const response = await fetch(`${this.baseUrl}${this.endpoints.sync}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(state)
      });

      if (!response.ok) {
        throw new Error(`Failed to synchronize state: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error synchronizing matrix state:', error);
      throw error;
    }
  }

  /**
   * Load matrix state from backend
   * @returns {Promise<Object>} Loaded state
   */
  async load() {
    try {
      const response = await fetch(`${this.baseUrl}${this.endpoints.load}`, {
        method: 'GET'
      });

      if (!response.ok) {
        throw new Error(`Failed to load state: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error loading matrix state:', error);
      throw error;
    }
  }

  /**
   * Update form labels
   * @param {Object} updatedLabels - Map of parameter IDs to updated labels
   * @returns {Promise<Object>} Update result
   */
  async updateLabels(updatedLabels) {
    try {
      const response = await fetch(`${this.baseUrl}${this.endpoints.updateLabels}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ labels: updatedLabels })
      });

      if (!response.ok) {
        throw new Error(`Failed to update labels: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating form labels:', error);
      throw error;
    }
  }

  /**
   * Submit form values to backend
   * @param {Object} values - Form values to submit
   * @param {string} version - Version ID (numeric part)
   * @returns {Promise<Object>} Submission result
   */
  async submitValues(values, version) {
    try {
      // Extract numeric version
      const numericVersion = version.replace(/\D/g, '');

      const response = await fetch(`${this.baseUrl}${this.endpoints.submitValues}/${numericVersion}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });

      if (!response.ok) {
        throw new Error(`Failed to submit values: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting form values:', error);
      throw error;
    }
  }

  /**
   * Submit filtered values to backend
   * @param {Object} filteredValues - Filtered values object
   * @param {string} version - Version ID (numeric part)
   * @returns {Promise<Object>} Submission result
   */
  async submitFilteredValues(filteredValues, version) {
    try {
      // Extract numeric version
      const numericVersion = version.replace(/\D/g, '');

      const response = await fetch(`${this.baseUrl}/append/${numericVersion}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain'
        },
        body: JSON.stringify(filteredValues, null, 2)
      });

      if (!response.ok) {
        throw new Error(`Failed to submit filtered values: ${response.statusText}`);
      }

      return await response.text();
    } catch (error) {
      console.error('Error submitting filtered values:', error);
      throw error;
    }
  }
}

/**
 * Matrix Enhanced Scaling Manager
 * Provides advanced scaling capabilities with matrix integration
 */
export class MatrixScalingManager {
  /**
   * Constructor
   * @param {Object} formMatrix - Form matrix object
   * @param {Object} versions - Versions state object
   * @param {Object} zones - Zones state object
   */
  constructor(formMatrix, versions, zones) {
    this.formMatrix = formMatrix;
    this.versions = versions;
    this.zones = zones;
    this.scalingGroups = [];
    this.operations = [
      { id: 'multiply', label: 'Multiply', symbol: '×' },
      { id: 'add', label: 'Add', symbol: '+' },
      { id: 'subtract', label: 'Subtract', symbol: '−' },
      { id: 'divide', label: 'Divide', symbol: '÷' },
      { id: 'power', label: 'Power', symbol: '^' },
      { id: 'log', label: 'Logarithmic', symbol: 'ln' },
      { id: 'exponential', label: 'Exponential', symbol: 'eˣ' }
    ];
  }

  /**
   * Set scaling groups
   * @param {Array} scalingGroups - Scaling groups
   */
  setScalingGroups(scalingGroups) {
    this.scalingGroups = scalingGroups;
  }

  /**
   * Get scaling base costs for a category
   * @param {string} category - Parameter category (e.g., 'Amount4')
   * @returns {Array} Base costs for scaling
   */
  getScalingBaseCosts(category) {
    const activeVersion = this.versions?.active || 'v1';
    const activeZone = this.zones?.active || 'z1';

    // Filter parameters by category
    const baseCosts = Object.entries(this.formMatrix)
      .filter(([paramId]) => paramId.includes(category))
      .map(([paramId, param]) => {
        // Get current value from matrix
        const paramValue = param.matrix?.[activeVersion]?.[activeZone] || 0;

        return {
          id: paramId,
          label: param.label || `Unnamed ${category}`,
          value: parseFloat(paramValue) || 0,
          baseValue: parseFloat(paramValue) || 0,
          vKey: param.dynamicAppendix?.itemState?.vKey || null,
          rKey: param.dynamicAppendix?.itemState?.rKey || null
        };
      });

    return baseCosts;
  }

  /**
   * Add a new scaling group
   * @param {string} category - Parameter category (e.g., 'Amount4')
   * @returns {Object} Created scaling group
   */
  addScalingGroup(category) {
    // Get base costs for this category
    const baseCosts = this.getScalingBaseCosts(category);

    // Look for gaps in the existing group sequence based on naming conventions
    const existingNumbers = this.scalingGroups
      .filter(group => group._scalingType === category)
      .map(group => {
        const match = group.name.match(/Scaling Group (\d+)/);
        return match ? parseInt(match[1], 10) : null;
      })
      .filter(Boolean)
      .sort((a, b) => a - b);

    // Find the first available gap in the sequence
    let newGroupNumber = 1;
    for (let i = 0; i < existingNumbers.length; i++) {
      if (existingNumbers[i] !== i + 1) {
        newGroupNumber = i + 1;
        break;
      }
      newGroupNumber = i + 2; // If no gap found, use the next number
    }

    // Create new scaling group
    const newGroup = {
      id: `group-${Date.now()}`,
      name: `Scaling Group ${newGroupNumber}`,
      isProtected: false,
      _scalingType: category,
      items: baseCosts.map(cost => ({
        ...cost,
        originalBaseValue: cost.baseValue,
        scalingFactor: 1,
        operation: 'multiply',
        enabled: true,
        notes: '',
        scaledValue: cost.baseValue
      }))
    };

    // Add to scaling groups
    this.scalingGroups.push(newGroup);

    return newGroup;
  }

  /**
   * Remove a scaling group
   * @param {string} groupId - Group ID
   * @returns {boolean} Success indicator
   */
  removeScalingGroup(groupId) {
    // Find group index
    const groupIndex = this.scalingGroups.findIndex(group => group.id === groupId);
    if (groupIndex === -1) return false;

    // Check if group is protected
    if (this.scalingGroups[groupIndex].isProtected) return false;

    // Remove group
    this.scalingGroups.splice(groupIndex, 1);

    return true;
  }

  /**
   * Update scaling group
   * @param {Object} updatedGroup - Updated scaling group
   * @returns {boolean} Success indicator
   */
  updateScalingGroup(updatedGroup) {
    // Find group index
    const groupIndex = this.scalingGroups.findIndex(group => group.id === updatedGroup.id);
    if (groupIndex === -1) return false;

    // Update group
    this.scalingGroups[groupIndex] = updatedGroup;

    return true;
  }

  /**
   * Calculate scaled value based on operation
   * @param {number} baseValue - Base value
   * @param {string} operation - Operation type
   * @param {number} factor - Scaling factor
   * @returns {number} Scaled value
   */
  calculateScaledValue(baseValue, operation, factor) {
    try {
      if (baseValue === 0 && operation === 'divide') {
        return 0; // Avoid division by zero
      }

      if (baseValue < 0 && operation === 'log') {
        return baseValue; // Avoid logarithm of negative number
      }

      switch (operation) {
        case 'multiply':
          return baseValue * factor;
        case 'add':
          return baseValue + factor;
        case 'subtract':
          return baseValue - factor;
        case 'divide':
          return factor !== 0 ? baseValue / factor : baseValue;
        case 'power':
          return Math.pow(baseValue, factor);
        case 'log':
          return baseValue > 0 ? Math.log(baseValue) * factor : baseValue;
        case 'exponential':
          return baseValue > 0 ? Math.exp(Math.log(baseValue) * factor) : baseValue;
        default:
          return baseValue;
      }
    } catch (error) {
      console.error('Error calculating scaled value:', error);
      return baseValue;
    }
  }

  /**
   * Propagate changes through the scaling chain
   * @param {number} startGroupIndex - Index of the group where changes started
   * @returns {Array} Updated scaling groups
   */
  propagateChanges(startGroupIndex) {
    // Skip if invalid index
    if (startGroupIndex < 0 || startGroupIndex >= this.scalingGroups.length - 1) {
      return this.scalingGroups;
    }

    // Clone scaling groups to avoid mutations
    const updatedGroups = JSON.parse(JSON.stringify(this.scalingGroups));

    // For each subsequent group, update base values from the previous group's results
    for (let i = startGroupIndex + 1; i < updatedGroups.length; i++) {
      const previousGroup = updatedGroups[i - 1];

      // Skip if groups have different types
      if (previousGroup._scalingType !== updatedGroups[i]._scalingType) continue;

      // Create a map of previous results
      const previousResults = {};
      previousGroup.items.forEach(item => {
        previousResults[item.id] = {
          scaledValue: item.enabled ? item.scaledValue : item.baseValue,
          enabled: item.enabled
        };
      });

      // Update each item in the current group
      updatedGroups[i].items = updatedGroups[i].items.map(item => {
        const prevResult = previousResults[item.id];
        if (!prevResult) return item;

        // Calculate new scaled value based on updated base value
        const newBaseValue = prevResult.scaledValue;
        const newScaledValue = this.calculateScaledValue(
          newBaseValue,
          item.operation,
          item.scalingFactor
        );

        return {
          ...item,
          originalBaseValue: item.originalBaseValue || item.baseValue, // Preserve original
          baseValue: newBaseValue,
          scaledValue: item.enabled ? newScaledValue : newBaseValue
        };
      });
    }

    // Update local state
    this.scalingGroups = updatedGroups;

    return updatedGroups;
  }

  /**
   * Calculate results from all scaling groups
   * @returns {Object} Results for each category
   */
  calculateResults() {
    const results = {};

    // Group scaling groups by category
    const groupsByCategory = {};
    this.scalingGroups.forEach(group => {
      const category = group._scalingType;
      if (!groupsByCategory[category]) {
        groupsByCategory[category] = [];
      }
      groupsByCategory[category].push(group);
    });

    // For each category, calculate final results
    Object.entries(groupsByCategory).forEach(([category, groups]) => {
      const categoryResults = {};

      // For each parameter ID, find the last scaled value
      groups.forEach(group => {
        group.items.forEach(item => {
          // Update parameter in results
          categoryResults[item.id] = {
            id: item.id,
            label: item.label,
            originalBaseValue: item.originalBaseValue,
            baseValue: item.baseValue,
            scaledValue: item.enabled ? item.scaledValue : item.baseValue,
            isActive: item.enabled
          };
        });
      });

      results[category] = categoryResults;
    });

    return results;
  }
}

/**
 * Matrix API Service
 * Provides API endpoints for matrix-based functionality
 */
export class MatrixAPIService {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    this.port = config.port || 3060;
    this.app = null;
    this.server = null;
    this.matrixState = {};
    this.routes = [
      { path: '/api/sync-matrix', method: 'POST', handler: this.handleSyncMatrix.bind(this) },
      { path: '/api/load-matrix', method: 'GET', handler: this.handleLoadMatrix.bind(this) },
      { path: '/api/update-form-labels', method: 'POST', handler: this.handleUpdateFormLabels.bind(this) },
      { path: '/api/submit-values/:version', method: 'POST', handler: this.handleSubmitValues.bind(this) },
      { path: '/api/export-matrix-config', method: 'POST', handler: this.handleExportConfig.bind(this) },
      { path: '/api/generate-config-matrix', method: 'POST', handler: this.handleGenerateConfigMatrix.bind(this) },
      { path: '/api/export-paths', method: 'POST', handler: this.handleExportPaths.bind(this) },
      { path: '/health', method: 'GET', handler: this.handleHealth.bind(this) }
    ];
  }

  /**
   * Initialize API service
   * @returns {Object} API service instance
   */
  async initialize() {
    try {
      // Setup Express app
      const express = await import('express');
      const cors = await import('cors');

      this.app = express.default();
      this.app.use(cors.default());
      this.app.use(express.default.json({ limit: '50mb' }));

      // Register routes
      this.registerRoutes();

      // Start server
      this.server = this.app.listen(this.port, () => {
        console.log(`Matrix API service running on port ${this.port}`);
      });

      return this;
    } catch (error) {
      console.error('Error initializing Matrix API service:', error);
      throw error;
    }
  }

  /**
   * Register API routes
   */
  registerRoutes() {
    if (!this.app) return;

    this.routes.forEach(route => {
      switch (route.method) {
        case 'GET':
          this.app.get(route.path, route.handler);
          break;
        case 'POST':
          this.app.post(route.path, route.handler);
          break;
        case 'PUT':
          this.app.put(route.path, route.handler);
          break;
        case 'DELETE':
          this.app.delete(route.path, route.handler);
          break;
        default:
          console.warn(`Unsupported method: ${route.method} for path: ${route.path}`);
      }
    });
  }

  /**
   * Stop API service
   * @returns {Promise<void>}
   */
  async stop() {
    if (this.server) {
      return new Promise((resolve, reject) => {
        this.server.close(err => {
          if (err) {
            reject(err);
          } else {
            console.log('Matrix API service stopped');
            resolve();
          }
        });
      });
    }
  }

  /**
   * Handle matrix state synchronization
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleSyncMatrix(req, res) {
    try {
      // Update matrix state
      this.matrixState = req.body;

      res.json({
        success: true,
        message: 'Matrix state synchronized successfully',
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Error handling sync matrix:', error);
      res.status(500).json({
        success: false,
        message: 'Error synchronizing matrix state',
        error: error.message
      });
    }
  }

  /**
   * Handle loading matrix state
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleLoadMatrix(req, res) {
    try {
      res.json({
        success: true,
        message: 'Matrix state loaded successfully',
        state: this.matrixState,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Error handling load matrix:', error);
      res.status(500).json({
        success: false,
        message: 'Error loading matrix state',
        error: error.message
      });
    }
  }

  /**
   * Handle updating form labels
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleUpdateFormLabels(req, res) {
    try {
      const { labels } = req.body;

      // Update labels in matrix state
      if (this.matrixState.formMatrix) {
        Object.entries(labels).forEach(([paramId, label]) => {
          if (this.matrixState.formMatrix[paramId]) {
            this.matrixState.formMatrix[paramId].label = label;
          }
        });
      }

      res.json({
        success: true,
        message: `Updated ${Object.keys(labels).length} labels successfully`,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Error handling update form labels:', error);
      res.status(500).json({
        success: false,
        message: 'Error updating form labels',
        error: error.message
      });
    }
  }

  /**
   * Handle submitting form values
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleSubmitValues(req, res) {
    try {
      const { version } = req.params;
      const values = req.body;

      // Process submitted values
      // This would typically involve saving to files or database

      res.json({
        success: true,
        message: `Submitted values for version ${version} successfully`,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Error handling submit values:', error);
      res.status(500).json({
        success: false,
        message: 'Error submitting values',
        error: error.message
      });
    }
  }

  /**
   * Handle exporting matrix configuration
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleExportConfig(req, res) {
    try {
      const config = req.body;

      // Process configuration
      // This would typically involve generating configuration files

      res.json({
        success: true,
        message: 'Matrix configuration exported successfully',
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Error handling export config:', error);
      res.status(500).json({
        success: false,
        message: 'Error exporting matrix configuration',
        error: error.message
      });
    }
  }

  /**
   * Handle generating configuration matrix
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleGenerateConfigMatrix(req, res) {
    try {
      const { version, efficacyPeriods } = req.body;

      // Generate configuration matrix
      // This would typically involve creating a matrix file

      res.json({
        success: true,
        message: `Generated configuration matrix for version ${version} successfully`,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Error handling generate config matrix:', error);
      res.status(500).json({
        success: false,
        message: 'Error generating configuration matrix',
        error: error.message
      });
    }
  }

  /**
   * Handle exporting paths
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleExportPaths(req, res) {
    try {
      const { version, S, selectedV, selectedF, selectedR, selectedRF } = req.body;

      // Generate paths
      // This would typically involve creating path structures for calculations

      res.json({
        success: true,
        message: `Exported paths for version ${version} successfully`,
        timestamp: Date.now(),
        paths: {
          version,
          selectedV,
          selectedF,
          selectedR,
          selectedRF,
          S
        }
      });
    } catch (error) {
      console.error('Error handling export paths:', error);
      res.status(500).json({
        success: false,
        message: 'Error exporting paths',
        error: error.message
      });
    }
  }

  /**
   * Handle health check
   * @param {Object} req - Request object
   * @param {Object} res - Response object
   */
  handleHealth(req, res) {
    res.json({
      status: 'healthy',
      service: 'Matrix API Service',
      timestamp: Date.now(),
      versions: this.matrixState.versions?.list?.length || 0,
      zones: this.matrixState.zones?.list?.length || 0,
      parameters: Object.keys(this.matrixState.formMatrix || {}).length || 0
    });
  }
}
