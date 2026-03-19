const axios = require('axios');
const { getPromptForField } = require('../utils/promptGenerator');

const rateLimiter = {
  queue: [],
  processing: false,
  
  async add(fn, ...args) {
    return new Promise((resolve, reject) => {
      this.queue.push({
        fn,
        args,
        resolve,
        reject
      });
      
      if (!this.processing) {
        this.processQueue();
      }
    });
  },
  
  async processQueue() {
    if (this.queue.length === 0) {
      this.processing = false;
      return;
    }
    
    this.processing = true;
    const item = this.queue.shift();
    
    try {
      const result = await item.fn(...item.args);
      item.resolve(result);
    } catch (error) {
      item.reject(error);
    }
    
    setTimeout(() => this.processQueue(), 1000);
  }
};

const getLLMFactualPrecedence = async (itemId, formContext) => {
  return rateLimiter.add(async () => {
    const prompt = getPromptForField(itemId, formContext);
    
    try {
      const response = await axios.post('https://api.openai.com/v1/chat/completions', {
        model: "gpt-4-turbo",
        messages: [
          {
            role: "system",
            content: `You are a factual database for techno-economic analysis. Provide accurate, sourced information about industrial parameters, costs, and economic factors. Format your response as JSON with the following structure:
            {
              "summary": "Brief overview of the parameter and industry context",
              "examples": [
                {"entity": "Source name", "value": numeric_value, "unit": "unit if applicable", "year": year_of_data, "source": "specific reference"}
              ],
              "recommendedValue": recommended_numeric_value,
              "recommendationRationale": "Brief explanation for the recommendation",
              "sources": ["Full citation 1", "Full citation 2"]
            }`
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.2,
        response_format: { type: "json_object" }
      }, {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      
      const llmResponse = response.data.choices[0].message.content;
      return JSON.parse(llmResponse);
    } catch (error) {
      console.error('Error calling LLM service:', error);
      throw new Error('Failed to retrieve data from LLM service');
    }
  });
};

const getLLMFilteredFactualPrecedence = async (itemId, formContext, filters) => {
  return rateLimiter.add(async () => {
    const filterDescriptions = [];
    
    Object.entries(filters).forEach(([category, selectedFilters]) => {
      if (selectedFilters.length > 0) {
        const filterLabels = selectedFilters.map(id => {
          const keyPointLabels = {
            'chemical': 'Chemical Processing',
            'energy': 'Energy Generation',
            'manufacturing': 'Manufacturing',
            'pharmaceuticals': 'Pharmaceuticals',
            'renewables': 'Renewable Energy',
            'conventional': 'Conventional Technology',
            'emerging': 'Emerging Technology',
            'novel': 'Novel/Experimental Technology',
            'small': 'Small Scale (<100M USD)',
            'medium': 'Medium Scale (100M-1B USD)',
            'large': 'Large Scale (>1B USD)',
            'north_america': 'North America',
            'europe': 'Europe',
            'asia_pacific': 'Asia-Pacific',
            'global': 'Global Average',
            'current': 'Current (≤ 2 years)',
            'recent': 'Recent (3-5 years)',
            'historical': 'Historical (>5 years)',
            'stringent': 'Stringent Regulation',
            'moderate': 'Moderate Regulation',
            'minimal': 'Minimal Regulation'
          };
          
          return keyPointLabels[id] || id;
        });
        
        const description = `${category}: ${filterLabels.join(', ')}`;
        filterDescriptions.push(description);
      }
    });
    
    const filterContext = filterDescriptions.length > 0
      ? `Please specifically focus on examples matching these criteria: ${filterDescriptions.join('; ')}.`
      : '';
    
    const basePrompt = getPromptForField(itemId, formContext);
    const enhancedPrompt = `${basePrompt}\n\n${filterContext}`;
    
    try {
      const response = await axios.post('https://api.openai.com/v1/chat/completions', {
        model: "gpt-4-turbo",
        messages: [
          {
            role: "system",
            content: `You are a factual database for techno-economic analysis. Provide accurate, sourced information about industrial parameters, costs, and economic factors. Focus on providing relevant data that matches the specified filters and criteria. Format your response as JSON with the following structure:
            {
              "summary": "Brief overview of the parameter in the filtered context",
              "examples": [
                {"entity": "Source name", "value": numeric_value, "unit": "unit if applicable", "year": year_of_data, "source": "specific reference"}
              ],
              "recommendedValue": recommended_numeric_value,
              "recommendationRationale": "Brief explanation for the recommendation based on the filtered criteria",
              "sources": ["Full citation 1", "Full citation 2"]
            }`
          },
          {
            role: "user",
            content: enhancedPrompt
          }
        ],
        temperature: 0.2,
        response_format: { type: "json_object" }
      }, {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      
      const llmResponse = response.data.choices[0].message.content;
      return JSON.parse(llmResponse);
    } catch (error) {
      console.error('Error calling LLM service for filtered query:', error);
      throw new Error('Failed to retrieve filtered data from LLM service');
    }
  });
};

module.exports = { getLLMFactualPrecedence, getLLMFilteredFactualPrecedence };
