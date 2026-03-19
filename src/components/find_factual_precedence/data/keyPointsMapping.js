export const keyPointCategories = {
  INDUSTRY_TYPE: 'industryType',
  TECHNOLOGY: 'technology',
  SCALE: 'scale',
  REGION: 'region',
  TIME_PERIOD: 'timePeriod',
  REGULATORY_FRAMEWORK: 'regulatoryFramework',
};

export const keyPointsData = {
  industryType: [
    { id: 'chemical', label: 'Chemical Processing' },
    { id: 'energy', label: 'Energy Generation' },
    { id: 'manufacturing', label: 'Manufacturing' },
    { id: 'pharmaceuticals', label: 'Pharmaceuticals' },
    { id: 'renewables', label: 'Renewable Energy' },
  ],
  technology: [
    { id: 'conventional', label: 'Conventional Technology' },
    { id: 'emerging', label: 'Emerging Technology' },
    { id: 'novel', label: 'Novel/Experimental Technology' },
  ],
  scale: [
    { id: 'small', label: 'Small Scale (<100M USD)' },
    { id: 'medium', label: 'Medium Scale (100M-1B USD)' },
    { id: 'large', label: 'Large Scale (>1B USD)' },
  ],
  region: [
    { id: 'north_america', label: 'North America' },
    { id: 'europe', label: 'Europe' },
    { id: 'asia_pacific', label: 'Asia-Pacific' },
    { id: 'global', label: 'Global Average' },
  ],
  timePeriod: [
    { id: 'current', label: 'Current (≤ 2 years)' },
    { id: 'recent', label: 'Recent (3-5 years)' },
    { id: 'historical', label: 'Historical (>5 years)' },
  ],
  regulatoryFramework: [
    { id: 'stringent', label: 'Stringent Regulation' },
    { id: 'moderate', label: 'Moderate Regulation' },
    { id: 'minimal', label: 'Minimal Regulation' },
  ],
};

export const formValueKeyPointRelevance = {
  "plantLifetimeAmount10": [
    keyPointCategories.INDUSTRY_TYPE,
    keyPointCategories.TECHNOLOGY,
    keyPointCategories.REGULATORY_FRAMEWORK,
  ],
  "initialSellingPriceAmount13": [
    keyPointCategories.INDUSTRY_TYPE,
    keyPointCategories.REGION,
    keyPointCategories.TIME_PERIOD,
  ],
};
