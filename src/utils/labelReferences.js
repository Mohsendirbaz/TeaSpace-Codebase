import { faDollarSign, faCogs, faIndustry, faBuilding, faWarehouse, faHandshake, faChartLine, faTools } from '@fortawesome/free-solid-svg-icons';

// Original property mappings that serve as the main reference for resets
// Complete property mapping object with updated vAmount nomenclature
export const propertyMapping = {
  "plantLifetimeAmount10": "Plant Lifetime",
  "bECAmount11": "Bare Erected Cost",
  "numberOfUnitsAmount12": "Number of Units",
  "initialSellingPriceAmount13": "Price",
  "totalOperatingCostPercentageAmount14": "Direct Total Operating Cost Percentage as % of Revenue",
  "engineering_Procurement_and_Construction_EPC_Amount15": "Engineering Procurement and Construction as % of BEC",
  "process_contingency_PC_Amount16": "Process Contingency as % of BEC",
  "project_Contingency_PT_BEC_EPC_PCAmount17": "Project Contingency as % of BEC, EPC, PC",
  "use_direct_operating_expensesAmount18": "Use Direct Operating Expenses",
  "use_direct_revenueAmount19": "Use Direct Revenue",
  "depreciationMethodAmount20": "Depreciation Method",
  "loanTypeAmount21": "Loan Type",
  "interestTypeAmount22": "Interest Type",
  "generalInflationRateAmount23": "General Inflation Rate",
  "interestProportionAmount24": "Interest Proportion",
  "principalProportionAmount25": "Principal Proportion",
  "loanPercentageAmount26": "Loan Percentage of TOC",
  "repaymentPercentageOfRevenueAmount27": "Repayment Percentage Of Revenue",
  "numberofconstructionYearsAmount28": "Number of Construction Years",
  "iRRAmount30": "Internal Rate of Return",
  "annualInterestRateAmount31": "Annual Interest Rate",
  "stateTaxRateAmount32": "State Tax Rate",
  "federalTaxRateAmount33": "Federal Tax Rate",
  "rawmaterialAmount34": "Feedstock Cost",
  "laborAmount35": "Labor Cost",
  "utilityAmount36": "Utility Cost",
  "maintenanceAmount37": "Maintenance Cost",
  "insuranceAmount38": "Insurance Cost",
  "vAmount40": "v40",
  "vAmount41": "v41",
  "vAmount42": "v42",
  "vAmount43": "v43",
  "vAmount44": "v44",
  "vAmount45": "v45",
  "vAmount46": "v46",
  "vAmount47": "v47",
  "vAmount48": "v48",
  "vAmount49": "v49",
  "vAmount50": "v50",
  "vAmount51": "v51",
  "vAmount52": "v52",
  "vAmount53": "v53",
  "vAmount54": "v54",
  "vAmount55": "v55",
  "vAmount56": "v56",
  "vAmount57": "v57",
  "vAmount58": "v58",
  "vAmount59": "v59",
  "rAmount60": "r60",
  "rAmount61": "r61",
  "rAmount62": "r62",
  "rAmount63": "r63",
  "rAmount64": "r64",
  "rAmount65": "r65",
  "rAmount66": "r66",
  "rAmount67": "r67",
  "rAmount68": "r68",
  "rAmount69": "r69",
  "rAmount70": "r70",
  "rAmount71": "r71",
  "rAmount72": "r72",
  "rAmount73": "r73",
  "rAmount74": "r74",
  "rAmount75": "r75",
  "rAmount76": "r76",
  "rAmount77": "r77",
  "rAmount78": "r78",
  "rAmount79": "r79",
};

// Complete select options mapping
export const selectOptionsMapping = {
  "depreciationMethodAmount20": ['Straight-Line', '5-MACRS', '7-MACRS', '15-MACRS', 'Custom'],
  "loanTypeAmount21": ['simple', 'compounded'],
  "interestTypeAmount22": ['fixed', 'variable'],
  "loanRepaymentFrequencyAmount21": ['quarterly', 'semiannually', 'annually'],
  "use_direct_operating_expensesAmount18": ['True', 'False'],
  "use_direct_revenueAmount19": ['True', 'False']
};

// Complete icon mapping with updated vAmount nomenclature
export const iconMapping = {
  // Amount10-19 icons
  "bECAmount11": faDollarSign,
  "numberOfUnitsAmount12": faCogs,
  "initialSellingPriceAmount13": faDollarSign,
  "totalOperatingCostPercentageAmount14": faChartLine,
  "engineering_Procurement_and_Construction_EPC_Amount15": faIndustry,
  "process_contingency_PC_Amount16": faCogs,
  "project_Contingency_PT_BEC_EPC_PCAmount17": faTools,
  "plantLifetimeAmount10": faBuilding,
  "use_direct_operating_expensesAmount18": faHandshake,
  "use_direct_revenueAmount19": faHandshake,

  // Amount20-29 icons
  "depreciationMethodAmount20": faChartLine,
  "loanTypeAmount21": faDollarSign,
  "interestTypeAmount22": faDollarSign,
  "generalInflationRateAmount23": faChartLine,
  "interestProportionAmount24": faDollarSign,
  "principalProportionAmount25": faDollarSign,
  "loanPercentageAmount26": faDollarSign,
  "repaymentPercentageOfRevenueAmount27": faDollarSign,
  "numberofconstructionYearsAmount28": faBuilding,

  // Amount30-39 icons
  "iRRAmount30": faChartLine,
  "annualInterestRateAmount31": faDollarSign,
  "stateTaxRateAmount32": faDollarSign,
  "federalTaxRateAmount33": faDollarSign,
  "rawmaterialAmount34": faWarehouse,
  "laborAmount35": faTools,
  "utilityAmount36": faWarehouse,
  "maintenanceAmount37": faTools,
  "insuranceAmount38": faHandshake,

  // vAmount icons (40-79)
  ...Object.fromEntries(
      Array.from({ length: 20 }, (_, i) => [`vAmount${40 + i}`, faWarehouse])
  ),
  ...Object.fromEntries(
      Array.from({ length: 40 }, (_, i) => [`rAmount${60 + i}`, faWarehouse])
  )
};

// Complete default values initialization
export const defaultValues = {
  // Amount10-19 defaults
  bECAmount11: 200_000,
  numberOfUnitsAmount12: 30000,
  initialSellingPriceAmount13: 2,
  totalOperatingCostPercentageAmount14: 0.1,
  engineering_Procurement_and_Construction_EPC_Amount15: 0,
  process_contingency_PC_Amount16: 0,
  project_Contingency_PT_BEC_EPC_PCAmount17: 0,
  use_direct_operating_expensesAmount18: 'False',
  use_direct_revenueAmount19: 'False',
  plantLifetimeAmount10: 20,

  // Amount20-29 defaults
  numberofconstructionYearsAmount28: 1,
  depreciationMethodAmount20: 'Straight-Line',
  loanTypeAmount21: 'simple',
  interestTypeAmount22: 'fixed',
  generalInflationRateAmount23: 0,
  interestProportionAmount24: 0.5,
  principalProportionAmount25: 0.5,
  loanPercentageAmount26: 0.2,
  repaymentPercentageOfRevenueAmount27: 0.1,

  // Amount30-39 defaults
  iRRAmount30: 0.05,
  annualInterestRateAmount31: 0.04,
  stateTaxRateAmount32: 0.05,
  federalTaxRateAmount33: 0.21,
  rawmaterialAmount34: 10000,
  laborAmount35: 24000,
  utilityAmount36: 5000,
  maintenanceAmount37: 2500,
  insuranceAmount38: 500,


  ...Object.fromEntries(
      Array.from({ length: 20 }, (_, i) => [`vAmount${40 + i}`,1])
  ),
  ...Object.fromEntries(
      Array.from({ length: 20 }, (_, i) => [`rAmount${60 + i}`,1])
  )
};
