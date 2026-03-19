const formFieldDescriptors = {
  "plantLifetimeAmount10": {
    description: "Typical operational lifetime of industrial facilities",
    context: "Used for depreciation calculations and long-term economic modeling",
    units: "years",
    industryRelevance: "All industrial sectors, especially capital-intensive industries",
  },
  "initialSellingPriceAmount13": {
    description: "Market price for the primary product",
    context: "Critical revenue parameter impacting project economics",
    units: "$/unit",
    industryRelevance: "Product market dynamics, competitive landscape",
  },
  // Add descriptors for all relevant form fields
};

const getPromptForField = (itemId, formContext) => {
  const fieldInfo = formFieldDescriptors[itemId] || {
    description: formContext.label || "parameter value",
    context: "techno-economic analysis",
    units: "",
    industryRelevance: "industrial projects"
  };
  
  return `Provide factual information about ${fieldInfo.description} (${fieldInfo.units}) in ${fieldInfo.industryRelevance}.
  
  Context: This parameter is used for ${fieldInfo.context}.
  
  Include:
  1. A brief summary of this parameter's importance and typical ranges
  2. At least 3-5 real-world examples from industry with specific values, sources, and years
  3. A recommended value based on current industry standards
  4. A brief rationale for your recommendation
  
  If the value is highly variable based on specific industries or applications, please indicate this and provide ranges for different contexts.`;
};

module.exports = { getPromptForField, formFieldDescriptors };
