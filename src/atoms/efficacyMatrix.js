/**
 * efficacyMatrix.js
 *
 * Jotai atom for efficacy-aware scaling groups.
 *
 * Item shape mirrors what SimpleScalingEditor.reconcileGroups produces
 * (src/components/scaling/SimpleScalingEditor.js lines 77-89) plus the
 * fields EfficacyManager.applyEfficacyToScalingGroups appends
 * (src/Consolidated2.js lines 1504-1515):
 *
 *   id, label, vKey, rKey,
 *   originalBaseValue, baseValue, scalingFactor, operation, enabled, notes,
 *   scaledValue,
 *   -- after applyEfficacyToScalingGroups --
 *   isActive, effectiveValue, efficacyPeriod: { start, end, isCustomized }
 *
 * Parameter IDs and default values come from src/utils/labelReferences.js.
 * Plant lifetime default is 20 (plantLifetimeAmount10).
 *
 * This atom starts with the real parameter set so the tooltip has meaningful
 * defaults before the app loads backend data.  SimpleScalingEditor / any
 * component calling applyEfficacyToScalingGroups should overwrite this atom
 * with live data.
 */

import { atom } from 'jotai';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const makeItem = (id, label, baseValue, vKey = null, rKey = null) => ({
  id,
  label,
  vKey,
  rKey,
  originalBaseValue: baseValue,
  baseValue,
  scalingFactor: 1,
  operation: 'multiply',
  enabled: true,
  notes: '',
  scaledValue: baseValue,
  isActive: true,
  effectiveValue: baseValue,
  efficacyPeriod: { start: 0, end: 20, isCustomized: false },
});

const makeGroup = (id, name, scalingType, items) => ({
  id,
  name,
  _scalingType: scalingType,
  items,
});

// ---------------------------------------------------------------------------
// Default groups — real parameter IDs from propertyMapping / defaultValues
// ---------------------------------------------------------------------------
const defaultGroups = [
  makeGroup('Amount10-group-1', 'Scaling Group 1 — Configuration', 'Amount1', [
    makeItem('plantLifetimeAmount10',                                 'Plant Lifetime',                   20),
    makeItem('bECAmount11',                                          'Bare Erected Cost',                200000),
    makeItem('numberOfUnitsAmount12',                                'Number of Units',                  30000),
    makeItem('initialSellingPriceAmount13',                          'Price',                            2),
    makeItem('totalOperatingCostPercentageAmount14',                 'Direct Total Operating Cost %',    0.1),
    makeItem('engineering_Procurement_and_Construction_EPC_Amount15','EPC as % of BEC',                  0),
    makeItem('process_contingency_PC_Amount16',                      'Process Contingency % of BEC',     0),
    makeItem('project_Contingency_PT_BEC_EPC_PCAmount17',            'Project Contingency %',            0),
    makeItem('numberofconstructionYearsAmount28',                    'Construction Years',               1),
  ]),

  makeGroup('Amount20-group-1', 'Scaling Group 1 — Financing', 'Amount2', [
    makeItem('depreciationMethodAmount20',  'Depreciation Method',       0),
    makeItem('generalInflationRateAmount23','General Inflation Rate',     0),
    makeItem('interestProportionAmount24',  'Interest Proportion',        0.5),
    makeItem('principalProportionAmount25', 'Principal Proportion',       0.5),
    makeItem('loanPercentageAmount26',      'Loan % of TOC',              0.2),
    makeItem('repaymentPercentageOfRevenueAmount27', 'Repayment % of Revenue', 0.1),
  ]),

  makeGroup('Amount30-group-1', 'Scaling Group 1 — Rates & Fixed Costs', 'Amount3', [
    makeItem('iRRAmount30',          'Internal Rate of Return', 0.05),
    makeItem('annualInterestRateAmount31', 'Annual Interest Rate',  0.04),
    makeItem('stateTaxRateAmount32', 'State Tax Rate',          0.05),
    makeItem('federalTaxRateAmount33','Federal Tax Rate',        0.21),
    makeItem('rawmaterialAmount34',  'Feedstock Cost',          10000),
    makeItem('laborAmount35',        'Labor Cost',              24000),
    makeItem('utilityAmount36',      'Utility Cost',             5000),
    makeItem('maintenanceAmount37',  'Maintenance Cost',         2500),
    makeItem('insuranceAmount38',    'Insurance Cost',            500),
  ]),

  makeGroup('Amount4-group-1', 'Scaling Group 1 — Process Quantities (V)', 'Amount4', [
    makeItem('vAmount40', 'v40', 1, 'V1'),
    makeItem('vAmount41', 'v41', 1, 'V2'),
    makeItem('vAmount42', 'v42', 1, 'V3'),
    makeItem('vAmount43', 'v43', 1, 'V4'),
    makeItem('vAmount44', 'v44', 1, 'V5'),
    makeItem('vAmount45', 'v45', 1, 'V6'),
    makeItem('vAmount46', 'v46', 1, 'V7'),
    makeItem('vAmount47', 'v47', 1, 'V8'),
    makeItem('vAmount48', 'v48', 1, 'V9'),
    makeItem('vAmount49', 'v49', 1, 'V10'),
  ]),

  makeGroup('Amount5-group-1', 'Scaling Group 1 — Process Costs (R)', 'Amount5', [
    makeItem('rAmount60', 'r60', 1, null, 'R1'),
    makeItem('rAmount61', 'r61', 1, null, 'R2'),
    makeItem('rAmount62', 'r62', 1, null, 'R3'),
    makeItem('rAmount63', 'r63', 1, null, 'R4'),
    makeItem('rAmount64', 'r64', 1, null, 'R5'),
    makeItem('rAmount65', 'r65', 1, null, 'R6'),
    makeItem('rAmount66', 'r66', 1, null, 'R7'),
    makeItem('rAmount67', 'r67', 1, null, 'R8'),
    makeItem('rAmount68', 'r68', 1, null, 'R9'),
    makeItem('rAmount69', 'r69', 1, null, 'R10'),
  ]),
];

export const efficacyAwareScalingGroupsAtom = atom(defaultGroups);
