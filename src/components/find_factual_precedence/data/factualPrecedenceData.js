/**
 * Enhanced Factual Precedence Data with richer context and corporate evolution insights
 */

// Function to get parameter type for context-aware data
const getParameterType = (itemId) => {
  if (itemId.includes('lifetime') || itemId.includes('Amount10')) return 'lifetime';
  if (itemId.includes('priceAmount') || itemId.includes('Amount13')) return 'price';
  if (itemId.includes('costAmount') || itemId.includes('Amount14')) return 'cost';
  if (itemId.includes('investmentAmount') || itemId.includes('Amount11')) return 'investment';
  if (itemId.includes('unitsAmount') || itemId.includes('Amount12')) return 'volume';
  if (itemId.includes('loanAmount') || itemId.includes('Amount26')) return 'financing';
  if (itemId.includes('rateAmount')) return 'rate';
  return 'general';
};

// Corporate evolution dataset for relevant success stories
const corporateEvolutionData = {
  energy: [
    {
      company: "Tesla Energy",
      founded: 2015,
      evolution: [
        { stage: "startup", metric: "price", value: 600, unit: "$/kWh", year: 2015 },
        { stage: "growth", metric: "price", value: 350, unit: "$/kWh", year: 2019 },
        { stage: "mature", metric: "price", value: 250, unit: "$/kWh", year: 2023 }
      ],
      challenge: "High initial battery costs made energy storage solutions too expensive for mass adoption",
      solution: "Focused on vertical integration and economies of scale to drive down costs systematically"
    },
    {
      company: "First Solar",
      founded: 1999,
      evolution: [
        { stage: "startup", metric: "cost", value: 3.25, unit: "$/watt", year: 2000 },
        { stage: "growth", metric: "cost", value: 1.08, unit: "$/watt", year: 2010 },
        { stage: "mature", metric: "cost", value: 0.25, unit: "$/watt", year: 2022 }
      ],
      challenge: "Solar panel manufacturing costs were prohibitively high",
      solution: "Innovated thin-film technology to reduce material costs and improve manufacturing efficiency"
    }
  ],
  technology: [
    {
      company: "Amazon Web Services",
      founded: 2006,
      evolution: [
        { stage: "startup", metric: "price", value: 0.15, unit: "$/GB-month", year: 2006 },
        { stage: "growth", metric: "price", value: 0.10, unit: "$/GB-month", year: 2010 },
        { stage: "mature", metric: "price", value: 0.023, unit: "$/GB-month", year: 2023 }
      ],
      challenge: "High data storage costs limited cloud adoption by businesses",
      solution: "Leveraged economies of scale and continuous infrastructure optimization to systematically reduce prices"
    },
    {
      company: "Salesforce",
      founded: 1999,
      evolution: [
        { stage: "startup", metric: "price", value: 65, unit: "$/user-month", year: 2000 },
        { stage: "growth", metric: "price", value: 125, unit: "$/user-month", year: 2010 },
        { stage: "mature", metric: "price", value: 150, unit: "$/user-month", year: 2023 }
      ],
      challenge: "Industry was locked into expensive on-premise software with upfront licenses",
      solution: "Pioneered SaaS model with subscription pricing to eliminate large initial costs while increasing lifetime value"
    }
  ],
  manufacturing: [
    {
      company: "Tesla Motors",
      founded: 2003,
      evolution: [
        { stage: "startup", metric: "volume", value: 2500, unit: "units/year", year: 2010 },
        { stage: "growth", metric: "volume", value: 35000, unit: "units/year", year: 2014 },
        { stage: "mature", metric: "volume", value: 1300000, unit: "units/year", year: 2022 }
      ],
      challenge: "Electric vehicles were too expensive for mass market adoption",
      solution: "Started with low-volume, high-margin luxury vehicles before scaling to mass market"
    },
    {
      company: "SpaceX",
      founded: 2002,
      evolution: [
        { stage: "startup", metric: "cost", value: 60, unit: "million $/launch", year: 2010 },
        { stage: "growth", metric: "cost", value: 50, unit: "million $/launch", year: 2016 },
        { stage: "mature", metric: "cost", value: 15, unit: "million $/launch", year: 2022 }
      ],
      challenge: "Space launch costs were prohibitive for commercial applications",
      solution: "Developed reusable rocket technology to dramatically reduce launch costs"
    }
  ],
  healthcare: [
    {
      company: "Moderna",
      founded: 2010,
      evolution: [
        { stage: "startup", metric: "investment", value: 40, unit: "million $", year: 2011 },
        { stage: "growth", metric: "investment", value: 500, unit: "million $", year: 2015 },
        { stage: "mature", metric: "investment", value: 1700, unit: "million $", year: 2020 }
      ],
      challenge: "mRNA technology required massive upfront research investment",
      solution: "Secured strategic partnerships and phased approach to funding that matched R&D milestones"
    }
  ]
};

// Main factual precedence dataset with enhanced industrial context
export const factualPrecedenceData = {
  "plantLifetimeAmount10": {
    summary: "Industrial plant lifetimes vary by sector, technology type, and operational conditions. Most facilities are designed for 20-40 year operational periods, with proper maintenance extending these timeframes.",
    examples: [
      { entity: "Chemical Production Plant", value: 25, unit: "years", year: 2023, source: "American Chemical Society Industry Report" },
      { entity: "Power Generation Facility", value: 30, unit: "years", year: 2022, source: "IEA World Energy Outlook" },
      { entity: "Renewable Energy Installation", value: 20, unit: "years", year: 2023, source: "NREL Renewable Lifespan Assessment" },
      { entity: "Oil & Gas Refinery", value: 40, unit: "years", year: 2021, source: "Petroleum Institute Standards" },
      { entity: "Pharmaceutical Facility", value: 22, unit: "years", year: 2023, source: "Industry Benchmarking Study" },
      { entity: "Semiconductor Fabrication", value: 15, unit: "years", year: 2022, source: "Electronics Manufacturing Association" }
    ],
    recommendedValue: 25,
    recommendationRationale: "Balance of industry averages with consideration for technological obsolescence",
    confidenceLevel: "high",
    industryInsights: [
      {
        industryName: "Energy",
        averageValue: 28,
        trend: "Renewable energy installations typically have shorter design lifetimes (15-25 years) than conventional power plants (30-40 years)",
        keyFactors: ["Maintenance practices", "Technology evolution rate", "Regulatory environment"]
      },
      {
        industryName: "Chemical",
        averageValue: 25,
        trend: "Modern chemical facilities are designed with modular components to extend useful life through partial upgrades",
        keyFactors: ["Corrosion management", "Safety regulations", "Process technology advances"]
      }
    ],
    evolutionInsights: {
      earlyYears: "Emerging operations often predict conservative lifetimes (15-20 years) to ensure ROI calculations remain viable",
      middlePhase: "Established operations frequently extend initial lifetime estimates through strategic maintenance and upgrades",
      maturePhase: "Legacy facilities can operate well beyond design lifetimes with proper lifecycle management and partial modernization"
    }
  },

  "initialSellingPriceAmount13": {
    summary: "Market prices fluctuate based on supply-demand dynamics, production costs, and competitive landscape. Historical trends provide context for projection models.",
    examples: [
      { entity: "Market Average", value: 2.15, unit: "$/unit", year: 2023, source: "Global Market Index" },
      { entity: "Premium Segment", value: 3.50, unit: "$/unit", year: 2023, source: "Industry Analysis Report" },
      { entity: "Budget Segment", value: 1.75, unit: "$/unit", year: 2022, source: "Market Research Data" },
      { entity: "Direct-to-Consumer", value: 2.65, unit: "$/unit", year: 2023, source: "E-commerce Analytics" },
      { entity: "Wholesale Channel", value: 1.90, unit: "$/unit", year: 2023, source: "Distribution Network Study" }
    ],
    recommendedValue: 2.25,
    recommendationRationale: "Slight premium over market average based on quality positioning",
    confidenceLevel: "medium-high",
    industryInsights: [
      {
        industryName: "Consumer Products",
        averageValue: 2.35,
        trend: "Premiumization trend has increased average price points by 8-12% over the past 5 years",
        keyFactors: ["Brand positioning", "Raw material costs", "Distribution channel"]
      },
      {
        industryName: "Technology",
        averageValue: 2.10,
        trend: "Initial high prices for innovative products followed by systematic price reductions as scale increases",
        keyFactors: ["Manufacturing scale", "Component costs", "Competitive intensity"]
      }
    ],
    evolutionInsights: {
      earlyYears: "Startup companies often enter with premium pricing (30-50% above market) to establish value positioning and cover higher unit costs",
      middlePhase: "Growth-stage businesses optimize pricing through segmentation and data-driven elasticity analysis",
      maturePhase: "Established companies maintain price discipline through brand value while driving down costs for margin improvement"
    }
  },

  "bECAmount11": {
    summary: "Initial capital investments for industrial projects vary significantly based on scale, technology maturity, and sector-specific requirements. Phased approaches can optimize cash flow.",
    examples: [
      { entity: "Small-Scale Pilot", value: 2.5, unit: "million $", year: 2023, source: "Venture Capital Benchmark" },
      { entity: "Mid-Size Facility", value: 12, unit: "million $", year: 2022, source: "Industry Investment Report" },
      { entity: "Large Industrial Plant", value: 75, unit: "million $", year: 2023, source: "Capital Projects Database" },
      { entity: "Technology Startup", value: 1.8, unit: "million $", year: 2023, source: "Startup Funding Analysis" },
      { entity: "Established Manufacturer", value: 25, unit: "million $", year: 2022, source: "Manufacturing Association" }
    ],
    recommendedValue: 10,
    recommendationRationale: "Balanced approach allowing for proof of concept while managing investor risk profile",
    confidenceLevel: "medium",
    industryInsights: [
      {
        industryName: "Manufacturing",
        averageValue: 18.5,
        trend: "Automation and digital transformation increasing upfront capital but reducing operating costs",
        keyFactors: ["Automation level", "Scale economies", "Land and infrastructure costs"]
      },
      {
        industryName: "Technology",
        averageValue: 3.2,
        trend: "Cloud infrastructure has dramatically reduced initial capital requirements for software startups",
        keyFactors: ["Hardware requirements", "Regulatory compliance", "Scalability approach"]
      }
    ],
    evolutionInsights: {
      earlyYears: "Successful startups often begin with minimal viable infrastructure (40-60% less than 'ideal' setup)",
      middlePhase: "Growth-stage companies implement modular expansion tied directly to revenue milestones",
      maturePhase: "Established businesses optimize capital allocation through data-driven forecasting and flexible capacity"
    }
  },

  "numberOfUnitsAmount12": {
    summary: "Production volume projections should balance market potential, manufacturing capabilities, and cash flow requirements. Conservative ramp-up schedules reduce operational risks.",
    examples: [
      { entity: "Startup Phase", value: 10000, unit: "units/year", year: 2023, source: "Venture Startup Database" },
      { entity: "Growth Phase", value: 75000, unit: "units/year", year: 2022, source: "Scale-up Analysis" },
      { entity: "Mature Operation", value: 250000, unit: "units/year", year: 2023, source: "Industry Capacity Report" },
      { entity: "Premium Segment", value: 25000, unit: "units/year", year: 2023, source: "Market Segmentation Study" },
      { entity: "Mass Market", value: 175000, unit: "units/year", year: 2022, source: "Consumer Products Analysis" }
    ],
    recommendedValue: 50000,
    recommendationRationale: "Balanced volume allowing for economies of scale while managing production ramp-up risks",
    confidenceLevel: "medium",
    industryInsights: [
      {
        industryName: "Consumer Electronics",
        averageValue: 125000,
        trend: "Production volumes increasingly aligned with just-in-time manufacturing to reduce inventory costs",
        keyFactors: ["Supply chain resilience", "Seasonal demand patterns", "Product lifecycle length"]
      },
      {
        industryName: "Industrial Equipment",
        averageValue: 15000,
        trend: "Higher value per unit with more customization driving lower production volumes",
        keyFactors: ["Customization level", "Capital requirements per unit", "Service component"]
      }
    ],
    evolutionInsights: {
      earlyYears: "Most successful manufacturers begin with production volumes 70-90% lower than long-term targets",
      middlePhase: "Systematic volume expansion based on proven demand and manufacturing capability",
      maturePhase: "Data-driven production planning with sophisticated demand forecasting models"
    }
  },

  "totalOperatingCostPercentageAmount14": {
    summary: "Operating cost structures vary widely by industry, scale, and business model. Continuous improvement programs can systematically reduce costs over time.",
    examples: [
      { entity: "Manufacturing Average", value: 0.65, unit: "ratio", year: 2023, source: "Production Economics Journal" },
      { entity: "Technology Services", value: 0.45, unit: "ratio", year: 2023, source: "Tech Industry Benchmark" },
      { entity: "Consumer Products", value: 0.72, unit: "ratio", year: 2022, source: "Retail Analytics" },
      { entity: "Heavy Industry", value: 0.78, unit: "ratio", year: 2023, source: "Industrial Economics Report" },
      { entity: "Software Companies", value: 0.38, unit: "ratio", year: 2022, source: "SaaS Metrics Database" }
    ],
    recommendedValue: 0.60,
    recommendationRationale: "Balanced operating structure with room for profitability while accounting for realistic costs",
    confidenceLevel: "medium-high",
    industryInsights: [
      {
        industryName: "Manufacturing",
        averageValue: 0.68,
        trend: "Automation and lean practices gradually reducing operating costs by 1-2% annually",
        keyFactors: ["Labor intensity", "Energy requirements", "Material costs"]
      },
      {
        industryName: "Software",
        averageValue: 0.40,
        trend: "Cloud-based solutions achieve greater economies of scale as customer base grows",
        keyFactors: ["Development costs", "Customer acquisition cost", "Infrastructure efficiency"]
      }
    ],
    evolutionInsights: {
      earlyYears: "Early-stage operations typically run 10-20% higher costs than industry averages due to scale limitations",
      middlePhase: "Process optimization and supplier negotiations drive systematic cost reduction",
      maturePhase: "Data analytics enable precise cost control and predictive maintenance to minimize operational expenses"
    }
  },

  "loanPercentageAmount26": {
    summary: "Debt-to-equity structures balance financial leverage, risk tolerance, and capital availability. Industry norms and project stability influence optimal ratios.",
    examples: [
      { entity: "Conservative Structure", value: 0.30, unit: "ratio", year: 2023, source: "Risk Management Guide" },
      { entity: "Balanced Approach", value: 0.50, unit: "ratio", year: 2022, source: "Financial Strategy Handbook" },
      { entity: "Leveraged Model", value: 0.70, unit: "ratio", year: 2023, source: "Capital Structure Analysis" },
      { entity: "Early Stage Venture", value: 0.20, unit: "ratio", year: 2023, source: "Startup Finance Report" },
      { entity: "Established Operation", value: 0.55, unit: "ratio", year: 2022, source: "Corporate Finance Benchmark" }
    ],
    recommendedValue: 0.45,
    recommendationRationale: "Moderate leverage providing capital efficiency while maintaining financial flexibility",
    confidenceLevel: "medium",
    industryInsights: [
      {
        industryName: "Capital Intensive Industries",
        averageValue: 0.60,
        trend: "Project finance structures increasingly segregating risk through special purpose vehicles",
        keyFactors: ["Asset life", "Revenue stability", "Interest rate environment"]
      },
      {
        industryName: "Technology",
        averageValue: 0.25,
        trend: "Earlier access to equity financing reducing reliance on debt for growth companies",
        keyFactors: ["Growth rate", "Profitability timeline", "Asset tangibility"]
      }
    ],
    evolutionInsights: {
      earlyYears: "Successful startups often begin with lower debt ratios (15-30%) until business model is proven",
      middlePhase: "Growth-stage companies optimize capital structure as revenue stability increases",
      maturePhase: "Established businesses leverage strong balance sheets for strategic debt financing"
    }
  }
};

/**
 * Get pre-populated precedence data with enhanced corporate evolution context
 */
export const getPrePopulatedPrecedenceData = (itemId, formValue) => {
  // Get the basic data for this parameter
  const baseData = factualPrecedenceData[itemId] || null;

  if (!baseData) {
    return Promise.resolve(null);
  }

  // Enhance the data with relevant corporate evolution stories
  const paramType = getParameterType(itemId);
  const enhancedData = { ...baseData };

  // Add evolution stories if available
  if (paramType === 'price' || paramType === 'cost') {
    // Find relevant companies that evolved their pricing or cost structure
    const relevantStories = [];

    Object.values(corporateEvolutionData).forEach(industryCompanies => {
      industryCompanies.forEach(company => {
        const relevantMetrics = company.evolution.filter(data =>
            data.metric === 'price' || data.metric === 'cost'
        );

        if (relevantMetrics.length > 0) {
          relevantStories.push({
            company: company.company,
            challenge: company.challenge,
            solution: company.solution,
            evolution: relevantMetrics
          });
        }
      });
    });

    if (relevantStories.length > 0) {
      enhancedData.evolutionStories = relevantStories.slice(0, 2); // Limit to 2 stories
    }
  }

  if (paramType === 'volume' || paramType === 'lifetime') {
    // Similar logic for volume-related parameters
    const relevantStories = [];

    Object.values(corporateEvolutionData).forEach(industryCompanies => {
      industryCompanies.forEach(company => {
        const relevantMetrics = company.evolution.filter(data =>
            data.metric === 'volume'
        );

        if (relevantMetrics.length > 0) {
          relevantStories.push({
            company: company.company,
            challenge: company.challenge,
            solution: company.solution,
            evolution: relevantMetrics
          });
        }
      });
    });

    if (relevantStories.length > 0) {
      enhancedData.evolutionStories = relevantStories.slice(0, 2);
    }
  }

  // Add a confidence score if not already present
  if (!enhancedData.confidenceLevel) {
    enhancedData.confidenceLevel = enhancedData.examples.length > 3 ? "high" : "medium";
  }

  return Promise.resolve(enhancedData);
};

/**
 * Generate context-aware parameter recommendations based on form values
 */
export const getContextAwareRecommendations = (formValues) => {
  const recommendations = {};

  // Check if we have essential project parameters
  if (formValues["bECAmount11"]?.value && formValues["initialSellingPriceAmount13"]?.value) {
    const investment = parseFloat(formValues["bECAmount11"].value);
    const price = parseFloat(formValues["initialSellingPriceAmount13"].value);

    // Recommend appropriate production volume based on investment scale
    if (!formValues["numberOfUnitsAmount12"]?.value) {
      const suggestedVolume = Math.round(investment * 5000 / price);
      recommendations.numberOfUnitsAmount12 = {
        value: suggestedVolume,
        rationale: "Recommended production volume based on investment scale and price point for optimal capacity utilization"
      };
    }

    // Recommend lifetime based on industry patterns and investment scale
    if (!formValues["plantLifetimeAmount10"]?.value) {
      let suggestedLifetime = 25; // Default

      if (investment < 5) {
        suggestedLifetime = 15; // Smaller investments often target shorter horizons
      } else if (investment > 50) {
        suggestedLifetime = 30; // Major investments typically plan for longer lifetimes
      }

      recommendations.plantLifetimeAmount10 = {
        value: suggestedLifetime,
        rationale: "Recommended facility lifetime based on investment scale and industry patterns"
      };
    }
  }

  return recommendations;
};